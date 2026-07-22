import random
from dataclasses import dataclass, field
from engine.cards import Card

@dataclass
class Player:
    name: str
    game_state: "Game_State"
    hand: list = field(default_factory=list)
    total: int = 0

    #computes the index every time called so that the index is alwasy accurate, O(n)
    @property
    def player_index(self):
        return self.game_state.players.index(self)

    def has_seen(self, card):
        return self.player_index in card.seen_by

    def mark_seen(self, card):
        if self.player_index not in card.seen_by:
            card.seen_by.append(self.player_index)

    def pick_up_card(self):
        card = self.game_state.draw_from_deck()
        self.game_state.logger.log("player_pick_up", player=self.name, drawn_card_value=card.value, drawn_card_suit=card.suit)
        return card
    
    def reveal_cards(self):
        #print(f'Revealed Cards {self.hand[2]} and {self.hand[3]}')
        self.game_state.logger.log("initial_reveal", player=self.name,
            card2_value=self.hand[2].value, card2_suit=self.hand[2].suit,
            card3_value=self.hand[3].value, card3_suit=self.hand[3].suit)

    def play_turn(self):
        new_card = self.pick_up_card()
        #print(f"You drew: {new_card}")

        choice = input("Would you like to swap or discard? (s/d)")
        if choice == 'd':
            self.game_state.logger.log("player_discard", player=self.name, discarded_card_value=new_card.value, discarded_card_suit=new_card.suit)
            self.game_state.discard_chosen(new_card)
        elif choice == 's':
            swap_choice = int(input(
                "What card would you like to swap with? Top-left(0) Top-right(1) Bottom-left(2) Bottom-right(3)"
            ))
            old_card = self.hand[swap_choice]
            self.game_state.logger.log("player_swap_with_own", player=self.name,
                discarded_card_value=old_card.value, discarded_card_suit=old_card.suit,
                new_own_card_value=new_card.value, new_own_card_suit=new_card.suit,
                swapped_index=swap_choice)
            self.game_state.swap_card_picked(swap_choice, new_card)

    def look_at_own_card(self, card_chosen):
        self.game_state.logger.log("player_viewed_own", player=self.name,
            card_viewed_value=card_chosen.value, card_viewed_suit=card_chosen.suit)
        self.mark_seen(card_chosen)
        #print(f'Own card: {card_chosen}')
    
    def look_at_opponent_card(self, card_chosen, owner):
        self.game_state.logger.log("player_viewed_opponent", player=self.name,
            card_viewed_value=card_chosen.value, card_viewed_suit=card_chosen.suit, opponent=owner)
        self.mark_seen(card_chosen)
        #print(f'{self.game_state.players[owner]} card: {card_chosen}')
        #Include in data backend!!! (log what player sees)
    
    def penalty(self):
        card = self.game_state.draw_from_deck()
        self.hand.append(card)
        self.total += card.value
        print(f'Card added to hand')
        self.game_state.logger.log("player_penalty", player=self.name, card_added_value=card.value, card_added_suit=card.suit)
    
    def react_to_discard(self):
        choice = input("Do you have matching card?(y/n or stop to end round)")
        while choice != 'stop':
            if choice == 'y':
                card_choice = int(input("Which card? Top-left(0) Top-right(1) Bottom-left(2) Bottom-right(3)"))
                if self.hand[card_choice].value == self.game_state.discard_pile[-1].value:
                    played_card = self.hand.pop(card_choice)
                    self.total -= played_card.value
                    self.game_state.discard_chosen(played_card)
                    self.game_state.logger.log("player_found_own_match", player=self.name, card_discarded_value=played_card.value, card_discarded_suit=played_card.suit)
                else:
                    self.penalty()
            if choice == 'n':
                print("You chose no")

            choice = input("Does your opponent have matching card?(y/n)")
            if choice == 'y':
                opponent = int(input("Which opponent? (1,2,3)"))
                opponent_card = int(input("Which card? Top-left(0) Top-right(1) Bottom-left(2) Bottom-right(3)"))
                if self.game_state.players[opponent].hand[opponent_card].value == self.game_state.discard_pile[-1].value:
                    matched_card = self.game_state.players[opponent].hand[opponent_card]
                    self.game_state.logger.log("player_found_opponent_match", player=self.name, card_discarded_value=matched_card.value, card_discarded_suit=matched_card.suit,
                                               opponent=opponent)
                    matched_card = self.game_state.players[opponent].hand.pop(opponent_card)
                    self.game_state.players[opponent].total -= matched_card.value
                    self.game_state.discard_chosen(matched_card)

                    give_choice = int(input(
                        "Which of your cards would you like to give your opponent? Top-left(0) Top-right(1) Bottom-left(2) Bottom-right(3)"
                    ))
                    given_card = self.hand.pop(give_choice)
                    self.total -= given_card.value
                    self.game_state.players[opponent].hand.append(given_card)
                    self.game_state.players[opponent].total += given_card.value
                    self.game_state.logger.log("player_give_card_to_opponent", player=self.name, card_given_value=given_card.value, card_given_suit=given_card.suit,
                                               opponent=opponent)
                else:
                    self.penalty()
            if choice == 'n':
                print("You chose no")
                self.game_state.logger.log("player_no_match", player=self.name)

            choice = input("Do you have matching card?(y/n or stop to end round)")
    
    def use_power_card(self):
        if not self.game_state.discard_pile:
            return

        if self.game_state.discard_pile[-1].value > 7:
            self.game_state.power_time = True
            self.game_state.logger.log("power_time_activated", player=self.name)
        
        choice = int(input("Would you like to use your power card?"))
        if choice == 'n':
            self.game_state.power_time = False

        if self.game_state.power_time:
            top_value = self.game_state.discard_pile[-1].value

            if top_value in (7, 8):
                choice = int(input("Which of YOUR cards would you like to look at? Top-left(0) Top-right(1) Bottom-left(2) Bottom-right(3)"))
                self.look_at_own_card(self.hand[choice])

            if top_value in (9, 10):
                opponent = int(input("Which opponent? (1,2,3)"))
                choice = int(input("Which of YOUR OPPONENTS cards would you like to look at? Top-left(0) Top-right(1) Bottom-left(2) Bottom-right(3)"))
                self.look_at_opponent_card(self.game_state.players[opponent].hand[choice], opponent)

            if top_value == 11:
                print("turn skipped")
                self.game_state.current_turn_player = (self.game_state.current_turn_player + 1) % 4
                self.game_state.logger.log("skipped_turn", player=self.name)

            if top_value == 12:
                print("blind swap")
                personal = int(input("Which of YOUR cards would you like to swap? Top-left(0) Top-right(1) Bottom-left(2) Bottom-right(3)"))
                opp_idx = int(input("Which opponent would you like to swap with? (1,2,3)"))

                opp_card_idx = int(input("Which of your Opponents cards would you like to swap? Top-left(0) Top-right(1) Bottom-left(2) Bottom-right(3)"))
                self.game_state.logger.log("blind_swap", player=self.name, opponent=opp_idx, opp_card=opp_card_idx, 
                                           personal_card=personal)
                
                opp_card = self.game_state.players[opp_idx].hand[opp_card_idx]
                my_card = self.game_state.players[self.game_state.current_turn_player].hand[personal]

                self.game_state.players[opp_idx].hand[opp_card_idx] = my_card
                self.game_state.players[opp_idx].total += my_card.value - opp_card.value
                self.game_state.players[self.game_state.current_turn_player].hand[personal] = opp_card
                self.game_state.players[self.game_state.current_turn_player].total += opp_card.value - my_card.value

            if top_value == 13:
                print("seen swap")
                personal = int(input("Which of YOUR cards would you like to look at? Top-left(0) Top-right(1) Bottom-left(2) Bottom-right(3)"))
                print(self.game_state.players[self.game_state.current_turn_player].hand[personal])
                opp_idx = int(input("Which opponent would you like to look at their card? (1,2,3)"))
                opp_card_idx = int(input("Which of your Opponents cards would you like to look? Top-left(0) Top-right(1) Bottom-left(2) Bottom-right(3)"))
                print(self.game_state.players[opp_idx].hand[opp_card_idx])

                self.game_state.logger.log("reveal_b4_seen_swap", player=self.name, opponent=opp_idx, opp_card=opp_card_idx, 
                                           personal_card=personal)
                
                swap_yes = input("Would you like to swap? (y/n)")
                if swap_yes == "y":
                    opp_card = self.game_state.players[opp_idx].hand[opp_card_idx]
                    my_card = self.game_state.players[self.game_state.current_turn_player].hand[personal]
                    self.game_state.players[opp_idx].hand[opp_card_idx] = my_card
                    self.game_state.players[opp_idx].total += my_card.value - opp_card.value
                    self.game_state.players[self.game_state.current_turn_player].hand[personal] = opp_card
                    self.game_state.players[self.game_state.current_turn_player].total += opp_card.value - my_card.value

                    self.game_state.logger.log("confirm_seen_swap", player=self.name, opponent=opp_idx, opp_card=opp_card_idx, 
                                           personal_card=personal)

    def call_cabo_decision(self):
        choice = input("Would you like to call Cabo? (y/n)")
        if choice == 'y':
            return True
        else:
            return False
            
@dataclass
class Random_Opponent(Player):
    def reveal_cards(self):
        self.game_state.logger.log("initial_reveal", player=self.name,
            card2_value=self.hand[2].value, card2_suit=self.hand[2].suit,
            card3_value=self.hand[3].value, card3_suit=self.hand[3].suit)

        self.total = self.hand[2].value + self.hand[3].value
    def play_turn(self):
        new_card = self.pick_up_card()
        #print(f"{self.name} drew a card and discarded it.")
        self.game_state.logger.log("player_discard", player=self.name, discarded_card_value=new_card.value, discarded_card_suit=new_card.suit)
        self.game_state.discard_chosen(new_card)
    def react_to_discard(self):
        pass
    def use_power_card(self):
        pass
    def call_cabo_decision(self):
        cabo_decision = random.random()
        if cabo_decision > 0.8:
            return True
        return False

@dataclass
class Heuristic_Opponent(Player):

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

        if all_cards_known and max(known_cards, key=lambda c: c.value).value > new_card.value:
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
                    opponent_card, opponent_idx, opponent_card_idx = card, p_idx, c_idx
                    break
            if opponent_card:
                break

        own_card = own_idx = None
        if opponent_card is None:
            for i, card in enumerate(self.hand):
                if self.has_seen(card) and card.value == discard_value:
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
            if not self.has_seen(card):
                return i
        return 0

    def pick_opponent_target(self):
        candidates = [p for i, p in enumerate(self.game_state.players) if p is not self]
        if not candidates:
            return None, None
        opponent = random.choice(candidates)
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
        if known_ratio < 0.7:
            return False
        avg_per_card = sum(c.value for c in known) / len(known)
        return avg_per_card <= 4