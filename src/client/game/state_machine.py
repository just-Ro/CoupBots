from enum import Enum, auto
from proto.game_proto import game_proto, GameMessage
from .core import *


class State(Enum):
    S_IDLE = auto()
    S_START = auto()
    S_TURN = auto()
    S_ACTION = auto()
    S_DO_ACTION = auto()
    S_BLOCK = auto()
    S_CHAL = auto()
    S_END = auto()

class SubState(Enum):
    SS_0 = auto()  # default substate 
    SS_START_COINS = auto()

class PlayerState(Enum):
    IDLE = auto()
    START = auto()
    END = auto()
    R_MY_TURN = auto()
    R_OTHER_TURN = auto()
    R_FAID = auto()
    R_INCOME = auto()
    R_EXCHANGE = auto()
    R_TAX = auto()
    R_ASSASS_ME = auto()
    R_ASSASS = auto()
    R_STEAL_ME = auto()
    R_STEAL = auto()
    R_COUP_ME = auto()
    R_COUP = auto()
    R_BLOCK_FAID = auto()
    R_BLOCK_ASSASS = auto()
    R_BLOCK_STEAL_B = auto()
    R_BLOCK_STEAL_C = auto()
    R_CHAL_A = auto()
    R_CHAL_B = auto()
    R_CHAL_C = auto()
    R_CHAL_D = auto()
    R_CHAL_E = auto()
    R_CHAL_MY_A = auto()
    R_CHAL_MY_B = auto()
    R_CHAL_MY_C = auto()
    R_CHAL_MY_D = auto()
    R_CHAL_MY_E = auto()
    R_LOSE = auto()
    R_SHOW = auto()
    R_COINS = auto()
    R_DECK = auto()
    R_CHOOSE = auto()
    R_PLAYER = auto()

class Tag(Enum):
    T_NONE = auto()
    T_BLOCKING = auto()
    T_BLOCKED = auto()
    T_CHALLENGING = auto()
    T_CHALLENGED = auto()

class PlayerSim:
    """
    Player state class.
    """

    def __init__(self, id: str, players: dict[str, "PlayerSim"]):
        self.id = id
        self.players = players
        self.coins: int = 0
        self.deck: list[str] = []
        self.exchange_cards = []
        self.ready = False
        self.alive = True
        self.turn = False
        self.tag = Tag.T_NONE
        self.state = PlayerState.IDLE
        self.replied = True
        self.possible_messages = []
        self.was_announced = False
        self.msg: GameMessage = GameMessage("OK")
    
    def set_state(self, state: PlayerState):
        self.state = state
        self.possible_messages = self.generate_responses()
    
    def generate_responses(self):
        """
        Generates a list of possible messages to send.
        """
        messages = []

        # If the player is dead or can't reply, they can't send any messages
        if not self.alive or self.state == State.S_IDLE:
            return messages
            
        # Wait for all players to be ready
        if self.state == PlayerState.START:
            messages.append(game_proto.READY())
        
        elif self.state == PlayerState.R_MY_TURN:
            if self.coins < 10:
                
                messages.append(game_proto.ACT(self.id, INCOME))
                messages.append(game_proto.ACT(self.id, FOREIGN_AID))
                messages.append(game_proto.ACT(self.id, TAX))
                messages.append(game_proto.ACT(self.id, EXCHANGE))
                
                for target in self.players.values():
                    if target != self and target.alive:
                        messages.append(game_proto.ACT(self.id, STEAL, target.id))
                
                if self.coins >= 3:
                    for target in self.players.values():
                        if target != self and target.alive:
                            messages.append(game_proto.ACT(self.id, ASSASSINATE, target.id))
            
            if self.coins >= 7:
                for target in self.players.values():
                    if target != self and target.alive:
                        messages.append(game_proto.ACT(self.id, COUP, target.id))
                
        elif self.state == PlayerState.R_OTHER_TURN:
            messages.append(game_proto.OK())
                
        elif self.state == PlayerState.R_FAID:
            messages.append(game_proto.OK())
            messages.append(game_proto.BLOCK(self.id, DUKE))
                
        elif self.state == PlayerState.R_INCOME:
            messages.append(game_proto.OK())

        elif self.state == PlayerState.R_EXCHANGE:
            messages.append(game_proto.OK())
            messages.append(game_proto.CHAL(self.id))
                
        elif self.state == PlayerState.R_TAX:
            messages.append(game_proto.OK())
            messages.append(game_proto.CHAL(self.id))
                
        elif self.state == PlayerState.R_ASSASS_ME:
            messages.append(game_proto.CHAL(self.id))
            messages.append(game_proto.BLOCK(self.id, CONTESSA))
            for card in self.deck:
                messages.append(game_proto.LOSE(self.id, card))
                
        elif self.state == PlayerState.R_ASSASS:
            messages.append(game_proto.OK())
            messages.append(game_proto.CHAL(self.id))
                
        elif self.state == PlayerState.R_STEAL_ME:
            messages.append(game_proto.OK())
            messages.append(game_proto.BLOCK(self.id, CAPTAIN))
            messages.append(game_proto.BLOCK(self.id, AMBASSADOR))
            messages.append(game_proto.CHAL(self.id))
                
        elif self.state == PlayerState.R_STEAL:
            messages.append(game_proto.OK())
            messages.append(game_proto.CHAL(self.id))
                
        elif self.state == PlayerState.R_COUP_ME:
            for card in self.deck:
                messages.append(game_proto.LOSE(self.id, card))
                
        elif self.state == PlayerState.R_COUP:
            messages.append(game_proto.OK())
                
        elif self.state == PlayerState.R_BLOCK_FAID:
            messages.append(game_proto.OK())
            messages.append(game_proto.CHAL(self.id))
                
        elif self.state == PlayerState.R_BLOCK_ASSASS:
            messages.append(game_proto.OK())
            messages.append(game_proto.CHAL(self.id))
                
        elif self.state == PlayerState.R_BLOCK_STEAL_B:
            messages.append(game_proto.OK())
            messages.append(game_proto.CHAL(self.id))
                
        elif self.state == PlayerState.R_BLOCK_STEAL_C:
            messages.append(game_proto.OK())
            messages.append(game_proto.CHAL(self.id))
                
        elif self.state == PlayerState.R_CHAL_A:
            messages.append(game_proto.OK())
                
        elif self.state == PlayerState.R_CHAL_B:
            messages.append(game_proto.OK())
                
        elif self.state == PlayerState.R_CHAL_C:
            messages.append(game_proto.OK())
                
        elif self.state == PlayerState.R_CHAL_D:
            messages.append(game_proto.OK())
                
        elif self.state == PlayerState.R_CHAL_E:
            messages.append(game_proto.OK())
                
        elif self.state == PlayerState.R_CHAL_MY_A:
            for card in self.deck:
                if card == ASSASSIN:
                    messages.append(game_proto.SHOW(self.id, card))
                else:
                    messages.append(game_proto.LOSE(self.id, card))
                
        elif self.state == PlayerState.R_CHAL_MY_B:
            for card in self.deck:
                if card == AMBASSADOR:
                    messages.append(game_proto.SHOW(self.id, card))
                else:
                    messages.append(game_proto.LOSE(self.id, card))
                
        elif self.state == PlayerState.R_CHAL_MY_C:
            for card in self.deck:
                if card == CAPTAIN:
                    messages.append(game_proto.SHOW(self.id, card))
                else:
                    messages.append(game_proto.LOSE(self.id, card))
                
        elif self.state == PlayerState.R_CHAL_MY_D:
            for card in self.deck:
                if card == DUKE:
                    messages.append(game_proto.SHOW(self.id, card))
                else:
                    messages.append(game_proto.LOSE(self.id, card))
                
        elif self.state == PlayerState.R_CHAL_MY_E:
            for card in self.deck:
                if card == CONTESSA:
                    messages.append(game_proto.SHOW(self.id, card))
                else:
                    messages.append(game_proto.LOSE(self.id, card))
                
        elif self.state == PlayerState.R_LOSE:
            messages.append(game_proto.OK())
                
        elif self.state == PlayerState.R_SHOW:
            if self.tag == Tag.T_CHALLENGING:
                for card in self.deck:
                    messages.append(game_proto.LOSE(self.id, card)) 
            else:
                messages.append(game_proto.OK())

        elif self.state == PlayerState.R_COINS:
            messages.append(game_proto.OK())

        elif self.state == PlayerState.R_DECK:
            messages.append(game_proto.OK())
            
        elif self.state == PlayerState.R_CHOOSE:
            options = self.deck + self.exchange_cards
            
            # Player only has 1 card left alive
            if len(options) == 2:
                for card in options:
                    messages.append(game_proto.KEEP(card))
                    
            # Player has 2 cards left alive
            elif len(options) == 4:
                for card1 in options:
                    for card2 in options:
                        if card1 != card2:
                            messages.append(game_proto.KEEP(card1, card2))
        
        elif self.state == PlayerState.R_PLAYER:
            messages.append(game_proto.OK())
        
        return messages
