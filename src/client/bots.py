from proto.game_proto import game_proto, GameMessage
from proto.game_proto import ACT, OK, CHAL, BLOCK, SHOW, LOSE, COINS, DECK, CHOOSE, KEEP, HELLO, PLAYER, START, READY, TURN, EXIT, ILLEGAL
from .game.state_machine import PlayerState, Tag
from .game.core import *
from .player import InformedPlayer
import random
from loguru import logger


# This class is used to implement your bot.
# You are free to edit and delete this class.
class CoupBot(InformedPlayer):
    """
    CoopBot player class.
    
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
        history (list[GameMessage]): History of received messages.
        ready (bool): Flag for whether the player is ready or not.
        replied (bool): Flag for whether the player has replied to the last message or not.
        state (PlayerState): State of the player.
        tag (Tag): Tag for the player. Used to identify the player in the game.
        term (Terminal): Terminal used to write messages manually.
        terminate_after_death (bool): Flag for whether the player should terminate after its own death.
        turn (bool): Flag for whether it is the player's turn or not.
    
    Methods:
        choose_message(): Choose a message to send to the server based on the current state of the game.
        
    """

    def __init__(self):
        super().__init__()

    def choose_message(self) -> None:
        if len(self.possible_messages) == 0:
            raise IndexError("No possible messages.")
        
        # Implement your bot here
        # Example: choose a random message from possible messages
        self.msg = GameMessage(random.choice(self.possible_messages))

class RandomBot(InformedPlayer):
    """RandomBot player class."""

    def __init__(self):
        super().__init__()

    def choose_message(self):
        if len(self.possible_messages) == 0:
            raise IndexError("No possible messages.")
        self.msg = GameMessage(random.choice(self.possible_messages)) # choose random

class HonestBot(InformedPlayer):
    """HonestBot player class."""

    def __init__(self):
        super().__init__()

    def pick_random(self, possible_messages: list[str]):
        """Pick a random message from the possible messages."""
        if len(possible_messages) == 0:
            raise IndexError("No possible messages.")
        
        self.msg = GameMessage(random.choice(possible_messages))

    def choose_message(self):
        current_msg = self.history[-1]
        previous_msg = self.history[-2]
        if current_msg.ID1 is None or len(self.players) == 0:
            self.pick_random(self.possible_messages)
            return
        
        choices: list[str] = []
        
        # Update previous player deck in case of a change in their deck
        if self.state == PlayerState.R_MY_TURN or self.state == PlayerState.R_OTHER_TURN:
            if previous_msg.command == ACT and previous_msg.action == EXCHANGE:
                # the player has exchanged cards successfully
                if previous_msg.ID1 in self.players:
                    self.players[previous_msg.ID1].deck = []
                else:
                    logger.warning(f"Player {previous_msg.ID1} not found in players list.")
                    
        elif self.state == PlayerState.R_LOSE or self.state == PlayerState.R_SHOW:
            if previous_msg.command == SHOW or previous_msg.command == LOSE:
                # the card that was shown or lost is no longer in the player's deck
                if previous_msg.ID1 in self.players:
                    if previous_msg.card1 in self.players[previous_msg.ID1].deck:
                        self.players[previous_msg.ID1].deck.remove(previous_msg.card1)
                else:
                    logger.warning(f"Player {previous_msg.ID1} not found in players list.")
        
        # Believe any player that claims to have a card, 
        # if at least one of their cards is unknown
        if self.state == PlayerState.R_MY_TURN:
            if self.coins < COUP_COINS_THRESHOLD:
                
                choices.append(game_proto.ACT(self.id, INCOME))
                choices.append(game_proto.ACT(self.id, FOREIGN_AID))
                if DUKE in self.deck:
                    choices.append(game_proto.ACT(self.id, TAX))
                if AMBASSADOR in self.deck:
                    choices.append(game_proto.ACT(self.id, EXCHANGE))
                
                if CAPTAIN in self.deck:
                    for target in self.players.values():
                        if target != self and target.alive:
                            choices.append(game_proto.ACT(self.id, STEAL, target.id))
                
                if ASSASSIN in self.deck and self.coins >= ASSASSINATION_COST:
                    for target in self.players.values():
                        if target != self and target.alive:
                            choices.append(game_proto.ACT(self.id, ASSASSINATE, target.id))
            
            if self.coins >= COUP_COST:
                for target in self.players.values():
                    if target != self and target.alive:
                        choices.append(game_proto.ACT(self.id, COUP, target.id))
                            
        elif self.state == PlayerState.R_FAID:
            choices.append(game_proto.OK())
            if DUKE in self.deck:
                choices.append(game_proto.BLOCK(self.id, DUKE))

        elif self.state == PlayerState.R_EXCHANGE:
            choices.append(game_proto.OK())
            if len(self.players[current_msg.ID1].deck) < 2:
                self.players[current_msg.ID1].deck.append(AMBASSADOR)
            elif AMBASSADOR not in self.players[current_msg.ID1].deck:
                choices.append(game_proto.CHAL(self.id))
            
        elif self.state == PlayerState.R_TAX:
            choices.append(game_proto.OK())
            if len(self.players[current_msg.ID1].deck) < 2:
                self.players[current_msg.ID1].deck.append(DUKE)
            elif DUKE not in self.players[current_msg.ID1].deck:
                choices.append(game_proto.CHAL(self.id))
                
        elif self.state == PlayerState.R_ASSASS_ME:
            choices.append(game_proto.OK())
            if CONTESSA in self.deck:
                choices.append(game_proto.BLOCK(self.id, CONTESSA))
            if len(self.players[current_msg.ID1].deck) < 2:
                self.players[current_msg.ID1].deck.append(ASSASSIN)
            elif ASSASSIN not in self.players[current_msg.ID1].deck:
                choices.append(game_proto.CHAL(self.id))
                
        elif self.state == PlayerState.R_ASSASS:
            choices.append(game_proto.OK())
            if len(self.players[current_msg.ID1].deck) < 2:
                self.players[current_msg.ID1].deck.append(ASSASSIN)
            elif ASSASSIN not in self.players[current_msg.ID1].deck:
                choices.append(game_proto.CHAL(self.id))
                
        elif self.state == PlayerState.R_STEAL_ME:
            choices.append(game_proto.OK())
            if CAPTAIN in self.deck:
                choices.append(game_proto.BLOCK(self.id, CAPTAIN))
            if AMBASSADOR in self.deck:
                choices.append(game_proto.BLOCK(self.id, AMBASSADOR))
            if len(self.players[current_msg.ID1].deck) < 2:
                self.players[current_msg.ID1].deck.append(CAPTAIN)
            elif CAPTAIN not in self.players[current_msg.ID1].deck:
                choices.append(game_proto.CHAL(self.id))
                
        elif self.state == PlayerState.R_STEAL:
            choices.append(game_proto.OK())
            if len(self.players[current_msg.ID1].deck) < 2:
                self.players[current_msg.ID1].deck.append(CAPTAIN)
            elif CAPTAIN not in self.players[current_msg.ID1].deck:
                choices.append(game_proto.CHAL(self.id))

        elif self.state == PlayerState.R_BLOCK_FAID:
            choices.append(game_proto.OK())
            if DUKE in self.deck:
                choices.append(game_proto.BLOCK(self.id, DUKE))
                
        elif self.state == PlayerState.R_BLOCK_ASSASS:
            choices.append(game_proto.OK())
            if len(self.players[current_msg.ID1].deck) < 2:
                self.players[current_msg.ID1].deck.append(CONTESSA)
            elif CONTESSA not in self.players[current_msg.ID1].deck:
                choices.append(game_proto.CHAL(self.id))
                
        elif self.state == PlayerState.R_BLOCK_STEAL_B:
            choices.append(game_proto.OK())
            if len(self.players[current_msg.ID1].deck) < 2:
                self.players[current_msg.ID1].deck.append(AMBASSADOR)
            elif AMBASSADOR not in self.players[current_msg.ID1].deck:
                choices.append(game_proto.CHAL(self.id))
                
        elif self.state == PlayerState.R_BLOCK_STEAL_C:
            choices.append(game_proto.OK())
            if len(self.players[current_msg.ID1].deck) < 2:
                self.players[current_msg.ID1].deck.append(CAPTAIN)
            elif CAPTAIN not in self.players[current_msg.ID1].deck:
                choices.append(game_proto.CHAL(self.id))
        
        else:
            self.pick_random(self.possible_messages)
            return
        
        self.pick_random(choices)
        
        

class TestBot(InformedPlayer):
    """TestBot player class."""

    def __init__(self):
        super().__init__()

    def choose_message(self):
        if len(self.possible_messages) == 0:
            raise IndexError("No possible messages.")
        self.msg = GameMessage(random.choice(self.possible_messages)) # choose random
        # self.msg = GameMessage(self.possible_messages[-1]) # choose last
        
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