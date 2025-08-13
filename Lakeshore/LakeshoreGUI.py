import sys
import json
import threading
import time
import datetime
import serial
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
import pyqtgraph as pg

# === Configuration ===
COM_PORTS = ['COM3', 'COM4']  # Replace with actual ports
SETPOINT_FILE = 'setpoints.json'

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
        self.ser = serial.Serial(port, 57600, timeout=1)
        self.sensor_ids = ['A', 'B']  # Can be extended if needed

    def run(self):
        while not self._stop_event.is_set():
            timestamp = datetime.datetime.now().strftime('%H:%M:%S')
            for sensor_id in self.sensor_ids:
                try:
                    self.ser.write(f"KRDG? {sensor_id}\n".encode())
                    temp = float(self.ser.readline().decode().strip())
                    self.update_callback(self.name, sensor_id, timestamp, temp)
                    if (self.name in self.setpoints and 
                        sensor_id in self.setpoints[self.name] and 
                        temp > self.setpoints[self.name][sensor_id]):
                        self.alert_signal.alert.emit(f"{self.name}-{sensor_id}", temp)
                except Exception as e:
                    print(f"[{self.name}] Error reading sensor {sensor_id}: {e}")
            time.sleep(1)

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
        for idx, port in enumerate(COM_PORTS):
            name = f"Device{idx+1}"
            self.data[name] = {}
            self.plots[name] = {}
            self.curves[name] = {}
            row = idx

            for col, sensor_id in enumerate(['A', 'B']):
                self.data[name][sensor_id] = {'x': [], 'y': []}

                plot_widget = pg.PlotWidget(title=f"{name} - Sensor {sensor_id}")
                plot_widget.showGrid(x=True, y=True)
                plot_widget.setLabel('left', 'Temperature', units='K')
                plot_widget.setLabel('bottom', 'Time')
                plot_widget.setXRange(0, 60)
                curve = plot_widget.plot([], [], pen='y')

                self.grid.addWidget(plot_widget, row, col)
                self.plots[name][sensor_id] = plot_widget
                self.curves[name][sensor_id] = curve

            device = LakeShoreDevice(
                port=port,
                name=name,
                update_callback=self.update_plot,
                alert_signal=self.alert_signal,
                setpoints=self.setpoints
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

        if len(data['x']) > 60:
            data['x'] = data['x'][-60:]
            data['y'] = data['y'][-60:]

        # Convert timestamp labels to index for plotting
        x_vals = list(range(len(data['x'])))
        self.curves[device_name][sensor_id].setData(x_vals, data['y'])

        self.plots[device_name][sensor_id].getAxis('bottom').setTicks([list(zip(x_vals, data['x']))])

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
    sys.exit(app.exec_())
