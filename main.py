import sys

import traceback
import logging
from PyQt5.QtWidgets import QApplication, QDialog

# Import our main window and the dialog from the UI module
from ui.game_window import GameWindow, PlayerNamesDialog


def main():
    # Configure logging right at the very beginning
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    logging.info("Starting the game application.")

    app = QApplication([])

    num_players = 4

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
