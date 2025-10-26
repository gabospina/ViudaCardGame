import json
import logging
from PyQt5.QtWidgets import QApplication, QLabel, QSizePolicy
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QPixmap, QDrag
from core.card import Card
from ui.drag_widget import DragWidget


class CardWidget(QLabel):
    def __init__(
        self,
        card,
        player_dragwidget,
        reveal_dragwidget,
        parent_window=None,
        parent=None,
        face_down=False,
    ):
        super().__init__(parent)
        # logging.info(
        #     f"Initializing card {card.value}{card.suit} with parent {parent}, parent_window: {parent_window}"
        # )
        # logging.debug(
        #     f"Card initialized: {card.value}{card.suit}, face_down={face_down}"
        # )
        self.setAcceptDrops(True)
        self.card = card
        self.player_dragwidget = player_dragwidget
        self.reveal_dragwidget = reveal_dragwidget
        self.parent_window = parent_window
        self.face_down = face_down

        if face_down:
            self.card.set_face_down()
        else:
            self.card.set_face_up()

        # self.drag_start_position = QPoint()
        self.drag_start_position = None
        self.init_ui()
        self.drag_type = None

        self.update_card_image()

        # logging.info(
        #     f"Widget relationships: parent_dragwidget={self.player_dragwidget}, reveal_dragwidget={self.reveal_dragwidget}, parent_window={self.parent_window}"
        # )

    def set_face_down(self):
        self.card.set_face_down()
        self.setPixmap(self.card.get_pixmap())

    def set_face_up(self):
        self.card.set_face_up()
        self.setPixmap(self.card.get_pixmap())

    def flip_card(self):
        if self.card.face_up:
            self.set_face_down()
        else:
            self.set_face_up()

    def update_card_image(self):
        pixmap = self.card.get_pixmap().scaled(
            50, 80, Qt.AspectRatioMode.KeepAspectRatio
        )
        self.setPixmap(pixmap)

    def __eq__(self, other):
        if isinstance(other, CardWidget):
            return (
                self.card.value == other.card.value
                and self.card.suit == other.card.suit
            )
        return False

    def mousePressEvent(self, e):
        # print(f"mousePressEvent on card: {self.card.value}{self.card.suit}")
        if not self.face_down:
            if e.buttons() == Qt.LeftButton:
                self.drag_start_position = e.pos()
        else:
            e.ignore()  # Ignore the event if conditions are not met

    # In CardWidget class (ui/card_widget.py)

    def mouseMoveEvent1(self, e):
        if self.face_down or e.buttons() != Qt.LeftButton:
            return

        # --- NEW TURN CHECK LOGIC ---
        source_widget = self.parent()
        # If the card is in the reveal area, only the current player can drag it.
        if source_widget == self.parent_window.reveal_dragwidget:
            if not self.parent_window.is_current_player_turn():
                print("Drag ignored: Not the current player's turn.")
                return  # Stop the drag from starting
        # --- END OF NEW LOGIC ---

        if (
            not self.drag_start_position
            or (e.pos() - self.drag_start_position).manhattanLength()
            < QApplication.startDragDistance()
        ):
            return

        drag = QDrag(self)
        mime = QMimeData()
        card_data = {
            "value": self.card.value,
            "suit": self.card.suit,
            "source_name": source_widget.objectName(),
        }
        mime.setText(json.dumps(card_data))
        drag.setMimeData(mime)
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        drag.setPixmap(pixmap)

        if isinstance(source_widget, DragWidget):
            source_widget.drag_item = self

        # --- MODIFIED LOGIC ---
        # Execute the drag and check if the drop was successful
        drop_action = drag.exec_(Qt.MoveAction)

        # Only call handle_card_movement if the card was actually moved to a NEW widget.
        # The new parent will be different from the source widget.
        if drop_action == Qt.MoveAction and self.parent() != source_widget:
            self.handle_card_movement()
        else:
            print(
                "Drag was either cancelled or was an internal rearrangement. No game logic triggered."
            )
        # --- END OF MODIFICATION ---

    # In CardWidget class (ui/card_widget.py)
    def mouseMoveEvent2(self, e):
        if self.face_down or e.buttons() != Qt.LeftButton:
            return

        source_widget = self.parent()
        if source_widget == self.parent_window.reveal_dragwidget:
            if not self.parent_window.is_current_player_turn():
                print("Drag ignored: Not the current player's turn.")
                return

        if (
            not self.drag_start_position
            or (e.pos() - self.drag_start_position).manhattanLength()
            < QApplication.startDragDistance()
        ):
            return

        drag = QDrag(self)
        mime = QMimeData()
        card_data = {
            "value": self.card.value,
            "suit": self.card.suit,
            "source_name": source_widget.objectName(),
        }
        mime.setText(json.dumps(card_data))
        drag.setMimeData(mime)
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        drag.setPixmap(pixmap)

        # Store a reference to this card widget on its parent.
        # This is CRITICAL for the dropEvent to find the original widget.
        if isinstance(source_widget, DragWidget):
            source_widget.drag_item = self

        # --- FIX: REMOVED LOGIC FROM HERE ---
        # We only execute the drag. The dropEvent is now solely responsible
        # for calling handle_card_movement.
        drag.exec_(Qt.MoveAction)
        # --- END OF FIX ---

    # In CardWidget class
    def mouseMoveEvent(self, e):
        if self.face_down or e.buttons() != Qt.LeftButton:
            return

        source_widget = self.parent()
        if source_widget == self.parent_window.reveal_dragwidget:
            if not self.parent_window.is_current_player_turn():
                print("Drag ignored: Not the current player's turn.")
                return

        if (
            not self.drag_start_position
            or (e.pos() - self.drag_start_position).manhattanLength()
            < QApplication.startDragDistance()
        ):
            return

        drag = QDrag(self)
        mime = QMimeData()
        card_data = {
            "value": self.card.value,
            "suit": self.card.suit,
            "source_name": source_widget.objectName(),
        }
        mime.setText(json.dumps(card_data))
        drag.setMimeData(mime)
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        drag.setPixmap(pixmap)

        if isinstance(source_widget, DragWidget):
            source_widget.drag_item = self

        # Simple execution. The logic is now entirely in dropEvent.
        drag.exec_(Qt.MoveAction)

    def handle_card_movementOriginal(self):
        parent_widget = self.parent()
        print(
            f"Handling card movement for {self.card.value}{self.card.suit} from {parent_widget}."
        )
        current_player = parent_widget.parent_window.is_current_player_turn()

        # Check if all player's buttons are disabled and red
        if not parent_widget.parent_window.is_action_allowed():
            print(
                "handle_card_movement - Cannot move cards when buttons are disabled and red."
            )
            return

        if parent_widget == self.reveal_dragwidget:
            if current_player and not self.face_down:
                if (
                    len(self.player_dragwidget.items)
                    < self.player_dragwidget.maximum_cards()
                ):
                    print(
                        f"Removing {self.card.value}{self.card.suit} from reveal_dragwidget."
                    )
                    self.reveal_dragwidget.remove_item(self)
                    print(
                        f"Adding {self.card.value}{self.card.suit} to player_dragwidget."
                    )
                    self.player_dragwidget.add_item(self)
                    self.setParent(self.player_dragwidget)
                    self.show()  # Ensure the widget is visible
                    print(
                        f"Removing {self.card.value}{self.card.suit} from all reveal_dragwidgets."
                    )
                    parent_widget.parent_window.main_window.remove_card_from_all_reveal_dragwidgets(
                        self.card, self.player_dragwidget
                    )
                    print(
                        f"Moved {self.card.value}{self.card.suit} from reveal_dragwidget to player_dragwidget"
                    )
                else:
                    print(
                        f"Cannot move {self.card.value}{self.card.suit} to player_dragwidget. Maximum cards limit reached."
                    )
            else:
                print(
                    f"Cannot move {self.card.value}{self.card.suit} to player_dragwidget. Not current player's turn or card is face down."
                )
        elif parent_widget == self.player_dragwidget:
            # Allow rearrangement within player_dragwidget at all times
            if (
                len(self.reveal_dragwidget.items)
                < self.reveal_dragwidget.maximum_cards()
            ):
                print(
                    f"Moving card {self.card.value}{self.card.suit} from player_dragwidget to reveal_dragwidget."
                )
                self.player_dragwidget.remove_item(self)
                self.reveal_dragwidget.add_item(self)
                self.setParent(self.reveal_dragwidget)
                self.show()  # Ensure the widget is visible
                print(
                    f"Adding {self.card.value}{self.card.suit} to all reveal_dragwidgets."
                )
                parent_widget.parent_window.main_window.add_card_to_all_reveal_dragwidgets(
                    self.card, exclude_widget=self.reveal_dragwidget
                )
                # Call end_current_player_turn after the move
                self.parent_window.end_current_player_turn()

                print(
                    f"Moved {self.card.value}{self.card.suit} from player_dragwidget to reveal_dragwidget"
                )
            else:
                print(
                    f"Cannot move {self.card.value}{self.card.suit} to reveal_dragwidget. Maximum cards limit reached."
                )
        else:
            print(
                f"Unknown parent widget for card {self.card.value}{self.card.suit}, defaulting to player_cards"
            )

    def handle_card_movement1(self):
        """
        This method is now ONLY for game logic AFTER a card has been successfully moved.
        It determines if the turn should end.
        """
        # The parent() is now the NEW widget the card lives in.
        new_parent_widget = self.parent()
        if not isinstance(new_parent_widget, DragWidget):
            return

        # Check if a card was moved from the player's hand to the reveal area
        # We identify this because the player's reveal_dragwidget is the new parent.
        if new_parent_widget == self.parent_window.reveal_dragwidget:
            print("Card moved to reveal area. Ending turn.")

            # This is the action that ends the turn.
            self.parent_window.main_window.consecutive_passes = 0
            if self.parent_window.main_window.call_button_clicked:
                self.parent_window.main_window.turns_after_call += 1

            # Propagate the card to other players' views
            self.parent_window.main_window.add_card_to_all_reveal_dragwidgets(
                self.card, exclude_widget=self.parent_window.reveal_dragwidget
            )

            self.parent_window.end_current_player_turn()

        # Check if a card was moved from the reveal area to the player's hand
        elif new_parent_widget == self.parent_window.player_dragwidget:
            print("Card taken from reveal area. Player must now return a card.")

            # Remove this card from all other players' reveal widgets
            self.parent_window.main_window.remove_card_from_all_reveal_dragwidgets(
                self.card, self.parent_window.player_dragwidget
            )
            # The turn does NOT end here. The player must now make another move.

    # In CardWidget class (ui/card_widget.py)

    def handle_card_movement(self):
        # --- ADD THIS GUARD ---
        if not self.parent_window.main_window.hand_in_progress:
            print("Card movement ignored: Hand not in progress.")
            return
        # -----------------------

        """
        Handles game logic AFTER a card has been successfully moved.
        It determines if the turn should end, enforcing the 5-card hand rule.
        """
        new_parent_widget = self.parent()
        if not isinstance(new_parent_widget, DragWidget):
            return

        # Check if a card was moved from the player's hand to the reveal area
        if new_parent_widget == self.parent_window.reveal_dragwidget:
            # --- NEW RULE CHECK ---
            # How many cards are left in the player's hand?
            player_hand_count = len(self.parent_window.player_dragwidget.items)

            if player_hand_count != 5:
                print(
                    f"Turn NOT ended. Player must have 5 cards, but has {player_hand_count}."
                )
                # The turn does not end. The player is now in a state where they must
                # take a card from the reveal area to get back to 5.
                return
            # --- END OF NEW RULE ---

            # If the check passes (player has 5 cards), then end the turn.
            print(
                f"Card moved to reveal area. Player has {player_hand_count} cards. Ending turn."
            )
            self.parent_window.main_window.consecutive_passes = 0
            if self.parent_window.main_window.call_button_clicked:
                self.parent_window.main_window.turns_after_call += 1

            self.parent_window.main_window.add_card_to_all_reveal_dragwidgets(
                self.card, exclude_widget=self.parent_window.reveal_dragwidget
            )

            self.parent_window.end_current_player_turn()

        # Check if a card was moved from the reveal area to the player's hand
        elif new_parent_widget == self.parent_window.player_dragwidget:
            print("Card taken from reveal area. Player must now return a card.")
            self.parent_window.main_window.remove_card_from_all_reveal_dragwidgets(
                self.card, self.parent_window.player_dragwidget
            )
            # The turn correctly does NOT end here.

    def print_card_movement_info(self):
        print(f"Added Dropped Card: {self.card.value}{self.card.suit}")
        current_items = [
            f"{card.card.value}{card.card.suit}"
            for card in self.player_dragwidget.findChildren(CardWidget)
        ]
        print(f"Current Items in player_dragwidget: {current_items}")

    def init_ui(self):
        # UI initialization for CardWidget
        self.setPixmap(self.card.get_pixmap().scaled(50, 80, Qt.KeepAspectRatio))
        self.setFixedSize(50, 80)  # Adjust size as needed
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setScaledContents(True)

    def set_data(self, card):
        self.card = card
        self.setPixmap(self.card.pixmap)
