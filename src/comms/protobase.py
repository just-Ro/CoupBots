

from typing import Any


class MsgArg:
    def __init__(self, name, check, required=True):
        self.name = name
        self.check = check
        self.required = required

class MsgType:
    def __init__(self, name: str, *args: MsgArg):    
        self.name = name
        self.args = args
        self.min_size = 0
        
        # check if there is an optional argument before a required one
        optional = False
        for arg in args:
            if arg.required and not optional:
                self.min_size += 1
            elif not arg.required:
                optional = True
            elif optional:
                raise SyntaxError("Protobase: Optional argument before required argument.")
        
class Proto:
    def __init__(self, *msg_types: MsgType):
        self.msg_types = msg_types
        self.sep = ','  # default separator
        self.term = '\n'  # default terminator
    
    def parse(self, msg: str):
        """
        parse a message string into a message type and arguments

        Arguments:
            msg {str} -- the message string

        Returns:
            tuple{str, dict} -- the message type and a dictionary of arguments
        """
        msg = msg.strip(self.term)
        msg_type, *args = msg.split(self.sep)
        return msg_type, self._parse_args(self._get_msg_type(msg_type), args)
    
    def _parse_args(self, msg_type: MsgType, args: list[str]):
        if len(args) < msg_type.min_size:
            raise SyntaxError("Protobase: Not enough arguments.")
        parsed_args = {}
        for i in range(min(len(args), len(msg_type.args))):
            if not msg_type.args[i].check(args[i]):
                raise SyntaxError(f"Protobase: Invalid argument for {msg_type.args[i].name}.")
            parsed_args[msg_type.args[i].name] = args[i]
        return parsed_args
    
    def serialize(self, msg_type: str, args: dict):
        """
        serialize a message type and arguments into a message string
        
        Arguments:
            msg_type {str} -- the message type
            args {dict{str | Any}} -- a dictionary of arguments
        
        Returns:
            str -- the message string
        """
        return self._serialize_args(self._get_msg_type(msg_type), args)
    
    def _serialize_args(self, msg_type: MsgType, args: dict):
        parts = [msg_type.name]
        for arg in msg_type.args:
            if arg.required:
                if arg.name not in args:
                    raise SyntaxError(f"Protobase: Missing required argument {arg.name}.")
                if not arg.check(args[arg.name]):
                    raise SyntaxError(f"Protobase: Invalid argument for {arg.name}.")
                parts.append(str(args[arg.name]))
            else:
                if arg.name in args and args[arg.name] is not None:
                    if not arg.check(args[arg.name]):
                        raise SyntaxError(f"Protobase: Invalid argument for {arg.name}.")
                    parts.append(str(args[arg.name]))

        return self.sep.join(parts) + self.term

    def _get_msg_type(self, name: str):
        for msg_type in self.msg_types:
            if msg_type.name == name:
                return msg_type
        raise SyntaxError("Protobase: Invalid message type.")

class BaseMsg:
    def __init__(self, proto: Proto, msg: str):
        self.proto = proto
        self.msg_type, self.args = proto.parse(msg)

    def __str__(self):
        return self.proto.serialize(self.msg_type, self.args)

    
        
        