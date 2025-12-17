from PyQt6.QtWidgets import QVBoxLayout,QWidget,QLabel,QScrollArea,QHBoxLayout,QSizePolicy,QButtonGroup
from PyQt6.QtCore import Qt,QTimer
import cv2
import json
import copy


from src.frontend_helper import image_converters as img_conv
from src.frontend_helper.gui_helpers import GuiHelpers
from src.frontend.extracted_objects import ObjectViewer
from src.backend.image_editmanager import EditManager
from src.backend.sam_detector import SamExtractor
from src.backend.file_manager import FileManager
from src.backend_helpers.helper_thread import WorkerThread


with open(r"src\frontend\config.json", "r") as f:
    theme = json.load(f)



class AssertViewer(QWidget):
    def __init__(self, boundingbox_dict):
        super().__init__()
        self.boundingbox_dict = copy.deepcopy(boundingbox_dict)
        self.edit_manager = EditManager()
        self.gui_helper = GuiHelpers()
        self.display_size = None
        self.current_image_path = None
        self.current_image_name = None


        self.setGeometry(100, 100, 900, 600)
        self.setFixedSize(900, 600)
        
        self.setStyleSheet(theme["MAINWINDOW_STYLE"])

        self.main_window_widget = QWidget()
        self.main_window_layout = self.gui_helper.create_layout(QVBoxLayout(self.main_window_widget),5,5)
        self.setLayout(self.main_window_layout)

        self.main_layout_topwidget = self.gui_helper.create_layout(QHBoxLayout(),0,5)
        self.main_window_layout.addLayout(self.main_layout_topwidget)

        self.main_layout_bottomwidget = self.gui_helper.create_layout(QHBoxLayout(),0,5)
        self.main_window_layout.addLayout(self.main_layout_bottomwidget)

        self.setup(self.main_layout_topwidget,self.main_layout_bottomwidget)
        
        
    def setup(self,top_layout,bottom_layout):
        self.thumbnail_area(top_layout)
        self.display_area(top_layout)
        self.control_area(bottom_layout)

        QTimer.singleShot(0, self.after_window_shown)

    def after_window_shown(self):
        self.disp_w = self.display_group.width() - 30
        self.disp_h = self.display_group.height() - 30
        self.display_size = (self.disp_w,self.disp_h)
        for image_name in self.boundingbox_dict:
            image_path = self.boundingbox_dict[image_name]['image_path']
            self.edit_manager.store_images_for_edits(image_name,image_path,self.display_size)
                #self.edit_manager.store_images_for_edits(image_path,object_id,self.display_size)

    
    def thumbnail_area(self,layout):

        self.thumbnail_group,self.thumbnail_layout = self.gui_helper.create_groupbox("IMAGE SELECT",QVBoxLayout(),200,style="QGroupBox { margin-top: 0px; }",parent=layout.parentWidget())

        self.thumb_scroll = QScrollArea(parent=self.thumbnail_group)
        self.thumb_scroll.setWidgetResizable(True)
        self.thumb_scroll.setStyleSheet(theme["SCROLLBAR_STYLE"])


        self.thumb_widget,self.thumb_widget_layout = self.gui_helper.create_qwidget_container(QVBoxLayout(),5,5,parent=self.thumbnail_group)
        self.thumb_widget_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        for image_name in self.boundingbox_dict:
            thumb_image = cv2.imread(self.boundingbox_dict[image_name]['image_path'])
            thumbnail = self.gui_helper.create_image_thumbnail(thumb_image,image_name,130,100,parent=self.thumb_widget)
            self.thumb_widget_layout.addWidget(thumbnail)
            thumbnail.mousePressEvent = lambda event,name=image_name: self.on_thumbnail_click(name)

        self.thumb_scroll.setWidget(self.thumb_widget)
        self.thumbnail_layout.addWidget(self.thumb_scroll)

        layout.addWidget(self.thumbnail_group)



    def display_area(self, layout):

        self.display_group,self.display_layout = self.gui_helper.create_groupbox("DISPLAY IMAGE",QVBoxLayout(),style="QGroupBox { margin-top: 4px; }",parent=None)

        self.image_display = QLabel('PLEASE SELECT IMAGE FROM LEFT',parent=self.display_group)
        self.image_display.setContentsMargins(0, 0, 0, 0)
        self.image_display.setStyleSheet("QLabel { padding: 0px; margin: 0px; }")

        self.display_layout.addWidget(self.image_display,alignment = Qt.AlignmentFlag.AlignCenter)
        self.image_display.mousePressEvent = lambda event : self.get_display_coordinates(event)

        # Add final group to main layout
        layout.addWidget(self.display_group)


    def get_display_coordinates(self,event):
        cordinates = event.pos()
        #print(cordinates.x(),cordinates.y())
        if self.object_select_btn_container_dict['Select Object'].isChecked():
            display_coordinates = (cordinates.x(),cordinates.y())
            self.edit_manager.apply_edits_to_display(self.current_image_name,'Pixel','get_points',(display_coordinates,'Object'))
            self.update_display_image()

        elif self.object_select_btn_container_dict['Select Background'].isChecked():
            display_coordinates = (cordinates.x(),cordinates.y())
            self.edit_manager.apply_edits_to_display(self.current_image_name,'Pixel','get_points',(display_coordinates,'Background'))
            self.update_display_image()


    def control_area(self, layout):

        self.control_widget,self.control_layout = self.gui_helper.create_qwidget_container(QHBoxLayout(),5,5,height=100,parent=layout.parentWidget())
        self.control_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # self.advanced_segmentation
        self.object_select_btngrp = QButtonGroup()
        self.object_select_btngrp.setExclusive(True)
        self.advanced_segmentation_btn_container,self.advanced_button_dict = self.gui_helper.create_button_containers(["Add Object Points",'Extract All Objects'],QHBoxLayout(),
                                                                                        self.object_select_btngrp,30,220,False,True,parent=self.control_widget)
        self.control_layout.addWidget(self.advanced_segmentation_btn_container,alignment=Qt.AlignmentFlag.AlignCenter)

        self.advanced_button_dict.get("Add Object Points").clicked.connect(lambda checked,container=self.advanced_segmentation_btn_container,
                                                                                 layout=self.control_layout : self.add_object_points(container,layout))
        
        self.advanced_button_dict.get("Extract All Objects").clicked.connect(lambda checked: self.segment_image())

        self.status_label = self.gui_helper.create_label("Tip: Add object points only in the iage where u dont have any overlapping bounding boxes.\nUse object point only when you are dealing with Overcrowded image or Visually dense image ",parent=self.control_widget)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.control_layout.addWidget(self.status_label)

        layout.addWidget(self.control_widget, alignment=Qt.AlignmentFlag.AlignBottom)


    def on_thumbnail_click(self,image_name):

        self.current_image_name = image_name

        self.update_display_image()


    def update_display_image(self):

        display_image = self.edit_manager.get_cached_image_to_display(self.current_image_name)
        image = img_conv.cv2_to_qpixmap_display(display_image)
        self.image_display.setPixmap(image)

    
    def add_object_points(self,container,container_layout):
        container.setVisible(False)

        self.status_label.setText("Select Object or Background, then click on the image to mark points.\nUse more detailed points when extracting full scenes or complex backgrounds.")

        self.object_select_btn_container,self.object_select_btn_container_dict = self.gui_helper.create_button_containers(["Select Object",'Select Background'],QHBoxLayout(),
                                                                                        None,30,150,True,True,parent=container)
        container_layout.addWidget(self.object_select_btn_container,alignment=Qt.AlignmentFlag.AlignCenter)
        self.object_select_btn_container_dict['Select Object'].clicked.connect(lambda clicked: self.object_select(clicked))
        self.object_select_btn_container_dict['Select Background'].clicked.connect(lambda clicked: self.background_select(clicked))

        self.edit_undo_btn_container,self.edit_undo_btn_dict = self.gui_helper.create_button_containers(["Undo",'Redo'],QVBoxLayout(),
                                                                                        self.object_select_btngrp,30,150,False,True,parent=container)
        self.edit_undo_btn_container.layout().setSpacing(5)
        container_layout.addWidget(self.edit_undo_btn_container,alignment=Qt.AlignmentFlag.AlignCenter)
        self.edit_undo_btn_dict['Undo'].clicked.connect(lambda clicked: self.undo_edits(clicked))
        self.edit_undo_btn_dict['Redo'].clicked.connect(lambda clicked: self.redo_edits(clicked))

        self.edit_confirm_btn  = self.gui_helper.create_button('Extract Object',False,self.object_select_btngrp,button_width=150,button_height=30,parent=container)
        self.edit_confirm_btn.clicked.connect(lambda clicked: self.segment_image())
        container_layout.addWidget(self.edit_confirm_btn,alignment=Qt.AlignmentFlag.AlignCenter)
        


    def object_select(self,value):
        print(value)
        self.object_select_btn_container_dict['Select Background'].setChecked(False)


    def background_select(self,value):
        print(value)
        self.object_select_btn_container_dict['Select Object'].setChecked(False)


    def undo_edits(self,value):
        print(value)
        self.object_select_btn_container_dict['Select Background'].setChecked(False)
        self.object_select_btn_container_dict['Select Object'].setChecked(False)
        self.edit_manager.apply_edits_to_display(self.current_image_name,'Undo','Undo','Undo')
        self.update_display_image()


    def redo_edits(self,value):
        self.object_select_btn_container_dict['Select Background'].setChecked(False)
        self.object_select_btn_container_dict['Select Object'].setChecked(False)
        self.edit_manager.apply_edits_to_display(self.current_image_name,'Redo','Redo','Redo')
        self.update_display_image()

    
    def segment_image(self):
        self.control_widget.setVisible(False)
        self.progress_widget,self.progressbar = self.gui_helper.create_progressbar_container(txt="Image Segmentation in Progress",visible=True,container_size=(None,100),parent=self.main_layout_bottomwidget.parentWidget())
        self.main_layout_bottomwidget.addWidget(self.progress_widget)

        point_dict = self.edit_manager.get_points(self.display_size)

        self.worker_thread = WorkerThread(lambda progress,point_dict=point_dict : self.segment_using_sam(progress,point_dict))
        self.worker_thread.progress.connect(self.progressbar.setValue)
        self.worker_thread.finished.connect(self.close_window)

        self.worker_thread.start()

        

    def close_window(self,final_obj_dict):
        self.close()
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.object_viewer = ObjectViewer(final_obj_dict)
        self.object_viewer.show()
        


    def segment_using_sam(self,progress_signal,point_dict):
        extracted_object_dict = {}
        model_path , model_config_path = FileManager().get_model_path('segmentor')
        self.sam = SamExtractor(sam_path=model_path,sam_model_config=model_config_path)
        self.sam.load_device()

        for i,image in enumerate(self.boundingbox_dict):
            progress = int((i/len(self.boundingbox_dict))*100)
            progress_signal.emit(progress)

            image_path = self.boundingbox_dict[image]["image_path"]
            bbox = self.boundingbox_dict[image]["bbox"]
            point_coord = point_dict[image][0]
            point_label = point_dict[image][1]
            extracted_objects = self.sam.segmented_objects(image_path,bbox,point_coords=point_coord,point_labels=point_label)
            for object_name,object in extracted_objects.items():
                extracted_object_dict[object_name] = object


        self.sam.close()

        return extracted_object_dict
    

