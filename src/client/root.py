from comms.comms import Protocol, Parse
from comms.comms import INCOME, FOREIGN_AID, COUP, TAX, ASSASSINATE, STEAL, EXCHANGE, ACTIONS, TARGET_ACTIONS  # Actions
from comms.comms import ASSASSIN, AMBASSADOR, CAPTAIN, DUKE, CONTESSA, CHARACTERS  # Characters
from .player import Player

NO_REPLY = 0
CHOOSE = 1
TURN = 2
SHOW = 3
LOSE = 4
START = 5
ACTION = 6
BLOCK = 7
p = Protocol()

class PlayerState:
    """
    Player state class.
    """

    def __init__(self, id: str, root: "Root"):
        self.id = id
        self.root = root
        self.coins = 0
        self.cards = []
        self.exchange_cards = []
        self.alive = True
        self.turn = False

        # When waiting for a certain reply
        # Possible messages to reply to: NO_REPLY, CHOOSE, TURN, SHOW, LOSE, START, ACTION, BLOCK
        self.reply_to = NO_REPLY
        self.possible_messages = []
    
    
    def generate_answers(self, reply: int, prev_action: str = ""):
        """
        Generates a list of possible messages to send.
        """
        # Update reply_to
        self.reply_to = reply
        
        # If the player is dead or can't reply, they can't send any messages
        if not self.alive or self.reply_to == NO_REPLY:
            self.possible_messages = []
            return
        
        messages = []
        
        # If the player has 10 coins, they can only coup someone
        if self.coins >= 10:
            
            # Target all other players
            for target in self.root.players.values():
                if target != self and target.alive:
                    messages.append(p.ACT(self.id, COUP, target.id))
            
            # Update possible messages
            self.possible_messages = messages
            return
        
        # Choose cards after Exchange action
        if self.reply_to == CHOOSE:
            options = self.cards + self.exchange_cards
            
            # Player only has 1 card left alive
            if len(options) == 2:
                for card in options:
                    messages.append(p.KEEP(card))
                    
            # Player has 2 cards left alive
            elif len(options) == 4:
                for card1 in options:
                    for card2 in options:
                        if card1 != card2:
                            messages.append(p.KEEP(card1, card2))

        # Choose an action to perform on its turn
        elif self.reply_to == TURN and self.turn:
            for action in ACTIONS:
                if action in TARGET_ACTIONS:
                    
                    # Check if the player has enough coins to perform the action
                    if action == COUP and self.coins < 7:
                        continue
                    if action == ASSASSINATE and self.coins < 3:
                        continue
                    
                    # Target all other players
                    for target in self.root.players.values():
                        if target != self and target.alive:
                            messages.append(p.ACT(self.id, COUP, target.id))
        
                else:
                    messages.append(p.ACT(self.id, action))
        
        # Choose a card to show
        elif self.reply_to == SHOW:
            for card in self.cards:
                messages.append(p.SHOW(self.id, card))
        
        # Choose a card to lose
        elif self.reply_to == LOSE:
            for card in self.cards:
                messages.append(p.LOSE(self.id, card))
        
        # Wait for all players to be ready
        elif self.reply_to == START:
            messages.append(p.READY())
        
        # Choose an action to perform in response to another player's action
        elif self.reply_to == ACTION:
            # Allow the action
            messages.append(p.ALLOW(self.id))
            
            # Challenge the action
            if prev_action in (FOREIGN_AID, TAX, ASSASSINATE, STEAL, EXCHANGE):
                messages.append(p.CHAL(self.id))
            
            # Block the action
            if prev_action == FOREIGN_AID:
                messages.append(p.BLOCK(self.id, DUKE))
            elif prev_action == ASSASSINATE:
                messages.append(p.BLOCK(self.id, CONTESSA))
            elif prev_action == STEAL:
                messages.append(p.BLOCK(self.id, CAPTAIN))
                messages.append(p.BLOCK(self.id, AMBASSADOR))
        
        # Choose to either allow or challenge another player's block
        elif self.reply_to == BLOCK:
            messages.append(p.ALLOW(self.id))
            messages.append(p.CHAL(self.id))
        
        # Update possible messages
        self.possible_messages = messages


class TestRoot(Player):
    def __init__(self):
        super().__init__()
        self.verbose = True
        self.is_root = True
        self.players: dict[str, PlayerState] = {}
        self.deck = [*CHARACTERS, *CHARACTERS, *CHARACTERS]
    
    def receive(self, addressed: str):
        orig, message = self.parse_addr(addressed)
        if orig is None:
            print(f"ID?? -> {message}")
            return
        print(f"ID{int(orig):02d} <- {message}")
        
    def send(self, msg: str, dest: str):
        print(f"ID{int(dest):02d} <- {msg}")
        self.checkout.put(self.address_to(msg, dest))
    
    def address_to(self, msg: str, dest: str, invert=False):
        return f"{'-' if invert else ''}{dest}@{msg}"
    
    def parse_addr(self, msg: str):
        if "@" in msg:
            return msg.split("@", 1)
        return None, msg

class Root(Player):
    """
    Root player class.

    This player sends and receives addressed messages, e.g. [orig,dest]message
    """

    def __init__(self):
        super().__init__()
        self.verbose = True
        self.is_root = True
        self.players: dict[str, PlayerState] = {}
        self.deck = [*CHARACTERS, *CHARACTERS, *CHARACTERS]
        
    def receive(self, addressed: str):
        # Split origin address from the message 
        orig, message = self.parse_addr(addressed)
        if orig is None:
            print(f"ID?? -> {message}")
            return
        
        # self.send(message, orig)
        # return
        
        # Parse the message
        try:
            m = Parse(message)
            print(f"ID{orig:02d} -> {message}")
        except SyntaxError:
            # Player message breaks Protocol
            print(f"ID{orig:02d} -> {message}")
            reply = p.ILLEGAL()
            self.send(reply, orig)
            return
        
        # Create a state for the player for the first time
        if m.command == "HELLO":
            if orig not in self.players.keys():
                self.players[orig] = (PlayerState(orig, self))
                reply = p.PLAYER(str(orig))
                self.send(reply, orig)
            return
        
        player = self.players[orig]
        if player is None:
            return
        
        if player.reply_to == NO_REPLY:
            reply = p.ILLEGAL()
            self.send(reply, orig)
            return
        
        if player.reply_to == START:
            if m.command == "READY":
                player.generate_answers(NO_REPLY)
                return
                
            
        
    def send(self, msg: str, dest: str):
        print(f"ID{int(dest):02d} <- {msg}")
        self.checkout.put(self.address_to(msg, dest))
    
    def address_to(self, msg: str, dest: str, invert=False):
        return f"{'-' if invert else ''}{dest}@{msg}"
    
    def parse_addr(self, msg: str):
        if "@" in msg:
            return msg.split("@", 1)
        return None, msg