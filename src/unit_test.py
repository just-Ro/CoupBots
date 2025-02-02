import unittest
from proto.game_proto import game_proto, GameMessage

class TestGameProto(unittest.TestCase):

    def test_serialize_act(self):
        with self.assertRaises(Exception) as context:
            msg = game_proto.serialize("ACT", {"ID1": 0, "action": "tax"})
        self.assertEqual(str(context.exception), "Invalid argument for ACTION")

    def test_serialize_ok(self):
        try:
            msg = game_proto.serialize("OK", {})
            self.assertEqual(msg, "OK")
        except Exception as e:
            self.fail(f"Serialization failed: {e}")

    def test_serialize_chal(self):
        try:
            msg = game_proto.serialize("CHAL", {"ID1": "0"})
            self.assertEqual(msg, "CHAL|0")
        except Exception as e:
            self.fail(f"Serialization failed: {e}")

    def test_parse_act(self):
        try:
            msg = "ACT|0|T"
            msg_type, args = game_proto.parse(msg)
            self.assertEqual(msg_type, "ACT")
            self.assertEqual(args, {"ID1": "0", "action": "T"})
        except Exception as e:
            self.fail(f"Parsing failed: {e}")

    def test_parse_ok(self):
        try:
            msg = "OK"
            msg_type, args = game_proto.parse(msg)
            self.assertEqual(msg_type, "OK")
            self.assertEqual(args, {})
        except Exception as e:
            self.fail(f"Parsing failed: {e}")

    def test_parse_chal(self):
        try:
            msg = "CHAL|0"
            msg_type, args = game_proto.parse(msg)
            self.assertEqual(msg_type, "CHAL")
            self.assertEqual(args, {"ID1": "0"})
        except Exception as e:
            self.fail(f"Parsing failed: {e}")

    def test_game_message(self):
        try:
            msg = GameMessage("ACT|0|T")
            self.assertEqual(msg.msg_type, "ACT")
            self.assertEqual(msg.args, {"ID1": "0", "action": "T"})
        except Exception as e:
            self.fail(f"GameMessage creation failed: {e}")
    
    def test_game_message_invalid(self):
        with self.assertRaises(Exception) as context:
            msg = GameMessage("ACT|0")
        self.assertEqual(str(context.exception), "Not enough arguments")
        
    def test_game_message_attributes(self):
        msg = GameMessage("ACT|0|T")
        self.assertEqual(msg.msg_type, "ACT")
        self.assertEqual(msg.args, {"ID1": "0", "action": "T"})
        self.assertEqual(msg.ID1, "0")
        self.assertEqual(msg.action, "T")
        

if __name__ == "__main__":
    unittest.main()
