from PyQt6.QtWidgets import QApplication, QWidget, QPushButton,\
QGroupBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton, \
QComboBox, QDoubleSpinBox, QButtonGroup
from PyQt6.QtGui import QFont

def generateQCChannelLayout(channel, masterState, stateDict, delayDict, widthDict, syncDict):
  allChannels = masterState.keys()
  Title = QLabel(masterState[channel][3])
  Title.setFont(QFont('Times New Roman', 10))
  # on/off
  SwitchOn = QRadioButton('ON')
  SwitchOff = QRadioButton('OFF')
  buttonGroupA = QButtonGroup()
  buttonGroupA.addButton(SwitchOn)
  buttonGroupA.addButton(SwitchOff)
  Status = QHBoxLayout()
  Status.addWidget(SwitchOn)
  Status.addWidget(SwitchOff)
  if masterState[channel][0] == '0':
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
  SyncTo.setCurrentText(masterState[channel][1].replace('CH', 'Channel '))
  # delay
  DelayLabel = QLabel('Delay (μs)')

  Delay =QDoubleSpinBox()
  Delay.setValue(float(masterState[channel][2]))
  Delay.setMinimum(0)
  Delay.setMaximum(1000000)
  Delay.setDecimals(3)
  Delay.setSingleStep(10)

  DelaySet = QPushButton('Set')
  DelayLayout = QHBoxLayout()
  DelayLayout.addWidget(DelayLabel)
  DelayLayout.addWidget(Delay)
  DelayLayout.addWidget(DelaySet)
  #width        
  WidthLabel = QLabel('Width (μs)')

  Width =QDoubleSpinBox()
  Width.setValue(float(masterState[channel][4])) 
  Width.setMinimum(0)
  Width.setMaximum(1000000)
  Width.setDecimals(3)
  Width.setSingleStep(10)


  WidthSet = QPushButton('Set')
  WidthLayout = QHBoxLayout()
  WidthLayout.addWidget(WidthLabel)
  WidthLayout.addWidget(Width)
  WidthLayout.addWidget(WidthSet)
  #readout
  ReadoutDelayLabel = QLabel('Current delay: ')
  DelayRead = QLabel(masterState[channel][2] + ' µs')
  ReadoutSyncLabel = QLabel('Currently synced to: ')
  SyncRead = QLabel(masterState[channel][1].replace('CH', 'Channel '))
  ReadoutLayout = QHBoxLayout()
  ReadoutLayout.addWidget(ReadoutDelayLabel)
  ReadoutLayout.addWidget(DelayRead)
  ReadoutLayout.addWidget(ReadoutSyncLabel)
  ReadoutLayout.addWidget(SyncRead)
  ReadoutWidthLabel = QLabel('Current Width: ')
  WidthRead = QLabel(masterState[channel][4] + ' µs') 
  ReadoutLayout.addWidget(ReadoutWidthLabel)
  ReadoutLayout.addWidget(WidthRead)

  Layout = QVBoxLayout()
  Layout.addWidget(Title)
  Layout.addLayout(Status)
  Layout.addLayout(SyncLayout)
  Layout.addLayout(DelayLayout)
  Layout.addLayout(WidthLayout)
  Layout.addLayout(ReadoutLayout)

  stateDict = {channel: [SwitchOn, SwitchOff]}
  #stateDict[channel] = [Aon, Aoff], no need to return
  delayDict = {channel: [Delay, DelayRead]}
  widthDict = {channel: [Width, WidthRead]}
  syncDict = {channel: [SyncTo, SyncRead]}
                    
  return Layout