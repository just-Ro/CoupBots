from comms.comms import Protocol, Parse
from comms.comms import INCOME, FOREIGN_AID, COUP, TAX, ASSASSINATE, STEAL, EXCHANGE, ACTIONS, TARGET_ACTIONS  # Actions
from comms.comms import ASSASSIN, AMBASSADOR, CAPTAIN, DUKE, CONTESSA, CHARACTERS  # Characters
from comms.comms import put_addr, pop_addr
from .player import Player
import random

IDLE = 0
CHOOSE = 1
TURN = 2
SHOW = 3
LOSE = 4
START = 5
ACTION = 6
BLOCK = 7
CHAL = 8
END = 9

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
        self.ready = False
        self.alive = True
        self.turn = False

        # When waiting for a certain reply
        # Possible messages to reply to: IDLE, CHOOSE, TURN, SHOW, LOSE, START, ACTION, BLOCK
        self.state = IDLE
        self.possible_messages = []
    
    
    def generate_answers(self, reply: int, prev_action: str = ""):
        """
        Generates a list of possible messages to send.
        """
        # Update reply_to
        self.state = reply
        
        # If the player is dead or can't reply, they can't send any messages
        if not self.alive or self.state == IDLE:
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
        if self.state == CHOOSE:
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
        elif self.state == TURN and self.turn:
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
        elif self.state == SHOW:
            for card in self.cards:
                messages.append(p.SHOW(self.id, card))
        
        # Choose a card to lose
        elif self.state == LOSE:
            for card in self.cards:
                messages.append(p.LOSE(self.id, card))
        
        # Wait for all players to be ready
        elif self.state == START:
            messages.append(p.OK())
        
        # Choose an action to perform in response to another player's action
        elif self.state == ACTION:
            # Allow the action
            messages.append(p.OK())
            
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
        elif self.state == BLOCK:
            messages.append(p.OK())
            messages.append(p.CHAL(self.id))
        
        # Update possible messages
        self.possible_messages = messages


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
        self.state = IDLE
        
    def receive(self, addressed: str):
        # Split origin address from the message 
        orig, message, _ = pop_addr(addressed)
        if orig is None:
            self.printv(f"\033[31mID?? -> {message}\033[m")
            return
        
        # Parse the message
        try:
            m = Parse(message)
            self.printv(f"ID{orig:02d} -> {message}")
        except SyntaxError:
            # Player message breaks Protocol
            self.printv(f"\033[31mID{orig:02d} -> {message}\033[m")
            self.send(p.ILLEGAL(), orig)
            return
        
        # Main state machine
        if self.state == IDLE:
            
            if m.command == "HELLO":
                # Create a state for the player for the first time
                if orig not in self.players.keys():
                    self.players[orig] = (PlayerState(orig, self))
                    self.send(p.PLAYER(str(orig)), orig)
                
            else:
                player = self.players[orig]
                if player is None:
                    return
                elif player.state == IDLE:
                    self.send(p.ILLEGAL(), orig)
                    return
                
                if player.state == START:
                    if m.command == "READY":
                        player.ready = True
                        player.generate_answers(IDLE)
                        return
                
                for player in self.players.values():
                    if not player.ready:
                        return

        elif self.state == TURN:
            pass
        elif self.state == ACTION:
            pass
        elif self.state == BLOCK:
            pass
        elif self.state == CHAL:
            pass
        elif self.state == END:
            pass
    
    def next_state(self):
        pass
    
    def put_card(self, deck: list[str], card: str):
        deck.append(card)

    def take_card(self, deck: list[str]):
        if deck:  # Check if deck is not empty
            return deck.pop(random.randint(0, len(deck) - 1))
        return None  # Return None if deck is empty
            
    def send(self, msg: str, dest: str):
        self.printv(f"ID{int(dest):02d} <- {msg}")
        self.checkout.put(put_addr(msg, dest))


class TestRoot(Player):
    def __init__(self):
        super().__init__()
        self.verbose = True
        self.is_root = True
        self.players: dict[str, PlayerState] = {}
        self.deck = [*CHARACTERS, *CHARACTERS, *CHARACTERS]
    
    def receive(self, addressed: str):
        orig, message, _ = pop_addr(addressed)
        if orig is None:
            self.printv(f"ID?? -> {message}")
            return
        self.printv(f"ID{int(orig):02d} -> {message}")
        
    def send(self, msg: str, dest: str):
        self.printv(f"ID{int(dest):02d} <- {msg}")
        self.checkout.put(put_addr(msg, dest))
    