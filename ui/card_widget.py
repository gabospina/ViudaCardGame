import json
import logging
from PyQt5.QtWidgets import QApplication, QLabel, QSizePolicy
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QPixmap, QDrag
from core.card import Card


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

    def mouseMoveEvent(self, e):
        # print(f"mouseMoveEvent on card: {self.card.value}{self.card.suit}")
        if not self.face_down:
            if e.buttons() != Qt.LeftButton:
                return
            if not self.drag_start_position:
                self.drag_start_position = e.pos()
                return
            if (
                e.pos() - self.drag_start_position
            ).manhattanLength() < QApplication.startDragDistance():
                return

            drag = QDrag(self)
            mime = QMimeData()
            card_data = {"value": self.card.value, "suit": self.card.suit}
            mime.setText(json.dumps(card_data))
            drag.setMimeData(mime)

            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drop_action = drag.exec_(Qt.MoveAction)

            if drop_action == Qt.MoveAction:
                self.handle_card_movement()

            self.drag_start_position = None
            self.parent().drag_item = self
        else:
            e.ignore()  # Ignore the event if conditions are not met

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
        parent_widget = self.parent()
        print(
            f"Handling card movement for {self.card.value}{self.card.suit} from {parent_widget}."
        )
        current_player = parent_widget.parent_window.is_current_player_turn()

        # Allow card movement only if the correct buttons are enabled (allow flexibility with certain buttons being red)
        if not (
            parent_widget.parent_window.reveal_button.isEnabled()
            or parent_widget.parent_window.exchange_button.isEnabled()
            or parent_widget.parent_window.pass_button.isEnabled()
        ):
            print(
                "handle_card_movement - Cannot move cards when required buttons are disabled."
            )
            return

        # Handle movement from reveal_dragwidget to player_dragwidget
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
        # Handle movement from player_dragwidget to reveal_dragwidget
        elif parent_widget == self.player_dragwidget:
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
                parent_widget.parent_window.end_current_player_turn()

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

    # In CardWidget class (ui/card_widget.py)
    def handle_card_movement(self):
        parent_widget = self.parent()
        print(
            f"Handling card movement for {self.card.value}{self.card.suit} from {parent_widget}."
        )
        current_player = parent_widget.parent_window.is_current_player_turn()

        if not (
            parent_widget.parent_window.reveal_button.isEnabled()
            or parent_widget.parent_window.exchange_button.isEnabled()
            or parent_widget.parent_window.pass_button.isEnabled()
        ):
            print(
                "handle_card_movement - Cannot move cards when required buttons are disabled."
            )
            return

        if parent_widget == self.reveal_dragwidget:
            # ... (logic for moving from reveal to player is the same) ...
            pass
        elif parent_widget == self.player_dragwidget:
            if (
                len(self.reveal_dragwidget.items)
                < self.reveal_dragwidget.maximum_cards()
            ):
                # --- ADD THIS LINE ---
                self.parent_window.main_window.consecutive_passes = 0
                # ---------------------

                print(
                    f"Moving card {self.card.value}{self.card.suit} from player_dragwidget to reveal_dragwidget."
                )
                self.player_dragwidget.remove_item(self)
                self.reveal_dragwidget.add_item(self)
                self.setParent(self.reveal_dragwidget)
                self.show()

                self.parent_window.main_window.add_card_to_all_reveal_dragwidgets(
                    self.card, exclude_widget=self.reveal_dragwidget
                )

                # --- ADD THIS LOGIC BLOCK ---
                if self.parent_window.main_window.call_button_clicked:
                    self.parent_window.main_window.turns_after_call += 1
                # ----------------------------

                parent_widget.parent_window.end_current_player_turn()
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
