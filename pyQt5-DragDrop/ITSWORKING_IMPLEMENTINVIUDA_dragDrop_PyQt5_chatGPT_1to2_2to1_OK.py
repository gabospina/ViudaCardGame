from PyQt5.QtWidgets import QApplication, QHBoxLayout, QWidget, QPushButton, QLabel, QMainWindow, QVBoxLayout, QDockWidget
from PyQt5.QtCore import Qt, QMimeData, pyqtSignal
from PyQt5.QtGui import QDrag, QPixmap


class DragItem(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setContentsMargins(25, 5, 25, 5)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("border: 1px solid black;")
        # Store data separately from display label, but use label for default.
        self.data = self.text()

    def set_data(self, data):
        self.data = data

    def mouseMoveEvent(self, e):

        if e.buttons() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)

            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)

            drag.exec_(Qt.MoveAction)


class DragWidget(QWidget):
    orderChanged = pyqtSignal(list)

    def __init__(self, *args, max_items=None, orientation=Qt.Orientation.Vertical, **kwargs):
        super().__init__()
        self.setAcceptDrops(True)

        # Store the orientation for drag checks later.
        self.orientation = orientation

        if self.orientation == Qt.Orientation.Vertical:
            self.blayout = QVBoxLayout()
        else:
            self.blayout = QHBoxLayout()

        self.setLayout(self.blayout)

        self.max_items = max_items

    def dragEnterEvent(self, e):
        e.accept()

    def dropEvent(self, e):
        widget = e.source()
        source_dock = widget.parent()

        # Check if the source is another DragWidget and target is this DragWidget
        if isinstance(source_dock, DragWidget) and source_dock != self:
            target_dock = self

            # Check if the target dock has space for the dropped item
            if target_dock.blayout.count() < target_dock.max_items:
                # Remove the widget from the source dock
                source_dock.blayout.removeWidget(widget)
                # Add the widget to the target dock
                target_dock.blayout.addWidget(widget)
                target_dock.orderChanged.emit(target_dock.get_item_data())

        e.accept()

    def add_item(self, item):
        if self.max_items is None or self.blayout.count() < self.max_items:
            self.blayout.addWidget(item)

    def get_item_data(self):
        data = []
        for n in range(self.blayout.count()):
            # Get the widget at each index in turn.
            w = self.blayout.itemAt(n).widget()
            data.append(w.data)
        return data


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        # Create dock1 with maximum of 5 items and minimum of 4 items
        self.dock1 = QDockWidget("Dockable 1")
        self.drag1 = DragWidget(orientation=Qt.Orientation.Vertical, max_items=5, min_items=4)
        for n, l in enumerate(['A', 'B', 'C', 'D', 'E']):
            item = DragItem(l)
            item.set_data(n)
            self.drag1.add_item(item)
        self.dock1.setWidget(self.drag1)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock1)

        # Create dock2 with maximum of 6 items and minimum of 5 items
        self.dock2 = QDockWidget("Dockable 2")
        self.drag2 = DragWidget(orientation=Qt.Orientation.Vertical, max_items=6, min_items=5)
        for n, l in enumerate(['F', 'G', 'H', 'I', 'H']):
            item = DragItem(l)
            item.set_data(n + 4)  # Adjust data for the second set of items
            self.drag2.add_item(item)
        self.dock2.setWidget(self.drag2)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock2)


app = QApplication([])
w = MainWindow()
w.show()
app.exec_()
