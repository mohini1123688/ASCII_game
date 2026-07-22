from engine.bots import Player
from dataclasses import dataclass, field
import random

@dataclass
class Random_Search_Opponent(Player):
    config: dict = field(default_factory=lambda: {
        "swap_margin": 0,                   # range: -3 to 3,
        "who_has_seen_opponent_card": 2,    # range: 1 to 4
        "who_has_seen_my_card": 2,          # range: 1 to 4
        "cabo_known_ratio_threshold": 0.7,  # range: 0.5 to 1
        "cabo_avg_value_threshold": 4,      # range: 2 to 6
    })

    def reveal_cards(self):
        self.game_state.logger.log("initial_reveal", player=self.name,
            card2_value=self.hand[0].value, card2_suit=self.hand[0].suit,
            card3_value=self.hand[1].value, card3_suit=self.hand[1].suit)
        self.mark_seen(self.hand[0])
        self.mark_seen(self.hand[1])
        self.total = self.hand[0].value + self.hand[1].value

    def play_turn(self):
        new_card = self.pick_up_card()
        self.mark_seen(new_card)

        known_cards = [c for c in self.hand if self.has_seen(c)]
        all_cards_known = len(self.hand) > 0 and len(known_cards) == len(self.hand)

        choice = 's' if not all_cards_known else 'd'

        if all_cards_known and max(known_cards, key=lambda c: c.value).value > new_card.value + self.config["swap_margin"]:
            choice = 's'

        for card in known_cards:
            if card.value == new_card.value:
                choice = 'd'

        for opponent in self.game_state.players:
            if opponent is self:
                continue
            for card in opponent.hand:
                if self.has_seen(card) and card.value == new_card.value:
                    choice = 'd'

        if choice == 'd':
            self.game_state.logger.log("player_discard", player=self.name,
                discarded_card_value=new_card.value, discarded_card_suit=new_card.suit)
            self.game_state.discard_chosen(new_card)
        else:
            if not all_cards_known:
                index, swap_choice = next((i, c) for i, c in enumerate(self.hand) if not self.has_seen(c))
            else:
                index, swap_choice = max(enumerate(self.hand), key=lambda x: x[1].value)

            self.game_state.logger.log("player_swap_with_own", player=self.name,
                discarded_card_value=swap_choice.value, discarded_card_suit=swap_choice.suit,
                new_own_card_value=new_card.value, new_own_card_suit=new_card.suit, swapped_index=index)
            self.game_state.swap_card_picked(index, new_card)
            self.mark_seen(new_card)  # the card now in that slot — you just drew it, you know it
            
    def react_to_discard(self):
        discard_value = self.game_state.discard_pile[-1].value

        opponent_card = opponent_idx = opponent_card_idx = None
        for p_idx, opponent in enumerate(self.game_state.players):
            if opponent is self:
                continue
            for c_idx, card in enumerate(opponent.hand):
                if self.has_seen(card) and card.value == discard_value:
                    if len(card.seen_by) < self.config["who_has_seen_opponent_card"]:
                        opponent_card, opponent_idx, opponent_card_idx = card, p_idx, c_idx
                        break
            if opponent_card:
                break

        own_card = own_idx = None
        if opponent_card is None:
            for i, card in enumerate(self.hand):
                if self.has_seen(card) and card.value == discard_value:
                    if len(card.seen_by) >= self.config["who_has_seen_my_card"]:
                        own_card, own_idx = card, i
                        break

        if own_card is not None:
            played_card = self.hand.pop(own_idx)
            self.total -= played_card.value
            self.game_state.discard_chosen(played_card)
            self.game_state.logger.log("player_found_own_match", player=self.name,
                card_discarded_value=played_card.value, card_discarded_suit=played_card.suit)

        elif opponent_card is not None:
            opponent = self.game_state.players[opponent_idx]
            self.game_state.logger.log("player_found_opponent_match", player=self.name,
                card_discarded_value=opponent_card.value, card_discarded_suit=opponent_card.suit,
                opponent=opponent.name)
            matched_card = opponent.hand.pop(opponent_card_idx)
            opponent.total -= matched_card.value
            self.game_state.discard_chosen(matched_card)

            known_cards = [c for c in self.hand if self.has_seen(c)]
            give_idx = self.hand.index(max(known_cards, key=lambda c: c.value)) if known_cards \
                else next((i for i, c in enumerate(self.hand) if not self.has_seen(c)), 0)

            given_card = self.hand.pop(give_idx)
            self.total -= given_card.value
            given_card.owner = opponent_idx
            opponent.hand.append(given_card)
            opponent.total += given_card.value
            self.game_state.logger.log("player_give_card_to_opponent", player=self.name,
                card_given_value=given_card.value, card_given_suit=given_card.suit, opponent=opponent.name)
            
    def use_power_card(self):
        if not self.game_state.discard_pile:
            return

        if self.game_state.discard_pile[-1].value > 7:
            self.game_state.power_time = True
            self.game_state.logger.log("power_time_activated", player=self.name)

        if self.game_state.power_time:
            top_value = self.game_state.discard_pile[-1].value

            if top_value in (7, 8):
                for card in self.hand:
                    if not self.has_seen(card):
                        self.look_at_own_card(card)
                        break

            if top_value in (9, 10):
                opponent, choice = self.pick_opponent_target()
                if opponent is not None:
                    self.look_at_opponent_card(self.game_state.players[opponent].hand[choice], opponent)

            if top_value == 11:
                self.game_state.current_turn_player = (self.game_state.current_turn_player + 1) % 4
                self.game_state.logger.log("skipped_turn", player=self.name)

            if top_value == 12:
                personal = self.pick_own_card_to_give_away()
                opp_idx, opp_card_idx = self.pick_opponent_target()
                if opp_idx is not None:
                    self.game_state.logger.log("blind_swap", player=self.name, opponent=opp_idx,
                                                opp_card=opp_card_idx, personal_card=personal)
                    self.do_swap(personal, opp_idx, opp_card_idx)

            if top_value == 13:
                personal = self.pick_own_card_to_give_away()
                opp_idx, opp_card_idx = self.pick_opponent_target()
                if opp_idx is None:
                    return

                my_card = self.hand[personal]
                opp_card = self.game_state.players[opp_idx].hand[opp_card_idx]
                self.mark_seen(my_card)
                self.mark_seen(opp_card)

                self.game_state.logger.log("reveal_b4_seen_swap", player=self.name, opponent=opp_idx,
                                            opp_card=opp_card_idx, personal_card=personal)

                if my_card.value > opp_card.value:
                    self.do_swap(personal, opp_idx, opp_card_idx)
                    self.game_state.logger.log("confirm_seen_swap", player=self.name, opponent=opp_idx,
                                                opp_card=opp_card_idx, personal_card=personal)

    def pick_own_card_to_give_away(self):
        known = [c for c in self.hand if self.has_seen(c)]
        if known:
            worst = max(known, key=lambda c: c.value)
            return self.hand.index(worst)
        for i, card in enumerate(self.hand):
            if self.has_seen(card): 
                return i
        return 0

    def pick_opponent_target(self):
        candidates = [p for i, p in enumerate(self.game_state.players) if p is not self]
        if not candidates:
            return None, None
        opponent = min(candidates, key=lambda x: len(x.hand))
        opponent_idx = self.game_state.players.index(opponent)
        for i, card in enumerate(opponent.hand):
            if not self.has_seen(card):
                return opponent_idx, i
        return opponent_idx, random.randrange(len(opponent.hand))

    def do_swap(self, personal_idx, opp_idx, opp_card_idx):
        opp_card = self.game_state.players[opp_idx].hand[opp_card_idx]
        my_card = self.hand[personal_idx]

        self.game_state.players[opp_idx].hand[opp_card_idx] = my_card
        self.game_state.players[opp_idx].total += my_card.value - opp_card.value
        self.hand[personal_idx] = opp_card
        self.total += opp_card.value - my_card.value
    
    def call_cabo_decision(self):
        known = [c for c in self.hand if self.has_seen(c)]
        known_ratio = len(known) / len(self.hand) if self.hand else 0
        if known_ratio < self.config["cabo_known_ratio_threshold"]:
            return False
        avg_per_card = sum(c.value for c in known) / len(known)
        return avg_per_card <= self.config["cabo_avg_value_threshold"]
    
    