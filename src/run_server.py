from server.coup_server import CoupServer
from client.coup_client import CoupClient
from client.root import TestRoot, Root
from loguru import logger
import sys
logger.remove()  # Remove default logger
logger.add(sys.stderr, level="SUCCESS", format="<level>{message}</level>", colorize=False, filter=lambda record: record['level'].name == 'SUCCESS')
logger.add(sys.stderr, level="WARNING", format="<level>{message}</level>", colorize=True)
open("../log/server.log", "w").close()  # Clear log file
logger.add(f"../log/server.log", level="TRACE", format="<green>{time: HH:mm:ss:SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>")

DEFAULT_ADDR = True  # Use default address for messages

if __name__ == "__main__":
    # Get host and port
    if DEFAULT_ADDR:
        logger.info("Using default address for messages.")
        host = "localhost"
        port = 12345
    else:
        host = input("Host (default 'localhost'): ") or "localhost"
        port = input("Port (default '12345'): ") or "12345"
        port = int(port)  # Ensure port is an integer

    # Create server instance and start
    server = CoupServer(host, port)

    # Create client
    # player = TestRoot() # Use for manual testing
    player = Root() # Still unfinished
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