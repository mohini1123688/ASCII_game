import random
from dataclasses import dataclass, field
from cards import Card

@dataclass
class Player:
    name: str
    game_state: "Game_State"
    hand: list = field(default_factory=list)
    total: int = 0

    def pick_up_card(self):
        card = self.game_state.draw_from_deck()
        self.game_state.logger.log("player_pick_up", player=self.name, drawn_card_value=card.value, drawn_card_suit=card.suit)
        return card
    
    def reveal_cards(self):
        print(f'Revealed Cards {self.hand[2]} and {self.hand[3]}')
        self.game_state.logger.log("initial_reveal", player=self.name,
            card2_value=self.hand[2].value, card2_suit=self.hand[2].suit,
            card3_value=self.hand[3].value, card3_suit=self.hand[3].suit)

    def play_turn(self):
        new_card = self.pick_up_card()
        print(f"You drew: {new_card}")

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
        self.game_state.logger.log("player_viewed_own", player=self.name, card_viewed_value=card_chosen.value, card_viewed_suit=card_chosen.suit)
        print(f'Own card: {card_chosen}')
    
    def look_at_opponent_card(self, card_chosen, owner):
        self.game_state.logger.log("player_viewed_opponent", player=self.name, card_viewed_value=card_chosen.value, card_viewed_suit=card_chosen.suit,
         opponent=owner)
        print(f'{self.game_state.players[owner]} card: {card_chosen}')
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
class Opponent(Player):
    def reveal_cards(self):
        self.game_state.logger.log("initial_reveal", player=self.name,
            card2_value=self.hand[2].value, card2_suit=self.hand[2].suit,
            card3_value=self.hand[3].value, card3_suit=self.hand[3].suit)
    def play_turn(self):
        new_card = self.pick_up_card()
        print(f"{self.name} drew a card and discarded it.")
        self.game_state.logger.log("player_discard", player=self.name, discarded_card_value=new_card.value, discarded_card_suit=new_card.suit)
        self.game_state.discard_chosen(new_card)
    def react_to_discard(self):
        pass
    def use_power_card(self):
        pass
    def call_cabo_decision(self):
        return False