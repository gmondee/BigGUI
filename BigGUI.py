import sys
import os
import requests
import json
import urllib
import asyncio
from functools import partial
from PyQt6 import QtWidgets, QtGui
from PyQt6.QtWidgets import QApplication, QMainWindow, QLayout, QFrame
from PyQt6.QtCore import QTimer, QStandardPaths, QThread, QObject, pyqtSignal
from PyQt6.QtGui import QAction
from ui_BigGUI import Ui_NEPTUNE_BigGUI
from BigSkyController.HugeSkyController import BigSkyHub
from PenningTrapISEG.Penning_Trap_Beam_Line import MyApp
from QuantumComposer.QuantumComposer import mainWindow as QComMainWindow
from TDC.TDC_DAQGUI import TDC_GUI
from pathlib import Path
from qasync import QEventLoop, asyncSlot

DOCS_PATH = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation))
# print(f"Documents folder: {DOCS_PATH}")



class BigGUI(QMainWindow):
  ### This is intended to consolidate the various NEPTUNE interfaces in one place. 
  ### Grant Mondeel | gmondeel@mit.edu | 07/25/2025
  def __init__(self, loop):
    super().__init__() #super]
    self.loop = loop #event loop, just storing it here so i can close it on exit
    self.IP = 'http://192.168.1.53:7557'
    self.auth = ('QTuser','QT_53')
    self.scanWavelength=None
    self.scanParams={}
    self.QCScanParams={}
    self.frequency = 10 # 10 Hz repetition rate
    self.scanSleepTask = None #this
    # Create and set up the UI
    self.ui = Ui_NEPTUNE_BigGUI()
    self.ui.setupUi(self)
    self.buildMenuBar()

    self.loadGUIs() #Load up the other GUIs, like the ablation control and TDC
    self.connect()  #Make the buttons do things

    set_all_margins(self)

  def buildMenuBar(self):
    fileMenu = self.ui.menubar.addMenu("Debug")

    # Create actions
    reloadQC = QAction("Reload QC", self)
    reloadAblation = QAction("Reload Ablation", self)
    reloadBeamline = QAction("Reload Beamline", self)
    reloadTDC = QAction("Reload TDC", self)

    # Add actions to menu
    fileMenu.addAction(reloadQC)
    fileMenu.addAction(reloadAblation)
    fileMenu.addAction(reloadBeamline)
    fileMenu.addAction(reloadTDC)

    # Connect using QAction.triggered.connect
    reloadQC.triggered.connect(lambda: self.loadQC(verbose=True))
    reloadAblation.triggered.connect(self.loadAblation)
    reloadBeamline.triggered.connect(self.loadBeamline)
    reloadTDC.triggered.connect(self.loadTDC)

  def loadGUIs(self):
    self.TDCLoaded = self.loadTDC() #load TDC last because its COM port checking is ugly
    self.AblationLoaded = self.loadAblation()
    self.BeamlineLoaded = self.loadBeamline()
    self.QCLoaded = self.loadQC()
    # if self.QCLoaded: self.prepareQCScan()

  def loadTDC(self):
    try:
      settingsDic={ 'int_time':1000,
                    'mode':'TTL',
                    'threshold':0.5,
                    'path':os.path.join(DOCS_PATH,'data','RFQ Tests')}
      self.TDCGUI = TDC_GUI(settingsDic=settingsDic)
      self.ui.frameTDC.layout().addWidget(self.TDCGUI)
      return 1
    except Exception as E:
      print(f"\nFailed to load TDCGUI: {E}")
      return 0
  def loadAblation(self):
    try: 
      self.AblationGUI.table_widget.safeExit()
      self.AblationGUI.layout().removeWidget(self.AblationGUI)
    except: pass
    try:
      self.AblationGUI = BigSkyHub()
      self.ui.frameAblation.layout().addWidget(self.AblationGUI)
      self.AblationGUI.table_widget.homeTab.labelLineEdits[-1].setText('NEPTUNE Ablation')
      self.AblationGUI.table_widget.homeTab.saveLabels()
      self.AblationGUI.table_widget.homeTab.buttons[-1].click()
      ablation_tab_count = self.AblationGUI.table_widget.tabs.count()
      ablationTabIndex = [i for i in range(ablation_tab_count) if "Ablation" in self.AblationGUI.table_widget.tabs.tabText(i)]
      self.ablationTab = self.AblationGUI.table_widget.tabs.widget(ablationTabIndex[0])
      print("Big Sky: Done.")
      return 1
    except Exception as E:
      print(f"\nFailed to load ablation GUI: {E}")
      return 0
  def loadBeamline(self):
    try:
      print("Beamline: Starting up...")
      self.BeamlineGUI = MyApp() #will be shown when the button is pressed
      script_dir = os.path.dirname(os.path.abspath(__file__))
      image_path = os.path.join(script_dir, "PenningTrapISEG","2D_Labeled_Diagram.png")
      self.BeamlineGUI.label_2.setPixmap(QtGui.QPixmap(image_path))
      self.BeamlineGUI.readAll()
      print("Beamline: Done.")
      return 1
    except Exception as E:
      print(f"\nFailed to load beamline GUI: {E}")
      return 0
  def loadQC(self, verbose=False):
    try: self.QCGUI.deleteLater()
    except: pass
    try:
      self.QCGUI = QComMainWindow(verbose=verbose)
      self.prepareQCScan()
      return 1
    except Exception as E:
      print(f"\nFailed to load Quantum Composer GUI: {E}")
      return 0
  def prepareQCScan(self):
    self.ui.comboBoxQCScanChannel.clear()
    for channel in  self.QCGUI.stateDict.keys():
      self.ui.comboBoxQCScanChannel.addItem(channel)

  def connect(self):
    ### Connects all of the interactive elements of the GUI to their respective functions
    # OPO Buttons
    self.ui.pushButtonToggleOPO.clicked.connect(lambda: self.sendToOPO(self.dict_enable_OPO()))
    self.ui.pushButtonOPOSet.clicked.connect(lambda: self.sendToOPO(self.dict_set_OPO_wavelength()))
    self.ui.pushButtonStartScan.clicked.connect(self.startWavelengthScan)
    self.ui.pushButtonStopScan.clicked.connect(self.stopWavelengthScan)
    # self.ui.pushButtonOpenOPOGUI.clicked.connect(self.openOPOGUI)
    self.ui.pushButtonOpenBeamlineGui.clicked.connect(self.openBeamlineGUI)
    self.ui.pushButtonOpenQC.clicked.connect(self.openQCGUI)
    self.ui.pushButtonStartLaser.clicked.connect(self.handleStartOPO) #cant think of any checks
    self.ui.pushButtonStopLaser.clicked.connect(self.handleStopOPO) #should also stop the scan
    self.ui.pushButtonQCScanStart.clicked.connect(self.startQCScan)
    self.ui.pushButtonQCScanStop.clicked.connect(self.stopQCScan)

  def handleStartOPO(self):
    ##any checks go here
    self.sendToOPO(self.dict_run_laser())

  def handleStopOPO(self):
    self.stopWavelengthScan()
    self.sendToOPO(self.dict_stop_laser())

  @asyncSlot()
  async def startQCScan(self):
    channel = self.ui.comboBoxQCScanChannel.currentText()
    if self.ui.radioButtonQCScanDelay.isChecked():
      scanMode = 'delay'
    elif self.ui.radioButtonQCScanWidth.isChecked():
      scanMode = 'width'
    else: 
      print("uh oh")
      return
    self.QCScanParams['startValue'] = self.ui.doubleSpinBoxQCScanStartValue.value()
    self.QCScanParams['endValue'] = self.ui.doubleSpinBoxQCScanEndValue.value()
    self.QCScanParams['stepSize'] = self.ui.doubleSpinBoxQCScanStepSize.value()
    self.QCScanParams['pulsesPerStep'] = self.ui.spinBoxQCScanPulsesPerStep.value()
    self.QCScanParams['mode'] = scanMode
    self.QCScanParams['channel'] = channel

    if self.QCScanParams["startValue"]+self.QCScanParams["stepSize"]>=self.QCScanParams["endValue"]:
      print('Starting time + step size must be less than the ending time')
      return
    
    self.QCScanTime = self.QCScanParams['startValue']

    ### Prepare for the scan
    ## Let user set ablation and OPO
    ## Disable GUI elements
    #TODO: disable GUI elements for safety

    scanETAmin = (1/self.frequency*self.QCScanParams["pulsesPerStep"]+0.5)*(self.QCScanParams["endValue"]-self.QCScanParams["startValue"])/self.QCScanParams["stepSize"]/60
    self.ui.labelQCScanStatus.setText("Scan Status: ON")
    print(f'Starting QC scan. ETA:{scanETAmin:.2f} minutes.\nScan parameters:{self.QCScanParams}')
    self.scanQCNext(scanMode)

  @asyncSlot()
  async def startWavelengthScan(self):

    ### Grab values from the GUI
    self.scanParams["startWL"] = self.ui.doubleSpinBoxScanStartingWavelength.value()
    self.scanParams["endWL"] = self.ui.doubleSpinBoxScanEndingWavelength.value()
    self.scanParams["stepSize"] = self.ui.doubleSpinBoxScanStepSize.value()
    self.scanParams["pulsesPerStep"] = self.ui.spinBoxScanPulsesPerStep.value()
    self.scanParams["measureAblationOff"] = self.ui.checkBoxScanMeasureAblationOff.isChecked()

    ### Check inputs
    if self.scanParams["startWL"]+self.scanParams["stepSize"]>=self.scanParams["endWL"]:
      print('Starting wavelength + step size must be less than the ending wavelength')
      return
    
    ### Construct the timer
    self.scanWavelength=self.scanParams["startWL"]

    ### Prepare for the scan
    ## Ablation on first; ablation control buttons are lampActivationButton and stopButton
    ablation_tab_count = self.AblationGUI.table_widget.tabs.count()
    ablationTabIndex = [i for i in range(ablation_tab_count) if "Ablation" in self.AblationGUI.table_widget.tabs.tabText(i)]
    self.ablationTab = self.AblationGUI.table_widget.tabs.widget(ablationTabIndex[0])
    self.ablationTab.lampActivationButton.click()
    ## OPO enabled and powered on (TODO: check shutter)
    self.ui.pushButtonToggleOPO.click() #enable OPO if it isn't already
    self.ui.doubleSpinBoxSetOPOWavelength.setValue(self.scanWavelength) #enter the initial wavelength
    self.ui.pushButtonOPOSet.click() #set the initial wavelength
    self.ui.pushButtonStartLaser.click() #start the laser
    if self.TDCGUI.scanToggled: #if there's a TDC run in progress, stop it
      self.TDCGUI.scanToggler.click()
    await asyncio.sleep(1.5) #let opo adjust before starting
    

  
    '''
    Start at the initial wavelength, set the DAQTimer according to pulsesPerStep, ablation on, and run
    On timeout, check if you need ablation off, rerun if needed.
    Change OPO parameters according to stepSize and repeat until self.scanWavelength+stepSize>endWL
    '''


    ### Disable scan GUI elements
    # Disable OPO options
    # Disable Ablation options
    # Disable TDC options
    scanETAmin=(1/self.frequency*self.scanParams["pulsesPerStep"]+1.5)*(self.scanParams["endWL"]-self.scanParams["startWL"])/self.scanParams["stepSize"]/60
    self.ui.labelScanStatus.setText("Scan Status: ON")
    print(f'Starting scan. ETA:{scanETAmin:.2f} minutes.\nScan parameters:{self.scanParams}')
    self.scanNext(skipSetup=True)

  @asyncSlot()
  async def scanNext(self, skipSetup=False):
    if not skipSetup:
      self.ui.doubleSpinBoxSetOPOWavelength.setValue(self.scanWavelength)
      self.ui.pushButtonOPOSet.click() #set the initial wavelength
      self.ui.pushButtonStartLaser.click() #start the laser
      await asyncio.sleep(1.5) #let opo adjust before starting
    
    ### Measure a spectrum, record parameters in the log file
    waitTime = int(1/self.frequency*self.scanParams["pulsesPerStep"])
    self.TDCGUI.scanToggler.click()
    try:
      await self.make_sleep_task(waitTime)
    except asyncio.CancelledError:
      print("Main function interrupted during sleep.")
      self.stopWavelengthScan()
      #TODO: handle canellation
      return
    #await asyncio.sleep(waitTime)## Wait for the measurement to finish
    self.TDCGUI.scanToggler.click()
    
    if self.scanParams["measureAblationOff"]:
      self.ablationTab.stopButton.click()
      self.TDCGUI.scanToggler.click()
      try:
        await self.make_sleep_task(waitTime)
      except asyncio.CancelledError:
        print("Main function interrupted during sleep.")
        self.stopWavelengthScan()
        return
      #await asyncio.sleep(waitTime)## Wait for the measurement to finish
      self.TDCGUI.scanToggler.click()
      self.ablationTab.lampActivationButton.click() #turn ablation back on for the next measurement
    
    if 2*self.scanParams["stepSize"]+self.scanWavelength >= self.scanParams["endWL"]:
      print("\nScan finished.\n")
      self.stopWavelengthScan()
      pass #scan over
    else:
      self.scanWavelength += self.scanParams["stepSize"]
      self.scanNext()

  def stopWavelengthScan(self):
    #self.scanTimer.stop()
    if self.scanSleepTask and not self.scanSleepTask.done():
      self.scanSleepTask.cancel()
      print('Stopped scan')
    else:
      print('No scan was in progress')
    self.ui.labelScanStatus.setText("Scan Status: OFF")
    
    ### Re-enable scan GUI elements

  def stopQCScan(self):
    #self.scanTimer.stop()
    if self.scanSleepTask and not self.scanSleepTask.done():
      self.scanSleepTask.cancel()
      print('Stopped scan')
    else:
      print('No scan was in progress')
    self.ui.labelQCScanStatus.setText("Scan Status: OFF")

  @asyncSlot()
  async def scanQCNext(self,scanMode):
    if self.TDCGUI.scanToggled: #if there's a TDC run in progress, stop it
      self.TDCGUI.scanToggler.click()
    waitTime = int(1/self.frequency*self.QCScanParams["pulsesPerStep"])
    channel = self.QCScanParams["channel"]

    if scanMode == "delay":
      # set the delay to the current value
      print(f'Setting QC delay to {self.QCScanTime}')
      self.QCGUI.QComController.setDelay(channel=channel, delay=self.QCScanTime)
    elif scanMode == "width": 
      print(f'Setting QC width to {self.QCScanTime}')
      self.QCGUI.QComController.setWidth(channel=channel, delay=self.QCScanTime)
    self.TDCGUI.scanToggler.click()  #start recording
    try:
      await self.make_sleep_task(waitTime)
    except asyncio.CancelledError:
      print("Main function interrupted during sleep.")
      # self.stopQCScan()
      #TODO: handle canellation
      return
    self.TDCGUI.scanToggler.click()

    if self.QCScanParams["stepSize"]+self.QCScanTime> self.QCScanParams["endValue"]:
      print("\nQC scan finished.\n")
      self.stopQCScan()
      pass #scan over
    else:
      self.QCScanTime += self.QCScanParams["stepSize"]
      self.scanQCNext()


  @asyncSlot()
  async def make_sleep_task(self, time_s):
      """Sleep that can be cancelled externally."""
      try:
        self.scanSleepTask = asyncio.create_task(asyncio.sleep(time_s))
        await self.scanSleepTask
      except asyncio.CancelledError:
        print("Sleep cancelled!")
        raise
      finally:
        self.scanSleepTask = None

  ### Functions for OPO communication
  def getOPOStatus(self):
    print("make the getOPOStatus function")

  def sendToOPO(self, payload):
    encoded = urllib.parse.quote(json.dumps(payload,separators=(',', ':')))
    url = f"{self.IP}/send?{encoded}"
    #todo: what if this fails
    response = requests.get(url, auth=self.auth)
    print("OPO Response:",response)
    if "failure" in response:
      print(f'\nFailed outgoing command {encoded}\nResponse:{response}')

  def openBeamlineGUI(self):
    try: self.BeamlineGUI.show()
    except Exception as E: print(E)

  def openQCGUI(self):
    try: self.QCGUI.show()
    except Exception as E: print(E)

  def dict_run_laser(self):
    return {"action":"control","code":{"device":"laser","values":{"laser-run": 1}}}

  def dict_stop_laser(self):
    return {"action":"control","code":{"device":"laser","values":{"laser-run": 0}}}

  def dict_set_OPO_wavelength(self): #in nm
    wavelengthnm = round(self.ui.doubleSpinBoxSetOPOWavelength.value(),2)
    return {"action":"control","code":{"device": "laser","values":{"forward-device":"opo","forward-protocol":"wavelength","forward-action":"control","wavelength": wavelengthnm}}}

  def dict_enable_OPO(self):
    return{"action":"control","code":{"device":"laser","values":{"forward-device":"harmonics","forward-protocol":"crystals","forward-action":"control","hu-status": 3.6}}}

  def dict_set_trigger_external_TP(self):
    return {"action":"control","code":{"device":"laser","values":{"trig-mode":2}}}
  
  def dict_set_trigger_internal(self):
    return {"action":"control","code":{"device":"laser","values":{"trig-mode":0}}}
  
  def closeEvent(self, event):
    print("\nClosing BigGUI...\n")
    try:
      print("Closing Beamline GUI...")
      self.BeamlineGUI.allChannelsOff()
    except Exception as E:
      print(E)
    try:
      print("Closing TDC GUI...")
      self.TDCGUI.safeExit()
    except Exception as E:
      print(E)
    try:
      print("Stopping event loop...")
      # self.loop.stop()
    except Exception as E:
      print(E)
    event.accept()
    
  
def set_all_margins(obj): #clean up GUI appearance: make the margins small and hide frames
  if isinstance(obj, QLayout):
    obj.setContentsMargins(1, 1, 1, 1)
    obj.setSpacing(1)
    for i in range(obj.count()):
      item = obj.itemAt(i)
      if item.widget():
        set_all_margins(item.widget())
      elif item.layout():
        set_all_margins(item.layout())
  elif hasattr(obj, 'layout') and callable(obj.layout):
    layout = obj.layout()
    if layout:
      set_all_margins(layout)
  if isinstance(obj, QFrame):
    obj.setFrameShape(QFrame.Shape.NoFrame)

# Main app entry
if __name__ == "__main__":
  sys._excepthook = sys.excepthook 
  def exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    sys._excepthook(exctype, value, traceback) 
    sys.exit(1) 
  sys.excepthook = exception_hook 

  app = QApplication(sys.argv)
  app.setApplicationName("BigGUI")
  loop = QEventLoop(app)
  asyncio.set_event_loop(loop)
  window = BigGUI(loop)
  window.show()
  with loop:
    loop.run_forever()
  sys.exit()
  # sys.exit(app.exec())




# if __name__ == "__main__":
#   import sys
#   app = QtWidgets.QApplication(sys.argv)
#   MainWindow = QtWidgets.QMainWindow()
#   ui = Ui_MainWindow()
#   ui.setupUi(MainWindow)
#   MainWindow.show()
#   sys.exit(app.exec())