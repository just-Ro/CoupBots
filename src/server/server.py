import socket
import threading
from utils.colored_text import red, green, yellow, blue
from utils.verbose import Verbose


CLIENT_TIMEOUT = 1.0  # Timeout for client socket
SERVER_TIMEOUT = 1.0  # Timeout for server socket
MAX_CONNECTIONS = 5  # Maximum number of connections
DEFAULT_ADDR = True  # Use default address for messages


# Client class, new instance created for each connected client
class Client(threading.Thread, Verbose):
    def __init__(self, socket: socket.socket, address, id, name, signal, server: "Server", verbose=True):
        threading.Thread.__init__(self)
        self.socket = socket
        self.address = address
        self.verbose = verbose
        self.id = id
        self.name = name
        self.signal = signal
        self.server = server  # Reference to the server to forward received messages
        self.socket.settimeout(CLIENT_TIMEOUT)  # Set a short timeout (1 second) for recv()

    def __str__(self):
        return str(self.id) + " " + str(self.address)

    def run(self):
        while self.signal:
            try:
                data = self.socket.recv(32)
                if data:
                    # Pass the received data to the server for broadcasting
                    self.server.route_message(self, data)
                else:
                    self.printv(f"Client {self.id} has disconnected")
                    self.signal = False
                    if self.server.broadcast_disconnection:
                        self.printv("Broadcasting disconnection message.")
                        self.server.route_message(self, self.server.disconnection_message.encode("utf-8"))
                    self.server.remove_client(self)
                    break
            except (socket.timeout, UnicodeDecodeError):
                continue
            except OSError:
                self.printv(f"Client {self.id} has disconnected")
                self.signal = False
                if self.server.broadcast_disconnection:
                    self.printv("Broadcasting disconnection message.")
                    self.server.route_message(self, self.server.disconnection_message.encode("utf-8"))
                self.server.remove_client(self)
                break



class Server(threading.Thread, Verbose):
    def __init__(self, host="localhost", port=12345, verbose=True):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.verbose = verbose
        self.socket = None
        self.signal = True
        self.connections: list[Client] = []  # Store connected clients
        self.total_connections = 0  # Count the total connections
        self.broadcast_disconnection = False
        self.disconnection_message = ""

    def setup_socket(self):
        """Setup the server socket, bind, and listen for connections."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(MAX_CONNECTIONS)
        self.socket.settimeout(SERVER_TIMEOUT)  # Add a timeout so the accept loop can regularly check for shutdown
        self.printv(green(f"Server listening on {self.host}:{self.port}"))

    def run(self):
        self.setup_socket()

        # Wait for new connections
        while self.signal:
            try:
                if self.socket is None:
                    self.signal = False
                    break
                sock, address = self.socket.accept()
                # TODO: assign the first available client id 
                new_client = Client(sock, address, self.total_connections, "Name", True, self, self.verbose)
                self.connections.append(new_client)
                new_client.start()
                self.printv(green(f"New connection at ID {new_client}"))
                self.total_connections += 1
            except OSError:
                continue

    def route_message(self, sender: Client, message: bytes):
        """Broadcast a message from the sender to all other connected clients."""
        self.printv(f"Broadcasting from ID {sender.id}: {message.decode('utf-8')}")
        for client in self.connections:
            if client.id != sender.id:  # Do not send the message back to the sender
                try:
                    client.socket.sendall(message)
                except OSError:
                    self.remove_client(client)

    def remove_client(self, client: Client):
        """Helper method to remove a client from the server's connection list."""
        if client in self.connections:
            self.connections.remove(client)
            self.printv(f"Client {client.address} removed from server.")

    def shutdown(self):
        """Gracefully shut down the server and all client connections."""
        self.printv("\nServer shutting down...")

        # Clean up: close the main server socket
        if self.socket:
            self.socket.close()

        # Signal all threads to finish
        self.signal = False
        self.join()

        for client in self.connections:
            client.signal = False
            client.join()

        self.printv("Server terminated.")


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
    except:
        server.shutdown()


if __name__ == "__main__":
    main()
