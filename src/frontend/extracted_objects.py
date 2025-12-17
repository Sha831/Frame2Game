from PyQt6.QtWidgets import QVBoxLayout,QWidget,QLabel,QScrollArea,QHBoxLayout,QSizePolicy,QButtonGroup
from PyQt6.QtCore import Qt,QTimer

import json
import copy





from src.frontend_helper import image_converters as img_conv
from src.frontend_helper.gui_helpers import GuiHelpers
from src.backend.image_editmanager import EditManager
from src.backend.edit_options import EditOptions
from src.frontend.object_enhancement import ObjectEnhancer
from src.backend_helpers.helper_thread import WorkerThread
from src.backend_helpers.path_helper import resource_path

path = resource_path(r"src\frontend\config.json")
with open(path, "r") as f:
    theme = json.load(f)


class ObjectViewer(QWidget):
    def __init__(self, extracted_objects):
        super().__init__()
        self.extracted_object_dict  = copy.deepcopy(extracted_objects)
        self.edit_manager = EditManager()
        self.gui_helper = GuiHelpers()
        self.display_size = None
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
        for image_name in self.extracted_object_dict :
            image = self.extracted_object_dict [image_name]
            self.edit_manager.store_images_for_edits(image_name,image,self.display_size)


    
    def thumbnail_area(self,layout):

        self.thumbnail_group,self.thumbnail_layout = self.gui_helper.create_groupbox("IMAGE SELECT",QVBoxLayout(),200,style="QGroupBox { margin-top: 0px; }",parent=layout.parentWidget())

        self.thumb_scroll = QScrollArea(parent=self.thumbnail_group)
        self.thumb_scroll.setWidgetResizable(True)
        self.thumb_scroll.setStyleSheet(theme["SCROLLBAR_STYLE"])


        self.thumb_widget,self.thumb_widget_layout = self.gui_helper.create_qwidget_container(QVBoxLayout(),5,5,parent=self.thumbnail_group)
        self.thumb_widget_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        for image_name in self.extracted_object_dict :
            thumb_image = self.extracted_object_dict.get(image_name)
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
        self.image_display.enterEvent = lambda event : self.handle_slider_change()
        

        self.display_layout.addWidget(self.image_display,alignment = Qt.AlignmentFlag.AlignCenter)
        self.image_display.mousePressEvent = lambda event : self.coordinates_on_mouse_press(event)
        self.image_display.mouseMoveEvent = lambda event : self.coordinates_on_mouse_drag(event)
        self.image_display.mouseReleaseEvent = lambda event : self.confirm_coordinates_on_mouse_release(event)

        # Add final group to main layout
        layout.addWidget(self.display_group)


    def handle_slider_change(self,val=None):
        if self.fill_erase_button_dict.get("Fill Holes").isChecked() or self.fill_erase_button_dict.get("Erase").isChecked():
            self.cursor_size = val if val is not None else self.slider.value()
            self.gui_helper.create_circular_cursor(self.cursor_size,self.display_group)


    def coordinates_on_mouse_press(self,event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_points = []   # start new list
            x, y = event.pos().x(), event.pos().y()
            self.drag_points.append((x, y))


    def coordinates_on_mouse_drag(self,event):
        if self.is_dragging:
            x, y = event.pos().x(), event.pos().y()
            self.drag_points.append((x, y))


    def confirm_coordinates_on_mouse_release(self,event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.is_dragging = False

            x, y = event.pos().x(), event.pos().y()
            self.drag_points.append((x, y))

            if self.fill_erase_button_dict.get("Fill Holes").isChecked():
                self.edit_manager.apply_edits_to_display(self.current_image_name,'Pixel','fill_or_erase_point',(self.drag_points,self.cursor_size,'Fill'))
                self.update_display_image()

            elif self.fill_erase_button_dict.get("Erase").isChecked():
                self.edit_manager.apply_edits_to_display(self.current_image_name,'Pixel','fill_or_erase_point',(self.drag_points,self.cursor_size,'Erase'))
                self.update_display_image()


        


    def on_thumbnail_click(self,image_name):

        self.current_image_name = image_name

        self.update_display_image()

        print(self.image_display.size())


    def update_display_image(self):

        display_image = self.edit_manager.get_cached_image_to_display(self.current_image_name)
        image = img_conv.cv2_to_qpixmap_display(display_image)
        self.image_display.setPixmap(image)
    

    def control_area(self, layout):

        self.control_widget,self.control_layout = self.gui_helper.create_qwidget_container(QHBoxLayout(),5,5,height=100,parent=layout.parentWidget())
        self.control_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)


        # self.advanced_segmentation
        self.object_select_btngrp = QButtonGroup()
        self.object_select_btngrp.setExclusive(True)
        self.fill_erase_btn_container,self.fill_erase_button_dict = self.gui_helper.create_button_containers(["Fill Holes",'Erase'],QHBoxLayout(),
                                                                                        None,30,130,True,True,parent=self.control_widget)
        self.control_layout.addWidget(self.fill_erase_btn_container,alignment=Qt.AlignmentFlag.AlignCenter)

        self.fill_erase_button_dict.get("Fill Holes").clicked.connect(lambda checked : self.fill_holes_in_object(checked))
        
        self.fill_erase_button_dict.get("Erase").clicked.connect(lambda checked: self.erase_in_object(checked))

        self.slider = self.gui_helper.create_slider(Qt.Orientation.Horizontal,True,True,5,50,60,20,self.control_widget)
        self.slider.setValue(20)
        self.slider.valueChanged.connect(self.handle_slider_change)
        self.control_layout.addWidget(self.slider, alignment=Qt.AlignmentFlag.AlignCenter)

        self.edit_undo_btn_container,self.edit_undo_btn_dict = self.gui_helper.create_button_containers(["Undo",'Redo'],QVBoxLayout(),
                                                                                        self.object_select_btngrp,30,130,False,True,parent=self.control_widget)
        self.edit_undo_btn_container.layout().setSpacing(10)
        self.edit_undo_btn_dict['Undo'].clicked.connect(lambda clicked: self.undo_edits(clicked))
        self.edit_undo_btn_dict['Redo'].clicked.connect(lambda clicked: self.redo_edits(clicked))
        self.control_layout.addWidget(self.edit_undo_btn_container, alignment=Qt.AlignmentFlag.AlignCenter)

        self.control_layout.addStretch(1)
        self.status_label = self.gui_helper.create_label("Please edit ALL OBJECTS before clicking 'Proceed'.\nTip: Use 'Fill Holes' to complete missing areas in objects.\nUse 'Erase' to remove unwanted points or corrections.",parent=self.control_widget)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.control_layout.addWidget(self.status_label,alignment = Qt.AlignmentFlag.AlignCenter)
        self.control_layout.addStretch(1)

        self.edit_confirm_btn  = self.gui_helper.create_button('Proceed',False,self.object_select_btngrp,button_width=130,button_height=30,parent=self.control_widget)
        self.edit_confirm_btn.clicked.connect(lambda clicked: self.proceed_with_images(clicked))
        self.control_layout.addWidget(self.edit_confirm_btn,alignment = Qt.AlignmentFlag.AlignCenter)


        layout.addWidget(self.control_widget)

    
    def fill_holes_in_object(self,checked):
        print('fill holes')
        self.fill_erase_button_dict['Erase'].setChecked(False)


    def erase_in_object(self,checked):
        print('erase')
        self.fill_erase_button_dict['Fill Holes'].setChecked(False)


    def undo_edits(self,checked):
        print('undo_edits')
        self.fill_erase_button_dict['Fill Holes'].setChecked(False)
        self.fill_erase_button_dict['Erase'].setChecked(False)
        self.edit_manager.apply_edits_to_display(self.current_image_name,'Undo','Undo','Undo')
        self.update_display_image()


    def redo_edits(self,checked):
        print('redo_edits')
        self.fill_erase_button_dict['Fill Holes'].setChecked(False)
        self.fill_erase_button_dict['Erase'].setChecked(False)
        self.edit_manager.apply_edits_to_display(self.current_image_name,'Redo','Redo','Redo')
        self.update_display_image()


    def proceed_with_images(self,checked):

        self.control_widget.setVisible(False)
        self.progress_widget,self.progressbar = self.gui_helper.create_progressbar_container(txt="Processing Objects",visible=True,container_size=(None,100),parent=self.main_layout_bottomwidget.parentWidget())
        self.main_layout_bottomwidget.addWidget(self.progress_widget)

        self.worker_thread = WorkerThread(self.confirm_holes_and_erase)
        self.worker_thread.progress.connect(self.progressbar.setValue)
        self.worker_thread.finished.connect(self.close_window)

        self.worker_thread.start()


    def confirm_holes_and_erase(self,progress_signal):
        print('confirm_holes_and_erase')
        final_image_dict_fill_erase = {}

        for i,(image_name,org_image) in enumerate(self.extracted_object_dict.items()):
            current_img = org_image.copy()
            progress = int((i/len(self.extracted_object_dict))*100)
            progress_signal.emit(progress)
            size = self.edit_manager.cached_image_size_dict[image_name]

            commands = self.edit_manager.command_stack['Undo'].get(image_name,[])
            if commands:
                for command in commands:
                    if len(command)>1 and command[1] == 'fill_or_erase_point':

                        points , diameter , edit_type = command[2]

                        diameter = img_conv.get_brush_diameter(diameter,size,current_img)

                        org_points = [img_conv.resize_to_original_coordinates(point,size,current_img) for point in points]

                        current_img = EditOptions.fill_or_erase_point(current_img,(org_points,diameter,edit_type))

                final_image_dict_fill_erase[image_name] = current_img

            else:
                final_image_dict_fill_erase[image_name] = current_img

        return final_image_dict_fill_erase
            


    def close_window(self,final_obj_dict):

        self.close()
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.object_viewer = ObjectEnhancer(final_obj_dict)
        self.object_viewer.show()


