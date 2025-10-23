from PyQt5.QtWidgets import QApplication, QHBoxLayout, QWidget, QPushButton, QLabel, QMainWindow, QVBoxLayout, QDockWidget
from PyQt5.QtCore import Qt, QMimeData, pyqtSignal
from PyQt5.QtGui import QDrag, QPixmap

class DragItem(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setContentsMargins(25, 5, 25, 5)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("border: 1px solid black;")
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

    def __init__(self, *args, orientation=Qt.Orientation.Vertical, max_items: int = None, **kwargs):
        super().__init__()
        self.setAcceptDrops(True)
        self.orientation = orientation
        self.max_items = max_items
        self.item_count = 0

        if self.orientation == Qt.Orientation.Vertical:
            self.blayout = QVBoxLayout()
        else:
            self.blayout = QHBoxLayout()

        self.setLayout(self.blayout)

    def dragEnterEvent(self, e):
        e.accept()

    def dropEvent(self, e):
        pos = e.pos()
        widget = e.source()

        if self.max_items is not None and self.item_count >= self.max_items:
            print("Max items reached")
            e.ignore()
            return

        for n in range(self.blayout.count()):
            w = self.blayout.itemAt(n).widget()
            if self.orientation == Qt.Orientation.Vertical:
                drop_here = pos.y() < w.y() + w.size().height() // 2
            else:
                drop_here = pos.x() < w.x() + w.size().width() // 2

            if drop_here:
                if widget.text() == 'K':
                    # Replace 'K' with the dropped item
                    self.blayout.replaceWidget(w, widget)
                    self.orderChanged.emit(self.get_item_data())
                    self.item_count += 1
                else:
                    self.blayout.insertWidget(n, widget)
                    self.orderChanged.emit(self.get_item_data())
                    self.item_count += 1
                break

        e.accept()

    def add_item(self, item):
        if self.max_items is not None and self.item_count >= self.max_items:
            return
        self.blayout.addWidget(item)
        self.item_count += 1

    def remove_item(self, item):
        self.blayout.removeWidget(item)
        item.deleteLater()
        self.item_count -= 1

    def get_item_data(self):
        data = []
        for n in range(self.blayout.count()):
            w = self.blayout.itemAt(n).widget()
            data.append(w.data)
        return data

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dock1 = QDockWidget("Dockable 1")
        self.drag1 = DragWidget(orientation=Qt.Orientation.Vertical, max_items=5)
        for n, l in enumerate(['A', 'B', 'C', 'D', 'E']):
            item = DragItem(l)
            item.set_data(n)
            self.drag1.add_item(item)
        self.dock1.setWidget(self.drag1)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock1)

        self.dock2 = QDockWidget("Dockable 2")
        self.drag2 = DragWidget(orientation=Qt.Orientation.Vertical, max_items=6)
        for n, l in enumerate(['F', 'G', 'H', 'I', 'J']):
            item = DragItem(l)
            item.set_data(n)
            self.drag2.add_item(item)

        self.dock2.setWidget(self.drag2)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock2)

        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.drag1.orderChanged.connect(self.handle_drag1_drop)
        self.drag2.orderChanged.connect(self.handle_drag2_drop)

    def handle_drag1_drop(self, item_data):
        if len(item_data) == 5 and self.drag2.item_count < 6:
            item = DragItem(item_data[-1])
            item.set_data(item_data[-1])
            self.drag2.add_item(item)

            # Remove dropped item from dock1
            self.drag1.remove_item(self.drag1.blayout.itemAt(len(item_data) - 1).widget())

    def handle_drag2_drop(self, item_data):
        pass

app = QApplication([])
w = MainWindow()
w.show()
app.exec_()
