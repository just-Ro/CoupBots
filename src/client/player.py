from proto.game_proto import game_proto, GameMessage
from proto.game_proto import ACT, OK, CHAL, BLOCK, SHOW, LOSE, COINS, DECK, CHOOSE, KEEP, HELLO, PLAYER, START, READY, TURN, EXIT, ILLEGAL
from .game.state_machine import PlayerState, Tag, PlayerSim
from .game.core import INCOME, FOREIGN_AID, COUP, TAX, ASSASSINATE, STEAL, EXCHANGE, ACTIONS, TARGET_ACTIONS  # Actions
from .game.core import ASSASSIN, AMBASSADOR, CAPTAIN, DUKE, CONTESSA, CHARACTERS  # Characters
from terminal.terminal import Terminal
import queue, random
from loguru import logger

CHECKOUT_TIMEOUT = 0.5

class Player:
    """
    Abstract class for a player in the game.
    """
    
    def __init__(self, terminal: Terminal | None = None):
        self.is_root = False
        
        # Create a queue to send messages
        self.checkout = queue.SimpleQueue()
        
        # Create a terminal to write messages manually
        self.term = Terminal(self.checkout) if terminal is None else terminal
    
    def sender(self):
        """
        Gets a message from checkout and returns it.

        Returns:
            _str_ | None -- message
        """
        try:
            # Check if the terminal thread finished
            if not self.term.signal:
                logger.info("Terminal closed.")
                raise KeyboardInterrupt
            
            return self.checkout.get(timeout=CHECKOUT_TIMEOUT)
        except queue.Empty:
            print(end="")   # weird way to update the console buffer
            return None

    def receive(self, message: str) -> int:
        """
        Informs the player of a message.
        Here, the player may or may not reply to the message.

        Arguments:
            message {_str_} -- request/informative message

        """
        raise NotImplementedError
        return 0


class InformedPlayer(Player, PlayerSim):
    """
    TestBot player class.
    """

    def __init__(self, terminal: Terminal | None = None):
        Player.__init__(self, terminal)
        PlayerSim.__init__(self, '0', {})
        self.rcv_msg = GameMessage(OK)
        self.msg = GameMessage(HELLO)
        self.send_message(self.msg)
        self.terminate_after_death = False

    def receive(self, message: str) -> int:
        try:
            logger.success("RECV - " + str(message))
            m = GameMessage(message)
            self.pre_update_state(m)
            if self.state == PlayerState.IDLE:
                pass
            elif self.state == PlayerState.END:
                logger.info("Game Over, terminating bot.")
                return 1
            else:
                # logger.debug(f"State: {self.state}")
                logger.debug(str(self.possible_messages))
                self.choose_message()
                self.post_update_state(self.msg)
                self.send_message(self.msg)
                self.rcv_msg = m
                logger.success("SEND - " + str(self.msg))
        except IndexError:
            logger.error(f"No possible messages.")
        except Exception as e:
            logger.error(f"Error in receive: " + str(e))
        return 0

    def pre_update_state(self, message: GameMessage):
                        
        if message.command == EXIT:
            self.set_state(PlayerState.END)
            logger.info(f"Received EXIT message.")
        
        elif not self.alive:
            if self.terminate_after_death:
                self.set_state(PlayerState.END)
            else:
                self.set_state(PlayerState.IDLE)
        
        elif message.command == HELLO:
            self.set_state(PlayerState.IDLE)
            logger.warning(f"Received unexpected message: HELLO")
        
        elif message.command == READY:
            self.set_state(PlayerState.IDLE)
            logger.warning(f"Received unexpected message: READY")
        
        elif message.command == OK:
            self.set_state(PlayerState.IDLE)
            logger.warning(f"Received unexpected message: OK")
        
        elif message.command == KEEP:
            self.set_state(PlayerState.IDLE)
            logger.warning(f"Received unexpected message: KEEP")
        
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
                logger.error(f"Invalid action: {message.action}")
                
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
                    logger.error(f"Invalid action: {self.msg.action}")
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
                    logger.error(f"Invalid action: {self.rcv_msg.action}")
                
        elif message.command == CHAL:
            self.tag = Tag.T_NONE
            logger.debug(f"Deck: {self.deck}")

            if self.turn:
                if self.rcv_msg.command == BLOCK:
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
                        logger.error(f"Challenging a non-challengeable action: {str(self.rcv_msg)}")
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
                        logger.error(f"Challenging a non-challengeable action: {str(self.msg)}")
                else:
                    self.set_state(PlayerState.IDLE)
                    logger.error(f"Challenging a non-challengeable action: {str(self.msg)}")
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
                        logger.error(f"Challenging a non-challengeable action: {str(self.msg)}")
                
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
                        logger.error(f"Challenging a non-challengeable action: {str(self.rcv_msg)}")
                
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
                        logger.error(f"Challenging a non-challengeable action: {str(self.rcv_msg)}")
            
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
                logger.error(f"Invalid CHOOSE message: {message}")
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
            logger.warning(f"Received ILLEGAL message.")
            for msg in self.possible_messages:
                if msg == str(self.msg):
                    self.possible_messages.remove(msg)
            
        else:
            self.set_state(PlayerState.IDLE)
            logger.error(f"Invalid command: {message.command}")
    
    def choose_message(self):
        raise NotImplementedError("choose_message() not implemented.")
    
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
                logger.debug(f"New deck: {self.deck}")
            else:
                logger.error(f"Invalid message: {message}")
        
        if not self.alive:
            self.set_state(PlayerState.END)
    
    def send_message(self, message: GameMessage):
        self.msg = message
        self.checkout.put(str(self.msg))
 
