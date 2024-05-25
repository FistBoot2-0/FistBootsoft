import sys
import os
import shutil
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QComboBox, QProgressBar, QMessageBox, QStackedWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap
from qt_material import apply_stylesheet

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

class IsoBurnThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, iso, drive):
        super().__init__()
        self.iso = iso
        self.drive = drive
        self.is_running = True

    def run(self):
        try:
            if sys.platform.startswith("linux"):
                self.burn_iso_linux()
            elif sys.platform == "win32":
                self.burn_iso_windows()
            if self.is_running:
                self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def burn_iso_linux(self):
        command = f"dd if={self.iso} of={self.drive} bs=4M status=progress"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for line in process.stderr:
            if not self.is_running:
                process.terminate()
                break
            if b'bytes' in line:
                parts = line.strip().split()
                copied = int(parts[0])
                self.progress.emit(copied)
        process.wait()

    def burn_iso_windows(self):
        try:
            script = f"""
            select disk {self.drive}
            clean
            create partition primary
            select partition 1
            active
            format fs=ntfs quick
            assign letter={self.drive}
            exit
            """
            with open("diskpart_script.txt", "w") as file:
                file.write(script)
            subprocess.run(["diskpart", "/s", "diskpart_script.txt"], check=True)
            subprocess.run(["xcopy", self.iso, f"{self.drive}:\\", "/s", "/e", "/f"], check=True)
            os.remove("diskpart_script.txt")
        except subprocess.CalledProcessError as e:
            self.error.emit(str(e))
        except PermissionError as e:
            self.error.emit("Permisos insuficientes. Por favor, ejecute la aplicación como administrador.")
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        self.is_running = False

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("FistBoot")
        self.setWindowIcon(QIcon("./img/Logo.ico"))
        self.setGeometry(300, 300 , 600, 400)

        self.stacked_widget = QStackedWidget()
        
        self.main_menu = self.create_main_menu()
        self.file_copy_page = self.create_file_copy_page()
        self.iso_burn_page = self.create_iso_burn_page()

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
        label.setStyleSheet("font-size: 20px; margin-bottom: 20px;")
        layout.addWidget(label)

        button_copy = QPushButton("Copiar Archivos")
        button_copy.setIcon(QIcon.fromTheme("document-open"))
        button_copy.setStyleSheet("padding: 10px; border-radius: 5px;")
        button_copy.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.file_copy_page))
        layout.addWidget(button_copy)

        button_burn = QPushButton("Grabar ISO")
        button_burn.setIcon(QIcon.fromTheme("media-record"))
        button_burn.setStyleSheet("padding: 10px; border-radius: 5px;")
        button_burn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.iso_burn_page))
        layout.addWidget(button_burn)

        widget.setLayout(layout)
        return widget

    def create_file_copy_page(self):
        widget = QWidget()
        layout = QVBoxLayout()

        back_button = QPushButton("Regresar")
        back_button.setIcon(QIcon.fromTheme("go-previous"))
        back_button.setStyleSheet("padding: 10px; border-radius: 5px; margin-bottom: 10px;")
        back_button.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.main_menu))
        layout.addWidget(back_button)


        self.selected_file_label = QLabel("Archivo seleccionado: Ninguno")
        self.selected_file_label.setStyleSheet("margin-bottom: 10px;")
        layout.addWidget(self.selected_file_label)

        button_select_file = QPushButton("Seleccionar Archivo")
        button_select_file.setIcon(QIcon.fromTheme("document-open"))
        button_select_file.setStyleSheet("padding: 10px; border-radius: 5px;")
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
        button_copy.setStyleSheet("padding: 10px; border-radius: 5px;")
        button_copy.clicked.connect(self.start_copy)
        button_layout.addWidget(button_copy)

        button_cancel = QPushButton("Cancelar")
        button_cancel.setIcon(QIcon.fromTheme("process-stop"))
        button_cancel.setStyleSheet("padding: 10px; border-radius: 5px;")
        button_cancel.clicked.connect(self.cancel_copy)
        button_layout.addWidget(button_cancel)

        layout.addLayout(button_layout)
        widget.setLayout(layout)
        return widget

    def create_iso_burn_page(self):
        widget = QWidget()
        layout = QVBoxLayout()

        back_button = QPushButton("Regresar")
        back_button.setIcon(QIcon.fromTheme("go-previous"))
        back_button.setStyleSheet("padding: 10px; border-radius: 5px; margin-bottom: 10px;")
        back_button.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.main_menu))
        layout.addWidget(back_button)


        self.selected_iso_label = QLabel("ISO seleccionado: Ninguno")
        self.selected_iso_label.setStyleSheet("margin-bottom: 10px;")
        layout.addWidget(self.selected_iso_label)

        button_select_iso = QPushButton("Seleccionar ISO")
        button_select_iso.setIcon(QIcon.fromTheme("document-open"))
        button_select_iso.setStyleSheet("padding: 10px; border-radius: 5px;")
        button_select_iso.clicked.connect(self.select_iso)
        layout.addWidget(button_select_iso)

        self.iso_drive_selection_box = QComboBox()
        self.iso_drive_selection_box.setStyleSheet("padding: 10px; border-radius: 5px; margin-top: 10px; margin-bottom: 10px;")
        layout.addWidget(self.iso_drive_selection_box)

        self.iso_progressBar = QProgressBar()
        self.iso_progressBar.setStyleSheet("padding: 10px; border-radius: 5px;")
        layout.addWidget(self.iso_progressBar)

        button_layout = QHBoxLayout()
        button_burn = QPushButton("Grabar ISO")
        button_burn.setIcon(QIcon.fromTheme("media-record"))
        button_burn.setStyleSheet("padding: 10px; border-radius: 5px;")
        button_burn.clicked.connect(self.start_burn_iso)
        button_layout.addWidget(button_burn)

        button_cancel = QPushButton("Cancelar")
        button_cancel.setIcon(QIcon.fromTheme("process-stop"))
        button_cancel.setStyleSheet("padding: 10px; border-radius: 5px;")
        button_cancel.clicked.connect(self.cancel_burn_iso)
        button_layout.addWidget(button_cancel)

        layout.addLayout(button_layout)
        widget.setLayout(layout)
        return widget

    def populate_drive_selection(self):
        drive_list = ["Seleccionar unidad"]
        for drive_letter in range(65, 91):
            drive = chr(drive_letter) + ":\\"
            if os.path.exists(drive):
                drive_list.append(drive)
        self.drive_selection_box.addItems(drive_list)
        self.iso_drive_selection_box.addItems(drive_list)

    def select_file(self):
        file_dialog = QFileDialog.getOpenFileName(self, "Seleccionar Archivo", "", "Todos los archivos (*.*)")
        if file_dialog[0]:
            self.selected_file = file_dialog[0]
            self.selected_file_label.setText(f"Archivo seleccionado: {os.path.basename(self.selected_file)}")

    def select_iso(self):
        file_dialog = QFileDialog.getOpenFileName(self, "Seleccionar ISO", "", "Imágenes ISO (*.iso)")
        if file_dialog[0]:
            self.selected_iso = file_dialog[0]
            self.selected_iso_label.setText(f"ISO seleccionado: {os.path.basename(self.selected_iso)}")

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

    def start_burn_iso(self):
        selected_drive = self.iso_drive_selection_box.currentText()
        if selected_drive == "Seleccionar unidad" or not hasattr(self, 'selected_iso'):
            QMessageBox.critical(self, "Error", "Selecciona un ISO y una unidad")
            return

        self.iso_burn_thread = IsoBurnThread(self.selected_iso, selected_drive)
        self.iso_burn_thread.progress.connect(self.update_iso_progress)
        self.iso_burn_thread.finished.connect(self.iso_burn_finished)
        self.iso_burn_thread.error.connect(self.show_error)
        try:
            self.iso_burn_thread.start()
        except PermissionError as e:
            QMessageBox.critical(self, "Error", "Permisos insuficientes. Por favor, ejecuta la aplicación como administrador.")
        except Exception as e:
            self.show_error(str(e))

    def cancel_burn_iso(self):
        if hasattr(self, 'iso_burn_thread'):
            self.iso_burn_thread.stop()

    def update_progress(self, value):
        self.progressBar.setValue(value)

    def update_iso_progress(self, value):
        self.iso_progressBar.setValue(value)

    def copy_finished(self):
        QMessageBox.information(self, "Finalizado", "Copia completada")
        self.progressBar.setValue(0)

    def iso_burn_finished(self):
        QMessageBox.information(self, "Finalizado", "ISO grabada con éxito")
        self.iso_progressBar.setValue(0)

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)
        self.progressBar.setValue(0)
        self.iso_progressBar.setValue(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.populate_drive_selection()  # Llamar después de definir los QComboBox
    apply_stylesheet(app, theme='dark_teal.xml')
    sys.exit(app.exec_())
