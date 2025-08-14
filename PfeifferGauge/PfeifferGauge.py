import sys
import time
import threading
from collections import deque
import numpy as np
import serial
import serial.tools.list_ports
import pyqtgraph as pg
import os
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QMessageBox, QCheckBox, QLineEdit, QHBoxLayout, QSpinBox
)
from PyQt6.QtCore import pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QIcon
import requests


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
            self.ser = serial.Serial(self.port, self.baudrate, timeout=.5)
            time.sleep(.2)  # Let it initialize
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            # import ipdb; ipdb.set_trace()

            self.ser.write(b's\r\n')
            self.ser.readline()
            self.ser.write(b'PR1\r\n') #warm up communication for some reason??
            self.ser.readline()
            self.ser.write(b'PR1\r\n')
            print(self.ser.read_all())
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()

            self.ser.write(b'COM,0\r\n')  # Start continuous output
            time.sleep(.3)
            time.sleep(.3)
            # import ipdb; ipdb.set_trace()
            ack = self.ser.read_all()
            if "\x06" not in ack.decode():
                print("Pfeiffer: command rejected:", ack.decode())
                self.ser.close()
                return
            
            print("Pfeiffer: Connected")
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
        #todo: make sure this is working
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
    overpressureSignal = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TPG261 Vacuum Gauge Monitor")
        # self.setMinimumSize(600, 400)

        # UI Elements
        self.label = QLabel("Pressure: --- mbar")
        self.label.setStyleSheet("font-size: 20px;")
        self.settingsPath = os.path.join(os.path.dirname(os.path.abspath(__file__)),'pfeifferSettings.json')
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)),"bbq.png")))
        try:
            with open(self.settingsPath, "r") as file:
                settings = json.load(file)
                self.pressureThreshold = float(settings['threshold'])
                self.overpressureTimeMs = int(settings['alertHoldTime'])
                self.teamsEnabled = int(settings['teamsEnabled'])
        except Exception as E:
            print("Pressure: failed to load settings file",E)
            self.pressureThreshold = 1.0e-4
            self.overpressureTimeMs = 550 #in ms
            self.teamsEnabled = True

        # Pressure threshold setup
        self.alertSent=False
        self.holdTimerActivate = False
        self.overpressureTimer = QTimer(self)
        self.overpressureTimer.setSingleShot(True)
        self.overpressureTimer.timeout.connect(self.sendTeamsAlert)

        self.start_button = QPushButton("Start Reading")
        self.stop_button = QPushButton("Stop Reading")
        self.teams_enabled_switch = QCheckBox(f"Send Teams Alert?")
        self.teams_enabled_switch.setChecked(self.teamsEnabled)
        # self.teams_enabled_switch.checkStateChanged.connect(self.updateTeamsLabel)
        self.threshold_label = QLabel(f"Set Alert Pressure Threshold ({self.pressureThreshold:.2e}):")
        self.threshold_lineEdit = QLineEdit()
        self.threshold_lineEdit.setText(f"{self.pressureThreshold:.2e}")
        self.threshold_lineEdit.returnPressed.connect(self.updatePressureThreshold)

        self.alert_hold_label = QLabel(f"Set Alert Hold Time ({self.overpressureTimeMs}ms):")
        self.alert_hold_spinBox= QSpinBox(minimum=0,maximum=int(1e7))
        # self.alert_hold_spinBox.setRange(0,1e7)
        self.alert_hold_spinBox.setValue(self.overpressureTimeMs)
        self.alert_hold_spinBox.valueChanged.connect(self.updateAlertHold)
        self.start_button.clicked.connect(self.start_reading)
        self.stop_button.clicked.connect(self.stop_reading)

        # Plot setup
        self.plot = pg.PlotWidget(axisItems = {'bottom': pg.DateAxisItem(), 'left':FineLogAxis('left'), 'right':FineLogAxis('right')})
        self.plot.setBackground('w')
        self.plot.setTitle("Pressure vs. Time", color='black', size="14pt")
        self.plot.setLabel('left', "Pressure", units='mbar', **{'color': 'black', 'font-size': '12pt'})
        self.plot.setLabel('bottom', "Time", units='s', **{'color': 'black', 'font-size': '12pt'})
        # self.plot.setLogMode(False, True)
        self.plot.showGrid(x=True, y=True)
        # import ipdb; ipdb.set_trace()
        self.curve = self.plot.plot(pen=pg.mkPen('b', width=2))

        self.pressureBuffer = deque(maxlen=1000)
        self.timeBuffer = deque(maxlen=1000)
        self.start_time = time.time()

        # Timer to update the plot
        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.update_plot)
        self.plot_timer.start(250)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.plot)

        layoutStartStopTeams = QHBoxLayout()
        layoutStartStopTeams.addWidget(self.start_button)
        layoutStartStopTeams.addWidget(self.stop_button)
        layoutStartStopTeams.addWidget(self.teams_enabled_switch)
        startStopTeamsWidget = QWidget()
        startStopTeamsWidget.setLayout(layoutStartStopTeams)

        layoutThresholdHold = QHBoxLayout()
        layoutThresholdHold.addWidget(self.threshold_label)
        layoutThresholdHold.addWidget(self.threshold_lineEdit)
        layoutThresholdHold.addWidget(self.alert_hold_label)
        layoutThresholdHold.addWidget(self.alert_hold_spinBox)
        thresholdHoldWidget = QWidget()
        thresholdHoldWidget.setLayout(layoutThresholdHold)

        layout.addWidget(startStopTeamsWidget)
        layout.addWidget(thresholdHoldWidget)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Reader setup
        self.reader = PressureReader() 
        self.reader.pressure_updated.connect(self.update_pressure)
        self.reader.error_occurred.connect(self.show_error)

    def updatePressureThreshold(self):
        try: 
            pth = float(self.threshold_lineEdit.text())
            self.pressureThreshold = pth
            self.threshold_label.setText(f"Set Alert Pressure Threshold ({self.pressureThreshold:.2e}):")
            print(f"Pressure: Set alarm threshold pressure to {pth} mbar")
        except: print("Pressure: Incorrect pressure threshold format. Use, for example, 5.0e-5")

    def updateAlertHold(self):
        try:
            ath = int(self.alert_hold_spinBox.value())
            self.overpressureTimeMs = ath
            self.alert_hold_label.setText(f"Set Alert Hold Time ({self.overpressureTimeMs}ms):")
            print(f"Pressure: Set alarm threshold time to {ath} ms")
        except: print("Pressure: Incorrect alert hold time format. Use, for example, 550 for 550ms")

    def update_pressure(self, status, pressure):
        # import ipdb; ipdb.set_trace()
        self.label.setText(f"Pressure: {pressure:.3e} mbar")
        current_time = time.time()# - self.start_time
        self.pressureBuffer.append(pressure)
        self.timeBuffer.append(current_time)
        if status!=0:
            print("Pfeiffer: Gauge status not 0/OK:",status)
        maxP = pressure
        if maxP>self.pressureThreshold:
            if not self.alertSent and not self.holdTimerActivate:
                now=time.time()
                print(f"Pressure: Overpressure {maxP:.2e} detected at {time.strftime('%X %x %Z')}")
                self.holdTimerActivate = True
                self.overpressureTimer.start(self.overpressureTimeMs)
        else:
            self.overpressureTimer.stop()
            self.holdTimerActivate = False
            self.alertSent = False

    def update_plot(self):
        if self.pressureBuffer and self.timeBuffer:
            self.curve.setData(list(self.timeBuffer), list(self.pressureBuffer))

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)
        self.stop_reading()

    def start_reading(self):
        self.start_time = time.time()
        self.pressureBuffer.clear()
        self.timeBuffer.clear()
        self.reader.start()
        self.label.setText("Reading...")

    def stop_reading(self):
        self.reader.stop()
        self.label.setText("Stopped")

    def closeEvent(self, event):
        self.stop_reading()
        self.saveSettings()
        self.reader.ser.close()
        event.accept()

    def saveSettings(self):
        settings={
            "threshold":str(self.pressureThreshold),
            "alertHoldTime":str(self.overpressureTimeMs),
            "teamsEnabled":str(int(self.teams_enabled_switch.isChecked()))
        }
        with open(self.settingsPath, "w") as file:
            json.dump(settings, file)


    def sendTeamsAlert(self):
        self.overpressureSignal.emit(f"Pressure limit ({self.pressureThreshold:.2e}) exceeded: {max(self.pressureBuffer):.2e}")
        if self.teams_enabled_switch.isChecked():
            pressure=max(self.pressureBuffer)
            teams_webhook = r'https://prod-184.westus.logic.azure.com:443/workflows/4e8133319bd74782976b43617ed71592/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=PwW7eTHBIxtbNSLiWBsPfnH53cv22VXYTCmj0yS3T8w'
            payload = {"text":f"Overpressure detected: {pressure} (Threshold: {self.pressureThreshold})"}
            headers = {"Content-Type":"application/json"}
            try:
                response = requests.post(teams_webhook,json=payload, headers=headers)
                self.alertSent=True
            except Exception as E:
                print(f"Error sending teams alert: {E}")
        else:
            print("Pressure: Pressure alert triggered but Teams alert is disabled.")


class FineLogAxis(pg.AxisItem):
    def __init__(self, orientation, **kwargs):
        super().__init__(orientation, **kwargs)
        self.setLogMode(True)

    def tickValues(self, minVal, maxVal, size):
        # Avoid invalid log values
        minVal = max(minVal, 1e-300)
        maxVal = max(maxVal, minVal * 1.001)

        # Desired spacing in log10 (affects how fine the ticks are)
        log_range = np.log10(maxVal) - np.log10(minVal)
        tick_density = size / 80  # Adjust this number to control tick density
        log_step = log_range / tick_density

        # Snap to nearest smaller log step like 0.1, 0.2, 0.5, etc.
        nice_steps = [1, 0.5, 0.2, 0.1, 0.05, 0.02, 0.01]
        step = next((s for s in nice_steps if s <= log_step), 0.01)

        # Create ticks in log space
        log_min = np.floor(np.log10(minVal / 10))
        log_max = np.ceil(np.log10(maxVal * 10))
        log_ticks = np.arange(log_min, log_max, step)
        values = 10 ** log_ticks

        # Split into major and minor ticks based on step
        major_step = 1
        major_vals = 10 ** np.arange(np.floor(np.log10(minVal)), np.ceil(np.log10(maxVal)) + 1, major_step)
        minor_vals = [v for v in values if v not in major_vals]

        return [(1, major_vals), (2, minor_vals)]

    def tickStrings(self, values, scale, spacing):
        return [f"{v:.2e}" if v > 0 else '' for v in values]
# Run the app
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
