import sys
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QApplication, QMainWindow, QLayout
from ui_BigGUI import Ui_MainWindow
from BigSkyController.HugeSkyController import BigSkyHub
from PenningTrapISEG import Penning_Trap_Beam_Line
from TDC.TDC_DAQGUI import TDC_GUI



class BigGUI(QMainWindow):
  ### This is intended to consolidate the various NEPTUNE interfaces in one place. 
  ### Grant Mondeel | gmondeel@mit.edu | 07/25/2025
  def __init__(self):
    super().__init__() #super

    # Create and set up the UI
    self.ui = Ui_MainWindow()
    self.ui.setupUi(self)

    self.loadGUIs() #Load up the other GUIs, like the ablation control and TDC
    self.connect()  #Make the buttons do things

    set_all_margins(self)


  def loadGUIs(self):
    self.TDC_GUI = TDC_GUI()
    self.ui.frameTDC.layout().addWidget(self.TDC_GUI)

    self.AblationGUI = BigSkyHub()
    self.ui.frameAblation.layout().addWidget(self.AblationGUI)



  def connect(self):
    ### Connects all of the interactive elements of the GUI to their respective functions
    # OPO Buttons
    # self.ui.
    pass

  def on_button_clicked(self):
    text = self.ui.lineEdit.text()
    self.ui.label.setText(f"Hello, {text}!")

def set_all_margins(obj):
    if isinstance(obj, QLayout):
        obj.setContentsMargins(1, 1, 1, 1)
        obj.setSpacing(1)
        for i in range(obj.count()):
            item = obj.itemAt(i)
            if item.widget():
                set_all_margins(item.widget())
                print('a')
            elif item.layout():
                set_all_margins(item.layout())
                print('b')
    elif hasattr(obj, 'layout') and callable(obj.layout):
        layout = obj.layout()
        if layout:
            set_all_margins(layout)
            print('c')
    else:
       print('nope')


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