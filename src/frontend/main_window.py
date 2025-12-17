from PyQt6.QtWidgets import QPushButton,QVBoxLayout,QWidget,QHBoxLayout,QMainWindow,QLabel,QGroupBox,QSizePolicy
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont,QPixmap
import json


from src.frontend.image_boundingbox import ImageViewer

with open(r"src\frontend\config.json", "r") as f:
    theme = json.load(f)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.images=[]
        self.videos = []
        self.max_limit_reached = False
        self.set_ui()

        

    def set_ui(self):
        self.setGeometry(100,100,900,600)
        self.setFixedSize(900,600)

        self.setStyleSheet(theme["MAINWINDOW_STYLE"])

        self.page1 = QWidget()
        self.setCentralWidget(self.page1)
        self.layout1 = QVBoxLayout(self.page1)
        self.layout1.setSpacing(10)
        self.page1.setLayout(self.layout1)
        self.title_area(self.layout1)
        self.drop_space_area(self.layout1)

        self.setAcceptDrops(True)


    def title_area(self, layout):
        
        self.title_group = QGroupBox()
        self.title_group.setFixedHeight(100)
        title_layout = QVBoxLayout(self.title_group)
        self.title_group.setStyleSheet(theme["MAINWINDOW_STYLE"] + "QGroupBox { border: none; margin-top: 0px }")

        #Container widget for icon+text
        title_label_widget = QWidget()
        title_label_widget.setContentsMargins(0, 0, 0, 0)
        title_layout_inner = QHBoxLayout(title_label_widget)
        title_layout_inner.setContentsMargins(0, 0, 0, 0)
        title_layout_inner.setSpacing(10)  # space between icon and text
        title_layout_inner.setAlignment(Qt.AlignmentFlag.AlignCenter)

        #app Icon
        pixmap = QPixmap('app.ico')
        icon_label = QLabel()
        icon_label.setPixmap(pixmap)
        icon_label.setFixedSize(40, 40)
        icon_label.setScaledContents(True)  # scale icon to fit the label
        title_layout_inner.addWidget(icon_label)


        title_label = QLabel("Frame2Game - Image to Game Asset Converter")
        title_font = QFont()
        title_font.setPointSize(40)  # increase font size
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #4CAF50;")  # keep same green color
        title_layout_inner.addWidget(title_label)

        title_layout.addWidget(title_label_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        
        desc_label = QLabel("Extract game assets with transparent backgrounds from images")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("color: #cccccc; padding: 10px;")
        title_layout.addWidget(desc_label)

        layout.addWidget(self.title_group)
        

    def drop_space_area(self,layout):

        self.image_count_label = QLabel("You can upload up to 15 images per session. Supported formats: .png, .jpg, .jpeg, .bmp, .webp, .tiff, .gif.")
        self.image_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_count_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.image_count_label)

        self.drop_group = QGroupBox("File Selection")
        self.drop_group.setMaximumHeight(400)
        drop_layout = QVBoxLayout(self.drop_group)

        self.drop_label=QLabel("DROP YOUR IMAGES HERE")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.addWidget(self.drop_label,alignment=Qt.AlignmentFlag.AlignCenter)

        confirm_button = QPushButton('Confirm Selection')
        confirm_button.setFixedSize(200,50)
        confirm_button.clicked.connect(self.navigate_to_appropriate_viewer)
        drop_layout.addWidget(confirm_button,alignment=Qt.AlignmentFlag.AlignHCenter)

        layout.addWidget(self.drop_group)

    
    def navigate_to_appropriate_viewer(self):
        
        if self.images and not self.videos:
            self.image_viewer = ImageViewer(self.images)
            self.image_viewer.show()
            self.close()
            self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
 
        
        elif self.videos and not self.images:
            # TODO: Implement video-to-game-asset feature here
            self.drop_label.setText("Video-to-Game-Asset support is coming soon! Stay tuned—right now the tool works with images only.")

        else:
            self.drop_label.setText("No Files, Please select image file.")


    def get_file_type(self, file_path):
        image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.webp', '.tiff', '.gif']
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
        path_lower = file_path.lower()

        if any(path_lower.endswith(ext) for ext in image_extensions):
            return "image"
        elif any(path_lower.endswith(ext) for ext in video_extensions):
            return "video"
        else:
            return None
        

    #file validation
    def validate_files(self, new_files):
        total_images = self.images + [f for f in new_files if self.get_file_type(f) == "image"]
        total_videos = self.videos + [f for f in new_files if self.get_file_type(f) == "video"]
        others = [f for f in new_files if self.get_file_type(f) is None]

        if others:
            return False, "<span style='color: red;'>Unsupported file types detected!</span>"

        if total_images and total_videos:
            return False, "<span style='color: red;'>Cannot mix images and videos!</span>"

        if len(total_images) > 15:
            return False, f"<span style='color: red;'>Maximum of 15 images allowed! You attempted {len(total_images)}. Adding a new file will reset all selected images.</span>"

        if len(total_videos) > 1:
            return False, f"<span style='color: red;'>Maximum of 1 video allowed! You attempted {len(total_videos)}. Adding a new file will reset all selected videos.</span>"

        return True, "OK"


    #Update labels
    def update_labels(self):
        if self.images and not self.videos:
            self.drop_label.setText("\n".join(self.images))
            self.image_count_label.setText(
                "You can upload up to 15 images per session. Supported formats: .png, .jpg, .jpeg, .bmp, .webp, .tiff, .gif.<br>"
                f"<span style='color: green;'>{len(self.images)} images added.</span>"
            )
        elif self.videos and not self.images:
            self.drop_label.setText("\n".join(self.videos))
            self.image_count_label.setText(
                "You can upload up to 15 images per session. Supported formats: .png, .jpg, .jpeg, .bmp, .webp, .tiff, .gif.<br>"
                f"<span style='color: green;'>{len(self.videos)} video loaded.</span>"
            )
        else:
            self.drop_label.setText("DROP YOUR IMAGES HERE")
            self.image_count_label.setText(
                "You can upload up to 15 images per session. Supported formats: .png, .jpg, .jpeg, .bmp, .webp, .tiff, .gif."
            )


    #Core logic
    def handle_new_files(self, incoming):
        #types of incoming files
        incoming_types = [self.get_file_type(f) for f in incoming if self.get_file_type(f) is not None]
        has_images = any(t == "image" for t in incoming_types)
        has_videos = any(t == "video" for t in incoming_types)

        # If mix detection
        if has_images and has_videos:
            self.image_count_label.setText(
                "You can upload up to 15 images per session. Supported formats: .png, .jpg, .jpeg, .bmp, .webp, .tiff, .gif."
                "<span style='color: red;'>Cannot mix images and videos in the same drop! All previous files reset.</span>"
            )
            self.images.clear()
            self.videos.clear()
            self.image_warning_shown = False
            self.video_warning_shown = False
            self.update_labels()
            return

        # Mix detection with existing files
        if (self.images and has_videos) or (self.videos and has_images):
            self.image_count_label.setText(
                "You can upload up to 15 images per session. Supported formats: .png, .jpg, .jpeg, .bmp, .webp, .tiff, .gif."
                "<span style='color: red;'>Cannot mix images and videos! All previous files reset.</span>"
            )
            self.images.clear()
            self.videos.clear()
            self.image_warning_shown = False
            self.video_warning_shown = False
            self.update_labels()
            return

        #Validate normal senario
        is_valid, message = self.validate_files(incoming)

        if is_valid:
            #Add files normaly
            self.images.extend([f for f in incoming if self.get_file_type(f) == "image"])
            self.videos.extend([f for f in incoming if self.get_file_type(f) == "video"])
            self.image_warning_shown = False
            self.video_warning_shown = False
            self.update_labels()
            return

        #Handle limit warnings
        incoming_type_set = set(incoming_types)
        for ftype in incoming_type_set:
            if ftype == "image":
                if not getattr(self, "image_warning_shown", False):
                    self.image_count_label.setText(f"""You can upload up to 15 images per session. Supported formats: .png, .jpg, .jpeg, .bmp, .webp, .tiff, .gif."<br>{message}""")
                    self.image_warning_shown = True
                    return
                else:
                    #reset images , allow only 15(for now)
                    self.images = [f for f in incoming if self.get_file_type(f) == "image"][:15]
                    self.image_warning_shown = False
            elif ftype == "video":
                if not getattr(self, "video_warning_shown", False):
                    self.image_count_label.setText(f"""You can upload up to 15 images per session. Supported formats: .png, .jpg, .jpeg, .bmp, .webp, .tiff, .gif."<br>{message}""")
                    self.video_warning_shown = True
                    return
                else:
                    #reset videos, allow only 1 (for now)
                    self.videos = [f for f in incoming if self.get_file_type(f) == "video"][:1]
                    self.video_warning_shown = False

        self.update_labels()


    #Drag/drop event
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if not event.mimeData().hasUrls():
            event.ignore()
            return

        incoming = [url.toLocalFile() for url in event.mimeData().urls()]
        self.handle_new_files(incoming)
        event.acceptProposedAction()

        












