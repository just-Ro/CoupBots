from .client import Client
from .player import Player, Human


DEFAULT_ADDR = True  # Use default address for messages
ROOT_ADDR = 0

class CoupClient(Client):
    def __init__(self, host, port, player: Player):
        super().__init__(host, port)

        # Get console configuration from player
        self.player = player
        self.verbose = player.verbose
        self.ui = player.ui

        

    def addr_root(self, message: str):
        return f"{ROOT_ADDR}@{message}"

    def addr_strip(self, message: str):
        return message.split("@")[1]

    def sender(self):
        try:
            while self.signal:
                message = self.player.sender()

                # Send the move to the server
                if message:
                    if not self.player.is_root:
                        # Add the root address
                        message = self.addr_root(message)
                    self.send(message)
                    
        except KeyboardInterrupt:
            self.printv("Keyboard interrupt detected, closing connection.")
        except NotImplementedError:
            self.printv("Method not implemented yet!")
        except:
            self.printv("Error in sender")
        self.signal = False

    def receiver(self, message: str):
        try:
            # Strip message address
            if not self.player.is_root:
                message = self.addr_strip(message)
            self.player.receive(message)
            
        except NotImplementedError:
            self.printv("Method not implemented yet!")
            self.signal = False
        except Exception as e:
            self.printv(f"Error in receiver: {e}")
            self.signal = False


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
