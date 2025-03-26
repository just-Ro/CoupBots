import sys

_backup = sys.stdout

class Tee(object):
    def __init__(self, *files):
        self.files = files
        
    def write(self, obj):
        for f in self.files:
            f.write(obj)
    
    def flush(self):
        for f in self.files:
            f.flush()

def disable_logging():
    """
    disable_logging disables logging to all files except for stdout.
    """
    if isinstance(sys.stdout, Tee):
        for f in sys.stdout.files:
            f.close
    sys.stdout = _backup

def log_to_file(file: str):
    """
    log_to_file logs all prints to a file.

    Arguments:
        file {str} -- The file path to log to.
    """
    
    f = open(file, 'w')
    sys.stdout = Tee(sys.stdout, f)
   