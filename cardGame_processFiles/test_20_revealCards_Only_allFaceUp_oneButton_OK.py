import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import random
from collections import namedtuple

CardTuple = namedtuple('Card', ['value', 'suit'])

cardvalues = [2, 3, 4, 5, 6, 7, 8, 9,
              "T",  # 10
              "J",  # Jack
              "Q",  # Queen
              "K",  # King
              "A"  # Ace
              ]

cardsuits = ['C', 'D', 'H', 'S']  # Clubs = 0, Diamonds = 1, Hearts = 2, Spades = 3


class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        self.face_up = False
        self.data = CardTuple(value=rank, suit=suit)
        self.id = f"{self.data.value}{self.data.suit}"
        self.img = f"graphics/cards/{self.id}.png"
        self.tk_image = None  # Placeholder for the image

    def load_image(self):
        try:
            self.pil_image = Image.open(self.img)
            # Define the desired width and height for the resized image
            target_width = 50  # Adjust as needed
            target_height = 100  # Adjust as needed
            # Resize the image
            self.pil_image = self.pil_image.resize((target_width, target_height), Image.BICUBIC)

            # Convert the PIL Image to a tkinter PhotoImage
            self.tk_image = ImageTk.PhotoImage(self.pil_image)
        except FileNotFoundError as e:
            print(f"Error loading card image: {self.img} ({e})")
            # Handle missing image case if needed

    def __str__(self):
        if self.face_up:
            return f"{self.rank} of {self.suit}"
        else:
            return "Face Down"


class Deck:
    def __init__(self):
        suits = cardsuits
        ranks = cardvalues
        self.cards = [Card(suit, rank) for suit in suits for rank in ranks]
        random.shuffle(self.cards)

    def deal_hand(self, num_cards):
        hand = self.cards[:num_cards]
        self.cards = self.cards[num_cards:]
        return hand


class CardGameGUI:
    instances = []
    CARD_HEIGHT = 75  # Define the height of the cards
    CARD_WIDTH = 75
    SPACING = 50

    def __init__(self, root, reveal_deck=None):
        self.__class__.instances.append(self)
        self.root = root
        self.root.title("Reveal Cards root")

        self.drop_targets = []
        self.reveal_deck = reveal_deck  # Assign reveal_deck passed from main()

        self.create_reveal_frame()

    @staticmethod
    def create_reveal_cards():
        deck = Deck()
        return deck.deal_hand(5)  # Return unique cards for each instance

    def create_reveal_frame(self):
        def reveal_cards():
            # Update face_up status and load images for the reveal cards
            for card in self.reveal_deck:
                card.face_up = True  # Flip the card face_up
                card.load_image()

            self.revealed = True  # Set revealed status to True

            # Reveal cards in all windows
            for instance in self.__class__.instances[1:]:
                for card in instance.reveal_deck:
                    card.face_up = True  # Flip the card face_up
                    card.load_image()

                instance.revealed = True  # Set revealed status to True

            self.reveal_button.destroy()  # Destroy the reveal button

            # Update the reveal_card_labels in all windows
            for instance in self.__class__.instances:
                for card_label, card in zip(instance.reveal_card_labels, instance.reveal_deck):
                    card_label.config(image=card.tk_image)

        self.reveal_frame = ttk.Frame(self.root)
        self.reveal_frame.pack(pady=10)

        # Create labels for the reveal cards
        self.reveal_card_labels = []
        for card in self.reveal_deck:
            # Load the default image for face-down cards
            default_image_path = "../graphics/cards/default.png"
            default_image = Image.open(default_image_path)
            default_image = default_image.resize((CardGameGUI.CARD_WIDTH, CardGameGUI.CARD_HEIGHT), Image.BICUBIC)
            default_tk_image = ImageTk.PhotoImage(default_image)

            # Create a label with the default image
            lbl = ttk.Label(self.reveal_frame, image=default_tk_image)
            lbl.default_image = default_tk_image  # Keep a reference to avoid garbage collection
            lbl.pack(side='left', padx=2)

            self.reveal_card_labels.append(lbl)

        # Create a button to reveal the cards
        if self.__class__.instances.index(self) == 0:
            self.reveal_button = ttk.Button(self.reveal_frame, text="Reveal", command=reveal_cards)
            self.reveal_button.pack()

        # Disable the reveal button for all windows except the first one
        else:
            self.reveal_button = None


# ONE BUTTON SHOWS CARDS IN FIRST WINDOWS ONLY
def main():
    root = tk.Tk()
    root.withdraw()

    # Define the number of windows to create
    num_windows = 3

    # Create a full deck and deal initial reveal cards for each window
    deck = Deck()
    reveal_decks = deck.deal_hand(5) * num_windows

    for i in range(num_windows):
        # Create a new reveal cards window
        reveal_cards_window = tk.Toplevel(root)
        reveal_cards_window.title("Reveal Cards")

        # Create an instance of CardGameGUI for the reveal cards
        reveal_deck = reveal_decks[i * 5: (i + 1) * 5]
        CardGameGUI(reveal_cards_window, reveal_deck)

    root.mainloop()


if __name__ == "__main__":
    main()
