from server.coup_server import CoupServer
from client.coup_client import CoupClient
from client.player import RootPlayer


DEFAULT_ADDR = True  # Use default address for messages
SERVER_VERBOSE = False  # Control all prints from CoupServer


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
    server = CoupServer(host, port, SERVER_VERBOSE)

    # Create client
    player = RootPlayer()
    client = CoupClient(host, port, player)

    try:
        server.start()
        client.run()
        server.shutdown()
    except KeyboardInterrupt:
        server.shutdown()
    except:
        server.shutdown()
        client.signal = False


if __name__ == "__main__":
    main()