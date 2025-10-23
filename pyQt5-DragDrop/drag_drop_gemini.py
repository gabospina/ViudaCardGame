from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import Qt

class DragDropWidget(QWidget):
    def __init__(self):
        super().__init__()
        try:
            self.init_ui()
            print("DragDropWidget initialized 1 of 11")  # Print after initialization
        except Exception as e:
            print(f"An error occurred during initialization: {e}")

    def init_ui(self):
        self.setWindowTitle("Drag and Drop Sample")
        print("Setting up UI... 2")  # Print before creating UI elements

        # Create main layout
        main_layout = QVBoxLayout(self)
        print("Created main layout 3")  # Print after creating main layout

        # Create frames
        self.frame1 = QWidget()
        self.frame2 = QWidget()
        print("Created frames 4")  # Print after creating frames

        # Layout for frames
        frame_layout = QHBoxLayout()
        frame_layout.addWidget(self.frame1)
        frame_layout.addWidget(self.frame2)

        main_layout.addLayout(frame_layout)
        print("Added frame layout to main layout 5")  # Print after adding frame layout

        # Create labels with text
        self.label1 = QLabel("Label 1")
        self.label2 = QLabel("Label 2")
        self.label3 = QLabel("Label 3")
        print("Created labels 6")  # Print after creating labels

        # Layout for labels in frames
        frame1_layout = QVBoxLayout(self.frame1)
        frame1_layout.addWidget(self.label1)
        frame1_layout.addWidget(self.label2)
        print("Added labels to frame1 layout 7")  # Print after adding labels to frame1

        frame2_layout = QVBoxLayout(self.frame2)
        frame2_layout.addWidget(self.label3)
        print("Added label3 to frame2 layout 8")  # Print after adding label3 to frame2

        # Set layout for the main window
        self.setLayout(main_layout)
        print("Set layout for main window 9")  # Print after adding layout

        # Install event filters on labels (uncomment for testing eventFilter)
        self.label1.installEventFilter(self)
        self.label2.installEventFilter(self)
        self.label3.installEventFilter(self)
        print("Installed event filters for labels 10")

    def eventFilter(self, source, event):
        # print("eventFilter 11")
        # Check if event is for a label and it's a mouse press
        # if event.type() == Qt.MouseButtonPress and source in (self.label1, self.label2, self.label3):
        #     print("Mouse press detected on: 11", source)
        #
        #     # Handle the event (e.g., initiate drag) here
        #     # (This part will be implemented later)
        #     #
        #     # Indicate that the event is handled
        #     return True  # Consumed the event, don't pass on for further processing

        # Pass on unhandled events to the parent's eventFilter
        return False  # Explicitly indicate unhandled events


if __name__ == "__main__":
    try:
        app = QApplication([])
        widget = DragDropWidget()
        widget.show()
        app.exec_()
    except Exception as e:
        print(f"An error occurred: {e}")
