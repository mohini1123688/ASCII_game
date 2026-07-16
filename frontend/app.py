from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, Grid
from textual.widgets import Static, Button, DataTable


SUIT_SYMBOLS = {"Heart": "♥", "Spade": "♠", "Club": "♣", "Diamond": "♦"}
RED_SUITS = {"Heart", "Diamond"}
RANK_NAMES = {1: "A", 11: "J", 12: "Q", 13: "K"}


def rank_label(value: int) -> str:
    return RANK_NAMES.get(value, str(value))


def card_face(value: int, suit: str, facing: str = "up") -> str:
    rank = rank_label(value)
    symbol = SUIT_SYMBOLS.get(suit, "?")
    left = rank.ljust(2)
    right = rank.rjust(2)

    if facing == "up":
        return (
            f"┌─────┐\n"
            f"│{left}   │\n"
            f"│  {symbol}  │\n"
            f"│   {right}│\n"
            f"└─────┘"
        )
    else:  # "down" — oriented toward the opponent across the table
        return (
            f"┌─────┐\n"
            f"│{right}   │\n"
            f"│  {symbol}  │\n"
            f"│   {left}│\n"
            f"└─────┘"
        )


CARD_BACK = (
    "┌─────┐\n"
    "│     │\n"
    "│  ♦  │\n"
    "│     │\n"
    "└─────┘"
)


class CardWidget(Button):
    def __init__(self, value: int, suit: str, facing: str = "up", face_up: bool = True, **kwargs):
        self.value = value
        self.suit = suit
        self.facing = facing
        self.face_up = face_up
        super().__init__(self._current_face(), classes=self._current_classes(), **kwargs)

    def _current_face(self) -> str:
        return card_face(self.value, self.suit, self.facing) if self.face_up else CARD_BACK

    def _current_classes(self) -> str:
        if not self.face_up:
            return "card face-down"
        color_class = "red-suit" if self.suit in RED_SUITS else "black-suit"
        return f"card {color_class}"

    async def flip(self):
        await self.styles.animate("width", value=1, duration=0.15).wait()
        self.face_up = not self.face_up
        self.update(self._current_face())
        self.set_classes(self._current_classes())
        await self.styles.animate("width", value=7, duration=0.15).wait()


class FaceDownCard(Button):
    def __init__(self, **kwargs):
        super().__init__(CARD_BACK, classes="card face-down", **kwargs)


class DrawnCardSlot(Static):
    """Holds the card a player has just drawn, while they decide swap/discard."""

    def __init__(self, **kwargs):
        super().__init__("", classes="card drawn-card empty-slot", **kwargs)

    def show_card(self, value: int, suit: str):
        color_class = "red-suit" if suit in RED_SUITS else "black-suit"
        self.update(card_face(value, suit))
        self.set_classes(f"card drawn-card {color_class}")

    def clear(self):
        self.update("")
        self.set_classes("card drawn-card empty-slot")


class PlayerHand(Vertical):
    """
    A player's hand, laid out in columns of 2 (top card, bottom card).
    New cards start a fresh column (top slot first), so the hand grows
    left-to-right rather than stacking deeper into existing columns.
    """

    def __init__(self, player_name: str, cards: list, name_position: str = "below",
                 facing: str = "up", **kwargs):
        super().__init__(**kwargs)
        self.player_name = player_name
        self.cards = cards  # list of (value, suit) tuples
        self.name_position = name_position
        self.facing = facing

    def compose(self) -> ComposeResult:
        if self.name_position == "above":
            yield Static(self.player_name, classes="player-name")

        with Horizontal(classes="hand-columns", id=f"{self.player_name}-columns"):
            for col_start in range(0, len(self.cards), 2):
                pair = self.cards[col_start:col_start + 2]
                with Vertical(classes="hand-column"):
                    for i, (value, suit) in enumerate(pair):
                        card_index = col_start + i
                        yield CardWidget(
                            value, suit, facing=self.facing,
                            id=f"{self.player_name}-card-{card_index}"
                        )

        if self.name_position == "below":
            yield Static(self.player_name, classes="player-name")

    def add_card(self, value: int, suit: str):
        """Call when the player picks up an extra card mid-game."""
        columns_container = self.query_one(f"#{self.player_name}-columns", Horizontal)
        new_index = len(self.cards)
        self.cards.append((value, suit))

        if new_index % 2 == 0:
            # start a fresh column, new card goes in the top slot
            new_column = Vertical(classes="hand-column")
            columns_container.mount(new_column)
            new_column.mount(CardWidget(
                value, suit, facing=self.facing, id=f"{self.player_name}-card-{new_index}"
            ))
        else:
            # bottom slot of the most recently created column
            last_column = columns_container.children[-1]
            last_column.mount(CardWidget(
                value, suit, facing=self.facing, id=f"{self.player_name}-card-{new_index}"
            ))


class HelpBox(Static):
    """
    A persistent panel telling a new player what they can currently do.
    Call set_options(...) whenever the game moves to a new decision point.
    """

    DEFAULT_MESSAGE = "Waiting for the game to start..."

    def __init__(self, **kwargs):
        super().__init__(self.DEFAULT_MESSAGE, classes="help-box", **kwargs)

    def set_options(self, title: str, options: list[str]):
        lines = [f"[b]{title}[/b]"] + [f"• {opt}" for opt in options]
        self.update("\n".join(lines))

    def clear_options(self):
        self.update(self.DEFAULT_MESSAGE)


class GameLayout(App):
    CSS_PATH = "styles.tcss"

    def compose(self) -> ComposeResult:
        with Grid(id="table"):
            yield Static("", classes="empty")  # box 1
            yield PlayerHand(
                "Opponent2",
                [(3, "Heart"), (9, "Spade"), (6, "Club"), (12, "Diamond")],
                name_position="above", facing="down", id="opp2-hand"
            )  # box 2
            with Vertical(id="scoreboard-panel"):  # box 3 (top right, centered)
                yield DataTable(id="scoreboard")
            yield PlayerHand(
                "Opponent1",
                [(5, "Club"), (2, "Diamond"), (7, "Spade"), (4, "Heart")],
                name_position="above", facing="down", id="opp1-hand"
            )  # box 4
            with Vertical(id="center-pile"):  # box 5
                with Horizontal(classes="pile-label-row"):
                    yield Static("DECK:", classes="pile-label")
                    yield Static("DISCARD PILE:", classes="pile-label")
                with Horizontal(classes="pile-card-row"):
                    with Vertical(classes="pile-column"):
                        yield FaceDownCard(id="deck-widget")
                        yield Static("PICKED:", classes="pile-sublabel")
                        yield DrawnCardSlot(id="drawn-card-widget")
                    yield CardWidget(7, "Heart", id="discard-widget")
            yield PlayerHand(
                "Opponent3",
                [(10, "Heart"), (1, "Spade"), (11, "Club"), (8, "Diamond")],
                name_position="above", facing="down", id="opp3-hand"
            )  # box 6
            yield Static("", classes="empty")  # box 7
            yield PlayerHand(
                "Player1",
                [(4, "Club"), (8, "Diamond"), (3, "Spade"), (13, "Heart")],
                name_position="below", facing="up", id="human-hand"
            )  # box 8
            yield HelpBox(id="help-box")  # box 9

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Player", "Wins")
        table.add_rows([
            ("Player1", 0),
            ("Opponent1", 0),
            ("Opponent2", 0),
            ("Opponent3", 0),
        ])

        help_box = self.query_one("#help-box", HelpBox)
        help_box.set_options("Your Turn", [
            "Click the deck to draw a card",
            "Or call Cabo to end the round",
        ])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "deck-widget":
            # placeholder demo — real version calls into your engine's
            # pick_up_card(), then shows the actual drawn card here
            drawn_slot = self.query_one("#drawn-card-widget", DrawnCardSlot)
            drawn_slot.show_card(5, "Club")

            help_box = self.query_one("#help-box", HelpBox)
            help_box.set_options("Card Drawn", [
                "Click a card in your hand to swap with it",
                "Or click the discard pile to discard the drawn card",
            ])


if __name__ == "__main__":
    GameLayout().run()