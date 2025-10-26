import logging
import random
from collections import Counter
from enum import IntEnum
from itertools import combinations_with_replacement

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QMessageBox

from viuda_card_config import VALUE_DICT
from .card import Card  # <-- This imports the Card class from the same folder


class HandRank(IntEnum):
    HIGH_CARD = 1
    ONE_PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    POKER = 8
    REPOKER = 9
    STRAIGHT_FLUSH = 10


class Dealer(QObject):
    table_chip_label_updated = pyqtSignal(int)  # Signal for updating table chip label
    side_chip_label_updated = pyqtSignal(int)  # Signal for updating side chip label
    player_chips_updated = pyqtSignal(int, int)  # Signal for updating player chips

    def __init__(
        self,
        game_window,
        player_windows,
        flop,
        table_chip_label,
        side_chip_label,
        table_chips,
        side_chips,
        deck,
    ):
        super().__init__()
        self.game_window = game_window
        self.value_dict = VALUE_DICT
        self.player_windows = player_windows
        self.determined_winner = None
        self.current_player_index = 0
        self.current_flop_index = 0
        self.printed_flop = False
        self.can_deal = True
        self.can_deal_flop = False
        self.last_dealt_card_time = None
        self.last_dealt_flop_time = None
        self.dealt_cards = 0
        self.flop = flop
        self.audio_channel = 0
        self.table_chips = table_chips
        self.side_chips = side_chips
        # self.side_chips = 1
        self.table_chip_label = table_chip_label
        self.side_chip_label = side_chip_label
        self.wild_card_value = None

        self.deck = deck

    def eval_hand1(self, hand):
        logging.info("Dealer Evaluating hand rank")
        value_map = self.value_dict
        values = []
        suits = []
        wildcards = []

        for card in hand:
            if card.is_wild:
                wildcards.append(
                    card.value
                )  # Assuming card.value is a placeholder for wildcards
            else:
                values.append(value_map[str(card.value)])
            suits.append(card.suit)

        # print(
        #     f"Dealer: eval_hand - Hand values before considering wild cards: {values}, suits: {suits}, wildcards: {wildcards}")

        # Generate possible hands considering all wildcards
        best_hand = None
        possible_values = list(
            range(2, 15)
        )  # Possible values for the wild cards (2 to Ace)

        if wildcards:
            for wild_combination in self.get_all_wildcard_combinations(
                wildcards, possible_values
            ):
                possible_hand = sorted(values + wild_combination, reverse=True)
                evaluated_hand = self.evaluate_possible_hand(
                    possible_hand, suits, wildcards
                )
                if not best_hand or evaluated_hand > best_hand:
                    best_hand = evaluated_hand
        else:
            best_hand = self.evaluate_possible_hand(values, suits, wildcards)

        return best_hand

    def eval_hand(self, hand):
        logging.info("Dealer Evaluating hand rank")
        value_map = self.value_dict
        values = []
        suits = []
        wildcards = []

        # --- NEW, CORRECTED LOGIC ---
        for card in hand:
            # A card is a wildcard IF AND ONLY IF its is_wild flag is True.
            if card.is_wild:
                # We add a placeholder value for wildcards, e.g., 0.
                # Its real value will be determined later.
                wildcards.append(0)
            else:
                # For all other cards, including a non-wild Ace, use the standard high value.
                values.append(value_map[str(card.value)])

            suits.append(card.suit)
        # --- END OF NEW LOGIC ---

        print(
            f"Dealer: eval_hand - Hand values: {values}, suits: {suits}, wildcards: {wildcards}"
        )

        # The rest of the method for trying combinations remains the same.
        best_hand = None
        possible_values = list(range(2, 15))

        if wildcards:
            for wild_combination in self.get_all_wildcard_combinations(
                wildcards, possible_values
            ):
                possible_hand = sorted(values + wild_combination, reverse=True)
                evaluated_hand = self.evaluate_possible_hand(
                    possible_hand, suits, wildcards
                )
                if not best_hand or evaluated_hand > best_hand:
                    best_hand = evaluated_hand
        else:
            best_hand = self.evaluate_possible_hand(values, suits, wildcards)

        return best_hand

    def get_all_wildcard_combinations(self, wildcards, possible_values):
        from itertools import combinations_with_replacement

        num_wildcards = len(wildcards)
        return [
            list(comb)
            for comb in combinations_with_replacement(possible_values, num_wildcards)
        ]

    def evaluate_possible_hand(self, values, suits, wildcards):
        count = Counter(values)
        most_common = count.most_common()
        # print(f"Dealer: eval_hand - Evaluating with values: {values} -> Most common: {most_common}")

        is_straight = self.check_straight(values)
        is_flush = self.check_flush(suits)
        poker_result = self.check_poker(most_common)

        if is_straight and is_flush:
            return HandRank.STRAIGHT_FLUSH, values
        elif most_common[0][1] == 4 and len(set(values)) == 4 and len(wildcards) == 1:
            return HandRank.REPOKER, most_common
        elif poker_result:
            return poker_result
        elif most_common[0][1] == 3 and most_common[1][1] == 2:
            return HandRank.FULL_HOUSE, most_common
        elif is_flush:
            return HandRank.FLUSH, values
        elif is_straight:
            return HandRank.STRAIGHT, values
        elif most_common[0][1] == 3:
            return HandRank.THREE_OF_A_KIND, most_common
        elif most_common[0][1] == 2 and most_common[1][1] == 2:
            return HandRank.TWO_PAIR, most_common
        elif most_common[0][1] == 2:
            return HandRank.ONE_PAIR, most_common
        return HandRank.HIGH_CARD, values

    def check_straight(self, values):
        sorted_values = sorted(set(values))
        if len(sorted_values) < 5:
            return False
        for i in range(len(sorted_values) - 4):
            if sorted_values[i + 4] - sorted_values[i] == 4:
                return True
        return False

    def check_flush(self, suits):
        suit_count = Counter(suits)
        return any(count >= 5 for count in suit_count.values())

    def check_poker(self, most_common):
        if len(most_common) == 0:
            return None

        if most_common[0][1] == 4:
            return HandRank.POKER, most_common
        elif most_common[0][1] == 3 and most_common[1][1] == 2:
            return HandRank.FULL_HOUSE, most_common

        return None

    # END hand evaluation ===========================

    def set_wild_card(self, card_value):
        for player_window in self.player_windows:
            for card_label in player_window.cards:
                card = card_label.card
                card.set_wild(card.value == card_value)
                card_label.setPixmap(card.pixmap)

    def update_wild_card_value(self):
        wild_card_value_number = self.table_chips % 13 + 1
        matching_values = [
            key
            for key, value in self.value_dict.items()
            if value == wild_card_value_number
        ]
        if matching_values:
            wild_card_value = matching_values[0]
            self.wild_card_value = wild_card_value
            print(
                f"Dealer: update_wild_card_value - Wild card updated to {self.wild_card_value}"
            )
        else:
            print(
                f"Dealer: update_wild_card_value - No matching wild card value found for table_chips = {self.table_chips}"
            )

        # Update card states
        for player_window in self.player_windows:
            for card in player_window.cards:
                card.set_wild(self.is_wild_card(card))
                card_label = player_window.find_card_label(card)
                if card_label:
                    card_label.setPixmap(card.get_pixmap())

    def determine_wild_card(self):
        wild_card_value = self.table_chips % 13 + 1
        return wild_card_value

    def is_wild_card(self, card):
        return card.value == str(self.determine_wild_card())

    # END ===============================

    def shuffle_deck(self):
        random.shuffle(self.deck)

    def deal(self, deck, num_cards):
        if len(self.deck) < num_cards:
            raise ValueError("Not enough cards in the deck to deal.")
        dealt_cards = self.deck[:num_cards]
        self.deck = self.deck[num_cards:]
        return dealt_cards

    def remaining_cards(self):
        return len(self.deck)

    def draw_card(self):
        if self.deck:
            return self.deck.pop()
        else:
            raise ValueError("No more cards in the deck")

    # Winner & Losser ===============

    # in core/dealer.py

    def determine_winner_and_loser(self, player_windows):
        """
        Evaluates hands for all players and returns the winning and losing windows.
        This method does NOT handle any UI updates.
        """
        all_hands = []
        for window in player_windows:
            player_cards = [item.card for item in window.player_dragwidget.items]
            all_hands.append((window, player_cards))

        evaluated_hands = []
        for window, cards in all_hands:
            hand_eval = self.eval_hand(cards)
            evaluated_hands.append((window, hand_eval, cards))  # Also return the cards

        evaluated_hands.sort(key=lambda x: x[1], reverse=True)

        winning_window, winning_hand, winning_cards = evaluated_hands[0]
        losing_window, losing_hand, losing_cards = evaluated_hands[-1]

        print(
            f"Winner: Player {winning_window.player_number} with hand: {winning_hand}"
        )
        print(f"Loser: Player {losing_window.player_number} with hand: {losing_hand}")

        # Return the actual window objects and their cards
        return winning_window, losing_window, winning_cards

    def display_winner(self, winner_window):
        print(
            f"D1 display_winner - The winner is: Player {winner_window.player_number}"
        )

    # END Winner & Losser ==========

    def update_side_chips(self, amount, game_window):
        print(
            f"D1-3 update_side_chips - Update side chips by {amount}. Current side chips: {self.side_chips}"
        )
        self.side_chips += amount

        if self.side_chips < 0:
            self.side_chips = 0

        print(f"D2-3 update_side_chips - New side chips count: {self.side_chips}")

        # Update the side chip label in the GameWindow
        game_window.update_side_chip_label()

        # Emit signal if side chips have been updated
        self.side_chip_label_updated.emit(self.side_chips)

        # If no side chips are left, remove the side chip label
        if self.side_chips == 0:
            game_window.remove_side_chip_label()

    def update_side_chip_labelOriginal(self, game_window):
        """Update the side chips label via the GameWindow."""
        game_window.update_side_chip_label()

    def update_side_chip_label(self):
        """Updates the side chip label in the GameWindow."""
        self.side_chip_label.setText(f"Side Chips: {self.side_chips}")

    def update_player_chips(self, player_index, amount):
        print(
            f"D1-3 update_player_chips - Updating player chips for player index: {player_index} with amount: {amount}"
        )
        if 0 <= player_index < len(self.player_windows):
            self.player_windows[player_index].player_chips += amount
            if self.player_windows[player_index].player_chips < 0:
                self.player_windows[player_index].player_chips = 0
            print(
                f"D2-3 update_player_chips - New chips count for player index {player_index}: {self.player_windows[player_index].player_chips}"
            )
            self.player_chips_updated.emit(
                player_index, self.player_windows[player_index].player_chips
            )
        else:
            print(
                f"D3-3 update_player_chips - Invalid player index: {player_index} for updating chips."
            )

    def check_for_winner(self):
        if len(self.player_windows) == 1:
            winner = self.player_windows[0]
            # Announce the winner
            QMessageBox.information(
                None,
                "Winner",
                f"D: check_for_winner - Player {winner.player_name} wins the game with {winner.player_chips} chips!",
            )

    def player_out(self, player_window):
        if player_window in self.player_windows:
            print(
                f"D1-2 player_out - Removing player {player_window.player_name} from the game."
            )
            # self.player_windows.remove(player_window)
            player_window.close()
            # self.remove_player(player_window)  # Ensure any additional updates are handled
            self.check_for_game_continuation()
            self.check_for_winner()  # Assuming this method checks if there's a winner or if the game needs to end
        else:
            print(
                f"D2-2 player_out - Player {player_window.player_name} not found in player_windows."
            )

    def check_for_game_continuation1(self):
        """Check if there's only one player left with chips or if the game needs to end."""
        if len(self.player_windows) == 1:
            print(
                "D1-2 check_for_game_continuation - Only one player left. Ending the game."
            )
            self.game_window.final_end_game()  # Assuming final_end_game is the method to end the game
        elif len(self.player_windows) > 1:
            self.game_window.alert_next_hand()  # Proceed to the next hand if the game can continue
        else:
            print(
                "D2-2 check_for_game_continuation - No players left. Ending the game."
            )
            self.game_window.final_end_game()

    # In Dealer class
    def check_for_game_continuation(self):
        """Check if there's only one active player left."""

        # Get the list of statuses from the main game window
        statuses = self.game_window.player_statuses

        # Count how many players are still 'Active'
        active_player_count = statuses.count("Active")

        print(
            f"check_for_game_continuation: Found {active_player_count} active players."
        )

        if active_player_count <= 1:
            print("Only one or zero players left. Ending the game.")
            self.game_window.final_end_game()
        elif active_player_count > 1:
            # More than one player is left, so start the next hand.
            self.game_window.alert_next_hand()
