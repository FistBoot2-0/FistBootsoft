import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QStackedWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from src.file_copy import FileCopyPage
from src.iso_burn import IsoBurnPage

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("FistBoot")
        self.setWindowIcon(QIcon("./img/Logo.ico"))
        self.setGeometry(300, 300, 600, 400)

        self.stacked_widget = QStackedWidget()

        self.main_menu = self.create_main_menu()
        self.file_copy_page = FileCopyPage(self.stacked_widget)
        self.iso_burn_page = IsoBurnPage(self.stacked_widget)

        self.stacked_widget.addWidget(self.main_menu)
        self.stacked_widget.addWidget(self.file_copy_page)
        self.stacked_widget.addWidget(self.iso_burn_page)

        layout = QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

        self.show()

    def create_main_menu(self):
        widget = QWidget()
        layout = QVBoxLayout()

        label = QLabel("Selecciona una opción:")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 15px; margin-bottom: 20px; color: white;")
        layout.addWidget(label)

        button_copy = QPushButton("Copiar Archivos")
        button_copy.setIcon(QIcon.fromTheme("document-open"))
        button_copy.setStyleSheet("padding: 8px; border-radius: 15px; background-color: #3949AB; color: white;")
        button_copy.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.file_copy_page))
        layout.addWidget(button_copy)

        button_burn = QPushButton("Grabar ISO")
        button_burn.setIcon(QIcon.fromTheme("media-record"))
        button_burn.setStyleSheet("padding: 8px; border-radius: 15px; background-color: #2E7D32; color: white;")
        button_burn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.iso_burn_page))
        layout.addWidget(button_burn)

        widget.setLayout(layout)
        return widget
