from .protobase import MsgType, MsgArg, Proto, BaseMsg
from client.game.core import ACTIONS, CHARACTERS


# Message types
ACT = "ACT"
OK = "OK"
CHAL = "CHAL"
BLOCK = "BLOCK"
SHOW = "SHOW"
LOSE = "LOSE"
COINS = "COINS"
DECK = "DECK"
CHOOSE = "CHOOSE"
KEEP = "KEEP"
HELLO = "HELLO"
PLAYER = "PLAYER"
START = "START"
READY = "READY"
TURN = "TURN"
EXIT = "EXIT"
ILLEGAL = "ILLEGAL"

def _check_action(action):
    return str(action).isalpha() and action in ACTIONS

def _check_card(card):
    return str(card).isalpha() and card in CHARACTERS

def _check_coins(coins):
    return str(coins).isnumeric() and int(coins) >= 0

def _check_id(id):
    return str(id).isnumeric()

class GameProto(Proto):
    def __init__(self):
        super().__init__(
            MsgType(ACT, 
                MsgArg("ID1", _check_id), 
                MsgArg("action", _check_action), 
                MsgArg("ID2", _check_id, False)),

            MsgType(OK),

            MsgType(CHAL, 
                MsgArg("ID1", _check_id)),

            MsgType(BLOCK, 
                MsgArg("ID1", _check_id), 
                MsgArg("card1", _check_card)),

            MsgType(SHOW, 
                MsgArg("ID1", _check_id, False), 
                MsgArg("card1", _check_card, False)),

            MsgType(LOSE, 
                MsgArg("ID1", _check_id, False), 
                MsgArg("card1", _check_card, False)),

            MsgType(COINS, 
                MsgArg("ID1", _check_id), 
                MsgArg("coins", _check_coins)),

            MsgType(DECK, 
                MsgArg("card1", _check_card, False), 
                MsgArg("card2", _check_card, False)),

            MsgType(CHOOSE, 
                MsgArg("card1", _check_card), 
                MsgArg("card2", _check_card, False)),

            MsgType(KEEP, 
                MsgArg("card1", _check_card), 
                MsgArg("card2", _check_card, False)),

            MsgType(HELLO),

            MsgType(PLAYER, 
                MsgArg("ID1", _check_id)),

            MsgType(START),

            MsgType(READY),

            MsgType(TURN, 
                MsgArg("ID1", _check_id)),
            
            MsgType(EXIT),
            
            MsgType(ILLEGAL)
        )
        self.sep = ' '
        self.term = ''

    ## helpers

    def ACT(self, ID1, action, ID2=None):
        return self.serialize(ACT, {"ID1": ID1, "action": action, "ID2": ID2})
    
    def OK(self):
        return self.serialize(OK, {})
    
    def CHAL(self, ID1):
        return self.serialize(CHAL, {"ID1": ID1})
    
    def BLOCK(self, ID1, card1):
        return self.serialize(BLOCK, {"ID1": ID1, "card1": card1})
    
    def SHOW(self, ID1=None, card1=None):
        return self.serialize(SHOW, {"ID1": ID1, "card1": card1})
    
    def LOSE(self, ID1=None, card1=None):
        return self.serialize(LOSE, {"ID1": ID1, "card1": card1})
    
    def COINS(self, ID1, coins):
        return self.serialize(COINS, {"ID1": ID1, "coins": coins})
    
    def DECK(self, card1=None, card2=None):
        return self.serialize(DECK, {"card1": card1, "card2": card2})
    
    def CHOOSE(self, card1, card2=None):
        return self.serialize(CHOOSE, {"card1": card1, "card2": card2})
    
    def KEEP(self, card1, card2=None):
        return self.serialize(KEEP, {"card1": card1, "card2": card2})
    
    def HELLO(self):
        return self.serialize(HELLO, {})
    
    def PLAYER(self, ID1):
        return self.serialize(PLAYER, {"ID1": ID1})
    
    def START(self):
        return self.serialize(START, {})
    
    def READY(self):
        return self.serialize(READY, {})
    
    def TURN(self, ID1):
        return self.serialize(TURN, {"ID1": ID1})
    
    def EXIT(self):
        return self.serialize(EXIT, {})
    
    def ILLEGAL(self):
        return self.serialize(ILLEGAL, {})

game_proto = GameProto()

class GameMessage(BaseMsg):
    def __init__(self, msg: str):
        super().__init__(game_proto, msg)
        self.ID1 = self.args.get("ID1", None)
        self.ID2 = self.args.get("ID2", None)
        self.action = self.args.get("action", None)
        self.card1 = self.args.get("card1", None)
        self.card2 = self.args.get("card2", None)
        self.coins = self.args.get("coins", None)
        self.command = self.msg_type

    
        