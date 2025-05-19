#!/usr/bin/env python3.12

from client.coup_client import CoupClient
from client.human import Human
from loguru import logger
import argparse
import sys, os


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', type=int, default=12345, help='Port number (default: 12345)')
    parser.add_argument('-a', type=str, default='localhost', help='Address (default: localhost)')
    parser.add_argument('-i', type=str, default='None', help="Player ID (default: None)")
    args = parser.parse_args()
    
    logger.remove()  # Remove default logger
    logger.add(sys.stderr, level="SUCCESS", format="<level>{message}</level>", colorize=False, filter=lambda record: record['level'].name == 'SUCCESS')
    logger.add(sys.stderr, level="WARNING", format="<level>{message}</level>", colorize=True)

    # Configure File logging 
    if not os.path.exists("../log"):
        os.makedirs("../log")
    if args.i != "None":
        open(f"../log/human_{args.i}.log", "w").close()   # clear log file if it exists
        logger.add(f"../log/human_{args.i}.log", 
                   level="TRACE", 
                   format="<green>{time:HH:mm:ss:SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>")

    # Create client
    player = Human()
    client = CoupClient(args.a, args.p, player)
    client.run()