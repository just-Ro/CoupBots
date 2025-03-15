from .protobase import MsgType, MsgArg, Proto, BaseMsg

ALL = "ALL"
SINGLE = "SINGLE"
EXCEPT = "EXCEPT"

DISCONNECT = "DISCONNECT"

def _check_game_msg(msg):
    return len(msg) > 0

def _check_addr(addr):
    return str(addr).isnumeric()

class NetworkProto(Proto):
    def __init__(self):
        super().__init__(
            MsgType(ALL,
                    MsgArg("msg", _check_game_msg)),
            
            MsgType(SINGLE,
                    MsgArg("addr", _check_addr),
                    MsgArg("msg", _check_game_msg)),
            
            MsgType(EXCEPT,
                    MsgArg("addr", _check_addr),
                    MsgArg("msg", _check_game_msg))
        )
        self.sep = '@'
    
    ## helpers
    
    def ALL(self, msg):
        return self.serialize(ALL, {"msg": msg})
    
    def SINGLE(self, addr, msg):
        return self.serialize(SINGLE, {"addr": addr, "msg": msg})
    
    def EXCEPT(self, addr, msg):
        return self.serialize(EXCEPT, {"addr": addr, "msg": msg})

network_proto = NetworkProto()

class NetworkMessage(BaseMsg):
    def __init__(self, msg: str):
        super().__init__(network_proto, msg)
        self.addr = self.args.get("addr", None)
        self.msg = self.args.get("msg", None)

    
        