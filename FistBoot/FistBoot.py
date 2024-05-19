import sys
import os
import time
import ctypes
import shutil
from PyQt5.QtWidgets import (
    QApplication, QWidget, QComboBox, QPushButton, QFileDialog,
    QVBoxLayout, QLabel, QMessageBox, QPlainTextEdit, QProgressBar, QSizePolicy
)
from PyQt5.QtCore import QProcess, Qt
from PyQt5.QtGui import QIcon, QColor, QPalette

text_selectdrive = "Seleccionar unidad"
text_button_selectfile = "Seleccionar Archivo"
text_selectfile = "Selecciona un archivo"
text_file = "Archivo"
text_button_prepare = "Preparar unidad"
text_status = "Estado:"
text_ready = "Listo"
text_writing = "Escribiendo"
text_error = "Error"
text_errorwait = "Espera hasta que termine el proceso actual."
text_nodrive = "Ninguna unidad seleccionada."
text_nofile = "Ningún archivo seleccionado."
text_areyousure = "¿Estás seguro?"
text_filewillbewritten = "El siguiente archivo será escrito en la unidad:"
text_processstarted = "Proceso iniciado."
text_processfinished = "Proceso terminado."
text_finished = "Finalizado"
text_copied = "copiado"

class FileWriter(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setMinimumSize(400, 300)
        self.setMaximumSize(400, 300)   # Aumento del tamaño de la ventana
        self.setWindowTitle("FistBoot")
        
        # Seleccionar el icono de la ventana dependiendo del directorio
        try:
            self.setWindowIcon(QIcon("./img/Logo.png"))
        except FileNotFoundError:
            self.setWindowIcon(QIcon("./img/Logo.png"))
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.isWriting = False

        # Obtener lista de unidades disponibles
        drive_list = [text_selectdrive]
        for drive_letter in range(65, 91):  # A-Z in ASCII
            drive = chr(drive_letter) + ":\\"
            if os.path.exists(drive):
                drive_list.append(drive)

        # Seleccionador de unidades
        self.drives_selection_box = QComboBox()
        self.drives_selection_box.addItems(drive_list)
        layout.addWidget(self.drives_selection_box)

        # Botón para seleccionar archivo
        self.button_selectFile = QPushButton(text_button_selectfile)
        self.button_selectFile.clicked.connect(self.getFile)
        layout.addWidget(self.button_selectFile)

        # Botón para escribir en la unidad
        self.button_write = QPushButton(text_button_prepare)
        self.button_write.clicked.connect(self.writeToFile)
        layout.addWidget(self.button_write)

        # Botón para cancelar
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.cancelWriting)
        layout.addWidget(self.cancel_button)

        # Estado
        self.statusText = QLabel(text_status + " " + text_ready)
        layout.addWidget(self.statusText)

        # Barra de progreso
        self.progressBar = QProgressBar()
        layout.addWidget(self.progressBar)

        # Consola
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.console)

        # Estilo oscuro por defecto
        self.setStyleSheet("""
            background-color: #17202A ; 
            color: #fff ;
        """)
        self.drives_selection_box.setStyleSheet("""
            background-color: #444; 
            color: #fff;
            border-radius:5px;
            padding: 5px;
            border: 1px solid gray;
        """)
        self.button_selectFile.setStyleSheet("""
            background-color: #444; 
            color: #fff;
            border: 0px solid gray;
            padding: 5px;
            border-radius:5px;
            border: 1px solid gray;
        """)
        self.button_write.setStyleSheet("""
            background-color: #444; 
            color: #fff;
            border: 1px solid gray;
            padding: 5px;
            border-radius:5px;
        """)
        self.progressBar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #00ff00;
                border-radius: 5px;
            }
        """)
        self.console.setStyleSheet("""
            background-color: #333; 
            color: #fff;
            border: 1px solid gray;
            border-radius:5px;
        """)
        self.cancel_button.setStyleSheet("""
            background-color: #444; 
            color: #fff;
            border: 1px solid gray;
            padding: 5px;
            border-radius:5px;
        """)

    def writeToFile(self):
        if self.isWriting:
            QMessageBox.critical(self, text_error, text_errorwait)
            return

        error = ""
        selected_drive = self.drives_selection_box.currentText()
        if selected_drive == text_selectdrive:
            error += text_nodrive + "\n"
        if not self.selected_file:
            error += text_nofile + "\n"

        if error:
            QMessageBox.critical(self, text_error, error)
        else:
            question_message = QMessageBox()
            start_process = question_message.question(
                self, text_areyousure,
                f"{text_filewillbewritten}\n{self.selected_file}\n\n{text_areyousure}",
                question_message.Yes | question_message.No
            )
            if start_process == question_message.Yes:
                # Comenzar proceso
                self.isWriting = True
                self.progressBar.setValue(0)
                self.statusText.setText(text_status + " " + text_writing)
                self.cancel_button.setEnabled(True)  # Habilitar el botón de cancelar

                try:
                    # Abrir el archivo para obtener su tamaño total
                    total_size = os.path.getsize(self.selected_file)

                    # Copiar archivo al dispositivo utilizando shutil
                    with open(self.selected_file, 'rb') as src_file:
                        with open(selected_drive + os.path.basename(self.selected_file), 'wb') as dest_file:
                            copied_size = 0
                            while True:
                                if not self.isWriting:  # Verificar si se ha solicitado cancelar
                                    break  # Salir del bucle si se ha solicitado cancelar
                                
                                chunk = src_file.read(4096)
                                if not chunk:
                                    break
                                dest_file.write(chunk)
                                copied_size += len(chunk)
                                # Actualizar la consola con los detalles del archivo que se está copiando
                                self.console.appendPlainText(f"Copiando {os.path.basename(self.selected_file)} ({copied_size}/{total_size} bytes)")

                                # Actualizar la barra de progreso
                                progress = int((copied_size / total_size) * 100)
                                self.progressBar.setValue(progress)

                                # Permitir que la aplicación responda durante el proceso de escritura
                                QApplication.processEvents()

                    # Proceso terminado exitosamente
                    self.processFinished()
                except Exception as e:
                    # Error al copiar el archivo
                    QMessageBox.critical(self, text_error, str(e))
                    self.isWriting = False
                    self.cancel_button.setEnabled(False)  # Deshabilitar el botón de cancelar después de un error

    def cancelWriting(self):
        # Método para cancelar el proceso de escritura
        if self.isWriting:
            self.isWriting = False
            self.statusText.setText(text_status + " " + text_ready)
            self.console.appendPlainText("Proceso cancelado por el usuario.")
            QMessageBox.information(self, "Cancelado", "Proceso de escritura cancelado.")
            self.cancel_button.setEnabled(False)  # Deshabilitar el botón de cancelar después de la cancelación

    def getFile(self):
        if self.isWriting:
            QMessageBox.critical(self, text_error, text_errorwait)
            return

        showDialog = QFileDialog.getOpenFileName(
            parent=self,
            caption=text_selectfile,
            filter=f"{text_file} (*.*)"
        )
        if showDialog[0]:
            self.selected_file = showDialog[0]
            self.button_selectFile.setText(os.path.basename(self.selected_file))

    def processFinished(self):
        self.progressBar.setValue(100)
        self.statusText.setText(text_status + " " + text_ready)
        self.console.appendPlainText(text_processfinished)
        QMessageBox.information(self, text_finished, text_processfinished)
        self.isWriting = False
        self.cancel_button.setEnabled(False)  # Deshabilitar el botón de cancelar después de finalizar el proceso

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileWriter()
    window.setWindowTitle("FistBoot")
    window.setWindowIcon(QIcon("./img/Logo.png"))
    app.setStyle("Fusion")  # Esto es para aplicar el estilo Fusion en toda la aplicación
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(0, 0, 0))
    app.setPalette(palette)
    window.show()
    sys.exit(app.exec_())
