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
    QPushButton, QInputDialog, QMessageBox, QDialog, QLineEdit, QListWidget, QListWidgetItem, QTextEdit
    )
from PyQt5.QtCore import Qt, QMimeData, pyqtSignal, QObject, QTimer, pyqtSlot
from PyQt5.QtGui import QPixmap, QDrag, QPainter, QPen, QIcon, QCloseEvent, QTextCursor
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
from itertools import combinations_with_replacement

print("Python executable:", sys.executable)
print("Python path:", sys.path)
print("Environment variables:", os.environ)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


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
            print(f"Card: load_image - Red border added to wild card: {self.id}")

    def add_red_border(self):
        if not self.pixmap.isNull():
            painter = QPainter(self.pixmap)
            pen = QPen(Qt.red, 5)
            painter.setPen(pen)
            painter.drawRect(0, 0, self.pixmap.width() - 1, self.pixmap.height() - 1)
            painter.end()

    def highlight_wild_card(self, card_label, is_face_up):
        if card_label is not None and hasattr(card_label, 'card'):
            if card_label.card.is_wild and is_face_up:
                card_label.setStyleSheet("border: 2px solid red;")
            else:
                card_label.setStyleSheet("")  # Clear the border style
        else:
            pass
            # print(f"Card: highlight_wild_card - Card label is None or does not have a 'card' attribute: {card_label}")

    def set_wild(self, is_wild):
        self.is_wild = is_wild
        self.load_image()
        if self.is_wild:
            # pass
            print(f"Card: set_wild - Card {self.id} is wild and should be highlighted.")
        else:
            pass
            # print(f"Card {self.id} is not wild.")

    # ACE value 1 wildcard and ACE value 14 no wildcard

    def get_value(self, table_chips):
        if table_chips == 1 and self.value == 'A':
            return 1
        return VALUE_DICT[self.value]

    # END ============================

    def set_face_down(self):
        self.face_up = False
        self.pixmap = QPixmap("graphics/cards/default.png")

    def set_face_up(self):
        self.face_up = True
        self.load_image()

    def get_pixmap(self):
        return self.pixmap


class Cards(QLabel):
    def __init__(self, card, player_dragwidget, reveal_dragwidget, parent_window=None, parent=None, face_down=False):
        super().__init__(parent)
        # logging.info(f"Cards- Initializing card {card.value}{card.suit} with parent {parent}, parent_window: {parent_window}")
        # logging.debug(f"Cards- initialized: {card.value}{card.suit}, face_down={face_down}")
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
        #     f"Cards- Widget relationships: parent_dragwidget={self.player_dragwidget}, reveal_dragwidget={self.reveal_dragwidget}, parent_window={self.parent_window}")

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
        pixmap = self.card.get_pixmap().scaled(50, 80, Qt.AspectRatioMode.KeepAspectRatio)
        self.setPixmap(pixmap)

    def __eq__(self, other):
        if isinstance(other, Cards):
            return self.card.value == other.card.value and self.card.suit == other.card.suit
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
            if (e.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
                return

            drag = QDrag(self)
            mime = QMimeData()
            card_data = {'value': self.card.value, 'suit': self.card.suit}
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

    def handle_card_movement(self):
        parent_widget = self.parent()
        print(f"Handling card movement for {self.card.value}{self.card.suit} from {parent_widget}.")
        current_player = parent_widget.parent_window.is_current_player_turn()

        # Allow card movement only if the correct buttons are enabled (allow flexibility with certain buttons being red)
        if not (parent_widget.parent_window.reveal_button.isEnabled() or
                parent_widget.parent_window.exchange_button.isEnabled() or
                parent_widget.parent_window.pass_button.isEnabled()):
            print("handle_card_movement - Cannot move cards when required buttons are disabled.")
            return

        # Handle movement from reveal_dragwidget to player_dragwidget
        if parent_widget == self.reveal_dragwidget:
            if current_player and not self.face_down:
                if len(self.player_dragwidget.items) < self.player_dragwidget.maximum_cards():
                    print(f"Removing {self.card.value}{self.card.suit} from reveal_dragwidget.")
                    self.reveal_dragwidget.remove_item(self)
                    print(f"Adding {self.card.value}{self.card.suit} to player_dragwidget.")
                    self.player_dragwidget.add_item(self)
                    self.setParent(self.player_dragwidget)
                    self.show()  # Ensure the widget is visible
                    print(f"Removing {self.card.value}{self.card.suit} from all reveal_dragwidgets.")
                    parent_widget.parent_window.main_window.remove_card_from_all_reveal_dragwidgets(self.card,
                                                                                                    self.player_dragwidget)
                    print(f"Moved {self.card.value}{self.card.suit} from reveal_dragwidget to player_dragwidget")
                else:
                    print(
                        f"Cannot move {self.card.value}{self.card.suit} to player_dragwidget. Maximum cards limit reached.")
            else:
                print(
                    f"Cannot move {self.card.value}{self.card.suit} to player_dragwidget. Not current player's turn or card is face down.")
        # Handle movement from player_dragwidget to reveal_dragwidget
        elif parent_widget == self.player_dragwidget:
            if len(self.reveal_dragwidget.items) < self.reveal_dragwidget.maximum_cards():
                print(f"Moving card {self.card.value}{self.card.suit} from player_dragwidget to reveal_dragwidget.")
                self.player_dragwidget.remove_item(self)
                self.reveal_dragwidget.add_item(self)
                self.setParent(self.reveal_dragwidget)
                self.show()  # Ensure the widget is visible
                print(f"Adding {self.card.value}{self.card.suit} to all reveal_dragwidgets.")
                parent_widget.parent_window.main_window.add_card_to_all_reveal_dragwidgets(self.card,
                                                                                           exclude_widget=self.reveal_dragwidget)
                # Call end_current_player_turn after the move
                parent_widget.parent_window.end_current_player_turn()

                print(f"Moved {self.card.value}{self.card.suit} from player_dragwidget to reveal_dragwidget")
            else:
                print(
                    f"Cannot move {self.card.value}{self.card.suit} to reveal_dragwidget. Maximum cards limit reached.")
        else:
            print(f"Unknown parent widget for card {self.card.value}{self.card.suit}, defaulting to player_cards")

    def print_card_movement_info(self):
        print(f"Added Dropped Card: {self.card.value}{self.card.suit}")
        current_items = [f"{card.card.value}{card.card.suit}" for card in self.player_dragwidget.findChildren(Cards)]
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

    def update_wild_card(self, table_chips):
        wild_card_value_number = table_chips
        matching_values = [key for key, value in self.value_dict.items() if value == wild_card_value_number]
        if matching_values:
            wild_card_value = matching_values[0]
            self.wild_card_value = wild_card_value
            print("")
            print(f"Deck: update_wild_card - Wild card updated to {self.wild_card_value}")
            print("")
        else:
            print(f"Deck: update_wild_card - ACE value 1 wildcard & value 14 not wildcar - No matching wild card value found for table_chips = {table_chips}")

        # Update card states
        for card in self.cards:
            card.set_wild(card.value == self.wild_card_value or (table_chips == 1 and card.value == 'A'))

    def draw_card(self):
        if not self.cards:
            raise ValueError("No cards left in the deck")
        return self.cards.pop()


class DragWidget(QWidget):
    orderChanged = pyqtSignal(list)
    cardDropped = pyqtSignal(dict)

    def __init__(self, parent_window=None, player_dragwidget=None, reveal_dragwidget=None, reveal_dragwidgets=None, parent=None, drag_type='player_cards', max_items=6, min_items=5):
        super().__init__(parent)
        logging.info(f"Initializing DragWidget with drag_type={drag_type}")
        logging.debug(f"DragWidget initialized with drag_type={drag_type}, max_items={max_items}")
        self.parent_window = parent_window
        self.drag_type = drag_type
        self.setAcceptDrops(True)
        self.player_dragwidget = player_dragwidget
        self.reveal_dragwidgets = reveal_dragwidgets if reveal_dragwidgets is not None else []

        self.items = []
        self.cards = []

        self.orientation = Qt.Horizontal
        self.max_items = max_items
        self.min_items = min_items
        self.drag_type = None  # Initialize drag_type attribute
        self.drag_index = None
        self.drag_start_position = None  # Initialize drag start position
        self.layout = QHBoxLayout() if self.orientation == Qt.Horizontal else QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.cards_face_up = False

        # Log the state after initialization
        print(f"DragWidget initialized with max_items={max_items} and min_items={min_items}")
        logging.info(
            f"DragWidget initialized with max_items={self.max_items} and reveal_dragwidgets={self.reveal_dragwidgets}")
        logging.debug(
            f"DragWidget initialized with drag_type={self.drag_type}, max_items={self.max_items}, min_items={self.min_items}")
        logging.debug(
            f"Associated reveal_dragwidgets: {len(self.reveal_dragwidgets)}, parent_window: {self.parent_window}")

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            logging.debug(f"Drag entered: {event.mimeData().text()}")
            print("Drag entered, accepting event.")
            event.acceptProposedAction()
        else:
            logging.debug("Drag entered without valid mimeData")
            print("Drag entered, ignoring event.")
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
                card = Card(card_data['value'], card_data['suit'])
                logging.debug(f"Dropping card: {card_data}")

                source_widget = event.source()
                if self == self.parent_window.reveal_dragwidget:
                    print("Handling drop on reveal_dragwidget")
                    self.handle_drop_on_reveal(event, card)
                elif self == self.parent_window.player_dragwidget:
                    print("Handling rearrangement within player_dragwidget")
                    self.rearrange_player_cards(event)
                    # No need to call end_current_player_turn here, as it is handled in handle_card_movement
                    logging.debug(f"Drop successful on widget {self} with card {card_data}")
            except Exception as e:
                logging.error(f"DropEvent error: {str(e)}")
                event.ignore()

            self.drag_item = None
            event.acceptProposedAction()
        else:
            logging.debug("dropEvent rejected: no valid mimeData")
            event.ignore()

    def handle_drop_on_reveal(self, event, card):
        source_widget = event.source()
        logging.debug(f"Handling drop on reveal_dragwidget with card {card.value} of {card.suit}")

        # Check if the drop is allowed based on button states, but focus on reveal and pass buttons.
        if not (self.parent_window.reveal_button.isEnabled() or self.parent_window.pass_button.isEnabled()):
            logging.debug("Drop rejected: action not allowed (reveal/pass button states invalid).")
            event.ignore()
            return

        # Don't allow cards to be dropped when reveal_dragwidget contains face-down cards
        if any(item.face_down for item in self.items):
            print("Cannot drop cards onto reveal_dragwidget when there are face-down cards.")
            event.ignore()
            return

        current_player = self.parent_window.is_current_player_turn()
        if not current_player:
            print("Cannot drop cards onto reveal_dragwidget when it's not the current player's turn.")
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
            dragged_card = Card(card_data['value'], card_data['suit'])

            dragged_card_index = None
            for i, card in enumerate(self.items):
                logging.debug(f"Card {i}: {card.card.value} of {card.card.suit}")
                if card.card.value == dragged_card.value:
                    dragged_card_index = i
                    break

            if dragged_card_index is None:
                print("rearrange_player_cards-Error: Dragged card not found in player cards.")
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
                f"Card moved from index {dragged_card_index} to {drop_index}. New card order: {[item.card.value for item in self.items]}")

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

    def get_dragged_card_index(self):
        print("589- get_dragged_card_index called")
        for i, card in enumerate(self.player_dragwidget.items):
            if card.isSelected():
                return i
        return None

    def get_index_at_position(self, pos):
        print("596- get_index_at_position called")
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
            print(f"Cannot add more items, max limit ({self.max_items}) reached.")

    def remove_item(self, item):
        if item in self.items:
            self.items.remove(item)
            self.layout.removeWidget(item)
            item.setParent(None)
            print(f"Removed item. Total items: {len(self.items)}")
        else:
            print("Item not found in DragWidget.")

    def add_card(self, card):
        if len(self.cards) < 6:  # Allow up to 6 cards during a drop event
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
    def __init__(self, player_id, player_number, player_dragwidget, reveal_dragwidget, parent_window, main_window, index, num_players, player_name, app, is_removed=False, is_active=True):
        super().__init__(parent_window)

        self.player_id = player_id
        self.player_number = player_number + 1
        self.parent_window = parent_window
        self.main_window = main_window
        self.app = app

        self.active_players = self.main_window.player_windows[:]
        self.is_active = is_active  # Set is_active parameter to track active players
        self.is_removed = is_removed
        self.player_chips = 1

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
        self.turns_after_pass = 0
        self.players = []  # List to hold all players
        self.items = []
        self.cards = []  #  OJOJOJOJOJOJOJO

        # Define the status label for the player window
        self.chips_label = QLabel(self)  # Chips display
        self.status_label = QLabel(self)
        # self.status_label.setFixedSize(20, 20)  # Example size for indicator
        self.status_label.setGeometry(10, 10, 20, 20)  # Example position and size
        self.status_label.setStyleSheet("background-color: green; border-radius: 10px;")  # Green for active

        # Create a QWidget to hold both chips_label and status_label side-by-side
        self.chips_status_widget = QWidget(self)
        chips_layout = QHBoxLayout(self.chips_status_widget)

        # Add both widgets to the layout
        chips_layout.addWidget(self.status_label)
        chips_layout.addWidget(self.chips_label)

        # Set stretch factor to make sure widgets are side by side
        chips_layout.setStretch(0, 0)  # No stretching for the status_label
        chips_layout.setStretch(1, 1)  # Allow chips_label to stretch if needed

        # Create a layout for buttons and labels
        main_layout = QHBoxLayout()  # Use a horizontal layout
        main_layout.addWidget(self.player_dragwidget)  # Add the player's button widgets
        main_layout.addStretch(1)  # Allow the layout to expand on the left
        main_layout.addWidget(self.chips_status_widget)  # Add the chips and status widget to the right
        main_layout.setAlignment(self.chips_status_widget, Qt.AlignRight)  # Align the chips/status widget to the right

        # Use a QWidget to hold the layout
        container_widget = QWidget(self)
        container_widget.setLayout(main_layout)
        # self.setCentralWidget(container_widget)

        self.update_chips_label(self.player_chips)  # Initialize with current chips

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
        if self.player_dragwidget is None or not hasattr(self.player_dragwidget, 'orderChanged'):
            raise ValueError("class PlayerWindow - player_dragwidget is not properly initialized.")

        # Ensure reveal_dragwidget is properly initialized
        if self.reveal_dragwidget is None:
            raise ValueError("class PlayerWindow - reveal_dragwidget is not properly initialized.")

        # Ensure player_dragwidget.items is initialized
        if not hasattr(self.player_dragwidget, 'items'):
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

        # Create and configure the chips label
        self.chips_label = QLabel(self)
        self.update_chips_label(self.player_chips)
        layout.addWidget(self.chips_label)

        # Create a QWidget to hold the layout and add it to the buttons_dock
        buttons_widget = QWidget()
        buttons_widget.setLayout(layout)
        buttons_dock.setWidget(buttons_widget)

        # Set the layout for the buttons_dock to ensure proper positioning
        self.addDockWidget(Qt.TopDockWidgetArea, buttons_dock)

        # Add the buttons dock on top of the reveal cards dock
        reveal_cards.setTitleBarWidget(buttons_dock)

    # send a message to the other players ================

    def init_message_ui(self):
        # Create a layout to organize the message components
        message_layout = QVBoxLayout()

        message_layout.addWidget(self.message_box)
        message_layout.addWidget(self.message_input)
        message_layout.addWidget(self.send_message_button)

        # Create a widget to hold the message layout and set it as the central widget
        message_widget = QWidget()
        message_widget.setLayout(message_layout)
        dock_widget = QDockWidget("Messages", self)
        dock_widget.setWidget(message_widget)

        # Add the message dock to the main window layout
        self.addDockWidget(Qt.BottomDockWidgetArea, dock_widget)

    @pyqtSlot()
    def send_input_message(self):
        message = self.message_input.text().strip()
        if message:
            self.send_message(message)
            self.message_input.clear()

    def send_message(self, message):
        try:
            self.server_connection.send(message.encode('utf-8'))
        except Exception as e:
            print(f"Error sending message: {e}")

    def receive_messages(self):
        while True:
            try:
                message = self.server_connection.recv(1024).decode('utf-8')
                if message:
                    self.display_message(message)
                else:
                    print("Connection closed by server.")
                    break
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    def display_message(self, message):
        self.message_box.append(message)

    def handle_received_message(self, message):
        self.message_box.append(message)
        super().handle_received_message(message)
        print(f"Received message: {message}")

    def closeEvent(self, event: QCloseEvent) -> None:
        print("Disconnecting from server.")
        if self.server_connection:
            self.server_connection.close()
        super().closeEvent(event)

    # END sending a message =====================

    def update_chips_label(self, chips):
        self.player_chips = chips
        self.chips_label.setText(f"P1-2 - Player Chips: {self.player_chips}")
        print(f"P2-2 - Updated chips label for Player {self.player_number} to {self.player_chips}")

    def create_card_widget(self, card):
        card_widget = Cards(card, parent_window=self)
        return card_widget

    def initialize_game(self):
        player = Player(self.player_id, self.player_number, self.player_dragwidget, self.reveal_dragwidget,
                        self.parent_window, self.main_window, self, self.player_index + 1, self.num_players,
                        self.player_name)
        self.player = player

    def find_card_label(self, card):
        for card_label in self.cards:
            if card_label.card == card:  # Assuming card_label has a card attribute
                return card_label
        return None

    def is_current_player_turn(self):
        return self.pass_button.isEnabled() and self.pass_button.styleSheet() == "background-color: green;"

    def is_action_allowed(self):
        try:
            # Check if the exchange button is enabled and green
            exchange_button_enabled = self.exchange_button.isEnabled()
            exchange_button_color = self.exchange_button.palette().button().color().name()
            exchange_button_is_green = exchange_button_color == "#008000"  # Green color check

            # Check if the reveal button is hidden
            reveal_button_hidden = self.reveal_button.isHidden()

            # Check if the pass button is enabled and green
            pass_button_enabled = self.pass_button.isEnabled()
            pass_button_color = self.pass_button.palette().button().color().name()
            pass_button_is_green = pass_button_color == "#008000"  # Green color check

            # The action is allowed if the exchange button is green, reveal button is hidden, and pass button is green
            if exchange_button_is_green and reveal_button_hidden and pass_button_is_green:
                return True

            return False

        except Exception as e:
            print(f"Error in is_action_allowed: {e}")
            return False

    def is_rearrange_action(self, event):
        return event.source() == self and self == self.parent_window.player_dragwidget

    def check_drag_drop_actions(self):
        if self.parent_window.is_current_player_turn():
            if self.reveal_dragwidget.current_item is not None and \
                    self.player_dragwidget.current_item is None:
                # Dragged from reveal_dragwidget to player_dragwidget
                self.reveal_dragwidget.current_item.setParent(self.player_dragwidget)
                self.end_current_player_turn()
            elif self.player_dragwidget.current_item is not None and \
                    self.reveal_dragwidget.current_item is None:
                # Dragged from player_dragwidget to reveal_dragwidget
                self.player_dragwidget.current_item.setParent(self.reveal_dragwidget)
                self.end_current_player_turn()

    def add_card(self, card, player_dragwidget=True):
        card_label = Cards(card, self.player_dragwidget, self.reveal_dragwidget, parent_window=self)
        if player_dragwidget:
            self.player_dragwidget.add_item(card_label)
        else:
            self.reveal_dragwidget.add_item(card_label)
        card_label.setAlignment(Qt.AlignCenter)

    # CARDS ==============

    def reveal_cards(self, table_chips):
        try:
            print("\n--- reveal_cards method started ---")
            print(f"reveal_cards clicked by Player name: {self.player_name} (player number: {self.player_number})")

            if not self.is_current_player_turn:
                print("It's not the current player's turn. Exiting method.")
                return  # Return early if it's not the current player's turn

            self.cards_revealed = True
            self.reveal_button_clicked = True  # Added flag to track reveal button click

            # Ensure lists are initialized
            self.reveal_cards = [card_label.card for card_label in self.reveal_dragwidget.items]
            self.player_cards = [card_label.card for card_label in self.player_dragwidget.items]

            # Clear both drag widgets
            self.player_dragwidget.clear()
            self.reveal_dragwidget.clear()

            # Update the drag widgets with the new cards
            for card in self.player_cards:
                card.set_face_down()
                card_label = Cards(card, self.player_dragwidget, self.reveal_dragwidget, parent_window=self)
                self.reveal_dragwidget.add_item(card_label)

            for card in self.reveal_cards:
                card.set_face_up()
                card.load_image()
                card_label = Cards(card, self.player_dragwidget, self.reveal_dragwidget, parent_window=self)
                self.player_dragwidget.add_item(card_label)

            # Update the card lists with the actual Card objects from the drag widgets
            self.reveal_cards = [card_label.card for card_label in self.reveal_dragwidget.items]
            self.player_cards = [card_label.card for card_label in self.player_dragwidget.items]

            print(f"reveal_cards - Current Player name: {self.player_name} (player number: {self.player_number})")

            # Determine the next player using player numbers
            next_player_window = self.main_window.get_next_active_player(self.player_number)

            if next_player_window:
                next_player_name = next_player_window.player_name
                next_player_number = next_player_window.player_number
                print(f"reveal_cards - Next player is Player name: {next_player_name} (player number: {next_player_number})")

                # Update the reveal button state for all players
                for window in self.main_window.player_windows:
                    window.reveal_button_clicked = True

                # ESTO ES PARA QUE CUANDO QUEDAN DOS JUGADORES EL JUEGO TERMINE BIEN
                if not self.call_button_clicked:
                    next_player_window.call_button.setEnabled(True)
                    next_player_window.call_button.setStyleSheet("background-color: green;")

                for window in self.main_window.player_windows:
                    window.reveal_button.hide()
                    if window == self:
                        for card_label in window.reveal_dragwidget.items:
                            card_label.card.set_face_up()
                            card_label.card.load_image()
                            scaled_pixmap = card_label.card.pixmap.scaled(50, 80, Qt.AspectRatioMode.KeepAspectRatio)
                            card_label.setPixmap(scaled_pixmap)
                        for card_label in window.player_dragwidget.items:
                            card_label.card.set_face_up()
                            card_label.card.load_image()
                            scaled_pixmap = card_label.card.pixmap.scaled(50, 80, Qt.AspectRatioMode.KeepAspectRatio)
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
                            card_label = Cards(card, window.player_dragwidget, window.reveal_dragwidget,
                                               parent_window=window)
                            card_label.card.set_face_up()
                            card_label.card.load_image()
                            card_label.setPixmap(
                                card_label.card.pixmap.scaled(50, 80, Qt.AspectRatioMode.KeepAspectRatio))
                            window.reveal_dragwidget.add_item(card_label)

                        if window.player_number not in [self.player_number, next_player_number]:
                            window.exchange_button.setEnabled(False)
                            window.exchange_button.setStyleSheet("background-color: red;")
                            window.call_button.setEnabled(False)
                            window.call_button.setStyleSheet("background-color: red;")
                            window.pass_button.setEnabled(False)
                            window.pass_button.setStyleSheet("background-color: red;")
                            print(f"reveal_cards - Player name: {window.player_name} (player number: {window.player_number}) buttons have been disabled.")

                if self.main_window.call_button_clicked:
                    for window in self.main_window.player_windows:
                        if window != self:
                            window.call_button.setEnabled(False)
                            window.call_button.setStyleSheet("background-color: red;")
                            # print(f"Call button has been disabled for player {window.player_number}.")

                QTimer.singleShot(0, lambda: self.main_window.check_end_hand(self.player_number, self.main_window.table_chips))

                print(f"Previous Player name: {self.player_name} (player number: {self.player_number}), now you see teh green button on Player name: {next_player_name} (player number: {next_player_number})")

        except Exception as e:
            print(f"Error in reveal_cards: {e}")

    def exchange_cards(self, table_chips):
        try:
            print("\n--- exchange_cards method started ---")
            print(
                f"exchange_cards - clicked by current Player name: {self.player_name} (player number: {self.player_number})")

            if not self.is_current_player_turn():
                print("It's not the current player's turn. Exiting method.")
                return  # Return early if it's not the current player's turn

            # Ensure lists are initialized
            self.reveal_cards = [card_label.card for card_label in self.reveal_dragwidget.items]
            self.player_cards = [card_label.card for card_label in self.player_dragwidget.items]

            # Get initial state of cards
            player_cards_before_exchange = self.player_dragwidget.items.copy()
            reveal_cards_before_exchange = self.reveal_dragwidget.items.copy()

            # Print statements to keep track of player_dragwidget and reveal_dragwidget cards
            print(
                f"exchange_cards - Reveal cards before exchange: {[card_label.card for card_label in reveal_cards_before_exchange]}")

            print(
                f"exchange_cards - Player cards before exchange: {[card_label.card for card_label in player_cards_before_exchange]}")

            # Clear both drag widgets
            self.player_dragwidget.clear()
            self.reveal_dragwidget.clear()

            # Swap cards between player_dragwidget and reveal_dragwidget
            for card_label in player_cards_before_exchange:
                self.reveal_dragwidget.addWidget(card_label)

            for card_label in reveal_cards_before_exchange:
                self.player_dragwidget.addWidget(card_label)

            # Update the card lists with the actual Card objects from the drag widgets
            self.reveal_cards = [card_label.card for card_label in self.reveal_dragwidget.items]
            self.player_cards = [card_label.card for card_label in self.player_dragwidget.items]

            # Print statements to keep track of player_dragwidget and reveal_dragwidget cards after exchange
            print(f"exchange_cards - Reveal cards after exchange: {self.reveal_cards}")
            print(f"exchange_cards - Player cards after exchange: {self.player_cards}")


            # Highlight wild cards
            for card_label in self.reveal_dragwidget.items:
                card_label.card.highlight_wild_card(card_label, True)
            for card_label in self.player_dragwidget.items:
                card_label.card.highlight_wild_card(card_label, not card_label.card.set_face_down)

            # Propagate changes to other player windows
            for window in self.main_window.player_windows:
                if window != self:
                    # Clear the reveal_dragwidget of the other player
                    window.reveal_dragwidget.clear()

                    # Update the reveal_dragwidget of the other players with the current player's revealed cards
                    for card in self.reveal_cards:
                        new_card_label = Cards(card, window.player_dragwidget, window.reveal_dragwidget,
                                               parent_window=self)
                        card.set_face_up()
                        new_card_label.setPixmap(card.pixmap.scaled(50, 80, Qt.AspectRatioMode.KeepAspectRatio))
                        window.reveal_dragwidget.addWidget(new_card_label)

            # Disable the exchange button for the current player
            self.disable_current_player_buttons()

            # Determine the next player using player numbers
            next_player_window = self.main_window.get_next_active_player(self.player_number)

            if next_player_window:
                print(
                    f"reveal_cards - Next player is Player name: {next_player_window.player_name} (player number: {next_player_window.player_number})")
                # Set the button states for the next player
                self.set_next_player_button_states(next_player_window)

            # Call the end hand check after a short delay
            QTimer.singleShot(0, lambda: self.main_window.check_end_hand(self.player_number, self.main_window.table_chips))

        except Exception as e:
            print(f"Error in exchange_cards: {e}")

    def pass_cards(self):
        try:
            print("\n--- pass_cards method started ---")
            print(f"pass_cards clicked by current Player: {self.player_number} (player number: {self.player_number})")

            if not self.is_current_player_turn():
                print("It's not the current player's turn. Exiting method.")
                return

            if self.pass_button.isEnabled() and self.pass_button.styleSheet() == "background-color: green;":
                self.pass_button.setEnabled(False)
                self.pass_button.setStyleSheet("background-color: red;")

                # Disable the call button for all players
                for window in self.main_window.player_windows:
                    window.call_button.setEnabled(False)
                    window.call_button.setStyleSheet("background-color: red;")

                # Determine the next player using player numbers
                next_player_window = self.main_window.get_next_active_player(self.player_number)

                if next_player_window:
                    print(
                        f"pass_cards - Next player is Player {next_player_window.player_name} (player number: {next_player_window.player_number}).")

                    # Check if the call button has been clicked before enabling it for the next player
                    if not self.call_button_clicked:
                        next_player_window.call_button.setEnabled(True)
                        next_player_window.call_button.setStyleSheet("background-color: green;")

                    # Disable all buttons for inactive players and enable for the next player
                    for window in self.main_window.player_windows:
                        if window == next_player_window:
                            self.set_next_player_button_states(window)
                            self.main_window.pass_button_clicked = True   # Set the pass button flag to True
                        else:
                            # window.disable_buttons()
                            window.reveal_button.setEnabled(False)
                            window.reveal_button.setStyleSheet("background-color: red;")
                            window.pass_button.setEnabled(False)
                            window.pass_button.setStyleSheet("background-color: red;")
                            window.call_button.setEnabled(False)
                            window.call_button.setStyleSheet("background-color: red;")
                            window.exchange_button.setEnabled(False)
                            window.exchange_button.setStyleSheet("background-color: red;")

                # Call the end hand check after a short delay
                QTimer.singleShot(0, lambda: self.main_window.check_end_hand(self.player_number, self.main_window.table_chips))

        except Exception as e:
            print(f"An error occurred in pass_cards: {e}")

    def call_cards(self):
        try:
            print("\n--- call_cards method started ---")
            current_player_name = self.player_name
            current_player_number = self.player_number

            print(
                f"call_cards - clicked by current Player name: {current_player_name} (player number: {current_player_number})")

            # Check if it's the current player's turn using player number
            if not self.is_current_player_turn():
                print("call_cards - Not the current player's turn.")
                return

            # Set the calling player number
            self.main_window.calling_player_number = current_player_number

            # Disable call, pass, and exchange buttons in all player windows
            for window in self.main_window.player_windows:
                window.call_button.setEnabled(False)
                window.call_button.setStyleSheet("background-color: red;")
                window.pass_button.setEnabled(False)
                window.pass_button.setStyleSheet("background-color: red;")
                window.exchange_button.setEnabled(False)
                window.exchange_button.setStyleSheet("background-color: red;")

            # Set a flag to indicate the call button has been clicked
            self.main_window.call_button_clicked = True

            # Disable buttons for the current player
            self.disable_current_player_buttons()

            print(
                f"call_cards - Current Player name: {current_player_name} (player number: {current_player_number})")

            # Determine the next player using player numbers
            next_player_window = self.main_window.get_next_active_player(current_player_number)

            if next_player_window:
                print(
                    f"call_cards - Next player is Player name: {next_player_window.player_name} (player number: {next_player_window.player_number})")
            else:
                print("call_cards - No valid next player found.")

            # Update button states for the next player if found
            if next_player_window:
                print(
                    f"call_cards - Setting button states for next player: Player name: {next_player_window.player_name} (player number: {next_player_window.player_number})")

                # Enable the reveal and pass buttons for the next player
                next_player_window.reveal_button.setEnabled(True)
                next_player_window.reveal_button.setStyleSheet("background-color: green;")
                next_player_window.pass_button.setEnabled(True)
                next_player_window.pass_button.setStyleSheet("background-color: green;")

                # Enable exchange button only if reveal is hidden
                if next_player_window.reveal_button.isHidden():
                    next_player_window.exchange_button.setEnabled(True)
                    next_player_window.exchange_button.setStyleSheet("background-color: green;")
                else:
                    next_player_window.exchange_button.setEnabled(False)
                    next_player_window.exchange_button.setStyleSheet("background-color: red;")

                # Disable the call button for the next player
                next_player_window.call_button.setEnabled(False)
                next_player_window.call_button.setStyleSheet("background-color: red;")
            else:
                print("Error: No next player could be assigned button control.")

            print("\n--- call_cards method completed ---")

            # Schedule the game end check after the next player's turn
            if next_player_window:
                QTimer.singleShot(0, lambda: self.main_window.check_end_hand(current_player_number,
                                                                             self.main_window.table_chips))
        except Exception as e:
            logging.error(f"An error occurred in call_cards: {e}")
            import traceback
            traceback.print_exc()

    # BUTTONS SEQUENCE =================

    def set_initial_button_states(self, current_player_number, call_button_clicked):
        try:
            # logging.debug(
            #     f"Player {self.player_number}: Setting initial button states (current_player_number: {current_player_number}, call_button_clicked: {call_button_clicked})")
            self.reveal_button.setEnabled(True)
            self.reveal_button.setStyleSheet("background-color: green;")
            # print(f"Player {self.player_number}: Reveal button enabled (green)")

            if self.player_number == current_player_number:
                self.exchange_button.setEnabled(False)
                self.exchange_button.setStyleSheet("background-color: red;")
                self.call_button.setEnabled(True)
                self.call_button.setStyleSheet("background-color: green;")
                self.pass_button.setEnabled(True)
                self.pass_button.setStyleSheet("background-color: green;")
                # print(
                #     f"Player {self.player_number}: Exchange button disabled (red), Call button enabled (green), Pass button enabled (green)")
            else:
                self.reveal_button.setEnabled(False)
                self.reveal_button.setStyleSheet("background-color: red;")
                self.exchange_button.setEnabled(False)
                self.exchange_button.setStyleSheet("background-color: red;")
                self.call_button.setEnabled(False)
                self.call_button.setStyleSheet("background-color: red;")
                self.pass_button.setEnabled(False)
                self.pass_button.setStyleSheet("background-color: red;")
                # print(f"Player {self.player_number}: All buttons disabled (red)")
        except Exception as e:
            print(f"An error occurred in set_initial_button_states: {e}")
            traceback.print_exc()

    def set_next_player_button_states(self, next_player_window):
        try:
            # logging.debug(
            #     f"Player {self.player_number}: Setting button states for next player (Player {next_player_window.player_number})")

            next_player_window.reveal_button.setEnabled(True)
            next_player_window.reveal_button.setStyleSheet("background-color: green;")
            # print(f"Player {next_player_window.player_number}: Reveal button enabled (green)")

            # Ensure the exchange button is disabled and red when the reveal button is enabled
            if next_player_window.reveal_button.isHidden():
                next_player_window.exchange_button.setEnabled(True)
                next_player_window.exchange_button.setStyleSheet("background-color: green;")
            else:
                next_player_window.exchange_button.setEnabled(False)
                next_player_window.exchange_button.setStyleSheet("background-color: red;")
            # print(
            #     f"Player {next_player_window.player_number}: Exchange button state: Enabled: {next_player_window.exchange_button.isEnabled()}, StyleSheet: {next_player_window.exchange_button.styleSheet()}")

            if not hasattr(self.main_window, 'call_button_clicked') or not self.main_window.call_button_clicked:
                next_player_window.call_button.setEnabled(True)
                next_player_window.call_button.setStyleSheet("background-color: green;")
                # print(f"Player {next_player_window.player_number}: Call button enabled (green)")
            else:
                next_player_window.call_button.setEnabled(False)
                next_player_window.call_button.setStyleSheet("background-color: red;")
                # print(f"Player {next_player_window.player_number}: Call button disabled (red)")

            next_player_window.pass_button.setEnabled(True)
            next_player_window.pass_button.setStyleSheet("background-color: green;")
            # print(f"Player {next_player_window.player_number}: Pass button enabled (green)")

        except Exception as e:
            print(f"An error occurred in set_next_player_button_states: {e}")
            traceback.print_exc()

    def disable_current_player_buttons(self):
        self.reveal_button.setEnabled(False)
        self.reveal_button.setStyleSheet("background-color: red;")
        self.exchange_button.setEnabled(False)
        self.exchange_button.setStyleSheet("background-color: red;")
        self.call_button.setEnabled(False)
        self.call_button.setStyleSheet("background-color: red;")
        self.pass_button.setEnabled(False)
        self.pass_button.setStyleSheet("background-color: red;")

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
            item.setPixmap(item.card.pixmap.scaled(50, 80, Qt.AspectRatioMode.KeepAspectRatio))

    def set_cards_face_up(self):
        if self.cards_revealed:
            print("Setting cards face up in DragWidget")
            for card_label in self.items:
                if not card_label.card.face_up:
                    card_label.card.face_up = True
                    card_label.card.load_image()  # Load the image for the card
                    scaled_pixmap = card_label.card.pixmap.scaled(50, 80, Qt.AspectRatioMode.KeepAspectRatio)
                    card_label.setPixmap(scaled_pixmap)

    def add_cards_to_widget(self, widget, cards, reveal):
        try:
            widget.clear()
            for card in cards[:5]:  # Ensure only the first 5 cards are added
                card_label = Cards(card, self.player_dragwidget, self.reveal_dragwidget, parent_window=self)
                if reveal:
                    card.set_face_down()
                    is_face_up = False
                else:
                    card.set_face_up()
                    is_face_up = True
                scaled_pixmap = card.pixmap.scaled(50, 80, Qt.AspectRatioMode.KeepAspectRatio)
                card_label.setPixmap(scaled_pixmap)

                # Highlight wild card
                card.highlight_wild_card(card_label, is_face_up)

                widget.add_item(card_label)
        except Exception as e:
            print(f"An error occurred in add_cards_to_widget: {e}")

    def update_cards(self, reveal_cards, player_cards):
        try:
            self.reveal_cards = reveal_cards[:5]  # Ensure only the first 5 cards are used for reveal
            self.player_cards = player_cards[:5]  # Ensure only the first 5 cards are used for player

            self.reveal_dragwidget.clear()
            self.add_cards_to_widget(self.reveal_dragwidget, self.reveal_cards, reveal=True)

            self.player_dragwidget.clear()
            self.add_cards_to_widget(self.player_dragwidget, self.player_cards, reveal=False)
        except Exception as e:
            print(f"An error occurred in update_cards: {e}")

    def get_card_details(self):
        # This method will gather and return the details of the cards in the player's widgets
        player_cards = [card.card for card in self.player_dragwidget.children() if hasattr(card, 'card')]
        reveal_cards = [card.card for card in self.reveal_dragwidget.children() if hasattr(card, 'card')]
        # return f"Player Cards: {player_cards}, Reveal Cards: {reveal_cards}"
        return player_cards, reveal_cards

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
        reveal_card_strings = [f"{str(card.value)}{card.suit}" for card in self.reveal_cards]
        player_card_strings = [f"{str(card.value)}{card.suit}" for card in self.player_cards]
        print(f"1191- Player {self.player_number} Reveal Cards: {reveal_card_strings}")
        print(f"1192- Player {self.player_number} Player Cards: {player_card_strings}")

    # This control the player list red & green lights

    def set_status_indicator(self, color):
        """
        Update the player's status indicator (e.g., label, icon, or border color) to reflect their activity status.
        """
        try:
            # Assuming there is a QLabel or similar widget as the status indicator
            if hasattr(self, 'status_label'):  # Check if status_label exists
                self.status_label.setStyleSheet(f"background-color: {color}; border-radius: 10px;")
                print(
                    f"Status indicator set to {color} for Player {self.player_name} (player number: {self.player_number})")
                # if color == 'red':
                #     self.disable_buttons()
            else:
                print("Status label is not defined in PlayerWindow. Define 'self.status_label' to set indicator color.")
        except Exception as e:
            print(f"An error occurred while setting the status indicator: {e}")

    def disable_buttons(self):
        """
        Disable all action buttons for the player and set them to inactive color (e.g., gray).
        """
        try:
            self.reveal_button.setEnabled(False)
            self.reveal_button.setStyleSheet("background-color: gray;")
            self.exchange_button.setEnabled(False)
            self.exchange_button.setStyleSheet("background-color: gray;")
            self.call_button.setEnabled(False)
            self.call_button.setStyleSheet("background-color: gray;")
            self.pass_button.setEnabled(False)
            self.pass_button.setStyleSheet("background-color: gray;")
            print(
                f"All buttons disabled for Player name: {self.player_name} (player number: {self.player_number})")
        except AttributeError as e:
            print(f"An error occurred in disable_buttons: {e}")


# Define your actual Player class here
class Player:
    def __init__(self, player_id, player_number, player_dragwidget, reveal_dragwidget, parent_window, main_window, game_window, player_position, num_players, player_name):
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
        self.is_active = True


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
            rotated_surface = pygame.transform.rotate(text_surface, self.win_rotation_angle)
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


class HandRank(IntEnum):
    HIGH_CARD = 1
    ONE_PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    POKER = 8
    REPOKER = 9
    STRAIGHT_FLUSH = 10


class Dealer(QObject):
    table_chip_label_updated = pyqtSignal(int)  # Signal for updating table chip label
    side_chip_label_updated = pyqtSignal(int)  # Signal for updating side chip label
    player_chips_updated = pyqtSignal(int, int)  # Signal for updating player chips

    def __init__(self, game_window,  player_windows, flop, table_chip_label, side_chip_label, table_chips, side_chips, deck):
        super().__init__()
        self.game_window = game_window
        self.value_dict = VALUE_DICT
        self.player_windows = player_windows
        self.determined_winner = None
        self.current_player_index = 0
        self.current_flop_index = 0
        self.printed_flop = False
        self.can_deal = True
        self.can_deal_flop = False
        self.last_dealt_card_time = None
        self.last_dealt_flop_time = None
        self.dealt_cards = 0
        self.flop = flop
        self.audio_channel = 0
        self.table_chips = table_chips
        self.side_chips = side_chips
        self.table_chip_label = table_chip_label
        self.side_chip_label = side_chip_label
        self.wild_card_value = None

        self.deck = deck

    # Wildcard ===========================

    def set_wild_card(self, card_value):
        for player_window in self.player_windows:
            for card_label in player_window.cards:
                card = card_label.card
                card.set_wild(card.value == card_value)
                card_label.setPixmap(card.pixmap)

    def update_wild_card_value(self):
        wild_card_value_number = self.table_chips
        matching_values = [key for key, value in self.value_dict.items() if value == wild_card_value_number]
        if matching_values:
            wild_card_value = matching_values[0]
            self.wild_card_value = wild_card_value
            print(f"Dealer: update_wild_card_value - Wild card updated to {self.wild_card_value}")
        else:
            print(
                f"Dealer: update_wild_card_value - No matching wild card value found for table_chips = {self.table_chips}")

        # Update card states
        for player_window in self.player_windows:
            for card in player_window.cards:
                card.set_wild(self.is_wild_card(card))
                card_label = player_window.find_card_label(card)
                if card_label:
                    card_label.setPixmap(card.get_pixmap())

    def determine_wild_card(self):
        wild_card_value = self.table_chips
        return wild_card_value

    def is_wild_card(self, card):
        return card.value == str(self.determine_wild_card())

    # END Wildcard ===============================

    def shuffle_deck(self):
        logging.info("Dealer shuffling the deck...")
        random.shuffle(self.deck)

    def deal(self, deck, num_cards):
        if len(self.deck) < num_cards:
            raise ValueError("Not enough cards in the deck to deal.")
        dealt_cards = self.deck[:num_cards]
        self.deck = self.deck[num_cards:]
        return dealt_cards

    def remaining_cards(self):
        return len(self.deck)

    def draw_card(self):
        if self.deck:
            return self.deck.pop()
        else:
            raise ValueError("No more cards in the deck")

    # from itertools import combinations_with_replacement ======================================

    def eval_hand(self, hand, table_chips):
        logging.info("Dealer Evaluating hand rank")
        value_map = self.value_dict
        values = []
        suits = []
        wildcards = []

        for card in hand:
            if card.is_wild:
                wildcards.append(card.value)  # Assuming card.value is a placeholder for wildcards
            else:
                # values.append(value_map[str(card.get_value())])
                values.append(card.get_value(table_chips))
            suits.append(card.suit)

        # print(
        #     f"Dealer: eval_hand - Hand values before considering wild cards: {values}, suits: {suits}, wildcards: {wildcards}")

        # Generate possible hands considering all wildcards
        best_hand = None
        possible_values = list(range(2, 15))  # Possible values for the wild cards (2 to Ace)

        if wildcards:
            from itertools import combinations_with_replacement
            num_wildcards = len(wildcards)
            for wild_combination in combinations_with_replacement(possible_values, num_wildcards):
                possible_hand = sorted(values + list(wild_combination), reverse=True)
                evaluated_hand = self.evaluate_possible_hand(possible_hand, suits,
                                                             [])  # Do not use wildcards in the evaluate_possible_hand method
                if not best_hand or evaluated_hand > best_hand:
                    best_hand = evaluated_hand
        else:
            best_hand = self.evaluate_possible_hand(values, suits, wildcards)

        return best_hand

    def evaluate_possible_hand(self, values, suits, wildcards):
        count = Counter(values)
        most_common = count.most_common()
        # print(f"Dealer: eval_hand - Evaluating with values: {values} -> Most common: {most_common}")

        is_straight = self.check_straight(values)
        is_flush = self.check_flush(suits)
        poker_result = self.check_poker(most_common)

        if is_straight and is_flush:
            return HandRank.STRAIGHT_FLUSH, values
        elif most_common and most_common[0][1] == 4 and len(set(values)) == 4 and len(wildcards) == 1:
            return HandRank.REPOKER, most_common
        elif poker_result:
            return poker_result
        elif most_common and most_common[0][1] == 3 and len(most_common) > 1 and most_common[1][1] == 2:
            return HandRank.FULL_HOUSE, most_common
        elif is_flush:
            return HandRank.FLUSH, values
        elif is_straight:
            return HandRank.STRAIGHT, values
        elif most_common and most_common[0][1] == 3:
            return HandRank.THREE_OF_A_KIND, most_common
        elif most_common and most_common[0][1] == 2 and len(most_common) > 1 and most_common[1][1] == 2:
            return HandRank.TWO_PAIR, most_common
        elif most_common and most_common[0][1] == 2:
            return HandRank.ONE_PAIR, most_common
        return HandRank.HIGH_CARD, values

    def check_straight(self, values):
        sorted_values = sorted(set(values))
        if len(sorted_values) < 5:
            return False
        for i in range(len(sorted_values) - 4):
            if sorted_values[i + 4] - sorted_values[i] == 4:
                return True
        return False

    def check_flush(self, suits):
        suit_count = Counter(suits)
        return any(count >= 5 for count in suit_count.values())

    def check_poker(self, most_common):
        if len(most_common) == 0:
            return None

        if most_common[0][1] == 4:
            return HandRank.POKER, most_common
        elif most_common[0][1] == 3 and most_common[1][1] == 2:
            return HandRank.FULL_HOUSE, most_common

        return None

    # Player Active & Inactive ===============

    def determine_winner_and_loser(self, player_windows, table_chips):
        all_hands = []
        for player_window in player_windows:
            if player_window.is_active:  # Only consider active players
                player_cards = [item.card for item in player_window.player_dragwidget.items if isinstance(item, Cards)]
                all_hands.append((player_window, player_cards))

        evaluated_hands = []
        for window, cards in all_hands:
            eval_cards = [card for card in cards if isinstance(card, Card)]
            hand_eval = self.eval_hand(eval_cards, table_chips)
            evaluated_hands.append((window, hand_eval))

            # Highlight wild cards
            for card in eval_cards:
                card_label = window.find_card_label(card)
                if card_label and hasattr(card_label, 'card'):
                    card.highlight_wild_card(card_label, is_face_up=True)

        evaluated_hands.sort(key=lambda x: x[1], reverse=True)
        winning_window, winning_hand = evaluated_hands[0]
        losing_window, losing_hand = evaluated_hands[-1]

        # Print hand ranks for all active players
        for window, hand_eval in evaluated_hands:
            hand_rank = hand_eval[0]
            print(
                f"determine_winner_and_loser - Player: Name {window.player_name} (player number {window.player_number}) with hand: {hand_eval}")
        print(
            f"determine_winner_and_loser - Winner: Name {winning_window.player_name} (player number {winning_window.player_number}) with hand: {winning_hand}")
        print(
            f"determine_winner_and_loser - Loser: Name {losing_window.player_name} (player number {losing_window.player_number}) with hand: {losing_hand}")

        return player_windows.index(winning_window), player_windows.index(losing_window)

    def get_hand_evaluation(self, player_window, table_chips):
        player_cards = [item.card for item in player_window.player_dragwidget.items if isinstance(item, Cards)]
        eval_cards = [card for card in player_cards if isinstance(card, Card)]
        return self.eval_hand(eval_cards, table_chips)

    def display_winner(self, winner_window):
        print(f"D1 display_winner - The winner is: Player {winner_window.player_number}")
        print(
            f"D1 display_winner - The winner is: Player {winner_window.player_name} index {winner_window.player_index} (player number {winner_window.player_number})")

    def update_side_chips(self, amount, game_window):
        print(f"D1-3 update_side_chips - Update side chips by {amount}. Current side chips: {self.side_chips}")
        self.side_chips += amount
        if self.side_chips < 0:
            self.side_chips = 0

        print(f"D2-3 update_side_chips - New side chips count: {self.side_chips}")

        # Update the side chip label in the GameWindow
        game_window.update_side_chip_label()

        # Emit signal if side chips have been updated
        self.side_chip_label_updated.emit(self.side_chips)

        # If no side chips are left, remove the side chip label
        if self.side_chips == 0:
            game_window.remove_side_chip_label()

    def update_player_chips(self, loser_window, player_index, amount):
        print(
            f"D1- Updating_player_chips for loser Player name: {loser_window.player_name} index: {player_index} (player number {loser_window.player_number}) with amount: {amount}")
        if 0 <= player_index < len(self.player_windows):
            self.player_windows[player_index].player_chips += amount
            if self.player_windows[player_index].player_chips < 0:
                self.player_windows[player_index].player_chips = 0
            print(
                f"D2- Updating_player_chips for loser Player name: {loser_window.player_name} index: {player_index} (player number {loser_window.player_number}) has {self.player_windows[player_index].player_chips} chips")
            self.player_chips_updated.emit(player_index, self.player_windows[player_index].player_chips)
        else:
            print(f"Invalid player index: {player_index} for updating chips.")

    def check_for_game_continuation(self):
        """Check if there's only one player left with chips or if the game needs to end."""
        active_players = [window for window in self.player_windows if window.is_active]
        if len(active_players) == 1:
            print("D1-2 check_for_game_continuation - Only one player left. Ending the game.")
            self.game_window.final_end_game()
        elif len(active_players) > 1:
            self.game_window.alert_next_hand()
        else:
            print("D2-2 check_for_game_continuation - No players left. Ending the game.")
            self.game_window.final_end_game()


class Flop:
    def __init__(self):
        self.cards = []

    def add_card(self, card):
        self.cards.append(card)

    def clear(self):
        self.cards = []


class GameWindow(QMainWindow):
    def __init__(self, app, num_players, player_names, player_windows, username, password, usernames, main_window, parent=None):
        try:
            super().__init__(parent)
            QMainWindow.__init__(self, parent)  # Initialize QMainWindow

            self.app = app
            self.num_players = num_players
            self.player_names = player_names
            # self.player_windows = player_windows
            self.player_windows = []
            self.username = username
            self.password = password
            self.usernames = usernames
            # self.passwords = passwords

            self.all_player_cards = {}  # Initialize with an empty dictionary for each player
            self.all_reveal_cards = []
            self.reveal_dragwidgets = []
            self.players = []

            self.main_window = main_window
            # self.server_socket = server_socket

            self.deck = Deck()

            print("GameWindow initialized with parameters:")
            print(f"num_players: {num_players}")
            print(f"player_names: {player_names}")
            print(f"username: {username}")
            print(f"usernames: {usernames}")

            # self.initialize_game()
            # self.player_index = 0

            self.player_windows = [
                PlayerWindow(
                    player_id=i + 1,
                    player_number=i,
                    # player_number=i + 1,
                    player_dragwidget=DragWidget(parent=None, max_items=6, min_items=5),
                    reveal_dragwidget=DragWidget(parent=None, max_items=5, min_items=4),
                    parent_window=self,
                    main_window=self,
                    index=i,
                    num_players=self.num_players,
                    player_name=self.player_names[i],
                    app=self.app,
                    is_active=True
                )
                for i in range(self.num_players)
            ]

            self.active_players = num_players
            self.player_statuses = {i: 'Active' for i in range(num_players)}

            # Initialize reveal_dragwidget and player_dragwidget instances
            self.reveal_dragwidget = DragWidget(self, 'reveal_dragwidget')
            self.player_dragwidget = DragWidget(self, 'player_dragwidget')

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
                self.deck
            )

            self.player_removed = False  # Initialize the flag to track player removal
            self.action_in_progress = False
            self.loser = None
            self.calling_player_number = None
            self.current_player_number = 1

            self.current_player_index = 0
            self.current_player = 0
            self.call_button_clicked = False
            self.turns_after_call = 0
            self.turns_after_pass = 0
            self.next_player_turn = None
            self.hand_in_progress = False  # Add this flag
            self.first_hand = True  # Added the first_hand attribute

            self.init_ui()

            # Connect signals from Dealer to update GUI
            self.dealer.table_chip_label_updated.connect(self.update_table_chip_label)
            self.dealer.side_chip_label_updated.connect(self.update_side_chip_label)
            self.dealer.player_chips_updated.connect(self.update_player_chips_label)

        except Exception as e:
            print(f"Error initializing GameWindow: {e}")
            import traceback
            traceback.print_exc()

        # # Start a thread to listen for messages from the server
        # threading.Thread(target=self.receive_message_from_server, daemon=True).start()
        #
        # # Start receiving messages
        # self.recv_thread = threading.Thread(target=self.receive_messages, daemon=True)
        # self.recv_thread.start()

        # Attempt to connect and login
        # self.connect_to_server(username, password)
        # self.connect_to_server()

    def init_ui(self):
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

        # Position already-created player windows
        for i, player_window in enumerate(self.player_windows):
            player_dragwidget = player_window.player_dragwidget
            reveal_dragwidget = player_window.reveal_dragwidget

            self.reveal_dragwidgets.append(reveal_dragwidget)

            # Adjust drag widget parent references if necessary
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

    def start_first_hand(self):
        self.deck = Deck()
        self.deck.shuffle()

        # Update the wild card based on current table chips
        self.deck.update_wild_card(self.table_chips)

        self.all_reveal_cards = self.deck.deal(5)
        self.all_player_cards = [self.deck.deal(5) for _ in range(self.num_players)]

        for player_window in self.player_windows:
            player_window.add_cards_to_widget(player_window.reveal_dragwidget, self.all_reveal_cards, reveal=True)
            player_window.add_cards_to_widget(player_window.player_dragwidget,
                                              self.all_player_cards[player_window.player_number - 1], reveal=False)

            # Set wild card color
            for card_widget in player_window.reveal_dragwidget.children():
                if hasattr(card_widget, 'card') and card_widget.card.is_wild:
                    card_widget.setStyleSheet("background-color: red;")

            player_window.set_initial_button_states(current_player_number=self.current_player_number,
                                                    call_button_clicked=False)

        # Log initial states for debugging
        # logging.debug("1-6 start_first_hand - num_players: {}".format(self.num_players))
        # logging.debug(f"2-6 start_first_hand - player_names: {[window.player_name for window in self.player_windows]}")
        # logging.debug(f"3-6 start_first_hand - all_reveal_cards: {self.all_reveal_cards}")
        # logging.debug(f"4-6 start_first_hand - all_player_cards: {self.all_player_cards}")

        print("1-6 start_first_hand - num_players: {}".format(self.num_players))
        print(f"2-6 start_first_hand - player_names: {[window.player_name for window in self.player_windows]}")
        print(f"3-6 start_first_hand - all_reveal_cards: {self.all_reveal_cards}")
        print(f"4-6 start_first_hand - all_player_cards: {self.all_player_cards}")

        # Determine and highlight the wild card
        for card in self.all_reveal_cards:
            if card.is_wild:
                logging.debug("5-6 start_first_hand - Card {} is wild and should be highlighted.".format(str(card)))
                for player_window in self.player_windows:
                    for card_widget in player_window.reveal_dragwidget.children():
                        if hasattr(card_widget, 'card') and card_widget.card == card:
                            card_widget.setStyleSheet("border: 2px solid red;")

        # logging.debug("6-6 start_first_hand - Setting initial button states for Players")

    def check_end_hand(self, player_number, table_chips):
        """Check if the hand should end based on the number of turns after the call or pass button was clicked."""
        try:
            logging.debug("check_end_hand - Checking if the hand should end.")
            if hasattr(self, 'call_button_clicked') and self.call_button_clicked:
                self.turns_after_call += 1
                print(f"DEBUG: Turns after call incremented to {self.turns_after_call}")
                logging.debug(f"check_end_hand - Turns after call incremented to {self.turns_after_call}")

                # Count the number of active players
                active_players = sum(1 for window in self.player_windows if window.is_active)
                logging.debug(f"check_end_hand - Active players remaining: {active_players}")
                logging.debug(f"check_end_hand - Turns after call: {self.turns_after_call}/{active_players}")

                if self.num_players == 2:
                    logging.debug("check_end_hand - Two players left. Handling reveal or pass.")
                    current_player_window = self.player_windows[self.calling_player_number - 1]

                    if current_player_window.reveal_button.isEnabled():
                        logging.debug("check_end_hand - Reveal button clicked.")
                        self.end_hand(table_chips)
                        return

                    if current_player_window.pass_button.isEnabled():
                        logging.debug("check_end_hand - Pass button clicked.")
                        return

                # If turns after call match the number of active players, end the hand
                if self.turns_after_call >= active_players:
                    logging.debug("check_end_hand - All required turns completed, ending hand.")
                    self.end_hand(table_chips)
                    return

            if hasattr(self, 'pass_button_clicked') and self.pass_button_clicked:
                self.turns_after_pass += 1
                print(f"DEBUG: Turns after pass incremented to {self.turns_after_pass}")  # Track the turn_after_pass
                logging.debug(f"check_end_hand - Turns after pass incremented to {self.turns_after_pass}")

                # Count the number of active players
                active_players = sum(1 for window in self.player_windows if window.is_active)
                logging.debug(f"check_end_hand - Active players remaining: {active_players}")
                logging.debug(f"check_end_hand - Turns after pass: {self.turns_after_pass}/{active_players}")

                # If turns after pass match the number of active players, end the hand
                if self.turns_after_pass >= active_players:
                    logging.debug("check_end_hand - All required turns completed, ending hand.")
                    self.end_hand(table_chips)
                    return

            logging.debug("check_end_hand - Hand not finished yet.")

            # Integrated check for ending the game when there's only one active player
            active_players_status = [window for window in self.player_windows if window.is_active]
            if len(active_players_status) == 1:
                logging.debug("check_end_hand - One active player remaining. Ending game.")
                self.final_end_game()
                return

        except Exception as e:
            logging.error(f"An error occurred in check_end_hand: {e}")
            import traceback
            traceback.print_exc()

    def next_hand(self):
        print("")
        print("\n--- next_hand method started ---")
        try:
            # Remove the loser before dealing cards and updating buttons
            if self.loser and self.loser in self.player_windows:
                print(f"Removing {self.loser.player_name} from the game.")
                self.loser.is_active = False
                self.loser = None  # Reset the loser attribute
                self.update_player_list()  # Update the player list in the UI

            # Ensure enough active players remain
            active_players = [p for p in self.player_windows if p.is_active]
            if len(active_players) < 2:
                print("Not enough players to continue the game.")
                return

            # Check if there are enough cards to deal
            required_cards = (len(active_players) * 5) + 5
            if len(self.deck.cards) < required_cards:
                self.deck = Deck()  # Reset the deck
                self.deck.update_wild_card(self.table_chips)
                self.deck.shuffle()

            # Deal new cards
            try:
                # self.call_button_clicked = False  # Reset call button state
                # self.turns_after_call = 0  # Reset the turn counter
                self.turns_after_call = 0  # Reset the turn counter
                self.turns_after_pass = 0  # Reset the turn counter
                self.call_button_clicked = False  # Reset call button state
                self.pass_button_clicked = False  # Reset pass button state

                self.all_reveal_cards = self.deck.deal(5)
                self.all_player_cards = {player.player_number: self.deck.deal(5) for player in active_players}
            except ValueError as e:
                self.deck = Deck()  # Reset the deck if there's an error
                self.deck.update_wild_card(self.table_chips)
                self.deck.shuffle()
                self.all_reveal_cards = self.deck.deal(5)
                self.all_player_cards = {player.player_number: self.deck.deal(5) for player in active_players}

            # Print statement to keep track of wildcard and table_chips
            print(f"next_hand1 - Table Chips: {self.table_chips}, Wildcard: {self.deck.wild_card_value}")

            # Clear and update widgets for each player
            for player_window in self.player_windows:
                if player_window.is_active:
                    player_window.add_cards_to_widget(player_window.reveal_dragwidget, self.all_reveal_cards,
                                                      reveal=True)
                    player_window.add_cards_to_widget(player_window.player_dragwidget,
                                                      self.all_player_cards[player_window.player_number], reveal=False)
                else:
                    # Ensure inactive players' reveal cards are face down
                    player_window.add_cards_to_widget(player_window.reveal_dragwidget, self.all_reveal_cards,
                                                      reveal=True)

            # Print statement to keep track of wildcard and table_chips
            print(f"next_hand2 - Table Chips: {self.table_chips}, Wildcard: {self.deck.wild_card_value}")

            # Re-enable and show the reveal buttons for all active players
            for player_window in self.player_windows:
                if player_window.is_active:  # check if the player is active before enabling buttons
                    player_window.reveal_button.setEnabled(True)
                    player_window.reveal_button.setVisible(True)
                    player_window.reveal_button.setStyleSheet("background-color: green;")

            # Set initial button states for each active player
            for player_window in self.player_windows:
                if player_window.is_active:  # Only set states if the player is active
                    player_window.set_initial_button_states(self.current_player_number, self.call_button_clicked)

            # Set the button states for the next active player
            if active_players:
                next_player_window = self.get_next_active_player(self.current_player_number)
                if next_player_window:
                    # Ensure the current player's turn is set correctly
                    self.current_player_number = next_player_window.player_number

                    # Set the button states for the next player
                    self.set_next_player_button_states(next_player_window)
                    # Debugging logs to verify button states
                    print(
                        f"Next player set to Player name: {next_player_window.player_name} (player number: {next_player_window.player_number})")
                    print(f"Reveal button enabled: {next_player_window.reveal_button.isEnabled()}, color: green")
                    print(f"Call button enabled: {next_player_window.call_button.isEnabled()}, color: green")
                    print(f"Pass button enabled: {next_player_window.pass_button.isEnabled()}, color: green")

        except Exception as e:
            print(f"Error in next_hand: {e}")
            import traceback
            traceback.print_exc()

    def end_hand(self, table_chips):
        try:
            print("\n--- end_hand method started ---")
            print(f"Current side chips: {self.dealer.side_chips}")

            self.hand_in_progress = False

            # Disable all players' buttons and set their colors to yellow
            for window in self.player_windows:
                window.reveal_button.setEnabled(False)
                window.reveal_button.setStyleSheet("background-color: yellow;")
                window.exchange_button.setEnabled(False)
                window.exchange_button.setStyleSheet("background-color: yellow;")
                window.call_button.setEnabled(False)
                window.call_button.setStyleSheet("background-color: yellow;")
                window.pass_button.setEnabled(False)
                window.pass_button.setStyleSheet("background-color: yellow;")

            # Determine winner and loser of the hand
            winner_index, loser_index = self.dealer.determine_winner_and_loser(self.player_windows, self.table_chips)
            winner_window = self.player_windows[winner_index]
            loser_window = self.player_windows[loser_index]
            winning_hand = self.dealer.get_hand_evaluation(winner_window, self.table_chips)
            losing_hand = self.dealer.get_hand_evaluation(loser_window, self.table_chips)
            print(
                f"end_hand - Winner name: {winner_window.player_name} index {winner_index} (player number: {winner_window.player_number}), Loser: {loser_window.player_name} index {loser_index} (player number: {loser_window.player_number})")

            # Update chips
            self.dealer.display_winner(winner_window)
            self.dealer.update_player_chips(loser_window, loser_index, -1)
            print("")
            print(
                f"end_hand - Updated player chips for Player name: {loser_window.player_name} index: {loser_index} (player number: {loser_window.player_number}): {loser_window.player_chips}")

            self.table_chips += 1  # Add the losing player's chip to the table chips
            self.update_table_chip_label(self.table_chips)  # Update the table chip label

            # Announce the winner and loser of the hand
            self.announce_hand_winner_and_loser(winner_window, loser_window, winning_hand, losing_hand, table_chips)

            # Handle side chip logic if needed
            if loser_window.player_chips <= 0:
                if self.side_chips > 0:
                    choice = self.ask_loser_to_take_side_chip(loser_window)
                    if choice == "Yes":
                        self.dealer.update_side_chips(-1, self)
                        self.dealer.update_player_chips(loser_window, loser_index, 1)
                        print(
                            f"Loser name: {loser_window.player_name} took the last side chip, now has {loser_window.player_chips} chips")
                    else:
                        self.inactive_player_from_game(loser_window, table_chips)
                        # Check if the game should end
                        active_players = [w for w in self.player_windows if w.is_active]
                        if len(active_players) == 1:
                            self.check_for_winner(winner_window, table_chips)
                            return
                else:
                    self.inactive_player_from_game(loser_window)
                    # Check if the game should end
                    active_players = [w for w in self.player_windows if w.is_active]
                    if len(active_players) == 1:
                        self.check_for_winner(winner_window, table_chips)
                        return

            self.dealer.check_for_game_continuation()

            # Reset turns_after_call and prepare for the next hand
            self.turns_after_call = 0

            # Update the side chip label
            self.update_side_chip_label()

        except Exception as e:
            print(f"An error occurred in end_hand: {e}")
            import traceback
            traceback.print_exc()

    # Gemini DO NOT DELETE ==============

    def get_next_active_player1ok(self, current_player_number):
        """
        Get the next active player after the given player number, wrapping around if necessary.
        """
        try:
            active_players = [player for player in self.player_windows if player.is_active]
            num_active_players = len(active_players)

            if num_active_players <= 1:
                return None  # If there's only one player left, or no players, return None

            current_player = next(
                (player for player in active_players if player.player_number == current_player_number), None)

            if not current_player:
                return active_players[0]  # If the current player is not found (shouldn't happen), start with the first player

            if self.side_chips == 0:
                loser_player = next(
                    (player for player in active_players if player.player_number == self.loser.player_number), None)
                if loser_player:
                     next_player = self.find_next_player_excluding_loser(current_player, loser_player, active_players)
                else:
                     next_player = self.find_next_player(current_player, active_players)
            else:
                 next_player = self.find_next_player(current_player, active_players)
            return next_player

        except Exception as e:
            print(f"Error in get_next_active_player: {e}")
            import traceback
            traceback.print_exc()
            return None

    def find_next_player(self, current_player, active_players):
        """
        Find the next active player in the list, wrapping around if necessary.
        """
        next_player_number = (current_player.player_number % len(self.player_windows)) + 1
        next_player = next((player for player in self.player_windows if
                            player.is_active and player.player_number == next_player_number),
                           None)
        if next_player is None:
           return next((player for player in active_players if player.player_number > current_player.player_number), active_players[0])
        return next_player

    def find_next_player_excluding_loser(self, current_player, loser_player, active_players):
        """
        Find the next active player in the list, excluding the loser player.
        """
        next_player = None
        if len(active_players) == 2:
            next_player_number = (current_player.player_number % len(self.player_windows)) + 1
            next_player = next((player for player in self.player_windows if
                                player.is_active and player.player_number == next_player_number), None)
            if next_player:
                return next_player
            else:
                return next(
                    (player for player in active_players if player.player_number > current_player.player_number),
                    active_players[0])
        elif len(active_players) == 3:
            if current_player.player_number == 1:
                if loser_player.player_number == 2:
                    next_player = next(
                        (player for player in self.player_windows if player.is_active and player.player_number == 3),
                        None)
                else:
                    next_player = next(
                        (player for player in self.player_windows if player.is_active and player.player_number == 2),
                        None)
            elif current_player.player_number == 2:
                if loser_player.player_number == 3:
                    next_player = next(
                        (player for player in self.player_windows if player.is_active and player.player_number == 1),
                        None)
                else:
                    next_player = next(
                        (player for player in self.player_windows if player.is_active and player.player_number == 3),
                        None)
            elif current_player.player_number == 3:
                if loser_player.player_number == 1:
                    next_player = next(
                        (player for player in self.player_windows if player.is_active and player.player_number == 2),
                        None)
                else:
                    next_player = next(
                        (player for player in self.player_windows if player.is_active and player.player_number == 1),
                        None)
            if next_player:
                return next_player
            else:
                return next(
                    (player for player in active_players if player.player_number > current_player.player_number),
                    active_players[0])

        elif len(active_players) == 4:
            if current_player.player_number == 1:
                if loser_player.player_number == 2:
                    next_player = next(
                        (player for player in self.player_windows if player.is_active and player.player_number == 3),
                        None)

                else:
                    next_player = next(
                        (player for player in self.player_windows if player.is_active and player.player_number == 2),
                        None)

            elif current_player.player_number == 2:
                if loser_player.player_number == 3:
                    next_player = next(
                        (player for player in self.player_windows if player.is_active and player.player_number == 4),
                        None)
                else:
                    next_player = next(
                        (player for player in self.player_windows if player.is_active and player.player_number == 3),
                        None)

            elif current_player.player_number == 3:
                if loser_player.player_number == 4:
                    next_player = next(
                        (player for player in self.player_windows if player.is_active and player.player_number == 1),
                        None)
                else:
                    next_player = next(
                        (player for player in self.player_windows if player.is_active and player.player_number == 4),
                        None)

            elif current_player.player_number == 4:
                if loser_player.player_number == 1:
                    next_player = next(
                        (player for player in self.player_windows if player.is_active and player.player_number == 2),
                        None)
                else:
                    next_player = next(
                        (player for player in self.player_windows if player.is_active and player.player_number == 1),
                        None)
            if next_player:
                return next_player
            else:
                return next(
                    (player for player in active_players if player.player_number > current_player.player_number),
                    active_players[0])
        else:
            next_player_number = (current_player.player_number % len(self.player_windows)) + 1
            next_player = next((player for player in self.player_windows if
                                player.is_active and player.player_number == next_player_number), None)
            if next_player:
                return next_player
            else:
                return next(
                    (player for player in active_players if player.player_number > current_player.player_number),
                    active_players[0])

    # Mistral ==================

    def get_next_active_player(self, current_player_number):
        """Gets the next active player after the given player number, wrapping around if necessary."""
        try:
            active_players = [player for player in self.player_windows if player.is_active]
            num_active_players = len(active_players)

            if num_active_players <= 1:
                return None  # If there's only one player left, or no players, return None

            current_player = next(
                (player for player in active_players if player.player_number == current_player_number), None)

            if not current_player:
                return active_players[
                    0]  # If the current player is not found (shouldn't happen), start with the first player

            next_player_number = (current_player.player_number % len(self.player_windows)) + 1
            next_player = next((player for player in self.player_windows if
                                player.is_active and player.player_number == next_player_number), None)
            if next_player:
                return next_player
            else:
                return next(
                    (player for player in active_players if player.player_number > current_player.player_number),
                    active_players[0])

        except Exception as e:
            print(f"Error in get_next_active_player: {e}")
            import traceback
            traceback.print_exc()
            return None

    # =====================

    def inactive_player_from_game(self, player, table_chips):
        """Marks a player as inactive when they have no chips left."""
        try:
            print(
                f"inactive_player_from_game - Marking Player name: {player.player_name} index: {player.player_index} (player number: {player.player_number}) as inactive.")
            player.is_active = False  # Set the player's status to inactive
            player.set_status_indicator('grey')  # Mark visually as inactive
            player.disable_buttons()  # Disable all buttons for the inactive player

            self.update_player_status(player.player_number, 'Inactive')  # Update the player status
            self.update_player_list()  # Refresh the player list in the UI to show status changes
            print(
                f"inactive_player_from_game - Player name: {player.player_name} (player number: {player.player_number}) has been marked as inactive.")

            # Get cards from player_dragwidget
            cards_to_redistribute = [card_label.card for card_label in player.player_dragwidget.items]

            # Clear the player_dragwidget but not the reveal_dragwidget
            player.player_dragwidget.clear()

            # Redistribute the cards to active players
            self.reveal_inactive_player_cards(cards_to_redistribute)
            # Reset turns_after_call counter
            self.turns_after_call = 0

            # Check if only one player is left active
            active_players = [w for w in self.player_windows if w.is_active]
            if len(active_players) == 1:
                self.check_for_winner(active_players[0], table_chips)  # End the game if only one player remains active

        except Exception as e:
            print(f"Error marking player as inactive: {e}")
            import traceback
            traceback.print_exc()

    def reveal_inactive_player_cards(self, cards_to_redistribute):
        """Distributes the collected cards from an inactive player."""
        active_players = [window for window in self.player_windows if window.is_active]
        num_active_players = len(active_players)

        if not active_players:
            return  # If there are no active players left, do not redistribute.

        # Ensure inactive players can see the active players' reveal cards
        for player_window in self.player_windows:
            if not player_window.is_active:
                player_window.add_cards_to_widget(player_window.reveal_dragwidget, self.all_reveal_cards,
                                                  reveal=False)

    # ==========

    def announce_hand_winner_and_loser(self, winner_window, loser_window, winning_hand, losing_hand, table_chips):
        try:
            # Announce the winner and loser of the hand
            alert_message = f"Winner: {winner_window.player_name} {winning_hand}\n"
            alert_message += f"Loser: {loser_window.player_name} {losing_hand}\n\n"
            alert_message += "Player cards:\n\n"
            for player_window in self.player_windows:
                player_name = player_window.player_name
                player_cards, reveal_cards = player_window.get_card_details()
                hand_rank = self.dealer.get_hand_evaluation(player_window, self.table_chips)
                alert_message += f"{player_name}: {player_cards} - {hand_rank}\n"

            QMessageBox.information(None, "announce_hand_winner_and_loser - Hand Result", alert_message)

        except Exception as e:
            print(f"An error occurred in announce_hand_winner_and_loser: {e}")
            import traceback
            traceback.print_exc()

    def check_for_winner(self, winner_window, table_chips):
        active_players = [window for window in self.player_windows if window.is_active]
        if len(active_players) == 1:
            winner = active_players[0]
            # Announce the winner
            alert_message = "Player cards:\n\n"
            for player_window in self.player_windows:
                player_name = player_window.player_name
                player_cards, reveal_cards = player_window.get_card_details()
                hand_rank = self.dealer.get_hand_evaluation(player_window, self.table_chips)
                alert_message += f"{player_name}: {player_cards} - {hand_rank}\n"

            QMessageBox.information(None, "GW check_for_winner",
                                        f"GW check_for_winner - Player {winner.player_name} wins the game with {winner.player_chips} chips!\n\n{alert_message}")

            self.final_end_game()

    def final_end_game(self):
        try:
            print("Finalizing game.")

            # Check for the number of active players directly in the final_end_game method
            active_players = [status for status in self.player_statuses.values() if status == 'Active']

            if len(active_players) == 1:
                # final_winner = self.player_windows[0]
                final_winner = [window for i, window in enumerate(self.player_windows) if self.player_statuses[i] == 'Active'][0]
                print(
                    f"final_end_game - The final winner is {final_winner.player_name} with {final_winner.player_chips} chips.")
                self.alert_next_hand()
            else:
                print("final_end_game - called with more than one player remaining, which should not happen.")

        except Exception as e:
            print(f"Error in final_end_game: {e}")

    def update_player_list(self):
        """Updates the player list in the GUI with player names and status indicators."""
        self.player_list_widget.clear()  # Clear the list widget

        for window in self.player_windows:
            player_number = window.player_number
            # player_index = window.player_index
            player_chips = window.player_chips  # Assuming you have this attribute in PlayerWindow

            # Ensure player_number exists in player_statuses
            if player_number not in self.player_statuses:
                self.player_statuses[player_number] = 'Active'

            # Create a list item with the player name, chip count, and status
            item_text = f"{window.player_name} - Chips: {player_chips} - {self.player_statuses[player_number]}"
            item = QListWidgetItem(item_text)

            # Set the appropriate status icon
            icon = QIcon()
            if self.player_statuses[player_number] == 'Active':
                icon.addPixmap(QPixmap("graphics/green_circle.png"))
            else:  # If status is anything other than 'Active', treat it as 'Inactive'
                icon.addPixmap(QPixmap("graphics/red_circle.png"))

            item.setIcon(icon)
            self.player_list_widget.addItem(item)

            print(
                f"update_player_list - Player name: {window.player_name} (player number: {window.player_number}) status: {self.player_statuses[player_number]}")

    def update_player_status(self, player_number, status):
        """Updates the status of a specific player and refreshes the player list."""
        # Set status using player number
        self.player_statuses[player_number] = status
        self.update_player_list()

    def set_next_player_button_states(self, next_player_window):
        try:
            # Disable all buttons for all players except the next player
            for player_window in self.player_windows:
                if player_window.player_number != next_player_window.player_number:
                    # Disable and color other players' buttons
                    player_window.reveal_button.setEnabled(False)
                    player_window.reveal_button.setStyleSheet("background-color: red;")  # Yellow for inactive
                    player_window.exchange_button.setEnabled(False)
                    player_window.exchange_button.setStyleSheet("background-color: red;")
                    player_window.call_button.setEnabled(False)
                    player_window.call_button.setStyleSheet("background-color: red;")
                    player_window.pass_button.setEnabled(False)
                    player_window.pass_button.setStyleSheet("background-color: red;")
                    print(
                        f"Player {player_window.player_name} (player number: {player_window.player_number}) buttons disabled and colored red.")
                else:
                    # Enable and color the next player's buttons
                    player_window.reveal_button.setEnabled(True)
                    player_window.reveal_button.setStyleSheet("background-color: green;")
                    player_window.reveal_button.setVisible(True)  # Ensure the reveal button is visible

                    player_window.exchange_button.setEnabled(False)
                    player_window.exchange_button.setStyleSheet("background-color: red;")

                    player_window.call_button.setEnabled(True)
                    player_window.call_button.setStyleSheet("background-color: green;")

                    player_window.pass_button.setEnabled(True)
                    player_window.pass_button.setStyleSheet("background-color: green;")
                    print(
                        f"Player {player_window.player_name} (player number: {player_window.player_number}) buttons disabled and colored red.")

            # Update the current player's number to the next player's number
            self.current_player_number = next_player_window.player_number

            # Debugging logs to verify button states
            print(
                f"set_next_player_button_states - Next player set to Player name: {next_player_window.player_name} (player number: {next_player_window.player_number})")
            print(f"Reveal button enabled: {next_player_window.reveal_button.isEnabled()}, color: green")
            print(f"Call button enabled: {next_player_window.call_button.isEnabled()}, color: green")
            print(f"Pass button enabled: {next_player_window.pass_button.isEnabled()}, color: green")

        except Exception as e:
            print(f"An error occurred in set_next_player_button_states: {e}")
            import traceback
            traceback.print_exc()

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
                "Next Hand - alert_next_hand",
                alert_message + "\nDo you want to continue to the next hand?",
                QMessageBox.Yes | QMessageBox.No
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

    def closeEvent(self, event):
        self.final_end_game()

    # ================

    def only_one_player_with_chips(self):
        players_with_chips = [player for player in self.player_windows if player.player_chips > 0]
        return len(players_with_chips) == 1

    def update_table_chip_label(self, table_chips=None):
        if table_chips is not None:
            self.table_chips = table_chips
        self.table_chip_label.setText(f"GW update_table_chip_label - Table Chips: {self.table_chips}")

        # Update the wild card based on the new table_chips value
        self.deck.update_wild_card(self.table_chips)

        # Print statement to keep track of table_chips and wildcard
        print(f"update_table_chip_label - Updated table_chips to {self.table_chips}")
        print(f"update_table_chip_label - Wild card updated to {self.deck.wild_card_value}")

        # Update the UI to reflect the new wild card
        self.update_wild_card_ui()

    def update_wild_card_ui(self):
        for player_window in self.player_windows:
            for card_widget in player_window.reveal_dragwidget.children():
                if hasattr(card_widget, 'card'):
                    card_widget.card.highlight_wild_card(card_widget, card_widget.card.face_up)
            for card_widget in player_window.player_dragwidget.children():
                if hasattr(card_widget, 'card'):
                    card_widget.card.highlight_wild_card(card_widget, card_widget.card.face_up)

        # Print statement to keep track of wildcard updates in the UI
        print(f"update_wild_card_ui - Updated wild card UI for all players")

    def update_player_chips_label(self, player_index, chips):
        if 0 <= player_index < len(self.player_windows):
            player_window = self.player_windows[player_index]
            print(
                f"GW- updating_player_chips_label for Player name: {player_window.player_name} with index: {player_index} (player number {player_window.player_number}) with chips: {chips}")
            player_window.update_chips_label(chips)
        else:
            print(f"Invalid player index: {player_index} for updating chips label.")

    def update_side_chip_label(self):
        """Update the side chips label in the GameWindow."""
        if hasattr(self, 'side_chip_label'):
            self.side_chip_label.setText(f"Side Chips: {self.dealer.side_chips}")
            print(f"Updated side chip label to {self.dealer.side_chips}")

    def ask_loser_to_take_side_chip(self, loser):
        """Prompts the loser to decide if they want to take a side chip."""
        if self.dealer.side_chips > 0:
            choice = QMessageBox.question(
                self,
                "ask_loser_to_take_side_chip - Take Side Chip?",
                f"{loser.player_name}, would you like to take a side chip?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            return "Yes" if choice == QMessageBox.Yes else "No"
        return "No"

    def remove_side_chip_label(self):
        """Removes the side chip label from the GUI."""
        self.side_chip_label.clear()
        print("remove_side_chip_label - from the GUI.")

    # ===========

    def update_all_cards(self, all_reveal_cards, all_player_cards):
        for i, player_window in enumerate(self.player_windows):
            for card in all_reveal_cards[i]:
                player_window.add_card(card, player_dragwidget=False)
            for card in all_player_cards[i]:
                player_window.add_card(card, player_dragwidget=True)

    def copy_reveal_dragwidget(self, source_dragwidget):
        new_dragwidget = DragWidget(parent=None, max_items=source_dragwidget.max_items,
                                    min_items=source_dragwidget.min_items)
        for item in source_dragwidget.items:
            new_dragwidget.add_item(item)
        return new_dragwidget

    def remove_card_from_all_reveal_dragwidgets(self, card, player_dragwidget):
        for reveal_dragwidget in self.reveal_dragwidgets:
            for item in reveal_dragwidget.findChildren(Cards):
                if item.card == card:
                    reveal_dragwidget.remove_item(item)
                    print(f"1639- Removed {card} from {reveal_dragwidget}.")
                    print(f"1640- Removed {card} from {self}.")
                    if player_dragwidget.drag_type == 'player_cards' and player_dragwidget.drag_item == item:
                        player_dragwidget.drag_type = None
                        player_dragwidget.drag_item = None  # reset the drag_item attribute

    def add_card_to_all_reveal_dragwidgets(self, card, exclude_widget=None):
        for reveal_dragwidget in self.reveal_dragwidgets:
            if reveal_dragwidget is not exclude_widget:
                if len(reveal_dragwidget.items) < reveal_dragwidget.maximum_cards():
                    card_label = Cards(card, reveal_dragwidget, reveal_dragwidget,
                                       face_down=False)  # Ensure face_down=False
                    reveal_dragwidget.add_item(card_label)
                else:
                    pass

    def print_all_cards(self):
        for player_window in self.player_windows:
            print(f"Player {player_window.player_number + 1} Reveal Cards:")
            for card in player_window.reveal_dragwidget.items:
                print(card.card.value,card.card.suit)
            print(f"Player {player_window.player_number + 1} Player Cards:")
            for card in player_window.player_dragwidget.items:
                print(card.card.value,card.card.suit)


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
        self.player_names = [input.text() if input.text().strip() else f"GoPlayer {i + 1}"
                             for i, input in enumerate(self.inputs)]
        super().accept()


def main():
    pass


if __name__ == '__main__':
    main()


