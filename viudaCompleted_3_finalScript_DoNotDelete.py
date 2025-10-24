from core.dealer import Dealer
import logging
from core.card import Card, Deck
import os
import sys
import json
from collections import namedtuple, Counter
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QWidget,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QDockWidget,
    QMainWindow,
    QPushButton,
    QInputDialog,
    QMessageBox,
    QDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QSplitter,
)
from PyQt5.QtCore import Qt, QMimeData, pyqtSignal, QObject, QTimer
from PyQt5.QtGui import QPixmap, QDrag, QPainter, QPen, QIcon
from collections import namedtuple
import random
import itertools
import pygame
from enum import IntEnum
from enum import Enum, auto
import traceback
import logging
from viuda_card_config import CARD_VALUES, CARD_SUITS, VALUE_DICT
import socket
import threading


class Cards(QLabel):
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
        logging.info(
            f"Initializing card {card.value}{card.suit} with parent {parent}, parent_window: {parent_window}"
        )
        logging.debug(
            f"Card initialized: {card.value}{card.suit}, face_down={face_down}"
        )
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

        logging.info(
            f"Widget relationships: parent_dragwidget={self.player_dragwidget}, reveal_dragwidget={self.reveal_dragwidget}, parent_window={self.parent_window}"
        )

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
        if isinstance(other, Cards):
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

    def handle_card_movement(self):
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

    def print_card_movement_info(self):
        print(f"Added Dropped Card: {self.card.value}{self.card.suit}")
        current_items = [
            f"{card.card.value}{card.card.suit}"
            for card in self.player_dragwidget.findChildren(Cards)
        ]
        print(f"Current Items in player_dragwidget: {current_items}")

    def init_ui(self):
        # UI initialization for Cards
        self.setPixmap(self.card.get_pixmap().scaled(50, 80, Qt.KeepAspectRatio))
        self.setFixedSize(50, 80)  # Adjust size as needed
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setScaledContents(True)

    def set_data(self, card):
        self.card = card
        self.setPixmap(self.card.pixmap)


class DragWidget(QWidget):
    orderChanged = pyqtSignal(list)
    cardDropped = pyqtSignal(dict)

    def __init__(
        self,
        parent_window=None,
        player_dragwidget=None,
        reveal_dragwidget=None,
        reveal_dragwidgets=None,
        parent=None,
        drag_type="player_cards",
        max_items=6,
        min_items=5,
    ):
        super().__init__(parent)
        logging.info(f"Initializing DragWidget with drag_type={drag_type}")
        logging.debug(
            f"DragWidget initialized with drag_type={drag_type}, max_items={max_items}"
        )
        self.parent_window = parent_window
        self.drag_type = drag_type
        self.setAcceptDrops(True)
        self.player_dragwidget = player_dragwidget
        self.reveal_dragwidgets = (
            reveal_dragwidgets if reveal_dragwidgets is not None else []
        )

        self.items = []
        self.cards = []

        self.orientation = Qt.Horizontal
        self.max_items = max_items
        self.min_items = min_items
        self.drag_type = None  # Initialize drag_type attribute
        self.drag_index = None
        self.drag_start_position = None  # Initialize drag start position
        self.layout = (
            QHBoxLayout() if self.orientation == Qt.Horizontal else QVBoxLayout()
        )
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.cards_face_up = False

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            logging.debug(f"Drag entered: {event.mimeData().text()}")
            # print("Drag entered, accepting event.")
            event.acceptProposedAction()
        else:
            logging.debug("Drag entered without valid mimeData")
            # print("Drag entered, ignoring event.")
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.setDropAction(Qt.MoveAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        logging.debug("dropEvent started")
        if event.mimeData().hasText():
            try:
                print(f"Drop event received with data: {event.mimeData().text()}")
                card_data = json.loads(event.mimeData().text())
                card = Card(card_data["value"], card_data["suit"])
                logging.debug(f"Dropping card: {card_data}")

                source_widget = event.source()
                if self == self.parent_window.reveal_dragwidget:
                    print("Handling drop on reveal_dragwidget")
                    self.handle_drop_on_reveal(event, card)
                elif self == self.parent_window.player_dragwidget:
                    print("Handling rearrangement within player_dragwidget")
                    self.rearrange_player_cards(event)
                    # No need to call end_current_player_turn here, as it is handled in handle_card_movement
                    logging.debug(
                        f"Drop successful on widget {self} with card {card_data}"
                    )
            except Exception as e:
                logging.error(f"DropEvent error: {str(e)}")
                event.ignore()

            self.drag_item = None
            event.acceptProposedAction()
        else:
            logging.debug("dropEvent rejected: no valid mimeData")
            event.ignore()

    def handle_drop_on_revealOriginal(self, event, card):
        source_widget = event.source()
        logging.debug(
            f"Handling drop on reveal_dragwidget with card {card.value} of {card.suit}"
        )

        # Check if the drop is allowed based on button states
        if not self.parent_window.is_action_allowed():
            # print("Drop not allowed: Exchange button must be green and reveal button must be hidden.")
            logging.debug(
                "Drop rejected: action not allowed (exchange/reveal button states invalid)."
            )
            event.ignore()
            return

        if any(item.face_down for item in self.items):
            print(
                "Cannot drop cards onto reveal_dragwidget when there are face-down cards."
            )
            event.ignore()
            return

        current_player = self.parent_window.is_current_player_turn()
        if not current_player or not self.parent_window.is_action_allowed():
            print(
                "Cannot drop cards onto reveal_dragwidget when it's not the current player's turn or actions are not allowed."
            )
            event.ignore()
            return

        if source_widget == self:
            print("Rearrangement within reveal_dragwidget is not allowed.")
            event.ignore()
        else:
            # Handle the drop
            print("Handling drop on reveal_dragwidget.")
            # (Your card handling logic here)
            event.acceptProposedAction()

    def handle_drop_on_reveal(self, event, card):
        source_widget = event.source()
        logging.debug(
            f"Handling drop on reveal_dragwidget with card {card.value} of {card.suit}"
        )
        print(
            f"Handling drop on reveal_dragwidget with card {card.value} of {card.suit}"
        )

        # Check if the drop is allowed based on button states, but focus on reveal and pass buttons.
        if not (
            self.parent_window.reveal_button.isEnabled()
            or self.parent_window.pass_button.isEnabled()
        ):
            logging.debug(
                "Drop rejected: action not allowed (reveal/pass button states invalid)."
            )
            event.ignore()
            return

        # Don't allow cards to be dropped when reveal_dragwidget contains face-down cards
        if any(item.face_down for item in self.items):
            print(
                "Cannot drop cards onto reveal_dragwidget when there are face-down cards."
            )
            event.ignore()
            return

        current_player = self.parent_window.is_current_player_turn()
        if not current_player:
            print(
                "Cannot drop cards onto reveal_dragwidget when it's not the current player's turn."
            )
            event.ignore()
            return

        if source_widget == self:
            print("Rearrangement within reveal_dragwidget is not allowed.")
            event.ignore()
        else:
            # Allow the drop if the card movement is allowed
            print("Handling drop on reveal_dragwidget.")
            event.acceptProposedAction()

    def rearrange_player_cards(self, event):
        logging.debug("Attempting to rearrange player cards.")
        print("rearrange_player_cards called")

        try:
            data = event.mimeData().text()
            print(f"Rearrangement data: {data}")
            logging.debug("Rearranging player cards.")
            card_data = json.loads(data)
            logging.debug(f"Dragged card: {card_data}")
            dragged_card = Card(card_data["value"], card_data["suit"])

            dragged_card_index = None
            for i, card in enumerate(self.items):
                logging.debug(f"Card {i}: {card.card.value} of {card.card.suit}")
                if card.card.value == dragged_card.value:
                    dragged_card_index = i
                    break

            if dragged_card_index is None:
                print(
                    "rearrange_player_cards-Error: Dragged card not found in player cards."
                )
                event.ignore()
                return

            drop_index = -1
            for i, widget in enumerate(self.items):
                if event.pos().x() < widget.x() + widget.width() / 2:
                    drop_index = i
                    break
            if drop_index == -1:
                drop_index = len(self.items)

            dragged_card_widget = self.items.pop(dragged_card_index)
            self.layout.removeWidget(dragged_card_widget)
            logging.debug(
                f"Card moved from index {dragged_card_index} to {drop_index}. New card order: {[item.card.value for item in self.items]}"
            )

            new_pos_x = event.pos().x()
            if drop_index < len(self.items):
                new_pos_x = min(new_pos_x, self.items[drop_index].x())

            dragged_card_widget.move(new_pos_x, dragged_card_widget.y())
            self.layout.insertWidget(drop_index, dragged_card_widget)
            self.items.insert(drop_index, dragged_card_widget)

            event.setDropAction(Qt.MoveAction)
            event.accept()
            self.orderChanged.emit(self.get_item_data())
            print("Player cards rearranged successfully")

        except Exception as ex:
            # print(f"Error during player card rearrangement: {ex}")
            logging.error(f"Error during player card rearrangement: {ex}")

    def rearrange_player_cardsB549(self, event):
        logging.debug("Attempting to rearrange player cards.")
        print("Rearranging player cards")

        try:
            data = event.mimeData().text()
            print(f"Rearrangement data: {data}")
            logging.debug("Rearranging player cards.")
            card_data = json.loads(data)
            logging.debug(f"Dragged card: {card_data}")
            dragged_card = Card(card_data["value"], card_data["suit"])

            dragged_card_index = None
            for i, card in enumerate(self.items):
                logging.debug(f"Card {i}: {card.card.value} of {card.card.suit}")
                if card.card.value == dragged_card.value:
                    dragged_card_index = i
                    break

            if dragged_card_index is None:
                print("Error: Dragged card not found in player cards.")
                event.ignore()
                return

            drop_index = self.get_index_at_position(event.pos())
            print(f"Drop index calculated: {drop_index}")

            dragged_card_widget = self.items.pop(dragged_card_index)
            self.layout.removeWidget(dragged_card_widget)
            logging.debug(
                f"Card moved from index {dragged_card_index} to {drop_index}. New card order: {[item.card.value for item in self.items]}"
            )
            self.layout.insertWidget(drop_index, dragged_card_widget)
            self.items.insert(drop_index, dragged_card_widget)

            event.setDropAction(Qt.MoveAction)
            event.accept()
            self.orderChanged.emit(self.get_item_data())
            print("Player cards rearranged successfully")

        except Exception as ex:
            # print(f"Error during player card rearrangement: {ex}")
            logging.error(f"Error during player card rearrangement: {ex}")

    def get_dragged_card_index(self):
        print("317- get_dragged_card_index called")
        for i, card in enumerate(self.player_dragwidget.items):
            if card.isSelected():
                return i
        return None

    def get_index_at_position(self, pos):
        print("324- get_index_at_position called")
        for i in range(len(self.items)):
            item = self.items[i]
            item_pos = self.layout.itemAt(i).widget().pos()
            if pos.x() < item_pos.x() + item.width() // 2:
                return i
        return len(self.items)

    def add_item(self, item):
        if len(self.items) < self.max_items:
            self.items.append(item)
            self.layout.addWidget(item)
            # print(f"add_item dw - Total items: {len(self.items)}")
        else:
            # print(f"Cannot add more items, max limit ({self.max_items}) reached.")
            pass

    def remove_item(self, item):
        if item in self.items:
            self.items.remove(item)
            self.layout.removeWidget(item)
            item.setParent(None)
        else:
            print("Item not found in DragWidget.")

    def add_card(self, card):
        if len(self.cards) < 6:  # Allow up to 6 cards during a drop event
            self.cards.append(card)
            self.update()
            print(f"Card added. Total cards: {len(self.cards)}")  # Log current state
        else:
            print(f"Cannot add more cards, max limit ({self.max_items}) reached.")

    def add_cardB549(self, card):
        if (
            len(self.cards) < self.max_items
        ):  # Adjusted to use self.max_items for consistency
            self.cards.append(card)
            self.update()
            print(f"Card added. Total cards: {len(self.cards)}")  # Log current state
        else:
            print(f"Cannot add more cards, max limit ({self.max_items}) reached.")

    def get_cards(self):
        return self.cards

    def remove_card(self, card):
        for c in self.cards:
            if c.card == card:
                self.cards.remove(c)
                c.setParent(None)
                return True
        return False

    def update_layout(self):
        self.layout.update()

    def get_item_data(self):
        return [card.card for card in self.items]

    def clear(self):
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget is not None:
                self.items.remove(widget)
                widget.setParent(None)

    def minimum_cards(self):
        return self.min_items

    def maximum_cards(self):
        return self.max_items

    def is_rearrange_action(self, event):
        return event.source() == self and self == self.parent_window.player_dragwidget

    def addWidget(self, widget):
        self.layout.addWidget(widget)
        self.items.append(widget)

    def insertWidget(self, index, widget):
        self.layout.insertWidget(index, widget)
        self.items.insert(index, widget)

    # CODE BELOW SEEMS TO BE DOING NOTHING - Chips ADDED BLOCK CODE FROM 18.40 =================

    def set_cards(self, cards):
        self.cards = cards
        self.update()

    def clear_cards(self):
        self.player_dragwidget.clear()
        self.reveal_dragwidget.clear()

    # =================================

    def handle_order_changed(self, item_data):
        print("orderChanged signal received with data:", item_data)
        # Rest of the slot function code


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

        self.player_dragwidget = player_dragwidget  # or DragWidget(parent_window=self)
        self.reveal_dragwidget = reveal_dragwidget  # or DragWidget(parent_window=self)

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

        self.setLayout(layout)

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
        card_widget = Cards(card, parent_window=self)
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
        card_label = Cards(
            card, self.player_dragwidget, self.reveal_dragwidget, parent_window=self
        )
        if player_dragwidget:
            self.player_dragwidget.add_item(card_label)
        else:
            self.reveal_dragwidget.add_item(card_label)
        card_label.setAlignment(Qt.AlignCenter)

    def reveal_cards(self):
        try:
            print("Reveal button clicked")
            self.cards_revealed = True

            # Ensure lists are initialized
            self.reveal_cards = [
                card_label.card for card_label in self.reveal_dragwidget.items
            ]
            self.player_cards = [
                card_label.card for card_label in self.player_dragwidget.items
            ]

            # Clear both drag widgets
            self.player_dragwidget.clear()
            self.reveal_dragwidget.clear()

            # Update the drag widgets with the new cards
            for card in self.player_cards:
                card.set_face_down()
                card_label = Cards(
                    card,
                    self.player_dragwidget,
                    self.reveal_dragwidget,
                    parent_window=self,
                )
                self.reveal_dragwidget.add_item(card_label)

            for card in self.reveal_cards:
                card.set_face_up()
                card.load_image()
                card_label = Cards(
                    card,
                    self.player_dragwidget,
                    self.reveal_dragwidget,
                    parent_window=self,
                )
                self.player_dragwidget.add_item(card_label)

            # Update the card lists with the actual Card objects from the drag widgets
            self.reveal_cards = [
                card_label.card for card_label in self.reveal_dragwidget.items
            ]
            self.player_cards = [
                card_label.card for card_label in self.player_dragwidget.items
            ]

            # Update the reveal button state for all players
            for window in self.main_window.player_windows:
                window.reveal_button_clicked = True

            # Check if the ***** call button was clicked before the reveal button *******
            if (
                self.main_window.call_button_clicked
            ):  # and not self.main_window.call_button_clicked_by_current_player:
                self.main_window.turns_after_call += 1

            # Determine the next player's number
            next_player_number = (
                self.player_number % len(self.main_window.player_windows)
            ) + 1

            for window in self.main_window.player_windows:
                window.reveal_button.hide()
                if window == self:
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

                    self.exchange_button.setEnabled(False)
                    self.exchange_button.setStyleSheet("background-color: red;")
                    self.call_button.setEnabled(False)
                    self.call_button.setStyleSheet("background-color: red;")
                    self.pass_button.setEnabled(False)
                    self.pass_button.setStyleSheet("background-color: red;")
                else:
                    window.reveal_dragwidget.clear()
                    if window.player_number == next_player_number:
                        window.reveal_button.setEnabled(True)
                        window.reveal_button.setStyleSheet("background-color: green;")
                        window.exchange_button.setEnabled(True)
                        window.exchange_button.setStyleSheet("background-color: green;")
                        window.call_button.setEnabled(True)
                        window.call_button.setStyleSheet("background-color: green;")
                        window.pass_button.setEnabled(True)
                        window.pass_button.setStyleSheet("background-color: green;")

                    for card in self.reveal_cards:
                        card_label = Cards(
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

                    if window.player_number not in [
                        self.player_number,
                        next_player_number,
                    ]:
                        window.exchange_button.setEnabled(False)
                        window.exchange_button.setStyleSheet("background-color: red;")
                        window.call_button.setEnabled(False)
                        window.call_button.setStyleSheet("background-color: red;")
                        window.pass_button.setEnabled(False)
                        window.pass_button.setStyleSheet("background-color: red;")

            if self.main_window.call_button_clicked:
                for window in self.main_window.player_windows:
                    if window != self:
                        window.call_button.setEnabled(False)
                        window.call_button.setStyleSheet("background-color: red;")

            for window in self.main_window.player_windows:
                if not window.call_button_clicked:
                    return

            QTimer.singleShot(0, lambda: self.main_window.check_end_hand())
        except Exception as e:
            print(f"An error occurred: {e}")

    def exchange_cards(self):
        try:
            if not self.is_current_player_turn:
                return  # Return early if it's not the current player's turn

            print("Exchange button clicked")

            # Ensure lists are initialized
            self.reveal_cards = [
                card_label.card for card_label in self.reveal_dragwidget.items
            ]
            self.player_cards = [
                card_label.card for card_label in self.player_dragwidget.items
            ]

            # Get initial state of cards
            player_cards_before_exchange = self.player_dragwidget.items.copy()
            reveal_cards_before_exchange = self.reveal_dragwidget.items.copy()

            # Clear both drag widgets
            self.player_dragwidget.clear()
            self.reveal_dragwidget.clear()

            # Swap cards between player_dragwidget and reveal_dragwidget
            for card_label in player_cards_before_exchange:
                self.reveal_dragwidget.addWidget(card_label)

            for card_label in reveal_cards_before_exchange:
                self.player_dragwidget.addWidget(card_label)

            # Update the card lists with the actual Card objects from the drag widgets
            self.reveal_cards = [
                card_label.card for card_label in self.reveal_dragwidget.items
            ]
            self.player_cards = [
                card_label.card for card_label in self.player_dragwidget.items
            ]

            # Highlight wild cards
            for card_label in self.reveal_dragwidget.items:
                card_label.card.highlight_wild_card(card_label, True)
            for card_label in self.player_dragwidget.items:
                card_label.card.highlight_wild_card(
                    card_label, not card_label.card.set_face_down
                )

            # Print the updated cards for debugging
            player_num = self.main_window.player_windows.index(self) + 1

            # Propagate changes to other player windows
            for window in self.main_window.player_windows:
                if window != self:
                    # Clear the reveal_dragwidget of the other player
                    window.reveal_dragwidget.clear()

                    # Update the reveal_dragwidget of the other players with the current player's revealed cards
                    for card in self.reveal_cards:
                        new_card_label = Cards(
                            card,
                            window.player_dragwidget,
                            window.reveal_dragwidget,
                            parent_window=self,
                        )
                        card.set_face_up()
                        new_card_label.setPixmap(
                            card.pixmap.scaled(
                                50, 80, Qt.AspectRatioMode.KeepAspectRatio
                            )
                        )
                        window.reveal_dragwidget.addWidget(new_card_label)

            # Disable the exchange button for the current player
            self.exchange_button.setEnabled(False)
            self.exchange_button.setStyleSheet("background-color: red;")
            self.call_button.setEnabled(False)
            self.call_button.setStyleSheet("background-color: red;")
            self.pass_button.setEnabled(False)
            self.pass_button.setStyleSheet("background-color: red;")

            # Get the index of the current player in the list of all players
            current_player_index = self.main_window.player_windows.index(self)

            # Calculate the index of the next player
            next_player_index = (current_player_index + 1) % len(
                self.main_window.player_windows
            )

            # Get the next player window
            next_player_window = self.main_window.player_windows[next_player_index]

            # Set the button states for the next player
            self.set_next_player_button_states(next_player_window)

            print("Exchange cards completed")

            QTimer.singleShot(0, lambda: self.main_window.check_end_hand())
        except Exception as e:
            print(f"Error in exchange_cards: {e}")

    def pass_cards(self):
        try:
            if (
                self.pass_button.isEnabled()
                and self.pass_button.styleSheet() == "background-color: green;"
            ):
                self.pass_button.setEnabled(False)
                self.pass_button.setStyleSheet("background-color: red;")

                # Disable the call button for all players
                for window in self.main_window.player_windows:
                    window.call_button.setEnabled(False)
                    window.call_button.setStyleSheet("background-color: red;")

                next_player_number = (
                    self.player_number % len(self.main_window.player_windows)
                ) + 1
                print(f"Next player number: {next_player_number}")

                # Check if the call button has been clicked before enabling it for the next player
                if not self.call_button_clicked:
                    self.main_window.player_windows[
                        next_player_number - 1
                    ].call_button.setEnabled(True)
                    self.main_window.player_windows[
                        next_player_number - 1
                    ].call_button.setStyleSheet("background-color: green;")

                for window in self.main_window.player_windows:
                    # print(f"pass_cards Processing window {window.player_number}")
                    if window.player_number == next_player_number:
                        self.set_next_player_button_states(window)
                    else:
                        window.reveal_button.setEnabled(False)
                        window.reveal_button.setStyleSheet("background-color: red;")
                        window.pass_button.setEnabled(False)
                        window.pass_button.setStyleSheet("background-color: red;")
                        window.call_button.setEnabled(False)
                        window.call_button.setStyleSheet("background-color: red;")
                        window.exchange_button.setEnabled(False)
                        window.exchange_button.setStyleSheet("background-color: red;")

                QTimer.singleShot(0, lambda: self.main_window.check_end_hand())
        except Exception as e:
            print(f"An error occurred in pass_cards: {e}")

    def call_cards(self):
        print("\n--- call_cards method started ---")
        print(f"call_cards button clicked by Player {self.player_number}")

        if not self.is_current_player_turn():
            # print(f"Not Player {self.player_number}'s turn. Exiting call_cards method.")
            return

        # Set the calling player number
        self.main_window.calling_player_number = self.player_number

        # Disable call button in all windows and turn them red
        for window in self.main_window.player_windows:
            # print(f"\nProcessing Player {window.player_number}:")
            # print(f"  Disabling call button for Player {window.player_number}")
            window.call_button.setEnabled(False)
            window.call_button.setStyleSheet("background-color: red;")
            # print(f"  Disabling pass button for Player {window.player_number}")
            window.pass_button.setEnabled(False)
            window.pass_button.setStyleSheet("background-color: red;")
            # Ensure exchange button is disabled and red for all players initially
            window.exchange_button.setEnabled(False)
            window.exchange_button.setStyleSheet("background-color: red;")
            # print(
            #     f"  exchange_button state for Player {window.player_number}: Enabled: {window.exchange_button.isEnabled()}, StyleSheet: {window.exchange_button.styleSheet()}")

        # Set a flag to indicate that the call button has been clicked
        self.main_window.call_button_clicked = True
        # print("\ncall_button_clicked flag set to True for all players")

        # Disable all buttons for the current player
        # print(f"\nDisabling buttons for Player {self.player_number} (current player):")
        self.call_button.setEnabled(False)
        self.call_button.setStyleSheet("background-color: red;")
        self.pass_button.setEnabled(False)
        self.pass_button.setStyleSheet("background-color: red;")
        self.exchange_button.setEnabled(False)
        self.exchange_button.setStyleSheet("background-color: red;")
        if hasattr(self, "reveal_button"):
            self.reveal_button.setEnabled(False)
            self.reveal_button.setStyleSheet("background-color: red;")

        # print(
        #     f"  exchange_button state for Player {self.player_number}: Enabled: {self.exchange_button.isEnabled()}, StyleSheet: {self.exchange_button.styleSheet()}")

        # Calculate the next player number
        next_player_number = (
            self.player_number % len(self.main_window.player_windows)
        ) + 1
        print(f"\nNext player number: {next_player_number}")

        # Enable reveal button and pass button for the next player
        next_player_window = self.main_window.player_windows[next_player_number - 1]
        # print(f"\nEnabling reveal button and pass button for Player {next_player_number}:")
        next_player_window.reveal_button.setEnabled(True)
        next_player_window.reveal_button.setStyleSheet("background-color: green;")
        next_player_window.pass_button.setEnabled(True)
        next_player_window.pass_button.setStyleSheet("background-color: green;")

        # Enable exchange button and set it to green for the next player only if the reveal button is hidden
        if next_player_window.reveal_button.isHidden():
            next_player_window.exchange_button.setEnabled(True)
            next_player_window.exchange_button.setStyleSheet("background-color: green;")
        else:
            next_player_window.exchange_button.setEnabled(False)
            next_player_window.exchange_button.setStyleSheet("background-color: red;")

        # print(
        #     f"  exchange_button state for Player {next_player_number}: Enabled: {next_player_window.exchange_button.isEnabled()}, StyleSheet: {next_player_window.exchange_button.styleSheet()}")

        # Disable the call button for the next player
        # print(f"\nDisabling call button for Player {next_player_number}:")
        next_player_window.call_button.setEnabled(False)
        next_player_window.call_button.setStyleSheet("background-color: red;")

        print("\n--- call_cards method completed ---")

        # Schedule the game end check after the next player's turn
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

    def end_current_player_turn(self):
        self.exchange_button.setEnabled(False)
        self.exchange_button.setStyleSheet("background-color: red;")
        self.call_button.setEnabled(False)
        self.call_button.setStyleSheet("background-color: red;")
        self.pass_button.setEnabled(False)
        self.pass_button.setStyleSheet("background-color: red;")

        next_player_number = (
            self.player_number % len(self.main_window.player_windows)
        ) + 1
        next_player_window = next(
            window
            for window in self.main_window.player_windows
            if window.player_number == next_player_number
        )
        self.main_window.set_next_player_button_states(next_player_window)

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

    def add_cards_to_widget(self, widget, cards, reveal):
        try:
            widget.clear()
            for card in cards[:5]:  # Ensure only the first 5 cards are added
                card_label = Cards(
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
        return f"Player Cards: {player_cards}, Reveal Cards: {reveal_cards}"

    def clear_widgets(self):
        try:
            self.player_dragwidget.clear()
            self.reveal_dragwidget.clear()
        except Exception as e:
            print(f"An error occurred in clear_widgets: {e}")

    def clear_widget(self, widget):
        """Remove all items from the given widget."""
        for card in widget.findChildren(Cards):
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
        print(f"1191- Player {self.player_number} Reveal Cards: {reveal_card_strings}")
        print(f"1192- Player {self.player_number} Player Cards: {player_card_strings}")


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


class Hand:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.winner = None
        # self.font = pygame.font.Font(GAME_FONT, 48)
        self.win_rotation_angle = random.uniform(-10, 10)
        self.p1 = Player()
        self.p2 = Player()
        self.flop = Flop()
        self.player_list = [self.p1, self.p2]
        self.dealer = Dealer(self.player_list, self.flop)

    def render_cards1(self):
        # Draw cards at current positions
        for player in self.player_list:
            for card in player.cards:
                self.display_surface.blit(card.card_surf, card.start_position)
        for card in self.flop.cards:
            self.display_surface.blit(card.card_surf, card.position)

    def render_winner1(self):
        # Set the text and color based on the winner and print to screen
        if self.dealer.determined_winner is not None:
            text = ""  # Initialize outside conditional blocks
            text_color = None  # Initialize outside conditional blocks

            # Set the text and color based on the winner
            if self.dealer.determined_winner == "Player 1":
                text = "render_winner Player 1 Wins!"
                text_color = (115, 235, 0)  # Blue
            elif self.dealer.determined_winner == "Player 2":
                text = "render_winner Player 2 Wins!"
                text_color = (135, 206, 235)  # Green
            elif self.dealer.determined_winner == "Tie":
                text = "Split Pot!"
                text_color = (255, 192, 203)  # Pink

            coordinates = (520, 100)
            # Winner text
            text_surface = self.font.render(text, True, text_color)
            text_rect = text_surface.get_rect()
            text_rect.topleft = coordinates
            rotated_surface = pygame.transform.rotate(
                text_surface, self.win_rotation_angle
            )
            rotated_rect = rotated_surface.get_rect(center=text_rect.center)
            self.display_surface.blit(rotated_surface, rotated_rect)

    def update1(self):
        """
        It calls self.dealer.update() which presumably updates the game state (dealing cards, etc.).
        Then it calls self.render_cards() to draw the cards on the screen.
        It calls self.render_winner() to render the winner information (not relevant at this point).
        """
        self.dealer.update()
        self.render_cards()
        self.render_winner()


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
        self.next_player_turn = None

        self.hand_in_progress = False  # Add this flag

        self.init_ui()
        self.init_ui_chips_and_list()

        # Connect signals from Dealer to update GUI
        self.dealer.table_chip_label_updated.connect(self.update_table_chip_label)
        self.dealer.side_chip_label_updated.connect(self.update_side_chip_label)
        self.dealer.player_chips_updated.connect(self.update_player_chips_label)

    def init_ui1ok(self):
        screen_resolution = self.app.desktop().screenGeometry()
        screen_width = screen_resolution.width()
        screen_height = screen_resolution.height()

        window_width = 500
        window_height = 400

        window_offset_x = 50
        window_offset_y = 50

        # Initialize labels
        self.table_chip_label = QLabel(self)
        self.side_chip_label = QLabel(self)

        # Setup labels
        self.update_table_chip_label()
        self.update_side_chip_label()

        # Layout for labels
        layout = QVBoxLayout()
        layout.addWidget(self.table_chip_label)
        layout.addWidget(self.side_chip_label)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

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

            window_x = int((screen_width / self.num_players) * i + window_offset_x)
            window_y = int(screen_height / 2 - window_height / 2 + window_offset_y)

            player_window.setGeometry(window_x, window_y, window_width, window_height)
            player_window.show()

        # Initialize the player list sidebar as a dockable widget
        self.player_list_dock = QDockWidget("Player List", self)
        self.player_list_widget = QListWidget()

        # Populate the player list with names and status indicators
        self.update_player_list()

        # Add the player list to the dock widget and dock it to the left
        self.player_list_dock.setWidget(self.player_list_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.player_list_dock)

    def init_ui2ok(self):
        screen_resolution = self.app.desktop().screenGeometry()
        screen_width = screen_resolution.width()
        screen_height = screen_resolution.height()

        window_width = 500
        window_height = 400

        window_offset_x = 50
        window_offset_y = 50

        # Initialize labels
        self.table_chip_label = QLabel(self)
        self.side_chip_label = QLabel(self)

        # Setup labels
        self.update_table_chip_label()
        self.update_side_chip_label()

        # Create a vertical layout for the chip labels
        chip_layout = QVBoxLayout()
        chip_layout.addWidget(self.table_chip_label)
        chip_layout.addWidget(self.side_chip_label)

        # Create a widget to hold the chip labels
        chip_widget = QWidget()
        chip_widget.setLayout(chip_layout)
        self.setCentralWidget(chip_widget)

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

            window_x = int((screen_width / self.num_players) * i + window_offset_x)
            window_y = int(screen_height / 2 - window_height / 2 + window_offset_y)

            player_window.setGeometry(window_x, window_y, window_width, window_height)
            player_window.show()

        # Initialize the player list sidebar as a dockable widget
        self.player_list_dock = QDockWidget("Player List", self)
        self.player_list_widget = QListWidget()

        # Add the player list to the dock widget
        self.player_list_dock.setWidget(self.player_list_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.player_list_dock)

        # Populate the player list with names and status indicators
        self.update_player_list()

        # Move the main window to the top-left corner (adjusting for the offsets)
        # self.setGeometry(window_offset_x, window_offset_y, window_width, window_height)

    def init_ui_chips_and_list3ok(self):
        """Initialize the UI for chips labels and player list dock."""
        # Set the position for the window containing chips and player list
        window_offset_x = 800  # Move to the left edge
        window_offset_y = 50  # Move to the top edge
        window_width = 150
        window_height = 400

        # Initialize labels for chips
        self.table_chip_label = QLabel(self)
        self.side_chip_label = QLabel(self)

        # Setup labels for chips
        self.update_table_chip_label()
        self.update_side_chip_label()

        # Create a vertical layout for the chip labels
        chip_layout = QVBoxLayout()
        chip_layout.addWidget(self.table_chip_label)
        chip_layout.addWidget(self.side_chip_label)

        # Create a widget to hold the chip labels
        chip_widget = QWidget()
        chip_widget.setLayout(chip_layout)
        self.setCentralWidget(chip_widget)

        # Initialize the player list sidebar as a dockable widget
        self.player_list_dock = QDockWidget("Player List", self)
        self.player_list_widget = QListWidget()

        # Add the player list to the dock widget
        self.player_list_dock.setWidget(self.player_list_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.player_list_dock)

        # Populate the player list with names and status indicators
        self.update_player_list()

        # Move the window containing chip labels and player list to the top-left corner
        self.setGeometry(window_offset_x, window_offset_y, window_width, window_height)

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

    def start_first_hand(self):
        # self.deck = Deck()
        self.deck.shuffle()

        # Update the wild card based on current table chips
        self.deck.update_wild_card(self.table_chips)

        self.all_reveal_cards = self.deck.deal(5)
        self.all_player_cards = [self.deck.deal(5) for _ in range(self.num_players)]

        for player_window in self.player_windows:
            player_window.add_cards_to_widget(
                player_window.reveal_dragwidget, self.all_reveal_cards, reveal=True
            )
            player_window.add_cards_to_widget(
                player_window.player_dragwidget,
                self.all_player_cards[player_window.player_number - 1],
                reveal=False,
            )

            # Set wild card color
            for card_widget in player_window.reveal_dragwidget.children():
                if hasattr(card_widget, "card") and card_widget.card.is_wild:
                    card_widget.setStyleSheet("background-color: red;")

            player_window.set_initial_button_states(
                current_player_number=1, call_button_clicked=False
            )  # Set initial button states

        # self.turns_after_call = 0  # Initialize turns after call

        # Log initial states for debugging
        # logging.debug("1-6 start_first_hand - num_players: {}".format(self.num_players))
        # logging.debug(f"2-6 start_first_hand - player_names: {[window.player_name for window in self.player_windows]}")
        # logging.debug(f"3-6 start_first_hand - all_reveal_cards: {self.all_reveal_cards}")
        # logging.debug(f"4-6 start_first_hand - all_player_cards: {self.all_player_cards}")

        # Determine and highlight the wild card
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

        # logging.debug("6-6 start_first_hand - Setting initial button states for Players")

    def check_end_hand(self):
        try:
            if hasattr(self, "call_button_clicked") and self.call_button_clicked:
                self.turns_after_call += 1
                total_players = len(self.player_windows)
                print(
                    f"check_end_hand - Turns after call: {self.turns_after_call}/{total_players}"
                )
                if self.turns_after_call >= total_players:
                    self.end_hand()
                    return  # Return early to avoid calling next_hand twice

            print("check_end_hand - Hand not finished yet.")
        except Exception as e:
            print(f"An error occurred in check_end_hand: {e}")
            import traceback

            traceback.print_exc()

    # 1 side_chip_label removed =========================

    def end_hand1(self):
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

            # Determine winner and loser
            winner_index, loser_index = self.dealer.determine_winner_and_loser(
                self.player_windows
            )

            if 0 <= loser_index < len(self.player_windows):
                loser = self.player_windows[loser_index]
                print(f"Winner: {self.player_windows[winner_index].player_name}")
                print(f"Loser: {loser.player_name}")
                self.dealer.display_winner(self.player_windows[winner_index])

                # Update the loser's chips, table chips, and side chips
                self.dealer.update_player_chips(loser_index, -1)
                print(
                    f"Updated player chips for {loser.player_name}: {loser.player_chips}"
                )
                self.table_chips += 1  # Add the losing player's chip to the table chips
                self.update_table_chip_label(
                    self.table_chips
                )  # Update the table chip label

                # Handle player with no chips
                if loser.player_chips <= 0:
                    # Condition 1: Player is removed if side_chips_label is no longer visible
                    if not self.side_chip_label.isVisible():
                        print(
                            f"Player {loser.player_name} has no chips left and no side chips available. Removing player."
                        )
                        self.remove_player_from_game(loser)
                        return  # Exit after removing the player to avoid further checks

                    # Condition 2 & 3: Player is removed when they decline the last side chip, even if side_chips_label is still visible
                    choice = self.ask_loser_to_take_side_chip(loser)
                    if choice == "Yes":
                        self.dealer.update_side_chips(
                            -1, self
                        )  # Decrease side chips by 1
                        self.dealer.update_player_chips(
                            loser_index, 1
                        )  # Add 1 chip to the loser's player chips
                        print(
                            f"{loser.player_name} took the last side chip. Player chips now: {loser.player_chips}"
                        )
                        # Remove the side chip label if side chips are depleted
                        if not self.side_chip_label.isVisible():
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

    # In your GameWindow class

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

            # ==================== START: CORRECTED BLOCK ====================
            # Determine winner, loser, and the winner's cards from the dealer
            winning_window, losing_window, winning_cards = (
                self.dealer.determine_winner_and_loser(self.player_windows)
            )

            # Highlight the winning hand's wild cards (UI logic is handled here)
            for card in winning_cards:
                card_label = winning_window.find_card_label(card)
                if card_label:
                    card.highlight_wild_card(card_label, is_face_up=True)

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

    def remove_player_from_game(self, loser):
        """Removes a player from the game if they have no chips left."""
        print(f"Removing {loser.player_name} from the game.")
        self.player_windows.remove(loser)
        self.dealer.player_out(loser)
        # QMessageBox.warning(
        #     self,
        #     "Player Removed",
        #     f"{loser.player_name} has no chips left and will be removed from the game."
        # )

        # Update the player list in the GUI (if applicable)
        self.update_player_list()
        print(f"Updated player list after removing {loser.player_name}.")

    # 1 New GUI =================

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

    def update_player_status(self, player_index, status):
        """Updates the status of a specific player and refreshes the player list."""
        self.player_statuses[player_index] = status
        self.update_player_list()

    def update_table_chip_label(self, table_chips=None):
        """Updates the table chip label in the GameWindow."""
        if table_chips is not None:
            self.table_chips = table_chips
        self.table_chip_label.setText(f"Table Chips: {self.table_chips}")

    # END =======================

    def next_hand(self):
        print("next_hand method called")
        try:
            # logging.debug("Starting next_hand method")

            # Check if there are enough players to proceed
            if not self.player_windows:
                # logging.error("No player windows available.")
                return

            # Check if there are enough cards to deal
            required_cards = (len(self.player_windows) * 5) + 5
            if len(self.deck.cards) < required_cards:
                # logging.warning("Not enough cards in the deck. Resetting and reshuffling deck.")
                self.deck = Deck()  # Reset the deck
                self.deck.update_wild_card(self.table_chips)
                self.deck.shuffle()

            # Deal new cards
            try:
                self.call_button_clicked = False  # Reset the call button state
                self.turns_after_call = 0  # Reset the turn counter
                # Increment turns_after_call for the current player
                self.player_windows[self.current_player].turns_after_call += 1

                self.all_reveal_cards = self.deck.deal(5)
                self.all_player_cards = [
                    self.deck.deal(5) for _ in range(len(self.player_windows))
                ]
            except ValueError as e:
                # logging.warning(f"Not enough cards in the deck: {e}. Resetting and reshuffling deck.")
                self.deck = Deck()  # Reset the deck
                self.deck.update_wild_card(self.table_chips)
                self.deck.shuffle()
                self.all_reveal_cards = self.deck.deal(5)
                self.all_player_cards = [
                    self.deck.deal(5) for _ in range(len(self.player_windows))
                ]

            # Print details for debugging
            # logging.debug(f"next_hand - num_players: {len(self.player_windows)}")
            # logging.debug(f"next_hand - player_names: {[window.player_name for window in self.player_windows]}")
            # logging.debug(f"next_hand - all_reveal_cards: {self.all_reveal_cards}")
            # logging.debug(f"next_hand - all_player_cards: {self.all_player_cards}")

            # Clear and update widgets for each player
            for player_window in self.player_windows:
                # logging.debug(f"next_hand - Player {player_window.player_number} dealing cards.")
                player_window.add_cards_to_widget(
                    player_window.reveal_dragwidget, self.all_reveal_cards, reveal=True
                )
                player_window.add_cards_to_widget(
                    player_window.player_dragwidget,
                    self.all_player_cards[player_window.player_index - 1],
                    reveal=False,
                )

            # Re-enable and show the reveal buttons for all players
            for player_window in self.player_windows:
                player_window.reveal_button.setEnabled(True)
                player_window.reveal_button.setVisible(True)
                player_window.reveal_button.setStyleSheet("background-color: green;")

            # Set initial button states for each player
            for player_window in self.player_windows:
                # logging.debug(f"Setting initial button states for Player {player_window.player_number}")
                player_window.set_initial_button_states(
                    self.current_player_number, self.call_button_clicked
                )

            # Ensure player windows are correctly indexed
            self.player_windows = [
                window for window in self.player_windows if window.player_chips
            ]
            for index, player_window in enumerate(self.player_windows):
                player_window.player_number = index + 1

            # Set the button states for the next player
            if self.player_windows:
                next_player_index = (self.current_player + 1) % len(self.player_windows)
                # logging.debug(f"Calculated next_player_index: {next_player_index}")

                # Check index before accessing list
                if next_player_index < len(self.player_windows):
                    next_player_window = self.player_windows[next_player_index]
                    # logging.debug(f"Setting button states for next player (Player {next_player_window.player_number})")

                    # Ensure the current player's turn is set correctly
                    self.current_player = next_player_index
                    self.current_player_number = next_player_window.player_number
                    # logging.debug(f"Current player index set to {self.current_player}")
                    # logging.debug(f"Current player number set to {self.current_player_number}")

                    # Set the button states for the next player
                    self.set_next_player_button_states(next_player_window)

            logging.debug("Completed next_hand method")
        except Exception as e:
            logging.error(f"An error occurred in next_hand: {e}")
            import traceback

            traceback.print_exc()

    def final_end_game(self):
        # Display the final winner
        if len(self.player_windows) == 1:
            final_winner = self.player_windows[0]
            print(
                f"Game Over. The final winner is {final_winner.player_name} with {final_winner.player_chips} chips."
            )
            # QMessageBox.information(
            #     self,
            #     "Game Over",
            #     f"GW: Game Over! The final winner is {final_winner.player_name} with {final_winner.player_chips} chips."
            # )
            self.close()  # Close the game window
        else:
            print(
                "Final end game called with more than one player remaining, which should not happen."
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
            current_player_window.end_current_player_turn()
            next_player_number = (
                self.current_player_number % len(self.player_windows)
            ) + 1
            next_player_window = self.get_player_window_by_number(next_player_number)
            self.set_current_player(next_player_number)
            self.set_next_player_button_states(next_player_window)

    def set_next_player_button_statesOriginal(self, next_player_window):
        try:
            # logging.debug(f"Setting button states for next player (Player {next_player_window.player_number})")

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

            # Enable reveal button for the next player
            next_player_window.reveal_button.setEnabled(True)
            next_player_window.reveal_button.setStyleSheet("background-color: green;")
            print(
                f"Player {next_player_window.player_number}: Reveal button enabled (green)"
            )

            # Ensure the exchange button is disabled and red when the reveal button is enabled
            next_player_window.exchange_button.setEnabled(False)
            next_player_window.exchange_button.setStyleSheet("background-color: red;")
            print(
                f"Player {next_player_window.player_number}: Exchange button disabled (red)"
            )

            # Enable call and pass buttons for the next player only if the reveal button is enabled
            if next_player_window.reveal_button.isEnabled():
                next_player_window.call_button.setEnabled(True)
                next_player_window.call_button.setStyleSheet("background-color: green;")
                next_player_window.pass_button.setEnabled(True)
                next_player_window.pass_button.setStyleSheet("background-color: green;")
                print(
                    f"Player {next_player_window.player_number}: Call button enabled (green), Pass button enabled (green)"
                )
            else:
                next_player_window.call_button.setEnabled(False)
                next_player_window.call_button.setStyleSheet("background-color: red;")
                next_player_window.pass_button.setEnabled(False)
                next_player_window.pass_button.setStyleSheet("background-color: red;")
                print(
                    f"Player {next_player_window.player_number}: Call button disabled (red), Pass button disabled (red)"
                )

            # Update the current player's number to the next player's number
            self.current_player_number = next_player_window.player_number
            # logging.debug(f"Current player number set to {self.current_player_number}")

        except Exception as e:
            print(f"An error occurred in set_next_player_button_states: {e}")
            traceback.print_exc()

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
            for item in reveal_dragwidget.findChildren(Cards):
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
                    card_label = Cards(
                        card, reveal_dragwidget, reveal_dragwidget, face_down=False
                    )  # Ensure face_down=False
                    reveal_dragwidget.add_item(card_label)
                else:
                    pass

    def print_all_cards(self):
        for player_window in self.player_windows:
            print(f"Player {player_window.player_number + 1} Reveal Cards:")
            for card in player_window.reveal_dragwidget.items:
                print(card.card.value, card.card.suit)
            print(f"Player {player_window.player_number + 1} Player Cards:")
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


def main():
    # Configure logging right at the very beginning
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
    )  # <-- ADD THIS LINE HERE

    logging.info("Starting the game application.")  # <-- Now you can use it!

    app = QApplication([])

    num_players = 3

    # Create and show the PlayerNamesDialog
    dialog = PlayerNamesDialog(num_players)
    if dialog.exec_() == QDialog.Accepted:
        player_names = dialog.player_names
    else:
        sys.exit(0)

    game_window = GameWindow(app, num_players, player_names)
    game_window.start_first_hand()

    def exception_hook(exctype, value, tb):
        print("Unhandled exception:", exctype, value)
        traceback.print_tb(tb)
        sys.__excepthook__(exctype, value, tb)
        sys.exit(1)

    sys.excepthook = exception_hook

    game_window.show()  # Show the game window
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
