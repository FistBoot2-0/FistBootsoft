import sys
import ctypes
from PyQt5.QtWidgets import QApplication
from qt_material import apply_stylesheet
from src.main_menu import MainWindow

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == "__main__":
    if is_admin():
        app = QApplication(sys.argv)
        window = MainWindow()
        apply_stylesheet(app, theme='dark_teal.xml')
        sys.exit(app.exec_())
    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
