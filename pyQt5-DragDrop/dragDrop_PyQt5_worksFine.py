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

    def __init__(self, *args, orientation=Qt.Orientation.Vertical, **kwargs):
        super().__init__()
        self.setAcceptDrops(True)

        # Store the orientation for drag checks later.
        self.orientation = orientation

        if self.orientation == Qt.Orientation.Vertical:
            self.blayout = QVBoxLayout()
        else:
            self.blayout = QHBoxLayout()

        self.setLayout(self.blayout)

    def dragEnterEvent(self, e):
        print("Drag enter event")
        e.accept()

    def dropEvent(self, e):
        print("Drop event")
        pos = e.pos()
        widget = e.source()

        # Remove the widget from its original position
        self.blayout.removeWidget(widget)

        for n in range(self.blayout.count()):
            # Get the widget at each index in turn.
            w = self.blayout.itemAt(n).widget()
            if self.orientation == Qt.Orientation.Vertical:
                # Drag drop vertically.
                drop_here = pos.y() < w.y() + w.size().height() // 2
            else:
                # Drag drop horizontally.
                drop_here = pos.x() < w.x() + w.size().width() // 2

            if drop_here:
                # We didn't drag past this widget.
                # insert to the left of it.
                self.blayout.insertWidget(n, widget)
                self.orderChanged.emit(self.get_item_data())
                break

        e.accept()

    def add_item(self, item):
        self.blayout.addWidget(item)

    def get_item_data(self):
        data = []
        for n in range(self.blayout.count()):
            # Get the widget at each index in turn.
            w = self.blayout.itemAt(n).widget()
            data.append(w.data)
        return data

    def remove_item(self, item):
        self.blayout.removeWidget(item)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # Create Dock Widgets
        self.dock_widgets = {}
        for name, items in [('Dock 1', ['A', 'B', 'C', 'D', 'E']), ('Dock 2', ['F', 'G', 'H', 'I', 'J'])]:
            dock_widget = QDockWidget(name)
            drag_widget = DragWidget(orientation=Qt.Orientation.Horizontal)
            for n, l in enumerate(items):
                item = DragItem(l)
                item.set_data(n)  # Store the data.
                drag_widget.add_item(item)
            dock_widget.setWidget(drag_widget)
            self.addDockWidget(Qt.LeftDockWidgetArea, dock_widget)
            self.dock_widgets[name] = drag_widget

        # Print out the changed order.
        for dock_widget in self.dock_widgets.values():
            dock_widget.orderChanged.connect(self.check_max_items)

    def check_max_items(self):
        dock2_items = self.dock_widgets['Dock 2'].get_items()
        if len(dock2_items) > 6:
            excess_items = dock2_items[6:]
            for item in excess_items:
                self.dock_widgets['Dock 1'].add_item(item)
                self.dock_widgets['Dock 2'].remove_item(item)



app = QApplication([])
w = MainWindow()
w.show()
app.exec_()
