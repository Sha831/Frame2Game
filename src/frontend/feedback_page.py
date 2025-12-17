from PyQt6.QtWidgets import QVBoxLayout,QWidget,QLabel
from PyQt6.QtCore import Qt
import json
import copy



with open(r"src\frontend\config.json", "r") as f:
    theme = json.load(f)


from src.frontend_helper.gui_helpers import GuiHelpers



class FeedBack(QWidget):
    def __init__(self, output_path,no_of_asserts):
        super().__init__()
        self.output_path  = copy.deepcopy(output_path)
        self.no_of_objects = copy.deepcopy(no_of_asserts)
        self.gui_helper = GuiHelpers()


        self.setGeometry(100, 100, 900, 600)
        self.setFixedSize(900, 600)
        
        self.setStyleSheet(theme["MAINWINDOW_STYLE"])

        self.main_window_widget = QWidget()
        self.main_window_layout = self.gui_helper.create_layout(QVBoxLayout(self.main_window_widget),50,15)
        self.setLayout(self.main_window_layout)

        self.setup(self.main_window_layout)

    
    def setup(self,layout):

        main_widget,main_widget_layout = self.gui_helper.create_qwidget_container(QVBoxLayout(),5,5,width=700,height=400,parent=layout.parentWidget())
        main_widget.setObjectName("main_widget") 
        main_widget.setStyleSheet("""QWidget#main_widget {border: 2px solid gray; border-radius: 10}""")

        note_text = ("""
    <div style="text-align: center; font-size: 15pt; color: #ffffff;">
        Thank you for using Frame2Game!<br><br>
        <div style="text-align: center; font-size: 12pt; color: #ffffff;">
        This is an initial version of the tool, designed to quickly create basic game assets from any photo, making it easier for solo and indie developers to prototype games fast.
        I’m working on improving all edit features and making technical and architectural enhancements to increase performance. 
        Currently, GPU acceleration is only supported on NVIDIA GPUs. Your feedback will help accelerate these updates."
        I hope it becomes a valuable part of your creative workflow.<br><br>
        Please share your valuable feedback to help improve the tool.<br><br>
        If you’d like to share ideas, report bugs, improve the tool, or contribute in any way,
        you’d be a big part of making it better! You can reach out to the developer via GitHub or email.
    </div>
                """)
        note_label = QLabel(note_text)
        note_label.setWordWrap(True)
        main_widget_layout.addWidget(note_label)

        contact_label = QLabel("""
        <div style="text-align: center; font-size: 12pt; color: #ffffff;">
            Gmail : pseudo.gmail.com<br>
            GitHub : <a href='https://github.com/pseudogitlink'>@pseudogitlink</a>
        </div>
        """)
        contact_label.setOpenExternalLinks(True)
        contact_label.setWordWrap(True)
        main_widget_layout.addWidget(contact_label)

        layout.addWidget(main_widget,alignment = Qt.AlignmentFlag.AlignCenter)

        output_label = QLabel(f"""
        <div style="text-align: center; font-size: 12pt; color: #ff0000;">
            {self.no_of_objects} ssserts stored in path {self.output_path}
        </div>
        """)

        layout.addWidget(output_label,alignment = Qt.AlignmentFlag.AlignCenter)


