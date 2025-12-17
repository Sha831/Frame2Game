from PyQt6.QtWidgets import QVBoxLayout,QWidget,QLabel,QScrollArea,QHBoxLayout,QSizePolicy,QGridLayout,QButtonGroup,QSlider
from PyQt6.QtCore import Qt,QTimer
import json
import copy


from src.frontend_helper import image_converters as img_conv
from src.frontend_helper.gui_helpers import GuiHelpers
from src.backend.image_editmanager import EditManager
from src.backend.edit_options import EditOptions
from src.frontend.object_style import ObjectStyle
from src.backend_helpers.helper_thread import WorkerThread


with open(r"src\frontend\config.json", "r") as f:
    theme = json.load(f)



class EditedObjectViewer(QWidget):
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
            self.edit_manager.store_images_for_edits(image_name,image)


    
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

        self.size_control_container , self.size_control_slider =self.gui_helper.create_slider_container('Resize Image using slider or standard size buttons',"",Qt.Orientation.Horizontal,True,width=200,height=15,range=(-100,100),parent=self.control_widget)
        self.size_control_slider.setValue(0)
        self.size_control_slider.setPageStep(20)
        self.size_control_slider.setTickPosition(QSlider.TickPosition.TicksBelow)  # Horizontal slider
        self.size_control_slider.setTickInterval(20)    
        self.size_control_slider.setToolTip(str(self.size_control_slider.value()))
        self.size_control_slider.valueChanged.connect(lambda val: self.image_size_with_slider(val))

        buttons = ['Tiny','Small','Medium','Large','Huge','Original']
        self.size_button_grp = QButtonGroup()
        self.size_button_grp.setExclusive(True)
        self.size_button_container ,self.size_button_dict  = self.gui_helper.create_button_containers(buttons,QGridLayout(),self.size_button_grp,24,100,row_nos=2,col_nos=3,btn_style="QPushButton{font-size: 12px;}",parent=self.size_control_container)
        for button_name,button in self.size_button_dict.items():
            button.clicked.connect(lambda clicked,btn_name=button_name: self.standard_image_size(clicked,btn_name))
        self.size_control_container.layout().addWidget(self.size_button_container)
        self.control_layout.addWidget(self.size_control_container)

        self.proceed_with_size_btn = self.gui_helper.create_button('Proceed',False,self.size_button_grp,parent=self.control_widget)
        self.proceed_with_size_btn.clicked.connect(lambda clicked: self.proceed_with_final_size(clicked))
        self.control_layout.addWidget(self.proceed_with_size_btn)

        layout.addWidget(self.control_widget)


    def standard_image_size(self,clicked,btn_name):
        if self.current_image_name:
            self.edit_manager.apply_edits_to_display(self.current_image_name,'Assert','apply_auto_or_manual_resize',btn_name)
            self.update_display_image()

    
    def image_size_with_slider(self,val):
        if self.current_image_name:
            self.edit_manager.apply_edits_to_display(self.current_image_name,'Assert','apply_auto_or_manual_resize',val)
            self.update_display_image()


    def proceed_with_final_size(self,clicked):
        self.control_widget.setVisible(False)
        self.progress_widget,self.progressbar = self.gui_helper.create_progressbar_container(txt="Processing Objects",visible=True,container_size=(None,100),parent=self.main_layout_bottomwidget.parentWidget())
        self.main_layout_bottomwidget.addWidget(self.progress_widget)

        self.worker_thread = WorkerThread(self.resize_original_image)
        self.worker_thread.progress.connect(self.progressbar.setValue)
        self.worker_thread.finished.connect(self.close_window)

        self.worker_thread.start()


    def resize_original_image(self,progress_signal):

        final_edited_image_dict = {}

        for i,(image_name,image) in enumerate(self.extracted_object_refined.items()):
            current_image = image.copy()
            progress = int((i/len(self.extracted_object_refined))*100)
            progress_signal.emit(progress)

            if self.edit_manager.command_stack['Undo'].get(image_name):
                edit = self.edit_manager.command_stack['Undo'][image_name][0][2]
                edited_image = EditOptions().apply_auto_or_manual_resize(current_image,edit)
                edited_image_tight_bound = img_conv.crop_to_tight_bounds(edited_image)

            else:
                edited_image = current_image 
                edited_image_tight_bound = img_conv.crop_to_tight_bounds(edited_image)

            final_edited_image_dict[image_name] = edited_image_tight_bound

        return final_edited_image_dict


    def close_window(self,final_obj_dict):

        self.close()
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.object_style_viewer = ObjectStyle(final_obj_dict)
        self.object_style_viewer.show()
        

