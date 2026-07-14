import random
from dataclasses import dataclass, field
from bots import Player, Opponent
from cards import Card, Deck
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
            self.players = [
                Player("Player1", self),
                Opponent("Opponent1", self),
                Opponent("Opponent2", self),
                Opponent("Opponent3", self)
            ]

    def draw_from_deck(self):
        if not self.deck_order:
            top_card = self.discard_pile.pop()
            self.deck_order = self.discard_pile
            self.discard_pile = [top_card]
            random.shuffle(self.deck_order)
            print("Deck was empty — reshuffled discard pile into a new deck.")
        return self.deck_order.pop()
    
    def deal_cards(self):
        for index, player in enumerate(self.players):
            for card in range(4):
                self.players[index].total = self.players[index].total + self.deck_order[-1].value
                self.players[index].hand.append(self.deck_order.pop())
    
    def discard_chosen(self, new_card):
        self.discard_pile.append(new_card)
        print(f"Card discarded: {self.discard_pile[-1]}")

    def swap_card_picked(self, choice, new_card):
        old_card = self.players[self.current_turn_player].hand[choice]
        self.players[self.current_turn_player].total -= old_card.value
        self.discard_pile.append(old_card)
        self.players[self.current_turn_player].hand[choice] = new_card
        self.players[self.current_turn_player].total += new_card.value
    
    def game_finished(self, player_who_called):
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
        print(f"Winner is... {self.game_winner}")
            
    def ten_second_timer(self):
        print("10 second timer starting!")
        global times_up 
        times_up = True
        print("Times up!")

def turn(game_state):
    player = game_state.players[game_state.current_turn_player]
    player.play_turn()
    reaction_phase(game_state)
    power_card_phase(game_state)

def reaction_phase(game_state):
    for player in game_state.players:
        player.react_to_discard()


def power_card_phase(game_state):
    player = game_state.players[game_state.current_turn_player]
    player.use_power_card()

def main():
    game_state = Game_State()
    game_deck = Deck(game_state)

    game_state.logger.log("game_start", seed=game_deck.seed)
    game_state.deal_cards()

    print(f'Initial card count: {len(game_state.deck_order)}')
    print("START GAME")

    for player in game_state.players:
        player.reveal_cards()

    while game_state.game_winner == "":
        current_index = game_state.current_turn_player
        current_player = game_state.players[current_index]
        game_state.logger.log("curren_player_turn", player=current_player.name)

        print(f"\n--- Turn {game_state.current_turn_number}: {current_player.name} ---")

        end_game = current_player.call_cabo_decision()
        if end_game:
            print(f"{current_player.name} called Cabo!")
            game_state.logger.log("called_cabo", player=current_player.name)
            game_state.game_finished(current_player.name)
            break

        turn(game_state)

        game_state.current_turn_player = (game_state.current_turn_player + 1) % 4
        if game_state.current_turn_player == 0:
            game_state.current_turn_number += 1

    print(f"\nFinal winner: {game_state.game_winner}")
    game_state.logger.log("final_winner", player=game_state.game_winner)
    game_state.logger.close()

if __name__ == "__main__":
    main()