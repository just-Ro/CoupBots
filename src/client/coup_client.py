from .client import Client
from .player import Player, Human
import queue


DEFAULT_ADDR = True  # Use default address for messages

class CoupClient(Client):
    def __init__(self, host, port, player: Player):
        super().__init__(host, port)

        # Get console configuration from player
        self.player = player
        self.verbose = player.verbose
        self.ui = player.ui

        # Create a queue for received messages
        self.received_queue = queue.SimpleQueue()

    def addr_root(self, message: str):
        return f"0|{message}"

    def addr_strip(self, message: str):
        return message.split("|", 1)[1]

    def sender(self):
        while self.signal:
            try:

                if not self.received_queue.empty():
                    # Get a message from the queue
                    message = self.received_queue.get()

                    # Receive information/request
                    if not self.player.is_root:
                        # Strip message address
                        message = self.addr_strip(message)
                    self.player.update(message)

                    # Ask player to make a move
                    self.printui("Make your move.")
                    message = self.player.action()

                    # Send the move to the server
                    if message is not None:
                        if not self.player.is_root:
                            # Add the root address
                            message = self.addr_root(message)
                        self.send(message)

            except KeyboardInterrupt:
                self.printv("Keyboard interrupt detected, closing connection.")
                self.signal = False
            except NotImplementedError as e:
                self.printv("Method not implemented yet!")
                e.args = ()
                self.signal = False
            except:
                self.printv("Error in sender")
                self.signal = False

    def receiver(self, message: str):
        self.received_queue.put(message)


def main():
    # Get host and port
    if DEFAULT_ADDR:
        print("Using default address for messages.")
        host = "localhost"
        port = 12345
    else:
        host = input("Host (default 'localhost'): ") or "localhost"
        port = input("Port (default '12345'): ") or "12345"
        port = int(port)  # Ensure port is an integer

    player = Human()
    client = CoupClient(host, port, player)
    client.run()


if __name__ == "__main__":
    main()
