from comms.game_proto import INCOME, FOREIGN_AID, COUP, TAX, ASSASSINATE, STEAL, EXCHANGE, ACTIONS, TARGET_ACTIONS  # Actions
from comms.game_proto import ASSASSIN, AMBASSADOR, CAPTAIN, DUKE, CONTESSA, CHARACTERS  # Characters
from comms.game_proto import game_proto, GameMessage
from comms.game_proto import ACT, OK, CHAL, BLOCK, SHOW, LOSE, COINS, DECK, CHOOSE, KEEP, HELLO, PLAYER, START, READY, TURN, ILLEGAL
from .player import Player


class CoupBot(Player):
    """
    CoopBot player class.
    """

    def __init__(self):
        super().__init__()
        self.verbose = True  # Error messages and connection status
        self.ui = False  # User interface like input prompts

    def receive(self, message: str):
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


