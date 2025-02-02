from proto.network_proto import network_proto, NetworkMessage
from proto.network_proto import ALL, SINGLE, EXCEPT, DISCONNECT
from proto.game_proto import game_proto, GameMessage
from proto.game_proto import ACT, OK, CHAL, BLOCK, SHOW, LOSE, COINS, DECK, CHOOSE, KEEP, HELLO, PLAYER, START, READY, TURN, EXIT, ILLEGAL
from .game.core import *
from .game.state_machine import State, SubState, PlayerState, Tag, PlayerSim
from .player import Player
from utils.colored_text import red, green, yellow, blue
import random
import itertools


class Root(Player):
    """
    Root player class.

    This player sends and receives addressed messages, e.g. orig@message
    """

    def __init__(self):
        super().__init__()
        self.verbose = True
        self.is_root = True
        self.players: dict[str, PlayerSim] = {}
        self.turn = None
        self.deck = [*CHARACTERS, *CHARACTERS, *CHARACTERS]
        self._state = State.S_IDLE
        self.sstate = SubState.SS_0
        self.turn_challenger = None
        self.turn_blocker = None
        self.blocker_challenger = None
        
        
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
            self.printv(f"Player {net.addr} disconnected.")
            return
        
        # Parse the message
        try:
            game = GameMessage(net.msg)
            self.printv(f"Received from player {net.addr}: {net.msg}")
        except SyntaxError:
            # Player message breaks Protocol
            self.printv(yellow(f"Received from player {net.addr}: {net.msg}"))
            
            self.send_illegal(net.addr)
            return
        
        # Create player state
        if game.command == HELLO:
            if net.addr in self.players.keys() or len(self.players) == MAX_PLAYERS:
                # Player already exists or game is full
                self.send_illegal(net.addr)
            else:
                # Add new player
                self.players[net.addr] = (PlayerSim(net.addr, self.players))
                self.send_single_and_update(game_proto.PLAYER(str(net.addr)), net.addr, PlayerState.R_PLAYER)
            return
        
        # Top-level state machine
        self.update_player_state(net.addr, game)
        if self.all_players_replied():
            self.update_game_state()
            self.printv("")

        # self.debug_player_states()
        # self.debug_player_possible_messages()
    
    ### State machine methods
    
    def update_player_state(self, orig: str, m: GameMessage):
        player = self.players[orig]
        if player is None:
            return
        
        if str(m) not in player.possible_messages or self.state != State.S_IDLE and player.replied:
            self.send_illegal(orig)
            return
        player.replied = True
        
        # Store the message
        player.msg = m

        if self.state == State.S_IDLE:  # Initial state
            if player.state == PlayerState.R_PLAYER:
                player.set_state(PlayerState.START)
            else:
                player.set_state(PlayerState.IDLE)
            if m.command == READY:
                player.ready = True

        elif self.state == State.S_START:  # Game setup
            player.coins = STARTING_COINS
            player.set_state(PlayerState.IDLE)
            
        elif self.state == State.S_TURN:    # Waiting for player to take an action
            player.tag = Tag.T_NONE
            player.set_state(PlayerState.IDLE)
            
        elif self.state == State.S_ACTION:  # Waiting for players to reply to the action
            if m.command == BLOCK:
                player.tag = Tag.T_BLOCKING
                if self.turn_blocker is None:
                    self.turn_blocker = player
            
            elif m.command == CHAL:
                player.tag = Tag.T_CHALLENGING
                if self.turn_challenger is None:
                    self.turn_challenger = player
            
            player.set_state(PlayerState.IDLE)
            
        elif self.state == State.S_BLOCK:   # Waiting for players to reply to the block
            if m.command == CHAL:
                player.tag = Tag.T_CHALLENGING
            player.set_state(PlayerState.IDLE)
            
        elif self.state == State.S_CHAL:    # Waiting for players to reply to the challenge
            player.set_state(PlayerState.IDLE)
            
        elif self.state == State.S_END:    # Game over
            player.set_state(PlayerState.IDLE)
    
    def update_game_state(self):
        """Called after all players replied."""
        
        if self.state == State.S_IDLE:
            # wait for all players to be ready, send deck
            
            if len(self.players) < MIN_PLAYERS:
                self.printv(yellow(f"Not enough players."))
            elif self.all_players_ready():
                for player in self.players.values():
                    self.generate_player_cards(player)
                    self.send_single_and_update(game_proto.DECK(player.deck[0], player.deck[1]), player.id, PlayerState.R_DECK)
                self.state = State.S_START
                
        elif self.state == State.S_START:
            # wait for players to receive deck, send coins and players
            if self.sstate == SubState.SS_0:
                # wait for players to receive deck, send coins
                for player in self.players.values():
                    self.send_single_and_update(game_proto.COINS(player.id, player.coins), player.id, PlayerState.R_COINS)
                self.sstate = SubState.SS_START_COINS
                
            elif self.sstate == SubState.SS_START_COINS:
                # wait for players to receive coins, send players and turn
                for player in self.players.values():
                    # return if there is a player that has not been announced, else break and ask for turn
                    if not player.was_announced:
                        player.was_announced = True
                        self.send_except_and_update(game_proto.PLAYER(player.id), player.id, PlayerState.R_PLAYER)
                        return
                
                # ask player for turn
                self.next_player_turn()
                self.set_all_states(PlayerState.R_OTHER_TURN)
                if self.turn is not None:
                    self.send_all_and_update(game_proto.TURN(self.turn), PlayerState.R_OTHER_TURN)
                    self.players[self.turn].set_state(PlayerState.R_MY_TURN)
                self.state = State.S_TURN
        
        elif self.state == State.S_TURN:
            # wait for players to receive turn, send action

            if self.turn is None:
                self.printv(red("Error updating game state: No player has the turn"))
                return

            if self.send_turn(self.players[self.turn].msg, self.players[self.turn]):
                return
            
            self.state = State.S_ACTION
            self.reset_turn()
            
        elif self.state == State.S_ACTION:
            # wait for players to receive action, assess action replies
            if self.turn is None:
                self.printv(red("Error updating game state: No player has the turn"))
                return
            
            # if there is a block, broadcast block to all other players, then BLOCK
            if self.turn_blocker is not None:
                if self.send_turn_block(self.players[self.turn].msg, self.turn_blocker):
                    return
                self.state = State.S_BLOCK
                
            # if there is a challenge, broadcast challenge to all other players, then CHAL
            elif self.turn_challenger is not None:
                if self.send_turn_chal(self.players[self.turn].msg, self.turn_challenger):
                    return
                self.state = State.S_CHAL
                
            # else perform action, then TURN
            else:
                # TODO: test code above
                # TODO: Perform action
                pass
        
        elif self.state == State.S_DO_ACTION:
            
            if self.turn is None:
                self.printv(red("Error updating game state: No player has the turn"))
                return
            
            pass
        
        elif self.state == State.S_BLOCK:
            # wait for players to receive block, assess block replies
            if self.turn is None:
                self.printv(red("Error updating game state: No player has the turn"))
                return
            
            # if there is a challenge, broadcast challenge to all other players, then CHAL
            if self.blocker_challenger is not None:
                if self.send_block_chal(self.players[self.turn].msg, self.blocker_challenger):
                    return
                self.state = State.S_CHAL
            
            # else perform block, then TURN
            else:
                # TODO: test code above
                # TODO: Perform block
                pass
                
        elif self.state == State.S_CHAL:
            # wait for players to receive challenge, assess challenge replies
            if self.turn is None:
                self.printv(red("Error updating game state: No player has the turn"))
                return
            
        elif self.state == State.S_END:
            pass
    
    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        # Reset substate when changing state
        self._state = value
        self.sstate = SubState.SS_0

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
    
    def set_all_states(self, state: PlayerState):
        for player in self.players.values():
            if player.alive:
                player.set_state(state)
    
    def reset_turn(self):
        self.turn_blocker = None
        self.turn_challenger = None
        self.blocker_challenger = None
    
    def debug_player_states(self):
        self.printv("Player states:")
        for player in self.players.values():
            self.printv(f"ID{player.id}: {player.state}")
    
    def debug_player_possible_messages(self):
        self.printv("Possible messages:")
        for player in self.players.values():
            self.printv(f"ID{player.id}: {player.possible_messages}")
    
    ### Game methods
    
    def generate_player_cards(self, player: PlayerSim):
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
    
    def send_turn(self, msg: GameMessage, turn: PlayerSim):
        if msg.action == INCOME:
            self.send_except_and_update(str(msg), turn.id, PlayerState.R_INCOME)
        elif msg.action == FOREIGN_AID:
            self.send_except_and_update(str(msg), turn.id, PlayerState.R_FAID)
        elif msg.action == TAX:
            self.send_except_and_update(str(msg), turn.id, PlayerState.R_TAX)
        elif msg.action == EXCHANGE:
            self.send_except_and_update(str(msg), turn.id, PlayerState.R_EXCHANGE)
        elif msg.action == ASSASSINATE:
            self.send_except_and_update(str(msg), turn.id, PlayerState.R_ASSASS)
            if msg.ID2 is not None:
                self.players[msg.ID2].set_state(PlayerState.R_ASSASS_ME)
        elif msg.action == STEAL:
            self.send_except_and_update(str(msg), turn.id, PlayerState.R_STEAL)
            if msg.ID2 is not None:
                self.players[msg.ID2].set_state(PlayerState.R_STEAL_ME)
        elif msg.action == COUP:
            self.send_except_and_update(str(msg), turn.id, PlayerState.R_COUP)
            if msg.ID2 is not None:
                self.players[msg.ID2].set_state(PlayerState.R_COUP_ME)
        else:
            self.printv(red(f"Invalid action: {msg.action}"))
            return True
        return False
    
    def send_turn_block(self, msg: GameMessage, blocker: PlayerSim):
        if msg.action == FOREIGN_AID:
            self.send_except_and_update(str(blocker.msg), blocker.id, PlayerState.R_BLOCK_FAID)
        elif msg.action == ASSASSINATE:
            self.send_except_and_update(str(blocker.msg), blocker.id, PlayerState.R_BLOCK_ASSASS)
        elif msg.action == STEAL and blocker.msg.card1 == CAPTAIN:
            self.send_except_and_update(str(blocker.msg), blocker.id, PlayerState.R_BLOCK_STEAL_C)
        elif msg.action == STEAL and blocker.msg.card1 == AMBASSADOR:
            self.send_except_and_update(str(blocker.msg), blocker.id, PlayerState.R_BLOCK_STEAL_B)
        else:
            self.printv(red(f"Block for invalid action: {msg.action}"))
            return True
        return False
    
    def send_turn_chal(self, msg: GameMessage, challenger: PlayerSim):
        if self.turn is None:
            return True
        if msg.action == EXCHANGE:
            self.send_except_and_update(str(challenger.msg), challenger.id, PlayerState.R_CHAL_B)
            self.players[self.turn].set_state(PlayerState.R_CHAL_MY_B)
        elif msg.action == TAX:
            self.send_except_and_update(str(challenger.msg), challenger.id, PlayerState.R_CHAL_D)
            self.players[self.turn].set_state(PlayerState.R_CHAL_MY_D)
        elif msg.action == ASSASSINATE:
            self.send_except_and_update(str(challenger.msg), challenger.id, PlayerState.R_CHAL_A)
            self.players[self.turn].set_state(PlayerState.R_CHAL_MY_A)
        elif msg.action == STEAL:
            self.send_except_and_update(str(challenger.msg), challenger.id, PlayerState.R_CHAL_C)
            self.players[self.turn].set_state(PlayerState.R_CHAL_MY_C)
        else:
            self.printv(red(f"Challenge for invalid action: {msg.action}"))
            return True
        return False
    
    def send_block_chal(self, msg: GameMessage, challenger: PlayerSim):
        pass
    
    ### Helper methods
    
    def _send_single(self, game_msg: str, dest: str):
        self.printv(f"Sent to player {dest}: {game_msg}")
        self.checkout.put(network_proto.SINGLE(dest, game_msg))
    
    def _send_all(self, game_msg: str):
        self.printv(f"Sent to ALL players: {game_msg}")
        self.checkout.put(network_proto.ALL(game_msg))
    
    def _send_except(self, game_msg: str, exclude: str):
        self.printv(f"Sent to all except player {exclude}: {game_msg}")
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
        self.players: dict[str, PlayerSim] = {}
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
        