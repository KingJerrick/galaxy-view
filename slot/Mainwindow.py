# Copyright (C) 2024 - 2024 Jerrick Zhu, Inc. All Rights Reserved 
#
# @Time    : 2024/9/19 19:54
# @Author  : Jerrick Zhu
# @File    : Mainwindow.py
# @IDE     : PyCharm

# DEBUG = True
DEBUG = False

import ui.ui_MainWindow
import gxipy as gx
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog
from PyQt5.QtCore import QTimer
from PIL import Image
from PyQt5 import QtGui
from PyQt5.QtGui import QPixmap

class MainwindowAct(QMainWindow,ui.ui_MainWindow.Ui_MainWindow):
    def __init__(self):
        super(MainwindowAct, self).__init__()
        self.setupUi(self)
        self.spinBox.setMaximum(4)
        self.spinBox.setMinimum(1)
        self.pushButton_2.setEnabled(False)
        self.pushButton_3.setEnabled(False)
        self.pushButton_4.setEnabled(False)
        self.pushButton_5.setEnabled(False)
        self.pushButton_6.setEnabled(False)
        self.pushButton_7.setEnabled(False)
        self.pushButton_8.setEnabled(False)
        self.pushButton_9.setEnabled(False)
        self.pushButton_10.setEnabled(False)

        for i in range(4):
            setattr(self, f'IS_label{i + 1}', True)
        self.timer_1 = QTimer(self)
        self.timer_2 = QTimer(self)
        self.timer_3 = QTimer(self)
        self.timer_4 = QTimer(self)


        self.comboBox.currentIndexChanged.connect(self.change_camera)
        self.spinBox.valueChanged.connect(self.change_label)
        self.pushButton.clicked.connect(self.list)
        self.pushButton_2.clicked.connect(self.open_close)
        self.pushButton_3.clicked.connect(self.timeout_1)
        self.pushButton_5.clicked.connect(self.timeout_2)
        self.pushButton_7.clicked.connect(self.timeout_3)
        self.pushButton_4.clicked.connect(self.save_img1)
        self.pushButton_6.clicked.connect(self.save_img2)
        self.pushButton_8.clicked.connect(self.save_img3)
        self.pushButton_10.clicked.connect(self.save_img4)



    def change_camera(self,index):
        self.camera_index = index
        if getattr(self,f'IS_camera{index+1}') and getattr(self,f'IS_label{self.spinBox.value()}'):
            self.pushButton_2.setEnabled(True)
            self.pushButton_2.setText("打开相机")
        elif not getattr(self,f'IS_label{self.spinBox.value()}'):
            self.pushButton_2.setEnabled(True)
            self.pushButton_2.setText("关闭相机")
        else:
            self.pushButton_2.setEnabled(False)

    def change_label(self,value):
        if getattr(self,f'IS_camera{self.camera_index+1}') and getattr(self,f'IS_label{value}'):
            self.pushButton_2.setEnabled(True)
            self.pushButton_2.setText("打开相机")
        elif not getattr(self,f'IS_label{value}'):
            self.pushButton_2.setEnabled(True)
            self.pushButton_2.setText("关闭相机")
        else:
            self.pushButton_2.setEnabled(False)




    def list(self):
        self.comboBox.clear()
        self.device_manager = gx.DeviceManager()
        dev_mum, self.dev_info_list = self.device_manager.update_device_list()

        if DEBUG:
            dev_mum = 5

        if dev_mum == 0:
            text = '<font color="red">' + "未找到相机!" + '</font>'
            self.textEdit.append(text)
            QApplication.processEvents()
        else: self.pushButton_2.setEnabled(True)

        for i in range(dev_mum):
            setattr(self,f'IS_camera{i+1}',True)
            self.comboBox.addItem(f"Camera {i + 1}")




    def open_close(self):
        Is_open = self.pushButton_2.text()
        if Is_open == "打开相机":
            label_num = self.spinBox.value()
            if label_num == 1:
                if DEBUG:
                    self.label_c1.setText("1")
                else:
                    str_cn = self.dev_info_list[self.camera_index].get("sn")
                    self.cam_1 = self.device_manager.open_device_by_sn(str_cn)
                    self.cam_1.ExposureTime.set(self.spinBox_2.value())
                    self.cam_1.stream_on()
                    self.timer_1.timeout.connect(self.display_1image)
                    self.timer_1.start(1000/(self.spinBox_3.value()))
                    self.IS_label1 = False
                    setattr(self, f'IS_camera{self.camera_index + 1}', False)
                    self.label1_num = self.camera_index
                    self.pushButton_2.setText("关闭相机")
                self.pushButton_3.setEnabled(True)
            elif label_num == 2:
                if DEBUG:
                    self.label_c2.setText("1")
                else:
                    str_cn = self.dev_info_list[self.camera_index].get("sn")
                    self.cam_2 = self.device_manager.open_device_by_sn(str_cn)
                    self.cam_2.ExposureTime.set(self.spinBox_2.value())
                    self.cam_2.stream_on()
                    self.timer_2.timeout.connect(self.display_2image)
                    self.timer_2.start(1000 / (self.spinBox_3.value()))
                    self.IS_label2 = False
                    setattr(self, f'IS_camera{self.camera_index + 1}', False)
                    self.label2_num = self.camera_index
                    self.pushButton_2.setText("关闭相机")
                self.pushButton_5.setEnabled(True)
            elif label_num == 3:
                str_cn = self.dev_info_list[self.camera_index].get("sn")
                self.cam_3 = self.device_manager.open_device_by_sn(str_cn)
                self.cam_3.ExposureTime.set(self.spinBox_2.value())
                self.cam_3.stream_on()
                self.timer_3.timeout.connect(self.display_3image)
                self.timer_3.start(1000 / (self.spinBox_3.value()))
                self.IS_label3 = False
                setattr(self, f'IS_camera{self.camera_index + 1}', False)
                self.label3_num = self.camera_index
                self.pushButton_2.setText("关闭相机")
                self.pushButton_7.setEnabled(True)
            else :
                str_cn = self.dev_info_list[self.camera_index].get("sn")
                self.cam_4 = self.device_manager.open_device_by_sn(str_cn)
                self.cam_4.ExposureTime.set(self.spinBox_2.value())
                self.cam_4.stream_on()
                self.timer_4.timeout.connect(self.display_4image)
                self.timer_4.start(1000 / (self.spinBox_3.value()))
                self.IS_label4 = False
                setattr(self, f'IS_camera{self.camera_index + 1}', False)
                self.label4_num = self.camera_index
                self.pushButton_2.setText("关闭相机")
                self.pushButton_9.setEnabled(True)


        if Is_open == "关闭相机":
            label_num = self.spinBox.value()
            if label_num == 1:
                if DEBUG:
                    self.label_c1.clear()
                self.timer_1.stop()
                self.cam_1.stream_off()
                self.cam_1.close_device()
                self.IS_label1 = True
                setattr(self, f'IS_camera{self.label1_num+1}', True)
                self.pushButton_2.setEnabled(getattr(self,f'IS_camera{self.camera_index+1}'))
                self.pushButton_2.setText("打开相机")
                self.pushButton_3.setEnabled(False)
            elif label_num == 2:
                self.timer_2.stop()
                self.cam_2.stream_off()
                self.cam_2.close_device()
                self.IS_label2 = True
                setattr(self, f'IS_camera{self.label2_num + 1}', True)
                self.pushButton_2.setEnabled(getattr(self, f'IS_camera{self.camera_index + 1}'))
                self.pushButton_2.setText("打开相机")
                self.pushButton_5.setEnabled(False)
            elif label_num == 3:
                self.timer_3.stop()
                self.cam_3.stream_off()
                self.cam_3.close_device()
                self.IS_label3 = True
                setattr(self, f'IS_camera{self.label3_num + 1}', True)
                self.pushButton_2.setEnabled(getattr(self, f'IS_camera{self.camera_index + 1}'))
                self.pushButton_2.setText("打开相机")
                self.pushButton_7.setEnabled(False)
            else:
                self.timer_4.stop()
                self.cam_4.stream_off()
                self.cam_4.close_device()
                self.IS_label4 = True
                setattr(self, f'IS_camera{self.label4_num + 1}', True)
                self.pushButton_2.setEnabled(getattr(self, f'IS_camera{self.camera_index + 1}'))
                self.pushButton_2.setText("打开相机")
                self.pushButton_9.setEnabled(False)


    def display_1image(self):
        raw_image = self.cam_1.data_stream[0].get_image()
        rgb_image = raw_image.convert("RGB")
        numpy_image = rgb_image.get_numpy_array()
        image = Image.fromarray(numpy_image, 'RGB')
        qimage = image.toqimage()
        pixmap = QPixmap.fromImage(qimage)
        pixmap = QtGui.QPixmap(pixmap).scaled(self.label_c1.width(), self.label_c1.height())
        self.label_c1.setPixmap(pixmap)

    def display_2image(self):
        raw_image = self.cam_2.data_stream[0].get_image()
        rgb_image = raw_image.convert("RGB")
        numpy_image = rgb_image.get_numpy_array()
        image = Image.fromarray(numpy_image, 'RGB')
        qimage = image.toqimage()
        pixmap = QPixmap.fromImage(qimage)
        pixmap = QtGui.QPixmap(pixmap).scaled(self.label_c2.width(), self.label_c2.height())
        self.label_c2.setPixmap(pixmap)

    def display_3image(self):
        raw_image = self.cam_3.data_stream[0].get_image()
        rgb_image = raw_image.convert("RGB")
        numpy_image = rgb_image.get_numpy_array()
        image = Image.fromarray(numpy_image, 'RGB')
        qimage = image.toqimage()
        pixmap = QPixmap.fromImage(qimage)
        pixmap = QtGui.QPixmap(pixmap).scaled(self.label_c3.width(), self.label_c3.height())
        self.label_c3.setPixmap(pixmap)

    def display_4image(self):
        raw_image = self.cam_4.data_stream[0].get_image()
        rgb_image = raw_image.convert("RGB")
        numpy_image = rgb_image.get_numpy_array()
        image = Image.fromarray(numpy_image, 'RGB')
        qimage = image.toqimage()
        pixmap = QPixmap.fromImage(qimage)
        pixmap = QtGui.QPixmap(pixmap).scaled(self.label_c4.width(), self.label_c4.height())
        self.label_c4.setPixmap(pixmap)

    def timeout_1(self):
        if self.pushButton_3.text() == "1号定格":
            if DEBUG:
                self.pushButton_3.setText("1号取消定格")
                self.pushButton_4.setEnabled(True)
            else:
                self.label_c1.clear()
                self.timer_1.stop()
                raw_image = self.cam_1.data_stream[0].get_image()
                rgb_image = raw_image.convert("RGB")
                numpy_image = rgb_image.get_numpy_array()
                self.image1 = Image.fromarray(numpy_image, 'RGB')
                qimage = self.image1.toqimage()
                pixmap = QPixmap.fromImage(qimage)
                pixmap = QtGui.QPixmap(pixmap).scaled(self.label_c1.width(), self.label_c1.height())
                self.label_c1.setPixmap(pixmap)
                self.pushButton_4.setEnabled(True)
                self.pushButton_3.setText("1号取消定格")
        else:
            if DEBUG:
                self.pushButton_3.setText("1号定格")
                self.pushButton_4.setEnabled(False)
            else:
                self.label_c1.clear()
                self.timer_1.start(1000 / (self.spinBox_3.value()))


    def timeout_2(self):
        if self.pushButton_5.text() == "2号定格":
            self.label_c2.clear()
            self.timer_2.stop()
            raw_image = self.cam_2.data_stream[0].get_image()
            rgb_image = raw_image.convert("RGB")
            numpy_image = rgb_image.get_numpy_array()
            self.image2 = Image.fromarray(numpy_image, 'RGB')
            qimage = self.image2.toqimage()
            pixmap = QPixmap.fromImage(qimage)
            pixmap = QtGui.QPixmap(pixmap).scaled(self.label_c2.width(), self.label_c2.height())
            self.label_c2.setPixmap(pixmap)
            self.pushButton_6.setEnabled(True)
            self.pushButton_5.setText("2号取消定格")
        else:
            self.label_c2.clear()
            self.timer_2.start(1000 / (self.spinBox_3.value()))

    def timeout_3(self):
        if self.pushButton_7.text() == "3号定格":
            self.label_c3.clear()
            self.timer_3.stop()
            raw_image = self.cam_3.data_stream[0].get_image()
            rgb_image = raw_image.convert("RGB")
            numpy_image = rgb_image.get_numpy_array()
            self.image3 = Image.fromarray(numpy_image, 'RGB')
            qimage = self.image3.toqimage()
            pixmap = QPixmap.fromImage(qimage)
            pixmap = QtGui.QPixmap(pixmap).scaled(self.label_c3.width(), self.label_c3.height())
            self.label_c3.setPixmap(pixmap)
            self.pushButton_8.setEnabled(True)
            self.pushButton_7.setText("3号取消定格")
        else:
            self.label_c3.clear()
            self.timer_3.start(1000 / (self.spinBox_3.value()))

    def timeout_4(self):
        if self.pushButton_9.text() == "4号定格":
            self.label_c4.clear()
            self.timer_4.stop()
            raw_image = self.cam_4.data_stream[0].get_image()
            rgb_image = raw_image.convert("RGB")
            numpy_image = rgb_image.get_numpy_array()
            self.image4 = Image.fromarray(numpy_image, 'RGB')
            qimage = self.image4.toqimage()
            pixmap = QPixmap.fromImage(qimage)
            pixmap = QtGui.QPixmap(pixmap).scaled(self.label_c4.width(), self.label_c4.height())
            self.label_c4.setPixmap(pixmap)
            self.pushButton_10.setEnabled(True)
            self.pushButton_9.setText("4号取消定格")
        else:
            self.label_c4.clear()
            self.timer_4.start(1000 / (self.spinBox_3.value()))


    def save_img1(self):
        if DEBUG:
            fpath, ftype = QFileDialog.getSaveFileName(self.centralwidget, "保存1的图片",
                                                       "d:\\", "*.bmp;;*.png;;All Files(*)")
            print(fpath)
            self.pushButton_4.setEnabled(False)
            self.pushButton_3.setText("1号定格")
            self.textEdit.append("图片保存成功")
            QApplication.processEvents()
        else:
            fpath, ftype = QFileDialog.getSaveFileName(self.centralwidget, "保存1的图片",
                                                       "d:\\", "*.bmp;;*.png;;All Files(*)")
            self.image1.save(fpath)
            self.timer_1.start(1000 / (self.spinBox_3.value()))
            self.pushButton_4.setEnabled(False)
            self.pushButton_3.setText("1号定格")
            self.textEdit.append("图片保存成功")
            QApplication.processEvents()


    def save_img2(self):
        fpath, ftype = QFileDialog.getSaveFileName(self.centralwidget, "保存2的图片",
                                                   "d:\\", "*.bmp;;*.png;;All Files(*)")
        self.image2.save(fpath)
        self.timer_2.start(1000 / (self.spinBox_3.value()))
        self.pushButton_5.setText("2号定格")
        self.pushButton_6.setEnabled(False)
        self.textEdit.append("图片保存成功")
        QApplication.processEvents()

    def save_img3(self):
        fpath, ftype = QFileDialog.getSaveFileName(self.centralwidget, "保存3的图片",
                                                   "d:\\", "*.bmp;;*.png;;All Files(*)")
        self.image3.save(fpath)
        self.timer_3.start(1000 / (self.spinBox_3.value()))
        self.pushButton_7.setText("3号定格")
        self.pushButton_8.setEnabled(False)
        self.textEdit.append("图片保存成功")
        QApplication.processEvents()

    def save_img4(self):
        fpath, ftype = QFileDialog.getSaveFileName(self.centralwidget, "保存4的图片",
                                                   "d:\\", "*.bmp;;*.png;;All Files(*)")
        self.image4.save(fpath)
        self.timer_4.start(1000 / (self.spinBox_3.value()))
        self.pushButton_9.setText("4号定格")
        self.pushButton_10.setEnabled(False)
        self.textEdit.append("图片保存成功")
        QApplication.processEvents()








