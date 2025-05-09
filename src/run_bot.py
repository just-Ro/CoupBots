#!/usr/bin/env python3.12

from client.coup_client import CoupClient
from client.bots import CoupBot, TestBot
from loguru import logger
import sys

DEFAULT_ADDR = False  # Use default address for messages
VERBOSE = True

logger.remove()  # Remove default logger
if VERBOSE:
    logger.add(sys.stderr, level="SUCCESS", format="<level>{message}</level>", colorize=False, filter=lambda record: record['level'].name == 'SUCCESS')
    logger.add(sys.stderr, level="WARNING", format="<level>{message}</level>", colorize=True)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        bot_id = sys.argv[1]
        # clear log file if it exists
        open(f"../log/bot_{bot_id}.log", "w").close()
        logger.add(f"../log/bot_{bot_id}.log", 
                   level="TRACE", 
                   format="<green>{time:HH:mm:ss:SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>")
    
    # Get host and port
    if DEFAULT_ADDR:
        logger.info("Using default address for messages.")
        host = "localhost"
        port = 12345
    else:
        host = input("Host (default 'localhost'): ") or "localhost"
        port = input("Port (default '12345'): ") or "12345"
        port = int(port)  # Ensure port is an integer

    # Create client
    player = TestBot()
    client = CoupClient(host, port, player)
    client.run()