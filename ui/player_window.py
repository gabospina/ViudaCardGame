import traceback
from PyQt5.QtWidgets import (
    QMainWindow,
    QDockWidget,
    QPushButton,
    QHBoxLayout,
    QWidget,
    QSizePolicy,
    QLabel,
)
from PyQt5.QtCore import Qt, QTimer

# Imports from our new modules
from core.card import Card
from ui.card_widget import CardWidget
from ui.drag_widget import DragWidget


# Define your actual Player class here
class Player:
    def __init__(
        self,
        player_id,
        player_number,
        player_dragwidget,
        reveal_dragwidget,
        parent_window,
        main_window,
        game_window,
        player_position,
        num_players,
        player_name,
    ):
        self.player_id = player_id
        self.player_number = player_number
        self.player_dragwidget = player_dragwidget
        self.reveal_dragwidget = reveal_dragwidget
        self.parent_window = parent_window
        self.main_window = main_window
        self.game_window = game_window
        self.player_position = player_position
        self.num_players = num_players
        self.player_name = player_name

        self.cards = []


class PlayerWindow(QMainWindow):
    def __init__(
        self,
        player_id,
        player_number,
        player_dragwidget,
        reveal_dragwidget,
        parent_window,
        main_window,
        index,
        num_players,
        player_name,
        app,
    ):
        super().__init__(parent_window)
        self.player_id = player_id
        self.player_number = player_number + 1
        # self.player_number = player_number
        self.parent_window = parent_window
        self.main_window = main_window
        self.app = app

        self.player_dragwidget = player_dragwidget
        self.reveal_dragwidget = reveal_dragwidget

        self.player_dragwidget.setAcceptDrops(True)
        self.reveal_dragwidget.setAcceptDrops(True)

        # Initialize other attributes
        self.player_cards = []
        self.cards_revealed = False
        self.call_button_clicked = False
        self.reveal_button_clicked = False
        self.player_index = index
        self.player_number = index + 1
        self.num_players = num_players
        self.player_name = player_name  # Store player's name
        self.initialize_game()
        self.turns_after_call = 0
        self.players = []  # List to hold all players
        self.items = []
        self.cards = []  #  OJOJOJOJOJOJOJO

        self.player_chips = 1  # Set the initial amount of chips for each player

        # Initialize the UI after setting up the widgets
        self.init_ui()

        self.player_dragwidget.cardDropped.connect(self.on_card_dropped)

        # Check if signal-slot connection for reveal_cards button exists and disconnect if needed
        try:
            self.reveal_button.clicked.disconnect()
        except TypeError:
            pass

        # Connect the reveal_cards button click event to the reveal_cards method
        self.reveal_button.clicked.connect(self.reveal_cards)

        # Connect the reveal_cards method to the reveal button only for the first window
        if player_number != 1:
            self.reveal_button.setEnabled(False)
            self.reveal_button.setStyleSheet("background-color: red;")

        # Ensure reveal_cards is initialized as an empty list
        self.reveal_cards = []

        # Ensure player_dragwidget is properly initialized
        if self.player_dragwidget is None or not hasattr(
            self.player_dragwidget, "orderChanged"
        ):
            raise ValueError(
                "class PlayerWindow - player_dragwidget is not properly initialized."
            )

        # Ensure reveal_dragwidget is properly initialized
        if self.reveal_dragwidget is None:
            raise ValueError(
                "class PlayerWindow - reveal_dragwidget is not properly initialized."
            )

        # Ensure player_dragwidget.items is initialized
        if not hasattr(self.player_dragwidget, "items"):
            self.player_dragwidget.items = []

    def init_ui(self):
        self.setWindowTitle(f"Viuda - Player {self.player_number} - {self.player_name}")
        self.setGeometry(100, 100, 400, 400)

        # Reveal cards dock widget
        reveal_cards = QDockWidget("Reveal cards")
        reveal_cards.setWidget(self.reveal_dragwidget)
        self.addDockWidget(Qt.TopDockWidgetArea, reveal_cards)

        # Player cards dock widget
        player_cards = QDockWidget("Player cards")
        player_cards.setWidget(self.player_dragwidget)
        player_cards.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(Qt.BottomDockWidgetArea, player_cards)

        buttons_dock = QDockWidget("Buttons")
        buttons_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)

        self.reveal_button = QPushButton("Reveal cards")
        self.reveal_button.setStyleSheet("background-color: green;")
        self.reveal_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.reveal_button.setMaximumWidth(100)  # Set the desired maximum width
        self.reveal_button.setMinimumWidth(100)  # Set the desired minimum width
        self.reveal_button.clicked.connect(self.reveal_cards)

        self.exchange_button = QPushButton("Exchange cards")
        self.exchange_button.setStyleSheet("background-color: red;")
        self.exchange_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.exchange_button.setMaximumWidth(100)  # Set the desired maximum width
        self.exchange_button.setMinimumWidth(100)  # Set the desired minimum width
        self.exchange_button.clicked.connect(self.exchange_cards)

        self.call_button = QPushButton("Call")
        self.call_button.setStyleSheet("background-color: red;")
        self.call_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.call_button.setMaximumWidth(100)  # Set the desired maximum width
        self.call_button.setMinimumWidth(100)
        self.call_button.clicked.connect(self.call_cards)

        self.pass_button = QPushButton("Pass")
        self.pass_button.setStyleSheet("background-color: red;")
        self.pass_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.pass_button.setMaximumWidth(100)  # Set the desired maximum width
        self.pass_button.setMinimumWidth(100)
        self.pass_button.clicked.connect(self.pass_cards)

        layout = QHBoxLayout()
        layout.addWidget(self.reveal_button)
        layout.addWidget(self.exchange_button)
        layout.addWidget(self.call_button)
        layout.addWidget(self.pass_button)

        buttons_widget = QWidget()
        buttons_widget.setLayout(layout)
        buttons_dock.setWidget(buttons_widget)
        self.addDockWidget(Qt.TopDockWidgetArea, buttons_dock)

        # Add chip display below buttons
        self.chips_label = QLabel(self)
        self.update_chips_label(self.player_chips)
        layout.addWidget(self.chips_label)

        # self.setLayout(layout)

        # Add the buttons dock on top of the reveal cards dock
        reveal_cards.setTitleBarWidget(buttons_dock)

    def check_for_side_chip(self):
        if self.main_window.side_chips > 0:
            self.main_window.side_chips -= 1
            self.chips += 1
            self.main_window.update_side_chip_label()
            self.chip_label.setText(f"P1 check_for_side_chip - Chips: {self.chips}")
        else:
            # If there are no side chips left, the player should be removed.
            self.main_window.remove_player_from_game(self)

    def update_chips_label(self, chips):
        self.player_chips = chips
        self.chips_label.setText(f"P1-2 - Player Chips: {self.player_chips}")
        print(
            f"P2-2 - Updated chips label for Player {self.player_number} to {self.player_chips}"
        )

    def create_card_widget(self, card):
        card_widget = CardWidget(card, parent_window=self)
        return card_widget

    def initialize_game(self):
        player = Player(
            self.player_id,
            self.player_number,
            self.player_dragwidget,
            self.reveal_dragwidget,
            self.parent_window,
            self.main_window,
            self,
            self.player_index + 1,
            self.num_players,
            self.player_name,
        )
        self.player = player

    def find_card_label(self, card):
        for card_label in self.cards:
            if card_label.card == card:  # Assuming card_label has a card attribute
                return card_label
        return None

    def is_current_player_turn(self):
        return (
            self.pass_button.isEnabled()
            and self.pass_button.styleSheet() == "background-color: green;"
        )

    def is_action_allowed(self):
        try:
            # Check if the exchange button is enabled and green
            exchange_button_enabled = self.exchange_button.isEnabled()
            exchange_button_color = (
                self.exchange_button.palette().button().color().name()
            )
            exchange_button_is_green = (
                exchange_button_color == "#008000"
            )  # Green color check

            # Check if the reveal button is hidden
            reveal_button_hidden = self.reveal_button.isHidden()

            # Check if the pass button is enabled and green
            pass_button_enabled = self.pass_button.isEnabled()
            pass_button_color = self.pass_button.palette().button().color().name()
            pass_button_is_green = pass_button_color == "#008000"  # Green color check

            # The action is allowed if the exchange button is green, reveal button is hidden, and pass button is green
            if (
                exchange_button_is_green
                and reveal_button_hidden
                and pass_button_is_green
            ):
                return True

            return False

        except Exception as e:
            print(f"Error in is_action_allowed: {e}")
            return False

    def is_rearrange_action(self, event):
        return event.source() == self and self == self.parent_window.player_dragwidget

    def check_drag_drop_actions(self):
        if self.parent_window.is_current_player_turn():
            if (
                self.reveal_dragwidget.current_item is not None
                and self.player_dragwidget.current_item is None
            ):
                # Dragged from reveal_dragwidget to player_dragwidget
                self.reveal_dragwidget.current_item.setParent(self.player_dragwidget)
                self.end_current_player_turn()
            elif (
                self.player_dragwidget.current_item is not None
                and self.reveal_dragwidget.current_item is None
            ):
                # Dragged from player_dragwidget to reveal_dragwidget
                self.player_dragwidget.current_item.setParent(self.reveal_dragwidget)
                self.end_current_player_turn()

    def get_next_player(self):
        # Get the next player in sequence
        if self.main_window and self.main_window.players:
            next_index = (self.main_window.player_index + 1) % len(
                self.main_window.players
            )
            return self.main_window.players[next_index]
        return None

    def add_card(self, card, player_dragwidget=True):
        card_label = CardWidget(
            card, self.player_dragwidget, self.reveal_dragwidget, parent_window=self
        )
        if player_dragwidget:
            self.player_dragwidget.add_item(card_label)
        else:
            self.reveal_dragwidget.add_item(card_label)
        card_label.setAlignment(Qt.AlignCenter)

    # In PlayerWindow class
    def reveal_cards1(self):
        try:
            # --- ADD THIS GUARD ---
            if not self.main_window.hand_in_progress:
                print("Reveal action ignored: Hand not in progress.")
                return
            # -----------------------

            self.main_window.consecutive_passes = 0
            print("Reveal button clicked")
            self.cards_revealed = True

            # ... (all the logic for getting card lists and swapping them is UNCHANGED) ...
            self.reveal_cards = [
                card_label.card for card_label in self.reveal_dragwidget.items
            ]
            self.player_cards = [
                card_label.card for card_label in self.player_dragwidget.items
            ]
            self.player_dragwidget.clear()
            self.reveal_dragwidget.clear()
            for card in self.player_cards:
                card.set_face_down()
                card_label = CardWidget(
                    card,
                    self.player_dragwidget,
                    self.reveal_dragwidget,
                    parent_window=self,
                )
                self.reveal_dragwidget.add_item(card_label)
            for card in self.reveal_cards:
                card.set_face_up()
                card.load_image()
                card_label = CardWidget(
                    card,
                    self.player_dragwidget,
                    self.reveal_dragwidget,
                    parent_window=self,
                )
                self.player_dragwidget.add_item(card_label)
            self.reveal_cards = [
                card_label.card for card_label in self.reveal_dragwidget.items
            ]
            self.player_cards = [
                card_label.card for card_label in self.player_dragwidget.items
            ]
            for window in self.main_window.player_windows:
                window.reveal_button_clicked = True

            # --- REPLACED a complex block with the new, reliable logic ---
            # 1. Find the next active player
            next_player_window = self.main_window.get_next_active_player(
                self.player_number
            )
            if not next_player_window:
                self.main_window.check_end_hand()
                return

            # 2. Loop through all player windows to update their state
            for window in self.main_window.player_windows:
                window.reveal_button.hide()  # Hide for everyone

                if window == self:
                    # This is the current player who just acted.
                    # Update their own cards to be face-up.
                    for card_label in window.reveal_dragwidget.items:
                        card_label.card.set_face_up()
                        card_label.card.load_image()
                        scaled_pixmap = card_label.card.pixmap.scaled(
                            50, 80, Qt.AspectRatioMode.KeepAspectRatio
                        )
                        card_label.setPixmap(scaled_pixmap)
                    for card_label in window.player_dragwidget.items:
                        card_label.card.set_face_up()
                        card_label.card.load_image()
                        scaled_pixmap = card_label.card.pixmap.scaled(
                            50, 80, Qt.AspectRatioMode.KeepAspectRatio
                        )
                        card_label.setPixmap(scaled_pixmap)

                    # Disable all their buttons as their turn is over.
                    self.exchange_button.setEnabled(False)
                    self.exchange_button.setStyleSheet("background-color: red;")
                    self.call_button.setEnabled(False)
                    self.call_button.setStyleSheet("background-color: red;")
                    self.pass_button.setEnabled(False)
                    self.pass_button.setStyleSheet("background-color: red;")

                elif window == next_player_window:
                    # This is the next active player. Enable their buttons.
                    self.set_next_player_button_states(window)
                    # Update their reveal widget with the current state.
                    window.reveal_dragwidget.clear()
                    for card in self.reveal_cards:
                        card_label = CardWidget(
                            card,
                            window.player_dragwidget,
                            window.reveal_dragwidget,
                            parent_window=window,
                        )
                        card_label.card.set_face_up()
                        card_label.card.load_image()
                        card_label.setPixmap(
                            card_label.card.pixmap.scaled(
                                50, 80, Qt.AspectRatioMode.KeepAspectRatio
                            )
                        )
                        window.reveal_dragwidget.add_item(card_label)

                else:
                    # This is any other player (not current, not next).
                    # All their buttons should be disabled.
                    window.exchange_button.setEnabled(False)
                    window.exchange_button.setStyleSheet("background-color: red;")
                    window.call_button.setEnabled(False)
                    window.call_button.setStyleSheet("background-color: red;")
                    window.pass_button.setEnabled(False)
                    window.pass_button.setStyleSheet("background-color: red;")
                    # Also update their reveal widget.
                    window.reveal_dragwidget.clear()
                    for card in self.reveal_cards:
                        card_label = CardWidget(
                            card,
                            window.player_dragwidget,
                            window.reveal_dragwidget,
                            parent_window=window,
                        )
                        card_label.card.set_face_up()
                        card_label.card.load_image()
                        card_label.setPixmap(
                            card_label.card.pixmap.scaled(
                                50, 80, Qt.AspectRatioMode.KeepAspectRatio
                            )
                        )
                        window.reveal_dragwidget.add_item(card_label)
            # --- END OF REPLACEMENT ---

            QTimer.singleShot(0, lambda: self.main_window.check_end_hand())
        except Exception as e:
            print(f"An error occurred: {e}")

    # In PlayerWindow class
    def reveal_cards(self):
        try:
            if (
                not self.main_window.hand_in_progress
                or not self.is_current_player_turn()
            ):
                return

            self.main_window.consecutive_passes = 0
            print("Reveal button clicked")
            self.cards_revealed = True

            # All of this logic is correct for updating the card widgets
            self.reveal_cards = [
                card_label.card for card_label in self.reveal_dragwidget.items
            ]
            self.player_cards = [
                card_label.card for card_label in self.player_dragwidget.items
            ]
            self.player_dragwidget.clear()
            self.reveal_dragwidget.clear()
            for card in self.player_cards:
                card.set_face_down()
                card_label = CardWidget(
                    card,
                    self.player_dragwidget,
                    self.reveal_dragwidget,
                    parent_window=self,
                )
                self.reveal_dragwidget.add_item(card_label)
            for card in self.reveal_cards:
                card.set_face_up()
                card.load_image()
                card_label = CardWidget(
                    card,
                    self.player_dragwidget,
                    self.reveal_dragwidget,
                    parent_window=self,
                )
                self.player_dragwidget.add_item(card_label)
            self.reveal_cards = [
                card_label.card for card_label in self.reveal_dragwidget.items
            ]
            self.player_cards = [
                card_label.card for card_label in self.player_dragwidget.items
            ]

            # Propagate the new reveal cards to other players' views
            for window in self.main_window.player_windows:
                if window != self:
                    window.reveal_dragwidget.clear()
                    for card in self.reveal_cards:
                        card_label = CardWidget(
                            card,
                            window.player_dragwidget,
                            window.reveal_dragwidget,
                            parent_window=window,
                        )
                        card_label.setPixmap(
                            card_label.card.pixmap.scaled(
                                50, 80, Qt.AspectRatioMode.KeepAspectRatio
                            )
                        )
                        window.reveal_dragwidget.add_item(card_label)

            # Hide the reveal button for all players for the rest of the hand
            for window in self.main_window.player_windows:
                window.reveal_button.hide()

            # --- SIMPLIFIED ENDING ---
            # After revealing, simply end the current player's turn.
            self.end_current_player_turn()
            # -------------------------

        except Exception as e:
            print(f"An error occurred in reveal_cards: {e}")

    # In PlayerWindow class
    def exchange_cards1(self):
        try:
            # --- ADD THIS GUARD ---
            if not self.main_window.hand_in_progress:
                print("Exchange action ignored: Hand not in progress.")
                return
            # -----------------------

            if not self.is_current_player_turn():
                return

            self.main_window.consecutive_passes = 0
            print("Exchange button clicked")

            # ... (all the logic for getting card lists and swapping them is UNCHANGED) ...
            self.reveal_cards = [
                card_label.card for card_label in self.reveal_dragwidget.items
            ]
            self.player_cards = [
                card_label.card for card_label in self.player_dragwidget.items
            ]
            player_cards_before_exchange = self.player_dragwidget.items.copy()
            reveal_cards_before_exchange = self.reveal_dragwidget.items.copy()
            self.player_dragwidget.clear()
            self.reveal_dragwidget.clear()
            for card_label in player_cards_before_exchange:
                self.reveal_dragwidget.addWidget(card_label)
            for card_label in reveal_cards_before_exchange:
                self.player_dragwidget.addWidget(card_label)
            self.reveal_cards = [
                card_label.card for card_label in self.reveal_dragwidget.items
            ]
            self.player_cards = [
                card_label.card for card_label in self.player_dragwidget.items
            ]

            # ... (all the logic for highlighting and propagating changes is UNCHANGED) ...
            for card_label in self.reveal_dragwidget.items:
                card_label.card.highlight_wild_card(card_label, True)
            for card_label in self.player_dragwidget.items:
                card_label.card.highlight_wild_card(
                    card_label, not card_label.card.set_face_down
                )
            for window in self.main_window.player_windows:
                if window != self:
                    window.reveal_dragwidget.clear()
                    for card in self.reveal_cards:
                        new_card_label = CardWidget(
                            card,
                            window.player_dragwidget,
                            window.reveal_dragwidget,
                            parent_window=self,  # Should probably be parent_window=window
                        )
                        card.set_face_up()
                        new_card_label.setPixmap(
                            card.pixmap.scaled(
                                50, 80, Qt.AspectRatioMode.KeepAspectRatio
                            )
                        )
                        window.reveal_dragwidget.addWidget(new_card_label)

            # Disable buttons for the current player
            self.exchange_button.setEnabled(False)
            self.exchange_button.setStyleSheet("background-color: red;")
            self.call_button.setEnabled(False)
            self.call_button.setStyleSheet("background-color: red;")
            self.pass_button.setEnabled(False)
            self.pass_button.setStyleSheet("background-color: red;")

            # --- REPLACED a complex block with the new, reliable logic ---
            next_player_window = self.main_window.get_next_active_player(
                self.player_number
            )
            if not next_player_window:
                self.main_window.check_end_hand()
                return
            # --- END OF REPLACEMENT ---

            # Set the button states for the next player
            self.set_next_player_button_states(next_player_window)

            print("Exchange cards completed")
            QTimer.singleShot(0, lambda: self.main_window.check_end_hand())
        except Exception as e:
            print(f"Error in exchange_cards: {e}")

    # In PlayerWindow class
    def exchange_cards(self):
        try:
            if (
                not self.main_window.hand_in_progress
                or not self.is_current_player_turn()
            ):
                return

            self.main_window.consecutive_passes = 0
            print("Exchange button clicked")

            # All of this logic for swapping and propagating cards is correct
            player_cards_before_exchange = self.player_dragwidget.items.copy()
            reveal_cards_before_exchange = self.reveal_dragwidget.items.copy()
            self.player_dragwidget.clear()
            self.reveal_dragwidget.clear()
            for card_label in player_cards_before_exchange:
                self.reveal_dragwidget.addWidget(card_label)
            for card_label in reveal_cards_before_exchange:
                self.player_dragwidget.addWidget(card_label)

            self.reveal_cards = [
                card_label.card for card_label in self.reveal_dragwidget.items
            ]
            self.player_cards = [
                card_label.card for card_label in self.player_dragwidget.items
            ]

            for card_label in self.reveal_dragwidget.items:
                card_label.card.highlight_wild_card(card_label, True)

            # NEW, CORRECTED CODE
            for card_label in self.player_dragwidget.items:
                # A card in the player's hand is always considered "face up" for highlighting purposes.
                card_label.card.highlight_wild_card(card_label, is_face_up=True)

            for window in self.main_window.player_windows:
                if window != self:
                    window.reveal_dragwidget.clear()
                    for card in self.reveal_cards:
                        new_card_label = CardWidget(
                            card,
                            window.player_dragwidget,
                            window.reveal_dragwidget,
                            parent_window=window,
                        )
                        new_card_label.setPixmap(
                            card.pixmap.scaled(
                                50, 80, Qt.AspectRatioMode.KeepAspectRatio
                            )
                        )
                        window.reveal_dragwidget.addWidget(new_card_label)

            # --- SIMPLIFIED ENDING ---
            # After exchanging, simply end the current player's turn.
            self.end_current_player_turn()
            # -------------------------

        except Exception as e:
            print(f"Error in exchange_cards: {e}")

    # In PlayerWindow class
    def pass_cards1(self):
        try:
            # --- ADD THIS GUARD ---
            if not self.main_window.hand_in_progress:
                print("Pass action ignored: Hand not in progress.")
                return
            # -----------------------

            if (
                self.pass_button.isEnabled()
                and self.pass_button.styleSheet() == "background-color: green;"
            ):
                self.main_window.consecutive_passes += 1
                self.pass_button.setEnabled(False)
                self.pass_button.setStyleSheet("background-color: red;")

                # --- NEW, RELIABLE LOGIC ---
                next_player_window = self.main_window.get_next_active_player(
                    self.player_number
                )
                if not next_player_window:
                    # This can happen if only one player is left.
                    self.main_window.check_end_hand()
                    return
                # --- END OF NEW LOGIC ---

                # Disable call buttons for all players first
                for window in self.main_window.player_windows:
                    window.call_button.setEnabled(False)
                    window.call_button.setStyleSheet("background-color: red;")

                # Set button states for all players
                for window in self.main_window.player_windows:
                    if window == next_player_window:
                        self.set_next_player_button_states(window)
                    else:
                        # Deactivate buttons for all other players (including self)
                        window.reveal_button.setEnabled(False)
                        window.reveal_button.setStyleSheet("background-color: red;")
                        window.pass_button.setEnabled(False)
                        window.pass_button.setStyleSheet("background-color: red;")
                        # Call button is already handled above
                        window.exchange_button.setEnabled(False)
                        window.exchange_button.setStyleSheet("background-color: red;")

                QTimer.singleShot(0, lambda: self.main_window.check_end_hand())
        except Exception as e:
            print(f"An error occurred in pass_cards: {e}")

    # In PlayerWindow class
    def pass_cards(self):
        if not self.main_window.hand_in_progress or not self.is_current_player_turn():
            return

        print(f"Player {self.player_number} clicked Pass.")
        self.main_window.consecutive_passes += 1
        self.end_current_player_turn()  # Simply end the turn

    # In PlayerWindow class
    def call_cards(self):
        # --- ADD THIS GUARD ---
        if not self.main_window.hand_in_progress:
            print("Call action ignored: Hand not in progress.")
            return
        # -----------------------

        print("\n--- call_cards method started ---")
        print(f"call_cards button clicked by Player {self.player_number}")

        if not self.is_current_player_turn():
            return

        self.main_window.consecutive_passes = 0
        self.main_window.call_button_clicked = True
        self.main_window.turns_after_call = 1
        self.main_window.calling_player_number = self.player_number

        # --- NEW, RELIABLE LOGIC ---
        next_player_window = self.main_window.get_next_active_player(self.player_number)
        if not next_player_window:
            self.main_window.check_end_hand()  # Only one player left, end the game
            return
        # --- END OF NEW LOGIC ---

        # Disable all buttons for ALL players first
        for window in self.main_window.player_windows:
            window.call_button.setEnabled(False)
            window.call_button.setStyleSheet("background-color: red;")
            window.pass_button.setEnabled(False)
            window.pass_button.setStyleSheet("background-color: red;")
            window.exchange_button.setEnabled(False)
            window.exchange_button.setStyleSheet("background-color: red;")
            if hasattr(window, "reveal_button"):
                window.reveal_button.setEnabled(False)
                window.reveal_button.setStyleSheet("background-color: red;")

        # Enable buttons ONLY for the next active player
        next_player_window.reveal_button.setEnabled(True)
        next_player_window.reveal_button.setStyleSheet("background-color: green;")
        next_player_window.pass_button.setEnabled(True)
        next_player_window.pass_button.setStyleSheet("background-color: green;")

        if next_player_window.reveal_button.isHidden():
            next_player_window.exchange_button.setEnabled(True)
            next_player_window.exchange_button.setStyleSheet("background-color: green;")

        # The call button remains disabled for everyone during the final round.

        print("\n--- call_cards method completed ---")
        QTimer.singleShot(0, lambda: self.main_window.check_end_hand())

    def set_initial_button_states(self, current_player_number, call_button_clicked):
        try:
            # logging.debug(
            #     f"Player {self.player_number}: Setting initial button states (current_player_number: {current_player_number}, call_button_clicked: {call_button_clicked})")
            self.reveal_button.setEnabled(True)
            self.reveal_button.setStyleSheet("background-color: green;")
            print(f"Player {self.player_number}: Reveal button enabled (green)")

            if self.player_number == current_player_number:
                self.exchange_button.setEnabled(False)
                self.exchange_button.setStyleSheet("background-color: red;")
                self.call_button.setEnabled(True)
                self.call_button.setStyleSheet("background-color: green;")
                self.pass_button.setEnabled(True)
                self.pass_button.setStyleSheet("background-color: green;")
                print(
                    f"Player {self.player_number}: Exchange button disabled (red), Call button enabled (green), Pass button enabled (green)"
                )
            else:
                self.reveal_button.setEnabled(False)
                self.reveal_button.setStyleSheet("background-color: red;")
                self.exchange_button.setEnabled(False)
                self.exchange_button.setStyleSheet("background-color: red;")
                self.call_button.setEnabled(False)
                self.call_button.setStyleSheet("background-color: red;")
                self.pass_button.setEnabled(False)
                self.pass_button.setStyleSheet("background-color: red;")
                print(f"Player {self.player_number}: All buttons disabled (red)")
        except Exception as e:
            print(f"An error occurred in set_initial_button_states: {e}")
            traceback.print_exc()

    def set_next_player_button_states(self, next_player_window):
        try:
            # logging.debug(
            #     f"Player {self.player_number}: Setting button states for next player (Player {next_player_window.player_number})")

            next_player_window.reveal_button.setEnabled(True)
            next_player_window.reveal_button.setStyleSheet("background-color: green;")
            print(
                f"Player {next_player_window.player_number}: Reveal button enabled (green)"
            )

            # Ensure the exchange button is disabled and red when the reveal button is enabled
            if next_player_window.reveal_button.isHidden():
                next_player_window.exchange_button.setEnabled(True)
                next_player_window.exchange_button.setStyleSheet(
                    "background-color: green;"
                )
            else:
                next_player_window.exchange_button.setEnabled(False)
                next_player_window.exchange_button.setStyleSheet(
                    "background-color: red;"
                )
            print(
                f"Player {next_player_window.player_number}: Exchange button state: Enabled: {next_player_window.exchange_button.isEnabled()}, StyleSheet: {next_player_window.exchange_button.styleSheet()}"
            )

            if (
                not hasattr(self.main_window, "call_button_clicked")
                or not self.main_window.call_button_clicked
            ):
                next_player_window.call_button.setEnabled(True)
                next_player_window.call_button.setStyleSheet("background-color: green;")
                print(
                    f"Player {next_player_window.player_number}: Call button enabled (green)"
                )
            else:
                next_player_window.call_button.setEnabled(False)
                next_player_window.call_button.setStyleSheet("background-color: red;")
                print(
                    f"Player {next_player_window.player_number}: Call button disabled (red)"
                )

            next_player_window.pass_button.setEnabled(True)
            next_player_window.pass_button.setStyleSheet("background-color: green;")
            print(
                f"Player {next_player_window.player_number}: Pass button enabled (green)"
            )

        except Exception as e:
            print(f"An error occurred in set_next_player_button_states: {e}")
            traceback.print_exc()

    def end_current_player_turn1(self):
        self.exchange_button.setEnabled(False)
        self.exchange_button.setStyleSheet("background-color: red;")
        self.call_button.setEnabled(False)
        self.call_button.setStyleSheet("background-color: red;")
        self.pass_button.setEnabled(False)
        self.pass_button.setStyleSheet("background-color: red;")

        # --- NEW, RELIABLE LOGIC ---
        next_player_window = self.main_window.get_next_active_player(self.player_number)
        if not next_player_window:
            self.main_window.check_end_hand()
            return
        # --- END OF NEW LOGIC ---

        self.main_window.set_next_player_button_states(next_player_window)

    # In PlayerWindow class
    def end_current_player_turn(self):
        print(f"--- Player {self.player_number}'s turn is ending. ---")

        # --- NEW CENTRALIZED LOGIC ---
        # This function is now the ONLY place that increments the turn counter.
        if self.main_window.call_button_clicked:
            self.main_window.turns_after_call += 1
        # --- END OF NEW LOGIC ---

        # Disable buttons for the current player
        self.exchange_button.setEnabled(False)
        self.exchange_button.setStyleSheet("background-color: red;")
        self.call_button.setEnabled(False)
        self.call_button.setStyleSheet("background-color: red;")
        self.pass_button.setEnabled(False)
        self.pass_button.setStyleSheet("background-color: red;")
        # Also disable reveal button if it exists
        if hasattr(self, "reveal_button") and not self.reveal_button.isHidden():
            self.reveal_button.setEnabled(False)
            self.reveal_button.setStyleSheet("background-color: red;")

        # Find and set up the next player
        next_player_window = self.main_window.get_next_active_player(self.player_number)
        if not next_player_window:
            # No more active players, trigger the end-of-hand check immediately
            print("end_current_player_turn: No next active player found.")
            QTimer.singleShot(0, self.main_window.check_end_hand)
            return

        # Set the next player's turn state
        self.main_window.current_player_number = next_player_window.player_number
        self.set_next_player_button_states(next_player_window)

        # Finally, check if the hand should end
        QTimer.singleShot(0, self.main_window.check_end_hand)

    def enable_drag_and_drop(self):
        self.reveal_dragwidget.setAcceptDrops(True)
        self.player_dragwidget.setAcceptDrops(True)

        for item in self.reveal_dragwidget.items:
            item.setAcceptDrops(True)
        for item in self.player_dragwidget.items:
            item.setAcceptDrops(True)

    def set_cards_face_down(self, drag_widget):
        for item in drag_widget.items:
            item.card.set_face_down()
            item.card.load_image()
            item.setPixmap(
                item.card.pixmap.scaled(50, 80, Qt.AspectRatioMode.KeepAspectRatio)
            )

    def set_cards_face_up(self):
        if self.cards_revealed:
            print("Setting cards face up in DragWidget")
            for card_label in self.items:
                if not card_label.card.face_up:
                    card_label.card.face_up = True
                    card_label.card.load_image()  # Load the image for the card
                    scaled_pixmap = card_label.card.pixmap.scaled(
                        50, 80, Qt.AspectRatioMode.KeepAspectRatio
                    )
                    card_label.setPixmap(scaled_pixmap)

    def add_cards_to_widget1(self, widget, cards, reveal):
        try:
            widget.clear()
            for card in cards[:5]:  # Ensure only the first 5 cards are added
                card_label = CardWidget(
                    card,
                    self.player_dragwidget,
                    self.reveal_dragwidget,
                    parent_window=self,
                )
                if reveal:
                    card.set_face_down()
                    is_face_up = False
                else:
                    card.set_face_up()
                    is_face_up = True
                scaled_pixmap = card.pixmap.scaled(
                    50, 80, Qt.AspectRatioMode.KeepAspectRatio
                )
                card_label.setPixmap(scaled_pixmap)

                # Highlight wild card
                card.highlight_wild_card(card_label, is_face_up)

                widget.add_item(card_label)
        except Exception as e:
            print(f"An error occurred in add_cards_to_widget: {e}")

    def add_cards_to_widget(self, widget, cards, reveal):
        try:
            # This was already here, but just for reference
            # widget.clear()

            for card in cards[:5]:
                # --- THE FIX IS HERE ---
                # We now pass 'face_down=reveal' directly to the CardWidget constructor.
                # The 'reveal' parameter is True for the reveal_dragwidget, correctly setting the cards to face down.
                card_label = CardWidget(
                    card,
                    self.player_dragwidget,
                    self.reveal_dragwidget,
                    parent_window=self,
                    face_down=reveal,  # <-- CRITICAL FIX
                )
                # --- END OF FIX ---

                # The CardWidget's __init__ method now handles setting the pixmap correctly,
                # so the code below is no longer needed here.

                # scaled_pixmap = card.pixmap.scaled(50, 80, Qt.AspectRatioMode.KeepAspectRatio)
                # card_label.setPixmap(scaled_pixmap)
                # card.highlight_wild_card(card_label, is_face_up)

                widget.add_item(card_label)
        except Exception as e:
            print(f"An error occurred in add_cards_to_widget: {e}")
            traceback.print_exc()  # Added for better error reporting

    def update_cards(self, reveal_cards, player_cards):
        try:
            self.reveal_cards = reveal_cards[
                :5
            ]  # Ensure only the first 5 cards are used for reveal
            self.player_cards = player_cards[
                :5
            ]  # Ensure only the first 5 cards are used for player

            self.reveal_dragwidget.clear()
            self.add_cards_to_widget(
                self.reveal_dragwidget, self.reveal_cards, reveal=True
            )

            self.player_dragwidget.clear()
            self.add_cards_to_widget(
                self.player_dragwidget, self.player_cards, reveal=False
            )
        except Exception as e:
            print(f"An error occurred in update_cards: {e}")

    def get_card_details(self):
        # This method will gather and return the details of the cards in the player's widgets
        player_cards = [
            card.card
            for card in self.player_dragwidget.children()
            if hasattr(card, "card")
        ]
        reveal_cards = [
            card.card
            for card in self.reveal_dragwidget.children()
            if hasattr(card, "card")
        ]
        return f"Player CardWidget: {player_cards}, Reveal CardWidget: {reveal_cards}"

    def clear_widgets(self):
        try:
            self.player_dragwidget.clear()
            self.reveal_dragwidget.clear()
        except Exception as e:
            print(f"An error occurred in clear_widgets: {e}")

    def clear_widget(self, widget):
        """Remove all items from the given widget."""
        for card in widget.findChildren(CardWidget):
            widget.remove_item(card)
            # print(f"clear_widget- Removed {card.card} from items.")

    def on_card_dropped(self, card, source, target):
        try:
            if isinstance(target, DragWidget) and isinstance(source, DragWidget):
                print(f"Card {card.value}{card.suit} dropped from {source} to {target}")
                source.remove_item(card)
                target.add_item(card)
        except Exception as e:
            print(f"Error in on_card_dropped: {e}")

    def print_cards(self):
        # pass
        reveal_card_strings = [
            f"{str(card.value)}{card.suit}" for card in self.reveal_cards
        ]
        player_card_strings = [
            f"{str(card.value)}{card.suit}" for card in self.player_cards
        ]
        print(
            f"1191- Player {self.player_number} Reveal CardWidget: {reveal_card_strings}"
        )
        print(
            f"1192- Player {self.player_number} Player CardWidget: {player_card_strings}"
        )
