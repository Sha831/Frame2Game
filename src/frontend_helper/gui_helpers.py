from PyQt6.QtWidgets import QPushButton,QVBoxLayout,QWidget,QLabel,QGroupBox,QSizePolicy,QGridLayout,QProgressBar,QComboBox,QButtonGroup,QSlider,QLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap,QPainter,QCursor,QColor
import numpy as np
import json


from src.frontend_helper import image_converters as img_conv

with open(r"src\frontend\config.json", "r") as f:
    theme = json.load(f)


def style_font(widget: QWidget, size: int = 14, bold: bool = True):
    font = widget.font()
    font.setPointSize(size)
    font.setBold(bold)
    widget.setFont(font)


class GuiHelpers():

    def create_layout(self,layout_type:QLayout,margin:int=0,spacing:int=5):
        layout = layout_type
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)

        return layout

    def create_groupbox(self,groupbox_title:str,groupbox_layout:QLayout,width:int=None,height:int=None,style:str="",parent=None):
        groupbox = QGroupBox(groupbox_title,parent)
        groupbox.setStyleSheet(theme["GROUPBOX_STYLE"] + style )

        style_font(groupbox,8,False)

        if width:
            groupbox.setFixedWidth(width)
        if height:
            groupbox.setFixedHeight(height)

        layout = self.create_layout(groupbox_layout,5,0)
        groupbox.setLayout(layout)

        return groupbox,layout


    def create_button(self,button_name:str,chekable:bool=True,button_group:QButtonGroup=None,style:str="",button_width:int=180,button_height:int=25,parent=None):
        button = QPushButton(button_name,parent)
        button.setFixedWidth(button_width)
        button.setFixedHeight(button_height)
        button.setStyleSheet(theme["BUTTON_STYLE"] + style)
        button.setCheckable(chekable)

        if button_group:
            button_group.addButton(button)

        return button


    def create_button_containers(self,button_list:list,layout:QLayout,button_group:QButtonGroup,btn_height:int,btn_width:int,chekable:bool=True,visible:bool=True,row_nos:int=1,col_nos:int=1,btn_style:str="",parent=None):
        widget = QWidget(parent)
        widget_layout = self.create_layout(layout,2,spacing=10)
        widget.setLayout(widget_layout)
        button_dict = {}
        for i,btn in enumerate(button_list):
            row = i//col_nos
            col = i%col_nos
            button = self.create_button(btn,chekable,button_group,btn_style,btn_width,btn_height,widget)
            if row_nos>1 or col_nos>1:
                widget_layout.addWidget(button,row,col)
            else:
                widget_layout.addWidget(button)
            button_dict[btn]=button 
    
        widget.setVisible(visible)

        return widget,button_dict


    def create_qwidget_container(self,layout:QLayout,margin:int,spacing:int,visible:bool=True,width:int=None,height:int=None,parent=None):
        widget = QWidget(parent)
        widget.setVisible(visible)
        layout = self.create_layout(layout,margin,spacing)
        if width:
            widget.setFixedWidth(width)
        if height:
            widget.setFixedHeight(height)

        widget.setLayout(layout)

        return widget,layout



    def create_slider(self,orientation:Qt.Orientation,tracking:bool=True,visible:bool=True,min_range:int=0,max_range:int=100,width:int=300,height:int=20,parent=None):

        slider = QSlider(orientation,parent)
        slider.setFixedWidth(width)
        slider.setFixedHeight(height)
        slider.setRange(min_range, max_range)
        slider.setValue(0)
        slider.setSingleStep(5)
        slider.setPageStep(10)
        slider.setTracking(tracking)
        slider.setVisible(visible)

        return slider
    
    def create_slider_container(self,slider_name:str,slider_tooltip:str,orientation:Qt.Orientation,tracking:bool=True,visible:bool=True,width:int=300,height:int=20,range:tuple[int,int]=None,parent=None):
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        widget.setLayout(layout)

        label = QLabel(slider_name,parent=widget)
        label.setToolTip(slider_tooltip)
        label.setStyleSheet("QLabel {color: #ffffff; font-size: 12px;} ")
        if range:
            min_range , max_range = range
        else:
            min_range , max_range = (0,100)
        
        slider = self.create_slider(orientation,tracking,min_range=min_range,max_range=max_range,width=width,height=height,parent=widget)

        layout.addWidget(slider,alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label,alignment=Qt.AlignmentFlag.AlignCenter)

        widget.setVisible(visible)

        return widget,slider

    def create_label(self,label_text:str,word_wrap:bool=True,visible:bool=True,size_policy:tuple=(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred),tooltip:str=None,parent=None):
        label = QLabel(label_text,parent=parent)
        label.setWordWrap(word_wrap)
        label.setSizePolicy(size_policy[0],size_policy[1])
        label.setVisible(visible)

        if tooltip:
            label.setToolTip(tooltip)
        
        return label


    def create_image_thumbnail(self,cropped_img:np.ndarray,object_id:str,width:int=130,height:int=100,margin:int=5,spacing:int=2,parent=None):
        image_container = QWidget(parent)
        image_container_layout = QVBoxLayout(image_container)
        image_container_layout.setContentsMargins(margin,margin,margin,margin)
        image_container_layout.setSpacing(spacing)
        image_container.setFixedWidth(width)
        image_container.setFixedHeight(height)

        image_holder = QLabel()
        thumbnail = img_conv.cv2_to_qpixmap_display(cropped_img,max_size=(image_container.width(), image_container.height()))
        image_holder.setPixmap(thumbnail)
        image_holder.setStyleSheet(theme["LABEL_STYLE"] + " QLabel { border: 2px solid #555; border-radius: 3px; }")

        image_container_layout.addWidget(image_holder,alignment=Qt.AlignmentFlag.AlignCenter)

        image_label = QLabel(object_id)
        image_label.setWordWrap(True)
        image_container_layout.addWidget(image_label,alignment=Qt.AlignmentFlag.AlignCenter)

        return image_container
    
    def create_image_thumbnail_dropbox(self,cropped_img:np.ndarray,bbox_dict:dict,func:callable,width:int=130,height:int=100,margin:int=5,spacing:int=2,parent=None):
        image_container = QWidget(parent)
        image_container_layout = QVBoxLayout(image_container)
        image_container_layout.setContentsMargins(margin,margin,margin,margin)
        image_container_layout.setSpacing(spacing)
        image_container.setFixedWidth(width)
        image_container.setFixedHeight(height)

        image_holder = QLabel()
        thumbnail = img_conv.cv2_to_qpixmap_display(cropped_img,max_size=(image_container.width(), image_container.height()))
        image_holder.setPixmap(thumbnail)
        image_holder.setStyleSheet(theme["LABEL_STYLE"] + " QLabel { border: 2px solid #555; border-radius: 3px; }")

        image_container_layout.addWidget(image_holder,alignment=Qt.AlignmentFlag.AlignCenter)

        #creating drop box
        dropbox = QComboBox()
        dropbox.setStyleSheet("QComboBox { min-width: 100px; }")

        index_to_bbox = []

        # ---- Add placeholder ----
        dropbox.addItem("— Select Object —")
        index_to_bbox.append((None, None))   # placeholder entry

        # ---- Add real bbox entries ----
        for obj_name, bbox in bbox_dict.items():
            dropbox.addItem(obj_name)
            index_to_bbox.append((obj_name, bbox))

        # ---- Connect only once ----
        def on_change(index, func=func, mapping=index_to_bbox):
            obj_name, bbox = mapping[index]
            if obj_name is None:
                return  # Ignore the placeholder
            func(obj_name, bbox)

        dropbox.currentIndexChanged.connect(on_change)

        image_container_layout.addWidget(dropbox,alignment=Qt.AlignmentFlag.AlignCenter)

        return image_container


    def create_circular_cursor(self,diameter:int=20,widget:QWidget=None):
        # custom cursor
        pix = QPixmap(diameter, diameter)
        pix.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(1, 1, diameter-1, diameter-1)
        painter.end()

        cursor = QCursor(pix)

        if widget:
            widget.setCursor(cursor)

        return cursor
    

    def create_progressbar(self,range:tuple[int,int],text:str='%p%..Completed',initial_val:int=0,width:int=500,height:int=50,text_visible:bool=True,parent=None):

        self.progressbar = QProgressBar(parent=parent)
        start , end = range
        self.progressbar.setRange(start,end)
        self.progressbar.setValue(initial_val)
        self.progressbar.setFixedWidth(width)
        self.progressbar.setFixedHeight(height)
        self.progressbar.setTextVisible(text_visible)
        self.progressbar.setFormat(text)
        self.progressbar.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter )
        self.progressbar.setSizePolicy(self.progressbar.sizePolicy().horizontalPolicy(),self.progressbar.sizePolicy().verticalPolicy())
        

        return self.progressbar
    

    def create_progressbar_container(self,range:tuple[int,int]=(0,100),txt:str="",bar_width:int=500,bar_height:int=50,visible:bool=True,container_size:tuple[int,int]=(),parent=None):
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        widget.setLayout(layout)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        if container_size[0]:
            widget.setFixedWidth(container_size[0])
        if container_size[1]:
            widget.setFixedHeight(container_size[1])

        progressbar = self.create_progressbar(range,'%p%..Completed',0,bar_width,bar_height,True,parent=widget)

        label = self.create_label(txt,False,parent=widget)

        layout.addWidget(progressbar,alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label,alignment=Qt.AlignmentFlag.AlignCenter)

        widget.setVisible(visible)

        return widget,progressbar
        


    def create_slider_container_with_multiple_sliders(self,slider_list,orientation: Qt.Orientation,
        no_col: int,visible: bool = True,tracking: bool = True,
        width: int = 100,height: int = 10,slider_tooltip: str = '',parent=None):
        
        main_widget = QWidget(parent)
        main_layout = QGridLayout()
        main_widget.setLayout(main_layout)

        slider_dict = {}

        for i, slider_name in enumerate(slider_list):

            # Row/Col placement in grid
            row = i // no_col
            col = i % no_col

            widget , slider =self.create_slider_container(slider_name,"",Qt.Orientation.Horizontal,width=width,height=height,parent=main_widget)

            # Add to dict
            label = widget.findChild(QLabel)

            slider_dict[slider_name] = (slider , label)

            main_layout.addWidget(widget, row, col, alignment=Qt.AlignmentFlag.AlignCenter)

        main_widget.setVisible(visible)

        return main_widget, slider_dict

