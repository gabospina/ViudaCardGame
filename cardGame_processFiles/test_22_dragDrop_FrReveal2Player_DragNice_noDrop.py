import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from tkinter import PhotoImage
import random
import pygame
from collections import namedtuple
# from viuda_DoNotDelete_card_game import DraggedCard

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
        # Print the image path for debugging
        print(f"Loading image: {self.img}")

        self.load_image()

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


class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.chips = 3  # Assuming players start with 3 chips (adjust as needed)
        self.called = False  # Player call flag for game loop
        self.score = 0

    def take_cards(self, cards):
        for card in cards:
            card.face_up = True
        self.hand.extend(cards)

    def move_card(self, from_idx, to_idx, other_player):
        card = self.hand.pop(from_idx)
        other_player.hand.insert(to_idx, card)

    def return_card(self):
        # Return one card from the bottom side to the top side
        if len(self.hand) > 1:
            card = self.hand.pop(-1)
            self.hand.insert(0, card)


# class DraggedCard(tk.Toplevel):
#     REFRESH_RATE = 10
#
#     def __init__(self, card, event, allowed_x, allowed_y):
#         super().__init__()
#         self.overrideredirect(True)
#         self.card = card
#         self.label = tk.Label(self, text=str(card))
#         self.label.pack()
#         self.geometry(f"+{event.x_root - 20}+{event.y_root - 20}")
#         self.allowed_x = allowed_x
#         self.allowed_y = allowed_y
#         self.update()


class DraggedCard:
    def __init__(self, card, idx, start_x, start_y):
        self.card = card
        self.idx = idx
        self.start_x = start_x
        self.start_y = start_y
        self.label = None

class CardGameGUI:
    instances = []
    CARD_HEIGHT = 75  # 100  # Define the height of the cards
    CARD_WIDTH = 75  # 100
    SPACING = 50

    def __init__(self, root, player, other_player, reveal_deck=None):
        self.__class__.instances.append(self)
        self.root = root
        self.player = player
        self.root.title(f"{player.name} - Viuda")
        self.other_player = other_player
        self.drop_targets = []

        # Add new attributes for drag and drop functionality
        self.reveal_dragged_card = None
        self.reveal_drop_targets = []

        self.create_player_hand_frame()
        self.reveal_deck = reveal_deck
        self.create_reveal_frame()

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

        def revel_drag_start(event, idx):
            card = self.reveal_deck[idx]

            self.reveal_dragged_card = DraggedCard(card, idx, event.x_root, event.y_root)
            self.reveal_dragged_card.label = ttk.Label(self.root, image=card.tk_image)

            self.reveal_dragged_card.label.place(x=event.x_root, y=event.y_root)

            # self.reveal_dragged_card.label.config(overrideredirect=True)
            self.reveal_dragged_card.label.config(borderwidth=0)

        def revel_drag_motion(event):
            if self.reveal_dragged_card:
                new_x = event.x_root - self.reveal_dragged_card.start_x
                new_y = event.y_root - self.reveal_dragged_card.start_y
                self.reveal_dragged_card.label.place(x=new_x, y=new_y)

        def revel_drag_end(event):
            if self.reveal_dragged_card:
                self.reveal_dragged_card.label.destroy()
                self.update_reveal_display()
                self.reveal_dragged_card = None

        self.reveal_frame = ttk.Frame(self.root)
        self.reveal_frame.pack(pady=10)
        self.reveal_card_labels = []

        # Create a button to reveal the cards
        if self.__class__.instances.index(self) == 0:
            self.reveal_button = ttk.Button(self.reveal_frame, text="Reveal", command=reveal_cards)
            self.reveal_button.pack()
        else:
            self.reveal_button = None

        for i, card in enumerate(self.reveal_deck):
            default_image_path = "../graphics/cards/default.png"
            default_image = Image.open(default_image_path)
            default_image = default_image.resize((CardGameGUI.CARD_WIDTH, CardGameGUI.CARD_HEIGHT), Image.BICUBIC)
            default_tk_image = ImageTk.PhotoImage(default_image)

            lbl = ttk.Label(self.reveal_frame, image=default_tk_image)
            lbl.default_image = default_tk_image
            lbl.pack(side='left', padx=2)

            # Bind events to the labels representing the cards in the reveal_cards frame
            lbl.bind("<Button-1>", lambda event, idx=i: revel_drag_start(event, idx))
            lbl.bind("<B1-Motion>", revel_drag_motion)
            lbl.bind("<ButtonRelease-1>", revel_drag_end)

            self.reveal_card_labels.append(lbl)

    def update_reveal_display(self):
        # Display each card in the reveal deck
        for i, card in enumerate(self.reveal_deck):
            if not card.face_up:
                continue  # Skip face-down cards

            # Load and resize the card image
            try:
                card.load_image()
            except FileNotFoundError as e:
                print(f"Error loading card image: {card.img} ({e})")
                continue  # Skip this card if the image cannot be loaded

            # Convert the pygame surface image to a PIL Image
            pil_image = Image.frombytes("RGBA", card.card_img.get_size(), pygame.image.tostring(card.card_img, "RGBA"))

            # Convert the PIL Image to a tkinter PhotoImage
            tk_image = ImageTk.PhotoImage(pil_image)

            # Create a tkinter Label with the PhotoImage
            lbl = tk.Label(self.reveal_frame, image=tk_image)
            lbl.photo = tk_image  # Keep a reference to avoid garbage collection
            lbl.pack(side='left', padx=2)

    def reveal_all_cards(self):
        for instance in self.instances:
            for card_label, card in zip(instance.reveal_card_labels, instance.reveal_deck):
                card.face_up = True
                card.load_image()
                card_label.config(image=card.tk_image)

        for instance in self.instances:
            instance.reveal_button.destroy()

    def create_player_hand_frame(self):
        # Create the hand_frame for each player
        self.hand_frame = ttk.Frame(self.root)
        self.hand_frame.pack(pady=10, side="bottom")  # Pack hand frame below reveal frame)

        # Label for player's name
        label = ttk.Label(self.hand_frame, text=f"{self.player.name}'s Hand:")
        label.pack()

        # Adjust the width of the hand_frame to accommodate six cards
        self.hand_frame.config(width=6 * CardGameGUI.CARD_WIDTH + 5 * CardGameGUI.SPACING)

        # Create and display player's hand
        self.update_hand_display()

    def update_hand_display(self):
        for widget in self.hand_frame.winfo_children()[1:]:
            widget.destroy()

        left_bound = self.hand_frame.winfo_rootx()
        right_bound = left_bound + self.hand_frame.winfo_width() - CardGameGUI.CARD_WIDTH  # Replace with appropriate calculation

        for i, card in enumerate(self.player.hand):
            tk_image = card.tk_image  # Use the tk_image attribute

            # Create a tkinter Label with the PhotoImage
            lbl = tk.Label(self.hand_frame, image=tk_image)
            lbl.photo = tk_image  # Keep a reference to avoid garbage collection
            lbl.pack(side='left', padx=2)

            # Bind events to the label
            lbl.bind("<Button-1>", lambda event, idx=i: self.on_drag_start(event))
            lbl.bind("<B1-Motion>", lambda event, idx=i: self.on_drag_motion(event, idx, left_bound, right_bound))
            lbl.bind("<ButtonRelease-1>", lambda event, idx=i: self.on_drag_end(event, idx))

        self.initialize_drop_targets()

    """ START PLAYERS HANDS CARDS DRAG & DROP """

    def initialize_drop_targets(self):
        self.drop_targets = [tk.Label(self.hand_frame, text="", width=2) for _ in
                             range(len(self.player.hand) + 2)]  # Add one for reveal deck

    def on_drag_start(self, event):
        widget_name = event.widget.winfo_name()
        if widget_name.startswith('card_'):
            idx = int(widget_name.split('_')[-1])
            card = self.player.hand[idx]
            # Calculate the boundaries within the hand_frame
            left_bound = self.hand_frame.winfo_rootx()  # Get the actual root x-coordinate
            right_bound = left_bound + self.hand_frame.winfo_width() - CardGameGUI.CARD_WIDTH
            top_bound = self.hand_frame.winfo_rooty()
            bottom_bound = top_bound + self.hand_frame.winfo_height() - CardGameGUI.CARD_HEIGHT
            # Pass the allowed position boundaries to DraggedCard
            print(f"Left bound: {left_bound}, Right bound: {right_bound}")
            print(f"Top bound: {top_bound}, Bottom bound: {bottom_bound}")
            self.dragged_card = DraggedCard(card, event, (left_bound, right_bound), (top_bound, bottom_bound))

    def on_drag_motion(self, event, idx, left_bound, right_bound):
        # Use relative mouse position within hand_frame for consistency
        x_root = event.widget.winfo_pointerx() - self.hand_frame.winfo_rootx()
        y_root = event.widget.winfo_pointery() - self.hand_frame.winfo_rooty()

        closest_target_idx = self.find_closest_target_idx(x_root)

        for i, target in enumerate(self.drop_targets):
            target.config(bg='red' if i == closest_target_idx else 'SystemButtonFace')

        # Get the current position and dimensions of the hand_frame
        hand_frame_x = self.hand_frame.winfo_x()
        hand_frame_y = self.hand_frame.winfo_y()
        hand_frame_width = self.hand_frame.winfo_width()
        hand_frame_height = self.hand_frame.winfo_height()

        # Calculate the maximum allowed x and y coordinates for the dragged card
        max_x = hand_frame_x + hand_frame_width - CardGameGUI.CARD_WIDTH
        max_y = hand_frame_y + hand_frame_height - CardGameGUI.CARD_HEIGHT

        # Clamp the new position within both left and right boundaries
        new_x = max(left_bound, min(x_root, right_bound))  # Clamp to both edges
        new_y = max(hand_frame_y, min(y_root - CardGameGUI.CARD_HEIGHT // 2, max_y))
        print(f"New position: ({new_x}, {new_y})")  # For debugging purposes (optional)

        # Update the position of the dragged card
        event.widget.place(x=new_x, y=new_y)

    def on_drag_end(self, event, idx):
        if hasattr(self, 'dragged_card'):
            self.dragged_card.destroy()

        closest_target_idx = self.find_closest_target_idx(event.x_root)

        if closest_target_idx is not None:
            if closest_target_idx == len(self.player.hand):
                # Move card to other player's hand
                self.player.move_card(idx, closest_target_idx, self.other_player)
            else:
                self.player.move_card(idx, closest_target_idx, self.player)

        self.reset_drop_target_colors(closest_target_idx)
        self.update_hand_display()

    def find_closest_target_idx(self, x_root):
        closest_target_idx = None
        min_distance = float('inf')

        for i in range(len(self.player.hand) + 1):
            target_x_root = self.hand_frame.winfo_rootx() + self.CARD_WIDTH // 2 + i * self.SPACING
            distance = abs(x_root - target_x_root)

            if distance < min_distance:
                min_distance = distance
                closest_target_idx = i

        return closest_target_idx

    def reset_drop_target_colors(self, closest_target_idx):
        for i, target in enumerate(self.drop_targets):
            target.config(bg='SystemButtonFace' if i != closest_target_idx else 'SystemButtonFace')

    """ END PLAYERS HANDS CARDS DRAG & DROP """


def main():
    root = tk.Tk()
    root.withdraw()

    num_players =4
    players = [Player(f"Player {i+1}") for i in range(num_players)]

    deck = Deck()
    reveal_deck = deck.deal_hand(5)

    other_player = Player("Other Player")
    other_player.take_cards(deck.deal_hand(5))

    for player in players:
        player.take_cards(deck.deal_hand(5))

        player_window = tk.Toplevel(root)
        player_window.title(f"{player.name}")
        CardGameGUI(player_window, player, other_player, reveal_deck)

    reveal_button = ttk.Button(root, text="Reveal All")
    reveal_button.config(command=CardGameGUI.reveal_all_cards)
    reveal_button.pack()

    root.protocol("WM_DELETE_WINDOW", root.quit)
    root.mainloop()


if __name__ == "__main__":
    main()
