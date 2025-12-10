import sys
from PyQt6.QtWidgets import QApplication
from gui import BeePlanWindow

def main():
    app = QApplication(sys.argv)
    window = BeePlanWindow()
    window.show()
    
    # PyQt6'da alt tire (_) YOKTUR:
    sys.exit(app.exec()) 

if __name__ == "__main__":
    main()