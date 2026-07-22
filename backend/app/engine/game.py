import random
from dataclasses import dataclass, field
from engine.bots import Player, Random_Opponent, Heuristic_Opponent
from engine.cards import Card, Deck
from storage.logger import GameLogger

@dataclass
class Game_State:
    logger: "GameLogger" = field(default_factory=GameLogger)
    players: list = field(default_factory=list)
    game_winner: str = ""
    current_turn_number: int = 1
    current_turn_player: int = 0
    discard_pile: list = field(default_factory=list) # []
    deck_order: list = field(default_factory=list)
    react: bool = False
    power_time: bool = False

    def __post_init__(self):
            if not self.players:
                self.players = [
                    Heuristic_Opponent("Heuristic0", self),
                    Random_Opponent("Random1", self),
                    Random_Opponent("Random2", self),
                    Random_Opponent("Random3", self)
                ]

    def draw_from_deck(self):
        times_reshuffled = 0
        if not self.deck_order:
            times_reshuffled = times_reshuffled + 1
            top_card = self.discard_pile.pop()
            self.deck_order = self.discard_pile
            self.discard_pile = [top_card]
            random.shuffle(self.deck_order)
            self.logger.log("deck_reshuffled", times_reshuffled = {times_reshuffled})
            #print("Deck was empty — reshuffled discard pile into a new deck.")
        return self.deck_order.pop()
    
    def deal_cards(self):
        for index, player in enumerate(self.players):
            for card in range(4):
                self.players[index].total = self.players[index].total + self.deck_order[-1].value
                self.players[index].hand.append(self.deck_order.pop())
    
    def discard_chosen(self, new_card):
        self.discard_pile.append(new_card)
        #print(f"Card discarded: {self.discard_pile[-1]}")

    def swap_card_picked(self, choice, new_card):
        old_card = self.players[self.current_turn_player].hand[choice]
        self.players[self.current_turn_player].total -= old_card.value
        self.discard_pile.append(old_card)
        self.players[self.current_turn_player].hand[choice] = new_card
        self.players[self.current_turn_player].total += new_card.value
    
    def game_finished(self, player_who_called):
        #print(f"called cabo {player_who_called}")
        min_score = min(player.total for player in self.players)
        tied_players = [p for p in self.players if p.total == min_score]

        caller = next((p for p in self.players if p.name == player_who_called), None)

        # Caller only loses the tiebreak if they're actually tied with someone else
        if caller in tied_players and len(tied_players) > 1:
            tied_players = [p for p in tied_players if p is not caller]

        if len(tied_players) > 1:
            min_cards = min(len(p.hand) for p in tied_players)
            tied_players = [p for p in tied_players if len(p.hand) == min_cards]

        if len(tied_players) > 1:
            tied_players = [random.choice(tied_players)]

        self.game_winner = tied_players[0].name
        #print(f"Winner is... {self.game_winner}")
        

def turn(game_state):
    player = game_state.players[game_state.current_turn_player]
    player.play_turn()
    reaction_phase(game_state)

    empty_hand_player = None
    for p in game_state.players:
        if len(p.hand) == 0:
            empty_hand_player = p
            break
        
    if empty_hand_player is not None:
        game_state.game_winner = empty_hand_player.name
        game_state.logger.log("empty_hand_win", player=empty_hand_player.name)
        return
    
    power_card_phase(game_state)

def reaction_phase(game_state):
    for player in game_state.players:
        player.react_to_discard()


def power_card_phase(game_state):
    player = game_state.players[game_state.current_turn_player]
    player.use_power_card()


def main(fresh_game_state):
    game_state = fresh_game_state
    game_deck = Deck(game_state)

    game_state.logger.log("game_start", seed = game_deck.seed)
    game_state.deal_cards()

    #print(f'Initial card count: {len(game_state.deck_order)}')
    #print("START GAME")

    for player in game_state.players:
        player.reveal_cards()

    while game_state.game_winner == "":
        current_index = game_state.current_turn_player
        current_player = game_state.players[current_index]
        game_state.logger.log("current_player_turn", player=current_player.name)

        #print(f"\n--- Turn {game_state.current_turn_number}: {current_player.name} ---")

        end_game = current_player.call_cabo_decision()
        if end_game:
            #print(f"{current_player.name} called Cabo!")
            game_state.logger.log("called_cabo", player=current_player.name)
            game_state.game_finished(current_player.name)
            break

        turn(game_state)

        if game_state.game_winner != "":
            break

        game_state.current_turn_player = (game_state.current_turn_player + 1) % 4
        if game_state.current_turn_player == 0:
            game_state.current_turn_number += 1

    #print(f"\nFinal winner: {game_state.game_winner}")
    game_state.logger.log("final_winner", player=game_state.game_winner)
    game_state.logger.close()
    return game_state.game_winner

if __name__ == "__main__":
    main()