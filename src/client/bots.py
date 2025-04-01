from proto.game_proto import game_proto, GameMessage
from proto.game_proto import ACT, OK, CHAL, BLOCK, SHOW, LOSE, COINS, DECK, CHOOSE, KEEP, HELLO, PLAYER, START, READY, TURN, EXIT, ILLEGAL
from .game.state_machine import PlayerState, Tag, PlayerSim
from .game.core import *
from .player import Player, InformedPlayer
import random
from loguru import logger



class CoupBot(InformedPlayer):
    """
    CoopBot player class.
    """

    def __init__(self):
        super().__init__()

    def receive(self, message: str) -> int:
        # TODO
        # Implement your bot here

        # Use GameMessage to help reading messages. Example:

        # m = GameMessage(message)
        # command = m.command
        # source = m.ID1
        # card1 = m.card1
        # card2 = m.card2
        # action = m.action
        # target = m.ID2
        # coins = m.coins

        # Use game_proto to create messages. Example:

        # m = game_proto.ACT("1", COUP, "2")
        
        # Put the reply onto the checkout queue. Example:
        # self.checkout.put(m)
        
        raise NotImplementedError
        return 0


class TestBot(InformedPlayer):
    """
    TestBot player class.
    """

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