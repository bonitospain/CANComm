import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QComboBox, QPushButton, QTextEdit
import can

class CANReader(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CAN Message Reader")
        self.setGeometry(100, 100, 600, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.interface_label = QLabel("Select CAN Interface:")
        self.layout.addWidget(self.interface_label)

        self.interface_combo = QComboBox()
        self.interface_combo.addItems(["socketcan", "pcan", "ixxat"])
        self.layout.addWidget(self.interface_combo)

        self.bitrate_label = QLabel("Select Bitrate:")
        self.layout.addWidget(self.bitrate_label)

        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["500000", "250000", "125000"])
        self.layout.addWidget(self.bitrate_combo)

        self.start_button = QPushButton("Start Reading")
        self.start_button.clicked.connect(self.start_reading)
        self.layout.addWidget(self.start_button)

        self.message_display = QTextEdit()
        self.layout.addWidget(self.message_display)

    def start_reading(self):
        interface = self.interface_combo.currentText()
        bitrate = int(self.bitrate_combo.currentText())

        # CAN 버스 설정
        try:
            bus = can.interface.Bus(interface=interface, channel='can0', bitrate=bitrate)
        except can.CanError as e:
            self.message_display.append(f"Error: {e}")
            return

        if bus:
            # 메시지 
            while True:
                message = bus.recv()
                if message:
                    self.message_display.append(f"ID: {message.arbitration_id}, Data: {message.data}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CANReader()
    window.show()
    sys.exit(app.exec_())