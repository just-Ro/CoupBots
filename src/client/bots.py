from proto.game_proto import game_proto, GameMessage
from proto.game_proto import ACT, OK, CHAL, BLOCK, SHOW, LOSE, COINS, DECK, CHOOSE, KEEP, HELLO, PLAYER, START, READY, TURN, EXIT, ILLEGAL
from .game.state_machine import PlayerState, Tag
from .game.core import *
from .player import InformedPlayer
import random
from loguru import logger
import gymnasium as gym
from gymnasium import spaces
import numpy as np

state_to_index = {state: idx for idx, state in enumerate(PlayerState)}
tag_to_index = {tag: idx for idx, tag in enumerate(Tag)}

class CoupBot(InformedPlayer, gym.Env):
    """ CoopBot player class.
        
        Attributes:
            alive (bool): Flag for whether the player is alive or not.
            checkout (SimpleQueue): Queue used to send messages to the server. The queue is thread-safe and can be used by multiple threads.
            coins (int): Number of coins the player has.
            deck (list[str]): List of cards in the player's deck.
            exchange_cards (list[str]): List of cards to exchange with the deck.
            id (str): Player ID.
            is_root (bool): Flag for whether the player is the root player or not.
            msg (GameMessage): Message to be sent to the server.
            players (dict[str, PlayerSim]): Dictionary of players in the game.
            possible_messages (list[str]): List of possible messages the player can send.
            rcv_msg (GameMessage): Last received message.
            ready (bool): Flag for whether the player is ready or not.
            replied (bool): Flag for whether the player has replied to the last message or not.
            state (PlayerState): State of the player.
            tag (Tag): Tag for the player. Used to identify the player in the game.
            term (Terminal): Terminal used to write messages manually.
            terminate_after_death (bool): Flag for whether the player should terminate after its own death.
            turn (bool): Flag for whether it is the player's turn or not.
        
        Methods:
            choose_message(): Choose a message to send to the server based on the current state of the game."""

    def __init__(self):
        InformedPlayer.__init__(self)
        gym.Env.__init__(self)
        self.message_to_id: dict[str, int] = {}
        self.id_to_message: dict[int, str] = {}
        self.precompute_ids()
        self.observation_vector = []
        
        # gym stuff
        obs_dim = 1 + len(PlayerState) + MAX_PLAYERS * (1 + 1 + 1 + len(CHARACTERS) + 1 + len(Tag))
        self.action_space = spaces.Discrete(len(self.message_to_id))  # message index
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(obs_dim,), dtype=np.float32)

    def choose_message(self) -> None:
        if len(self.possible_messages) == 0:
            raise IndexError("No possible messages.")
        
        # Implement your bot here
        # Example: choose a random message from possible messages
        self.msg = GameMessage(random.choice(self.possible_messages))

    def precompute_ids(self):
        msgs: list[str] = []
        for id1 in ("1", "2", "3", "4", "5", "6"):
            # ACT
            for action in ACTIONS:
                if action in TARGET_ACTIONS:
                    for id2 in ("1", "2", "3", "4", "5", "6"):
                        if id1 != id2:
                            msgs.append(game_proto.ACT(id1, action, id2))
                else:
                    msgs.append(game_proto.ACT(id1, action))
            # CHAL
            msgs.append(game_proto.CHAL(id1))
            # BLOCK & SHOW & LOSE
            for card in CHARACTERS:
                msgs.append(game_proto.BLOCK(id1, card))
                msgs.append(game_proto.SHOW(id1, card))
                msgs.append(game_proto.LOSE(id1, card))
            # COINS
            for coins in range(0, 13):
                msgs.append(game_proto.COINS(id1, coins))
            # PLAYER
            msgs.append(game_proto.PLAYER(id1))
            # TURN
            msgs.append(game_proto.TURN(id1))
            # DEAD
            msgs.append(game_proto.DEAD(id1))
            
        # OK
        msgs.append(game_proto.OK())
        # SHOW
        msgs.append(game_proto.SHOW())
        # LOSE
        msgs.append(game_proto.LOSE())
        # DECK
        for card1 in CHARACTERS:
            for card2 in CHARACTERS:
                msgs.append(game_proto.DECK(card1, card2))
        # CHOOSE & KEEP
        for card1 in CHARACTERS:
            msgs.append(game_proto.KEEP(card1))
            for card2 in CHARACTERS:
                msgs.append(game_proto.CHOOSE(card1, card2))
                msgs.append(game_proto.KEEP(card1, card2))
        # HELLO
        msgs.append(game_proto.HELLO())
        # START
        msgs.append(game_proto.START())
        # READY
        msgs.append(game_proto.READY())
        # EXIT
        msgs.append(game_proto.EXIT())
        # ILLEGAL
        msgs.append(game_proto.ILLEGAL())
        
        # Index messages
        for i, msg in enumerate(msgs):
            self.message_to_id[msg] = i
            self.id_to_message[i] = msg
    
    def update_observations(self):
        """Update the observation vector based on the current state of the game."""
        # State is:
        # my player id (normalized)
        # my player state (one-hot)
        # player n alive (bool)
        # player n coins (normalized)
        # player n deck len (normalized)
        # player n deck (multi-hot)
        # player n turn (bool)
        # player n tag (one-hot)
        state = []
        state.append(normalize(int(self.id), 1, 6))   # my player id
        state.extend(playerstate_one_hot(self.state))   # my player state
        for id in range(1, MAX_PLAYERS + 1):
            exists = id in self.players.keys()
            if str(id) == self.id:
                state.append(int(self.alive))   # alive
                state.append(normalize(self.coins, 0, 12))  # coins
                state.append(normalize(len(self.deck), 0, 2))   # deck len
                deck = [0.0] * len(CHARACTERS)  # deck
                for card in self.deck:
                    deck[CHARACTERS.index(card)] += 0.5
                state.extend(deck)
                state.append(int(self.turn))    # turn
                state.extend(tag_one_hot(self.tag)) # tag
            else:
                state.append(int(self.players[str(id)].alive) if exists else 0) # alive
                state.append(normalize(self.players[str(id)].coins, 0, 12) if exists else 0.0) # coins
                state.append(normalize(len(self.players[str(id)].deck), 0, 2) if exists else 0.0)  # deck len
                deck = [0.0] * len(CHARACTERS)  # deck
                if exists:
                    for card in self.players[str(id)].deck:
                        deck[CHARACTERS.index(card)] += 0.5
                state.extend(deck)
                state.append(int(self.players[str(id)].turn) if exists else 0) # turn
                state.extend(tag_one_hot(self.players[str(id)].tag if exists else Tag.T_NONE))    # tag
        
        self.observation_vector = state

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.__init__()  # or a proper internal reset
        obs = self._get_observation()
        return obs, {}
    
    def _get_observation(self):
        self.update_observations()
        return np.array(self.observation_vector, dtype=np.float32)

    def compute_reward(self):
        # Reward is 1 if the player wins, 0 otherwise
        if self.alive and all([not player.alive for player in self.players.values() if player.alive]):
            return 1.0
        return 0.0


def tag_one_hot(tag: Tag) -> list[int]:
    """One-hot encode a player state."""
    vec = [0] * len(Tag)
    vec[tag_to_index[tag]] = 1
    return vec

def playerstate_one_hot(state: PlayerState) -> list[int]:
    """One-hot encode a player state."""
    vec = [0] * len(PlayerState)
    vec[state_to_index[state]] = 1
    return vec
    
def int_one_hot(num: int, min: int, max: int) -> list[int]:
    """One-hot encode a number."""
    if num < min or num > max:
        raise ValueError(f"Number {num} is out of range [{min}, {max}]")
    vec = [0] * (max - min + 1)
    vec[num - min] = 1
    return vec

def normalize(num: int, min: int, max: int) -> float:
    """Normalize a number to the range [0, 1]."""
    if num < min or num > max:
        raise ValueError(f"Number {num} is out of range [{min}, {max}]")
    return (num - min) / (max - min)

class TestBot(InformedPlayer):
    """TestBot player class."""

    def __init__(self):
        super().__init__()

    def choose_message(self):
        if len(self.possible_messages) == 0:
            raise IndexError("No possible messages.")
        self.msg = GameMessage(random.choice(self.possible_messages)) # choose random
        # self.msg = GameMessage(self.possible_messages[-1]) # choose last
        return
        
        # test with priority choices
        msgs: list[GameMessage] = []
        for m in self.possible_messages:
            msgs.append(GameMessage(m))
        for m in msgs:
            if m.command == ACT and m.action == ASSASSINATE:
                self.msg = m
                return
        for m in msgs:
            if m.command == ACT and m.action == INCOME:
                self.msg = m
                return
        for m in msgs:
            if m.command == BLOCK and len(self.deck) == 1:
                self.msg = m
                return