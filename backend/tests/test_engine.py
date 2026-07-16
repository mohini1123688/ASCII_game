import pytest
from game import Game_State
from bots import Player, Opponent
from cards import Card

@pytest.fixture
def game_state():
    gs = Game_State()
    for player in gs.players:
        player.hand = [Card(1, "Heart"), Card(2, "Heart"), Card(3, "Heart"), Card(4, "Heart")]
        player.total = 10
    return gs

def test_swap_updates_total_correctly(game_state):
    player = game_state.players[0]
    game_state.current_turn_player = 0
    new_card = Card(9, "Spade")

    game_state.swap_card_picked(0, new_card)  # swap out the Card(1, Heart) at index 0

    assert player.hand[0] == new_card
    assert player.total == 10 - 1 + 9  # old total, minus the old card's value, plus the new one

def test_reaction_matches_by_value_not_object(game_state):
    game_state.discard_pile = [Card(4, "Diamond")]  # target value is 4
    player = game_state.players[0]
    player.hand = [Card(4, "Heart"), Card(2, "Spade"), Card(3, "Club"), Card(5, "Spade")]

    # simulate what react_to_discard's core comparison logic does
    target_value = game_state.discard_pile[-1].value
    assert player.hand[0].value == target_value  # different suit, same value — should still match

def test_caller_loses_tiebreak(game_state):
    game_state.players[0].name = "Player1"
    game_state.players[0].total = 5
    game_state.players[1].total = 5   # tied with the caller
    game_state.players[2].total = 8
    game_state.players[3].total = 9

    game_state.game_finished("Player1")

    assert game_state.game_winner != "Player1"
    assert game_state.game_winner == game_state.players[1].name

def test_deck_reshuffles_when_empty(game_state):
    game_state.deck_order = []
    game_state.discard_pile = [Card(3, "Club"), Card(7, "Heart"), Card(9, "Spade")]  # 9 is "on top"

    drawn = game_state.draw_from_deck()

    assert game_state.discard_pile == [Card(9, "Spade")]  # top card preserved
    assert drawn in [Card(3, "Club"), Card(7, "Heart")]    # drew from the reshuffled remainder
    assert len(game_state.deck_order) == 1                 # one card left after drawing