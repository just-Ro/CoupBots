import threading
import queue
from utils.colored_text import red, green, blue, yellow


class Terminal(threading.Thread):
    def __init__(self, fifo: queue.SimpleQueue, prompt = ""):
        threading.Thread.__init__(self)
        self.daemon = True  # If this is the last active thread, it exits silently
        self.signal = True
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
            print(red(f"Error in Terminal"))
            self.signal = False
        
        
