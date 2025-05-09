#!/usr/bin/env python3.12

import subprocess
import time
import argparse
import sys

SLEEP_TIME = 0.5  # seconds

process_calls = ["python run_server.py -m auto", 
                 "python run_bot.py -i 1 -v", 
                 "python run_bot.py -i 2 -v", 
                 "python run_bot.py -i 3 -v", 
                 "python run_bot.py -i 4 -v", 
                 "python run_bot.py -i 5 -v", 
                 "python run_bot.py -i 6 -v"]

def game(terminal: bool):
    # Determine where to send subprocess output
    output = None if terminal else subprocess.DEVNULL
    # print("Starting server and bots...")
    server_process = subprocess.Popen(process_calls[0].split(" "), stdout=output, stderr=output)
    # print("Starting server...")

    bot_processes: list[subprocess.Popen[bytes]] = []
    time.sleep(SLEEP_TIME)
    for i in range(1,7):
        bot_processes.append(subprocess.Popen(process_calls[i].split(" "), stdout=output, stderr=output))
        # print(f"Starting bot {i}...")
    
    start_time = time.time()
    
    # Wait for all processes to finish
    # print("Running simulation...")
    server_process.wait()
    for bot_process in bot_processes:
        bot_process.wait()
    
    end_time = time.time()
    print(f"Simulation completed in {end_time - start_time - SLEEP_TIME:.2f} seconds.")
    # Check if the server finished successfully
    if server_process.returncode != 0:
        print("Server process failed")
    
    # Check if the bots finished successfully
    for i, bot_process in enumerate(bot_processes):
        if bot_process.returncode != 0:
            print(f"Bot process {i} failed")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-j', type=int, default=1, help='Number of games to run (default: 1)')
    parser.add_argument('-o', action='store_true', help='Output to terminal (default: False)')
    args = parser.parse_args()
    
    start_time = time.time()
    for i in range(args.j):
        print(f"Game {i+1}/{args.j}: ", end="")
        game(args.o)
        time.sleep(SLEEP_TIME)
    end_time = time.time()
    print(f"All games completed in {end_time - start_time:.2f} seconds.")