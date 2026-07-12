import random
from dataclasses import dataclass, field
import threading

suits = ["Heart", "Spade", "Club", "Diamond"]
values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]

@dataclass
class Card:
    value: int
    suit: str

@dataclass
class Deck:
    game_state: "Game_State"
    cards: list = field(default_factory=list)

    def __post_init__(self):
        self.create_deck()
        self.shuffle_deck()
        self.game_state.deck_order = self.cards

    def create_deck(self):
        for suit_type in suits:
            for value in values:
                self.cards.append(Card(value, suit_type))
    
    def shuffle_deck(self):
        random.shuffle(self.cards)

@dataclass
class Player:
    name: str
    game_state: "Game_State"
    hand: list = field(default_factory=list)
    total: int = 0

    def pick_up_card(self):
        return self.game_state.draw_from_deck()
    
    def look_at_own_card(self, card_chosen):
        print(f'Own card: {card_chosen}')
        #Include in data backend!!! (log what player sees)
    
    def look_at_opponent_card(self, card_chosen, owner):
        print(f'{self.game_state.players[owner]} card: {card_chosen}')
        #Include in data backend!!! (log what player sees)
    
    def penalty(self):
        card = self.game_state.draw_from_deck()
        self.hand.append(card)
        self.total += card.value
        print(f'Card added to hand')

@dataclass
class Opponent(Player):
    def play_turn(self):
        new_card = self.pick_up_card()
        print(f"{self.name} drew a card and discarded it.")
        self.game_state.discard_chosen(new_card)

@dataclass
class Game_State:
    players: list = field(default_factory=list)
    game_winner: str = ""
    current_turn_number: int = 1
    current_turn_player: int = 0
    discard_pile: list = field(default_factory=list) # []
    deck_order: list = field(default_factory=list)
    react: bool = False
    power_time: bool = False

    def draw_from_deck(self):
        if not self.deck_order:
            top_card = self.discard_pile.pop()
            self.deck_order = self.discard_pile
            self.discard_pile = [top_card]
            random.shuffle(self.deck_order)
            print("Deck was empty — reshuffled discard pile into a new deck.")
        return self.deck_order.pop()
    def __post_init__(self):
            self.players = [
                Player("Player1", self),
                Opponent("Opponent1", self),
                Opponent("Opponent2", self),
                Opponent("Opponent3", self)
            ]

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

def human_turn(game_state):
    player = game_state.players[game_state.current_turn_player]

    new_card = player.pick_up_card()
    print(f"You drew: {new_card}")

    choice = input("Would you like to swap or discard? (s/d)")
    if choice == 'd':
        game_state.discard_chosen(new_card)
    elif choice == 's':
        swap_choice = int(input(
            "What card would you like to swap with? Top-left(0) Top-right(1) Bottom-left(2) Bottom-right(3)"
        ))
        game_state.swap_card_picked(swap_choice, new_card)

    reaction_phase(game_state)
    power_card_phase(game_state)


def ai_turn(game_state):
    player = game_state.players[game_state.current_turn_player]
    player.play_turn()

def reaction_phase(game_state):
    choice = input("Do you have matching card?(y/n or stop to end round)")
    while choice != 'stop':
        if choice == 'y':
            card_choice = int(input("Which card? Top-left(0) Top-right(1) Bottom-left(2) Bottom-right(3)"))
            played_card = game_state.players[game_state.current_turn_player].hand.pop(card_choice)
            game_state.players[game_state.current_turn_player].total -= played_card.value
            game_state.discard_chosen(played_card)
        if choice == 'n':
            print("You chose no")

        choice = input("Does your opponent have matching card?(y/n)")
        if choice == 'y':
            opponent = int(input("Which opponent? (1,2,3)"))
            opponent_card = int(input("Which card? Top-left(0) Top-right(1) Bottom-left(2) Bottom-right(3)"))
            if game_state.players[opponent].hand[opponent_card].value == game_state.discard_pile[-1].value:
                matched_card = game_state.players[opponent].hand.pop(opponent_card)
                game_state.players[opponent].total -= matched_card.value
                game_state.discard_chosen(matched_card)

                give_choice = int(input(
                    "Which of your cards would you like to give your opponent? Top-left(0) Top-right(1) Bottom-left(2) Bottom-right(3)"
                ))
                given_card = game_state.players[game_state.current_turn_player].hand.pop(give_choice)
                game_state.players[game_state.current_turn_player].total -= given_card.value
                game_state.players[opponent].hand.append(given_card)
                game_state.players[opponent].total += given_card.value
            else:
                game_state.players[game_state.current_turn_player].penalty()
        if choice == 'n':
            print("You chose no")

        choice = input("Do you have matching card?(y/n or stop to end round)")


def power_card_phase(game_state):
    if not game_state.discard_pile:
        return

    if game_state.discard_pile[-1].value > 7:
        game_state.power_time = True

    if game_state.power_time:
        top_value = game_state.discard_pile[-1].value

        if top_value in (7, 8):
            choice = int(input("Which of YOUR cards would you like to look at? Top-left(0) Top-right(1) Bottom-left(2) Bottom-right(3)"))
            print(game_state.players[game_state.current_turn_player].hand[choice])

        if top_value in (9, 10):
            opponent = int(input("Which opponent? (1,2,3)"))
            choice = int(input("Which of YOUR OPPONENTS cards would you like to look at? Top-left(0) Top-right(1) Bottom-left(2) Bottom-right(3)"))
            print(game_state.players[opponent].hand[choice].value)

        if top_value == 11:
            print("turn skipped")
            game_state.current_turn_player = (game_state.current_turn_player + 1) % 4

        if top_value == 12:
            print("blind swap")
            personal = int(input("Which of YOUR cards would you like to swap? Top-left(0) Top-right(1) Bottom-left(2) Bottom-right(3)"))
            opp_idx = int(input("Which opponent would you like to swap with? (1,2,3)"))
            opp_card_idx = int(input("Which of your Opponents cards would you like to swap? Top-left(0) Top-right(1) Bottom-left(2) Bottom-right(3)"))

            opp_card = game_state.players[opp_idx].hand[opp_card_idx]
            my_card = game_state.players[game_state.current_turn_player].hand[personal]

            game_state.players[opp_idx].hand[opp_card_idx] = my_card
            game_state.players[opp_idx].total += my_card.value - opp_card.value
            game_state.players[game_state.current_turn_player].hand[personal] = opp_card
            game_state.players[game_state.current_turn_player].total += opp_card.value - my_card.value

        if top_value == 13:
            print("seen swap")
            personal = int(input("Which of YOUR cards would you like to look at? Top-left(0) Top-right(1) Bottom-left(2) Bottom-right(3)"))
            print(game_state.players[game_state.current_turn_player].hand[personal])
            opp_idx = int(input("Which opponent would you like to look at their card? (1,2,3)"))
            opp_card_idx = int(input("Which of your Opponents cards would you like to look? Top-left(0) Top-right(1) Bottom-left(2) Bottom-right(3)"))
            print(game_state.players[opp_idx].hand[opp_card_idx])

            swap_yes = input("Would you like to swap? (y/n)")
            if swap_yes == "y":
                opp_card = game_state.players[opp_idx].hand[opp_card_idx]
                my_card = game_state.players[game_state.current_turn_player].hand[personal]
                game_state.players[opp_idx].hand[opp_card_idx] = my_card
                game_state.players[opp_idx].total += my_card.value - opp_card.value
                game_state.players[game_state.current_turn_player].hand[personal] = opp_card
                game_state.players[game_state.current_turn_player].total += opp_card.value - my_card.value

        game_state.power_time = False


def main():
    game_state = Game_State()
    game_deck = Deck(game_state)
    game_state.deal_cards()

    print(f'Initial card count: {len(game_state.deck_order)}')
    print("START GAME")
    print(f'Revealed Cards {game_state.players[0].hand[2]} and {game_state.players[0].hand[3]}')

    while game_state.game_winner == "":
        current_index = game_state.current_turn_player
        current_player = game_state.players[current_index]

        print(f"\n--- Turn {game_state.current_turn_number}: {current_player.name} ---")

        if isinstance(current_player, Opponent):
            pass  # AI Cabo-calling logic goes here later
        else:
            choice = input("Would you like to call Cabo? (y/n)")
            if choice == 'y':
                print(f"{current_player.name} called Cabo!")
                game_state.game_finished(current_player.name)
                break

        if isinstance(current_player, Opponent):
            ai_turn(game_state)
        else:
            human_turn(game_state)

        game_state.current_turn_number += 1
        game_state.current_turn_player = (game_state.current_turn_player + 1) % 4

    print(f"\nFinal winner: {game_state.game_winner}")

if __name__ == "__main__":
    main()

