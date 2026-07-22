import random
from dataclasses import dataclass, field

suits = ["Heart", "Spade", "Club", "Diamond"]
values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]

@dataclass
class Card:
    value: int
    suit: str
    owner: int = 5
    seen_by: list = field(default_factory=list)

@dataclass
class Deck:
    game_state: "Game_State"
    cards: list = field(default_factory=list)
    seed: int = field(default_factory=lambda: random.randint(0, 2**31 - 1))

    def __post_init__(self):
        self.create_deck()
        self.shuffle_deck()
        self.game_state.deck_order = self.cards

    def create_deck(self):
        for suit_type in suits:
            for value in values:
                self.cards.append(Card(value, suit_type, 5))
    
    def shuffle_deck(self):
        shuffle_seed = random.Random(self.seed)
        print(f"seed chosen for deck: {self.seed}")
        shuffle_seed.shuffle(self.cards)

