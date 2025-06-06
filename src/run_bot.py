#!/usr/bin/env python3.12

from client.coup_client import CoupClient
from client.bots import CoupBot, TestBot, RandomBot, HonestBot
from loguru import logger
import argparse
import sys, os

BOTS = {
    "CoupBot": CoupBot,
    "TestBot": TestBot,
    "RandomBot": RandomBot,
    "HonestBot": HonestBot,
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', type=int, default=12345, help='Port number (default: 12345)')
    parser.add_argument('-a', type=str, default='localhost', help='Address (default: localhost)')
    parser.add_argument('-i', type=str, default='None', help="Player ID (default: None)")
    parser.add_argument('-v', action='store_false', help='Verbose mode (default: True)')
    parser.add_argument('-b', type=str, default='TestBot', help='Bot type (default: TestBot)', choices=BOTS.keys())
    args = parser.parse_args()
    
    logger.remove()  # Remove default logger
    if args.v:
        logger.add(sys.stderr, level="SUCCESS", format="<level>{message}</level>", colorize=False, filter=lambda record: record['level'].name == 'SUCCESS')
        logger.add(sys.stderr, level="WARNING", format="<level>{message}</level>", colorize=True)

    # Configure File logging
    if not os.path.exists("../log"):
        os.makedirs("../log")
    if args.i != "None":
        open(f"../log/bot_{args.i}.log", "w").close()   # clear log file if it exists
        logger.add(f"../log/bot_{args.i}.log", 
                   level="TRACE", 
                   format="<green>{time:HH:mm:ss:SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>")

    # Create client
    player = BOTS[args.b]()
    client = CoupClient(args.a, args.p, player)
    client.run()