from proto.game_proto import game_proto, GameMessage
from proto.game_proto import ACT, OK, CHAL, BLOCK, SHOW, LOSE, COINS, DECK, CHOOSE, KEEP, HELLO, PLAYER, START, READY, TURN, EXIT, DEAD, ILLEGAL
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
        """Flag for whether the player is the root player. \n\n- True: The player is the root player. \n- False: The player is not the root player."""
        self.checkout = queue.SimpleQueue()
        """Queue used to send messages to the server. The queue is thread-safe and can be used by multiple threads."""
        self.term = Terminal(self.checkout) if terminal is None else terminal
        """Terminal used to write messages manually."""
    
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

        Returns:
            int -- 1 if the player wants to terminate, 0 otherwise.
        """
        raise NotImplementedError
        return 0


class InformedPlayer(Player, PlayerSim):
    """
    Player class that is informed of the game state and can send messages to the game.
    This class is used to simulate a player in the game.
    
    Attributes:
        alive (bool): Flag for whether the player is alive or not.
        checkout (SimpleQueue): Queue used to send messages to the server. The queue is thread-safe and can be used by multiple threads.
        coins (int): Number of coins the player has.
        deck (list[str]): List of cards in the player's deck.
        exchange_cards (list[str]): List of cards to exchange with the deck.
        id (str): Player ID.
        is_root (bool): Flag for whether the player is the root player or not.
        msg (GameMessage): Message to be sent to the server.
        players (dict[str, PlayerSim]): Dictionary of players in the game.
        possible_messages (list[str]): List of possible messages the player can send.
        history (list[GameMessage]): History of received messages.
        ready (bool): Flag for whether the player is ready or not.
        replied (bool): Flag for whether the player has replied to the last message or not.
        state (PlayerState): State of the player.
        tag (Tag): Tag for the player. Used to identify the player in the game.
        term (Terminal): Terminal used to write messages manually.
        terminate_after_death (bool): Flag for whether the player should terminate after its own death.
        turn (bool): Flag for whether it is the player's turn or not.
    """

    def __init__(self, terminal: Terminal | None = None):
        Player.__init__(self, terminal)
        PlayerSim.__init__(self, '0', {})
        self.terminate_after_death = False
        """Flag for whether the player should terminate after its own death. \n\n- True: The player will terminate when dead. \n- False: The player will continue to receive messages without replying."""
        self.history: list[GameMessage] = [GameMessage(OK)]
        """History of received messages. Current received message is always the last one."""
        self.msg = GameMessage(HELLO)
        self.send_message(self.msg)

    def receive(self, message: str) -> int:
        try:
            logger.success("RECV - " + str(message))
            self.history.append(GameMessage(message))
            self.pre_update_state()
            if self.state == PlayerState.IDLE or self.history[-1].command == DEAD:
                pass
            elif self.state == PlayerState.END:
                logger.info("Game Over, terminating bot.")
                return 1
            else:
                logger.debug(f"State: {self.state}")
                logger.debug(f"Possible messages: {self.possible_messages}")
                self.choose_message()
                self.post_update_state()
                self.send_message(self.msg)
                logger.success("SEND - " + str(self.msg))
        except IndexError:
            logger.error(f"No possible messages.")
        except Exception as e:
            logger.exception(f"Error in receive: " + str(e))
        return 0

    def pre_update_state(self) -> None:
        """
        Updates the state of the player based on the received message before any action is taken. 

        Arguments:
            message {GameMessage} -- received message
        """
        current_msg = self.history[-1]
        prev_msg = self.history[-2]

        if current_msg.command == EXIT:
            self.set_state(PlayerState.END)
            logger.info(f"Received EXIT message.")
        
        elif current_msg.command == DEAD:
            # Don't change state
            if current_msg.ID1 is not None:
                self.players[current_msg.ID1].alive = False
        
        elif not self.alive:
            if self.terminate_after_death:
                self.set_state(PlayerState.END)
            else:
                self.set_state(PlayerState.IDLE)
        
        elif current_msg.command == HELLO:
            self.set_state(PlayerState.IDLE)
            logger.warning(f"Received unexpected message: HELLO")
        
        elif current_msg.command == READY:
            self.set_state(PlayerState.IDLE)
            logger.warning(f"Received unexpected message: READY")
        
        elif current_msg.command == OK:
            self.set_state(PlayerState.IDLE)
            logger.warning(f"Received unexpected message: OK")
        
        elif current_msg.command == KEEP:
            self.set_state(PlayerState.IDLE)
            logger.warning(f"Received unexpected message: KEEP")
        
        elif current_msg.command == ACT:
            if current_msg.action == INCOME:
                self.set_state(PlayerState.R_INCOME)
            elif current_msg.action == FOREIGN_AID:
                self.set_state(PlayerState.R_FAID)
            elif current_msg.action == TAX:
                self.set_state(PlayerState.R_TAX)
            elif current_msg.action == EXCHANGE:
                self.set_state(PlayerState.R_EXCHANGE)
            elif current_msg.action == ASSASSINATE:
                if current_msg.ID2 == self.id:
                    self.set_state(PlayerState.R_ASSASS_ME)
                else:
                    self.set_state(PlayerState.R_ASSASS)
            elif current_msg.action == STEAL:
                if current_msg.ID2 == self.id:
                    self.set_state(PlayerState.R_STEAL_ME)
                else:
                    self.set_state(PlayerState.R_STEAL)
            elif current_msg.action == COUP:
                if current_msg.ID2 == self.id:
                    self.set_state(PlayerState.R_COUP_ME)
                else:
                    self.set_state(PlayerState.R_COUP)
            else:
                self.set_state(PlayerState.IDLE)
                logger.error(f"Invalid action: {current_msg.action}")
                
        elif current_msg.command == BLOCK:
            self.tag = Tag.T_NONE
            if self.turn:
                self.tag = Tag.T_BLOCKED
                if self.msg.action == FOREIGN_AID:
                    self.set_state(PlayerState.R_BLOCK_FAID)
                elif self.msg.action == ASSASSINATE:
                    self.set_state(PlayerState.R_BLOCK_ASSASS)
                elif self.msg.action == STEAL and current_msg.card1 == CAPTAIN:
                    self.set_state(PlayerState.R_BLOCK_STEAL_C)
                elif self.msg.action == STEAL and current_msg.card1 == AMBASSADOR:
                    self.set_state(PlayerState.R_BLOCK_STEAL_B)
                else:
                    self.set_state(PlayerState.IDLE)
                    logger.error(f"Invalid action: {self.msg.action}")
            else: 
                if prev_msg.action == FOREIGN_AID:
                    self.set_state(PlayerState.R_BLOCK_FAID)
                elif prev_msg.action == ASSASSINATE:
                    self.set_state(PlayerState.R_BLOCK_ASSASS)
                elif prev_msg.action == STEAL and current_msg.card1 == CAPTAIN:
                    self.set_state(PlayerState.R_BLOCK_STEAL_C)
                elif prev_msg.action == STEAL and current_msg.card1 == AMBASSADOR:
                    self.set_state(PlayerState.R_BLOCK_STEAL_B)
                else:
                    self.set_state(PlayerState.IDLE)
                    logger.error(f"Invalid action: {prev_msg.action}")
                
        elif current_msg.command == CHAL:
            self.tag = Tag.T_NONE
            logger.debug(f"Deck: {self.deck}")

            if self.turn:
                if prev_msg.command == BLOCK:
                    if prev_msg.card1 == AMBASSADOR:
                        self.set_state(PlayerState.R_CHAL_B)
                    elif prev_msg.card1 == CAPTAIN:
                        self.set_state(PlayerState.R_CHAL_C)
                    elif prev_msg.card1 == DUKE:
                        self.set_state(PlayerState.R_CHAL_D)
                    elif prev_msg.card1 == CONTESSA:
                        self.set_state(PlayerState.R_CHAL_E)
                    else:
                        self.set_state(PlayerState.IDLE)
                        logger.error(f"Challenging a non-challengeable action: {str(prev_msg)}")
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
                
                elif prev_msg.command == BLOCK:
                    if prev_msg.card1 == AMBASSADOR:
                        self.set_state(PlayerState.R_CHAL_B)
                    elif prev_msg.card1 == CAPTAIN:
                        self.set_state(PlayerState.R_CHAL_C)
                    elif prev_msg.card1 == DUKE:
                        self.set_state(PlayerState.R_CHAL_D)
                    elif prev_msg.card1 == CONTESSA:
                        self.set_state(PlayerState.R_CHAL_E)
                    else:
                        self.set_state(PlayerState.IDLE)
                        logger.error(f"Challenging a non-challengeable action: {str(prev_msg)}")
                
                elif prev_msg.command == ACT:
                    if prev_msg.action == ASSASSINATE:
                        self.set_state(PlayerState.R_CHAL_A)
                    elif prev_msg.action == EXCHANGE:
                        self.set_state(PlayerState.R_CHAL_B)
                    elif prev_msg.action == STEAL:
                        self.set_state(PlayerState.R_CHAL_C)
                    elif prev_msg.action == TAX:
                        self.set_state(PlayerState.R_CHAL_D)
                    else:
                        self.set_state(PlayerState.IDLE)
                        logger.error(f"Challenging a non-challengeable action: {str(prev_msg)}")
            
        elif current_msg.command == SHOW:
            self.set_state(PlayerState.R_SHOW)
                
        elif current_msg.command == LOSE:
            if current_msg.ID1 == None or current_msg.ID1 == self.id:
                self.set_state(PlayerState.R_LOSE_ME)
            else:
                self.set_state(PlayerState.R_LOSE)
            
        elif current_msg.command == COINS:
            self.set_state(PlayerState.R_COINS)
            if current_msg.ID1 is not None and current_msg.coins is not None:
                if current_msg.ID1 == self.id:
                    self.coins = int(current_msg.coins)
                elif current_msg.ID1 in self.players.keys():
                    self.players[current_msg.ID1].coins = int(current_msg.coins)
            
        elif current_msg.command == DECK:
            self.set_state(PlayerState.R_DECK)
            if current_msg.card1 is not None:
                if current_msg.card2 is not None:
                    self.deck = [current_msg.card1, current_msg.card2]
                else:
                    self.deck = [current_msg.card1]
            else:
                self.deck = []
                self.alive = False
            
        elif current_msg.command == CHOOSE:
            if current_msg.card1 is None or current_msg.card2 is None:
                self.set_state(PlayerState.IDLE)
                logger.error(f"Invalid CHOOSE message: {prev_msg}")
            else:
                self.exchange_cards = [current_msg.card1, current_msg.card2]
                self.set_state(PlayerState.R_CHOOSE)
            
        elif current_msg.command == PLAYER:
            self.set_state(PlayerState.R_PLAYER)
            if current_msg.ID1 is not None:
                if self.id == '0':
                    self.id = str(current_msg.ID1)
                else:
                    self.players[current_msg.ID1] = PlayerSim(current_msg.ID1, self.players)
                    self.players[current_msg.ID1].alive = True
            
        elif current_msg.command == START:
            self.set_state(PlayerState.START)
            
        elif current_msg.command == TURN:
            if current_msg.ID1 == self.id:
                self.turn = True
                self.set_state(PlayerState.R_MY_TURN)
            else:
                self.turn = False
                self.set_state(PlayerState.R_OTHER_TURN)
   
        elif current_msg.command == ILLEGAL:
            # keep in the same state
            logger.warning(f"Received ILLEGAL message.")
            for msg in self.possible_messages:
                if msg == str(self.msg):
                    self.possible_messages.remove(msg)
            
        else:
            self.set_state(PlayerState.IDLE)
            logger.error(f"Invalid command: {current_msg.command}")
    
    def choose_message(self) -> None:
        """
        Called when the player is in a state where it can choose a message to send. 
        Reads _self.possible_messages_, chooses one of them and sets _self.msg_ to it.
        """
        raise NotImplementedError("choose_message() not implemented.")
    
    def post_update_state(self) -> None:
        """
        Updates the state of the player based on the received message and the chosen reply.

        Arguments:
            message {GameMessage} -- chosen message to be sent
        """
        if self.msg.command == CHAL:
            self.tag = Tag.T_CHALLENGING
            
        elif self.msg.command == BLOCK:
            self.tag = Tag.T_BLOCKING
        
        elif self.msg.command == KEEP:
            if self.msg.card1 is not None:
                if self.msg.card2 is not None:
                    self.deck = [self.msg.card1, self.msg.card2]
                else:
                    self.deck = [self.msg.card1]
                logger.debug(f"New deck: {self.deck}")
            else:
                logger.error(f"Invalid message: {self.msg}")
        
        if not self.alive:
            self.set_state(PlayerState.END)
    
    def send_message(self, message: GameMessage) -> None:
        """
        Sends a message to the server. The message is put in the checkout queue.
        This method is called when the player is in a state where it can send a message.

        Arguments:
            message {GameMessage} -- message to be sent
        """
        self.msg = message
        self.checkout.put(str(self.msg))
 
