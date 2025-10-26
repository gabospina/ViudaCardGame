import json
import logging
import traceback
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from core.card import Card


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

    def dropEvent1(self, event):
        from ui.card_widget import CardWidget

        logging.debug("dropEvent started")
        if not event.mimeData().hasText():
            event.ignore()
            return

        try:
            source_widget = event.source().parent()

            if source_widget == self:
                # This is an INTERNAL drag for rearrangement. This is always allowed.
                print("Handling rearrangement within player_dragwidget")
                self.rearrange_player_cards(event)
                event.acceptProposedAction()
            else:
                # This is an EXTERNAL drop from another widget.
                # --- NEW TURN CHECK LOGIC ---
                if not self.parent_window.is_current_player_turn():
                    print("Drop rejected: Not the current player's turn.")
                    event.ignore()
                    return
                # --- END OF NEW LOGIC ---

                print("Handling external drop from another widget")
                dragged_item = (
                    source_widget.drag_item
                    if hasattr(source_widget, "drag_item")
                    else None
                )

                if dragged_item and isinstance(dragged_item, CardWidget):
                    source_widget.remove_item(dragged_item)
                    self.add_item(dragged_item)
                    dragged_item.setParent(self)
                    dragged_item.show()
                    dragged_item.handle_card_movement()
                    event.acceptProposedAction()
                else:
                    print("Error: Could not find the source CardWidget for the drop.")
                    event.ignore()

        except Exception as e:
            logging.error(f"DropEvent error: {str(e)}")
            traceback.print_exc()
            event.ignore()

    # In DragWidget class (ui/drag_widget.py)

    def dropEvent2(self, event):
        from ui.card_widget import CardWidget

        logging.debug("dropEvent started")
        if not event.mimeData().hasText():
            event.ignore()
            return

        try:
            source_widget = event.source().parent()

            if source_widget == self:
                # Internal drag for rearrangement is always allowed.
                print("Handling rearrangement within player_dragwidget")
                self.rearrange_player_cards(event)
                event.acceptProposedAction()
            else:
                # This is an EXTERNAL drop from another widget.
                if not self.parent_window.is_current_player_turn():
                    print("Drop rejected: Not the current player's turn.")
                    event.ignore()
                    return

                # --- NEW RULE CHECK ---
                # Are any cards in this widget currently face down?
                for item in self.items:
                    if item.face_down:
                        print(
                            "Drop rejected: Cannot drop onto a widget with face-down cards."
                        )
                        event.ignore()
                        return
                # --- END OF NEW RULE ---

                print("Handling external drop from another widget")
                dragged_item = (
                    source_widget.drag_item
                    if hasattr(source_widget, "drag_item")
                    else None
                )

                if dragged_item and isinstance(dragged_item, CardWidget):
                    source_widget.remove_item(dragged_item)
                    self.add_item(dragged_item)
                    dragged_item.setParent(self)
                    dragged_item.show()
                    dragged_item.handle_card_movement()
                    event.acceptProposedAction()
                else:
                    print("Error: Could not find the source CardWidget for the drop.")
                    event.ignore()

        except Exception as e:
            logging.error(f"DropEvent error: {str(e)}")
            import traceback

            traceback.print_exc()
            event.ignore()

    # In DragWidget class
    def dropEvent(self, event):
        from ui.card_widget import CardWidget

        logging.debug("dropEvent started")

        if not event.mimeData().hasText():
            event.ignore()
            return

        try:
            source_widget = event.source().parent()

            # --- FINAL, CORRECTED LOGIC ---
            if source_widget == self:
                # This is an INTERNAL DRAG.
                # Only rearrange the cards and do nothing else.
                print("Handling rearrangement. No game action.")
                self.rearrange_player_cards(event)
                event.acceptProposedAction()
                return  # IMPORTANT: Stop all further processing.

            # If we reach here, it must be an EXTERNAL DROP.
            # Now, we apply all the game rules for an external drop.
            if not self.parent_window.is_current_player_turn():
                print("Drop rejected: Not the current player's turn.")
                event.ignore()
                return

            for item in self.items:
                if item.face_down:
                    print(
                        "Drop rejected: Cannot drop onto a widget with face-down cards."
                    )
                    event.ignore()
                    return

            dragged_item = getattr(source_widget, "drag_item", None)

            if dragged_item and isinstance(dragged_item, CardWidget):
                # This is a valid external drop. Physically move the widget.
                source_widget.remove_item(dragged_item)
                self.add_item(dragged_item)
                dragged_item.setParent(self)
                dragged_item.show()

                # Now that the move is complete, call the game logic handler ONCE.
                dragged_item.handle_card_movement()
                event.acceptProposedAction()
            else:
                print("Error: Could not find the source CardWidget for the drop.")
                event.ignore()

        except Exception as e:
            logging.error(f"DropEvent error: {str(e)}")
            import traceback

            traceback.print_exc()
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
