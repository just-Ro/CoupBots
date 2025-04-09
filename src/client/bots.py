from proto.game_proto import game_proto, GameMessage
from proto.game_proto import ACT, OK, CHAL, BLOCK, SHOW, LOSE, COINS, DECK, CHOOSE, KEEP, HELLO, PLAYER, START, READY, TURN, EXIT, ILLEGAL
from .game.state_machine import PlayerState, Tag
from .game.core import *
from .player import InformedPlayer
import random
from loguru import logger



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
        rcv_msg (GameMessage): Last received message.
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
            if m.command == ACT and m.action == TAX:
                self.msg = m
                return
            elif m.command == BLOCK:
                self.msg = m
                return