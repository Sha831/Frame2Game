
from PyQt6.QtCore import QThread, pyqtSignal



class WorkerThread(QThread):
    progress = pyqtSignal(int) 
    finished = pyqtSignal(object)

    def __init__(self,func):
        super().__init__()
        self.func = func

    def run(self):

        result = self.func(self.progress)

        self.finished.emit(result)



class WorkerThreadDownload(QThread):
    progress = pyqtSignal(int) 
    finished = pyqtSignal(object)

    def __init__(self,func):
        super().__init__()
        self.func = func

    def run(self):

        result , text = self.func(self.progress)

        self.finished.emit((result,text))


class WorkerThreadYolo(QThread):
    progress = pyqtSignal(int) 
    finished = pyqtSignal(object)

    def __init__(self,func):
        super().__init__()
        self.func = func

    def run(self):

        result = self.func()

        self.finished.emit(result)