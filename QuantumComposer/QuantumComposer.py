import time
import json
import threading
import serial
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton,\
QGroupBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton, \
QComboBox, QLineEdit, QButtonGroup
from PyQt6.QtCore import QObject, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon
import re
from PyQt6.QtGui import QFont
import os
import serial.tools.list_ports

class QComController():
    def __init__(self, verbose=False):
        print("QC+: Starting up...")
        self.settingsPath = os.path.join(os.path.dirname(os.path.abspath(__file__)),'data.json')
        self.alphabet_list = ['T0', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        self.number_list = ['0', '1', '2', '3', '4', '5', '6', '7', '8']
        self.channel_index = dict(zip(self.alphabet_list, self.number_list))
        self.reply = ''
        self.connected=False
        self.verbose=verbose
        #masterState is 0=state, 1=sync, 2=delay, 3=label, 4=width
        self.masterState = {'A': [0, 0, 0, 'Channel A: Not used',0],
                            'B': [0, 0, 0, 'Channel B: Ablation Flashlamp',0],
                            'C': [0, 0, 0, 'Channel C: Ablation Q-Switch',0],
                            'D': [0, 0, 0, 'Channel D: Gas',0],
                            'E': [0, 0, 0, 'Channel E: Ionization Flashlamp',0],
                            'F': [0, 0, 0, 'Channel F: TDC/Ionization Q-Switch',0],
                            'G': [0, 0, 0, 'Channel G: OPO Flashlamp',0],
                            'H': [0, 0, 0, 'Channel H: OPO Q-Switch',0]}
        # possibleDevices=[comport.device for comport in serial.tools.list_ports.comports()]
        sn = 'AB0PEW5NA'
        device_list = serial.tools.list_ports.comports()
        # import ipdb; ipdb.set_trace()
        for dev in device_list:
          if dev.serial_number==sn:
            try:
              if self.verbose: print('QC+: trying com port %s'%dev)
              self.ser = serial.Serial(dev.device, 19200, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=.25)
              # if self.verbose: print(" maybe this one?")
              self.ser.flush()
              self.ser.reset_output_buffer()
              self.ser.readline().decode('utf-8').rstrip('\r\n') #check for prefilled line
              self.checkIdentification() #should actually clear anything out so it works
              response = self.checkIdentification()
              #response = self.ser.read(2000).decode('utf-8').rstrip('\r\n'); if self.verbose: print("response:", response)
              if "951" in response:
                print(f"QC+: Connected to {dev}.")
                self.connected=True
              else: 
                print("QC+: Error: Failed to connect to Quantum Composer!")
                self.ser.close()
                return
            except Exception as E:
                print("QC+: Error: Failed to connect to Quantum Composer!", E)
                return
        if not self.connected:
            print("QC: Failed to connect.")
            return
        self.getQCValues()
        # self.startUpdateLoop() #disable until multithreading
        print("QC+: Done.")
        with open(self.settingsPath, "w") as file:
            json.dump(self.masterState, file)

    def getQCValues(self):
        for key in self.masterState.keys():
          self.getState(key)
          self.getSync(key)
          self.getDelay(key)
          self.getWidth(key)
        self.triggering = self.getState("T0")
    def startUpdateLoop(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.getQCValues)
        self.timer.start(2000)  # ms
    def write(self, command, channel, dataType):
        command = (command + '\r\n').encode('utf-8')
        if self.verbose: print(command)
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        self.ser.write(command)
        self.out = self.ser.readline().decode('utf-8').rstrip('\r\n')
        if self.out == 'ok':
            if self.verbose: print('QC+: task trasmitted')
        else:
            if self.verbose: print('QC+: this is out: ' + self.out)
        if channel == 'SYSTEM' or channel=="T0":
            pass
        else:
            if re.match("^[0-9.]+$", self.out) and len(self.out) > 2:
                self.out = str(float(self.out[:-4])*1e6) #change timings to nanoseconds
            self.masterState[channel][dataType] = self.out
            print(command, self.out)
            #if self.verbose: print(self.masterState)
        with open(self.settingsPath, "w") as file:
            json.dump(self.masterState, file)
        return self.out
    
    def pauseTrigDecorator(f):
        def wrapper(self, *args,**kwargs):
            if self.triggering:
                self.stop()
                ret = f(self, *args, **kwargs)
                self.start()
                return ret
            else:
                return f(self, *args,**kwargs)
        return wrapper
    
    def getState(self, channel):
        channel_number = self.channel_index[channel]
        command = ":PULSE" + str(channel_number) + ":STATE?"
        return int(self.write(command, channel, 0))

    def setState(self, channel, state):
        channel_number = self.channel_index[channel]
        command = ":PULSE"+str(channel_number)+":STATE "+ str(state)
        self.write(command, channel, 0)

    
    def getSync(self, channel):
        channel_number = self.channel_index[channel]
        command = ":PULSE"+str(channel_number)+":SYNC?"
        self.write(command, channel, 1)

    @pauseTrigDecorator
    def setSync(self, channel, sync_channel):
        channel_number = self.channel_index[channel]
        #sync_channel_number = self.channel_index[sync_channel]
        command = ":PULSE"+str(channel_number)+":SYNC "+str(sync_channel)
        self.write(command, channel, 1)

    def getDelay(self, channel):
        self.channel_number = self.channel_index[channel]
        command = ":PULSE"+str(self.channel_number)+":DELAY?"
        self.write(command, channel, 2)

    @pauseTrigDecorator
    def setDelay(self, channel, delay):
        self.channel_number = self.channel_index[channel]
        command = ':PULSE' + self.channel_number + ':DELAY ' + '{:.9f}'.format(float(delay)*1e-6)
        self.write(command, channel, 2)

    def getWidth(self, channel):
        self.channel_number = self.channel_index[channel]
        command = ":PULSE"+str(self.channel_number)+":WIDTH?"
        self.write(command, channel, 4)

    @pauseTrigDecorator
    def setWidth(self, channel, width):
        self.channel_number = self.channel_index[channel]
        command = ':PULSE' + self.channel_number + ':WIDTH ' + '{:.9f}'.format(float(width)*1e-6)
        self.write(command, channel, 4)


    def checkIdentification(self):
        command = "*IDN?"
        return self.write(command,channel='SYSTEM',dataType=None)
    
    def start(self):
        self.setState("T0",1)
        self.triggering = self.getState("T0")
        # for channel in self.masterState.keys():
        #     channel_number = self.channel_index[channel]
        #     command = ":PULSE"+str(channel_number)+":STATE 1"
        #     self.write(command, channel, 0)
    
    def stop(self):
        self.setState("T0",0)
        self.triggering = self.getState("T0")
        # for channel in self.masterState.keys():
        #     channel_number = self.channel_index[channel]
        #     command = ":PULSE"+str(channel_number)+":STATE 0"
        #     self.write(command, channel, 0)
    



class mainWindow(QWidget):
    def __init__(self, verbose=False):
        super().__init__()
        self.QComController = QComController(verbose=verbose)
        self.title = "Quantum Composer Controller"
        self.left = 10
        self.top = 10
        self.verbose=verbose
        self.width = 1000
        self.height = 500
        self.initUI()
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)),"Greece.png")))
        self.stateDict = {'A': [self.channelASwitchOn, self.channelASwitchOff],
                    'B': [self.channelBSwitchOn, self.channelBSwitchOff],
                    'C': [self.channelCSwitchOn, self.channelCSwitchOff],
                    'D': [self.channelDSwitchOn, self.channelDSwitchOff],
                    'E': [self.channelESwitchOn, self.channelESwitchOff],
                    'F': [self.channelFSwitchOn, self.channelFSwitchOff],
                    'G': [self.channelGSwitchOn, self.channelGSwitchOff],
                    'H': [self.channelHSwitchOn, self.channelHSwitchOff]
                    }
        self.delayDict = {'A': [self.channelADelay, self.channelADelayRead],
                        'B': [self.channelBDelay, self.channelBDelayRead],
                        'C': [self.channelCDelay, self.channelCDelayRead],
                        'D': [self.channelDDelay, self.channelDDelayRead],
                        'E': [self.channelEDelay, self.channelEDelayRead],
                        'F': [self.channelFDelay, self.channelFDelayRead],
                        'G': [self.channelGDelay, self.channelGDelayRead],
                        'H': [self.channelHDelay, self.channelHDelayRead]
                        }
        self.widthDict = {'A': [self.channelAWidth, self.channelAWidthRead],
                        'B': [self.channelBWidth, self.channelBWidthRead],
                        'C': [self.channelCWidth, self.channelCWidthRead],
                        'D': [self.channelDWidth, self.channelDWidthRead],
                        'E': [self.channelEWidth, self.channelEWidthRead],
                        'F': [self.channelFWidth, self.channelFWidthRead],
                        'G': [self.channelGWidth, self.channelGWidthRead],
                        'H': [self.channelHWidth, self.channelHWidthRead]
                        }
        
        self.syncDict = {'A': [self.channelASyncTo, self.channelASyncRead],
                    'B': [self.channelBSyncTo, self.channelBSyncRead],
                    'C': [self.channelCSyncTo, self.channelCSyncRead],
                    'D': [self.channelDSyncTo, self.channelDSyncRead],
                    'E': [self.channelESyncTo, self.channelESyncRead],
                    'F': [self.channelFSyncTo, self.channelFSyncRead],
                    'G': [self.channelGSyncTo, self.channelGSyncRead],
                    'H': [self.channelHSyncTo, self.channelHSyncRead]
                    }
        # Store the QC controller as a class level variable so it can be accessed in other functions
        # import ipdb; ipdb.set_trace()
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.height, self.width, self.height)
        ## channel A
        self.channelATitle = QLabel(self.QComController.masterState['A'][3])
        self.channelATitle.setFont(QFont('Times New Roman', 10))
        # on/off
        self.channelASwitchOn = QRadioButton('ON')
        self.channelASwitchOff = QRadioButton('OFF')
        self.buttonGroupA = QButtonGroup()
        self.buttonGroupA.addButton(self.channelASwitchOn)
        self.buttonGroupA.addButton(self.channelASwitchOff)
        channelAStatus = QHBoxLayout()
        channelAStatus.addWidget(self.channelASwitchOn)
        channelAStatus.addWidget(self.channelASwitchOff)
        if self.QComController.masterState['A'][0] == '0':
            self.channelASwitchOff.setChecked(True)
        else:
            self.channelASwitchOn.setChecked(True)
        # sync
        self.channelASyncLabel = QLabel('Sync to: ')
        self.channelASyncTo = QComboBox()
        self.channelASyncTo.addItem('T0')
        self.channelASyncTo.addItem('Channel B')
        self.channelASyncTo.addItem('Channel C')
        self.channelASyncTo.addItem('Channel D')
        self.channelASyncTo.addItem('Channel E')
        self.channelASyncTo.addItem('Channel F')
        self.channelASyncTo.addItem('Channel G')
        self.channelASyncTo.addItem('Channel H')
        channelASyncLayout = QHBoxLayout()
        channelASyncLayout.addWidget(self.channelASyncLabel)
        channelASyncLayout.addWidget(self.channelASyncTo)
        self.channelASyncTo.setCurrentText(self.QComController.masterState['A'][1].replace('CH', 'Channel '))
        # delay
        self.channelADelayLabel = QLabel('Delay (μs)')
        self.channelADelay =QLineEdit(str(self.QComController.masterState['A'][2]))
        self.channelADelaySet = QPushButton('Set')
        channelADelayLayout = QHBoxLayout()
        channelADelayLayout.addWidget(self.channelADelayLabel)
        channelADelayLayout.addWidget(self.channelADelay)
        channelADelayLayout.addWidget(self.channelADelaySet)
        #width        
        self.channelAWidthLabel = QLabel('Width (μs)')
        self.channelAWidth =QLineEdit(str(self.QComController.masterState['A'][4])) 
        self.channelAWidthSet = QPushButton('Set')
        channelAWidthLayout = QHBoxLayout()
        channelAWidthLayout.addWidget(self.channelAWidthLabel)
        channelAWidthLayout.addWidget(self.channelAWidth)
        channelAWidthLayout.addWidget(self.channelAWidthSet)
        #readout
        self.channelAReadoutDelayLabel = QLabel('Current delay: ')
        self.channelADelayRead = QLabel(self.QComController.masterState['A'][2] + ' µs')
        self.channelAReadoutSyncLabel = QLabel('Currently synced to: ')
        self.channelASyncRead = QLabel(self.QComController.masterState['A'][1].replace('CH', 'Channel '))
        channelAReadoutLayout = QHBoxLayout()
        channelAReadoutLayout.addWidget(self.channelAReadoutDelayLabel)
        channelAReadoutLayout.addWidget(self.channelADelayRead)
        channelAReadoutLayout.addWidget(self.channelAReadoutSyncLabel)
        channelAReadoutLayout.addWidget(self.channelASyncRead)
        self.channelAReadoutWidthLabel = QLabel('Current Width: ')
        self.channelAWidthRead = QLabel(self.QComController.masterState['A'][4] + ' µs') 
        channelAReadoutLayout.addWidget(self.channelAReadoutWidthLabel)
        channelAReadoutLayout.addWidget(self.channelAWidthRead)

        channelALayout = QVBoxLayout()
        channelALayout.addWidget(self.channelATitle)
        channelALayout.addLayout(channelAStatus)
        channelALayout.addLayout(channelASyncLayout)
        channelALayout.addLayout(channelADelayLayout)
        channelALayout.addLayout(channelAWidthLayout)
        channelALayout.addLayout(channelAReadoutLayout)

        ## channel B
        self.channelBTitle = QLabel(self.QComController.masterState['B'][3])
        self.channelBTitle.setFont(QFont('Times New Roman', 10))
        # on/off
        self.channelBSwitchOn = QRadioButton('ON')
        self.channelBSwitchOff = QRadioButton('OFF')
        self.buttonGroupB = QButtonGroup()
        self.buttonGroupB.addButton(self.channelBSwitchOn)
        self.buttonGroupB.addButton(self.channelBSwitchOff)
        channelBStatus = QHBoxLayout()
        channelBStatus.addWidget(self.channelBSwitchOn)
        channelBStatus.addWidget(self.channelBSwitchOff)
        if self.QComController.masterState['B'][0] == '0':
            self.channelBSwitchOff.setChecked(True)
        else:
            self.channelBSwitchOn.setChecked(True)
        # sync
        self.channelBSyncLabel = QLabel('Sync to: ')
        self.channelBSyncTo = QComboBox()
        self.channelBSyncTo.addItem('T0')
        self.channelBSyncTo.addItem('Channel A')
        self.channelBSyncTo.addItem('Channel C')
        self.channelBSyncTo.addItem('Channel D')
        self.channelBSyncTo.addItem('Channel E')
        self.channelBSyncTo.addItem('Channel F')
        self.channelBSyncTo.addItem('Channel G')
        self.channelBSyncTo.addItem('Channel H')
        channelBSyncLayout = QHBoxLayout()
        channelBSyncLayout.addWidget(self.channelBSyncLabel)
        channelBSyncLayout.addWidget(self.channelBSyncTo)
        self.channelBSyncTo.setCurrentText(self.QComController.masterState['B'][1].replace('CH', 'Channel '))
        # delay
        self.channelBDelayLabel = QLabel('Delay (μs)')
        self.channelBDelay =QLineEdit(str(self.QComController.masterState['B'][2]))
        self.channelBDelaySet = QPushButton('Set')
        channelBDelayLayout = QHBoxLayout()
        channelBDelayLayout.addWidget(self.channelBDelayLabel)
        channelBDelayLayout.addWidget(self.channelBDelay)
        channelBDelayLayout.addWidget(self.channelBDelaySet)        
        #width        
        self.channelBWidthLabel = QLabel('Width (μs)')
        self.channelBWidth =QLineEdit(str(self.QComController.masterState['B'][4])) 
        self.channelBWidthSet = QPushButton('Set')
        channelBWidthLayout = QHBoxLayout()
        channelBWidthLayout.addWidget(self.channelBWidthLabel)
        channelBWidthLayout.addWidget(self.channelBWidth)
        channelBWidthLayout.addWidget(self.channelBWidthSet)
        #readout
        self.channelBReadoutDelayLabel = QLabel('Current delay: ')
        self.channelBDelayRead = QLabel(self.QComController.masterState['B'][2] + ' µs')
        self.channelBReadoutSyncLabel = QLabel('Currently synced to: ')
        self.channelBSyncRead = QLabel(self.QComController.masterState['B'][1].replace('CH', 'Channel '))
        channelBReadoutLayout = QHBoxLayout()
        channelBReadoutLayout.addWidget(self.channelBReadoutDelayLabel)
        channelBReadoutLayout.addWidget(self.channelBDelayRead)
        channelBReadoutLayout.addWidget(self.channelBReadoutSyncLabel)
        channelBReadoutLayout.addWidget(self.channelBSyncRead)
        self.channelBReadoutWidthLabel = QLabel('Current Width: ')
        self.channelBWidthRead = QLabel(self.QComController.masterState['B'][4] + ' µs') 
        channelBReadoutLayout.addWidget(self.channelBReadoutWidthLabel)
        channelBReadoutLayout.addWidget(self.channelBWidthRead)

        channelBLayout = QVBoxLayout()
        channelBLayout.addWidget(self.channelBTitle)
        channelBLayout.addLayout(channelBStatus)
        channelBLayout.addLayout(channelBSyncLayout)
        channelBLayout.addLayout(channelBDelayLayout)
        channelBLayout.addLayout(channelBWidthLayout)
        channelBLayout.addLayout(channelBReadoutLayout)


        ## channel C
        self.channelCTitle = QLabel(self.QComController.masterState['C'][3])
        self.channelCTitle.setFont(QFont('Times New Roman', 10))
        # on/off
        self.channelCSwitchOn = QRadioButton('ON')
        self.channelCSwitchOff = QRadioButton('OFF')
        self.buttonGroupC = QButtonGroup()
        self.buttonGroupC.addButton(self.channelCSwitchOn)
        self.buttonGroupC.addButton(self.channelCSwitchOff)
        channelCStatus = QHBoxLayout()
        channelCStatus.addWidget(self.channelCSwitchOn)
        channelCStatus.addWidget(self.channelCSwitchOff)
        if self.QComController.masterState['C'][0] == '0':
            self.channelCSwitchOff.setChecked(True)
        else:
            self.channelCSwitchOn.setChecked(True)
        # sync
        self.channelCSyncLabel = QLabel('Sync to: ')
        self.channelCSyncTo = QComboBox()
        self.channelCSyncTo.addItem('T0')
        self.channelCSyncTo.addItem('Channel A')
        self.channelCSyncTo.addItem('Channel B')
        self.channelCSyncTo.addItem('Channel D')
        self.channelCSyncTo.addItem('Channel E')
        self.channelCSyncTo.addItem('Channel F')
        self.channelCSyncTo.addItem('Channel G')
        self.channelCSyncTo.addItem('Channel H')
        channelCSyncLayout = QHBoxLayout()
        channelCSyncLayout.addWidget(self.channelCSyncLabel)
        channelCSyncLayout.addWidget(self.channelCSyncTo)
        self.channelCSyncTo.setCurrentText(self.QComController.masterState['C'][1].replace('CH', 'Channel '))
        # delay
        self.channelCDelayLabel = QLabel('Delay (μs)')
        self.channelCDelay =QLineEdit(str(self.QComController.masterState['C'][2]))
        self.channelCDelaySet = QPushButton('Set')
        channelCDelayLayout = QHBoxLayout()
        channelCDelayLayout.addWidget(self.channelCDelayLabel)
        channelCDelayLayout.addWidget(self.channelCDelay)
        channelCDelayLayout.addWidget(self.channelCDelaySet)
        #width        
        self.channelCWidthLabel = QLabel('Width (μs)')
        self.channelCWidth =QLineEdit(str(self.QComController.masterState['C'][4])) 
        self.channelCWidthSet = QPushButton('Set')
        channelCWidthLayout = QHBoxLayout()
        channelCWidthLayout.addWidget(self.channelCWidthLabel)
        channelCWidthLayout.addWidget(self.channelCWidth)
        channelCWidthLayout.addWidget(self.channelCWidthSet)
        #readout
        self.channelCReadoutDelayLabel = QLabel('Current delay: ')
        self.channelCDelayRead = QLabel(self.QComController.masterState['C'][2] + ' µs')
        self.channelCReadoutSyncLabel = QLabel('Currently synced to: ')
        self.channelCSyncRead = QLabel(self.QComController.masterState['C'][1].replace('CH', 'Channel '))
        channelCReadoutLayout = QHBoxLayout()
        channelCReadoutLayout.addWidget(self.channelCReadoutDelayLabel)
        channelCReadoutLayout.addWidget(self.channelCDelayRead)
        channelCReadoutLayout.addWidget(self.channelCReadoutSyncLabel)
        channelCReadoutLayout.addWidget(self.channelCSyncRead)
        self.channelCReadoutWidthLabel = QLabel('Current Width: ')
        self.channelCWidthRead = QLabel(self.QComController.masterState['C'][4] + ' µs') 
        channelCReadoutLayout.addWidget(self.channelCReadoutWidthLabel)
        channelCReadoutLayout.addWidget(self.channelCWidthRead)

        channelCLayout = QVBoxLayout()
        channelCLayout.addWidget(self.channelCTitle)
        channelCLayout.addLayout(channelCStatus)
        channelCLayout.addLayout(channelCSyncLayout)
        channelCLayout.addLayout(channelCDelayLayout)
        channelCLayout.addLayout(channelCWidthLayout)
        channelCLayout.addLayout(channelCReadoutLayout)

        ## channel D
        self.channelDTitle = QLabel(self.QComController.masterState['D'][3])
        self.channelDTitle.setFont(QFont('Times New Roman', 10))
        # on/off
        self.channelDSwitchOn = QRadioButton('ON')
        self.channelDSwitchOff = QRadioButton('OFF')
        self.buttonGroupD = QButtonGroup()
        self.buttonGroupD.addButton(self.channelDSwitchOn)
        self.buttonGroupD.addButton(self.channelDSwitchOff)
        channelDStatus = QHBoxLayout()
        channelDStatus.addWidget(self.channelDSwitchOn)
        channelDStatus.addWidget(self.channelDSwitchOff)
        if self.QComController.masterState['D'][0] == '0':
            self.channelDSwitchOff.setChecked(True)
        else:
            self.channelDSwitchOn.setChecked(True)
        # sync
        self.channelDSyncLabel = QLabel('Sync to: ')
        self.channelDSyncTo = QComboBox()
        self.channelDSyncTo.addItem('T0')
        self.channelDSyncTo.addItem('Channel A')
        self.channelDSyncTo.addItem('Channel B')
        self.channelDSyncTo.addItem('Channel C')
        self.channelDSyncTo.addItem('Channel E')
        self.channelDSyncTo.addItem('Channel F')
        self.channelDSyncTo.addItem('Channel G')
        self.channelDSyncTo.addItem('Channel H')
        channelDSyncLayout = QHBoxLayout()
        channelDSyncLayout.addWidget(self.channelDSyncLabel)
        channelDSyncLayout.addWidget(self.channelDSyncTo)
        self.channelDSyncTo.setCurrentText(self.QComController.masterState['D'][1].replace('CH', 'Channel '))
        # delay
        self.channelDDelayLabel = QLabel('Delay (μs)')
        self.channelDDelay =QLineEdit(str(self.QComController.masterState['D'][2]))
        self.channelDDelaySet = QPushButton('Set')
        channelDDelayLayout = QHBoxLayout()
        channelDDelayLayout.addWidget(self.channelDDelayLabel)
        channelDDelayLayout.addWidget(self.channelDDelay)
        channelDDelayLayout.addWidget(self.channelDDelaySet)
        #width        
        self.channelDWidthLabel = QLabel('Width (μs)')
        self.channelDWidth =QLineEdit(str(self.QComController.masterState['D'][4])) 
        self.channelDWidthSet = QPushButton('Set')
        channelDWidthLayout = QHBoxLayout()
        channelDWidthLayout.addWidget(self.channelDWidthLabel)
        channelDWidthLayout.addWidget(self.channelDWidth)
        channelDWidthLayout.addWidget(self.channelDWidthSet)
        #readout
        self.channelDReadoutDelayLabel = QLabel('Current delay: ')
        self.channelDDelayRead = QLabel(self.QComController.masterState['D'][2] + ' µs')
        self.channelDReadoutSyncLabel = QLabel('Currently synced to: ')
        self.channelDSyncRead = QLabel(self.QComController.masterState['D'][1].replace('CH', 'Channel '))
        channelDReadoutLayout = QHBoxLayout()
        channelDReadoutLayout.addWidget(self.channelDReadoutDelayLabel)
        channelDReadoutLayout.addWidget(self.channelDDelayRead)
        channelDReadoutLayout.addWidget(self.channelDReadoutSyncLabel)
        channelDReadoutLayout.addWidget(self.channelDSyncRead)
        self.channelDReadoutWidthLabel = QLabel('Current Width: ')
        self.channelDWidthRead = QLabel(self.QComController.masterState['D'][4] + ' µs') 
        channelDReadoutLayout.addWidget(self.channelDReadoutWidthLabel)
        channelDReadoutLayout.addWidget(self.channelDWidthRead)

        channelDLayout = QVBoxLayout()
        channelDLayout.addWidget(self.channelDTitle)
        channelDLayout.addLayout(channelDStatus)
        channelDLayout.addLayout(channelDSyncLayout)
        channelDLayout.addLayout(channelDDelayLayout)
        channelDLayout.addLayout(channelDWidthLayout)
        channelDLayout.addLayout(channelDReadoutLayout)

        channelAtoDLayout = QVBoxLayout()
        pushButtonUpdate=QPushButton("Refresh Values from QC")
        pushButtonUpdate.clicked.connect(self.refreshUI)
        channelAtoDLayout.addWidget(pushButtonUpdate)
        channelAtoDLayout.addLayout(channelALayout)
        channelAtoDLayout.addLayout(channelBLayout)
        channelAtoDLayout.addLayout(channelCLayout)
        channelAtoDLayout.addLayout(channelDLayout)

         ## channel E
        self.channelETitle = QLabel(self.QComController.masterState['E'][3])
        self.channelETitle.setFont(QFont('Times New Roman', 10))
        # on/off
        self.channelESwitchOn = QRadioButton('ON')
        self.channelESwitchOff = QRadioButton('OFF')
        self.buttonGroupE = QButtonGroup()
        self.buttonGroupE.addButton(self.channelESwitchOn)
        self.buttonGroupE.addButton(self.channelESwitchOff)
        channelEStatus = QHBoxLayout()
        channelEStatus.addWidget(self.channelESwitchOn)
        channelEStatus.addWidget(self.channelESwitchOff)
        if self.QComController.masterState['E'][0] == '0':
            self.channelESwitchOff.setChecked(True)
        else:
            self.channelESwitchOn.setChecked(True)
        # sync
        self.channelESyncLabel = QLabel('Sync to: ')
        self.channelESyncTo = QComboBox()
        self.channelESyncTo.addItem('T0')
        self.channelESyncTo.addItem('Channel A')
        self.channelESyncTo.addItem('Channel B')
        self.channelESyncTo.addItem('Channel C')
        self.channelESyncTo.addItem('Channel D')
        self.channelESyncTo.addItem('Channel F')
        self.channelESyncTo.addItem('Channel G')
        self.channelESyncTo.addItem('Channel H')
        channelESyncLayout = QHBoxLayout()
        channelESyncLayout.addWidget(self.channelESyncLabel)
        channelESyncLayout.addWidget(self.channelESyncTo)
        self.channelESyncTo.setCurrentText(self.QComController.masterState['E'][1].replace('CH', 'Channel '))
        # delay
        self.channelEDelayLabel = QLabel('Delay (μs)')
        self.channelEDelay =QLineEdit(str(self.QComController.masterState['E'][2]))
        self.channelEDelaySet = QPushButton('Set')
        channelEDelayLayout = QHBoxLayout()
        channelEDelayLayout.addWidget(self.channelEDelayLabel)
        channelEDelayLayout.addWidget(self.channelEDelay)
        channelEDelayLayout.addWidget(self.channelEDelaySet)
        #width        
        self.channelEWidthLabel = QLabel('Width (μs)')
        self.channelEWidth =QLineEdit(str(self.QComController.masterState['E'][4])) 
        self.channelEWidthSet = QPushButton('Set')
        channelEWidthLayout = QHBoxLayout()
        channelEWidthLayout.addWidget(self.channelEWidthLabel)
        channelEWidthLayout.addWidget(self.channelEWidth)
        channelEWidthLayout.addWidget(self.channelEWidthSet)
        #readout
        self.channelEReadoutDelayLabel = QLabel('Current delay: ')
        self.channelEDelayRead = QLabel(self.QComController.masterState['E'][2] + ' µs')
        self.channelEReadoutSyncLabel = QLabel('Currently synced to: ')
        self.channelESyncRead = QLabel(self.QComController.masterState['E'][1].replace('CH', 'Channel '))
        channelEReadoutLayout = QHBoxLayout()
        channelEReadoutLayout.addWidget(self.channelEReadoutDelayLabel)
        channelEReadoutLayout.addWidget(self.channelEDelayRead)
        channelEReadoutLayout.addWidget(self.channelEReadoutSyncLabel)
        channelEReadoutLayout.addWidget(self.channelESyncRead)
        self.channelEReadoutWidthLabel = QLabel('Current Width: ')
        self.channelEWidthRead = QLabel(self.QComController.masterState['E'][4] + ' µs') 
        channelEReadoutLayout.addWidget(self.channelEReadoutWidthLabel)
        channelEReadoutLayout.addWidget(self.channelEWidthRead)

        channelELayout = QVBoxLayout()
        channelELayout.addWidget(self.channelETitle)
        channelELayout.addLayout(channelEStatus)
        channelELayout.addLayout(channelESyncLayout)
        channelELayout.addLayout(channelEDelayLayout)
        channelELayout.addLayout(channelEWidthLayout)
        channelELayout.addLayout(channelEReadoutLayout)

        ## channel F
        self.channelFTitle = QLabel(self.QComController.masterState['F'][3])
        self.channelFTitle.setFont(QFont('Times New Roman', 10))
        # on/off
        self.channelFSwitchOn = QRadioButton('ON')
        self.channelFSwitchOff = QRadioButton('OFF')
        self.buttonGroupF = QButtonGroup()
        self.buttonGroupF.addButton(self.channelFSwitchOn)
        self.buttonGroupF.addButton(self.channelFSwitchOff)
        channelFStatus = QHBoxLayout()
        channelFStatus.addWidget(self.channelFSwitchOn)
        channelFStatus.addWidget(self.channelFSwitchOff)
        if self.QComController.masterState['F'][0] == '0':
            self.channelFSwitchOff.setChecked(True)
        else:
            self.channelFSwitchOn.setChecked(True)
        # sync
        self.channelFSyncLabel = QLabel('Sync to: ')
        self.channelFSyncTo = QComboBox()
        self.channelFSyncTo.addItem('T0')
        self.channelFSyncTo.addItem('Channel A')
        self.channelFSyncTo.addItem('Channel C')
        self.channelFSyncTo.addItem('Channel D')
        self.channelFSyncTo.addItem('Channel E')
        self.channelFSyncTo.addItem('Channel F')
        self.channelFSyncTo.addItem('Channel G')
        self.channelFSyncTo.addItem('Channel H')
        channelFSyncLayout = QHBoxLayout()
        channelFSyncLayout.addWidget(self.channelFSyncLabel)
        channelFSyncLayout.addWidget(self.channelFSyncTo)
        self.channelFSyncTo.setCurrentText(self.QComController.masterState['F'][1].replace('CH', 'Channel '))
        # delay
        self.channelFDelayLabel = QLabel('Delay (μs)')
        self.channelFDelay =QLineEdit(str(self.QComController.masterState['F'][2]))
        self.channelFDelaySet = QPushButton('Set')
        channelFDelayLayout = QHBoxLayout()
        channelFDelayLayout.addWidget(self.channelFDelayLabel)
        channelFDelayLayout.addWidget(self.channelFDelay)
        channelFDelayLayout.addWidget(self.channelFDelaySet)
        #width        
        self.channelFWidthLabel = QLabel('Width (μs)')
        self.channelFWidth =QLineEdit(str(self.QComController.masterState['F'][4])) 
        self.channelFWidthSet = QPushButton('Set')
        channelFWidthLayout = QHBoxLayout()
        channelFWidthLayout.addWidget(self.channelFWidthLabel)
        channelFWidthLayout.addWidget(self.channelFWidth)
        channelFWidthLayout.addWidget(self.channelFWidthSet)
        #readout
        self.channelFReadoutDelayLabel = QLabel('Current delay: ')
        self.channelFDelayRead = QLabel(self.QComController.masterState['F'][2] + ' µs')
        self.channelFReadoutSyncLabel = QLabel('Currently synced to: ')
        self.channelFSyncRead = QLabel(self.QComController.masterState['F'][1].replace('CH', 'Channel '))
        channelFReadoutLayout = QHBoxLayout()
        channelFReadoutLayout.addWidget(self.channelFReadoutDelayLabel)
        channelFReadoutLayout.addWidget(self.channelFDelayRead)
        channelFReadoutLayout.addWidget(self.channelFReadoutSyncLabel)
        channelFReadoutLayout.addWidget(self.channelFSyncRead)
        self.channelFReadoutWidthLabel = QLabel('Current Width: ')
        self.channelFWidthRead = QLabel(self.QComController.masterState['F'][4] + ' µs') 
        channelFReadoutLayout.addWidget(self.channelFReadoutWidthLabel)
        channelFReadoutLayout.addWidget(self.channelFWidthRead)

        channelFLayout = QVBoxLayout()
        channelFLayout.addWidget(self.channelFTitle)
        channelFLayout.addLayout(channelFStatus)
        channelFLayout.addLayout(channelFSyncLayout)
        channelFLayout.addLayout(channelFDelayLayout)
        channelFLayout.addLayout(channelFWidthLayout)
        channelFLayout.addLayout(channelFReadoutLayout)

        ## channel G
        self.channelGTitle = QLabel(self.QComController.masterState['G'][3])
        self.channelGTitle.setFont(QFont('Times New Roman', 10))
        # on/off
        self.channelGSwitchOn = QRadioButton('ON')
        self.channelGSwitchOff = QRadioButton('OFF')
        self.buttonGroupG = QButtonGroup()
        self.buttonGroupG.addButton(self.channelGSwitchOn)
        self.buttonGroupG.addButton(self.channelGSwitchOff)
        channelGStatus = QHBoxLayout()
        channelGStatus.addWidget(self.channelGSwitchOn)
        channelGStatus.addWidget(self.channelGSwitchOff)
        if self.QComController.masterState['G'][0] == '0':
            self.channelGSwitchOff.setChecked(True)
        else:
            self.channelGSwitchOn.setChecked(True)
        # sync
        self.channelGSyncLabel = QLabel('Sync to: ')
        self.channelGSyncTo = QComboBox()
        self.channelGSyncTo.addItem('T0')
        self.channelGSyncTo.addItem('Channel A')
        self.channelGSyncTo.addItem('Channel B')
        self.channelGSyncTo.addItem('Channel C')
        self.channelGSyncTo.addItem('Channel D')
        self.channelGSyncTo.addItem('Channel E')
        self.channelGSyncTo.addItem('Channel F')
        self.channelGSyncTo.addItem('Channel H')
        channelGSyncLayout = QHBoxLayout()
        channelGSyncLayout.addWidget(self.channelGSyncLabel)
        channelGSyncLayout.addWidget(self.channelGSyncTo)
        self.channelGSyncTo.setCurrentText(self.QComController.masterState['G'][1].replace('CH', 'Channel '))
        # delay
        self.channelGDelayLabel = QLabel('Delay (μs)')
        self.channelGDelay =QLineEdit(str(self.QComController.masterState['G'][2]))
        self.channelGDelaySet = QPushButton('Set')
        channelGDelayLayout = QHBoxLayout()
        channelGDelayLayout.addWidget(self.channelGDelayLabel)
        channelGDelayLayout.addWidget(self.channelGDelay)
        channelGDelayLayout.addWidget(self.channelGDelaySet)
        #width        
        self.channelGWidthLabel = QLabel('Width (μs)')
        self.channelGWidth =QLineEdit(str(self.QComController.masterState['G'][4])) 
        self.channelGWidthSet = QPushButton('Set')
        channelGWidthLayout = QHBoxLayout()
        channelGWidthLayout.addWidget(self.channelGWidthLabel)
        channelGWidthLayout.addWidget(self.channelGWidth)
        channelGWidthLayout.addWidget(self.channelGWidthSet)
        #readout
        self.channelGReadoutDelayLabel = QLabel('Current delay: ')
        self.channelGDelayRead = QLabel(self.QComController.masterState['G'][2] + ' µs')
        self.channelGReadoutSyncLabel = QLabel('Currently synced to: ')
        self.channelGSyncRead = QLabel(self.QComController.masterState['G'][1].replace('CH', 'Channel '))
        channelGReadoutLayout = QHBoxLayout()
        channelGReadoutLayout.addWidget(self.channelGReadoutDelayLabel)
        channelGReadoutLayout.addWidget(self.channelGDelayRead)
        channelGReadoutLayout.addWidget(self.channelGReadoutSyncLabel)
        channelGReadoutLayout.addWidget(self.channelGSyncRead)
        self.channelGReadoutWidthLabel = QLabel('Current Width: ')
        self.channelGWidthRead = QLabel(self.QComController.masterState['G'][4] + ' µs') 
        channelGReadoutLayout.addWidget(self.channelGReadoutWidthLabel)
        channelGReadoutLayout.addWidget(self.channelGWidthRead)

        channelGLayout = QVBoxLayout()
        channelGLayout.addWidget(self.channelGTitle)
        channelGLayout.addLayout(channelGStatus)
        channelGLayout.addLayout(channelGSyncLayout)
        channelGLayout.addLayout(channelGDelayLayout)
        channelGLayout.addLayout(channelGWidthLayout)
        channelGLayout.addLayout(channelGReadoutLayout)

        ## channel H
        self.channelHTitle = QLabel(self.QComController.masterState['H'][3])
        self.channelHTitle.setFont(QFont('Times New Roman', 10))
        # on/off
        self.channelHSwitchOn = QRadioButton('ON')
        self.channelHSwitchOff = QRadioButton('OFF')
        self.buttonGroupH = QButtonGroup()
        self.buttonGroupH.addButton(self.channelHSwitchOn)
        self.buttonGroupH.addButton(self.channelHSwitchOff)
        channelHStatus = QHBoxLayout()
        channelHStatus.addWidget(self.channelHSwitchOn)
        channelHStatus.addWidget(self.channelHSwitchOff)
        if self.QComController.masterState['H'][0] == '0':
            self.channelHSwitchOff.setChecked(True)
        else:
            self.channelHSwitchOn.setChecked(True)
        # sync
        self.channelHSyncLabel = QLabel('Sync to: ')
        self.channelHSyncTo = QComboBox()
        self.channelHSyncTo.addItem('T0')
        self.channelHSyncTo.addItem('Channel A')
        self.channelHSyncTo.addItem('Channel B')
        self.channelHSyncTo.addItem('Channel C')
        self.channelHSyncTo.addItem('Channel D')
        self.channelHSyncTo.addItem('Channel E')
        self.channelHSyncTo.addItem('Channel F')
        self.channelHSyncTo.addItem('Channel G')
        channelHSyncLayout = QHBoxLayout()
        channelHSyncLayout.addWidget(self.channelHSyncLabel)
        channelHSyncLayout.addWidget(self.channelHSyncTo)
        self.channelHSyncTo.setCurrentText(self.QComController.masterState['H'][1].replace('CH', 'Channel '))
        # delay
        self.channelHDelayLabel = QLabel('Delay (μs)')
        self.channelHDelay =QLineEdit(str(self.QComController.masterState['H'][2]))
        self.channelHDelaySet = QPushButton('Set')
        channelHDelayLayout = QHBoxLayout()
        channelHDelayLayout.addWidget(self.channelHDelayLabel)
        channelHDelayLayout.addWidget(self.channelHDelay)
        #width        
        self.channelHWidthLabel = QLabel('Width (μs)')
        self.channelHWidth =QLineEdit(str(self.QComController.masterState['H'][4])) 
        # self.channelHWidthSet = QPushButton('Set')
        channelHWidthLayout = QHBoxLayout()
        channelHWidthLayout.addWidget(self.channelHWidthLabel)
        channelHWidthLayout.addWidget(self.channelHWidth)
        # channelHWidthLayout.addWidget(self.channelHWidthSet)
        #readout
        self.channelHReadoutDelayLabel = QLabel('Current delay: ')
        self.channelHDelayRead = QLabel(self.QComController.masterState['H'][2] + ' µs')
        self.channelHReadoutSyncLabel = QLabel('Currently synced to: ')
        self.channelHSyncRead = QLabel(self.QComController.masterState['H'][1].replace('CH', 'Channel '))
        channelHReadoutLayout = QHBoxLayout()
        channelHReadoutLayout.addWidget(self.channelHReadoutDelayLabel)
        channelHReadoutLayout.addWidget(self.channelHDelayRead)
        channelHReadoutLayout.addWidget(self.channelHReadoutSyncLabel)
        channelHReadoutLayout.addWidget(self.channelHSyncRead)
        self.channelHReadoutWidthLabel = QLabel('Current Width: ')
        self.channelHWidthRead = QLabel(self.QComController.masterState['H'][4] + ' µs') 
        channelHReadoutLayout.addWidget(self.channelHReadoutWidthLabel)
        channelHReadoutLayout.addWidget(self.channelHWidthRead)

        channelHLayout = QVBoxLayout()
        channelHLayout.addWidget(self.channelHTitle)
        channelHLayout.addLayout(channelHStatus)
        channelHLayout.addLayout(channelHSyncLayout)
        channelHLayout.addLayout(channelHDelayLayout)
        channelHLayout.addLayout(channelHWidthLayout)
        channelHLayout.addLayout(channelHReadoutLayout)

        channelEtoHLayout = QVBoxLayout()
        channelEtoHLayout.addLayout(channelELayout)
        channelEtoHLayout.addLayout(channelFLayout)
        channelEtoHLayout.addLayout(channelGLayout)
        channelEtoHLayout.addLayout(channelHLayout)

        self.systemOnLabel = QLabel('Turn on all the channels')
        self.systemOn = QPushButton('SYSTEM ON')
        if self.QComController.triggering:
          self.systemOn.setText('SYSTEM ON')
          self.systemOn.setStyleSheet("background-color : lightblue")
        else:
          self.systemOn.setText('SYSTEM OFF')
          self.systemOn.setStyleSheet("background-color : lightpink")
        self.systemOn.setCheckable(True)
        self.systemOn.clicked.connect(lambda:self.start())


        channelsLayout = QHBoxLayout()
        channelsLayout.addLayout(channelAtoDLayout)
        channelsLayout.addLayout(channelEtoHLayout)

        windowLayout = QVBoxLayout()
        windowLayout.addLayout(channelsLayout)
        windowLayout.addWidget(self.systemOn)


        self.setLayout(windowLayout)
        # self.show()

        self.channelASwitchOn.clicked.connect(lambda:self.switchOnClick('A'))
        self.channelASwitchOff.clicked.connect(lambda:self.switchOffClick('A'))
        self.channelASyncTo.activated.connect(lambda:self.syncTo('A'))
        self.channelADelaySet.clicked.connect(lambda:self.delaySelect('A'))
        self.channelAWidthSet.clicked.connect(lambda:self.widthSelect('A'))

        self.channelBSwitchOn.clicked.connect(lambda:self.switchOnClick('B'))
        self.channelBSwitchOff.clicked.connect(lambda:self.switchOffClick('B'))
        self.channelBSyncTo.activated.connect(lambda:self.syncTo('B'))
        self.channelBDelaySet.clicked.connect(lambda:self.delaySelect('B'))
        self.channelBWidthSet.clicked.connect(lambda:self.widthSelect('B'))

        self.channelCSwitchOn.clicked.connect(lambda:self.switchOnClick('C'))
        self.channelCSwitchOff.clicked.connect(lambda:self.switchOffClick('C'))
        self.channelCSyncTo.activated.connect(lambda:self.syncTo('C'))
        self.channelCDelaySet.clicked.connect(lambda:self.delaySelect('C'))
        self.channelCWidthSet.clicked.connect(lambda:self.widthSelect('C'))

        self.channelDSwitchOn.clicked.connect(lambda:self.switchOnClick('D'))
        self.channelDSwitchOff.clicked.connect(lambda:self.switchOffClick('D'))
        self.channelDSyncTo.activated.connect(lambda:self.syncTo('D'))
        self.channelDDelaySet.clicked.connect(lambda:self.delaySelect('D'))
        self.channelDWidthSet.clicked.connect(lambda:self.widthSelect('D'))

        self.channelESwitchOn.clicked.connect(lambda:self.switchOnClick('E'))
        self.channelESwitchOff.clicked.connect(lambda:self.switchOffClick('E'))
        self.channelESyncTo.activated.connect(lambda:self.syncTo('E'))
        self.channelEDelaySet.clicked.connect(lambda:self.delaySelect('E'))
        self.channelEWidthSet.clicked.connect(lambda:self.widthSelect('E'))

        self.channelFSwitchOn.clicked.connect(lambda:self.switchOnClick('F'))
        self.channelFSwitchOff.clicked.connect(lambda:self.switchOffClick('F'))
        self.channelFSyncTo.activated.connect(lambda:self.syncTo('F'))
        self.channelFDelaySet.clicked.connect(lambda:self.delaySelect('F'))
        self.channelFWidthSet.clicked.connect(lambda:self.widthSelect('F'))

        self.channelGSwitchOn.clicked.connect(lambda:self.switchOnClick('G'))
        self.channelGSwitchOff.clicked.connect(lambda:self.switchOffClick('G'))
        self.channelGSyncTo.activated.connect(lambda:self.syncTo('G'))
        self.channelGDelaySet.clicked.connect(lambda:self.delaySelect('G'))
        self.channelGWidthSet.clicked.connect(lambda:self.widthSelect('G'))

        self.channelHSwitchOn.clicked.connect(lambda:self.switchOnClick('H'))
        self.channelHSwitchOff.clicked.connect(lambda:self.switchOffClick('H'))
        self.channelHSyncTo.activated.connect(lambda:self.syncTo('H'))
        self.channelHDelaySet.clicked.connect(lambda:self.delaySelect('H'))

    def start(self):
        if not self.QComController.triggering: #self.systemOn.isChecked() == True:
            self.QComController.start()
            self.systemOn.setText('SYSTEM ON')
            self.systemOn.setStyleSheet("background-color : lightblue")
        elif self.QComController.triggering:#self.systemOn.isChecked() == False:
            self.QComController.stop()
            self.systemOn.setText('SYSTEM OFF')
            self.systemOn.setStyleSheet("background-color : lightpink")
        else:
            if self.verbose: print('QC+: error')
        for channel in self.QComController.masterState.keys():
            self.QComController.getState(channel)
            if self.QComController.masterState[channel][0] == '1':
                self.stateDict[channel][0].setChecked(True)
            elif self.QComController.masterState[channel][0] == '0':
                self.stateDict[channel][1].setChecked(True)
            else:
                if self.verbose: print('QC+: error')

    def switchOnClick(self, channel):
        if self.QComController.masterState[channel][0] == '0':
            self.QComController.setState(channel, 'ON')
            self.QComController.masterState[channel][0] = '1'
            if self.verbose: print(self.QComController.masterState[channel][0])
            self.QComController.getState(channel)
        else:
            if self.verbose: print('QC+: already on')
    
    def switchOffClick(self, channel):
        if self.QComController.masterState[channel][0] == '1':
            self.QComController.setState(channel, 'OFF')
            self.QComController.masterState[channel][0] == '0'
            if self.verbose: print(self.QComController.masterState[channel][0])
            self.QComController.getState(channel)
        else:
            if self.verbose: print('QC+: already off')
    
    def syncTo(self, channel):
        sync = self.syncDict[channel][0].currentText()
        if 'Channel ' in sync:
            sync = sync.replace('Channel ', 'CH')
            if self.verbose: print(sync)
        else:
            sync = 'T0'
            if self.verbose: print(sync)
        self.QComController.setSync(channel, sync)
        self.QComController.getSync(channel)
        self.syncDict[channel][1].setText(self.QComController.masterState[channel][1].replace('CH', 'Channel '))
    
    def delaySelect(self, channel):
        delay = self.delayDict[channel][0].text()
        self.QComController.setDelay(channel, delay)
        self.QComController.getDelay(channel)
        self.delayDict[channel][1].setText(self.QComController.masterState[channel][2] + ' µs')
        self.delayDict[channel][0].setText(self.QComController.masterState[channel][2])
        # self.QComController.getSync(channel)  
    def widthSelect(self, channel):
        width = self.widthDict[channel][0].text()
        self.QComController.setWidth(channel, width)
        self.QComController.getWidth(channel)
        self.widthDict[channel][1].setText(self.QComController.masterState[channel][4] + ' µs')
        self.widthDict[channel][0].setText(self.QComController.masterState[channel][4])
        # self.QComController.getSync(channel)  
    def refreshUI(self):
        self.QComController.getQCValues()
        for ch in self.QComController.masterState.keys():
          # self.stateDict #[switchOn, SwitchOff]
          if self.QComController.masterState[ch][0] == '0': #radio buttons
              self.stateDict[ch][1].setChecked(True)
          else:
              self.stateDict[ch][0].setChecked(True)

          # self.delayDict #[delay textbox, delay readout]
          self.delayDict[ch][1].setText(self.QComController.masterState[ch][2] + ' µs')
          # self.channelCDelayRead.setText(self.QComController.masterState['C'][2] + ' µs') #delay readout label

          self.delayDict[ch][0].setText(str(self.QComController.masterState[ch][2]))
          # self.channelHDelay.setText(str(self.QComController.masterState['H'][2])) #delay lineedit

          #widthDict bla
          self.widthDict[ch][1].setText(self.QComController.masterState[ch][4] + ' µs')
          # self.channelCDelayRead.setText(self.QComController.masterState['C'][2] + ' µs') #delay readout label

          self.widthDict[ch][0].setText(str(self.QComController.masterState[ch][4]))

          self.syncDict[ch][0].setCurrentText(self.QComController.masterState[ch][1].replace('CH', 'Channel '))
          # self.channelHSyncTo.setCurrentText(self.QComController.masterState['H'][1].replace('CH', 'Channel ')) #combobox

          self.syncDict[ch][1].setText(self.QComController.masterState[ch][1].replace('CH', 'Channel '))
          # self.channelHSyncRead.setText(self.QComController.masterState['H'][1].replace('CH', 'Channel '))
        
        if self.QComController.triggering:
          self.systemOn.setText('SYSTEM ON')
          self.systemOn.setStyleSheet("background-color : lightblue")
        else:
          self.systemOn.setText('SYSTEM OFF')
          self.systemOn.setStyleSheet("background-color : lightpink")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = mainWindow(verbose=True)
    ex.show()
    app.exec()