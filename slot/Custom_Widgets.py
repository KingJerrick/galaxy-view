"""
自定义控件库
"""
from PyQt5.QtWidgets import QLabel, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, QWidget,QMenu
from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtCore import pyqtSignal , Qt

class ClickableLabel(QLabel):
    """
    提升控件，可点击的label类，返回点击点对应图像的坐标
    """
    pointClicked = pyqtSignal(int,int)
    def __init__(self, parent=None):
        super(ClickableLabel, self).__init__(parent)
        self.scale_ratio = (1.0,1.0)
        self.image = None

    def setImage(self, image):
        self.image = image
        h_image, w_image = image.shape[:2]
        h_label, w_label = self.height(), self.width()
        self.scale_ratio = (w_image / w_label, h_image / h_label)

    def mousePressEvent(self, event):
        if self.image is None:
            return
        x = int(event.pos().x()*self.scale_ratio[0])
        y = int(event.pos().y()*self.scale_ratio[1])
        if 0 <= x < self.image.shape[1] and 0 <= y < self.image.shape[0]:
            self.pointClicked.emit(x,y)

class ClearableTextEdit(QTextEdit):
    """
    提升控件带清空的textedit
    """
    def contextMenuEvent(self, event: QContextMenuEvent):
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        clear_action = menu.addAction("clear")
        action = menu.exec_(event.globalPos())
        if action == clear_action:
            self.clear()

class CameraLabel(QLabel):
    """
    相机专用label
    """
    closed = pyqtSignal(int)
    pause = pyqtSignal(int)
    save = pyqtSignal(int)
    def __init__(self, serial, parent=None):
        super().__init__(parent)
        self.serial = serial
        self.on_pause = None      # 回调函数（暂停）
        self.on_save = None       # 回调函数（保存）
        self.on_close = None      # 回调函数（关闭）

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        pause_action = menu.addAction("暂停")
        save_action = menu.addAction("保存图像")
        close_action = menu.addAction("关闭相机")
        action = menu.exec_(event.globalPos())

        if action == pause_action:
            self.pause.emit(self.serial)
            
        elif action == save_action:
            self.save.emit(self.serial)

        elif action == close_action:
            self.closed.emit(self.serial)
