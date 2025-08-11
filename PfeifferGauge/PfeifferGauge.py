import sys
import time
import threading
from collections import deque

import serial
import serial.tools.list_ports
import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, QObject, QTimer


# Worker Thread Object
class PressureReader(QObject):
    pressure_updated = pyqtSignal(int, float)
    error_occurred = pyqtSignal(str)

    def __init__(self, baudrate=19200):
        super().__init__()
        pid = 8963
        device_list = serial.tools.list_ports.comports()
        for dev in device_list:
          if dev.pid==pid:
              self.port=dev.device
        # self.port = port
        self.baudrate = baudrate
        self._running = False
        self._thread = None
        self.ser = None

    def start(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=.2, stopbits=1)
            time.sleep(.2)  # Let it initialize
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            # import ipdb; ipdb.set_trace()

            self.ser.write(b'PR1\r\n') #warm up communication for some reason??
            self.ser.readline()
            self.ser.write(b'PR1\r\n')
            self.ser.readline()

            self.ser.write(b'COM,1\r\n')  # Start continuous output
            ack = self.ser.readline()
            if "\x06" not in ack.decode():
                print("Pfeiffer: command rejected:", ack.decode())
                return

            self._running = True
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()
        except serial.SerialException as e:
            self.error_occurred.emit(f"Serial error: {e}")
        except Exception as E:
            print("Pfeiffer: Unknown error",E, E.with_traceback)

    def stop(self):
        self._running = False
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(b's\r\n')  # Stop continuous output
                time.sleep(0.1)
                self.ser.close()
            except Exception as e:
                self.error_occurred.emit(str(e))

    def _read_loop(self):
        while self._running:
            try:
                # print(self.ser.in_waiting)
                if self.ser.in_waiting:
                    line = self.ser.readline().decode('ascii', errors='ignore').strip()
                    # print(line)
                    # Example line: b'0, 2.2100E-07,5, 0.0000E+00\r\n'
                    # format is S1, Pressure1E-0X, S2, Pressure2E-0X
                    # where S is the gauge status (0=okay, 4=error). 
                    # There's readout support for up to two sensors for this model; ours is sensor 1 and S2/Pressure2 will be 0.
                    parts = line.split(',')
                    # import ipdb; ipdb.set_trace()
                    if len(parts):
                        try:
                            status = int(parts[0])
                            pressure = float(parts[1])
                            self.pressure_updated.emit(status, pressure)
                        except ValueError:
                            continue
            except Exception as e:
                self.error_occurred.emit(str(e))
                self._running = False


# Main GUI
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TPG261 Vacuum Gauge Monitor")
        self.setMinimumSize(600, 400)

        # UI Elements
        self.label = QLabel("Pressure: --- mbar")
        self.label.setStyleSheet("font-size: 20px;")

        self.start_button = QPushButton("Start Reading")
        self.stop_button = QPushButton("Stop Reading")
        self.start_button.clicked.connect(self.start_reading)
        self.stop_button.clicked.connect(self.stop_reading)

        # Plot setup
        self.plot = pg.PlotWidget()
        self.plot.setBackground('w')
        self.plot.setTitle("Pressure over Time", color='black', size="14pt")
        self.plot.setLabel('left', "Pressure", units='mbar', **{'color': 'black', 'font-size': '12pt'})
        self.plot.setLabel('bottom', "Time", units='s', **{'color': 'black', 'font-size': '12pt'})
        self.plot.showGrid(x=True, y=True)
        self.curve = self.plot.plot(pen=pg.mkPen('b', width=2))

        self.data_buffer = deque(maxlen=300)
        self.time_buffer = deque(maxlen=300)
        self.start_time = time.time()

        # Timer to update the plot
        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.update_plot)
        self.plot_timer.start(500)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.plot)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Reader setup
        self.reader = PressureReader()  # Change this port if needed
        self.reader.pressure_updated.connect(self.update_pressure)
        self.reader.error_occurred.connect(self.show_error)

    def update_pressure(self, status, pressure):
        # import ipdb; ipdb.set_trace()
        self.label.setText(f"Pressure: {pressure:.3e} mbar")
        current_time = time.time() - self.start_time
        self.data_buffer.append(pressure)
        self.time_buffer.append(current_time)

    def update_plot(self):
        if self.data_buffer and self.time_buffer:
            self.curve.setData(list(self.time_buffer), list(self.data_buffer))

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)
        self.stop_reading()

    def start_reading(self):
        self.start_time = time.time()
        self.data_buffer.clear()
        self.time_buffer.clear()
        self.reader.start()
        self.label.setText("Reading...")

    def stop_reading(self):
        self.reader.stop()
        self.label.setText("Stopped")

    def closeEvent(self, event):
        self.stop_reading()
        event.accept()


# Run the app
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
