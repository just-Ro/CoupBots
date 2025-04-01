from proto.game_proto import GameMessage
from terminal.terminal import Terminal
from .player import InformedPlayer
from queue import SimpleQueue
import sys, threading


class Human(InformedPlayer):
    """
    Human player class.
    """

    def __init__(self):
        super().__init__(KeepAlive())
        
    def choose_message(self):
        if len(self.possible_messages) == 1:
            self.msg = GameMessage(self.possible_messages[0])
            return
        print("Choose a reply: ", end="")
        print(str(self.possible_messages).strip("[]").replace("'", ""))
        msg = input("> ").strip()
        while msg not in self.possible_messages:
            print("Invalid reply. Choose again:")
            print(str(self.possible_messages).strip("[]").replace("'", ""))
            msg = input("> ").strip()
        self.msg = GameMessage(msg)


class KeepAlive(Terminal):
    """
    KeepAlive thread class.
    """

    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True  # If this is the last active thread, it exits silently
        self.signal = True
        self.start()

    def run(self):
        return