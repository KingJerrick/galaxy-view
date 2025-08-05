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
from PyQt5.QtCore import QTimer, Qt, QObject, pyqtSignal,QThread
from PIL import Image
from PyQt5 import QtGui
from PyQt5.QtGui import QPixmap, QImage
import slot.Custom_Widgets as CS
from datetime import datetime
import time


import threading
import time
from PyQt5.QtCore import QObject, pyqtSignal

class ImageAcquisitionWorker(QObject):
    image_acquired = pyqtSignal(object)  # numpy.ndarray类型传递时用object更稳妥
    current_frame_signal = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.running = False
        self.frame_rate = 6
        self.exposure_time = 10
        self.cam = None
        self.current_frame = None
        self._thread = None

    def _acquisition_loop(self):
        if self.cam.AcquisitionFrameRate.is_writable():
            self.cam.AcquisitionFrameRate.set(self.frame_rate)
        if self.cam.ExposureTime.is_writable():
            self.cam.ExposureTime.set(self.exposure_time)

        self.cam.stream_on()

        while self.running:
            raw_image = self.cam.data_stream[0].get_image()
            if raw_image and raw_image.get_status() == 0:  # gx.GxFrameStatusList.SUCCESS通常是0
                rgb_image = raw_image.convert("RGB")
                numpy_image = rgb_image.get_numpy_array()
                if numpy_image is not None:
                    self.current_frame = numpy_image
                    self.image_acquired.emit(numpy_image)
            time.sleep(0.1)

        self.cam.stream_off()

    def start_acquisition(self):
        if self.cam is None:
            return
        if self.running:
            return  # 已经在运行

        self.running = True
        self._thread = threading.Thread(target=self._acquisition_loop, daemon=True)
        self._thread.start()

    def stop_acquisition(self):
        self.running = False
        if self._thread is not None:
            self._thread.join()  # 等待线程退出，防止资源冲突

    def restart_acquisition(self):
        if self.running:
            # 如果正在运行，先停止
            self.stop_acquisition()
        self.start_acquisition()

    def set_camera(self, cam):
        self.cam = cam

    def update_parameters(self, frame_rate, exposure_time):
        self.frame_rate = frame_rate
        self.exposure_time = exposure_time
        if self.cam is not None:
            if self.cam.AcquisitionFrameRate.is_writable():
                self.cam.AcquisitionFrameRate.set(frame_rate)
            if self.cam.ExposureTime.is_writable():
                self.cam.ExposureTime.set(exposure_time)

    def get_current_frame(self):
        if self.current_frame is not None:
            self.current_frame_signal.emit(self.current_frame)

class MainwindowAct(QMainWindow,ui.ui_MainWindow.Ui_MainWindow):
    def __init__(self):
        super(MainwindowAct, self).__init__()
        self.setupUi(self)
        self.camera_map = {}
        self.last_images = {}


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
        self.pushButton.clicked.connect(self.list)
        self.spinBox2.valueChanged.connect(self.change_parameters)
        self.spinBox3.valueChanged.connect(self.change_parameters)

    
    def change_parameters(self):
        frame_rate = self.spinBox3.value()
        exposure_time = self.spinBox2.value()
        for cam_info in self.camera_map.values():
            worker = cam_info.get("worker")
            if worker:
                worker.update_parameters(frame_rate, exposure_time)

    
    def list(self):
        if self.comboBox_CamerList.currentIndex() == -1:
            self.device_manager = gx.DeviceManager()
            dev_mum, self.dev_info_list = self.device_manager.update_device_list()

            if dev_mum == 0:
                text = '<font color="red">' + "未找到相机!" + '</font>'
                self.textEdit.append(text)
                QApplication.processEvents()

            for i, dev_info in enumerate(self.dev_info_list):
                display_name = dev_info.get("display_name", f"Camera {i + 1}")
                self.comboBox_CamerList.addItem(display_name, i)
        else:
            text = '<font color="red">' + "请勿重复查找相机!" + '</font>'
            self.textEdit.append(text)
            QApplication.processEvents()

    def toggle_group_content(self, groupbox, checked):
        """
        隐藏部分按键
        """
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
        # label.setText(f"camera{self.spinBox.value()}")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("border: 1px solid gray;")

        worker = ImageAcquisitionWorker()
        thread = QThread()
        worker.moveToThread(thread)

        camera_index = self.comboBox_CamerList.currentIndex()
        str_cn = self.dev_info_list[camera_index].get("sn")
        self.cam = self.device_manager.open_device_by_sn(str_cn)

        worker.set_camera(self.cam)  # 打开相机并设置

        worker.image_acquired.connect(lambda img, l=label: self.update_label(l, img))

        thread.started.connect(worker.start_acquisition)

        thread.start()


        label.closed.connect(self.close_camera)
        label.save.connect(self.save_image)
        label.pause.connect(self.pause_camera)

        self.camera_map[self.spinBox.value()] = {"sn":str_cn,
                                                 "label":label,
                                                 "worker":worker,
                                                 "thread":thread,
                                                 "num_pic":1,
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

    def close_camera(self, serial_number):
        if serial_number not in self.camera_map:
            self.textEdit.append(f"相机 {serial_number} 不存在")
            return

        info = self.camera_map[serial_number]

        # 停止线程
        if "worker" in info:
            info["worker"].stop_acquisition()
        if "thread" in info:
            info["thread"].quit()
            info["thread"].wait()

        # 关闭相机连接
        if "cam" in info:
            try:
                info["cam"].close_device()
                self.textEdit.append(f"相机 {serial_number} 已断开")
            except Exception as e:
                self.textEdit.append(f"关闭相机 {serial_number} 失败: {e}")

        # 删除 label（不需要手动 del，它的 parent 会被清理）
        label = info.get("label")
        if label:
            label.setParent(None)

        # 删除记录
        del self.camera_map[serial_number]
        if serial_number in self.last_images:
            del self.last_images[serial_number]

        self.textEdit.append(f"相机 {serial_number} 已关闭")
        self.textEdit.append(f"当前相机总数: {len(self.camera_map)}")

        self.update_label_sizes()


    def update_label(self, label, img):
        qt_img = QImage(img.data, img.shape[1], img.shape[0], QImage.Format_RGB888)
        label.setPixmap(QPixmap.fromImage(qt_img).scaled(label.size(), Qt.KeepAspectRatio))
        self.last_images[label.serial] = img


    def save_image(self,serial_number):
        if not self.verticalGroupBox_2.isChecked():
            sn = self.camera_labels[serial_number]['sn']
            num_pic = self.camera_labels[serial_number]['num_pic']
            file_name = f"{self.date}\\{sn}\\{num_pic}"
            self.camera_map[serial_number]["num_pic"] = num_pic+1
            self.last_images[serial_number].save(file_name)
            self.camera_map[serial_number]['worker'].restart_acquisition()

    def pause_camera(self,serial_number):
        self.camera_map[serial_number]['worker'].stop_acquisition()



    def closeEvent(self, event):
        for serial_number in list(self.camera_map.keys()):
            self.close_camera(serial_number)
        event.accept()  # 正常关闭窗口





