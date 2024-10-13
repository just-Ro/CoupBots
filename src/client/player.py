from comms.comms import Protocol, Parse
from comms.comms import INCOME, FOREIGN_AID, COUP, TAX, ASSASSINATE, STEAL, EXCHANGE, ACTIONS, TARGET_ACTIONS  # Actions
from comms.comms import ASSASSIN, AMBASSADOR, CAPTAIN, DUKE, CONTESSA, CHARACTERS  # Characters


class Player:
    """
    Abstract class for a player in the game.
    """

    def __init__(self):
        self.verbose = True
        self.ui = False
        self.is_root = False

    def action(self):
        """
        Asks the player for a move and returns it.
        Always called after update().

        Returns:
            _str_ | None -- message with the player's move
        """

        raise NotImplementedError

    def update(self, message: str):
        """
        Informs the player of a message.
        Here, the player can update its knowledge and possibly plan the next move.

        Arguments:
            message {_str_} -- request/informative message

        """
        raise NotImplementedError


class Human(Player):
    """
    Human player class.
    """

    def __init__(self):
        super().__init__()
        self.ui = True

    def action(self):
        while True:
            try:
                message = input("> ")
                Parse(message)
                return message
            except SyntaxError as e:
                print(e)

    def update(self, message: str):
        print(message)


class RootPlayer(Player):
    """
    Root player class.

    This player sends and receives addressed messages, e.g. addr|message
    """

    def __init__(self):
        super().__init__()
        self.verbose = True
        self.ui = False
        self.is_root = True
        self.msg = ""

    def action(self):
        # Simple echo for testing purposes
        print(f"echo '{self.msg}'")
        return self.msg

    def update(self, message: str):
        self.msg = message
