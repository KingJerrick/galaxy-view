# Copyright (C) 2024 - 2024 Jerrick Zhu, Inc. All Rights Reserved 
#
# @Time    : 2024/9/19 19:54
# @Author  : Jerrick Zhu
# @File    : Mainwindow.py
# @IDE     : PyCharm

# DEBUG = True
DEBUG = False
import numpy as np
import ui.ui_MainWindow
import os
import gxipy as gx
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QTextEdit, QLabel, QGridLayout
from PyQt5.QtCore import QTimer, Qt, QObject, pyqtSignal
from PIL import Image
from PyQt5 import QtGui
from PyQt5.QtGui import QPixmap
import slot.Custom_Widgets as CS
from datetime import datetime
import time


class ImageAcquisitionWorker(QObject):
    image_acquired = pyqtSignal(np.ndarray)  # 用于传递图像的信号
    current_frame_signal = pyqtSignal(np.ndarray)  # 用于显示当前帧的信号

    def __init__(self):
        super().__init__()
        self.running = False
        self.frame_rate = 6
        self.exposure_time = 10
        self.cam = None

    def start_acquisition(self):
        if self.cam is None:
            return

        # 设置帧率和曝光时间
        if self.cam.AcquisitionFrameRate.is_writable():
            self.cam.AcquisitionFrameRate.set(self.frame_rate)
        if self.cam.ExposureTime.is_writable():
            self.cam.ExposureTime.set(self.exposure_time)
        # if self.cam.BalanceWhiteAuto.is_implemented() and self.cam.BalanceWhiteAuto.is_writable():
        #     # 设置自动白平衡模式为 Continuous（持续自动调整）
        #     self.cam.BalanceWhiteAuto.set(gx.GxAutoEntry.ONCE)

        self.cam.stream_on()
        self.running = True
        while self.running:
            raw_image = self.cam.data_stream[0].get_image()
            if raw_image and raw_image.get_status() == gx.GxFrameStatusList.SUCCESS:
                rgb_image = raw_image.convert("RGB")
                numpy_image = rgb_image.get_numpy_array()
                if numpy_image is not None:
                    # 发射信号传递图像
                    self.current_frame = numpy_image  # 保存当前帧
                    self.image_acquired.emit(numpy_image)
            time.sleep(0.1)

        self.cam.stream_off()

    def stop_acquisition(self):
        self.running = False

    def set_camera(self, cam):
        self.cam = cam

    def update_parameters(self, frame_rate, exposure_time):
        if self.cam is None:
            self.frame_rate = frame_rate
            self.exposure_time = exposure_time
        else:
            if self.cam.AcquisitionFrameRate.is_writable():
                self.cam.AcquisitionFrameRate.set(frame_rate)
            if self.cam.ExposureTime.is_writable():
                self.cam.ExposureTime.set(exposure_time)
            # if self.cam.BalanceWhiteAuto.is_implemented() and self.cam.BalanceWhiteAuto.is_writable():
            #     # 设置自动白平衡模式为 Continuous（持续自动调整）
            #     self.cam.BalanceWhiteAuto.set(gx.GxAutoEntry.ONCE)


    def get_current_frame(self):
        # 将当前帧通过信号发射
        if self.current_frame is not None:
            self.current_frame_signal.emit(self.current_frame)


class MainwindowAct(QMainWindow,ui.ui_MainWindow.Ui_MainWindow):
    def __init__(self):
        super(MainwindowAct, self).__init__()
        self.setupUi(self)
        self.camera_map = {}

        self.grid_layout = self.gridGroupBox.layout()
        assert isinstance(self.grid_layout, QGridLayout), "gridGroupBox 必须设置为 GridLayout！"

        layout = self.textEdit.parent().layout()
        index = layout.indexOf(self.textEdit)
        layout.removeWidget(self.textEdit)
        self.textEdit.deleteLater()

        self.textEdit = CS.ClearableTextEdit(self)
        layout.insertWidget(index, self.textEdit)

        now = datetime.now()
        self.date = now.date()

        self.textEdit.append("不勾选保存选项,将以类似以下格式进行文件保存")
        self.textEdit.append(f"{self.date}\\camera_id\\1.bmp")
        self.textEdit.append("\n")
        self.textEdit.append("右键可清空")

        self.lineEdit.setText(f"{os.getcwd()}\\{self.date}")

        self.pushButton_4.clicked.connect(self.close)

        self.toggle_group_content(self.verticalGroupBox_3, False)
        self.verticalGroupBox_3.toggled.connect(lambda checked: self.toggle_group_content(self.verticalGroupBox_3, checked))
        self.toggle_group_content(self.gridGroupBox_2, False)
        self.gridGroupBox_2.toggled.connect(lambda checked: self.toggle_group_content(self.gridGroupBox_2, checked))

        self.pushButton_2.clicked.connect(self.add_camera_view)

    def toggle_group_content(self, groupbox, checked):
        def toggle_layout_items(layout):
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item.widget():
                    item.widget().setVisible(checked)
                elif item.layout():
                    toggle_layout_items(item.layout())  # 递归处理嵌套布局

        layout = groupbox.layout()
        if layout:
            toggle_layout_items(layout)

    def add_camera_view(self):
        if len(self.camera_map) >= 12:
            self.textEdit.append("最多支持12路相机")
            return

        if self.spinBox.value() in self.camera_map:
            self.textEdit.append(f"相机{self.spinBox.value()}已打开")
            return


        label = CS.CameraLabel(self.spinBox.value())
        label.setText(f"camera{self.spinBox.value()}")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("border: 1px solid gray;")

        label.closed.connect(self.close_camera)

        self.camera_map[self.spinBox.value()] = {"sn":"adjvafcc",
                                                 "label":label,
                                                 }

        self.update_label_sizes()

    def update_label_sizes(self):
        # 获取当前 label 列表（从 camera_map）
        # 按照编号升序排序 camera_map
        self.camera_labels = [self.camera_map[k]["label"] for k in sorted(self.camera_map.keys())]
        total = len(self.camera_labels)
        if total == 0:
            return

        container_width = self.gridGroupBox.width()
        container_height = self.gridGroupBox.height()

        # 单独处理 1 和 2 个 label 的特殊布局
        if total == 1:
            label_width, label_height = 1200, 800
            best_rows, best_cols = 1, 1
        elif total == 2:
            label_width, label_height = 800, 600
            best_rows, best_cols = 1, 2
        else:
            # 自动寻找最优布局
            best_rows, best_cols = None, None
            max_area = 0
            best_label_size = (0, 0)

            for cols in range(1, 5):  # 最多4列
                rows = (total + cols - 1) // cols
                if rows > 3:
                    continue

                spacing = 15
                available_width = container_width - (cols + 1) * spacing
                available_height = container_height - (rows + 1) * spacing

                label_width = available_width // cols
                label_height = available_height // rows
                aspect_ratio = label_width / label_height

                if 1.0 <= aspect_ratio <= 16 / 9:
                    area = label_width * label_height
                    if area > max_area:
                        max_area = area
                        best_rows, best_cols = rows, cols
                        best_label_size = (label_width, label_height)

            if best_rows is None:
                best_cols = min(total, 4)
                best_rows = (total + best_cols - 1) // best_cols
                spacing = 10
                best_label_size = (
                    (container_width - (best_cols + 1) * spacing) // best_cols,
                    (container_height - (best_rows + 1) * spacing) // best_rows
                )

            label_width, label_height = best_label_size

        # 清空旧布局
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        # 重新布局
        for idx, label in enumerate(self.camera_labels):
            row, col = divmod(idx, best_cols)
            self.grid_layout.addWidget(label, row, col)
            label.setFixedSize(label_width, label_height)

    def close_camera(self,serial_number):
        if serial_number not in self.camera_map:
            self.textEdit.append(f"相机 {serial_number} 不存在")
            return

        self.textEdit.append(f"相机 {serial_number} 已关闭")

        del self.camera_map[serial_number]
        self.textEdit.append(f"当前相机总数:{len(self.camera_map)}")

        self.update_label_sizes()



