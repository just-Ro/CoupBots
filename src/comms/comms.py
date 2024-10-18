"""
INIT|ID|card1|card2|coins                        // Game Initialization: ID = Player ID, card1 = First card, card2 = Second card, coins = Initial coin count
READY|ID                                         // Player Ready: ID = Player ID
ACT|ID|ACTION|targetID(optional)                 // Player Action: ID = Player ID, ACTION = Action type, targetID = Target Player ID (if applicable)
ALLOW|ID                                         // Allow Action: ID = Player ID allowing an action to proceed (no block, no challenge)
CHAL|ID|targetID|ACTION                          // Challenge Action: ID = Challenger Player ID, targetID = Player performing action, ACTION = Action being challenged
BLOCK|ID|ACTION|CARD                             // Block Action: ID = Blocking Player ID, ACTION = Action being blocked, CARD = Character used to block
SHOW|ID|card                                     // Request Card Reveal: ID = Player ID, card = Character card to reveal
LOSE|ID|card                                     // Lose Influence: ID = Player ID, card = Character card lost
COINS|ID|coins                                   // Update Coins: ID = Player ID, coins = Current coin count
END|winnerID                                     // Game End: winnerID = Player ID of the winner
DECK|ID|card1|card2                              // Inform Player of Current Deck: ID = Player ID, card1 = First card, card2 = Second card
CHOOSE|ID|card1|card2                            // Ask Player to Choose Cards to Exchange: ID = Player ID, card1 = First card to choose, card2 = Second card to choose
KEEP|ID|card1|card2                              // Player Chooses Which 2 Cards to Keep: ID = Player ID, card1 = First card to keep, card2 = Second card to keep

---

### Actions (ACTION code)
I    // Income
F    // Foreign Aid
C    // Coup
T    // Tax (Duke)
A    // Assassinate (Assassin)
S    // Steal (Captain)
X    // Exchange (Ambassador)

### Character Codes (card code)
D    // Duke
A    // Assassin
C    // Contessa
Cp   // Captain
Am   // Ambassador
"""

# Actions
INCOME = "I"
FOREIGN_AID = "F"
COUP = "C"
TAX = "T"
ASSASSINATE = "A"
STEAL = "S"
EXCHANGE = "X"
ACTIONS = (INCOME, FOREIGN_AID, COUP, TAX, ASSASSINATE, STEAL, EXCHANGE)
TARGET_ACTIONS = (COUP, ASSASSINATE, STEAL)

# Characters
ASSASSIN = "A"
AMBASSADOR = "B"
CAPTAIN = "C"
DUKE = "D"
CONTESSA = "E"
CHARACTERS = (DUKE, ASSASSIN, CONTESSA, CAPTAIN, AMBASSADOR)


class Parse:
    def __init__(self, message: str):
        """
        Parse the message into its components.

        Arguments:
            message {_str_} -- message to be parsed

        Raises:
            SyntaxError: If the message violates the protocol
        """
        self.command = None
        self.ID1 = None
        self.card1 = None
        self.card2 = None
        self.action = None
        self.ID2 = None
        self.coins = None
        self.parse(message)

    def parse(self, message: str):

        # Split the message into a list
        list = message.strip().split("|")
        if len(list) < 1:
            raise SyntaxError(f"Bad format in message '{message}': Empty message.")

        # Get the command
        self.command = list[0]

        # Get the command arguments
        if self.command == "INIT":
            if len(list) != 5:
                raise SyntaxError(f"Bad format in message '{message}': expected 5 arguments, got {len(list)}.")
            self.ID1 = list[1]
            self.card1 = list[2]
            self.card2 = list[3]
            self.coins = list[4]

        elif self.command == "READY":
            if len(list) != 1:
                raise SyntaxError(f"Bad format in message '{message}': expected 1 argument, got {len(list)}.")

        elif self.command == "ACT":
            if len(list) < 3:
                raise SyntaxError(f"Bad format in message '{message}': expected at least 3 arguments, got {len(list)}.")
            self.ID1 = list[1]
            self.action = list[2]

            if self.action in TARGET_ACTIONS:
                if len(list) != 4:
                    raise SyntaxError(f"Bad format in message '{message}': expected 4 arguments, got {len(list)}.")
                self.ID2 = list[3]

        elif self.command == "ALLOW":
            if len(list) != 2:
                raise SyntaxError(f"Bad format in message '{message}': expected 2 arguments, got {len(list)}.")
            self.ID1 = list[1]

        elif self.command == "CHAL":
            if len(list) != 2:
                raise SyntaxError(f"Bad format in message '{message}': expected 2 arguments, got {len(list)}.")
            self.ID1 = list[1]

        elif self.command == "BLOCK":
            if len(list) != 3:
                raise SyntaxError(f"Bad format in message '{message}': expected 3 arguments, got {len(list)}.")
            self.ID1 = list[1]
            self.card1 = list[3]

        elif self.command == "SHOW":
            if len(list) != 1:
                if len(list) != 3:
                    raise SyntaxError(f"Bad format in message '{message}': expected 1 or 3 arguments, got {len(list)}.")
                self.ID1 = list[1]
                self.card1 = list[2]

        elif self.command == "LOSE":
            if len(list) != 1:
                if len(list) != 3:
                    raise SyntaxError(f"Bad format in message '{message}': expected 1 or 3 arguments, got {len(list)}.")
                self.ID1 = list[1]
                self.card1 = list[2]

        elif self.command == "COINS":
            if len(list) != 3:
                raise SyntaxError(f"Bad format in message '{message}': expected 3 arguments, got {len(list)}.")
            self.ID1 = list[1]
            self.coins = list[2]

        elif self.command == "END":
            if len(list) != 2:
                raise SyntaxError(f"Bad format in message '{message}': expected 2 arguments, got {len(list)}.")
            self.ID1 = list[1]

        elif self.command == "DECK":
            if len(list) != 2: 
                if len(list) != 3:
                    raise SyntaxError(f"Bad format in message '{message}': expected 2 or 3 arguments, got {len(list)}.")
                self.card2 = list[2]
            self.card1 = list[1]

        elif self.command == "CHOOSE":
            if len(list) != 2: 
                if len(list) != 3:
                    raise SyntaxError(f"Bad format in message '{message}': expected 2 or 3 arguments, got {len(list)}.")
                self.card2 = list[2]
            self.card1 = list[1]

        elif self.command == "KEEP":
            if len(list) != 2: 
                if len(list) != 3:
                    raise SyntaxError(f"Bad format in message '{message}': expected 2 or 3 arguments, got {len(list)}.")
                self.card2 = list[2]
            self.card1 = list[1]

        else:
            raise SyntaxError(f"Bad format in message '{message}': '{self.command}' is not a valid command.")

        if self.action not in ACTIONS and self.action != None:
            raise SyntaxError(f"Bad format in message '{message}': '{self.action}' is not a valid action.")
        if self.card1 not in CHARACTERS and self.card1 != None:
            raise SyntaxError(f"Bad format in message '{message}': '{self.card1}' is not a valid card.")
        if self.card2 not in CHARACTERS and self.card2 != None:
            raise SyntaxError(f"Bad format in message '{message}': '{self.card2}' is not a valid card.")
        if self.ID1 != None and not self.ID1:
            raise SyntaxError(f"Bad format in message '{message}': ID1 is missing.")
        if self.ID2 != None and not self.ID2:
            raise SyntaxError(f"Bad format in message '{message}': ID2 is missing.")
        if self.coins != None and not self.coins:
            raise SyntaxError(f"Bad format in message '{message}': coins is missing.")


class Protocol:
    """
    Protocol class for the game.
    """

    def INIT(self, ID1: str, card1: str, card2: str, coins: int):
        """Game initialization"""
        self.__check__(card1=card1, card2=card2, coins=coins)
        return f"INIT|{ID1}|{card1}|{card2}|{coins}"

    def READY(self):
        """Player ready"""
        return f"READY"

    def ACT(self, ID1: str, ACTION: str, ID2: str = ""):
        """Player action"""
        self.__check__(ACTION=ACTION)
        if ID2:
            return f"ACT|{ID1}|{ACTION}|{ID2}"
        return f"ACT|{ID1}|{ACTION}"

    def ALLOW(self, ID1: str):
        """Allow action"""
        return f"ALLOW|{ID1}"

    def CHAL(self, ID1: str):
        """Challenge action"""
        return f"CHAL|{ID1}"

    def BLOCK(self, ID1: str, card1: str):
        """Block action"""
        self.__check__(card1=card1)
        return f"BLOCK|{ID1}|{card1}"

    def SHOW(self, ID1: str = "", card1: str = ""):
        """Request card reveal"""
        if ID1 and card1:
            self.__check__(card1=card1)
            return f"SHOW|{ID1}|{card1}"
        return f"SHOW"

    def LOSE(self, ID1: str = "", card1: str = ""):
        """Lose influence"""
        if ID1 and card1:
            self.__check__(card1=card1)
            return f"LOSE|{ID1}|{card1}"
        return f"LOSE"

    def COINS(self, ID1: str, coins):
        """Update coins"""
        self.__check__(coins=coins)
        return f"COINS|{ID1}|{coins}"

    def END(self, ID1):
        """Remove player from game"""
        return f"END|{ID1}"

    def DECK(self, card1: str, card2: str = ""):
        """Inform player of current deck"""
        self.__check__(card1=card1)
        if card2:
            self.__check__(card2=card2)
            return f"DECK|{card1}|{card2}"
        return f"DECK|{card1}"

    def CHOOSE(self, card1: str, card2: str = ""):
        """Ask player to choose cards to exchange"""
        self.__check__(card1=card1)
        if card2:
            self.__check__(card2=card2)
            return f"CHOOSE|{card1}|{card2}"
        return f"CHOOSE|{card1}"

    def KEEP(self, card1: str, card2: str = ""):
        """Player chooses which 2 cards to keep"""
        self.__check__(card1=card1)
        if card2:
            self.__check__(card2=card2)
            return f"KEEP|{card1}|{card2}"
        return f"KEEP|{card1}"

    def __check__(self, ACTION=None, card1=None, card2=None, coins=None):
        """
        Check the validity of the message components.

        Keyword Arguments:
            ACTION {_str_ | None} -- action
            card1 {_str_ | None} -- card1
            card2 {_str_ | None} -- card2
            coins {_int_ | None} -- coins

        Raises:
            SyntaxError: If at least one of the given arguments violates the protocol
        """
        if ACTION and ACTION not in ACTIONS:
            raise SyntaxError(f"Bad format in message: '{ACTION}' is not a valid action.")
        if card1 and card1 not in CHARACTERS:
            raise SyntaxError(f"Bad format in message: '{card1}' is not a valid card.")
        if card2 and card2 not in CHARACTERS:
            raise SyntaxError(f"Bad format in message: '{card2}' is not a valid card.")
        if coins and not (isinstance(coins, int) and coins >= 0):
            raise SyntaxError(f"Bad format in message: '{coins}' is not a valid coin count.")


# Testing purposes
if __name__ == "__main__":

    # Test the Protocol class
    p = Protocol()
    try:
        print(p.INIT("P1", "D", "Cp", 2))
    except SyntaxError as e:
        print(e)

    # Testing the Parse class
    message = "ACT|P1|C|P2"
    try:
        m = Parse(message)
        print(m.command)
        print(m.ID1)
        print(m.card1)
        print(m.card2)
        print(m.action)
        print(m.ID2)
        print(m.coins)
    except SyntaxError as e:
        print(e)
