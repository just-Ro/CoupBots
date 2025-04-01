import threading
import queue
from loguru import logger


class Terminal(threading.Thread):
    def __init__(self, fifo: queue.SimpleQueue, prompt = ""):
        threading.Thread.__init__(self)
        self.daemon = True  # If this is the last active thread, it exits silently
        self.signal = fifo is not None  # If fifo is None, the thread will not run
        self.fifo = fifo
        self.prompt = prompt
        self.start()
    
    def run(self):
        try:
            while self.signal:
                message = input(self.prompt)
                self.fifo.put(message)
        except (KeyboardInterrupt, EOFError):
            self.signal = False
        except:
            logger.error(f"Error in Terminal")
            self.signal = False
        
        
