

class Verbose:
    def __init__(self):
        self.verbose = True
        self.ui = True
        
    def printv(self, string: str):
        if self.verbose:
            print(f"[{str(self.__class__.__name__)}] {string}")

    def printui(self, string: str):
        if self.ui:
            print(string)