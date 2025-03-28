import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                           QLabel, QDesktopWidget, QPushButton, QListWidget, QMessageBox, QGridLayout, QGroupBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPalette, QColor
import can

class StatusLight(QWidget):
    def __init__(self, name):
        super().__init__()
        self.name = name
        
        # Create circle indicator
        self.start = "QPushButton{border: 1px solid lightgray;border-radius: 50px;background-color: #ccc;}"
        self.green = "QPushButton{border: 1px solid lightgray;border-radius: 50px;background-color: green;}"
        self.warning = "QPushButton{border: 1px solid lightgray;border-radius: 50px;background-color: yellow;}"
        self.fault = "QPushButton{border: 1px solid lightgray;border-radius: 50px;background-color: red;}"
        self.indicator = QPushButton()
        self.indicator.setFixedSize(100, 100)
        self.indicator.setStyleSheet(self.start)

    def display(self):
        group = QGroupBox()
        layout = QVBoxLayout()
        group.setLayout(layout)

        self.label = QLabel(self.name)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 20px;font-weight: bold;")
        
        layout.addWidget(self.indicator, alignment=Qt.AlignCenter)
        layout.addWidget(self.label, alignment=Qt.AlignCenter)
        return group


    def change_status(self, status):
        if status == "작동":
            self.indicator.setStyleSheet(self.green)
        elif status == "경고":
            self.indicator.setStyleSheet(self.warning)
        elif status == "고장":
            self.indicator.setStyleSheet(self.fault)

class InspectionSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        self.label_style = "border: 1px solid lightgray;font-size: 16px;font-weight: bold;"
        self.label_edit = "border: 1px solid lightgray;font-size: 16px;font-weight: bold;background-color: white;"
        self.error_style = "border: 1px solid lightgray;font-size: 16px;font-weight: bold;background-color: red;"
        self.voltage = QLabel("0")
        self.temperature = QLabel("0")
        self.communication = QLabel("정상")
        self.list_widget = QListWidget()

        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("포탑승압기")
        screensize = QDesktopWidget().screenGeometry(-1)
        self.setMinimumSize(screensize.width(), screensize.height())

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        left_widget = self.left_ui()
        right_widget = self.right_ui()
        
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)
        
        # Initialize variables
        self.start_time = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_elapsed_time)
        self.bus = None
        self.is_running = False

    def left_ui(self):
        # Table headers
        # Left side (Table)
        left_widget = QGroupBox("포탑승압기 모니터링")
        left_layout = QGridLayout()
        left_widget.setLayout(left_layout)

        headers = ["구분", "출력 전압", "과열", "통신"]
        for col, header in enumerate(headers):
            label = QLabel(header)
            label.setStyleSheet(self.label_style)
            label.setAlignment(Qt.AlignCenter)
            if col == 0:
                left_layout.addWidget(label, 0, col, 2, 1)
            elif col == 1:
                left_layout.addWidget(label, 0, col, 1, 2)
            elif col >= 2:
                left_layout.addWidget(label, 0, col+1, 2, 1)

        vols = ["저전압", "고전압"]
        for col, vol in enumerate(vols):
            label = QLabel(vol)
            label.setStyleSheet(self.label_style)
            label.setAlignment(Qt.AlignCenter)
            left_layout.addWidget(label, 1, col+1)
        
        # Table rows
        rows = [ QLabel("현재 값"), self.voltage, self.temperature, self.communication]
        for col, label in enumerate(rows):
            # Row header
            if col == 0:
                label.setStyleSheet(self.label_style)
                label.setAlignment(Qt.AlignCenter)
                left_layout.addWidget(label, 2, col)
            elif col == 1:
                label.setStyleSheet(self.label_edit)
                label.setAlignment(Qt.AlignCenter)
                left_layout.addWidget(label, 2, col, 1, 2)
            elif col >= 2:
                label.setStyleSheet(self.label_edit)
                label.setAlignment(Qt.AlignCenter)
                left_layout.addWidget(label, 2, col+1)
            

        rows = ["기준", "268 V 미만만", "272 V 초과", "100°C 초과", "연속 5회\n응답없음"]
        for col, label in enumerate(rows):
            label = QLabel(label)
            label.setStyleSheet(self.label_style)
            label.setAlignment(Qt.AlignCenter)
            left_layout.addWidget(label, 3, col)


        elabel = QLabel("경고이력")
        elabel.setStyleSheet(self.label_style)
        left_layout.addWidget(elabel, 4, 0, 1, 5)
        left_layout.addWidget(self.list_widget, 5, 0, 10, 5)

        return left_widget

    def right_ui(self):
        # Right side (Status and Controls)
        right_group = QGroupBox("상태표시등")
        right_layout = QVBoxLayout()
        right_group.setLayout(right_layout)

        # Status lights
        status_group = QGroupBox("상태표시등")
        status_layout = QHBoxLayout()
        status_group.setLayout(status_layout)

        self.status_normal = StatusLight("작동")  # Light green
        self.status_warning = StatusLight("경고")
        self.status_error = StatusLight("고장")
        
        status_layout.addWidget(self.status_normal.display())
        status_layout.addWidget(self.status_warning.display())
        status_layout.addWidget(self.status_error.display())

        right_layout.addWidget(status_group)

        # Time information
        time_group = QGroupBox("시간 정보")
        time_layout = QGridLayout()
        time_group.setLayout(time_layout)
        
        tlabel = QLabel("시작시각:")
        tlabel.setStyleSheet(self.label_style)
        time_layout.addWidget(tlabel, 0, 0)

        self.start_time_label = QLabel("0000-00-00 00:00:00")
        self.start_time_label.setStyleSheet(self.label_edit)
        time_layout.addWidget(self.start_time_label, 0, 1, 1, 3)
        
        elabel = QLabel("경과시간:")
        elabel.setStyleSheet(self.label_style)
        time_layout.addWidget(elabel, 1, 0)

        self.elapsed_time_label = QLabel("00 일 00 시간 00 분 00 초")
        self.elapsed_time_label.setStyleSheet(self.label_edit)
        time_layout.addWidget(self.elapsed_time_label, 1, 1, 1, 3)
        
        right_layout.addWidget(time_group)
        
        # Control buttons
        button_group = QGroupBox()
        button_layout = QHBoxLayout()
        button_group.setLayout(button_layout)

        self.start_button = QPushButton("점검시작")
        self.stop_button = QPushButton("점검종료")
        self.start_button.setFixedSize(300, 100)
        self.stop_button.setFixedSize(300, 100)
        self.start_button.clicked.connect(self.start_inspection)
        self.stop_button.clicked.connect(self.stop_inspection)
        self.stop_button.setEnabled(False)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        right_layout.addWidget(button_group)


        error_group = QGroupBox()
        error_layout = QHBoxLayout()
        error_group.setLayout(error_layout)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(self.label_style)
        error_layout.addWidget(self.error_label)

        right_layout.addWidget(error_group)
        
        return right_group# Add left and right widgets to main layout
        
    def start_inspection(self):
        self.status_normal.change_status("작동")
        self.start_time = datetime.now()
        self.start_time_label.setText(self.start_time.strftime("%Y-%m-%d %H:%M:%S"))
        self.timer.start(1000)  # Update every second
        try:
            self.bus = can.Bus(interface='ixxat', channel='0', bitrate=500000)
            print("Connect :: ", self.bus)
            
            self.start_time = datetime.now()
            self.start_time_label.setText(self.start_time.strftime("%Y-%m-%d %H:%M:%S"))
            self.timer.start(3000)  # Update every second
            
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.is_running = True
            self.read_messages()
            
        except Exception as e:
            # print("Error :: ", e)
            # QMessageBox.critical(
            #     self,
            #     "Error",
            #     f"Failed to initialize CAN interface:\n{str(e)}\n\n"
            #     f"If using IXXAT, please ensure VCI drivers are installed and DLLs are accessible."
            # )
            self.error_label.setText(f"Failed to initialize CAN interface:\n{str(e)}\n\n")
            
            

    def stop_inspection(self):
        self.is_running = False
        if self.bus:
            self.bus.shutdown()
            self.bus = None
        self.timer.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def update_elapsed_time(self):
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            days = elapsed.days
            hours = elapsed.seconds // 3600
            minutes = (elapsed.seconds % 3600) // 60
            seconds = elapsed.seconds % 60
            self.elapsed_time_label.setText(f"{days:02d} 일 {hours:02d} 시간 {minutes:02d} 분 {seconds:02d} 초")

    def read_messages(self):
        while self.is_running and self.bus:
            try:
                message = self.bus.recv(1)
                if message is not None:
                    # Process CAN message and update UI accordingly
                    self.process_can_message(message)
            except Exception as e:
                print(f"Error reading message: {e}")
                self.stop_inspection()
                break

    def process_can_message(self, message):
        print(message)

    def closeEvent(self, event):
        self.stop_inspection()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InspectionSystem()
    window.show()
    sys.exit(app.exec_())