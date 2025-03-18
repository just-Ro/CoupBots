from proto.network_proto import network_proto, NetworkMessage
from proto.network_proto import ALL, SINGLE, EXCEPT, DISCONNECT
from proto.game_proto import game_proto, GameMessage
from proto.game_proto import ACT, OK, CHAL, BLOCK, SHOW, LOSE, COINS, DECK, CHOOSE, KEEP, HELLO, PLAYER, START, READY, TURN, EXIT, ILLEGAL
from .game.core import *
from .game.state_machine import PlayerState, Tag, PlayerSim
from .player import Player
from state_machine.state import State, StateMachine
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
        self.turn_id = None
        self.deck = [*CHARACTERS, *CHARACTERS, *CHARACTERS]
        self.sm = RootStateMachine(self)
        self.turn_challenger = None
        self.turn_blocker = None
        self.blocker_challenger = None
        self.turn_msg = None
            
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
            # Remove player from the game
            # TODO: let other players know that this player disconnected
            self.printv(f"Player {net.addr} disconnected.")
            self.players[net.addr].alive = False
            if self.game_over() and self.sm.current_state.name != "IDLE":
                self.end_game()
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
            if net.addr in self.players.keys() or len(self.players) == MAX_PLAYERS or self.sm.current_state.name != "IDLE":
                # Player already exists or game is full
                self.send_illegal(net.addr)
            else:
                # Add new player
                # TODO: assign first unused ID instead of using the address
                self.players[net.addr] = (PlayerSim(net.addr, self.players))
                self.send_single_and_update(game_proto.PLAYER(str(net.addr)), net.addr, PlayerState.R_PLAYER)
            return
        
        # Top-level state machine
        self.update_player_state(net.addr, game)
        if self.all_players_replied():
            self.sm.update()
            self.printv("")

        self.debug_player_states()
        self.debug_player_possible_messages()

### Player States
    
    def update_player_state(self, orig: str, m: GameMessage):
        player = self.players[orig]
        if player is None:
            return
        
        if str(m) not in player.possible_messages or self.sm.current_state.name != "IDLE" and player.replied:
            self.send_illegal(orig)
            return
        player.replied = True
        
        # Store the message
        player.msg = m

        if self.sm.current_state.name == "IDLE":  # Initial state
            if m.command == READY:
                player.ready = True
            if player.state == PlayerState.R_PLAYER:
                player.set_state(PlayerState.START)
                return
            
        elif self.sm.current_state.name in ("FAID", "TAX", "EXCHANGE", "ASSASS", "STEAL"):  # Waiting for players to reply to the action
            if m.command == BLOCK:
                if self.turn_blocker is None:
                    self.turn_blocker = player
            
            elif m.command == CHAL:
                if self.turn_challenger is None:
                    self.turn_challenger = player
            
        elif self.sm.current_state.name.endswith("BLOCK"):   # Waiting for players to reply to the block
            if m.command == CHAL:
                if self.blocker_challenger is None:
                    self.blocker_challenger = player
            
        elif self.sm.current_state.name == "EXCHANGE_CHOOSE":
            if player.state == PlayerState.R_CHOOSE:
                player.exchange_cards = []
                if m.card1 is not None:
                    if m.card2 is not None:
                        player.deck = [m.card1, m.card2]
                    else:
                        player.deck = [m.card1]
                else:
                    self.printv(red("No cards to exchange."))
                    return
            
        player.set_state(PlayerState.IDLE)
    
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
    
    def debug_player_states(self):
        self.printv("Player states:")
        for player in self.players.values():
            if player.alive:
                self.printv(f"ID{player.id}: {player.state}")
    
    def debug_player_possible_messages(self):
        self.printv("Possible messages:")
        for player in self.players.values():
            if player.alive:
                self.printv(f"ID{player.id}: {player.possible_messages}")

### State Machine Conditions
    
    def all_players_ready(self):
        return all([player.alive and player.ready for player in self.players.values()])
 
    def all_players_announced(self):
        return all([player.alive and player.was_announced for player in self.players.values()])
    
    def action_is_income(self):
        return self.turn_id is not None and self.players[self.turn_id].msg.action == INCOME
    
    def action_is_foreign_aid(self):
        return self.turn_id is not None and self.players[self.turn_id].msg.action == FOREIGN_AID
    
    def action_is_tax(self):
        return self.turn_id is not None and self.players[self.turn_id].msg.action == TAX
    
    def action_is_exchange(self):
        return self.turn_id is not None and self.players[self.turn_id].msg.action == EXCHANGE
    
    def action_is_assassinate(self):
        return self.turn_id is not None and self.players[self.turn_id].msg.action == ASSASSINATE
    
    def action_is_steal(self):
        return self.turn_id is not None and self.players[self.turn_id].msg.action == STEAL
    
    def action_is_coup(self):
        return self.turn_id is not None and self.players[self.turn_id].msg.action == COUP

    def turn_has_block(self):
        return self.turn_blocker is not None
    
    def turn_has_challenge(self):
        return self.turn_challenger is not None
    
    def block_has_challenge(self):
        return self.blocker_challenger is not None
    
    def block_has_challenge_AMB(self):
        return self.blocker_challenger is not None and self.blocker_challenger.msg.card1 == AMBASSADOR
    
    def block_has_challenge_CAP(self):
        return self.blocker_challenger is not None and self.blocker_challenger.msg.card1 == CAPTAIN
    
    def turn_is_bluff(self):
        return self.turn_msg is not None and self.turn_msg.command == LOSE
    
    def block_is_bluff(self):
        return self.turn_blocker is not None and self.turn_blocker.msg.command == LOSE
    
    def game_over(self):
        return sum([player.alive for player in self.players.values()]) <= 1
    
### State Machine Actions
    
    def setup_decks(self):
        for player in self.players.values():
            self.generate_player_cards(player)
            self.send_single_and_update(game_proto.DECK(player.deck[0], player.deck[1]), player.id, PlayerState.R_DECK)
    
    def setup_coins(self):
        for player in self.players.values():
            player.coins = STARTING_COINS
            self.send_single_and_update(game_proto.COINS(player.id, player.coins), player.id, PlayerState.R_COINS)
    
    def setup_players(self):
        for player in self.players.values():
            if not player.was_announced:
                player.was_announced = True
                self.send_except_and_update(game_proto.PLAYER(player.id), player.id, PlayerState.R_PLAYER)
                break
    
    def send_turn(self):
        self.next_player_turn()
        if self.turn_id is None:
            self.printv(red("No player has the turn."))
            return
        
        self.set_all_states(PlayerState.R_OTHER_TURN)
        self.send_all_and_update(game_proto.TURN(self.turn_id), PlayerState.R_OTHER_TURN)
        self.players[self.turn_id].set_state(PlayerState.R_MY_TURN)
    
    def reset_turn(self):
        self.turn_blocker = None
        self.turn_challenger = None
        self.blocker_challenger = None
        if self.turn_id is not None:
            self.turn_msg = self.players[self.turn_id].msg

    def send_income(self):
        if self.turn_id is not None:
            self.send_except_and_update(str(self.turn_msg), self.turn_id, PlayerState.R_INCOME)
    
    def send_foreign_aid(self):
        if self.turn_id is not None:
            self.send_except_and_update(str(self.turn_msg), self.turn_id, PlayerState.R_FAID)
        
    def send_tax(self):
        if self.turn_id is not None:
            self.send_except_and_update(str(self.turn_msg), self.turn_id, PlayerState.R_TAX)
    
    def send_exchange(self):
        if self.turn_id is not None:
            self.send_except_and_update(str(self.turn_msg), self.turn_id, PlayerState.R_EXCHANGE)
    
    def send_assassinate(self):
        if self.turn_id is not None and self.players[self.turn_id].msg.ID2 is not None:
            self.send_except_and_update(str(self.turn_msg), self.turn_id, PlayerState.R_ASSASS)
            self.players[self.players[self.turn_id].msg.ID2].set_state(PlayerState.R_ASSASS_ME)
        
    def send_steal(self):
        if self.turn_id is not None and self.players[self.turn_id].msg.ID2 is not None:
            self.send_except_and_update(str(self.turn_msg), self.turn_id, PlayerState.R_STEAL)
            self.players[self.players[self.turn_id].msg.ID2].set_state(PlayerState.R_STEAL_ME)
    
    def send_coup(self):
        if self.turn_id is not None and self.players[self.turn_id].msg.ID2 is not None:
            self.send_except_and_update(str(self.turn_msg), self.turn_id, PlayerState.R_COUP)
            self.players[self.players[self.turn_id].msg.ID2].set_state(PlayerState.R_COUP_ME)
    
    def income_coins(self):
        if self.turn_id is not None:
            self.players[self.turn_id].coins += INCOME_COINS
            self.send_turn_coins()
    
    def foreign_aid_coins(self):
        if self.turn_id is not None:
            self.players[self.turn_id].coins += FOREIGN_AID_COINS
            self.send_turn_coins()
    
    def tax_coins(self):
        if self.turn_id is not None:
            self.players[self.turn_id].coins += TAX_COINS
            self.send_turn_coins()
    
    def steal_receive_coins(self):
        if self.turn_id is not None and self.turn_msg is not None and self.turn_msg.ID2 is not None:
            self.players[self.turn_id].coins += min(MAX_COIN_STEAL, self.players[self.turn_msg.ID2].coins)
            self.send_turn_coins()
    
    def steal_take_coins(self):
        if self.turn_id is not None and self.turn_msg is not None and self.turn_msg.ID2 is not None:
            self.players[self.turn_msg.ID2].coins -= min(MAX_COIN_STEAL, self.players[self.turn_msg.ID2].coins)
            self.send_all_and_update(game_proto.COINS(self.turn_msg.ID2, self.players[self.turn_msg.ID2].coins), PlayerState.R_COINS)
    
    def send_turn_coins(self):
        if self.turn_id is not None:
            self.send_all_and_update(game_proto.COINS(self.turn_id, self.players[self.turn_id].coins), PlayerState.R_COINS)
    
    def send_foreign_aid_block(self):
        if self.turn_blocker is not None:
            self.send_except_and_update(str(self.turn_blocker.msg), self.turn_blocker.id, PlayerState.R_BLOCK_FAID)
    
    def send_assassinate_block(self):
        if self.turn_blocker is not None:
            self.send_except_and_update(str(self.turn_blocker.msg), self.turn_blocker.id, PlayerState.R_BLOCK_ASSASS)
    
    def send_steal_block(self):
        if self.turn_blocker is not None:
            if self.turn_blocker.msg.card1 == CAPTAIN:
                self.send_except_and_update(str(self.turn_blocker.msg), self.turn_blocker.id, PlayerState.R_BLOCK_STEAL_C)
            elif self.turn_blocker.msg.card1 == AMBASSADOR:
                self.send_except_and_update(str(self.turn_blocker.msg), self.turn_blocker.id, PlayerState.R_BLOCK_STEAL_B)        
    
    def send_challenge_ASS(self):
        if self.turn_id is not None and self.turn_challenger is not None:
            self.send_except_and_update(str(self.turn_challenger.msg), self.turn_challenger.id, PlayerState.R_CHAL_A)
            self.players[self.turn_id].set_state(PlayerState.R_CHAL_MY_A)
    
    def send_challenge_AMB(self):
        if self.turn_blocker is not None and self.blocker_challenger is not None:
            self.send_except_and_update(str(self.blocker_challenger.msg), self.blocker_challenger.id, PlayerState.R_CHAL_B)
            self.players[self.turn_blocker.id].set_state(PlayerState.R_CHAL_MY_B)
        elif self.turn_id is not None and self.turn_challenger is not None:
            self.send_except_and_update(str(self.turn_challenger.msg), self.turn_challenger.id, PlayerState.R_CHAL_B)
            self.players[self.turn_id].set_state(PlayerState.R_CHAL_MY_B)
    
    def send_challenge_CAP(self):
        if self.turn_blocker is not None and self.blocker_challenger is not None:
            self.send_except_and_update(str(self.blocker_challenger.msg), self.blocker_challenger.id, PlayerState.R_CHAL_C)
            self.players[self.turn_blocker.id].set_state(PlayerState.R_CHAL_MY_C)
        elif self.turn_id is not None and self.turn_challenger is not None:
            self.send_except_and_update(str(self.turn_challenger.msg), self.turn_challenger.id, PlayerState.R_CHAL_C)
            self.players[self.turn_id].set_state(PlayerState.R_CHAL_MY_C)
    
    def send_challenge_DUK(self):
        if self.turn_blocker is not None and self.blocker_challenger is not None:
            self.send_except_and_update(str(self.blocker_challenger.msg), self.blocker_challenger.id, PlayerState.R_CHAL_D)
            self.players[self.turn_blocker.id].set_state(PlayerState.R_CHAL_MY_D)
        elif self.turn_id is not None and self.turn_challenger is not None:
            self.send_except_and_update(str(self.turn_challenger.msg), self.turn_challenger.id, PlayerState.R_CHAL_D)
            self.players[self.turn_id].set_state(PlayerState.R_CHAL_MY_D)
    
    def send_challenge_CON(self):
        if self.turn_blocker is not None and self.blocker_challenger is not None:
            self.send_except_and_update(str(self.blocker_challenger.msg), self.blocker_challenger.id, PlayerState.R_CHAL_E)
            self.players[self.turn_blocker.id].set_state(PlayerState.R_CHAL_MY_E)
    
    def send_choose(self):
        if self.turn_id is not None:
            if len(self.players[self.turn_id].deck) == 1:
                self.players[self.turn_id].exchange_cards = [self.take_card(self.deck)]
            else:
                self.players[self.turn_id].exchange_cards = [self.take_card(self.deck), self.take_card(self.deck)]
            self.send_single_and_update(game_proto.CHOOSE(*self.players[self.turn_id].exchange_cards), self.turn_id, PlayerState.R_CHOOSE)
    
    def assassinate_pay(self):
        if self.turn_id is not None:
            self.players[self.turn_id].coins -= ASSASSINATION_COST

    def coup_pay(self):
        if self.turn_id is not None:
            self.players[self.turn_id].coins -= COUP_COST
    
    def assassinate_kill(self):
        if self.turn_msg is not None and self.turn_msg.ID2 is not None:
            self.send_single_and_update(game_proto.LOSE(self.turn_msg.ID2), self.turn_msg.ID2, PlayerState.R_LOSE_ME)
    
    def target_lose(self):
        if self.turn_msg is not None and self.turn_msg.ID2 is not None:
            self.broadcast_lose(self.players[self.turn_msg.ID2])
    
    def turn_lose(self):
        if self.turn_id is not None:
            self.broadcast_lose(self.players[self.turn_id])
    
    def blocker_lose(self):
        if self.turn_blocker is not None:
            self.broadcast_lose(self.turn_blocker)
    
    def challenger_lose(self):
        if self.turn_challenger is not None:
            self.broadcast_lose(self.turn_challenger)
    
    def blocker_challenger_lose(self):
        if self.blocker_challenger is not None:
            self.broadcast_lose(self.blocker_challenger)

    def turn_show(self):
        if self.turn_id is not None:
            self.send_except_and_update(str(self.players[self.turn_id].msg), self.turn_id, PlayerState.R_SHOW)
            self.replace_player_card(self.players[self.turn_id], self.players[self.turn_id].msg.card1)
    
    def blocker_show(self):
        if self.turn_blocker is not None:
            self.send_except_and_update(str(self.turn_blocker.msg), self.turn_blocker.id, PlayerState.R_SHOW)
            self.replace_player_card(self.turn_blocker, self.turn_blocker.msg.card1)
    
    def turn_replace_deck(self):
        if self.turn_id is not None:
            self.send_single_and_update(game_proto.DECK(*self.players[self.turn_id].deck), self.turn_id, PlayerState.R_DECK)
    
    def blocker_replace_deck(self):
        if self.turn_blocker is not None:
            self.send_single_and_update(game_proto.DECK(*self.turn_blocker.deck), self.turn_blocker.id, PlayerState.R_DECK)
    
    def end_game(self):
        self.send_all_and_update(game_proto.EXIT(), PlayerState.END)
    
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
    
    def replace_player_card(self, player: PlayerSim, card: str):
        if card not in player.deck:
            self.printv(red(f"Invalid card to replace: {card}"))
            return
        player.deck.remove(card)
        new_card = self.replace_card(self.deck, card)
        if new_card is not None:
            player.deck.append(new_card)
    
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
            self.turn_id = next(players_cycle)
            self.players[self.turn_id].turn = True
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
                self.turn_id = player_id
                self.players[player_id].turn = True  # Set next player's turn
                return

    def do_action(self, msg: GameMessage, turn: PlayerSim, target: PlayerSim | None):
        if turn is None or msg is None:
            self.printv(red("Error doing action: No player has the turn"))
            return True
        
        if msg.action == INCOME:
            turn.coins += INCOME_COINS
            self.send_all_and_update(game_proto.COINS(self.turn_id, turn.coins), PlayerState.R_COINS)
            
        elif msg.action == FOREIGN_AID:
            turn.coins += FOREIGN_AID_COINS
            self.send_all_and_update(game_proto.COINS(self.turn_id, turn.coins), PlayerState.R_COINS)
        
        elif msg.action == TAX:
            turn.coins += TAX_COINS
            self.send_all_and_update(game_proto.COINS(self.turn_id, turn.coins), PlayerState.R_COINS)
            
        elif msg.action == EXCHANGE:
            if len(turn.deck) == 1:
                turn.exchange_cards = [self.take_card(self.deck)]
            else:
                turn.exchange_cards = [self.take_card(self.deck), self.take_card(self.deck)]
            print(self.players[turn.id].exchange_cards)
            self.send_single_and_update(game_proto.CHOOSE(*turn.exchange_cards), turn.id, PlayerState.R_CHOOSE)
            
        elif msg.action == ASSASSINATE:
            if target is None:
                self.printv(red("Error doing action: No target for assassination."))
                return True
            self.send_except_and_update(str(target.msg), target.id, PlayerState.R_LOSE)
            
        elif msg.action == STEAL:
            if target is None:
                self.printv(red("Error doing action: No target for stealing."))
                return True
            turn.coins += min(MAX_COIN_STEAL, target.coins)
            self.send_all_and_update(game_proto.COINS(self.turn_id, turn.coins), PlayerState.R_COINS)
            
        elif msg.action == COUP:
            if target is None:
                self.printv(red("Error doing action: No target for coup."))
                return True
            self.send_except_and_update(str(target.msg), target.id, PlayerState.R_LOSE)
            
        else:
            self.printv(red(f"Invalid action: {msg.action}"))
            return True
        
        return False
    
### Helper methods
            
    def broadcast_lose(self, target: PlayerSim):
        if target is not None:
            self.send_except_and_update(str(target.msg), target.id, PlayerState.R_LOSE)
            target.deck.remove(target.msg.card1)
            self.send_single_and_update(game_proto.DECK(*target.deck), target.id, PlayerState.R_DECK)
            if len(target.deck) == 0:
                target.alive = False
    
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


class RootStateMachine(StateMachine):
    def __init__(self, root: Root):
        super().__init__(State("IDLE", entry_action=None))
        self.add_transition("IDLE", "SETUP_DECK", root.all_players_ready)
        
        auto = lambda: True
        
        self.new_state("SETUP_DECK", 
                        entry_action=root.setup_decks, 
                        transitions={"SETUP_COINS": auto})
        self.new_state("SETUP_COINS",
                        entry_action=root.setup_coins,
                        transitions={"SETUP_PLAYERS": auto})
        self.new_state("SETUP_PLAYERS",
                        entry_action=root.setup_players,
                        transitions={"TURN": root.all_players_announced,
                                    "SETUP_PLAYERS": auto})
        self.new_state("TURN",
                        entry_action=root.send_turn,
                        exit_action=root.reset_turn,
                        transitions={"INCOME": root.action_is_income,
                                    "FAID": root.action_is_foreign_aid,
                                    "TAX": root.action_is_tax,
                                    "EXCHANGE": root.action_is_exchange,
                                    "ASSASS": root.action_is_assassinate,
                                    "STEAL": root.action_is_steal,
                                    "COUP": root.action_is_coup})
        
        # INCOME
        self.new_state("INCOME",
                        entry_action=root.send_income,
                        transitions={"INCOME_COINS": auto})
        self.new_state("INCOME_COINS",
                        entry_action=root.income_coins,
                        transitions={"TURN": auto})
        
        # FOREIGN AID
        self.new_state("FAID",
                        entry_action=root.send_foreign_aid,
                        transitions={"FAID_BLOCK": root.turn_has_block,
                                    "FAID_COINS": auto})
        self.new_state("FAID_COINS",
                        entry_action=root.foreign_aid_coins,
                        transitions={"TURN": auto})
        self.new_state("FAID_BLOCK",
                        entry_action=root.send_foreign_aid_block,
                        transitions={"FAID_BLOCK_CHAL": root.block_has_challenge,
                                    "TURN": auto})
        self.new_state("FAID_BLOCK_CHAL",
                        entry_action=root.send_challenge_DUK,
                        transitions={"FAID_BLOCK_CHAL_BLUFF": root.block_is_bluff,
                                    "FAID_BLOCK_CHAL_FAIL_1": auto})
        self.new_state("FAID_BLOCK_CHAL_BLUFF",
                        entry_action=root.blocker_lose,
                        transitions={"END": root.game_over,
                                    "FAID_COINS": auto})
        self.new_state("FAID_BLOCK_CHAL_FAIL_1",
                        entry_action=root.blocker_show,
                        transitions={"FAID_BLOCK_CHAL_FAIL_2": auto})
        self.new_state("FAID_BLOCK_CHAL_FAIL_2",
                        entry_action=root.blocker_challenger_lose,
                        transitions={"END": root.game_over,
                                    "FAID_BLOCK_CHAL_FAIL_3": auto})
        self.new_state("FAID_BLOCK_CHAL_FAIL_3",
                        entry_action=root.blocker_replace_deck,
                        transitions={"TURN": auto})
        
        # TAX
        self.new_state("TAX",
                        entry_action=root.send_tax,
                        transitions={"TAX_CHAL": root.turn_has_challenge,
                                     "TAX_COINS": auto})
        self.new_state("TAX_COINS",
                        entry_action=root.tax_coins,
                        transitions={"TURN": auto})
        self.new_state("TAX_CHAL",
                        entry_action=root.send_challenge_DUK,
                        transitions={"TAX_CHAL_BLUFF": root.turn_is_bluff,
                                    "TAX_CHAL_FAIL_1": auto})
        self.new_state("TAX_CHAL_BLUFF",
                        entry_action=root.turn_lose,
                        transitions={"END": root.game_over,
                                    "TURN": auto})
        self.new_state("TAX_CHAL_FAIL_1",
                        entry_action=root.turn_show,
                        transitions={"TAX_CHAL_FAIL_2": auto})
        self.new_state("TAX_CHAL_FAIL_2",
                        entry_action=root.challenger_lose,
                        transitions={"END": root.game_over,
                                    "TAX_CHAL_FAIL_3": auto})
        self.new_state("TAX_CHAL_FAIL_3",
                        entry_action=root.turn_replace_deck,
                        transitions={"TAX_COINS": auto})
        
        # EXCHANGE
        self.new_state("EXCHANGE",
                        entry_action=root.send_exchange,
                        transitions={"EXCHANGE_CHAL": root.turn_has_challenge,
                                    "EXCHANGE_CHOOSE": auto})
        self.new_state("EXCHANGE_CHOOSE",
                        entry_action=root.send_choose,
                        transitions={"TURN": auto})
        self.new_state("EXCHANGE_CHAL",
                        entry_action=root.send_challenge_AMB,
                        transitions={"EXCHANGE_CHAL_BLUFF": root.turn_is_bluff,
                                    "EXCHANGE_CHAL_FAIL_1": auto})
        self.new_state("EXCHANGE_CHAL_BLUFF",
                        entry_action=root.turn_lose,
                        transitions={"END": root.game_over,
                                    "TURN": auto})
        self.new_state("EXCHANGE_CHAL_FAIL_1",
                        entry_action=root.turn_show,
                        transitions={"EXCHANGE_CHAL_FAIL_2": auto})
        self.new_state("EXCHANGE_CHAL_FAIL_2",
                        entry_action=root.challenger_lose,
                        transitions={"END": root.game_over,
                                    "EXCHANGE_CHAL_FAIL_3": auto})
        self.new_state("EXCHANGE_CHAL_FAIL_3",
                        entry_action=root.turn_replace_deck,
                        transitions={"EXCHANGE_CHOOSE": auto})

        # ASSASSINATE
        self.new_state("ASSASS",
                        entry_action=root.send_assassinate,
                        exit_action=root.assassinate_pay,
                        transitions={"ASSASS_BLOCK": root.turn_has_block,
                                     "ASSASS_CHAL": root.turn_has_challenge,
                                     "ASSASS_KILL": auto})
        self.new_state("ASSASS_KILL",
                        entry_action=root.assassinate_kill,
                        transitions={"ASSASS_LOSE": auto})
        self.new_state("ASSASS_LOSE",
                        entry_action=root.target_lose,
                        transitions={"END": root.game_over,
                                     "ASSASS_COINS": auto})
        self.new_state("ASSASS_COINS",
                        entry_action=root.send_turn_coins,
                        transitions={"TURN": auto})
        self.new_state("ASSASS_BLOCK",
                        entry_action=root.send_assassinate_block,
                        transitions={"ASSASS_BLOCK_CHAL": root.block_has_challenge,
                                     "ASSASS_COINS": auto})
        self.new_state("ASSASS_BLOCK_CHAL",
                        entry_action=root.send_challenge_CON,
                        transitions={"ASSASS_BLOCK_CHAL_BLUFF": root.block_is_bluff,
                                     "ASSASS_BLOCK_CHAL_FAIL_1": auto})
        self.new_state("ASSASS_BLOCK_CHAL_BLUFF",
                        entry_action=root.blocker_lose,
                        transitions={"END": root.game_over,
                                     "ASSASS_KILL": auto})
        self.new_state("ASSASS_BLOCK_CHAL_FAIL_1",
                        entry_action=root.blocker_show,
                        transitions={"ASSASS_BLOCK_CHAL_FAIL_2": auto})
        self.new_state("ASSASS_BLOCK_CHAL_FAIL_2",
                        entry_action=root.blocker_challenger_lose,
                        transitions={"END": root.game_over,
                                     "ASSASS_BLOCK_CHAL_FAIL_3": auto})
        self.new_state("ASSASS_BLOCK_CHAL_FAIL_3",
                        entry_action=root.blocker_replace_deck,
                        transitions={"ASSASS_COINS": auto})
        self.new_state("ASSASS_CHAL",
                        entry_action=root.send_challenge_ASS,
                        transitions={"ASSASS_CHAL_BLUFF": root.turn_is_bluff,
                                     "ASSASS_CHAL_FAIL_1": auto})
        self.new_state("ASSASS_CHAL_BLUFF",
                        entry_action=root.turn_lose,
                        transitions={"END": root.game_over,
                                     "ASSASS_COINS": auto})
        self.new_state("ASSASS_CHAL_FAIL_1",
                        entry_action=root.turn_show,
                        transitions={"ASSASS_CHAL_FAIL_2": auto})
        self.new_state("ASSASS_CHAL_FAIL_2",
                        entry_action=root.challenger_lose,
                        transitions={"END": root.game_over,
                                     "ASSASS_CHAL_FAIL_3": auto})
        self.new_state("ASSASS_CHAL_FAIL_3",
                        entry_action=root.turn_replace_deck,
                        transitions={"ASSASS_KILL": auto})
        
        # STEAL
        self.new_state("STEAL",
                        entry_action=root.send_steal,
                        transitions={"STEAL_BLOCK": root.turn_has_block,
                                     "STEAL_CHAL": root.turn_has_challenge,
                                     "STEAL_TAKE": auto})
        self.new_state("STEAL_RECEIVE",
                        entry_action=root.steal_receive_coins,
                        transitions={"STEAL_TAKE": auto})
        self.new_state("STEAL_TAKE",
                        entry_action=root.steal_take_coins,
                        transitions={"TURN": auto})
        self.new_state("STEAL_BLOCK",
                        entry_action=root.send_steal_block,
                        transitions={"STEAL_BLOCK_CHAL": root.block_has_challenge,
                                     "TURN": auto})
        self.new_state("STEAL_BLOCK_CHAL_B",
                        entry_action=root.send_challenge_AMB,
                        transitions={"STEAL_BLOCK_CHAL_BLUFF": root.turn_is_bluff,
                                     "STEAL_BLOCK_CHAL_FAIL_1": auto})
        self.new_state("STEAL_BLOCK_CHAL_C",
                        entry_action=root.send_challenge_CAP,
                        transitions={"STEAL_BLOCK_CHAL_BLUFF": root.block_is_bluff,
                                     "STEAL_BLOCK_CHAL_FAIL_1": auto})
        self.new_state("STEAL_BLOCK_CHAL_BLUFF",
                        entry_action=root.blocker_lose,
                        transitions={"END": root.game_over,
                                     "STEAL_TAKE": auto})
        self.new_state("STEAL_BLOCK_CHAL_FAIL_1",
                        entry_action=root.blocker_show,
                        transitions={"STEAL_BLOCK_CHAL_FAIL_2": auto})
        self.new_state("STEAL_BLOCK_CHAL_FAIL_2",
                        entry_action=root.blocker_challenger_lose,
                        transitions={"END": root.game_over,
                                     "STEAL_BLOCK_CHAL_FAIL_3": auto})
        self.new_state("STEAL_BLOCK_CHAL_FAIL_3",
                        entry_action=root.blocker_replace_deck,
                        transitions={"TURN": auto})
        self.new_state("STEAL_CHAL",
                        entry_action=root.send_challenge_CAP,
                        transitions={"STEAL_CHAL_BLUFF": root.turn_is_bluff,
                                     "STEAL_CHAL_FAIL_1": auto})
        self.new_state("STEAL_CHAL_BLUFF",
                        entry_action=root.turn_lose,
                        transitions={"END": root.game_over,
                                     "TURN": auto})
        self.new_state("STEAL_CHAL_FAIL_1",
                        entry_action=root.turn_show,
                        transitions={"STEAL_CHAL_FAIL_2": auto})
        self.new_state("STEAL_CHAL_FAIL_2",
                        entry_action=root.challenger_lose,
                        transitions={"END": root.game_over,
                                     "STEAL_CHAL_FAIL_3": auto})
        self.new_state("STEAL_CHAL_FAIL_3",
                        entry_action=root.turn_replace_deck,
                        transitions={"STEAL_TAKE": auto})
        
        # COUP
        self.new_state("COUP",
                        entry_action=root.send_coup,
                        exit_action=root.coup_pay,
                        transitions={"COUP_LOSE": auto})
        self.new_state("COUP_LOSE",
                        entry_action=root.target_lose,
                        transitions={"END": root.game_over,
                                     "COUP_COINS": auto})
        self.new_state("COUP_COINS",
                        entry_action=root.send_turn_coins,
                        transitions={"TURN": auto})
        
        # END
        self.new_state("END",
                        entry_action=root.end_game,
                        transitions={})

        
    def new_state(self, name: str, entry_action = None, exit_action = None, transitions = {}):
        self.add_state(State(name, entry_action, exit_action))
        for to_state, condition in transitions.items():
            self.add_transition(name, to_state, condition)
            
            
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
        