from comms.network_proto import network_proto, NetworkMessage
from comms.network_proto import ALL, SINGLE, EXCEPT, DISCONNECT
from comms.game_proto import INCOME, FOREIGN_AID, COUP, TAX, ASSASSINATE, STEAL, EXCHANGE, ACTIONS, TARGET_ACTIONS  # Actions
from comms.game_proto import ASSASSIN, AMBASSADOR, CAPTAIN, DUKE, CONTESSA, CHARACTERS  # Characters
from comms.game_proto import game_proto, GameMessage
from comms.game_proto import ACT, OK, CHAL, BLOCK, SHOW, LOSE, COINS, DECK, CHOOSE, KEEP, HELLO, PLAYER, START, READY, TURN, EXIT, ILLEGAL
from utils.colored_text import red, green, yellow, blue
from .player import Player
import random
import itertools
import traceback

S_IDLE = 0
S_PRESTART = 1
S_START = 2
S_TURN = 5
S_ACTION = 6
S_BLOCK = 7
S_CHAL = 8
S_END = 9



SS_0 = 100  # default substate 
SS_START_DECK = 101
SS_START_COINS = 102
SS_START_PLAYERS = 103

# Player states
R_MY_TURN = 10
R_OTHER_TURN = 11
R_FAID = 12
R_INCOME = 13
R_EXCHANGE = 14
R_TAX = 15
R_ASSASS_ME = 16
R_ASSASS = 17
R_STEAL_ME = 18
R_STEAL = 19
R_COUP_ME = 20
R_COUP = 21
R_BLOCK_FAID = 22
R_BLOCK_ASSASS = 23
R_BLOCK_STEAL_B = 24
R_BLOCK_STEAL_C = 25
R_CHAL_A = 26
R_CHAL_B = 27
R_CHAL_C = 28
R_CHAL_D = 29
R_CHAL_E = 30
R_CHAL_MY_A = 31
R_CHAL_MY_B = 32
R_CHAL_MY_C = 33
R_CHAL_MY_D = 34
R_CHAL_MY_E = 35
R_LOSE = 36
R_SHOW = 37
R_COINS = 38
R_DECK = 39
R_CHOOSE = 40
R_PLAYER = 41

T_NONE = 0
T_BLOCKING = 1
T_BLOCKED = 2
T_CHALLENGING = 3
T_CHALLENGED = 4

MIN_PLAYERS = 2
MAX_PLAYERS = 5
STARTING_COINS = 2

class PlayerState:
    """
    Player state class.
    """

    def __init__(self, id: str, players: dict[str, "PlayerState"]):
        self.id = id
        self.players = players
        self.coins: int = 0
        self.deck: list[str] = []
        self.exchange_cards = []
        self.ready = False
        self.alive = True
        self.turn = False
        self.tag = T_NONE
        self.state = S_IDLE
        self.replied = True
        self.possible_messages = []
        self.was_announced = False
        self.msg: GameMessage = GameMessage("OK")
    
    def set_state(self, state: int):
        self.state = state
        self.possible_messages = self.generate_responses()
    
    def generate_responses(self):
        """
        Generates a list of possible messages to send.
        """
        messages = []

        # If the player is dead or can't reply, they can't send any messages
        if not self.alive or self.state == S_IDLE:
            return messages
            
        # Wait for all players to be ready
        if self.state == S_START:
            messages.append(game_proto.READY())
        
        elif self.state == R_MY_TURN:
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
                
        elif self.state == R_OTHER_TURN:
            messages.append(game_proto.OK())
                
        elif self.state == R_FAID:
            messages.append(game_proto.OK())
            messages.append(game_proto.BLOCK(self.id, DUKE))
                
        elif self.state == R_INCOME:
            messages.append(game_proto.OK())

        elif self.state == R_EXCHANGE:
            messages.append(game_proto.OK())
            messages.append(game_proto.CHAL(self.id))
                
        elif self.state == R_TAX:
            messages.append(game_proto.OK())
            messages.append(game_proto.CHAL(self.id))
                
        elif self.state == R_ASSASS_ME:
            messages.append(game_proto.CHAL(self.id))
            messages.append(game_proto.BLOCK(self.id, CONTESSA))
            for card in self.deck:
                messages.append(game_proto.LOSE(self.id, card))
                
        elif self.state == R_ASSASS:
            messages.append(game_proto.OK())
            messages.append(game_proto.CHAL(self.id))
                
        elif self.state == R_STEAL_ME:
            messages.append(game_proto.OK())
            messages.append(game_proto.BLOCK(self.id, CAPTAIN))
            messages.append(game_proto.BLOCK(self.id, AMBASSADOR))
            messages.append(game_proto.CHAL(self.id))
                
        elif self.state == R_STEAL:
            messages.append(game_proto.OK())
            messages.append(game_proto.CHAL(self.id))
                
        elif self.state == R_COUP_ME:
            for card in self.deck:
                messages.append(game_proto.LOSE(self.id, card))
                
        elif self.state == R_COUP:
            messages.append(game_proto.OK())
                
        elif self.state == R_BLOCK_FAID:
            messages.append(game_proto.OK())
            messages.append(game_proto.CHAL(self.id))
                
        elif self.state == R_BLOCK_ASSASS:
            messages.append(game_proto.OK())
            messages.append(game_proto.CHAL(self.id))
                
        elif self.state == R_BLOCK_STEAL_B:
            messages.append(game_proto.OK())
            messages.append(game_proto.CHAL(self.id))
                
        elif self.state == R_BLOCK_STEAL_C:
            messages.append(game_proto.OK())
            messages.append(game_proto.CHAL(self.id))
                
        elif self.state == R_CHAL_A:
            messages.append(game_proto.OK())
                
        elif self.state == R_CHAL_B:
            messages.append(game_proto.OK())
                
        elif self.state == R_CHAL_C:
            messages.append(game_proto.OK())
                
        elif self.state == R_CHAL_D:
            messages.append(game_proto.OK())
                
        elif self.state == R_CHAL_E:
            messages.append(game_proto.OK())
                
        elif self.state == R_CHAL_MY_A:
            for card in self.deck:
                if card == ASSASSIN:
                    messages.append(game_proto.SHOW(self.id, card))
                else:
                    messages.append(game_proto.LOSE(self.id, card))
                
        elif self.state == R_CHAL_MY_B:
            for card in self.deck:
                if card == AMBASSADOR:
                    messages.append(game_proto.SHOW(self.id, card))
                else:
                    messages.append(game_proto.LOSE(self.id, card))
                
        elif self.state == R_CHAL_MY_C:
            for card in self.deck:
                if card == CAPTAIN:
                    messages.append(game_proto.SHOW(self.id, card))
                else:
                    messages.append(game_proto.LOSE(self.id, card))
                
        elif self.state == R_CHAL_MY_D:
            for card in self.deck:
                if card == DUKE:
                    messages.append(game_proto.SHOW(self.id, card))
                else:
                    messages.append(game_proto.LOSE(self.id, card))
                
        elif self.state == R_CHAL_MY_E:
            for card in self.deck:
                if card == CONTESSA:
                    messages.append(game_proto.SHOW(self.id, card))
                else:
                    messages.append(game_proto.LOSE(self.id, card))
                
        elif self.state == R_LOSE:
            messages.append(game_proto.OK())
                
        elif self.state == R_SHOW:
            if self.tag == T_CHALLENGING:
                for card in self.deck:
                    messages.append(game_proto.LOSE(self.id, card)) 
            else:
                messages.append(game_proto.OK())

        elif self.state == R_COINS:
            messages.append(game_proto.OK())

        elif self.state == R_DECK:
            messages.append(game_proto.OK())
            
        elif self.state == R_CHOOSE:
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
        
        elif self.state == R_PLAYER:
            messages.append(game_proto.OK())
        
        return messages

class Root(Player):
    """
    Root player class.

    This player sends and receives addressed messages, e.g. orig@message
    """

    def __init__(self):
        super().__init__()
        self.verbose = True
        self.is_root = True
        self.players: dict[str, PlayerState] = {}
        self.turn = None
        self.deck = [*CHARACTERS, *CHARACTERS, *CHARACTERS]
        self._state = S_IDLE
        self.sstate = SS_0
        
        
    def receive(self, net_msg: str):
        # Split origin address from the message 
        try:
            net = NetworkMessage(net_msg)
        except SyntaxError:
            self.printv(yellow(f"Invalid message format."))
            return
        if net.msg is None or net.addr is None:
            self.printv(yellow(f"Received {net}"))
            return
        
        # Check for disconnection message
        if net.msg == DISCONNECT:
            # TODO: Remove player from the game and let other players know
            self.printv(f"ID{net.addr} disconnected.")
            return
        
        # Parse the message
        try:
            game = GameMessage(net.msg)
            self.printv(f"ID{net.addr} -> {net.msg}")
        except SyntaxError:
            # Player message breaks Protocol
            self.printv(yellow(f"ID{net.addr} -> {net.msg}"))
            
            self.send_illegal(net.addr)
            return
        
        # Create player state
        if game.command == "HELLO":
            if net.addr in self.players.keys() or len(self.players) == MAX_PLAYERS:
                # Player already exists or game is full
                self.send_illegal(net.addr)
            else:
                # Add new player
                self.players[net.addr] = (PlayerState(net.addr, self.players))
                self.send_single_and_update(game_proto.PLAYER(str(net.addr)), net.addr, R_PLAYER)
            return
        
        # Top-level state machine
        self.update_player_state(net.addr, game)
        if self.all_players_replied():
            self.update_game_state()
    
        # self.debug_player_states()
        # self.debug_player_possible_messages()
    
    ### State machine methods
    
    def update_player_state(self, orig: str, m: GameMessage):
        player = self.players[orig]
        if player is None:
            return
        
        if str(m) not in player.possible_messages or self.state != S_IDLE and player.replied:
            self.send_illegal(orig)
            return
        player.replied = True
        
        # Store the message
        player.msg = m

        if self.state == S_IDLE:  # Initial state
            if player.state == R_PLAYER:
                player.set_state(S_START)
            else:
                player.set_state(S_IDLE)
            if m.command == "READY":
                player.ready = True

        elif self.state == S_START:  # Game setup
            player.coins = STARTING_COINS
            player.set_state(S_IDLE)
            
        elif self.state == S_TURN:    # Waiting for player to take an action
            player.tag = T_NONE
            player.set_state(S_IDLE)
            
        elif self.state == S_ACTION:  # Waiting for players to reply to the action
            if m.command == "BLOCK":
                player.tag = T_BLOCKING
            elif m.command == "CHAL":
                player.tag = T_CHALLENGING
            player.set_state(S_IDLE)
            
        elif self.state == S_BLOCK:   # Waiting for players to reply to the block
            if m.command == "CHAL":
                player.tag = T_CHALLENGING
            player.set_state(S_IDLE)
            
        elif self.state == S_CHAL:    # Waiting for players to reply to the challenge
            player.set_state(S_IDLE)
            
        elif self.state == S_END:    # Game over
            player.set_state(S_IDLE)
    
    def update_game_state(self):
        """Called after all players replied."""
        if self.state == S_IDLE:
            # wait for all players to be ready, send deck
            
            if len(self.players) < MIN_PLAYERS:
                self.printv(yellow(f"Not enough players."))
            elif self.all_players_ready():
                for player in self.players.values():
                    self.generate_player_cards(player)
                    self.send_single_and_update(game_proto.DECK(player.deck[0], player.deck[1]), player.id, R_DECK)
                self.state = S_START
                
        elif self.state == S_START:
            # wait for players to receive deck, send coins and players
            if self.sstate == SS_0:
                # wait for players to receive deck, send coins
                for player in self.players.values():
                    self.send_single_and_update(game_proto.COINS(player.id, player.coins), player.id, R_COINS)
                self.sstate = SS_START_COINS
                
            elif self.sstate == SS_START_COINS:
                # wait for players to receive coins, send players and turn
                for player in self.players.values():
                    # return if there is a player that has not been announced, else break and ask for turn
                    if not player.was_announced:
                        player.was_announced = True
                        self.send_except_and_update(game_proto.PLAYER(player.id), player.id, R_PLAYER)
                        return
                
                # ask player for turn
                self.next_player_turn()
                self.set_all_states(R_OTHER_TURN)
                if self.turn is not None:
                    self.send_all_and_update(game_proto.TURN(self.turn), R_OTHER_TURN)
                    self.players[self.turn].set_state(R_MY_TURN)
                self.state = S_TURN
        
        elif self.state == S_TURN:
            # wait for players to receive turn, send action
            turn = self.turn
            if turn is None:
                self.printv(red("Error in S_TURN: No player has the turn"))
                return
            
            action = self.players[turn].msg.action
            msg = self.players[turn].msg
            
            if action == INCOME:
                self.send_except_and_update(str(msg), turn, R_INCOME)
            elif action == FOREIGN_AID:
                self.send_except_and_update(str(msg), turn, R_FAID)
            elif action == TAX:
                self.send_except_and_update(str(msg), turn, R_TAX)
            elif action == EXCHANGE:
                self.send_except_and_update(str(msg), turn, R_EXCHANGE)
            elif action == ASSASSINATE:
                self.send_except_and_update(str(msg), turn, R_ASSASS)
                if msg.ID2 is not None:
                    self.players[msg.ID2].set_state(R_ASSASS_ME)
            elif action == STEAL:
                self.send_except_and_update(str(msg), turn, R_STEAL)
                if msg.ID2 is not None:
                    self.players[msg.ID2].set_state(R_STEAL_ME)
            elif action == COUP:
                self.send_except_and_update(str(msg), turn, R_COUP)
                if msg.ID2 is not None:
                    self.players[msg.ID2].set_state(R_COUP_ME)
            else:
                self.printv(red(f"Invalid action: {action}"))
            
            self.state = S_ACTION
            
        elif self.state == S_ACTION:
            # wait for players to receive action, assess action replies
            
            if self.turn is None:
                self.printv(red("Error in S_ACTION: No player has the turn"))
                return
            # check if there is a block or challenge
            turn = self.players[self.turn]
            blocking = challenging = None
            for player in self.players.values():
                if player.tag == T_BLOCKING and blocking is None:
                    blocking = player
                elif player.tag == T_CHALLENGING and challenging is None:
                    challenging = player
            
            action = turn.msg.action
            # if there is a block, broadcast block to all other players, then BLOCK
            if blocking is not None:
                if action == FOREIGN_AID:
                    self.send_except_and_update(str(blocking.msg), blocking.id, R_BLOCK_FAID)
                elif action == ASSASSINATE:
                    self.send_except_and_update(str(blocking.msg), blocking.id, R_BLOCK_ASSASS)
                elif action == STEAL and blocking.msg.card1 == CAPTAIN:
                    self.send_except_and_update(str(blocking.msg), blocking.id, R_BLOCK_STEAL_C)
                elif action == STEAL and blocking.msg.card1 == AMBASSADOR:
                    self.send_except_and_update(str(blocking.msg), blocking.id, R_BLOCK_STEAL_B)
                else:
                    self.printv(red(f"Block for invalid action: {action}"))
                    return
                self.state = S_BLOCK
            # if there is a challenge, broadcast challenge to all other players, then CHAL
            elif challenging is not None:
                if action == EXCHANGE:
                    self.send_except_and_update(str(challenging.msg), challenging.id, R_CHAL_B)
                    self.players[self.turn].set_state(R_CHAL_MY_B)
                elif action == TAX:
                    self.send_except_and_update(str(challenging.msg), challenging.id, R_CHAL_D)
                    self.players[self.turn].set_state(R_CHAL_MY_D)
                elif action == ASSASSINATE:
                    self.send_except_and_update(str(challenging.msg), challenging.id, R_CHAL_A)
                    self.players[self.turn].set_state(R_CHAL_MY_A)
                elif action == STEAL:
                    self.send_except_and_update(str(challenging.msg), challenging.id, R_CHAL_C)
                    self.players[self.turn].set_state(R_CHAL_MY_C)
                else:
                    self.printv(red(f"Challenge for invalid action: {action}"))
                    return
                self.state = S_CHAL
            # else perform action, then TURN
            else:
                # TODO: test code above
                # TODO: Perform action
                pass
        elif self.state == S_BLOCK:
            # wait for players to receive block, assess block replies
            # if there is a challenge, broadcast challenge to all other players, then CHAL
            # else perform block, then TURN
            pass
        elif self.state == S_CHAL:
            # wait for players to receive challenge, assess challenge replies
            pass
        elif self.state == S_END:
            pass
    
    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        # Reset substate when changing state
        self._state = value
        self.sstate = SS_0

    def expect_reply_from_everyone(self):
        for player in self.players.values():
            if player.alive:
                player.replied = False
    
    def expect_reply_from(self, id: str):
        if self.players[id].alive:
            self.players[id].replied = False
    
    def dont_expect_reply_from(self, id: str):
        self.players[id].replied = True
    
    def all_players_replied(self):
        for player in self.players.values():
            if not player.replied:
                return False
        return True
    
    def set_all_states(self, state: int):
        for player in self.players.values():
            if player.alive:
                player.set_state(state)
    
    def debug_player_states(self):
        self.printv("Player states:")
        for player in self.players.values():
            self.printv(f"ID{player.id}: {player.state}")
    
    def debug_player_possible_messages(self):
        self.printv("Possible messages:")
        for player in self.players.values():
            self.printv(f"ID{player.id}: {player.possible_messages}")
    
    ### Game methods
    
    def generate_player_cards(self, player: PlayerState):
        card1 = self.take_card(self.deck)
        card2 = self.take_card(self.deck)
        if card1 is None or card2 is None:
            self.printv(red("Not enough cards in the deck."))
            return
        player.deck = [card1, card2]
        
    def replace_card(self, deck: list[str], card: str):
        self.put_card(deck, card)
        return self.take_card(deck)
    
    def put_card(self, deck: list[str], card: str):
        deck.append(card)

    def take_card(self, deck: list[str]):
        if deck:  # Check if deck is not empty
            return deck.pop(random.randint(0, len(deck) - 1))
        return None  # Return None if deck is empty
    
    def next_player_turn(self):
        players_cycle = itertools.cycle(self.players.keys())
        
        # Check if any player has `turn = True`
        current_player_id = None
        for player_id in self.players:
            if self.players[player_id].turn:
                current_player_id = player_id
                break
        
        # If no player has `turn = True`, start from the first player in the cycle
        if current_player_id is None:
            self.turn = next(players_cycle)
            self.players[self.turn].turn = True
            return
        
        # Skip to the current player's position in the cycle and reset their turn
        for player_id in players_cycle:
            if player_id == current_player_id:
                self.players[player_id].turn = False  # Reset current player's turn
                break
        
        # Continue to find the next alive player
        for player_id in players_cycle:
            player = self.players[player_id]
            if player.alive:
                self.turn = player_id
                self.players[player_id].turn = True  # Set next player's turn
                return
    
    def all_players_ready(self):
        
        for player in self.players.values():
            if not player.ready:
                return False
        return True
    
    ### Helper methods
    
    def _send_single(self, game_msg: str, dest: str):
        self.printv(f"ID{int(dest):02d} <- {game_msg}")
        self.checkout.put(network_proto.SINGLE(dest, game_msg))
    
    def _send_all(self, game_msg: str):
        self.printv(f"ALL <- {game_msg}")
        self.checkout.put(network_proto.ALL(game_msg))
    
    def _send_except(self, game_msg: str, exclude: str):
        self.printv(f"NOT ID{exclude} <- {game_msg}")
        self.checkout.put(network_proto.EXCEPT(exclude, game_msg))

    def send_illegal(self, dest: str):
        self._send_single(game_proto.ILLEGAL(), dest)
    
    def send_single_and_update(self, game_msg: str, dest: str, state):
        self._send_single(game_msg, dest)
        if self.players[dest].alive:
            self.players[dest].set_state(state)
            self.expect_reply_from(dest)

    def send_all_and_update(self, game_msg: str, state):
        self._send_all(game_msg)
        self.set_all_states(state)
        self.expect_reply_from_everyone()
    
    def send_except_and_update(self, game_msg: str, exclude: str, state):
        self._send_except(game_msg, exclude)
        for player in self.players.values():
            if player.id != exclude and player.alive:
                player.set_state(state)
                self.expect_reply_from(player.id)

class TestRoot(Player):
    def __init__(self):
        super().__init__()
        self.verbose = True
        self.is_root = True
        self.players: dict[str, PlayerState] = {}
        self.deck = [*CHARACTERS, *CHARACTERS, *CHARACTERS]
    
    def receive(self, net_msg: str):
        try:
            net = NetworkMessage(net_msg)
            if net.msg is not None and net.msg == DISCONNECT:
                if net.addr is not None:
                    self.printv(f"ID{int(net.addr):02d} disconnected.")
                    return
            if net.msg is not None:
                game = GameMessage(net.msg)
        except SyntaxError:
            self.printv(yellow(f"Invalid message format."))
            return
        if net.addr is None:
            self.printv(yellow(f"ID?? -> {net.msg}"))
            return
        self.printv(f"ID{int(net.addr):02d} -> {net.msg}")
        
    def send_single(self, game_msg: str, dest: str):
        self.printv(f"ID{int(dest):02d} <- {game_msg}")
        self.checkout.put(network_proto.SINGLE(dest, game_msg))
    
    def send_all(self, game_msg: str):
        self.printv(f"ALL <- {game_msg}")
        self.checkout.put(network_proto.ALL(game_msg))
    
    def send_except(self, game_msg: str, exclude: str):
        self.printv(f"NOT ID{exclude} <- {game_msg}")
        self.checkout.put(network_proto.EXCEPT(exclude, game_msg))
        
class TestBot(Player, PlayerState):
    """
    TestBot player class.
    """

    def __init__(self):
        Player.__init__(self)
        PlayerState.__init__(self, '0', {})
        self.verbose = True  # Error messages and connection status
        self.ui = False  # User interface like input prompts
        self.rcv_msg = GameMessage(OK)
        self.msg = GameMessage(HELLO)
        self.send_message(self.msg)

    def receive(self, message: str):
        try:
            self.printv(green(str(message)))
            m = GameMessage(message)
            self.pre_update_state(m)
            if self.state not in [S_IDLE, S_END]:
                self.printv(f"State: {self.state}\n Possible messages: {self.possible_messages}")
                self.choose_message()
                self.post_update_state(self.msg)
                self.send_message(self.msg)
                self.rcv_msg = m
                self.printv(blue(str(self.msg)))
        except IndexError:
            self.printv(red(f"No possible messages."))
        except Exception as e:
            self.printv(red(f"Error in receive: " + str(e)))
            traceback.print_exc()

    def pre_update_state(self, message: GameMessage):
        if message.command == HELLO:
            self.set_state(S_IDLE)
            self.printv(yellow(f"Received unexpected message: HELLO"))
        
        elif message.command == READY:
            self.set_state(S_IDLE)
            self.printv(yellow(f"Received unexpected message: READY"))
        
        elif message.command == OK:
            self.set_state(S_IDLE)
            self.printv(yellow(f"Received unexpected message: OK"))
        
        elif message.command == KEEP:
            self.set_state(S_IDLE)
            self.printv(yellow(f"Received unexpected message: KEEP"))
        
        elif message.command == ACT:
            if message.action == INCOME:
                self.set_state(R_INCOME)
            elif message.action == FOREIGN_AID:
                self.set_state(R_FAID)
            elif message.action == TAX:
                self.set_state(R_TAX)
            elif message.action == EXCHANGE:
                self.set_state(R_EXCHANGE)
            elif message.action == ASSASSINATE:
                if message.ID2 == self.id:
                    self.set_state(R_ASSASS_ME)
                else:
                    self.set_state(R_ASSASS)
            elif message.action == STEAL:
                if message.ID2 == self.id:
                    self.set_state(R_STEAL_ME)
                else:
                    self.set_state(R_STEAL)
            elif message.action == COUP:
                if message.ID2 == self.id:
                    self.set_state(R_COUP_ME)
                else:
                    self.set_state(R_COUP)
            else:
                self.set_state(S_IDLE)
                self.printv(red(f"Invalid action: {message.action}"))
                
        elif message.command == BLOCK:
            self.tag = T_NONE
            if self.turn:
                self.tag = T_BLOCKED
                if self.msg.action == FOREIGN_AID:
                    self.set_state(R_BLOCK_FAID)
                elif self.msg.action == ASSASSINATE:
                    self.set_state(R_BLOCK_ASSASS)
                elif self.msg.action == STEAL and message.card1 == CAPTAIN:
                    self.set_state(R_BLOCK_STEAL_C)
                elif self.msg.action == STEAL and message.card1 == AMBASSADOR:
                    self.set_state(R_BLOCK_STEAL_B)
                else:
                    self.set_state(S_IDLE)
                    self.printv(red(f"Invalid action: {self.msg.action}"))
            else: 
                if self.rcv_msg.action == FOREIGN_AID:
                    self.set_state(R_BLOCK_FAID)
                elif self.rcv_msg.action == ASSASSINATE:
                    self.set_state(R_BLOCK_ASSASS)
                elif self.rcv_msg.action == STEAL and message.card1 == CAPTAIN:
                    self.set_state(R_BLOCK_STEAL_C)
                elif self.rcv_msg.action == STEAL and message.card1 == AMBASSADOR:
                    self.set_state(R_BLOCK_STEAL_B)
                else:
                    self.set_state(S_IDLE)
                    self.printv(red(f"Invalid action: {self.rcv_msg.action}"))
                
        elif message.command == CHAL:
            self.tag = T_NONE
            self.printv(f"Deck: {self.deck}")
            if self.rcv_msg.command == ACT:
                if self.rcv_msg.action == ASSASSINATE:
                    self.set_state(R_CHAL_A)
                elif self.rcv_msg.action == EXCHANGE:
                    self.set_state(R_CHAL_B)
                elif self.rcv_msg.action == STEAL:
                    self.set_state(R_CHAL_C)
                elif self.rcv_msg.action == TAX:
                    self.set_state(R_CHAL_D)
                else:
                    self.set_state(S_IDLE)
                    self.printv(red(f"Challenging non-challengeable actions: {str(self.rcv_msg)}"))
            elif self.rcv_msg.command == BLOCK:
                if self.rcv_msg.card1 == CONTESSA:
                    self.set_state(R_CHAL_E)
                else:
                    self.set_state(S_IDLE)
                    self.printv(red(f"Challenging a non-challengeable action: {str(self.rcv_msg)}"))
            elif self.msg.command == ACT:
                if self.msg.action == ASSASSINATE:
                    self.tag = T_CHALLENGED
                    self.set_state(R_CHAL_MY_A)
                elif self.msg.action == EXCHANGE:
                    self.tag = T_CHALLENGED
                    self.set_state(R_CHAL_MY_B)
                elif self.msg.action == STEAL:
                    self.tag = T_CHALLENGED
                    self.set_state(R_CHAL_MY_C)
                elif self.msg.action == TAX:
                    self.tag = T_CHALLENGED
                    self.set_state(R_CHAL_MY_D)
                else:
                    self.set_state(S_IDLE)
                    self.printv(red(f"Challenging non-challengeable actions: {str(self.msg)}"))
            elif self.msg.command == BLOCK:
                if self.msg.card1 == CONTESSA:
                    self.tag = T_CHALLENGED
                    self.set_state(R_CHAL_MY_E)
            else:
                self.set_state(S_IDLE)
                self.printv(red(f"Challenging non-challengeable actions: Mine: {str(self.msg)}, Previous: {str(self.rcv_msg)}"))
                
        elif message.command == SHOW:
            self.set_state(R_SHOW)
                
        elif message.command == LOSE:
            self.set_state(R_LOSE)
            
        elif message.command == COINS:
            self.set_state(R_COINS)
            if message.ID1 is not None and message.coins is not None:
                if message.ID1 == self.id:
                    self.coins = int(message.coins)
                elif message.ID1 in self.players.keys():
                    self.players[message.ID1].coins = int(message.coins)
            
        elif message.command == DECK:
            self.set_state(R_DECK)
            if message.card1 is not None:
                if message.card2 is not None:
                    self.deck = [message.card1, message.card2]
                else:
                    self.deck = [message.card1]
            
        elif message.command == CHOOSE:
            self.set_state(R_CHOOSE)
            
        elif message.command == PLAYER:
            self.set_state(R_PLAYER)
            if message.ID1 is not None:
                if self.id == '0':
                    self.id = str(message.ID1)
                else:
                    self.players[message.ID1] = PlayerState(message.ID1, self.players)
                    self.players[message.ID1].alive = True
            
        elif message.command == START:
            self.set_state(S_START)
            
        elif message.command == TURN:
            if message.ID1 == self.id:
                self.turn = True
                self.set_state(R_MY_TURN)
            else:
                self.turn = False
                self.set_state(R_OTHER_TURN)
                
        elif message.command == EXIT:
            self.set_state(S_END)
            self.printv(f"Received EXIT message.")
            
        elif message.command == ILLEGAL:
            # keep in the same state
            self.printv(yellow(f"Received ILLEGAL message."))
            for msg in self.possible_messages:
                if msg == str(self.msg):
                    self.possible_messages.remove(msg)
            # # ! temporary fix
            # self.set_state(S_IDLE)
            
        else:
            self.set_state(S_IDLE)
            self.printv(red(f"Invalid command: {message.command}"))

    def post_update_state(self, message: GameMessage):      
        if message.command == CHAL:
            self.tag = T_CHALLENGING
            
        elif message.command == BLOCK:
            self.tag = T_BLOCKING
    
    def choose_message(self):
        if len(self.possible_messages) == 0:
            raise IndexError("No possible messages.")
        self.msg = GameMessage(random.choice(self.possible_messages)) # choose random
        # self.msg = GameMessage(self.possible_messages[-1]) # choose last
        # return
        
        # test with priority choices
        msgs: list[GameMessage] = []
        for m in self.possible_messages:
            msgs.append(GameMessage(m))
        for m in msgs:
            if m.command == ACT and m.action == FOREIGN_AID:
                self.msg = m
                return
            elif m.command == BLOCK:
                self.msg = m
                return
        
    
    def send_message(self, message: GameMessage):
        self.msg = message
        self.checkout.put(str(self.msg))
    