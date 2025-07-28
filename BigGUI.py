import sys
import requests
import json
import urllib
import asyncio
from qasync import QEventLoop, asyncSlot
from functools import partial
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QApplication, QMainWindow, QLayout, QFrame
from PyQt6.QtCore import QTimer
from ui_BigGUI import Ui_MainWindow
from BigSkyController.HugeSkyController import BigSkyHub
from PenningTrapISEG.Penning_Trap_Beam_Line import MyApp
from TDC.TDC_DAQGUI import TDC_GUI



class BigGUI(QMainWindow):
  ### This is intended to consolidate the various NEPTUNE interfaces in one place. 
  ### Grant Mondeel | gmondeel@mit.edu | 07/25/2025
  def __init__(self):
    super().__init__() #super
    self.IP = 'http://192.168.1.53:7557'
    self.auth = ('QTuser','QT_53')
    self.scanWavelength=None
    self.DAQTimer = QTimer(self, singleShot=True)
    self.DAQTimer.timeout.connect(self.stopDAQ)
    self.scanParams={}
    self.frequency = 10 # 10 Hz repetition rate
    self.scanSleepTask = None #this
    # Create and set up the UI
    self.ui = Ui_MainWindow()
    self.ui.setupUi(self)

    self.loadGUIs() #Load up the other GUIs, like the ablation control and TDC
    self.connect()  #Make the buttons do things

    set_all_margins(self)


  def loadGUIs(self):
    try:
      self.TDCGUI = TDC_GUI()
      self.ui.frameTDC.layout().addWidget(self.TDCGUI)
    except Exception as E:
      print(f"\nFailed to load TDCGUI: {E}")

    try:
      self.AblationGUI = BigSkyHub()
      self.ui.frameAblation.layout().addWidget(self.AblationGUI)
      self.AblationGUI.table_widget.homeTab.buttons[-1].click()
      self.AblationGUI.table_widget.homeTab.labelLineEdits[-1].setText('NEPTUNE Ablation')
      self.AblationGUI.table_widget.homeTab.saveLabels()
      ablation_tab_count = self.AblationGUI.table_widget.tabs.count()
      ablationTabIndex = [self.AblationGUI.table_widget.tabs.tabText(i) for i in range(ablation_tab_count) if "Ablation" in self.AblationGUI.table_widget.tabs.tabText(i)]
      self.ablationTab = self.AblationGUI.table_widget.tabs.widget(ablationTabIndex[0])
    except Exception as E:
      print(f"\nFailed to load ablation GUI: {E}")

    
    # self.BeamlineGUI = MyApp() #will be shown when the button is pressed

    #self.QuantumComposerGUI = blah #eventually need to make this

  def connect(self):
    ### Connects all of the interactive elements of the GUI to their respective functions
    # OPO Buttons
    self.ui.pushButtonToggleOPO.clicked.connect(partial(self.sendToOPO,self.dict_enable_OPO))
    self.ui.pushButtonOPOSet.clicked.connect(partial(self.sendToOPO,self.dict_set_OPO_wavelength))
    self.ui.pushButtonStartScan.clicked.connect(self.startWavelengthScan)
    self.ui.pushButtonStopScan.clicked.connect(self.stopWavelengthScan)
    # self.ui.pushButtonOpenOPOGUI.clicked.connect(self.openOPOGUI)
    self.ui.pushButtonStartLaser.clicked.connect(self.handleStartOPO) #cant think of any checks
    self.ui.pushButtonStopLaser.clicked.connect(self.handleStopOPO) #should also stop the scan

  def handleStartOPO(self):
    ##any checks go here
    self.sendToOPO(self.dict_run_laser())

  def handleStopOPO(self):
    self.stopWavelengthScan()
    self.sendToOPO(self.dict_stop_laser())

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
    scanETAmin=(1/self.frequency*self.scanParams["pulsesPerStep"]+1.5)*(self.scanParams["startWL"]-self.scanParams["endWL"])/self.scanParams["stepSize"]/60
    self.ui.labelScanStatus.setText("Scan Status: ON")
    print(f'Starting scan. ETA:{scanETAmin:.2f} minutes.\nScan parameters:{self.scanParams}')

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
      await self.sleep_task(waitTime)
    except asyncio.CancelledError:
      print("Main function interrupted during sleep.")
      #TODO: handle canellation
      return
    #await asyncio.sleep(waitTime)## Wait for the measurement to finish
    self.TDCGUI.scanToggler.click()
    
    if self.scanParams["measureAblationOff"]:
      self.ablationTab.stopButton.click()
      self.TDCGUI.scanToggler.click()
      try:
        await self.sleep_task(waitTime)
      except asyncio.CancelledError:
        print("Main function interrupted during sleep.")
        return
      #await asyncio.sleep(waitTime)## Wait for the measurement to finish
      self.TDCGUI.scanToggler.click()
      self.ablationTab.lampActivationButton.click() #turn ablation back on for the next measurement
    
    if 2*self.scanParams["stepSize"]+self.scanWavelength > self.scanParams["endWL"]:
      print("\nScan finished.\n")
      pass #scan over
    else:
      self.scanWavelength += self.scanParams["stepSize"]
      self.scanNext()

  def stopWavelengthScan(self):
    #self.scanTimer.stop()
    if self.sleep_task and not self.sleep_task.done():
      self.sleep_task.cancel()
      print('Stopped scan')
    self.ui.labelScanStatus.setText("Scan Status: OFF")
    print('Stopping scan (doesnt do anything)')

    ### Re-enable scan GUI elements

  @asyncSlot()
  async def sleep_task(self, time_s):
      """Sleep that can be cancelled externally."""
      try:
        self.sleep_task = asyncio.create_task(asyncio.sleep(time_s))
        await self.sleep_task
      except asyncio.CancelledError:
        print("Sleep cancelled!")
        raise
      finally:
        self.sleep_task = None

  @asyncSlot()
  async def startSleepForScan(self):
    if self.scanSleepTask and not self.scanSleepTask.done():
      print("Already sleeping...")
      return
    self.scanSleepTask = asyncio.create_task(self.sleep_task())

  def cancelSleepForScan(self):
    if self.scanSleepTask and not self.scanSleepTask.done():
        self.scanSleepTask.cancel()

  def stopDAQ(self):
    print("add some stuff to stop the daq")
  ### Functions for OPO communication
  def getOPOStatus(self):
    pass
  def sendToOPO(self, payload):
    encoded = urllib.parse.quote(json.dumps(payload,separators=(',', ':')))
    url = f"{self.IP}/send?{encoded}"
    #todo: what if this fails
    response = requests.get(url, auth=self.auth)
    if "failure" in response:
      print(f'\nFailed outgoing command {encoded}\nResponse:{response}')


  def dict_run_laser(self):
    return {"action":"control","code":{"device":"laser","values":{"laser-run": 1}}}

  def dict_stop_laser(self):
    return {"action":"control","code":{"device":"laser","values":{"laser-run": 0}}}

  def dict_set_OPO_wavelength(self): #in nm
    wavelengthnm = round(self.ui.doubleSpinBoxSetOPOWavelength.value(),2)
    return {"action":"control","code":{"device": "laser","values":{"forward-device":"opo","forward-protocol":"wavelength","forward-action":"control","wavelength": wavelengthnm}}}

  def dict_enable_OPO():
    return{"action":"control","code":{"device":"laser","values":{"forward-device":"harmonics","forward-protocol":"crystals","forward-action":"control","hu-status": 3.6}}}

  def dict_set_trigger_external_TP():
    return {"action":"control","code":{"device":"laser","values":{"trig-mode":2}}}
  
  def dict_set_trigger_internal():
    return {"action":"control","code":{"device":"laser","values":{"trig-mode":0}}}
  
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
  loop = QEventLoop(app)
  asyncio.set_event_loop(loop)
  window = BigGUI()
  window.show()
  with loop:
    loop.run_forever()
  # sys.exit(app.exec())




# if __name__ == "__main__":
#   import sys
#   app = QtWidgets.QApplication(sys.argv)
#   MainWindow = QtWidgets.QMainWindow()
#   ui = Ui_MainWindow()
#   ui.setupUi(MainWindow)
#   MainWindow.show()
#   sys.exit(app.exec())