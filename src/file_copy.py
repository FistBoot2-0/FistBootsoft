import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QComboBox, QProgressBar, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QIcon

class CopyThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, source, destination):
        super().__init__()
        self.source = source
        self.destination = destination
        self.is_running = True

    def run(self):
        try:
            total_size = os.path.getsize(self.source)
            copied_size = 0
            with open(self.source, 'rb') as src_file:
                with open(self.destination, 'wb') as dest_file:
                    while self.is_running:
                        chunk = src_file.read(4096)
                        if not chunk:
                            break
                        dest_file.write(chunk)
                        copied_size += len(chunk)
                        progress = int((copied_size / total_size) * 100)
                        self.progress.emit(progress)
            if self.is_running:
                self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        self.is_running = False

class FileCopyPage(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        back_button = QPushButton("Regresar")
        back_button.setIcon(QIcon.fromTheme("go-previous"))
        back_button.setStyleSheet("padding: 10px; border-radius: 5px; margin-bottom: 10px;")
        back_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        layout.addWidget(back_button)

        self.selected_file_label = QLabel("Archivo seleccionado: Ninguno")
        self.selected_file_label.setStyleSheet("margin-bottom: 10px; color: white;")
        layout.addWidget(self.selected_file_label)

        button_select_file = QPushButton("Seleccionar Archivo")
        button_select_file.setIcon(QIcon.fromTheme("document-open"))
        button_select_file.setStyleSheet("padding: 10px; border-radius: 5px; background-color: #3949AB; color: white;")
        button_select_file.clicked.connect(self.select_file)
        layout.addWidget(button_select_file)

        self.drive_selection_box = QComboBox()
        self.drive_selection_box.setStyleSheet("padding: 10px; border-radius: 5px; margin-top: 10px; margin-bottom: 10px;")
        layout.addWidget(self.drive_selection_box)

        self.progressBar = QProgressBar()
        self.progressBar.setStyleSheet("padding: 10px; border-radius: 5px;")
        layout.addWidget(self.progressBar)

        button_layout = QHBoxLayout()
        button_copy = QPushButton("Preparar unidad")
        button_copy.setIcon(QIcon.fromTheme("media-playback-start"))
        button_copy.setStyleSheet("padding: 10px; border-radius: 5px; background-color: #2E7D32; color: white;")
        button_copy.clicked.connect(self.start_copy)
        button_layout.addWidget(button_copy)

        button_cancel = QPushButton("Cancelar")
        button_cancel.setIcon(QIcon.fromTheme("process-stop"))
        button_cancel.setStyleSheet("padding: 10px; border-radius: 5px; background-color: #C62828; color: white;")
        button_cancel.clicked.connect(self.cancel_copy)
        button_layout.addWidget(button_cancel)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.populate_drive_selection()

    def populate_drive_selection(self):
        drive_list = ["Seleccionar unidad"]
        for drive_letter in range(65, 91):
            drive = chr(drive_letter) + ":\\"
            if os.path.exists(drive):
                drive_list.append(drive)
        self.drive_selection_box.addItems(drive_list)

    def select_file(self):
        file_dialog = QFileDialog.getOpenFileName(self, "Seleccionar Archivo", "", "Todos los archivos (*.*)")
        if file_dialog[0]:
            self.selected_file = file_dialog[0]
            self.selected_file_label.setText(f"Archivo seleccionado: {os.path.basename(self.selected_file)}")

    def start_copy(self):
        selected_drive = self.drive_selection_box.currentText()
        if selected_drive == "Seleccionar unidad" or not hasattr(self, 'selected_file'):
            QMessageBox.critical(self, "Error", "Selecciona un archivo y una unidad")
            return

        self.copy_thread = CopyThread(self.selected_file, os.path.join(selected_drive, os.path.basename(self.selected_file)))
        self.copy_thread.progress.connect(self.update_progress)
        self.copy_thread.finished.connect(self.copy_finished)
        self.copy_thread.error.connect(self.show_error)
        self.copy_thread.start()

    def cancel_copy(self):
        if hasattr(self, 'copy_thread'):
            self.copy_thread.stop()

    def update_progress(self, value):
        self.progressBar.setValue(value)

    def copy_finished(self):
        QMessageBox.information(self, "Finalizado", "Copia completada")
        self.progressBar.setValue(0)

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)
        self.progressBar.setValue(0)
