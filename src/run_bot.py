from client.coup_client import CoupClient
from client.bots import CoupBot, TestBot
from utils.print_logger import log_to_file, disable_logging
import sys


DEFAULT_ADDR = True  # Use default address for messages

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

    # Create client
    # player = CoupBot()
    player = TestBot()
    client = CoupClient(host, port, player)
    client.run()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        bot_number = sys.argv[1]
        log_to_file(f"../log/bot{bot_number}.ans")
    main()
