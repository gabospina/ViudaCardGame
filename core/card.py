import os
import random
import logging
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QPen
from viuda_card_config import CARD_VALUES, CARD_SUITS, VALUE_DICT


class Card:
    def __init__(self, value, suit, is_wild=False):
        if value not in CARD_VALUES:
            raise ValueError(f"Invalid card value: {value}")
        if suit not in CARD_SUITS:
            raise ValueError(f"Invalid card suit: {suit}")
        self.value = value
        self.suit = suit
        self.is_wild = is_wild  # Initialize with the given wild status
        self.face_up = False
        self.id = f"{self.value}{self.suit}"
        self.pixmap = QPixmap()  # Initialize pixmap
        self.load_image()

    def __str__(self):
        return f"{self.value} of {self.suit}" + (" (Wild)" if self.is_wild else "")

    def __repr__(self):
        return f"{self.value}{self.suit}"

    # wild card ===================
    def load_image(self):
        """Load the image for the card and add a red border if it's a wild card."""
        img_path = os.path.join("graphics/cards", f"{self.id}.png")
        self.pixmap = QPixmap(img_path)
        if self.is_wild:
            self.add_red_border()
            # print(f"Card: load_image - Red border added to wild card: {self.id}")

    def add_red_border(self):
        if not self.pixmap.isNull():
            painter = QPainter(self.pixmap)
            pen = QPen(Qt.red, 5)
            painter.setPen(pen)
            painter.drawRect(0, 0, self.pixmap.width() - 1, self.pixmap.height() - 1)
            painter.end()

    def highlight_wild_card(self, card_label, is_face_up):
        if card_label is not None and hasattr(card_label, "card"):
            if card_label.card.is_wild and is_face_up:
                card_label.setStyleSheet("border: 2px solid red;")
            else:
                card_label.setStyleSheet("")  # Clear the border style
        else:
            pass
            # print(f"Card: highlight_wild_card - Card label is None or does not have a 'card' attribute: {card_label}")

    def set_wild(self, is_wild):
        self.is_wild = is_wild
        # self.load_image()
        if self.is_wild:
            pass
            # print(f"Card: set_wild - Card {self.id} is wild and should be highlighted.")
        else:
            pass
            # print(f"Card {self.id} is not wild.")

    # END ============================

    def set_face_down(self):
        self.face_up = False
        self.pixmap = QPixmap("graphics/cards/default.png")

    def set_face_up(self):
        self.face_up = True
        self.load_image()

    def get_pixmap(self):
        return self.pixmap


class Deck:
    def __init__(self):
        self.cards = self.create_deck()
        self.value_dict = VALUE_DICT  # Use the common value dictionary
        self.wild_card_value = None

    def create_deck(self):
        return [Card(value, suit) for suit in CARD_SUITS for value in CARD_VALUES]

    def shuffle(self):
        logging.info("Deck shuffling the deck...")
        random.shuffle(self.cards)
        print("Deck: shuffled.")

    def deal(self, num_cards):
        if len(self.cards) < num_cards:
            raise ValueError("Not enough cards in the deck to deal.")
        dealt_cards = [self.cards.pop() for _ in range(num_cards)]
        return dealt_cards

    def remaining_cards(self):
        return len(self.cards)

    def update_wild_card1(self, table_chips):
        wild_card_value_number = table_chips
        matching_values = [
            key
            for key, value in self.value_dict.items()
            if value == wild_card_value_number
        ]
        if matching_values:
            wild_card_value = matching_values[0]
            self.wild_card_value = wild_card_value
            print(
                f"Deck: update_wild_card - Wild card updated to {self.wild_card_value}"
            )
        else:
            print(
                f"Deck: update_wild_card - No matching wild card value found for table_chips = {table_chips}"
            )

        # Update card states
        for card in self.cards:
            card.set_wild(card.value == self.wild_card_value)

    def update_wild_card(self, table_chips):
        # Import the new dictionary
        from viuda_card_config import REVERSE_VALUE_DICT

        # --- NEW, CORRECTED LOGIC ---
        # The wild card number cycles from 1 to 13.
        # The modulo operator (%) is perfect for this.
        # (table_chips - 1) % 13 ensures the result is always 0-12.
        # Adding +1 makes it 1-13.
        wild_card_number = ((table_chips - 1) % 13) + 1

        # Look up the card's string value (e.g., 'A', 'K', '8') using the number
        self.wild_card_value = REVERSE_VALUE_DICT.get(wild_card_number)
        # --- END OF NEW LOGIC ---

        if self.wild_card_value:
            print(
                f"Deck: update_wild_card - Wild card value is now '{self.wild_card_value}'"
            )
            # Update the is_wild status for all cards in the deck
            for card in self.cards:
                card.set_wild(card.value == self.wild_card_value)
        else:
            print(
                f"Deck: update_wild_card - Error: Could not find a wild card for number {wild_card_number}"
            )

    def draw_card(self):
        if not self.cards:
            raise ValueError("No cards left in the deck")
        return self.cards.pop()
