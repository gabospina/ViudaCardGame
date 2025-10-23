import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from tkinter import PhotoImage
import random
import pygame
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
        self.pil_image = None
        self.tk_image = None
        self.data = CardTuple(value=rank, suit=suit)
        self.id = f"{self.data.value}{self.data.suit}"

        self.load_image()

    def load_image(self):
        if self.pil_image:
            return

        img = os.path.join(f"graphics/cards/{self.id}.png")
        self.pil_image = Image.open(img)
        self.pil_image = self.pil_image.resize((CardGameGUI.CARD_WIDTH, CardGameGUI.CARD_HEIGHT), Image.BICUBIC)
        self.tk_image = ImageTk.PhotoImage(self.pil_image)

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


class DraggedCard:
    def __init__(self, card, idx, start_x, start_y):
        self.card = card
        self.idx = idx
        self.start_x = start_x
        self.start_y = start_y
        self.label = None
        self.tk_image = card.tk_image  # Add the tk_image attribute from the card object


class CardGameGUI:
    instances = []
    CARD_HEIGHT = 100  # 75  # Define the height of the cards
    CARD_WIDTH = 100  # 50
    SPACING = 450

    def __init__(self, root, player, other_player, reveal_deck=None):
        self.__class__.instances.append(self)
        self.root = root
        self.root.title(f"{player.name} - Viuda")
        self.player = player
        self.other_player = other_player
        self.hand = player.hand  # Add this line to store the player's hand
        self.drop_targets = []

        # self.root.geometry("650x350")  # Adjust the window size
        self.event_allowed = True

        # Add new attributes for drag and drop functionality
        self.reveal_dragged_card = None
        self.reveal_drop_targets = []
        self.dragged_card = None  # Add this line to initialize the dragged_card attribute

        self.create_player_hand_frame()
        self.reveal_deck = reveal_deck
        self.create_reveal_frame()

        # Add this instance to the list of instances
        CardGameGUI.instances.append(self)

    def create_reveal_frame(self):
        self.reveal_frame = tk.Frame(self.root, bg="blue", width=200, height=250, borderwidth=6, relief=tk.RIDGE)
        self.reveal_frame.pack(side=tk.TOP, fill=tk.Y, padx=10, pady=10)
        # self.reveal_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        self.reveal_card_labels = []

        label = tk.Label(self.reveal_frame, text=f"Viuda:")
        label.pack()

        # Show the "Reveal" button and "Pass" button on the FIRST WINDOW only
        # if CardGameGUI.instances.index(self) == 0:
        #     self.reveal_button = tk.Button(self.reveal_frame, text="Reveal", command=self.reveal_cards)
        #     self.reveal_button.pack(side=tk.TOP, padx=(0, 500), pady=10)
        #     self.pass_button = tk.Button(self.reveal_frame, text="Pass", command=self.pass_turn)
        #     self.pass_button.pack(side=tk.TOP, padx=(500, 0), pady=10)
        # else:
        #     self.reveal_button = None
        #     self.pass_button = None

        # Create buttons in ALL THE WINDOWS
        self.reveal_button = tk.Button(self.reveal_frame, text="Reveal", command=self.reveal_cards)
        self.reveal_button.pack(side=tk.TOP, padx=(0, 500), pady=10)
        self.pass_button = tk.Button(self.reveal_frame, text="Pass", command=self.pass_turn)
        self.pass_button.pack(side=tk.TOP, padx=(500, 0), pady=10)

        # ACTIVATE buttons first window & DEACTIVATE buttons others windows
        if CardGameGUI.instances.index(self) > 1:
            # self.create_buttons()
            self.update_buttons_visibility()

        for i, card in enumerate(self.reveal_deck):
            default_image_path = "../graphics/cards/default.png"
            default_image = Image.open(default_image_path)
            default_image = default_image.resize((CardGameGUI.CARD_WIDTH, CardGameGUI.CARD_HEIGHT), Image.BICUBIC)
            default_tk_image = ImageTk.PhotoImage(default_image)

            # lbl = ttk.Label(self.reveal_frame, image=default_tk_image)
            lbl = tk.Label(self.reveal_frame, image=default_tk_image)
            lbl.default_image = default_tk_image
            lbl.pack(side='left', padx=2)

            # Bind events to the labels representing the cards in the reveal_cards frame
            # lbl.bind("<Button-1>", lambda event, idx=i: self.reveal_drag_start(event, idx))
            # lbl.bind("<B1-Motion>", lambda event, label=lbl: self.reveal_drag_motion(event, label))
            # lbl.bind("<ButtonRelease-1>", lambda event, label=lbl: self.reveal_drag_end(event, label))

            # Bind events for drag and drop
            lbl.bind("<ButtonPress-1>", self.start_drag)
            lbl.bind("<B1-Motion>", self.drag)
            lbl.bind("<ButtonRelease-1>", self.drop)

            self.reveal_card_labels.append(lbl)
            self.update_hand_display()  # Update hand display after dropping the card
            # self.update_reveal_display()  # Update reveal cards display

    # def create_buttons(self):
    #     # Create the reveal and pass buttons
    #     self.reveal_button = tk.Button(self.reveal_frame, text="Reveal", command=self.reveal_cards)
    #     self.pass_button = tk.Button(self.reveal_frame, text="Pass", command=self.pass_turn)
    #     # self.reveal_button = tk.Button(self.root, text="Reveal", command=self.reveal_cards)
    #     # self.pass_button = tk.Button(self.root, text="Pass", command=self.pass_turn)
    #
    #     # Pack the buttons DUPLICATE DEACTIVATED BUTTONS FIRST WINDOW !!!!!!!
    #     self.reveal_button.pack(side=tk.TOP, padx=(0, 500), pady=10)
    #     self.pass_button.pack(side=tk.TOP, padx=(500, 0), pady=10)

    def disable_buttons(self):
        if self.reveal_button:
            self.reveal_button.config(state=tk.DISABLED)
        if self.pass_button:
            self.pass_button.config(state=tk.DISABLED)

    def pass_turn(self):
        # Destroy buttons in the current window
        self.reveal_button.destroy()
        self.pass_button.destroy()

    # Method activate reveal and pass buttons in the first window:
    def update_buttons_visibility(self):
        # first instance == 1 ACTIVATE ALL || == 0 DEACTIVATE FIRST WINDOW - ALL OTHERS ACTIVATED
        if len(self.__class__.instances) == 0:
            # Enable buttons in the first window
            self.reveal_button.config(state=tk.NORMAL)
            self.pass_button.config(state=tk.NORMAL)
        else:
            # Deactivate all buttons in other windows
            if self.reveal_button:
                self.reveal_button.config(state=tk.DISABLED)
            if self.pass_button:
                self.pass_button.config(state=tk.DISABLED)

    def reveal_cards(self):
        # Update face_up status and load images for the reveal cards
        for card in self.reveal_deck:
            card.face_up = True  # Flip the card face_up
            card.load_image()

        self.revealed = True  # Set revealed status to True

        # Update the reveal_card_labels in all windows
        for instance in self.__class__.instances:
            for card_label, card in zip(instance.reveal_card_labels, instance.reveal_deck):
                card_label.config(image=card.tk_image)

        # Destroy buttons in all windows
        for instance in self.__class__.instances:
            instance.reveal_button.destroy()
            instance.pass_button.destroy()

    def hide_buttons(self):
        if self.reveal_button:
            self.reveal_button.pack_forget()
        if self.pass_button:
            self.pass_button.pack_forget()

    """ DO NO DELETE - reveal_drag_start """
    # def reveal_drag_start(self, event, idx):
    #     print("reveal_drag_start called")
    #     if not self.event_allowed:
    #         return
    #     if self.reveal_dragged_card:
    #         return  # Only allow one dragged card at a time
    #     card = self.reveal_deck[idx]
    #     if self.reveal_dragged_card:
    #         return  # Only allow one dragged card at a time
    #     # prevent click events on face-down cards
    #     if not card.face_up:  # Don't allow dragging of face-down cards
    #         return
    #     # print(f"reveal_drag_end: self.reveal_dragged_card = {self.reveal_dragged_card}")
    #     # print(f"reveal_drag_end: self.reveal_deck = {self.reveal_deck}")
    #
    #     card.face_up = True
    #     card.load_image()
    #     card.tk_image = ImageTk.PhotoImage(card.pil_image)
    #     # Create a DraggedCard instance
    #     self.reveal_dragged_card = DraggedCard(card, idx, event.x, event.y)
    #     # Create and place label for the dragged card
    #     self.reveal_dragged_card_label = tk.Label(self.root, image=card.tk_image)
    #     self.reveal_dragged_card_label.image = card.tk_image
    #     self.reveal_dragged_card_label.place(x=event.x_root, y=event.y_root)
    #
    # def reveal_drag_motion(self, event, label):
    #     print("reveal_drag_motion called")
    #     if self.reveal_dragged_card and self.reveal_dragged_card.label:
    #         # Calculate the new position based on mouse movement
    #         _, new_y = label.winfo_pointerxy()
    #         # Update the label position
    #         self.reveal_dragged_card.label.place(x=self.reveal_dragged_card.start_x, y=new_y)
    #
    #         # Check if the dragged card's x-coordinate touches the x-axis of the player's hand frame
    #         hand_frame_bbox = self.hand_frame.bbox()
    #         if hand_frame_bbox is not None:
    #             if self.reveal_dragged_card.start_x >= hand_frame_bbox[0] and \
    #                     self.reveal_dragged_card.start_x <= hand_frame_bbox[2]:
    #                 print("Card is being dragged within the player's hand frame.")
    #
    # def reveal_drag_end(self, event, label):
    #     print("reveal_drag_end called")
    #     if not self.reveal_dragged_card:
    #         return
    #
    #     self.event_allowed = False
    #     self.root.after(500, self.allow_events)
    #
    #     # Check if the mouse pointer is within the player's hand frame
    #     x, y = label.winfo_pointerxy()
    #     hand_frame_bbox = self.hand_frame.bbox()
    #     if hand_frame_bbox is not None and hand_frame_bbox[1] <= y <= hand_frame_bbox[3]:
    #         # If the mouse pointer is within the player's hand frame, add the card to the player's hand
    #         self.player.hand.append(self.reveal_dragged_card)
    #         self.update_hand_display()
    #
    #     # Reset the dragged card
    #     self.reveal_dragged_card = None
    """ DO NO DELETE - reveal_drag_end """

    def start_drag(self, event):
        self.dragging = event.widget

    def enter_hand(self, event):
        self.hand_frame.config(bg="lightblue")

    def leave_hand(self, event):
        self.hand_frame.config(bg="lightyellow")

    def drag(self, event):
        if self.dragging:
            y = event.y
            if 0 <= y <= self.hand_frame.winfo_height():
                self.dragging.place(x=0, y=y)

    def drop(self, event):
        if self.dragging:
            # Check if the drop occurred within the hand frame
            if event.widget == self.hand_frame:
                print("Card dropped into Player's Hand")
            else:
                print("Card dropped outside Player's Hand")
            self.dragging = None


    def player_drag_start(self, event, idx):
        print("player_drag_start called")
        if not self.event_allowed:
            return
        card = self.player.hand[idx]
        card.face_up = True
        card.load_image()
        card.tk_image = ImageTk.PhotoImage(card.pil_image)

        self.dragged_card = DraggedCard(card, idx, event.x, event.y)
        self.dragged_card.tk_image = card.tk_image

        self.dragged_card_label = tk.Label(self.root, image=card.tk_image)
        self.dragged_card_label.image = card.tk_image
        self.dragged_card_label.place(x=event.x_root, y=event.y_root)

        self.dragged_card_label.bind("<B1-Motion>",
                                     lambda event, label=self.dragged_card_label: self.player_drag_motion(event, label))
        self.dragged_card_label.bind("<ButtonRelease-1>",
                                     lambda event, label=self.dragged_card_label: self.player_drag_end(event, label))
        self.dragged_card_label.bind("<Button-1>", lambda event: self.player_to_reveal_drag_end(event, idx))

    def player_drag_motion(self, event, label):
        print("player_drag_motion called")
        if self.dragged_card:
            new_x = event.x_root - self.dragged_card.start_x
            new_y = event.y_root - self.dragged_card.start_y
            label.place(x=new_x, y=new_y)

            left_bound = self.hand_frame.winfo_rootx()
            right_bound = left_bound + self.hand_frame.winfo_width() - CardGameGUI.CARD_WIDTH

            # Check if the mouse movement is mostly horizontal or vertical
            if abs(event.x_root - self.dragged_card.start_x) > abs(event.y_root - self.dragged_card.start_y):
                # If mostly horizontal, call on_drag_motion
                if left_bound is not None and right_bound is not None:
                    self.on_drag_motion(event, self.dragged_card.idx, left_bound, right_bound)
            else:
                # If mostly vertical, continue with player_drag_motion
                pass

    def player_drag_end(self, event, label):
        if self.dragged_card:
            self.event_allowed = False
            self.root.after(500, self.allow_events)

            x, y = label.winfo_pointerxy()
            reveal_frame_bbox = self.reveal_frame.bbox()
            if reveal_frame_bbox is not None and x >= reveal_frame_bbox[0] and x <= reveal_frame_bbox[2] and y >= reveal_frame_bbox[1] and y <= reveal_frame_bbox[3]:
                self.player_to_reveal_drag_end(event, label)
            else:
                label.place(x=self.dragged_card.start_x, y=self.dragged_card.start_y)  # Reset position
                self.dragged_card = None

        else:
            label.destroy()
            self.dragged_card = None

    def on_player_drag_motion(self, event, label):
        if self.dragged_card and self.dragged_card.label:
            new_x = event.x_root - self.dragged_card.start_x
            new_y = event.y_root - self.dragged_card.start_y
            self.dragged_card.label.place(x=new_x, y=new_y)

            # Check if the dragged card is within the reveal frame
            reveal_frame_bbox = self.reveal_frame.bbox()
            if reveal_frame_bbox is not None:
                x, y = event.x_root, event.y_root
                if (x >= reveal_frame_bbox[0] and x <= reveal_frame_bbox[2] and
                        y >= reveal_frame_bbox[1] and y <= reveal_frame_bbox[3]):
                    # If the card is within the reveal frame, change its appearance or behavior
                    pass  # Add your desired functionality here

    def player_to_reveal_drag_end(self, event, label):
        print("player_to_reveal_drag_end called")
        if self.dragged_card:
            self.event_allowed = False
            self.root.after(500, self.allow_events)

            self.player.hand.remove(self.dragged_card)
            self.reveal_deck.append(self.dragged_card)
            self.dragged_card.face_up = True
            self.update_hand_display()
            self.update_reveal_display()
            self.dragged_card = None

    def allow_events(self):
        self.event_allowed = True

    def update_reveal_display(self):
        # Display each card in the reveal deck
        self.reveal_labels = []  # Keep a reference to the labels
        for i, card in enumerate(self.reveal_deck):
            if not card.face_up:
                continue  # Skip face-down cards

            # Load and resize the card image
            try:
                card.load_image()
            except FileNotFoundError as e:
                print(f"Error loading card image: {card.img} ({e})")
                continue  # Skip this card if the image cannot be loaded

            # Convert the PIL Image to a tkinter PhotoImage
            tk_image = ImageTk.PhotoImage(card.pil_image)

            # Create a tkinter Label with the PhotoImage
            lbl = tk.Label(self.reveal_frame, image=tk_image)
            lbl.photo = tk_image  # Keep a reference to avoid garbage collection
            lbl.pack(side='left', padx=2)

            # Bind events to the labels representing the cards in the reveal_cards frame
            lbl.bind("<Button-1>", lambda event, idx=i: self.reveal_drag_start(event, idx))
            lbl.bind("<B1-Motion>", lambda event, label=lbl: self.reveal_drag_motion(event, label))
            lbl.bind("<ButtonRelease-1>", lambda event, label=lbl: self.reveal_drag_end(event, label))

            self.reveal_labels.append(lbl)  # Add the label to the list

    def update_hand_display(self):
        for widget in self.hand_frame.winfo_children()[1:]:
            widget.destroy()

        left_bound = self.hand_frame.winfo_rootx()
        right_bound = left_bound + self.hand_frame.winfo_width() - CardGameGUI.CARD_WIDTH  # Replace with appropriate calculation

        for i, card in enumerate(self.player.hand):
            if not card.face_up:
                continue  # Skip face-down cards

            tk_image = card.tk_image  # Use the tk_image attribute

            # Create a tkinter Label with the PhotoImage
            lbl = tk.Label(self.hand_frame, image=tk_image)
            lbl.image = tk_image  # Keep a reference to avoid garbage collection
            lbl.pack(side='left', padx=2)

            # # Bind events to the label
            lbl.bind("<Button-1>", lambda event, idx=i: self.on_drag_start(event))
            lbl.bind("<B1-Motion>", lambda event, label=lbl: self.on_drag_motion(event, left_bound, right_bound))
            lbl.bind("<ButtonRelease-1>", lambda event, idx=i: self.on_drag_end(event, idx))

            # Bind events to the label for dragging from player's hand to reveal
            # lbl.bind("<Button-1>", lambda event, idx=i: self.player_drag_start(event, idx))
            # lbl.bind("<B1-Motion>", lambda event, idx=i: self.on_drag_motion(event, idx, left_bound, right_bound))
            # lbl.bind("<ButtonRelease-1>", lambda event, label=lbl: self.player_drag_end(event, label))

        self.initialize_drop_targets()

    def reveal_all_cards(self):
        for instance in self.instances:
            for card_label, card in zip(instance.reveal_card_labels, instance.reveal_deck):
                card.face_up = True
                card.load_image()
                card_label.config(image=card.tk_image)

        for instance in self.instances:
            instance.reveal_button.destroy()

    def create_player_hand_frame(self):
        CARD_WIDTH = 100
        hand_frame_width = CARD_WIDTH * 6
        # Create the hand_frame for each player
        self.hand_frame = tk.Frame(self.root, bg="green", width=hand_frame_width * 6, height=CardGameGUI.CARD_HEIGHT, borderwidth=6, relief=tk.RIDGE)
        # self.hand_frame = tk.Frame(self.root, bg="green", width=200, height=450, borderwidth=2, relief=tk.RIDGE)
        self.hand_frame.pack(side=tk.BOTTOM, fill=tk.Y, padx=10, pady=10)
        # self.hand_frame.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT)


        # Label for player's name
        label = tk.Label(self.hand_frame, text=f"{self.player.name}'s Hand:")
        label.pack()

        # Adjust the width of the hand_frame to accommodate six cards
        # self.hand_frame.config(width=6 * CardGameGUI.CARD_WIDTH + 5 * CardGameGUI.SPACING)
        # self.hand_frame.config(width=6 * CardGameGUI.CARD_WIDTH + 6 * CardGameGUI.SPACING)

        print("Hand Frame Dimensions:")
        print("Width:", self.hand_frame.winfo_width())
        print("Height:", self.hand_frame.winfo_height())

        print("Card Dimensions:")
        print("Width:", CardGameGUI.CARD_WIDTH)
        print("Height:", CardGameGUI.CARD_HEIGHT)

        # Bind events for drag and drop
        self.hand_frame.bind("<Enter>", self.enter_hand)
        self.hand_frame.bind("<Leave>", self.leave_hand)
        self.hand_frame.bind("<ButtonRelease-1>", self.drop)

        # Create and display player's hand
        self.update_hand_display()

    def on_reveal_card_click(self, event, card, btn):
        if not card.face_up:
            # If the card is face-down, reveal it and update the button text
            card.face_up = True
            btn.config(image=card.tk_image)

    """ START PLAYERS HANDS CARDS DRAG & DROP """

    def reveal_initialize_drop_targets(self):
        self.reveal_drop_targets = [tk.Label(self.reveal_frame, text="", width=2) for _ in
                                    range(len(self.player.hand) + 2)]  # Add one for reveal deck

    def reveal_find_closest_target_idx(self, x_root):
        closest_target_idx = None
        min_distance = float('inf')

        for i in range(len(self.player.hand) + 1):
            target_x_root = self.hand_frame.winfo_rootx() + CardGameGUI.CARD_WIDTH // 2 + i * self.SPACING
            distance = abs(x_root - target_x_root)

            if distance < min_distance:
                min_distance = distance
                closest_target_idx = i

        return closest_target_idx

    def initialize_drop_targets(self):
        self.drop_targets = [tk.Label(self.hand_frame, text="", width=2) for _ in
                             range(len(self.player.hand) + 2)]  # Add one for reveal deck

    def on_drag_start(self, event):
        print("on_drag_start called")
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

            # self.dragged_card = DraggedCard(card, event, (left_bound, right_bound), (top_bound, bottom_bound))

            self.dragged_card = DraggedCard(card, idx, event.x_root, event.y_root)

            # Create a label for the dragged card
            # self.dragged_card.label = ttk.Label(self.root, image=card.tk_image)
            self.dragged_card.label = tk.Label(self.root, image=card.tk_image)
            self.dragged_card.label.image = card.tk_image
            self.dragged_card.label.place(x=event.x_root, y=event.y_root)

            self.dragged_card_label.bind("<B1-Motion>",
                                         lambda event, label=self.dragged_card_label: self.player_drag_motion(event,
                                                                                                              label))
            self.dragged_card_label.bind("<ButtonRelease-1>",
                                         lambda event, label=self.dragged_card_label: self.player_drag_end(event,
                                                                                                           label))
            # self.dragged_card_label.bind("<Button-1>", lambda event: self.player_to_reveal_drag_end(event, idx))

    def on_drag_motion(self, event, left_bound, right_bound):
        print("on_drag_motion called")
        if hasattr(self, 'dragged_card') and self.dragged_card is not None:
            # Use relative mouse position within hand_frame for consistency
            x_root = event.widget.winfo_pointerx() - self.hand_frame.winfo_rootx()
            y_root = event.widget.winfo_pointery() - self.hand_frame.winfo_rooty()

            new_x = event.x_root - self.dragged_card.start_x
            new_y = event.y_root - self.dragged_card.start_y

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
            # new_x = max(left_bound, min(x_root, right_bound))  # Clamp to both edges
            # new_y = max(hand_frame_y, min(y_root - CardGameGUI.CARD_HEIGHT // 2, max_y))
            if left_bound <= event.x_root <= right_bound:
                self.dragged_card_label.place(x=new_x, y=new_y)

            print(f"New position: ({new_x}, {new_y})")  # For debugging purposes (optional)

            self.dragged_card.label.place(x=new_x, y=new_y)

    def on_drag_end(self, event, idx):
        print("on_drag_end called")
        if hasattr(self, 'dragged_card') and self.dragged_card is not None:
            self.dragged_card.label.destroy()

        closest_target_idx = self.find_closest_target_idx(event.x_root)

        if closest_target_idx is not None:
            if closest_target_idx == len(self.player.hand):
                # Move card to other player's hand
                self.player.move_card(idx, closest_target_idx, self.other_player)
            else:
                self.player.move_card(idx, closest_target_idx, self.player)

        self.reset_drop_target_colors(closest_target_idx)
        self.update_hand_display()

        if self.dragged_card:
            # Check if there are six cards in the player's hand
            if len(self.player.hand) == 6:
                # Remove the card being dragged from the player's hand
                self.player.hand.remove(self.dragged_card)
                # Add the card back to the reveal cards frame
                self.reveal_deck.append(self.dragged_card)
                self.update_reveal_display()  # Update the reveal cards display
            else:
                # Add the card to the player's hand
                self.player.hand.append(self.dragged_card)
                self.dragged_card.face_up = True
                # Update the hand display to show the dropped card
                self.update_hand_display()
                # Remove the card from the reveal deck
                self.reveal_deck.remove(self.dragged_card)
                self.update_reveal_display()  # Update the reveal cards display

            self.dragged_card = None  # Indicate that the drag and drop operation has ended

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
