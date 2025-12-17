from PyQt6.QtWidgets import QPushButton,QVBoxLayout,QWidget,QLabel,QGroupBox,QScrollArea,QHBoxLayout,QProgressBar
from PyQt6.QtCore import Qt,QTimer
import cv2
from pathlib import Path
import json
from collections import namedtuple
from itertools import chain


from src.frontend_helper import image_converters as img_conv
from src.backend.image_processing_yolo import ImageProcess
from src.frontend.image_assert import AssertViewer
from src.backend_helpers.helper_thread import WorkerThreadYolo

with open(r"src\frontend\config.json", "r") as f:
    theme = json.load(f)

BoundingBox = namedtuple('BoundingBox',['x1','y1','x2','y2'])

def style_font(widget: QWidget, size: int = 14, bold: bool = True):
    font = widget.font()
    font.setPointSize(size)
    font.setBold(bold)
    widget.setFont(font)


class ImageViewer(QWidget):
    def __init__(self, images):
        super().__init__()
        self.images = list(images) 
        self.current_image_path = None
        self.yolo_selection = 0
        self.manual_selection = 0
        self.yolo_results = {}
        self.is_drawing = None
        self.drawing_complete = None
        self.image_to_display = None
        self.manualboxes = {}
        self.manualboxes_org_img = {}
        self.confirmed_objects = {}
        self.image_process = ImageProcess()


        self.setGeometry(100, 100, 900, 600)
        self.setFixedSize(900, 600)
        
        self.setStyleSheet(theme["MAINWINDOW_STYLE"])

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(6, 6, 6, 6)
        self.main_layout.setSpacing(5) 
        self.setLayout(self.main_layout)

        top_container = QWidget()
        top_layout = QHBoxLayout(top_container)
        top_layout.setContentsMargins(0,0, 0, 0)
        top_layout.setSpacing(5)
        self.main_layout.addWidget(top_container,stretch=1)

        self.thumbnail_area(top_layout)

        self.display_area(top_layout)

        self.control_area(self.main_layout)


    def thumbnail_area(self,layout):

        self.thumb_group = QGroupBox("IMAGE SELECT")
        self.thumb_group.setFixedWidth(200)
        style_font(self.thumb_group,8,False)
        self.thumb_group.setStyleSheet(theme["GROUPBOX_STYLE"] + "QGroupBox { margin-top: 4px; }")
        
        thumb_layout = QVBoxLayout(self.thumb_group)

        thumb_scroll = QScrollArea()
        thumb_scroll.setWidgetResizable(True)
        thumb_scroll.setStyleSheet(theme["SCROLLBAR_STYLE"])

        thumb_widget = QWidget()
        thumb_widget_layout = QVBoxLayout(thumb_widget)
        thumb_widget_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        thumb_widget_layout.setSpacing(5) 

        for i,image in enumerate(self.images):
            thumb = self.create_thumbnail(image)
            thumb_widget_layout.addWidget(thumb)

        thumb_scroll.setWidget(thumb_widget)

        thumb_layout.addWidget(thumb_scroll)

        layout.addWidget(self.thumb_group)


    def display_area(self,layout):

        self.display_group = QGroupBox("IMAGE DISPLAY")
        style_font(self.display_group,8,False)
        self.display_group.setStyleSheet(theme["GROUPBOX_STYLE"] + "QGroupBox { margin-top: 4px; }")
        
        display_layout = QVBoxLayout()
        self.display_group.setLayout(display_layout)

        self.image_display = QLabel("SELECT A IMAGE FROM LEFT")
        self.image_display.setContentsMargins(0, 0, 0, 0)
        self.image_display.setStyleSheet("QLabel { padding: 0px; margin: 0px; }")
        self.image_display.setMouseTracking(True)
        self.image_display.mousePressEvent = self.image_mouse_press
        self.image_display.mouseReleaseEvent = self.image_mouse_release
        display_layout.addWidget(self.image_display,alignment=Qt.AlignmentFlag.AlignCenter)
        

        layout.addWidget(self.display_group)


    def control_area(self,layout):

        self.control_group = QGroupBox()
        self.control_group.setFixedHeight(100)
        self.control_group.setStyleSheet(theme["GROUPBOX_STYLE"])
        
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(2,2,2,2)
        self.control_group.setLayout(control_layout)

        #left side buttons
        row1_layout = QVBoxLayout()

        self.yolo_button = QPushButton("AI Batch Object Detect")
        self.yolo_button.setFixedSize(200,25)
        self.yolo_button.setStyleSheet(theme["BUTTON_STYLE"])
        self.yolo_button.hide()
        self.yolo_button.clicked.connect(self.yolo_detection)

        self.manual_button = QPushButton("Manual Object Select")
        self.manual_button.setFixedSize(200,25)
        self.manual_button.setStyleSheet(theme["BUTTON_STYLE"])
        self.manual_button.setCheckable(True)
        self.manual_button.hide()
        self.manual_button.clicked.connect(self.manual_box_select)

        self.box_reset_button=QPushButton("Reset All Boxes")
        self.box_reset_button.setFixedSize(200,25)
        self.box_reset_button.setStyleSheet(theme["BUTTON_STYLE"])
        self.box_reset_button.setCheckable(False)
        self.box_reset_button.hide()
        self.box_reset_button.clicked.connect(self.reset_all_boxes)

        row1_layout.addWidget(self.yolo_button,alignment=Qt.AlignmentFlag.AlignLeft)
        row1_layout.addWidget(self.manual_button,alignment=Qt.AlignmentFlag.AlignLeft)
        row1_layout.addWidget(self.box_reset_button,alignment=Qt.AlignmentFlag.AlignLeft)
        #center info area
        row2_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        self.status_label = QLabel("Ready - Select an image to begin")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(theme["LABEL_STYLE"] + "QLabel { font-size: 15px; }")

        row2_layout.addWidget(self.progress_bar)
        row2_layout.addWidget(self.status_label,alignment=Qt.AlignmentFlag.AlignCenter,stretch=1)


        #right side buttons
        row3_layout = QVBoxLayout()

        self.yolo_selection = QLabel(" AI Selection : 0 ")
        self.yolo_selection.setFixedWidth(180)
        self.yolo_selection.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.yolo_selection.setStyleSheet(theme["LABEL_STYLE"] + "QLabel { background-color: #2b2b2b; }")

        self.manual_selection = QLabel(" Manual Selections : 0 ")
        self.manual_selection.setFixedWidth(180)
        self.manual_selection.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.manual_selection.setStyleSheet(theme["LABEL_STYLE"] + "QLabel { background-color: #2b2b2b; }")

        self.confirm_button = QPushButton("Confirm Objects")
        self.confirm_button.setFixedSize(180,30)
        self.confirm_button.setStyleSheet(theme["BUTTON_STYLE"])
        self.confirm_button.hide()
        self.confirm_button.clicked.connect(self.confirm_objects_for_sam)
       
        row3_layout.addWidget(self.yolo_selection,alignment=Qt.AlignmentFlag.AlignRight)
        row3_layout.addWidget(self.manual_selection,alignment=Qt.AlignmentFlag.AlignRight)
        row3_layout.addWidget(self.confirm_button,alignment=Qt.AlignmentFlag.AlignRight)

        control_layout.addLayout(row1_layout)
        control_layout.addLayout(row2_layout)
        control_layout.addLayout(row3_layout)

        layout.addWidget(self.control_group,alignment=Qt.AlignmentFlag.AlignBottom)

        
    def create_thumbnail(self,image_path):
        image_container = QWidget()
        image_container_layout = QVBoxLayout(image_container)
        image_container_layout.setContentsMargins(5,5,5,5)
        image_container_layout.setSpacing(2)
        image_container.setFixedSize(130,100)

        image_holder = QLabel()
        thumbnail = img_conv.image_path_to_qpixmap(image_path,max_size=(image_container.width(), image_container.height()))
        image_holder.setPixmap(thumbnail)
        image_holder.setStyleSheet(theme["LABEL_STYLE"] + " QLabel { border: 2px solid #555; border-radius: 3px; }")

        image_container_layout.addWidget(image_holder,alignment=Qt.AlignmentFlag.AlignCenter)

        image_label = QLabel(Path(image_path).stem)
        image_label.setWordWrap(True)
        image_container_layout.addWidget(image_label,alignment=Qt.AlignmentFlag.AlignCenter)

        image_container.mousePressEvent = lambda event, path=image_path: self.on_thumbnail_click(path)

        return image_container
        

    def on_thumbnail_click(self,image_path):

        self.current_image_path = image_path

        self.status_label.setText(f"Seletcted Image : {Path(self.current_image_path).stem}")

        self.yolo_button.show()
        self.manual_button.show()
        self.confirm_button.show()

        if self.yolo_results or self.manualboxes:
            self.redraw_image_with_boundingbox(self.yolo_results,self.manualboxes)
            self.box_reset_button.show()
        else:
            self.image_to_display = cv2.imread(self.current_image_path)
            image = img_conv.cv2_to_qpixmap_display(self.image_to_display,max_size=(self.display_group.width(), self.display_group.height()))
            self.image_display.setPixmap(image)
            

    def reset_all_boxes(self):
        current_img = Path(self.current_image_path).stem
        self.manual_button.setChecked(False)

        if self.yolo_results:
            self.yolo_results.pop(current_img,None)
            self.yolo_selection.setText(" AI Selection : 0")

        if self.manualboxes:
            self.manualboxes.pop(current_img,None)
            self.manualboxes_org_img.pop(current_img,None)
            self.manual_selection.setText(" Manual Selections : 0")


        self.on_thumbnail_click(self.current_image_path)


    def yolo_detection(self):

        if self.manual_button.isChecked():
            self.manual_button.setChecked(False)

        if not self.images:
            self.status_label.setText("No Images Added")
            return
        
        self.status_label.setText("Running YOLO detection...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(25)

        def handle_yolo_result(result):
            self.progress_bar.setValue(75)
            
            self.yolo_results = result

            if self.yolo_results and len(self.yolo_results) > 0:
                self.on_thumbnail_click(self.current_image_path)
            else:
                self.yolo_selection.setText(" AI Selection : 0 ")
                self.status_label.setText(" No objects detected")
            
            self.progress_bar.setValue(100)
            QTimer.singleShot(1000, lambda: self.progress_bar.setVisible(False))

        try:
            self.workerthread = WorkerThreadYolo(lambda : self.image_process.object_detection(self.images))
            self.workerthread.finished.connect(handle_yolo_result)  

            self.workerthread.start()
            
            
        except Exception as e:
            self.status_label.setText(f"❌ YOLO Error: {str(e)}")
            print(f"YOLO Error: {e}")
        

        QTimer.singleShot(1000, lambda: self.progress_bar.setVisible(False))


    def manual_box_select(self):
        if self.manual_button.isChecked():
            self.status_label.setText(f"Seletcted Image : {Path(self.current_image_path).stem}\n"
                                      "You can now manually draw bounding box.\n"
                                      "Left-Click and drag cursor around the object to draw a bounding box.")

            self.is_drawing = False
            self.drawing_complete = False
            self.manualbox_start_pos = None
            self.manualbox_end_pos = None


        else:
            self.status_label.setText(f"Seletcted Image : {Path(self.current_image_path).stem}")
            self.manual_button.setStyleSheet(theme["BUTTON_STYLE"])


    def image_mouse_press(self, event):
        if self.manual_button.isChecked() and event.button() == Qt.MouseButton.LeftButton:
            self.is_drawing = True
            self.drawing_complete = False
            self.manualbox_start_pos = event.pos()
            print("Start:", self.manualbox_start_pos)

    def image_mouse_release(self, event):
        if self.is_drawing and event.button() == Qt.MouseButton.LeftButton:
            self.is_drawing = False
            self.drawing_complete = True
            self.manualbox_end_pos = event.pos()
            print("End:", self.manualbox_end_pos)
            self.draw_manual_box()

    def get_image_offset_within_label(self):#Not used maybe usefull later
        """Calculate offset of image within the QLabel due to alignment"""
        if not self.image_display.pixmap():
            return 0, 0
        
        label_rect = self.image_display.contentsRect()
        pixmap_size = self.image_display.pixmap().size()
        
        # Calculate centering offsets
        offset_x = (label_rect.width() - pixmap_size.width()) / 2
        offset_y = (label_rect.height() - pixmap_size.height()) / 2
        
        return offset_x, offset_y

    def draw_manual_box(self):
        if self.drawing_complete and not self.is_drawing:
            image_name = Path(self.current_image_path).stem
            x1 , x2 = sorted([self.manualbox_start_pos.x(),self.manualbox_end_pos.x()])
            y1 , y2 = sorted([self.manualbox_start_pos.y(),self.manualbox_end_pos.y()])
            
            #box dimensions
            box_width = x2 - x1
            box_height = y2 - y1
            
            # Only create box if large enough 
            if box_width > 10 and box_height > 10:
                    display_box = BoundingBox(x1, y1, x2, y2)
                    self.manualboxes.setdefault(image_name, []).append(display_box)

                
                    display_widget_size  = (self.display_group.width(), self.display_group.height())
                    org_box=img_conv.change_coordinates_pixmap_to_cv2(self.current_image_path,display_widget_size,display_box)
                    self.manualboxes_org_img.setdefault(image_name, []).append(org_box)

                    self.on_thumbnail_click(self.current_image_path)

            
    def redraw_image_with_boundingbox(self, yolo_box, manual_box):
        image_name = Path(self.current_image_path).stem
        
        self.image_to_display = cv2.imread(self.current_image_path)
        
        # Apply YOLO boxes if available
        if yolo_box and image_name in yolo_box:
            boxed_image = self.yolo_results.get(image_name)[0]
            object_count = self.yolo_results.get(image_name)[1]
            self.image_to_display = boxed_image  
            self.yolo_selection.setText(f" AI Selection : {object_count}")
            self.status_label.setText(f"Found {object_count} objects!")
        else:
            self.yolo_selection.setText(" AI Selection : 0")
        
        # Apply manual boxes ON TOP of YOLO image
        if image_name and image_name in manual_box:
            manual_count = len(self.manualboxes.get(image_name))
            

            if self.manualboxes_org_img.get(image_name):
                self.image_to_display = self.image_process.update_img_with_manual_boundigbox(
                    self.image_to_display,  
                    self.manualboxes_org_img.get(image_name)
                )
            
            self.manual_selection.setText(f" Manual Selections : {manual_count}")
        else:
            self.manual_selection.setText(" Manual Selections : 0")
        

        if self.image_to_display is not None:
            image = img_conv.cv2_to_qpixmap_display(
                self.image_to_display,
                max_size=(self.display_group.width(), self.display_group.height())
            )
            self.image_display.setPixmap(image)
            

        
    def confirm_objects_for_sam(self):

        if getattr(self, "workerthread", None) is None or not self.workerthread.isRunning():
            has_object = False

            for path in self.images:
                image_name = Path(path).stem

                yolo_box = self.yolo_results.get(image_name,None)
                yolo_obj = yolo_box[2] if yolo_box and len(yolo_box)>2 and len(yolo_box[2])>0 else None
                manual_obj = self.manualboxes_org_img.get(image_name,None)

                if yolo_obj or manual_obj:

                    has_object = True

                    self.confirmed_objects.setdefault(image_name, {})

                    # Store img path
                    self.confirmed_objects[image_name]["image_path"] = path
                    
                    # Store YOLO objects
                    yolo_box = self.yolo_results.get(image_name,None)
                    yolo_boundingbox = yolo_box[2] if yolo_box and len(yolo_box)>2 and len(yolo_box[2])>0 else []
                    
                    # Store manual boxes  
                    manual_boundingbox = self.manualboxes_org_img.get(image_name,[])

                    combined = list(chain(yolo_boundingbox or [], manual_boundingbox or []))
                    seen = set()

                    bounding_box = {
                        f"{image_name}_object_{i}": x
                        for i,x in enumerate(combined)
                        if x not in seen and not seen.add(x)
                    }

                        

                    self.confirmed_objects[image_name]["bbox"] = bounding_box




            if not has_object:
                self.confirmed_objects = {}
                self.status_label.setText("0 Objects selected\n"
                                            "Please select object manually or use AI Object Detect")
                
            else:
                print("Opening assert viewer")
                print(self.confirmed_objects)
                self.close_window(self.confirmed_objects)


    def close_window(self,confirmed_objects):
        self.image_process.close()
        self.assert_viewer = AssertViewer(confirmed_objects)
        self.assert_viewer.show()
        self.close()
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

    
            


