import time
import json
import threading
import serial
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton,\
QGroupBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton, \
QComboBox, QDoubleSpinBox, QButtonGroup
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
        sn = 'AB0PEW5NA' #this is specific to the cable for the quantum composer, so it needs to be changed if the cable changes
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
            print("QC+ Failed to connect.")
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
        try:
            command = ':PULSE' + self.channel_number + ':DELAY ' + '{:.9f}'.format(float(delay)*1e-6)
        except ValueError:
            print("QC+ Invaid input")
            return
        self.write(command, channel, 2)

    def getWidth(self, channel):
        self.channel_number = self.channel_index[channel]
        command = ":PULSE"+str(self.channel_number)+":WIDTH?"
        self.write(command, channel, 4)

    @pauseTrigDecorator
    def setWidth(self, channel, width):
        self.channel_number = self.channel_index[channel]
        try:
            command = ':PULSE' + self.channel_number + ':WIDTH ' + '{:.9f}'.format(float(width)*1e-6)
        except ValueError:
            print("QC+ Invaid input")
            return
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
        # self.stateDict = {'A': [self.channelASwitchOn, self.channelASwitchOff],
        #             'B': [self.channelBSwitchOn, self.channelBSwitchOff],
        #             'C': [self.channelCSwitchOn, self.channelCSwitchOff],
        #             'D': [self.channelDSwitchOn, self.channelDSwitchOff],
        #             'E': [self.channelESwitchOn, self.channelESwitchOff],
        #             'F': [self.channelFSwitchOn, self.channelFSwitchOff],
        #             'G': [self.channelGSwitchOn, self.channelGSwitchOff],
        #             'H': [self.channelHSwitchOn, self.channelHSwitchOff]
        #             }
        # self.delayDict = {'A': [self.channelADelay, self.channelADelayRead],
        #                 'B': [self.channelBDelay, self.channelBDelayRead],
        #                 'C': [self.channelCDelay, self.channelCDelayRead],
        #                 'D': [self.channelDDelay, self.channelDDelayRead],
        #                 'E': [self.channelEDelay, self.channelEDelayRead],
        #                 'F': [self.channelFDelay, self.channelFDelayRead],
        #                 'G': [self.channelGDelay, self.channelGDelayRead],
        #                 'H': [self.channelHDelay, self.channelHDelayRead]
        #                 }
        # self.widthDict = {'A': [self.channelAWidth, self.channelAWidthRead],
        #                 'B': [self.channelBWidth, self.channelBWidthRead],
        #                 'C': [self.channelCWidth, self.channelCWidthRead],
        #                 'D': [self.channelDWidth, self.channelDWidthRead],
        #                 'E': [self.channelEWidth, self.channelEWidthRead],
        #                 'F': [self.channelFWidth, self.channelFWidthRead],
        #                 'G': [self.channelGWidth, self.channelGWidthRead],
        #                 'H': [self.channelHWidth, self.channelHWidthRead]
        #                 }
        
        # self.syncDict = {'A': [self.channelASyncTo, self.channelASyncRead],
        #             'B': [self.channelBSyncTo, self.channelBSyncRead],
        #             'C': [self.channelCSyncTo, self.channelCSyncRead],
        #             'D': [self.channelDSyncTo, self.channelDSyncRead],
        #             'E': [self.channelESyncTo, self.channelESyncRead],
        #             'F': [self.channelFSyncTo, self.channelFSyncRead],
        #             'G': [self.channelGSyncTo, self.channelGSyncRead],
        #             'H': [self.channelHSyncTo, self.channelHSyncRead]
        #             }
        # Store the QC controller as a class level variable so it can be accessed in other functions
        # import ipdb; ipdb.set_trace()
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.height, self.width, self.height)
        # ## channel A
        # self.channelATitle = QLabel(self.QComController.masterState['A'][3])
        # self.channelATitle.setFont(QFont('Times New Roman', 10))
        # # on/off
        # self.channelASwitchOn = QRadioButton('ON')
        # self.channelASwitchOff = QRadioButton('OFF')
        # self.buttonGroupA = QButtonGroup()
        # self.buttonGroupA.addButton(self.channelASwitchOn)
        # self.buttonGroupA.addButton(self.channelASwitchOff)
        # channelAStatus = QHBoxLayout()
        # channelAStatus.addWidget(self.channelASwitchOn)
        # channelAStatus.addWidget(self.channelASwitchOff)
        # if self.QComController.masterState['A'][0] == '0':
        #     self.channelASwitchOff.setChecked(True)
        # else:
        #     self.channelASwitchOn.setChecked(True)
        # # sync
        # self.channelASyncLabel = QLabel('Sync to: ')
        # self.channelASyncTo = QComboBox()
        # self.channelASyncTo.addItem('T0')
        # self.channelASyncTo.addItem('Channel B')
        # self.channelASyncTo.addItem('Channel C')
        # self.channelASyncTo.addItem('Channel D')
        # self.channelASyncTo.addItem('Channel E')
        # self.channelASyncTo.addItem('Channel F')
        # self.channelASyncTo.addItem('Channel G')
        # self.channelASyncTo.addItem('Channel H')
        # channelASyncLayout = QHBoxLayout()
        # channelASyncLayout.addWidget(self.channelASyncLabel)
        # channelASyncLayout.addWidget(self.channelASyncTo)
        # self.channelASyncTo.setCurrentText(self.QComController.masterState['A'][1].replace('CH', 'Channel '))
        # # delay
        # self.channelADelayLabel = QLabel('Delay (μs)')

        # self.channelADelay =QDoubleSpinBox()
        # self.channelADelay.setValue(float(self.QComController.masterState['A'][2]))
        # self.channelADelay.setMinimum(0)
        # self.channelADelay.setMaximum(1000000)
        # self.channelADelay.setDecimals(3)
        # self.channelADelay.setSingleStep(10)

        # self.channelADelaySet = QPushButton('Set')
        # channelADelayLayout = QHBoxLayout()
        # channelADelayLayout.addWidget(self.channelADelayLabel)
        # channelADelayLayout.addWidget(self.channelADelay)
        # channelADelayLayout.addWidget(self.channelADelaySet)
        # #width        
        # self.channelAWidthLabel = QLabel('Width (μs)')

        # self.channelAWidth =QDoubleSpinBox()
        # self.channelAWidth.setValue(float(self.QComController.masterState['A'][4])) 
        # self.channelAWidth.setMinimum(0)
        # self.channelAWidth.setMaximum(1000000)
        # self.channelAWidth.setDecimals(3)
        # self.channelAWidth.setSingleStep(10)


        # self.channelAWidthSet = QPushButton('Set')
        # channelAWidthLayout = QHBoxLayout()
        # channelAWidthLayout.addWidget(self.channelAWidthLabel)
        # channelAWidthLayout.addWidget(self.channelAWidth)
        # channelAWidthLayout.addWidget(self.channelAWidthSet)
        # #readout
        # self.channelAReadoutDelayLabel = QLabel('Current delay: ')
        # self.channelADelayRead = QLabel(self.QComController.masterState['A'][2] + ' µs')
        # self.channelAReadoutSyncLabel = QLabel('Currently synced to: ')
        # self.channelASyncRead = QLabel(self.QComController.masterState['A'][1].replace('CH', 'Channel '))
        # channelAReadoutLayout = QHBoxLayout()
        # channelAReadoutLayout.addWidget(self.channelAReadoutDelayLabel)
        # channelAReadoutLayout.addWidget(self.channelADelayRead)
        # channelAReadoutLayout.addWidget(self.channelAReadoutSyncLabel)
        # channelAReadoutLayout.addWidget(self.channelASyncRead)
        # self.channelAReadoutWidthLabel = QLabel('Current Width: ')
        # self.channelAWidthRead = QLabel(self.QComController.masterState['A'][4] + ' µs') 
        # channelAReadoutLayout.addWidget(self.channelAReadoutWidthLabel)
        # channelAReadoutLayout.addWidget(self.channelAWidthRead)

        # channelALayout = QVBoxLayout()
        # channelALayout.addWidget(self.channelATitle)
        # channelALayout.addLayout(channelAStatus)
        # channelALayout.addLayout(channelASyncLayout)
        # channelALayout.addLayout(channelADelayLayout)
        # channelALayout.addLayout(channelAWidthLayout)
        # channelALayout.addLayout(channelAReadoutLayout)


        pushButtonUpdate=QPushButton("Refresh Values from QC")
        pushButtonUpdate.clicked.connect(self.refreshUI)

        self.stateDict = {}
        self.delayDict = {}
        self.widthDict = {}
        self.syncDict = {}

        channels = self.QComController.masterState.keys()
        channelLayouts = []
        channelLayoutCol1=QVBoxLayout()
        channelLayoutCol1.addWidget(pushButtonUpdate)
        channelLayoutCol2=QVBoxLayout()
        for i, ch in enumerate(channels):
            chLayout = self.generateQCChannelLayout(ch)
            channelLayouts.append(chLayout)
            if i<4:
                channelLayoutCol1.addLayout(chLayout)
            else:
                channelLayoutCol2.addLayout(chLayout)



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
        channelsLayout.addLayout(channelLayoutCol1)
        channelsLayout.addLayout(channelLayoutCol2)

        windowLayout = QVBoxLayout()
        windowLayout.addLayout(channelsLayout)
        windowLayout.addWidget(self.systemOn)


        self.setLayout(windowLayout)
        # self.show()

        # self.channelASwitchOn.clicked.connect(lambda:self.switchOnClick('A'))
        # self.channelASwitchOff.clicked.connect(lambda:self.switchOffClick('A'))
        # self.channelASyncTo.activated.connect(lambda:self.syncTo('A'))
        # self.channelADelaySet.clicked.connect(lambda:self.delaySelect('A'))
        # self.channelAWidthSet.clicked.connect(lambda:self.widthSelect('A'))


    def generateQCChannelLayout(self, channel):
        allChannels = self.QComController.masterState.keys()
        Title = QLabel(self.QComController.masterState[channel][3])
        Title.setFont(QFont('Times New Roman', 10))
        # on/off
        SwitchOn = QRadioButton('ON')
        SwitchOff = QRadioButton('OFF')
        buttonGroup = QButtonGroup(self)
        buttonGroup.addButton(SwitchOn)
        buttonGroup.addButton(SwitchOff)
        Status = QHBoxLayout()
        Status.addWidget(SwitchOn)
        Status.addWidget(SwitchOff)
        if self.QComController.masterState[channel][0] == '0':
            SwitchOff.setChecked(True)
        else:
            SwitchOn.setChecked(True)
        # sync
        SyncLabel = QLabel('Sync to: ')
        SyncTo = QComboBox()
        SyncTo.addItem('T0')
        for ch in allChannels:
            if channel!=ch:
                SyncTo.addItem(f'Channel {ch}')

        SyncLayout = QHBoxLayout()
        SyncLayout.addWidget(SyncLabel)
        SyncLayout.addWidget(SyncTo)
        SyncTo.setCurrentText(self.QComController.masterState[channel][1].replace('CH', 'Channel '))
        # delay
        DelayLabel = QLabel('Delay (μs)')

        Delay =QDoubleSpinBox()
        Delay.setMinimum(0)
        Delay.setMaximum(1000000)
        Delay.setDecimals(3)
        Delay.setSingleStep(10)
        Delay.setValue(float(self.QComController.masterState[channel][2]))

        DelaySet = QPushButton('Set')
        DelayLayout = QHBoxLayout()
        DelayLayout.addWidget(DelayLabel)
        DelayLayout.addWidget(Delay)
        DelayLayout.addWidget(DelaySet)
        #width        
        WidthLabel = QLabel('Width (μs)')

        Width =QDoubleSpinBox()
        Width.setMinimum(0)
        Width.setMaximum(1000000)
        Width.setDecimals(3)
        Width.setSingleStep(1)
        Width.setValue(float(self.QComController.masterState[channel][4])) 


        WidthSet = QPushButton('Set')
        WidthLayout = QHBoxLayout()
        WidthLayout.addWidget(WidthLabel)
        WidthLayout.addWidget(Width)
        WidthLayout.addWidget(WidthSet)
        #readout
        ReadoutDelayLabel = QLabel('Current delay: ')
        DelayRead = QLabel(self.QComController.masterState[channel][2] + ' µs')
        ReadoutSyncLabel = QLabel('Currently synced to: ')
        SyncRead = QLabel(self.QComController.masterState[channel][1].replace('CH', 'Channel '))
        ReadoutLayout = QHBoxLayout()
        ReadoutLayout.addWidget(ReadoutDelayLabel)
        ReadoutLayout.addWidget(DelayRead)
        ReadoutLayout.addWidget(ReadoutSyncLabel)
        ReadoutLayout.addWidget(SyncRead)
        ReadoutWidthLabel = QLabel('Current Width: ')
        WidthRead = QLabel(self.QComController.masterState[channel][4] + ' µs') 
        ReadoutLayout.addWidget(ReadoutWidthLabel)
        ReadoutLayout.addWidget(WidthRead)

        Layout = QVBoxLayout()
        Layout.addWidget(Title)
        Layout.addLayout(Status)
        Layout.addLayout(SyncLayout)
        Layout.addLayout(DelayLayout)
        Layout.addLayout(WidthLayout)
        Layout.addLayout(ReadoutLayout)

        SwitchOn.clicked.connect(lambda:self.switchOnClick(channel))
        SwitchOff.clicked.connect(lambda:self.switchOffClick(channel))
        SyncTo.activated.connect(lambda:self.syncTo(channel))
        DelaySet.clicked.connect(lambda:self.delaySelect(channel))
        WidthSet.clicked.connect(lambda:self.widthSelect(channel))

        self.stateDict[channel]= [SwitchOn, SwitchOff]
        #stateDict[channel] = [Aon, Aoff], no need to return
        self.delayDict[channel]= [Delay, DelayRead]
        self.widthDict[channel]= [Width, WidthRead]
        self.syncDict[channel]= [SyncTo, SyncRead]

        # import ipdb; ipdb.set_trace()
                            
        return Layout

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
        self.delayDict[channel][0].setValue(float(self.QComController.masterState[channel][2]))
        # self.QComController.getSync(channel)  
    def widthSelect(self, channel):
        width = self.widthDict[channel][0].text()
        self.QComController.setWidth(channel, width)
        self.QComController.getWidth(channel)
        self.widthDict[channel][1].setText(self.QComController.masterState[channel][4] + ' µs')
        self.widthDict[channel][0].setValue(float(self.QComController.masterState[channel][4]))
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

          self.delayDict[ch][0].setValue(float(self.QComController.masterState[ch][2]))
          # self.channelHDelay.setText(str(self.QComController.masterState['H'][2])) #delay lineedit

          #widthDict bla
          self.widthDict[ch][1].setText(self.QComController.masterState[ch][4] + ' µs')
          # self.channelCDelayRead.setText(self.QComController.masterState['C'][2] + ' µs') #delay readout label

          self.widthDict[ch][0].setValue(float(self.QComController.masterState[ch][4]))

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