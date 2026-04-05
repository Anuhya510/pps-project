# quiz_app/main.py
# Application Entry Point

import sys
from pathlib import Path

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

# Import the main function from main_window
from gui.main_window import main


if __name__ == "__main__":
    main()