import sys
import requests
import json
import urllib
from functools import partial
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QApplication, QMainWindow, QLayout, QFrame
from ui_BigGUI import Ui_MainWindow
from BigSkyController.HugeSkyController import BigSkyHub
from PenningTrapISEG import Penning_Trap_Beam_Line
from TDC.TDC_DAQGUI import TDC_GUI



class BigGUI(QMainWindow):
  ### This is intended to consolidate the various NEPTUNE interfaces in one place. 
  ### Grant Mondeel | gmondeel@mit.edu | 07/25/2025
  def __init__(self):
    super().__init__() #super
    self.IP = 'http://192.168.1.53:7557'
    self.auth = ('QTuser','QT_53')
    # Create and set up the UI
    self.ui = Ui_MainWindow()
    self.ui.setupUi(self)

    self.loadGUIs() #Load up the other GUIs, like the ablation control and TDC
    self.connect()  #Make the buttons do things

    set_all_margins(self)


  def loadGUIs(self):
    self.TDCGUI = TDC_GUI()
    self.ui.frameTDC.layout().addWidget(self.TDCGUI)

    self.AblationGUI = BigSkyHub()
    self.ui.frameAblation.layout().addWidget(self.AblationGUI)

    self.BeamlineGUI = Penning_Trap_Beam_Line() #will be shown when the button is pressed

    #self.QuantumComposerGUI = blah #eventually need to make this

  def connect(self):
    ### Connects all of the interactive elements of the GUI to their respective functions
    # OPO Buttons
    self.ui.pushButtonToggleOPO.clicked.connect(partial(self.sendToOPO(self.dict_enable_OPO)))
    self.ui.pushButtonOPOSet.clicked.connect(partial(self.sendToOPO(self.dict_set_OPO_wavelength())))
    self.ui.pushButtonStartScan.clicked.connect(self.startWavelengthScan)
    self.ui.pushButtonStopScan.clicked.connect(self.stopWavelengthScan)
    self.ui.pushButtonOpenOPOGUI.clicked.connect(self.openOPOGUI)
    self.ui.pushButtonStartLaser.clicked.connect(self.handleStartOPO) #cant think of any checks
    self.ui.pushButtonStopLaser.clicked.connect(self.handleStopOPO) #should also stop the scan



  ### Functions for OPO communication
  def getOPOStatus(self):
    pass
  def sendToOPO(self, payload):
    encoded = urllib.parse.quote(json.dumps(payload,separators=(',', ':')))
    url = f"{self.IP}/send?{encoded}"
    #todo: what if this fails
    response = requests.get(url, auth=self.auth)
    if "failure" in response:
      pass


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
  app = QApplication(sys.argv)
  window = BigGUI()
  window.show()
  sys.exit(app.exec())



# if __name__ == "__main__":
#   import sys
#   app = QtWidgets.QApplication(sys.argv)
#   MainWindow = QtWidgets.QMainWindow()
#   ui = Ui_MainWindow()
#   ui.setupUi(MainWindow)
#   MainWindow.show()
#   sys.exit(app.exec())