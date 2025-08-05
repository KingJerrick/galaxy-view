# Copyright (C) 2024 - 2024 Jerrick Zhu, Inc. All Rights Reserved
#
# @Time    : 2024/9/19 19:53
# @Author  : Jerrick Zhu
# @File    : main.py
# @IDE     : PyCharm v2024


import sys
from PyQt5.QtWidgets import QApplication, QWidget
import slot.Mainwindow
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon





if __name__ == '__main__':
    # 界面的入口，在这里需要定义QApplication对象，之后界面跳转时不用重新定义，只需要调用show()函数jikt
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    MainWindow = slot.Mainwindow.MainwindowAct()
    MainWindow.setWindowIcon(QIcon("res/favicon.ico"))
    MainWindow.show()  # 显示窗体
    sys.exit(app.exec_())  # 程序关闭时退出进程


