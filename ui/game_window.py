import logging
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QDialog,
    QLabel,
    QMessageBox,
    QDockWidget,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLineEdit,
    QPushButton,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap

# Import all our new modules
from core.card import Deck
from core.dealer import Dealer
from ui.drag_widget import DragWidget
from ui.player_window import PlayerWindow


class Flop:
    def __init__(self):
        self.cards = []

    def add_card(self, card):
        self.cards.append(card)

    def clear(self):
        self.cards = []


class GameWindow(QMainWindow):
    def __init__(self, app, num_players, player_names, parent=None):
        super().__init__(parent)
        self.app = app
        self.num_players = num_players
        self.player_names = player_names
        self.all_player_cards = [
            [] for _ in range(num_players)
        ]  # Initialize with empty lists for each player
        self.all_reveal_cards = []
        self.player_windows = []
        self.reveal_dragwidgets = []
        self.players = []
        self.player_index = 0
        self.deck = Deck()

        self.player_statuses = [
            "Active" for _ in range(num_players)
        ]  # Initial status for all players

        # Initialize reveal_dragwidget and player_dragwidget instances
        self.reveal_dragwidget = DragWidget(self, "reveal_dragwidget")
        self.player_dragwidget = DragWidget(self, "player_dragwidget")

        self.flop = Flop()  # Assuming you have a Flop class or similar

        # Initialize labels for chips (assuming you have these labels defined in your UI)
        self.table_chip_label = QLabel(self)
        self.side_chip_label = QLabel(self)

        self.table_chips = 1  # Start with one chip on the table
        self.side_chips = 1  # Two chips available on the side

        # Pass self (GameWindow instance) to Dealer along with the other required arguments
        self.dealer = Dealer(
            self,  # Reference to the GameWindow instance
            self.player_windows,
            self.flop,
            self.table_chip_label,
            self.side_chip_label,
            self.table_chips,
            self.side_chips,
            self.deck,
        )

        self.calling_player_number = None

        self.current_player_number = 1
        self.current_player = 0
        self.call_button_clicked = False
        self.turns_after_call = 0
        self.consecutive_passes = 0
        # --- ADD THIS LINE ---
        self.last_loser_number = 0
        self.hand_starter_number = 0
        # ---------------------

        self.next_player_turn = None
        self.hand_in_progress = False  # Add this flag
        self.init_ui()
        self.init_ui_chips_and_list()

        # Connect signals from Dealer to update GUI
        self.dealer.table_chip_label_updated.connect(self.update_table_chip_label)
        self.dealer.side_chip_label_updated.connect(self.update_side_chip_label)
        self.dealer.player_chips_updated.connect(self.update_player_chips_label)

    def init_ui_chips_and_list(self):
        """Initialize the UI for chips labels and player list dock without icons."""
        window_width = 100
        window_height = 300
        window_offset_x = 800  # Move to the left edge
        window_offset_y = 100  # Move to the top edge

        # Set a custom window title
        self.setWindowTitle(
            "Viuda - mire el comodin"
        )  # Replace with the desired game name

        # Initialize labels for chips
        self.table_chip_label = QLabel(self)
        self.side_chip_label = QLabel(self)

        # Setup labels for chips
        self.update_table_chip_label()
        self.update_side_chip_label()

        # Create a QDockWidget for the chip labels (no icons)
        self.chip_dock = QDockWidget("Chips", self)
        self.chip_dock.setFeatures(
            QDockWidget.NoDockWidgetFeatures
        )  # Disable all icons

        # Create a widget to hold the chip labels
        chip_widget = QWidget()
        chip_layout = QVBoxLayout()
        chip_layout.addWidget(self.table_chip_label)
        chip_layout.addWidget(self.side_chip_label)
        chip_widget.setLayout(chip_layout)

        # Set a fixed size for the chip widget
        chip_widget.setFixedSize(320, 50)  # Adjust size to fit labels

        # Add the chip widget to the dock widget
        self.chip_dock.setWidget(chip_widget)

        # Add the dock widget to the main window
        self.addDockWidget(Qt.LeftDockWidgetArea, self.chip_dock)

        # Initialize the player list dock widget (no icons)
        self.player_list_dock = QDockWidget("Player List", self)
        self.player_list_dock.setFeatures(
            QDockWidget.NoDockWidgetFeatures
        )  # Disable all icons
        self.player_list_widget = QListWidget()

        # Add the player list to the dock widget
        self.player_list_dock.setWidget(self.player_list_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.player_list_dock)

        # Populate the player list with names and status indicators
        self.update_player_list()

        # Move the window containing chip labels and player list to the top-left corner
        self.setGeometry(window_offset_x, window_offset_y, window_width, window_height)

    def init_ui(self):
        """Initialize the UI for player windows."""
        screen_resolution = self.app.desktop().screenGeometry()
        screen_width = screen_resolution.width()
        screen_height = screen_resolution.height()

        window_width = 500
        window_height = 400
        window_offset_x = 30
        window_offset_y = 70

        # Create player windows for each player
        for i in range(self.num_players):
            player_dragwidget = DragWidget(parent=None, max_items=6, min_items=5)
            reveal_dragwidget = DragWidget(parent=None, max_items=5, min_items=4)

            self.reveal_dragwidgets.append(reveal_dragwidget)

            player_window = PlayerWindow(
                i + 1,
                i,
                player_dragwidget,
                reveal_dragwidget,
                self,
                self,
                index=i,
                num_players=self.num_players,
                player_name=self.player_names[i],
                app=self.app,
            )
            self.player_windows.append(player_window)

            player_window.player_dragwidget = player_dragwidget
            player_window.reveal_dragwidget = reveal_dragwidget

            player_dragwidget.parent_window = player_window
            reveal_dragwidget.parent_window = player_window

            # Set the geometry of player windows
            window_x = int((screen_width / self.num_players) * i + window_offset_x)
            window_y = int(screen_height / 1.9 - window_height / 2 + window_offset_y)

            player_window.setGeometry(window_x, window_y, window_width, window_height)
            player_window.show()

    # In GameWindow class
    def start_first_hand(self):
        self.deck.shuffle()
        self.deck.update_wild_card(self.table_chips)

        self.all_reveal_cards = self.deck.deal(5)
        self.all_player_cards = [self.deck.deal(5) for _ in range(self.num_players)]

        # Use enumerate to get a reliable index 'i'
        for i, player_window in enumerate(self.player_windows):
            player_window.add_cards_to_widget(
                player_window.reveal_dragwidget, self.all_reveal_cards, reveal=True
            )
            # Use the reliable index 'i' instead of player_number to get the correct set of cards
            player_window.add_cards_to_widget(
                player_window.player_dragwidget,
                self.all_player_cards[i],
                reveal=False,
            )

        # --- ADD/CHANGE THIS LOGIC BLOCK ---
        # Explicitly set the starter for the very first hand.
        self.hand_starter_number = 1
        self.current_player_number = 1
        print(f"--- FIRST HAND --- Player {self.current_player_number} will start.")

        # Set button states for all players based on the starter.
        for player_window in self.player_windows:
            player_window.set_initial_button_states(
                self.current_player_number, call_button_clicked=False
            )
        # --- END OF CHANGES ---

        # (Your wild card highlighting logic remains unchanged)
        for card in self.all_reveal_cards:
            if card.is_wild:
                logging.debug(
                    "5-6 start_first_hand - Card {} is wild and should be highlighted.".format(
                        str(card)
                    )
                )
                for player_window in self.player_windows:
                    for card_widget in player_window.reveal_dragwidget.children():
                        if hasattr(card_widget, "card") and card_widget.card == card:
                            card_widget.setStyleSheet("border: 2px solid red;")

    # In GameWindow class
    def check_end_hand(self):
        try:
            # Get a fresh list of currently active players
            active_players = [
                p
                for p in self.player_windows
                if p.player_chips > 0
                and self.player_statuses[self.player_windows.index(p)] == "Active"
            ]
            num_active_players = len(active_players)

            # --- FIX: PASS BUTTON STRICT RULE CHECK ---
            if self.consecutive_passes >= num_active_players and num_active_players > 1:
                print(
                    f"check_end_hand - All {num_active_players} active players have passed consecutively. Ending hand."
                )
                self.end_hand()
                return

            # --- FIX: CALL BUTTON LOGIC CHECK ---
            if self.call_button_clicked:
                print(
                    f"check_end_hand - Turns after call: {self.turns_after_call}/{num_active_players}"
                )
                if self.turns_after_call >= num_active_players:
                    print(
                        f"check_end_hand - Final round is over ({self.turns_after_call} turns taken). Ending hand."
                    )
                    self.end_hand()
                    return

            print("check_end_hand - Hand not finished yet.")
        except Exception as e:
            print(f"An error occurred in check_end_hand: {e}")
            import traceback

            traceback.print_exc()

    def end_hand(self):
        try:
            print("\n--- end_hand method started ---")
            print(f"Current side chips: {self.side_chips}")

            self.hand_in_progress = False

            # Disable all buttons for all players and set them to yellow
            for window in self.player_windows:
                window.reveal_button.setEnabled(False)
                window.reveal_button.setStyleSheet("background-color: yellow;")
                window.exchange_button.setEnabled(False)
                window.exchange_button.setStyleSheet("background-color: yellow;")
                window.call_button.setEnabled(False)
                window.call_button.setStyleSheet("background-color: yellow;")
                window.pass_button.setEnabled(False)
                window.pass_button.setStyleSheet("background-color: yellow;")

            # --- FIX: Only evaluate hands of ACTIVE players ---
            active_player_windows = [
                p
                for p in self.player_windows
                if self.player_statuses[p.player_index] == "Active"
            ]
            winning_window, losing_window, winning_cards = (
                self.dealer.determine_winner_and_loser(active_player_windows)
            )
            # --- END OF FIX ---

            # Highlight the winning hand's wild cards (UI logic is handled here)
            for card in winning_cards:
                card_label = winning_window.find_card_label(card)
                if card_label:
                    card.highlight_wild_card(card_label, is_face_up=True)

            # --- ADD THIS LINE ---
            self.last_loser_number = losing_window.player_number
            # ---------------------

            # Get the loser object and its index
            loser = losing_window
            loser_index = self.player_windows.index(losing_window)

            # Display winner and loser information
            print(f"Winner: {winning_window.player_name}")
            print(f"Loser: {loser.player_name}")
            self.dealer.display_winner(winning_window)
            # ===================== END: CORRECTED BLOCK =====================

            # Update the loser's chips, table chips, and side chips
            self.dealer.update_player_chips(loser_index, -1)
            print(f"Updated player chips for {loser.player_name}: {loser.player_chips}")
            self.table_chips += 1  # Add the losing player's chip to the table chips
            self.update_table_chip_label(
                self.table_chips
            )  # Update the table chip label

            # Handle player with no chips (THIS LOGIC IS UNCHANGED)
            if loser.player_chips <= 0:
                # Condition 1: Player is removed if side_chips_label is no longer visible
                if not self.side_chip_label.isVisible():
                    print(
                        f"Player {loser.player_name} has no chips left and no side chips available. Removing player."
                    )
                    self.remove_player_from_game(loser)
                    return  # Exit after removing the player to avoid further checks

                # Condition 2 & 3: Player is removed when they decline the last side chip
                choice = self.ask_loser_to_take_side_chip(loser)
                if choice == "Yes":
                    self.dealer.update_side_chips(-1, self)  # Decrease side chips by 1
                    self.dealer.update_player_chips(
                        loser_index, 1
                    )  # Add 1 chip to the loser's player chips
                    print(
                        f"{loser.player_name} took the last side chip. Player chips now: {loser.player_chips}"
                    )
                    # Remove the side chip label if side chips are depleted
                    if self.dealer.side_chips == 0:  # Check the actual value
                        self.remove_side_chip_label()
                else:
                    print(f"{loser.player_name} declined the last side chip.")
                    self.remove_player_from_game(loser)

            # Clear any QMessage or reset state to avoid duplication in the next hand
            self.clear_previous_qmessage()

            # Check if the game should continue
            self.dealer.check_for_game_continuation()

        except Exception as e:
            print(f"An error occurred in end_hand: {e}")
            import traceback

            traceback.print_exc()

    def clear_previous_qmessage(self):
        """
        Clears any QMessage or resets its state to ensure it doesn't appear twice.
        """
        # Add the logic here to reset QMessage or clear its content.
        # This might depend on how the QMessage is being implemented in the UI.
        pass

    def update_side_chip_label(self):
        """Update the side chips label in the GameWindow."""
        if hasattr(self, "side_chip_label"):
            self.side_chip_label.setText(f"Side Chips: {self.dealer.side_chips}")
            print(f"Updated side chip label to {self.dealer.side_chips}")

    def remove_side_chip_label(self):
        """Hides the side_chip_label from the GUI when no side chips are left."""
        if hasattr(self, "side_chip_label"):
            self.side_chip_label.hide()
            print("Side chip label removed from the GUI.")

    def ask_loser_to_take_side_chip(self, loser):
        """Prompts the loser to decide if they want to take the last side chip."""
        choice = QMessageBox.question(
            self,
            "Take Side Chip?",
            f"{loser.player_name}, would you like to take the last side chip?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return "Yes" if choice == QMessageBox.Yes else "No"

    # In GameWindow class, replace the old method with this one
    def remove_player_from_game(self, loser_window):
        """Handles removing a player from the game logically and visually."""
        print(f"Removing {loser_window.player_name} from the game.")

        # --- FIX: Correct order of operations ---
        # 1. Update the status to 'Out'. This will turn the circle red.
        self.update_player_status(loser_window, "Out")

        # 2. Close the player's window to remove it from the screen.
        loser_window.close()

        # 3. Mark the player as having 0 chips to make them inactive for game logic.
        #    (This is already done by the dealer, but we ensure it here).
        loser_window.player_chips = 0

        # NOTE: We NO LONGER remove the player from self.player_windows.
        # They stay in the list forever but with an 'Out' status.
        # This fixes the "player not found" error and keeps the UI consistent.
        # self.player_windows.remove(loser)  <-- DO NOT DO THIS

        # Now, check if the game should continue or end.
        self.dealer.check_for_game_continuation()

    def update_player_list(self):
        """Updates the player list in the GUI with player names and status indicators."""
        self.player_list_widget.clear()  # Clear the list widget

        for i, window in enumerate(self.player_windows):
            # Get the player's chip count
            player_chips = (
                window.player_chips
            )  # Assuming you have this attribute in PlayerWindow

            # Create a list item with the player name, chip count, and status
            item_text = f"{window.player_name} - Chips: {player_chips} - {self.player_statuses[i]}"
            item = QListWidgetItem(item_text)

            # Set the appropriate status icon
            icon = QIcon()
            if self.player_statuses[i] == "Active":
                icon.addPixmap(QPixmap("graphics/green_circle.png"))
            elif self.player_statuses[i] == "Folded":
                icon.addPixmap(QPixmap("graphics/red_circle.png"))
            elif self.player_statuses[i] == "Out":
                icon.addPixmap(QPixmap("graphics/gray_circle.png"))

            item.setIcon(icon)
            self.player_list_widget.addItem(item)

        # Ensure the player list is raised to the front
        # self.player_list_widget.raise_()  # Bring the player list to the front

    def update_player_status(self, player_window, status):
        """Updates the status of a player and refreshes the player list UI."""
        try:
            # Find the original index of the player, which is constant
            player_index = player_window.player_index
            if 0 <= player_index < len(self.player_statuses):
                print(f"Updating status for {player_window.player_name} to '{status}'")
                self.player_statuses[player_index] = status
                self.update_player_list()  # Refresh the UI to show the change
            else:
                print(f"Error: Could not find index for {player_window.player_name}")
        except Exception as e:
            print(f"Error in update_player_status: {e}")

    def update_table_chip_label(self, table_chips=None):
        """Updates the table chip label in the GameWindow."""
        if table_chips is not None:
            self.table_chips = table_chips
        self.table_chip_label.setText(f"Table Chips: {self.table_chips}")

    # END =======================

    def next_hand(self):
        print("next_hand method called")
        try:
            print("next_hand: RESETTING COUNTERS")
            self.call_button_clicked = False
            self.turns_after_call = 0
            self.consecutive_passes = 0

            # --- FIX: Make sure all Reveal buttons are visible at the start of a hand ---
            for window in self.player_windows:
                if window.reveal_button.isHidden():
                    window.reveal_button.show()
            # --- END OF FIX ---

            # --- NEW, CORRECTED STARTING PLAYER LOGIC ---
            # The rule: The next hand is started by the next player in the original sequence.

            # We start our search from the player number who started the LAST hand.
            search_start_number = self.hand_starter_number

            # This loop will start checking from the player AFTER the last starter.
            starter_window = self.get_next_active_player(search_start_number)

            # If no one is found (which means only one active player is left), end the game.
            if not starter_window:
                print("next_hand: No other active players found. Ending game.")
                self.dealer.check_for_game_continuation()
                return

            # We found the starter! Update the game state for the new hand.
            self.current_player_number = starter_window.player_number
            self.hand_starter_number = (
                self.current_player_number
            )  # Remember who started THIS hand for the next rotation.
            print(f"--- NEW HAND --- Player {self.current_player_number} will start.")
            # --- END OF CORRECTED LOGIC ---

            # (Card dealing logic)
            active_player_count = len(
                [s for s in self.player_statuses if s == "Active"]
            )
            required_cards = (active_player_count * 5) + 5
            if len(self.deck.cards) < required_cards:
                self.deck = Deck()
                self.deck.update_wild_card(self.table_chips)
                self.deck.shuffle()

            self.all_reveal_cards = self.deck.deal(5)
            self.all_player_cards = [self.deck.deal(5) for _ in range(self.num_players)]

            for i, player_window in enumerate(self.player_windows):
                player_window.player_dragwidget.clear()
                player_window.reveal_dragwidget.clear()

                if self.player_statuses[player_window.player_index] == "Active":
                    print(
                        f"Dealing cards to active player: {player_window.player_name}"
                    )
                    player_window.add_cards_to_widget(
                        player_window.reveal_dragwidget,
                        self.all_reveal_cards,
                        reveal=True,
                    )
                    player_window.add_cards_to_widget(
                        player_window.player_dragwidget,
                        self.all_player_cards[i],
                        reveal=False,
                    )

            # Set button states for all players based on the new current player
            for window in self.player_windows:
                window.set_initial_button_states(
                    self.current_player_number, self.call_button_clicked
                )

        except Exception as e:
            logging.error(f"An error occurred in next_hand: {e}")
            import traceback

            traceback.print_exc()

    def final_end_game(self):
        """Finds the last active player and declares them the winner."""

        # --- NEW, RELIABLE LOGIC ---
        # Find all players who are still marked as 'Active'
        active_players = []
        for i, status in enumerate(self.player_statuses):
            if status == "Active":
                active_players.append(self.player_windows[i])
        # --- END OF NEW LOGIC ---

        if len(active_players) == 1:
            final_winner = active_players[0]
            print(
                f"Game Over. The final winner is {final_winner.player_name} with {final_winner.player_chips} chips."
            )
            QMessageBox.information(
                self,
                "Game Over",
                f"Game Over! The final winner is {final_winner.player_name} with {final_winner.player_chips} chips.",
            )
            self.close()  # Close the main game window
        else:
            # This message will now only appear if there is a genuine logic error.
            print(
                f"Final end game called with {len(active_players)} active players remaining, which should not happen."
            )

    def closeEvent(self, event):
        self.final_end_game()

    def only_one_player_with_chips(self):
        players_with_chips = [
            player for player in self.player_windows if player.player_chips > 0
        ]
        return len(players_with_chips) == 1

    def alert_next_hand(self):
        logging.debug("Starting alert_next_hand method")
        try:
            # Iterate through player windows to get their card information
            alert_message = "Player cards:\n\n"
            for player_window in self.player_windows:
                player_name = player_window.player_name
                player_cards = player_window.get_card_details()
                alert_message += f"{player_name}: {player_cards}\n"

            # Show a QMessageBox with the player card details
            response = QMessageBox.question(
                self,
                "Next Hand",
                alert_message + "\nDo you want to continue to the next hand?",
                QMessageBox.Yes | QMessageBox.No,
            )

            # Continue to next hand if the player selects Yes
            if response == QMessageBox.Yes:
                self.next_hand()
            else:
                self.close()
                print("Game stopped by the user.")

        except Exception as e:
            logging.error(f"An error occurred in alert_next_hand: {e}")
            import traceback

            traceback.print_exc()

        logging.debug("alert_next_hand method completed successfully")

    def declare_final_winner(self):
        winner = next(player for player in self.player_windows if player.chips > 0)
        QMessageBox.information(
            self,
            "Game Over",
            f"The winner is {winner.player_name} with {winner.chips} chips!",
        )

    def update_table_chip_label(self, table_chips=None):
        if table_chips is not None:
            self.table_chips = table_chips
        self.table_chip_label.setText(f"Table Chips: {self.table_chips}")

    def update_player_chips_label(self, player_index, chips):
        # print(f"Updating player chips label for player index: {player_index} with chips: {chips}")
        if 0 <= player_index < len(self.player_windows):
            self.player_windows[player_index].update_chips_label(chips)
        else:
            print(f"Invalid player index: {player_index} for updating chips label.")

    def determine_loser_index(self, loser_window):
        for index, window in enumerate(self.player_windows):
            if window == loser_window:
                return index
        return None

    def set_current_player(self, player_number):
        self.current_player_number = player_number

    def get_current_player_window(self):
        for player_window in self.player_windows:
            if player_window.player_number == self.current_player_number:
                return player_window
        return None

    def end_current_player_turn(self):
        current_player_window = self.get_current_player_window()
        if current_player_window:
            # The PlayerWindow's own method will handle disabling its buttons.
            # It will then call get_next_active_player and set the next turn.
            current_player_window.end_current_player_turn()

    def set_next_player_button_states(self, next_player_window):
        try:
            # Enable all buttons for the next player
            next_player_window.reveal_button.setEnabled(True)
            next_player_window.reveal_button.setStyleSheet("background-color: green;")
            next_player_window.call_button.setEnabled(True)
            next_player_window.call_button.setStyleSheet("background-color: green;")
            next_player_window.pass_button.setEnabled(True)
            next_player_window.pass_button.setStyleSheet("background-color: green;")

            # Disable the exchange button if the reveal button is visible
            if not next_player_window.reveal_button.isHidden():
                next_player_window.exchange_button.setEnabled(False)
                next_player_window.exchange_button.setStyleSheet(
                    "background-color: red;"
                )
            else:
                next_player_window.exchange_button.setEnabled(True)
                next_player_window.exchange_button.setStyleSheet(
                    "background-color: green;"
                )

            print(
                f"Player {next_player_window.player_number}: All buttons enabled (green)"
            )

            # Disable all buttons for all players except the next player
            for player_window in self.player_windows:
                if player_window.player_number != next_player_window.player_number:
                    player_window.reveal_button.setEnabled(False)
                    player_window.reveal_button.setStyleSheet("background-color: red;")
                    player_window.exchange_button.setEnabled(False)
                    player_window.exchange_button.setStyleSheet(
                        "background-color: red;"
                    )
                    player_window.call_button.setEnabled(False)
                    player_window.call_button.setStyleSheet("background-color: red;")
                    player_window.pass_button.setEnabled(False)
                    player_window.pass_button.setStyleSheet("background-color: red;")
                    print(
                        f"Player {player_window.player_number}: All buttons disabled (red)"
                    )

            # Update the current player's number to the next player's number
            self.current_player_number = next_player_window.player_number
            logging.debug(f"Current player number set to {self.current_player_number}")

        except Exception as e:
            print(f"An error occurred in set_next_player_button_states: {e}")
            traceback.print_exc()

    def get_next_active_player(self, current_player_number):
        """
        Finds the next active player in sequence, starting from the player
        AFTER the current_player_number.
        """
        num_players = len(self.player_windows)
        if num_players == 0:
            return None

        # Find the index of the current player
        try:
            start_index = [p.player_number for p in self.player_windows].index(
                current_player_number
            )
        except ValueError:
            return None  # Current player not found

        # Loop starting from the next player, wrapping around if necessary
        for i in range(1, num_players + 1):
            next_index = (start_index + i) % num_players
            next_player = self.player_windows[next_index]

            # Check the player's status using their original index
            if self.player_statuses[next_player.player_index] == "Active":
                print(
                    f"get_next_active_player: Found next active player: {next_player.player_name}"
                )
                return next_player

        print("get_next_active_player: Could not find any other active player.")
        return None

    def update_all_cards(self, all_reveal_cards, all_player_cards):
        for i, player_window in enumerate(self.player_windows):
            for card in all_reveal_cards[i]:
                player_window.add_card(card, player_dragwidget=False)
            for card in all_player_cards[i]:
                player_window.add_card(card, player_dragwidget=True)

    def copy_reveal_dragwidget(self, source_dragwidget):
        new_dragwidget = DragWidget(
            parent=None,
            max_items=source_dragwidget.max_items,
            min_items=source_dragwidget.min_items,
        )
        for item in source_dragwidget.items:
            new_dragwidget.add_item(item)
        return new_dragwidget

    def remove_card_from_all_reveal_dragwidgets(self, card, player_dragwidget):
        for reveal_dragwidget in self.reveal_dragwidgets:
            for item in reveal_dragwidget.findChildren(CardWidget):
                if item.card == card:
                    reveal_dragwidget.remove_item(item)
                    # print(f"1639- Removed {card} from {reveal_dragwidget}.")
                    # print(f"1640- Removed {card} from {self}.")
                    if (
                        player_dragwidget.drag_type == "player_cards"
                        and player_dragwidget.drag_item == item
                    ):
                        player_dragwidget.drag_type = None
                        player_dragwidget.drag_item = (
                            None  # reset the drag_item attribute
                        )

    def add_card_to_all_reveal_dragwidgets(self, card, exclude_widget=None):
        for reveal_dragwidget in self.reveal_dragwidgets:
            if reveal_dragwidget is not exclude_widget:
                if len(reveal_dragwidget.items) < reveal_dragwidget.maximum_cards():
                    card_label = CardWidget(
                        card, reveal_dragwidget, reveal_dragwidget, face_down=False
                    )  # Ensure face_down=False
                    reveal_dragwidget.add_item(card_label)
                else:
                    pass

    def print_all_cards(self):
        for player_window in self.player_windows:
            print(f"Player {player_window.player_number + 1} Reveal CardWidget:")
            for card in player_window.reveal_dragwidget.items:
                print(card.card.value, card.card.suit)
            print(f"Player {player_window.player_number + 1} Player CardWidget:")
            for card in player_window.player_dragwidget.items:
                print(card.card.value, card.card.suit)


class PlayerNamesDialog(QDialog):
    def __init__(self, num_players, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Player Names")
        self.player_names = []
        self.layout = QVBoxLayout(self)

        self.inputs = []
        for i in range(num_players):
            h_layout = QHBoxLayout()
            label = QLabel(f"Player {i + 1} Name:")
            line_edit = QLineEdit()
            h_layout.addWidget(label)
            h_layout.addWidget(line_edit)
            self.layout.addLayout(h_layout)
            self.inputs.append(line_edit)

        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        self.layout.addLayout(button_layout)

    def accept(self):
        self.player_names = [
            input.text() if input.text().strip() else f"GoPlayer {i + 1}"
            for i, input in enumerate(self.inputs)
        ]
        super().accept()
