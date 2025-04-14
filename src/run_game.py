import subprocess
import time
SLEEP_TIME = 0.05  # seconds
TERMINAL_OUTPUT = False
JOBS = 10

process_calls = ["python run_server.py auto", 
             "python run_bot.py 1", 
             "python run_bot.py 2", 
             "python run_bot.py 3", 
             "python run_bot.py 4", 
             "python run_bot.py 5", 
             "python run_bot.py 6"]

def game():
    # Determine where to send subprocess output
    output = None if TERMINAL_OUTPUT else subprocess.DEVNULL
    # print("Starting server and bots...")
    server_process = subprocess.Popen(process_calls[0].split(" "), stdout=output, stderr=output)
    # print("Starting server...")

    bot_processes: list[subprocess.Popen[bytes]] = []
    for i in range(1,7):
        time.sleep(SLEEP_TIME)
        bot_processes.append(subprocess.Popen(process_calls[i].split(" "), stdout=output, stderr=output))
        # print(f"Starting bot {i}...")
    
    start_time = time.time()
    
    # Wait for all processes to finish
    # print("Running simulation...")
    server_process.wait()
    for bot_process in bot_processes:
        bot_process.wait()
    
    end_time = time.time()
    print(f"Simulation completed in {end_time - start_time:.2f} seconds.")
    # Check if the server finished successfully
    if server_process.returncode != 0:
        print("Server process failed")
    
    # Check if the bots finished successfully
    for i, bot_process in enumerate(bot_processes):
        if bot_process.returncode != 0:
            print(f"Bot process {i} failed")

if __name__ == "__main__":
    start_time = time.time()
    for i in range(JOBS):
        print(f"Game {i+1}/{JOBS}: ", end="")
        game()
        time.sleep(SLEEP_TIME)
    end_time = time.time()
    print(f"All games completed in {end_time - start_time:.2f} seconds.")