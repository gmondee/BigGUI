import sys
import json
import threading
import time
import datetime
import serial
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
import pyqtgraph as pg
import os
from serial.tools import list_ports
from collections import deque

# === Configuration ===
device_list = list_ports.comports()
TEST_COMMAND = b'*IDN?\r\n' 
def test_connections():
    lakeshores = {}
    for dev in device_list:
        try:
            with serial.Serial(dev.device, 9600, timeout=0.2, bytesize=7, parity="O") as ser:
                    
                # print(f"Connected to {dev.device} at {9600} baud.")

                # Flush buffers
                ser.reset_input_buffer()
                ser.reset_output_buffer()

                print(f"Sending command: {TEST_COMMAND}")
                ser.write(TEST_COMMAND)

                time.sleep(0.2)  # Give device time to respond

                response = ser.read_all()
                print(f"Response:{response.decode()}")
                # print(response)
                if "LSCI" not in response.decode():
                    pass
                elif "331" in response.decode():
                    lakeshores["Lakeshore331"] = dev.device
                elif "218" in response.decode():
                    lakeshores["Lakeshore218"] = dev.device
                else:
                    print("Unknown Lakeshore device.")
        except:
            pass
    return lakeshores
COM_PORTS = test_connections()
# COM_PORTS = ['COM3', 'COM4']  # Replace with actual ports
SETPOINT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),'setpoints.json')

# === Helper Classes ===

class SensorAlertSignal(QObject):
    alert = pyqtSignal(str, float)


class LakeShoreDevice(threading.Thread):
    def __init__(self, port, name, update_callback, alert_signal, setpoints):
        super().__init__()
        self.port = port
        self.name = name
        self.update_callback = update_callback
        self.alert_signal = alert_signal
        self.setpoints = setpoints
        self._stop_event = threading.Event()
        self.ser = serial.Serial(port, 9600, timeout=0.5, bytesize=7, parity="O")
        self.sensor_ids = list(range(1,len(setpoints)+1))

    def run(self):
        while not self._stop_event.is_set():
            timestamp = time.time()
            for sensor_id, sensor_name in enumerate(self.setpoints.keys()):
                sensor_id+=1
                try:
                    self.ser.reset_input_buffer()
                    self.ser.reset_output_buffer()
                    self.ser.write(f"KRDG? {sensor_id}\r\n".encode())

                    # print(self.ser.read_all())
                    temp = float(self.ser.readline().decode().strip())
                    self.update_callback(self.name, sensor_name, timestamp, temp)
                    if (self.name in self.setpoints and 
                        sensor_id in self.setpoints[self.name] and 
                        temp > self.setpoints[self.name][sensor_id]):
                        self.alert_signal.alert.emit(f"{self.name}-{sensor_id}", temp)
                except Exception as e:
                    print(f"[{self.name}] Error reading sensor {sensor_id}: {e}")
            time.sleep(.4)

    def stop(self):
        self._stop_event.set()
        if self.ser and self.ser.is_open:
            self.ser.close()

# === GUI ===

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lakeshore Temperature Monitor")
        self.setGeometry(100, 100, 1200, 800)

        self.devices = []
        self.plots = {}
        self.curves = {}
        self.data = {}
        self.setpoints = self.load_setpoints()

        self.alert_signal = SensorAlertSignal()
        self.alert_signal.alert.connect(self.handle_alert)

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        layout = QVBoxLayout()

        self.grid = QGridLayout()
        layout.addLayout(self.grid)

        # Buttons
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.start_button.clicked.connect(self.start_monitoring)
        self.stop_button.clicked.connect(self.stop_monitoring)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def load_setpoints(self):
        try:
            with open(SETPOINT_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    def save_setpoints(self):
        with open(SETPOINT_FILE, 'w') as f:
            json.dump(self.setpoints, f, indent=2)

    def start_monitoring(self):
        self.status_label.setText("Monitoring started.")
        for row, (Lakeshore, port) in enumerate(COM_PORTS.items()):
            name = Lakeshore
            self.data[name] = {}
            self.plots[name] = {}
            self.curves[name] = {}

            for col, sensor_id in enumerate(self.setpoints[Lakeshore].keys()):
                self.data[name][sensor_id] = {'x': deque(maxlen=60*60*12), 'y': deque(maxlen=60*60*12)}

                plot_widget = pg.PlotWidget(title=f"{name} - {sensor_id}",axisItems = {'bottom': pg.DateAxisItem('bottom')})
                plot_widget.showGrid(x=True, y=True)
                plot_widget.setLabel('left', 'Temperature', units='K')
                plot_widget.setLabel('bottom', 'Time', units='s')
                # plot_widget.setXRange(0, 60)
                curve = plot_widget.plot([], [], pen='y')

                self.grid.addWidget(plot_widget, row, col)
                self.plots[name][sensor_id] = plot_widget
                self.curves[name][sensor_id] = curve

            device = LakeShoreDevice(
                port=port,
                name=name,
                update_callback=self.update_plot,
                alert_signal=self.alert_signal,
                setpoints=self.setpoints[Lakeshore]
            )
            device.start()
            self.devices.append(device)


    def stop_monitoring(self):
        self.status_label.setText("Monitoring stopped.")
        for device in self.devices:
            device.stop()
        self.devices.clear()

    def update_plot(self, device_name, sensor_id, timestamp, temp):
        data = self.data[device_name][sensor_id]
        data['x'].append(timestamp)
        data['y'].append(temp)

        # Convert timestamp labels to index for plotting
        x_vals = list(range(len(data['x'])))
        self.curves[device_name][sensor_id].setData(data['x'], data['y'])

        # self.plots[device_name][sensor_id].getAxis('bottom').setTicks([list(zip(x_vals, data['x']))])

    def handle_alert(self, sensor_full_name, temp):
        print(f"ALERT: {sensor_full_name} above setpoint! Temp: {temp:.2f} K")

    def closeEvent(self, event):
        self.stop_monitoring()
        self.save_setpoints()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
