import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app import StickyTabsApp


def resource_path(relative_path):
    """Return the correct asset path for source and packaged builds."""

    if hasattr(sys, "_MEIPASS"):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent

    return base_path / relative_path


def main():
    app = QApplication(sys.argv)

    app.setWindowIcon(
        QIcon(str(resource_path("assets/stickytabs_icon.ico")))
    )

    window = StickyTabsApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()