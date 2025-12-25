# Copyright (C) 2023 - 2025 Jerrick Zhu, Inc. All Rights Reserved 
#
# @Time    : 2024/9/19 19:54
# @Author  : Jerrick Zhu
# @File    : Mainwindow.py
# @IDE     : PyCharm

# DEBUG = True
DEBUG = False
version = "v2.3.1_Beta"        #版本号在此修改

import numpy as np
import ui.ui_MainWindow
import ui.ui_save
import os
import gxipy as gx
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QTextEdit, QLabel, QGridLayout,QWidget
from PyQt5.QtCore import QTimer, Qt, QObject, pyqtSignal,QThread,QUrl
from PIL import Image
from PyQt5 import QtGui
from PyQt5.QtGui import QPixmap, QImage,QDesktopServices
import slot.Custom_Widgets as CS
from datetime import datetime
import time
import slot.utils

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

class SaveWindow(QWidget,ui.ui_save.Ui_Form):
    Change_ED_signal = pyqtSignal(int)  
    Change_EN_signal = pyqtSignal(int)
    Change_TYPE_signal = pyqtSignal(int)

    def __init__(self):
        super(SaveWindow, self).__init__()
        self.setupUi(self)
        self.ED = 0
        self.EN = 0
        self.TYPE = 0
        self.change_lineedit()
        
        self.radioButton_ED_1.toggled.connect(self.change_al)
        self.radioButton_ED_2.toggled.connect(self.change_al)
        self.radioButton_EN_1.toggled.connect(self.change_al)
        self.radioButton_EN_2.toggled.connect(self.change_al)
        self.radioButton_EN_3.toggled.connect(self.change_al)
        self.radioButton_T_1.toggled.connect(self.change_al)
        self.radioButton_T_2.toggled.connect(self.change_al)
        self.radioButton_T_3.toggled.connect(self.change_al)

        self.pushButton.clicked.connect(self.close)

    def change_al(self):
        ser = self.sender()
        if ser.isChecked():
            if ser == self.radioButton_ED_1:
                self.ED = 0
            elif ser == self.radioButton_ED_2:
                self.ED = 1
            elif ser == self.radioButton_EN_1:
                self.EN = 0
            elif ser == self.radioButton_EN_2:
                self.EN = 1
            elif ser == self.radioButton_EN_3:
                self.EN = 2
            elif ser == self.radioButton_T_1:
                self.TYPE = 0
            elif ser == self.radioButton_T_2:
                self.TYPE = 1
            else:
                self.TYPE = 2
        self.change_lineedit()


    def change_lineedit(self):
        if not self.ED:
            file_dir = "sn"
        else:
            file_dir = "camera_1"

        if self.EN == 0:
            file_name = "1"
        elif self.EN == 1:
            file_name = "Ⅰ"
        else:
            file_name = "a"
        
        if self.TYPE == 0:
            file_type = "bmp"
        elif self.TYPE == 1:
            file_type = "jpg"
        else:
            file_type = "png"
        
        file = f'\\{file_dir}\\{file_name}.{file_type}'
        self.lineEdit.setText(file)

    def closeEvent(self, event):
        self.Change_ED_signal.emit(self.ED)
        self.Change_EN_signal.emit(self.EN)
        self.Change_TYPE_signal.emit(self.TYPE)


class MainwindowAct(QMainWindow,ui.ui_MainWindow.Ui_MainWindow):
    def __init__(self):
        super(MainwindowAct, self).__init__()

        self.setupUi(self)
        self.camera_map = {}
        self.last_images = {}
        self.label_4.setText(f"Copyright © 2023-2025 Jerrick Zhu, All rights reserved.    {version}")


        self.grid_layout = self.gridGroupBox.layout()
        assert isinstance(self.grid_layout, QGridLayout), "gridGroupBox 必须设置为 GridLayout！"

        layout = self.textEdit.parent().layout()    ###替换控件
        index = layout.indexOf(self.textEdit)
        layout.removeWidget(self.textEdit)
        self.textEdit.deleteLater()
        self.textEdit = CS.ClearableTextEdit(self)
        layout.insertWidget(index, self.textEdit)   ###替换控件


        layout = self.lineEdit.parent().layout()
        index = layout.indexOf(self.lineEdit)
        layout.removeWidget(self.lineEdit)
        self.lineEdit.deleteLater()
        self.lineEdit = CS.FolderSelectLineEdit(self)
        layout.insertWidget(index, self.lineEdit)

        now = datetime.now()
        self.date = now.date()

        self.textEdit.append("不勾选保存选项,将以类似以下格式进行文件保存")
        self.textEdit.append(f"{self.date}\\camera_id\\1.bmp")
        self.textEdit.append("\n")
        self.textEdit.append("同步保存,将以类似以下格式进行文件保存")
        self.textEdit.append(f"{self.date}\\camera_id\\s1.bmp")
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
        # self.pushButton.clicked.connect(self.save_image)
        self.spinBox_2.valueChanged.connect(self.change_parameters)
        self.spinBox_3.valueChanged.connect(self.change_parameters)
        self.pushButton_5.clicked.connect(self.pause_Synchronous)
        self.pushButton_6.clicked.connect(self.save_Synchronous)
        self.pushButton_3.clicked.connect(self.save_Options)
        self.pushButton_7.clicked.connect(self.open_folder)

        self.ED = 0
        self.EN = 0
        self.TYPE = 0

        self.savewindow = SaveWindow()
        self.savewindow.Change_ED_signal.connect(lambda v:setattr(self,"ED",v))
        self.savewindow.Change_EN_signal.connect(lambda v:setattr(self,"EN",v))
        self.savewindow.Change_TYPE_signal.connect(lambda v:setattr(self,"TYPE",v))

        self.Synchronous_num = 1
        self.IS_Synchronous = False

    
    def change_parameters(self):
        frame_rate = self.spinBox_3.value()
        exposure_time = self.spinBox_2.value()
        for cam_info in self.camera_map.values():
            worker = cam_info.get("worker")
            if worker:
                worker.update_parameters(frame_rate, exposure_time)

    
    def list(self):
        if self.comboBox.currentIndex() == -1:
            self.device_manager = gx.DeviceManager()
            dev_mum, self.dev_info_list = self.device_manager.update_device_list()

            if dev_mum == 0:
                text = '<font color="red">' + "未找到相机!" + '</font>'
                self.textEdit.append(text)
                QApplication.processEvents()

            for i, dev_info in enumerate(self.dev_info_list):
                display_name = dev_info.get("display_name", f"Camera {i + 1}")
                self.comboBox.addItem(display_name, i)
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

        cam_id = self.spinBox.value()
        if cam_id in self.camera_map:
            self.textEdit.append(f"相机编号 {cam_id} 已打开")
            return

        camera_index = self.comboBox.currentIndex()
        if camera_index == -1:
            self.textEdit.append("请先枚举并选择相机")
            return

        str_sn = self.dev_info_list[camera_index].get("sn")
        for info in self.camera_map.values():
            if str_sn == info['sn']:
                self.textEdit.append(f"序列号 {str_sn} 的相机已在运行中")
                return

        try:
            # 1. 打开相机硬件
            cam_obj = self.device_manager.open_device_by_sn(str_sn)

            # 2. 创建 UI 标签
            label = CS.CameraLabel(cam_id)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("border: 1px solid gray;")

            # 3. 初始化工作线程
            worker = ImageAcquisitionWorker()
            thread = QThread()
            worker.moveToThread(thread)
            worker.set_camera(cam_obj)  # 传入当前打开的对象

            # 4. 绑定信号
            worker.image_acquired.connect(lambda img, l=label: self.update_label(l, img))
            thread.started.connect(worker.start_acquisition)

            label.closed.connect(self.close_camera)
            label.save.connect(self.save_image)
            label.pause.connect(self.pause_camera)

            # 5. 保存到 map (注意这里保存了 cam 对象)
            self.camera_map[cam_id] = {
                "sn": str_sn,
                "label": label,
                "worker": worker,
                "thread": thread,
                "cam": cam_obj,  # 必须保存引用以便关闭
                "num_pic": 1,
            }

            # 6. 启动并刷新布局
            thread.start()
            self.update_label_sizes()
            self.textEdit.append(f"相机 {cam_id} (SN:{str_sn}) 开启成功")

        except Exception as e:
            self.textEdit.append(f'<font color="red">开启相机失败: {str(e)}</font>')

    def update_label_sizes(self):
        # 按照编号升序获取所有当前有效的 label
        sorted_keys = sorted(self.camera_map.keys())
        active_labels = [self.camera_map[k]["label"] for k in sorted_keys]
        total = len(active_labels)

        if total == 0:
            # 如果没相机了，清空布局即可
            while self.grid_layout.count():
                item = self.grid_layout.takeAt(0)
                if item.widget(): item.widget().hide()
            return

        container_width = self.gridGroupBox.width()
        container_height = self.gridGroupBox.height()

        # 计算行列数
        if total == 1:
            best_rows, best_cols = 1, 1
        elif total == 2:
            best_rows, best_cols = 1, 2
        elif total <= 4:
            best_rows, best_cols = 2, 2
        elif total <= 6:
            best_rows, best_cols = 2, 3
        elif total <= 9:
            best_rows, best_cols = 3, 3
        else:
            best_rows, best_cols = 3, 4

        spacing = 10
        label_width = (container_width - (best_cols + 1) * spacing) // best_cols
        label_height = (container_height - (best_rows + 1) * spacing) // best_rows

        # 重新填充布局前，先清空现有布局关系（不删除对象）
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.takeAt(i)

        # 重新按计算好的行列添加
        for idx, label in enumerate(active_labels):
            row, col = divmod(idx, best_cols)
            self.grid_layout.addWidget(label, row, col)
            label.setFixedSize(label_width, label_height)
            label.show()  # 确保可见=

    def close_camera(self, cam_id):
        if cam_id not in self.camera_map:
            return

        info = self.camera_map[cam_id]

        # 1. 停止采集逻辑和线程
        if "worker" in info:
            info["worker"].stop_acquisition()
        if "thread" in info:
            info["thread"].quit()
            info["thread"].wait()  # 等待线程安全退出

        # 2. 关键：关闭硬件连接，释放 SDK 句柄
        if "cam" in info and info["cam"] is not None:
            try:
                info["cam"].close_device()
                self.textEdit.append(f"相机 {cam_id} 硬件已安全释放")
            except Exception as e:
                self.textEdit.append(f"释放相机硬件异常: {e}")

        # 3. 从 UI 布局中移除标签
        label = info.get("label")
        if label:
            self.grid_layout.removeWidget(label)
            label.setParent(None)
            label.deleteLater()

        # 4. 清理内存记录
        del self.camera_map[cam_id]
        if cam_id in self.last_images:
            del self.last_images[cam_id]

        self.textEdit.append(f"相机 {cam_id} 已完全关闭")
        self.update_label_sizes()


    def update_label(self, label, img):
        qt_img = QImage(img.data, img.shape[1], img.shape[0], QImage.Format_RGB888)
        label.setPixmap(QPixmap.fromImage(qt_img).scaled(label.size(), Qt.KeepAspectRatio))
        self.last_images[label.serial] = img


    def save_image(self,serial_number):
        file_dir = self.lineEdit.text()
        if self.IS_Synchronous:
            num_pic = self.Synchronous_num
        else:
            num_pic = self.camera_map[serial_number]['num_pic']
            self.camera_map[serial_number]["num_pic"] = num_pic+1

        if not self.ED:
            extension_dir = self.camera_map[serial_number]['sn']
        else:
            extension_dir = f"camera_{serial_number}"

        if self.EN == 0:
            extension_name = str(num_pic)
        elif self.EN == 1:
            extension_name = slot.utils.int_to_roman(num_pic)
        else:
            extension_name = slot.utils.int_to_letters(num_pic)
        
        if self.TYPE == 0:
            type_pic = "bmp"
        elif self.TYPE == 1:
            type_pic = "jpg"
        else:
            type_pic = "png"
        
        if self.IS_Synchronous:
            file_name = f"{file_dir}\\{extension_dir}\\s{extension_name}.{type_pic}"
        else:
            file_name = f"{file_dir}\\{extension_dir}\\{extension_name}.{type_pic}"

        folder_path = f"{file_dir}\\{extension_dir}"
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)  # 可以递归创建多级目录

        img = Image.fromarray(self.last_images[serial_number])
        img.save(file_name)
        self.camera_map[serial_number]['worker'].restart_acquisition()

    def pause_camera(self,serial_number):
        self.camera_map[serial_number]['worker'].stop_acquisition()


    def pause_Synchronous(self):
        if not len(self.camera_map):
            self.textEdit.append("至少打开一个相机！")
            return
        for serial_number in list(self.camera_map.keys()):
            self.pause_camera(serial_number)
    
    def save_Synchronous(self):
        if not len(self.camera_map):
            self.textEdit.append("至少打开一个相机！")
            return
        self.IS_Synchronous = True
        for serial_number in list(self.camera_map.keys()):
            self.save_image(serial_number)
        self.IS_Synchronous = False
        self.Synchronous_num = self.Synchronous_num + 1 

    def save_Options(self):
        self.savewindow.show()

    def open_folder(self):
        file_dir = self.lineEdit.text()
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)  # 可以递归创建多级目录
        QDesktopServices.openUrl(QUrl.fromLocalFile(file_dir))

    def closeEvent(self, event):
        for serial_number in list(self.camera_map.keys()):
            self.close_camera(serial_number)
        event.accept()  # 正常关闭窗口

