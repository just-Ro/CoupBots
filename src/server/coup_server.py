from .server import Server, Client
from comms.comms import pop_addr, put_addr
from comms.comms import DISCONNECTION
import socket
import threading


DEFAULT_ADDR = True  # Use default address for messages
ROOT_ADDR = 0

class CoupServer(Server):
    def __init__(self, host="localhost", port=12345, verbose=True):
        super().__init__(host, port, verbose)
        self.broadcast_disconnection = True
        self.disconnection_message = put_addr(DISCONNECTION, str(ROOT_ADDR))

    def route_message(self, sender: Client, addr_message: bytes):
        """Route a message based on its format."""
        addr_message_str = addr_message.decode("utf-8")

        # If the message is not addressed, address it to root
        addr, message_str, invert_addr = pop_addr(addr_message_str)
        if addr is None:
            dest = ROOT_ADDR
        else:
            dest = int(addr)

        if invert_addr:
            # Broadcast to everyone except sender and the client with the specified ID
            self.printv(f"Broadcasting except ID {dest}.")
            self.broadcast_except(sender, message_str, dest)
        else:
            # Direct message to a specific client
            self.printv(f"Sending message to ID {dest}.")
            self.send_to_client(sender, message_str, dest)
            
        
    def broadcast_except(self, sender: Client, message: str, exclude_client_id: int):
        """Broadcast the message to all clients except the sender and optionally exclude a specific client."""
        self.printv(f"Broadcasting from ID {sender.id}: {message}")
        
        # Add origin address to the message
        addr_message = put_addr(message, sender.id)
        
        # Broadcast
        for client in self.connections:
            if client.id != sender.id and client.id != exclude_client_id:
                try:
                    client.socket.sendall(addr_message.encode("utf-8"))
                except OSError:
                    self.remove_client(client)

    def send_to_client(self, sender: Client, message: str, client_id: int):
        """Send a message to a specific client identified by client_id."""
        self.printv(f"Sending message to client {client_id} from ID {sender.id}: {message}")
        
        # Check if client is addressing itself
        if client_id == sender.id:
            self.printv("Client addressed itself.")
            return
        
        # Add origin address to the message
        addr_message = put_addr(message, sender.id)
        
        # Find the client with the specified ID
        for client in self.connections:
            if client.id != sender.id and client.id == client_id:
                try:
                    client.socket.sendall(addr_message.encode("utf-8"))
                except OSError:
                    self.remove_client(client)
                return
        
        # Client not found
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
