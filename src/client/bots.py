from proto.game_proto import game_proto, GameMessage
from proto.game_proto import ACT, OK, CHAL, BLOCK, SHOW, LOSE, COINS, DECK, CHOOSE, KEEP, HELLO, PLAYER, START, READY, TURN, EXIT, ILLEGAL
from .game.state_machine import State, SubState, PlayerState, Tag, PlayerSim
from .game.core import *
from .player import Player
from utils.colored_text import red, green, yellow, blue
import random



class CoupBot(Player):
    """
    CoopBot player class.
    """

    def __init__(self):
        super().__init__()
        self.verbose = True  # Error messages and connection status
        self.ui = False  # User interface like input prompts

    def receive(self, message: str) -> int:
        # TODO
        # Implement your bot here

        # Use GameMessage to help reading messages. Example:

        # m = GameMessage(message)
        # command = m.command
        # source = m.ID1
        # card1 = m.card1
        # card2 = m.card2
        # action = m.action
        # target = m.ID2
        # coins = m.coins

        # Use game_proto to create messages. Example:

        # m = game_proto.ACT("1", COUP, "2")
        
        # Put the reply onto the checkout queue. Example:
        # self.checkout.put(m)
        
        raise NotImplementedError
        return 0


class TestBot(Player, PlayerSim):
    """
    TestBot player class.
    """

    def __init__(self):
        Player.__init__(self)
        PlayerSim.__init__(self, '0', {})
        self.verbose = True  # Error messages and connection status
        self.ui = False  # User interface like input prompts
        self.rcv_msg = GameMessage(OK)
        self.msg = GameMessage(HELLO)
        self.send_message(self.msg)
        self.terminate_after_death = False

    def receive(self, message: str) -> int:
        try:
            self.printv(green("RECV - " + str(message)))
            m = GameMessage(message)
            self.pre_update_state(m)
            if self.state == PlayerState.IDLE:
                pass
            elif self.state == PlayerState.END:
                self.printv(blue("Game Over, terminating bot."))
                return 1
            else:
                # self.printv(f"State: {self.state}")
                self.printv(str(self.possible_messages))
                self.choose_message()
                self.post_update_state(self.msg)
                self.send_message(self.msg)
                self.rcv_msg = m
                self.printv(blue("SEND - " + str(self.msg)))
        except IndexError:
            self.printv(red(f"No possible messages."))
        except Exception as e:
            self.printv(red(f"Error in receive: " + str(e)))
        return 0

    def pre_update_state(self, message: GameMessage):
                        
        if message.command == EXIT:
            self.set_state(PlayerState.END)
            self.printv(f"Received EXIT message.")
        
        elif not self.alive:
            if self.terminate_after_death:
                self.set_state(PlayerState.END)
            else:
                self.set_state(PlayerState.IDLE)
        
        elif message.command == HELLO:
            self.set_state(PlayerState.IDLE)
            self.printv(yellow(f"Received unexpected message: HELLO"))
        
        elif message.command == READY:
            self.set_state(PlayerState.IDLE)
            self.printv(yellow(f"Received unexpected message: READY"))
        
        elif message.command == OK:
            self.set_state(PlayerState.IDLE)
            self.printv(yellow(f"Received unexpected message: OK"))
        
        elif message.command == KEEP:
            self.set_state(PlayerState.IDLE)
            self.printv(yellow(f"Received unexpected message: KEEP"))
        
        elif message.command == ACT:
            if message.action == INCOME:
                self.set_state(PlayerState.R_INCOME)
            elif message.action == FOREIGN_AID:
                self.set_state(PlayerState.R_FAID)
            elif message.action == TAX:
                self.set_state(PlayerState.R_TAX)
            elif message.action == EXCHANGE:
                self.set_state(PlayerState.R_EXCHANGE)
            elif message.action == ASSASSINATE:
                if message.ID2 == self.id:
                    self.set_state(PlayerState.R_ASSASS_ME)
                else:
                    self.set_state(PlayerState.R_ASSASS)
            elif message.action == STEAL:
                if message.ID2 == self.id:
                    self.set_state(PlayerState.R_STEAL_ME)
                else:
                    self.set_state(PlayerState.R_STEAL)
            elif message.action == COUP:
                if message.ID2 == self.id:
                    self.set_state(PlayerState.R_COUP_ME)
                else:
                    self.set_state(PlayerState.R_COUP)
            else:
                self.set_state(PlayerState.IDLE)
                self.printv(red(f"Invalid action: {message.action}"))
                
        elif message.command == BLOCK:
            self.tag = Tag.T_NONE
            if self.turn:
                self.tag = Tag.T_BLOCKED
                if self.msg.action == FOREIGN_AID:
                    self.set_state(PlayerState.R_BLOCK_FAID)
                elif self.msg.action == ASSASSINATE:
                    self.set_state(PlayerState.R_BLOCK_ASSASS)
                elif self.msg.action == STEAL and message.card1 == CAPTAIN:
                    self.set_state(PlayerState.R_BLOCK_STEAL_C)
                elif self.msg.action == STEAL and message.card1 == AMBASSADOR:
                    self.set_state(PlayerState.R_BLOCK_STEAL_B)
                else:
                    self.set_state(PlayerState.IDLE)
                    self.printv(red(f"Invalid action: {self.msg.action}"))
            else: 
                if self.rcv_msg.action == FOREIGN_AID:
                    self.set_state(PlayerState.R_BLOCK_FAID)
                elif self.rcv_msg.action == ASSASSINATE:
                    self.set_state(PlayerState.R_BLOCK_ASSASS)
                elif self.rcv_msg.action == STEAL and message.card1 == CAPTAIN:
                    self.set_state(PlayerState.R_BLOCK_STEAL_C)
                elif self.rcv_msg.action == STEAL and message.card1 == AMBASSADOR:
                    self.set_state(PlayerState.R_BLOCK_STEAL_B)
                else:
                    self.set_state(PlayerState.IDLE)
                    self.printv(red(f"Invalid action: {self.rcv_msg.action}"))
                
        elif message.command == CHAL:
            self.tag = Tag.T_NONE
            self.printv(f"Deck: {self.deck}")

            if self.turn:
                if self.rcv_msg.command == BLOCK:
                    if self.rcv_msg.card1 == AMBASSADOR:
                        self.set_state(PlayerState.R_CHAL_B)
                    elif self.rcv_msg.card1 == CAPTAIN:
                        self.set_state(PlayerState.R_CHAL_C)
                    elif self.rcv_msg.card1 == DUKE:
                        self.set_state(PlayerState.R_CHAL_D)
                    else:
                        self.set_state(PlayerState.IDLE)
                        self.printv(red(f"Challenging a non-challengeable action: {str(self.rcv_msg)}"))
                elif self.msg.command == ACT:
                    if self.msg.action == ASSASSINATE:
                        self.tag = Tag.T_CHALLENGED
                        self.set_state(PlayerState.R_CHAL_MY_A)
                    elif self.msg.action == EXCHANGE:
                        self.tag = Tag.T_CHALLENGED
                        self.set_state(PlayerState.R_CHAL_MY_B)
                    elif self.msg.action == STEAL:
                        self.tag = Tag.T_CHALLENGED
                        self.set_state(PlayerState.R_CHAL_MY_C)
                    elif self.msg.action == TAX:
                        self.tag = Tag.T_CHALLENGED
                        self.set_state(PlayerState.R_CHAL_MY_D)
                    else:
                        self.set_state(PlayerState.IDLE)
                        self.printv(red(f"Challenging a non-challengeable action: {str(self.msg)}"))
                else:
                    self.set_state(PlayerState.IDLE)
                    self.printv(red(f"Challenging a non-challengeable action: {str(self.msg)}"))
            else:
                if self.msg.command == BLOCK:
                    if self.msg.card1 == AMBASSADOR:
                        self.tag = Tag.T_CHALLENGED
                        self.set_state(PlayerState.R_CHAL_MY_B)
                    elif self.msg.card1 == CAPTAIN:
                        self.tag = Tag.T_CHALLENGED
                        self.set_state(PlayerState.R_CHAL_MY_C)
                    elif self.msg.card1 == DUKE:
                        self.tag = Tag.T_CHALLENGED
                        self.set_state(PlayerState.R_CHAL_MY_D)
                    elif self.msg.card1 == CONTESSA:
                        self.tag = Tag.T_CHALLENGED
                        self.set_state(PlayerState.R_CHAL_MY_E)
                    else:
                        self.set_state(PlayerState.IDLE)
                        self.printv(red(f"Challenging a non-challengeable action: {str(self.msg)}"))
                
                elif self.rcv_msg.command == BLOCK:
                    if self.rcv_msg.card1 == AMBASSADOR:
                        self.set_state(PlayerState.R_CHAL_B)
                    elif self.rcv_msg.card1 == CAPTAIN:
                        self.set_state(PlayerState.R_CHAL_C)
                    elif self.rcv_msg.card1 == DUKE:
                        self.set_state(PlayerState.R_CHAL_D)
                    elif self.rcv_msg.card1 == CONTESSA:
                        self.set_state(PlayerState.R_CHAL_E)
                    else:
                        self.set_state(PlayerState.IDLE)
                        self.printv(red(f"Challenging a non-challengeable action: {str(self.rcv_msg)}"))
                
                elif self.rcv_msg.command == ACT:
                    if self.rcv_msg.action == ASSASSINATE:
                        self.set_state(PlayerState.R_CHAL_A)
                    elif self.rcv_msg.action == EXCHANGE:
                        self.set_state(PlayerState.R_CHAL_B)
                    elif self.rcv_msg.action == STEAL:
                        self.set_state(PlayerState.R_CHAL_C)
                    elif self.rcv_msg.action == TAX:
                        self.set_state(PlayerState.R_CHAL_D)
                    else:
                        self.set_state(PlayerState.IDLE)
                        self.printv(red(f"Challenging a non-challengeable action: {str(self.rcv_msg)}"))
            
        elif message.command == SHOW:
            self.set_state(PlayerState.R_SHOW)
                
        elif message.command == LOSE:
            if message.ID1 == None or message.ID1 == self.id:
                self.set_state(PlayerState.R_LOSE_ME)
            else:
                self.set_state(PlayerState.R_LOSE)
            
        elif message.command == COINS:
            self.set_state(PlayerState.R_COINS)
            if message.ID1 is not None and message.coins is not None:
                if message.ID1 == self.id:
                    self.coins = int(message.coins)
                elif message.ID1 in self.players.keys():
                    self.players[message.ID1].coins = int(message.coins)
            
        elif message.command == DECK:
            self.set_state(PlayerState.R_DECK)
            if message.card1 is not None:
                if message.card2 is not None:
                    self.deck = [message.card1, message.card2]
                else:
                    self.deck = [message.card1]
            else:
                self.deck = []
                self.alive = False
            
        elif message.command == CHOOSE:
            if message.card1 is None or message.card2 is None:
                self.set_state(PlayerState.IDLE)
                self.printv(red(f"Invalid CHOOSE message: {message}"))
            else:
                self.exchange_cards = [message.card1, message.card2]
                self.set_state(PlayerState.R_CHOOSE)
            
        elif message.command == PLAYER:
            self.set_state(PlayerState.R_PLAYER)
            if message.ID1 is not None:
                if self.id == '0':
                    self.id = str(message.ID1)
                else:
                    self.players[message.ID1] = PlayerSim(message.ID1, self.players)
                    self.players[message.ID1].alive = True
            
        elif message.command == START:
            self.set_state(PlayerState.START)
            
        elif message.command == TURN:
            if message.ID1 == self.id:
                self.turn = True
                self.set_state(PlayerState.R_MY_TURN)
            else:
                self.turn = False
                self.set_state(PlayerState.R_OTHER_TURN)
   
        elif message.command == ILLEGAL:
            # keep in the same state
            self.printv(yellow(f"Received ILLEGAL message."))
            for msg in self.possible_messages:
                if msg == str(self.msg):
                    self.possible_messages.remove(msg)
            
        else:
            self.set_state(PlayerState.IDLE)
            self.printv(red(f"Invalid command: {message.command}"))

    def post_update_state(self, message: GameMessage):      
        if message.command == CHAL:
            self.tag = Tag.T_CHALLENGING
            
        elif message.command == BLOCK:
            self.tag = Tag.T_BLOCKING
        
        elif message.command == KEEP:
            if message.card1 is not None:
                if message.card2 is not None:
                    self.deck = [message.card1, message.card2]
                else:
                    self.deck = [message.card1]
                self.printv(f"New deck: {self.deck}")
            else:
                self.printv(red(f"Invalid KEEP message: {message}"))
        
        if not self.alive:
            self.set_state(PlayerState.END)
    
    def choose_message(self):
        if len(self.possible_messages) == 0:
            raise IndexError("No possible messages.")
        self.msg = GameMessage(random.choice(self.possible_messages)) # choose random
        # self.msg = GameMessage(self.possible_messages[-1]) # choose last
        return
        
        # test with priority choices
        msgs: list[GameMessage] = []
        for m in self.possible_messages:
            msgs.append(GameMessage(m))
        for m in msgs:
            if m.command == ACT and m.action == TAX:
                self.msg = m
                return
            elif m.command == BLOCK:
                self.msg = m
                return
        
    def send_message(self, message: GameMessage):
        self.msg = message
        self.checkout.put(str(self.msg))
  