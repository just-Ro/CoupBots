from .server import Server, Client
import socket
import threading


DEFAULT_ADDR = True  # Use default address for messages


class CoupServer(Server):
    def __init__(self, host="localhost", port=12345, verbose=True):
        super().__init__(host, port, verbose)

    def route_message(self, sender: Client, message: bytes):
        """Route a message based on its format."""
        message_str = message.decode("utf-8")
        parts = message_str.split("|", 1)

        # If the first part is an integer, process it accordingly
        try:
            first_part = int(parts[0])

            # Direct message to a specific client
            if first_part >= 0:
                self.printv(f"Sending message to ID {first_part}.")
                self.send_to_client(first_part, sender, message)
            # Broadcast to everyone except sender and the client with the specified ID
            else:
                self.printv(f"Broadcasting except ID {first_part}.")
                self.broadcast_except(sender, message, exclude_client_id=abs(first_part))
        except ValueError:
            # If the first part is not an integer, it's a normal broadcast
            self.printv("Untagged message. Broadcasting.")
            self.broadcast_except(sender, message)

    def broadcast_except(self, sender: Client, message: bytes, exclude_client_id=None):
        """Broadcast the message to all clients except the sender and optionally exclude a specific client."""
        self.printv(f"Broadcasting from ID {sender.id}: {message.decode('utf-8')}")
        for client in self.connections:
            if client.id != sender.id and client.id != exclude_client_id:
                try:
                    client.socket.sendall(message)
                except OSError:
                    self.remove_client(client)

    def send_to_client(self, client_id: int, sender: Client, message: bytes):
        """Send a message to a specific client identified by client_id."""
        self.printv(f"Sending message to client {client_id} from ID {sender.id}: {message}")
        if client_id == sender.id:
            self.printv("Client addressed itself.")
            return
        for client in self.connections:
            if client.id != sender.id and client.id == client_id:
                try:
                    client.socket.sendall(message)
                except OSError:
                    self.remove_client(client)
                return
        self.printv(f"Client with ID {client_id} not found.")


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

    # Create server instance and start
    server = Server(host, port)
    server.start()

    try:
        while True:
            pass  # Main thread is idle, just to catch the KeyboardInterrupt
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
