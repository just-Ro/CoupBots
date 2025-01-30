from .server import Server, Client
from comms.network_proto import network_proto, NetworkMessage
from comms.network_proto import ALL, SINGLE, EXCEPT, DISCONNECT
from utils.colored_text import red, green, yellow, blue


DEFAULT_ADDR = True  # Use default address for messages
ROOT_ADDR = 0

class CoupServer(Server):
    def __init__(self, host="localhost", port=12345, verbose=True):
        super().__init__(host, port, verbose)
        self.broadcast_disconnection = True
        self.disconnection_message = network_proto.SINGLE(ROOT_ADDR, DISCONNECT)

    def route_message(self, sender: Client, net_msg: bytes):
        """Route a message based on its format."""
        net_msg_str = net_msg.decode("utf-8")

        self.printv(blue(f"Received message from ID {sender.id}: {net_msg_str}"))
        
        # If the message is not addressed, address it to root
        try:
            net = NetworkMessage(net_msg_str)
        except SyntaxError:
            self.printv(yellow("Invalid message format."))
            return
        
        if net.msg is None:
            self.printv(yellow("Empty message."))
            return

        if net.msg_type == SINGLE:
            # Direct message to a specific client
            if net.addr is None:
                self.printv(yellow("No address specified for single message."))
            else:
                self.send_to_client(sender, net.msg, int(net.addr))
                
        elif net.msg_type == EXCEPT:
            # Broadcast to everyone except sender and the client with the specified ID
            if net.addr is None:
                self.printv(yellow("No address specified for except message."))
            else:
                self.broadcast_except(sender, net.msg, int(net.addr))
                
        elif net.msg_type == ALL:
            # Broadcast to everyone except sender
            self.broadcast_except(sender, net.msg, int(sender.id))
            
        
    def broadcast_except(self, sender: Client, message: str, exclude_client_id: int):
        """Broadcast the message to all clients except the sender and optionally exclude a specific client."""
        self.printv(f"Broadcasting from ID {sender.id}: {message}")
        
        # Add origin address to the message
        try:
            net_msg = network_proto.SINGLE(sender.id, message)
        except SyntaxError:
            self.printv(yellow("Invalid message format."))
            return
        
        # Broadcast
        for client in self.connections:
            if client.id != sender.id and client.id != exclude_client_id:
                try:
                    client.socket.sendall(net_msg.encode("utf-8"))
                except OSError:
                    self.remove_client(client)

    def send_to_client(self, sender: Client, message: str, client_id: int):
        """Send a message to a specific client identified by client_id."""
        self.printv(f"Sending message to client {client_id} from ID {sender.id}: {message}")
        
        # Check if client is addressing itself
        if client_id == sender.id:
            self.printv(yellow("Client addressed itself."))
            return
        
        # Add origin address to the message
        try:
            net_msg = network_proto.SINGLE(sender.id, message)
        except SyntaxError:
            self.printv(yellow("Invalid message format."))
            return
        
        # Find the client with the specified ID
        for client in self.connections:
            if client.id != sender.id and client.id == client_id:
                try:
                    client.socket.sendall(net_msg.encode("utf-8"))
                except OSError:
                    self.remove_client(client)
                return
        
        # Client not found
        self.printv(yellow(f"Client with ID {client_id} not found."))


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
