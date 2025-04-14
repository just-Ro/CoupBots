from server.coup_server import CoupServer
from client.coup_client import CoupClient
from client.root import Root
from loguru import logger
import sys

DEFAULT_ADDR = True  # Use default address for messages
VERBOSE = True

# Remove default logger
logger.remove()

# Configure Terminal logging
if VERBOSE:
    logger.add(sys.stderr, level="SUCCESS", format="<level>{message}</level>", colorize=False, filter=lambda record: record['level'].name == 'SUCCESS')
    logger.add(sys.stderr, level="WARNING", format="<level>{message}</level>", colorize=True)

# Configure File logging
open("../log/server.log", "w").close()  # Clear log file
logger.add(f"../log/server.log", level="TRACE", format="<green>{time:YYYY:MM:DD at HH:mm:ss:SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>")

# Configure Short game summary logging
open("../log/game_summary.log", "w").close()  # Clear log file
logger.add(f"../log/game_summary.log", level="SUCCESS", format="<level>{message}</level>", filter=lambda record: "Player" in record["message"] and "OK" not in record["message"])


if __name__ == "__main__":
    mode = "manual"
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg in ["manual", "auto"]:
            mode = arg
        else:
            print("Invalid argument. Use 'manual' or 'auto'.")
            sys.exit(1)
    
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
    player = Root(mode)
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