#!/usr/bin/env python3.12

from server.coup_server import CoupServer
from client.coup_client import CoupClient
from client.root import Root
from loguru import logger
import argparse
import sys


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', type=int, default=12345, help='Port number (default: 12345)')
    parser.add_argument('-a', type=str, default='localhost', help='Address (default: localhost)')
    parser.add_argument('-m', choices=['manual', 'auto'], default='manual', help="Mode of operation: 'manual' or 'auto' (default: manual)")
    parser.add_argument('-v', action='store_false', help='Verbose mode (default: True)')
    args = parser.parse_args()
    
    # Remove default logger
    logger.remove()
    
    # Configure Terminal logging
    if args.v:
        logger.add(sys.stderr, level="SUCCESS", format="<level>{message}</level>", colorize=False, filter=lambda record: record['level'].name == 'SUCCESS')
        logger.add(sys.stderr, level="WARNING", format="<level>{message}</level>", colorize=True)

    # Configure File logging
    open("../log/server.log", "w").close()  # Clear log file
    logger.add(f"../log/server.log", level="TRACE", format="<green>{time:YYYY:MM:DD at HH:mm:ss:SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>")

    # Configure Short game summary logging
    open("../log/game_summary.log", "w").close()  # Clear log file
    logger.add(f"../log/game_summary.log", level="SUCCESS", format="<level>{message}</level>", filter=lambda record: "Player" in record["message"] and "OK" not in record["message"])

    # Create server instance and start
    server = CoupServer(args.a, args.p)

    # Create client
    player = Root(args.m)
    client = CoupClient(args.a, args.p, player)

    try:
        server.start()
        client.run()
        server.shutdown()
    except KeyboardInterrupt:
        server.shutdown()
    except:
        server.shutdown()
        client.signal = False