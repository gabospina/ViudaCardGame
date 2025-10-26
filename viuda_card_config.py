# card_config.py
CARD_VALUES = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
CARD_SUITS = ["C", "D", "H", "S"]  # Clubs, Diamonds, Hearts, Spades
# CARD_SUITS = ["hearts", "diamonds", "clubs", "spades"]
VALUE_DICT = {
    "A": 14,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "T": 10,
    "J": 11,
    "Q": 12,
    "K": 13,
}

# --- ADD THIS NEW DICTIONARY ---
# This lets us find a card's string value (like 'A') from its number.
REVERSE_VALUE_DICT = {v: k for k, v in VALUE_DICT.items()}
REVERSE_VALUE_DICT[1] = "A"  # Special case: 1 should also map to Ace for wild card
# --- END OF ADDITION ---
