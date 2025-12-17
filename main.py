import sys
from PyQt6.QtWidgets import (QApplication, QDialog, QVBoxLayout,QWidget, 
                             QProgressBar, QLabel, QPushButton,QHBoxLayout)
from PyQt6.QtGui import QIcon,QFont,QPixmap
from PyQt6.QtCore import QTimer,Qt
import shutil

from src.backend.file_manager import FileManager
from src.backend_helpers.helper_thread import WorkerThreadDownload
from src.frontend.main_window import MainWindow
from src.backend_helpers.path_helper import resource_path


class DownloadDialog(QDialog):

    def __init__(self, download_url, file_manager, parent=None):
        super().__init__(parent)
        self.download_url = download_url
        self.file_manager = file_manager
        self.setup_ui()


    def setup_ui(self):
        self.setWindowTitle("Frame2Game - First Time Setup")
        self.setFixedSize(450, 250)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        

        #Container widget for icon+text
        title_label_widget = QWidget()
        title_label_widget.setContentsMargins(0, 0, 0, 0)
        title_layout_inner = QHBoxLayout(title_label_widget)
        title_layout_inner.setContentsMargins(0, 0, 0, 0)
        title_layout_inner.setSpacing(10)  # space between icon and text
        title_layout_inner.setAlignment(Qt.AlignmentFlag.AlignCenter)

        #app Icon
        icon_path = resource_path(r'app.ico')
        pixmap = QPixmap(icon_path)
        icon_label = QLabel()
        icon_label.setPixmap(pixmap)
        icon_label.setFixedSize(30, 30)
        icon_label.setScaledContents(True)  # scale icon to fit the label
        title_layout_inner.addWidget(icon_label)


        title_label = QLabel("Frame2Game - Image to Game Asset Converter")
        title_font = QFont()
        title_font.setPointSize(10)  # increase font size
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #4CAF50;")  # keep same green color
        title_layout_inner.addWidget(title_label)

        layout.addWidget(title_label_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        
        # Description
        desc = QLabel("AI models required for asset extraction\n(~1GB, one-time download)")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("font-size: 14px; color: #666;")
        layout.addWidget(desc)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #555;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Ready to download")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Size info
        self.size_label = QLabel("Total size: ~1GB")
        self.size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.size_label.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(self.size_label)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        self.download_btn = QPushButton("Download")
        self.download_btn.setFixedWidth(150)
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 5px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.download_btn.clicked.connect(self.start_download)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedWidth(150)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.download_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)


    def start_download(self):
        """Start download using FileManager"""
        self.download_btn.setEnabled(False)
        self.cancel_btn.setText("Stop")
        self.status_label.setText("Starting download...")
        
        #download thread
        self.download_thread = WorkerThreadDownload(lambda progress_callback,url=self.download_url: self.file_manager.download_models(progress_callback,url))
        self.download_thread.progress.connect(self.progress_bar.setValue)
        self.download_thread.finished.connect(self.close_window)

        self.download_thread.start()


    def close_window(self,status_text):
        status , text = status_text
        if status:
            self.progress_bar.setValue(100)
            self.status_label.setText(text)
            self.size_label.setText("Ready to launch!")
            QTimer.singleShot(2000, self.accept) 

        else:
            self.status_label.setText(f"Download Failed! - {text}")
            self.download_btn.setText("Retry")
            self.download_btn.setEnabled(True)
            self.cancel_btn.setText("Exit")


    def reject(self):
        #Handle cancel/stop
        if hasattr(self, 'download_thread') and self.download_thread.isRunning():
            self.download_thread.terminate()
            self.download_thread.wait()

            self.base_dir = self.file_manager.get_base_dir()
            self.models_dir = self.base_dir / "models"
            if self.models_dir.exists():
                shutil.rmtree(self.models_dir)
                print("deleted old models folder")
        
        super().reject()



def main():
    #Check models 
    file_manager = FileManager()
    models_ready = file_manager.check_if_required_models_exist()

    app_name_and_version = 'Frame2Game v1.0.0'
    app = QApplication(sys.argv)
    app.setApplicationName(app_name_and_version)
    icon_path = resource_path(r'app.ico')
    app.setWindowIcon(QIcon(icon_path))

    if models_ready:
        #launch main app
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    else:
        #show download dialog
        
        MODEL_ZIP_URL = "https://github.com/Sha831/Frame2Game/releases/download/Models-Frame2Game_v1.0.0/models.zip"#to be updated

        dialog = DownloadDialog(MODEL_ZIP_URL, file_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            #Download successful ,launch app
            window = MainWindow()
            window.show()
            sys.exit(app.exec())
        else:
            sys.exit(0)


if __name__ == "__main__":
    main()