from comms.comms import Protocol, Parse
from comms.comms import INCOME, FOREIGN_AID, COUP, TAX, ASSASSINATE, STEAL, EXCHANGE, ACTIONS, TARGET_ACTIONS  # Actions
from comms.comms import ASSASSIN, AMBASSADOR, CAPTAIN, DUKE, CONTESSA, CHARACTERS  # Characters
from terminal.terminal import Terminal
import queue


class Player:
    """
    Abstract class for a player in the game.
    """
    
    def __init__(self):
        self.verbose = True
        self.ui = False
        self.is_root = False
        
        # Create a queue to send messages
        self.checkout = queue.SimpleQueue()
        
        # Create a terminal to write messages manually
        self.term = Terminal(self.checkout)
    
    def sender(self):
        """
        Gets a message from checkout and returns it.

        Returns:
            _str_ | None -- message
        """
        try:
            # Check if the terminal thread finished
            if not self.term.signal:
                print("Terminal closed.")
                raise KeyboardInterrupt
            
            return self.checkout.get(timeout=0.5)
        except queue.Empty:
            print(end="")   # weird way to update the console buffer
            return None

    def receive(self, message: str):
        """
        Informs the player of a message.
        Here, the player may or may not reply to the message.

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
        self.verbose = True
        self.ui = True
        self.checkout.put("HELLO")
        
    def receive(self, message: str):
        print(message)
