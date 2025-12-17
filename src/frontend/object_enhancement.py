from PyQt6.QtWidgets import QVBoxLayout,QWidget,QLabel,QScrollArea,QHBoxLayout,QSizePolicy
from PyQt6.QtCore import Qt,QTimer
import json
import copy


from src.frontend_helper import image_converters as img_conv
from src.frontend_helper.gui_helpers import GuiHelpers
from src.backend.image_editmanager import EditManager
from src.backend.edit_options import EditOptions
from src.frontend.edited_objects import EditedObjectViewer
from src.backend_helpers.helper_thread import WorkerThread
from src.backend_helpers.path_helper import resource_path

path = resource_path(r"src\frontend\config.json")
with open(path, "r") as f:
    theme = json.load(f)




class ObjectEnhancer(QWidget):
    def __init__(self, extracted_objects):
        super().__init__()
        self.extracted_object_refined  = copy.deepcopy(extracted_objects)
        self.edit_manager = EditManager()
        self.gui_helper = GuiHelpers()
        self.display_size = None
        self.current_image_name = None
        self.slider_value_dict = {}


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
        for image_name in self.extracted_object_refined :
            image = self.extracted_object_refined [image_name]
            self.edit_manager.store_images_for_edits(image_name,image,self.display_size)


    
    def thumbnail_area(self,layout):

        self.thumbnail_group,self.thumbnail_layout = self.gui_helper.create_groupbox("IMAGE SELECT",QVBoxLayout(),200,style="QGroupBox { margin-top: 0px; }",parent=layout.parentWidget())

        self.thumb_scroll = QScrollArea(parent=self.thumbnail_group)
        self.thumb_scroll.setWidgetResizable(True)
        self.thumb_scroll.setStyleSheet(theme["SCROLLBAR_STYLE"])


        self.thumb_widget,self.thumb_widget_layout = self.gui_helper.create_qwidget_container(QVBoxLayout(),5,5,parent=self.thumbnail_group)
        self.thumb_widget_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        for image_name in self.extracted_object_refined :
            thumb_image = self.extracted_object_refined.get(image_name)
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

        # Add final group to main layout
        layout.addWidget(self.display_group)



    def on_thumbnail_click(self,image_name):

        self.current_image_name = image_name

        if self.current_image_name in self.slider_value_dict:
            for slider_name,(slider,label) in self.slider_dict.items():
                val = self.slider_value_dict[self.current_image_name].get(slider_name)
                slider.setValue(0 if val is None else val)

        self.update_display_image()


    def update_display_image(self):

        display_image = self.edit_manager.get_cached_image_to_display(self.current_image_name)
        image = img_conv.cv2_to_qpixmap_display(display_image)
        self.image_display.setPixmap(image)
    

    def control_area(self, layout):

        self.control_widget,self.control_layout = self.gui_helper.create_qwidget_container(QHBoxLayout(),5,5,height=130,parent=layout.parentWidget())
        self.control_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)


        self.status_label = self.gui_helper.create_label("Ensure all objects are edited before pressing 'Proceed'.\nClicking 'Proceed' will auto-save and apply changes to each image where edits were made.",parent=self.control_widget)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.control_layout.addWidget(self.status_label)
        

        self.slider_list = ['Denoising','Sharpen/Darken Edges','White Balance','Color Balance','Saturation','Refine Edges']

        self.slider_container , self.slider_dict = self.gui_helper.create_slider_container_with_multiple_sliders(self.slider_list,Qt.Orientation.Horizontal,no_col=3,tracking=True,parent=self.control_widget)
        self.control_layout.addWidget(self.slider_container, alignment=Qt.AlignmentFlag.AlignCenter)
        for slider_name , (slider,label) in self.slider_dict.items():
            slider.valueChanged.connect(lambda val,name=slider_name ,lbl=label:self.set_slider_change_fun(name,val,lbl))


        self.edit_confirm_btn  = self.gui_helper.create_button('Proceed',False,button_width=130,button_height=30,parent=self.control_widget)
        self.edit_confirm_btn.clicked.connect(lambda clicked: self.proceed_with_edits(clicked))
        self.control_layout.addWidget(self.edit_confirm_btn,alignment = Qt.AlignmentFlag.AlignCenter)


        layout.addWidget(self.control_widget)



    def set_slider_change_fun(self,slider_name,val,label):

        if self.current_image_name:
            label.setText(f'{slider_name}-{val}')
            if self.current_image_name:
                self.slider_value_dict.setdefault(self.current_image_name,{})[slider_name]=val

            self.edit_manager.apply_edits_to_display(self.current_image_name,'Image','add_full_image_edits',self.slider_value_dict[self.current_image_name])

            self.update_display_image()



    def proceed_with_edits(self,clicked):
        self.control_widget.setVisible(False)
        self.progress_widget,self.progressbar = self.gui_helper.create_progressbar_container(txt="Processing Objects",visible=True,container_size=(None,100),parent=self.main_layout_bottomwidget.parentWidget())
        self.main_layout_bottomwidget.addWidget(self.progress_widget)

        self.worker_thread = WorkerThread(self.confirm_edited_images)
        self.worker_thread.progress.connect(self.progressbar.setValue)
        self.worker_thread.finished.connect(self.close_window)

        self.worker_thread.start()


    def confirm_edited_images(self,progress_signal):

        final_edited_image_dict = {}

        for i,(image_name,image) in enumerate(self.extracted_object_refined.items()):
            current_image = image.copy()
            progress = int((i/len(self.extracted_object_refined))*100)
            progress_signal.emit(progress)
            if self.edit_manager.command_stack['Undo'].get(image_name):
                edits = self.edit_manager.command_stack['Undo'][image_name][0][2]
                edited_image = EditOptions().add_full_image_edits(current_image,edits)
                edited_image_tight_bound = img_conv.crop_to_tight_bounds(edited_image)

            else:
                edited_image = current_image 
                edited_image_tight_bound = img_conv.crop_to_tight_bounds(edited_image)

            final_edited_image_dict[image_name] = edited_image_tight_bound

        return final_edited_image_dict



    def close_window(self,final_obj_dict):

        self.close()
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.edited_object_viewer = EditedObjectViewer(final_obj_dict)
        self.edited_object_viewer.show()
    

