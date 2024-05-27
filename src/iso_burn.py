import os
import subprocess
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QComboBox, QProgressBar, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QIcon
import sys 

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
            drive_number = self.get_drive_number(self.drive)
            if drive_number is None:
                raise Exception(f"No se pudo encontrar el número del disco para la unidad {self.drive}")
            script = f"""
            select disk {drive_number}
            clean
            create partition primary
            select partition 1
            active
            format fs=ntfs quick
            assign letter={self.drive[0]}
            exit
            """
            with open("diskpart_script.txt", "w") as file:
                file.write(script)
            subprocess.run(["diskpart", "/s", "diskpart_script.txt"], check=True)
            subprocess.run(["xcopy", self.iso, f"{self.drive}", "/s", "/e", "/f"], check=True)
            os.remove("diskpart_script.txt")
        except subprocess.CalledProcessError as e:
            self.error.emit(str(e))
        except PermissionError as e:
            self.error.emit("Permisos insuficientes. Por favor, ejecute la aplicación como administrador.")
        except Exception as e:
            self.error.emit(str(e))

    def get_drive_number(self, drive_letter):
        command = "wmic logicaldisk get caption,deviceid,drivetype"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if drive_letter in line and '2' in line:  # DriveType 2 means removable drive
                drive_id = line.split()[1]
                command = f"wmic diskdrive where \"DeviceID='{drive_id}'\" get index"
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                for line in result.stdout.splitlines():
                    if line.strip().isdigit():
                        return line.strip()
        return None

    def stop(self):
        self.is_running = False

class IsoBurnPage(QWidget):
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

        self.selected_iso_label = QLabel("ISO seleccionado: Ninguno")
        self.selected_iso_label.setStyleSheet("margin-bottom: 10px; color: white;")
        layout.addWidget(self.selected_iso_label)

        button_select_iso = QPushButton("Seleccionar ISO")
        button_select_iso.setIcon(QIcon.fromTheme("document-open"))
        button_select_iso.setStyleSheet("padding: 10px; border-radius: 5px; background-color: #3949AB; color: white;")
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
        button_burn.setStyleSheet("padding: 10px; border-radius: 5px; background-color: #2E7D32; color: white;")
        button_burn.clicked.connect(self.start_burn_iso)
        button_layout.addWidget(button_burn)

        button_cancel = QPushButton("Cancelar")
        button_cancel.setIcon(QIcon.fromTheme("process-stop"))
        button_cancel.setStyleSheet("padding: 10px; border-radius: 5px; background-color: #C62828; color: white;")
        button_cancel.clicked.connect(self.cancel_burn_iso)
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
        self.iso_drive_selection_box.addItems(drive_list)

    def select_iso(self):
        file_dialog = QFileDialog.getOpenFileName(self, "Seleccionar ISO", "", "Imágenes ISO (*.iso)")
        if file_dialog[0]:
            self.selected_iso = file_dialog[0]
            self.selected_iso_label.setText(f"ISO seleccionado: {os.path.basename(self.selected_iso)}")

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

    def update_iso_progress(self, value):
        self.iso_progressBar.setValue(value)

    def iso_burn_finished(self):
        QMessageBox.information(self, "Finalizado", "ISO grabada con éxito")
        self.iso_progressBar.setValue(0)

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)
        self.iso_progressBar.setValue(0)
