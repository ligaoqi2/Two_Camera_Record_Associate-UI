import sys
import os
import time

import cv2
import datetime

import requests
from HttpUtil import *
from AssociateUtil import *

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QPalette, QBrush, QPixmap

# 全局变量，传送是否拍摄的信号
record_flag = 0

# 全局变量，传送初始化拍摄线程的信号
init_thread_record_flag = 0

# 图片保存路径
save_path_left = 0
save_path_right = 0

image_l = 0
image_r = 0

# http request
payload = {}
files = {}
headers = {}


# UI Thread
class ArucoUI(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ArucoUI, self).__init__(parent)

        self.timer_camera = QtCore.QTimer()  # 初始化定时器

        self.set_ui()  # 设置UI -> set_ui()
        self.slot_init()  # 建立通信连接 -> slot_init()

        # init cameras ip
        if os.path.exists("./history_ip.txt"):
            with open("./history_ip.txt") as his_ip_f:
                data = his_ip_f.read()
                self.ip1 = data.split(",")[0]
                self.ip2 = data.split(",")[1]
        else:
            self.ip1 = 0
            self.ip2 = 0

        # init file save path
        if os.path.exists("./history_savepath.txt"):
            with open("./history_savepath.txt", mode="r") as his_save_f:
                self.save_path = his_save_f.read()
        else:
            self.save_path = os.getcwd()

        self.cap1 = cv2.VideoCapture()  # 初始化camera 1
        self.cap2 = cv2.VideoCapture()  # 初始化camera 2

        self.__flag_work = 0
        self.x = 0
        self.count = 0

        self.threadCame1 = None
        self.threadCame2 = None

        self.fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    def set_ui(self):
        # self.__layout_main = QtWidgets.QHBoxLayout()  # 采用QHBoxLayout类，按照从左到右的顺序来添加控件
        self.__layout_main = QtWidgets.QVBoxLayout()
        self.__layout_show_camera = QtWidgets.QHBoxLayout()
        self.__layout_fun_button = QtWidgets.QHBoxLayout()

        self.config_save_path = QtWidgets.QPushButton(u'请设置拍摄文件保存路径\n(默认为C盘)')
        self.config_ip = QtWidgets.QPushButton(u'请点击此处设置手机端ip')

        self.button_open_camera = QtWidgets.QPushButton(u'打开相机')
        # self.button_close_camera = QtWidgets.QPushButton(u'关闭相机')
        self.button_open_camera.setEnabled(False)
        # self.button_close_camera.setEnabled(False)

        self.button_start_record = QtWidgets.QPushButton(u'开始录制')
        self.button_end_record = QtWidgets.QPushButton(u'结束录制')
        self.button_start_record.setEnabled(False)
        self.button_end_record.setEnabled(False)

        self.button_close = QtWidgets.QPushButton(u'退出')

        self.config_ip.setMinimumHeight(60)  # 设置最小高度
        self.config_save_path.setMinimumHeight(60)

        self.button_open_camera.setMinimumHeight(60)
        # self.button_close_camera.setMinimumHeight(50)

        self.button_start_record.setMinimumHeight(60)
        self.button_end_record.setMinimumHeight(60)

        self.button_close.setMinimumHeight(60)

        # move()方法是移动窗口在屏幕上的位置到x = 500，y = 500的位置上
        self.move(300, 300)

        # 信息显示
        # camera1
        self.label_show_camera1 = QtWidgets.QLabel()
        self.label_show_camera1.setFixedSize(641, 481)
        self.label_show_camera1.setAutoFillBackground(False)

        # camera2
        self.label_show_camera2 = QtWidgets.QLabel()
        self.label_show_camera2.setFixedSize(641, 481)
        self.label_show_camera2.setAutoFillBackground(False)

        self.label_move = QtWidgets.QLabel()
        self.label_move.setFixedSize(100, 100)

        self.__layout_fun_button.addWidget(self.config_save_path)
        self.__layout_fun_button.addWidget(self.config_ip)

        self.__layout_fun_button.addWidget(self.button_open_camera)
        # self.__layout_fun_button.addWidget(self.button_close_camera)

        self.__layout_fun_button.addWidget(self.button_start_record)
        self.__layout_fun_button.addWidget(self.button_end_record)

        self.__layout_fun_button.addWidget(self.button_close)
        self.__layout_fun_button.addWidget(self.label_move)

        self.__layout_show_camera.addWidget(self.label_show_camera1)
        self.__layout_show_camera.addWidget(self.label_show_camera2)

        self.__layout_main.addLayout(self.__layout_fun_button)
        self.__layout_main.addLayout(self.__layout_show_camera)

        self.setLayout(self.__layout_main)
        self.label_move.raise_()
        self.setWindowTitle(u'双目视频同步采集系统')

    def slot_init(self):  # 建立通信连接
        # 配置ip
        self.config_ip.clicked.connect(self.config_phone_ip)
        # 配置文件保存路径
        self.config_save_path.clicked.connect(self.config_File_save_path)

        # 连接相机
        self.button_open_camera.clicked.connect(self.button_open_camera_click)
        # self.button_close_camera.clicked.connect(self.button_close_camera_click)

        # 连接拍摄
        self.button_start_record.clicked.connect(self.start_record)
        self.button_end_record.clicked.connect(self.end_record)

        self.button_close.clicked.connect(self.close)

    def config_File_save_path(self):
        self.save_path = self.config_savefilepath()

    def config_phone_ip(self):
        self.ip1, self.ip2 = self.dialogIp()

    def button_open_camera_click(self):
        flag1 = self.cap1.open(self.ip1)
        flag2 = self.cap2.open(self.ip2)
        if flag1 is False or flag2 is False:
            msg = QtWidgets.QMessageBox.Warning(self, u'Warning', u'请检测手机与电脑是否连接正确',
                                                buttons=QtWidgets.QMessageBox.Ok,
                                                defaultButton=QtWidgets.QMessageBox.Ok)
        else:
            self.button_open_camera.setEnabled(False)
            # self.button_close_camera.setEnabled(True)
            self.button_start_record.setEnabled(True)
            # self.button_end_record.setEnabled(True)
            self.previewCamera()

    def closeEvent(self, event):
        ok = QtWidgets.QPushButton()
        cancel = QtWidgets.QPushButton()

        msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, u'关闭', u'是否关闭！')
        msg.addButton(ok, QtWidgets.QMessageBox.ActionRole)
        msg.addButton(cancel, QtWidgets.QMessageBox.RejectRole)

        ok.setText(u'确定')
        cancel.setText(u'取消')

        if msg.exec_() == QtWidgets.QMessageBox.RejectRole:
            event.ignore()

        else:
            if isinstance(self.threadCame1, ThreadCamera) or isinstance(self.threadCame1, ThreadCamera):
                self.threadCame1.terminate()
                self.threadCame2.terminate()
            if self.cap1.isOpened() or self.cap2.isOpened():
                self.cap1.release()
                self.cap2.release()
            self.label_show_camera1.clear()
            self.label_show_camera2.clear()
            QApplication.quit()

    def previewCamera(self):
        # # config whole file path
        # self.record_time = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        #
        # os.makedirs(os.path.join(self.save_path, self.record_time, "came1"))
        # os.makedirs(os.path.join(self.save_path, self.record_time, "came2"))
        #
        # self.path_result1 = os.path.join(self.save_path, self.record_time, "came1")
        # self.path_result2 = os.path.join(self.save_path, self.record_time, "came2")
        #
        # self.path_result = os.path.join(self.save_path, self.record_time)
        #
        # # init video save path
        # self.out1 = cv2.VideoWriter(os.path.join(self.path_result, "came1.mp4"), self.fourcc, 30.0, (int(self.cap1.get(3)), int(self.cap1.get(4))))
        # self.out2 = cv2.VideoWriter(os.path.join(self.path_result, "came2.mp4"), self.fourcc, 30.0, (int(self.cap2.get(3)), int(self.cap2.get(4))))

        self.threadCame1 = ThreadCamera(self.cap1, self.label_show_camera1, left_flag=True)
        self.threadCame2 = ThreadCamera(self.cap2, self.label_show_camera2, left_flag=False)

        self.threadCame1.start()
        self.threadCame2.start()

    def start_record(self):
        # config whole file path
        self.record_time = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')

        os.makedirs(os.path.join(self.save_path, self.record_time, "came1"))
        os.makedirs(os.path.join(self.save_path, self.record_time, "came2"))

        global save_path_left
        global save_path_right

        save_path_left = os.path.join(self.save_path, self.record_time, "came1")
        save_path_right = os.path.join(self.save_path, self.record_time, "came2")

        self.path_result = os.path.join(self.save_path, self.record_time)

        # init video save path
        self.out1 = cv2.VideoWriter(os.path.join(self.path_result, "came1.mp4"), self.fourcc, 30.0, (int(self.cap1.get(3)), int(self.cap1.get(4))))
        self.out2 = cv2.VideoWriter(os.path.join(self.path_result, "came2.mp4"), self.fourcc, 30.0, (int(self.cap2.get(3)), int(self.cap2.get(4))))

        self.button_start_record.setEnabled(False)
        self.button_end_record.setEnabled(True)
        global init_thread_record_flag
        global record_flag
        init_thread_record_flag = 1
        record_flag = 1

    def end_record(self):
        self.button_start_record.setEnabled(True)
        self.button_end_record.setEnabled(False)
        global record_flag
        record_flag = 0

        msg_associate = QMessageBox(QMessageBox.Warning, u'正在同步', u'请稍等...')
        msg_associate.show()
        # 同步时间戳
        gene_txt(self.path_result)
        run_associate(self.path_result, self.out1, self.out2)

        msg_associate.done(1)

        msg_associate_finished = QMessageBox(QMessageBox.Information, u'提示', u'已完成双目手机视频的时间戳对齐')
        msg_associate_finished.exec_()

    def dialogIp(self):
        """config camera IP"""
        dialog = QDialog()  # 自定义一个dialog
        dialog.setWindowTitle(u'请设置相机ip')
        dialog.resize(500, 200)
        # 配置layout
        formLayout = QFormLayout(dialog)

        ip1_text = QLineEdit()
        ip1_text.setText("http://192.168.1.193:8080/video")
        # ip1_text.setText("http://admin:admin@192.168.1.175:8081")
        ip2_text = QLineEdit()
        ip2_text.setText("http://192.168.1.227:8080/video")
        # ip2_text.setText("http://admin:admin@192.168.1.231:8081")

        formLayout.addRow('Ip1: ', ip1_text)
        formLayout.addRow('Ip2: ', ip2_text)

        button = QDialogButtonBox(QDialogButtonBox.Ok)
        formLayout.addRow(button)

        button.clicked.connect(dialog.accept)

        if dialog.exec() == QDialog.Accepted:

            self.ip_config1 = ip1_text.text().split('/video')[-2]
            self.ip_config2 = ip2_text.text().split('/video')[-2]

            msg_ip = QMessageBox(QMessageBox.Warning, u'请稍等', u'请稍等...')
            msg_ip.show()

            # config focus distance
            try:
                httpGet(self.ip_config1)
                httpGet(self.ip_config2)

                # Turn off the focus change
                turnOffTheFocusDistance(self.ip_config1)
                turnOffTheFocusDistance(self.ip_config2)

                # Set default focus
                setTheFocusDistance(self.ip_config1, 2.9)
                setTheFocusDistance(self.ip_config2, 0.5)

                msg_ip.done(1)
                msg_box = QMessageBox(QMessageBox.Warning, '提示', 'ip设置成功')
                msg_box.exec_()

                self.button_open_camera.setEnabled(True)

                with open("./history_ip.txt", mode="w") as ip_f:
                    ip_f.write(ip1_text.text() + "," + ip2_text.text())

                return ip1_text.text(), ip2_text.text()

            except Exception as e:
                msg_ip.done(1)
                self.button_open_camera.setEnabled(False)
                msg_reject = QMessageBox(QMessageBox.Warning, u'Warning', u'请检测手机与电脑是否连接正确\n并重新输入手机端显示的连接ip')
                msg_reject.exec_()

                return ip1_text.text(), ip2_text.text()

        else:
            return ip1_text.text(), ip2_text.text()

    def config_savefilepath(self):
        """config file save path"""

        default_path = "C:\\"

        if os.path.exists("./history_savepath.txt"):
            with open("./history_savepath.txt") as ff:
                default_path = ff.read()

        filedir = QFileDialog.getExistingDirectory(None, "选取文件夹", default_path)
        with open("./history_savepath.txt", mode="w") as save_f:
            save_f.write(filedir)
        return filedir


# Sub Thread
class ThreadCamera(QThread):
    def __init__(self, cap, label, left_flag):
        super(ThreadCamera, self).__init__()
        self.cap = cap
        self.label = label
        self.left_flag = left_flag

    def run(self) -> None:
        sub_sub_thread = 0
        if self.left_flag:
            global image_l
        else:
            global image_r
        while True:
            if self.left_flag:
                flag, image_l = self.cap.read()
            else:
                flag, image_r = self.cap.read()

            # init record thread
            global init_thread_record_flag
            global save_path_left
            global save_path_right
            if init_thread_record_flag:
                if self.left_flag:
                    sub_sub_thread = ThreadRecord(save_path_left, self.left_flag)
                else:
                    sub_sub_thread = ThreadRecord(save_path_right, False)

            # start record thread
            if record_flag and isinstance(sub_sub_thread, ThreadRecord):
                sub_sub_thread.start()
            elif not record_flag and isinstance(sub_sub_thread, ThreadRecord) and sub_sub_thread.isRunning():
                sub_sub_thread.terminate()
            else:
                pass

            if self.left_flag:
                show = cv2.resize(image_l, (640, 480))
            else:
                show = cv2.resize(image_r, (640, 480))

            show = cv2.cvtColor(show, cv2.COLOR_BGR2RGB)
            showImage = QtGui.QImage(show.data, show.shape[1], show.shape[0], QtGui.QImage.Format_RGB888)
            self.label.setPixmap(QtGui.QPixmap.fromImage(showImage))

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break


# Sub Sub Thread
class ThreadRecord(QThread):
    def __init__(self, save_path, left_flag):
        super(ThreadRecord, self).__init__()
        self.save_path = save_path
        self.left_flag = left_flag

    def run(self) -> None:
        if self.left_flag:
            cv2.imwrite(self.save_path + "/" + datetime.datetime.now().strftime('%H-%M-%S.%f') + ".jpg", image_l)
        else:
            cv2.imwrite(self.save_path + "/" + datetime.datetime.now().strftime('%H-%M-%S.%f') + ".jpg", image_r)


if __name__ == '__main__':
    App = QApplication(sys.argv)
    win = ArucoUI()
    win.show()
    sys.exit(App.exec_())
