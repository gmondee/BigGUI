# -*- coding: utf-8 -*-
"""
Created on Thu Jun 23 15:17:18 2022

@author: Scott Moroch
"""

import sys
import PyQt6
import os
from time import sleep
from PyQt6 import QtCore, QtGui, QtWidgets, uic, QtTest
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog, QApplication, QFileDialog
from .isegHV import isegHV
from .ui_trap_beamline_gui import Ui_Form
import pandas as pd
import numpy as np
import logging
from datetime import date, datetime
import json


ip = '169.254.55.226'
hv = isegHV(ip)
# qtCreatorFile = os.path.join(os.path.dirname(__file__),"trap_beamline_gui.ui") # Enter file here.

Ui_MainWindow = Ui_Form#uic.loadUiType(qtCreatorFile)

from PyQt6.QtCore import QObject, QThread, pyqtSignal

global state
state = True

#default directory for saving the beamtune files
default_dir = "C:\\Users\\User\\Documents\\Penning Trap ISEG"

# Step 1: Create a worker class
class VoltageRead(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(list)

    #Read voltages
    def readAllVoltages(self,channelList):
        command = ""
        for i in range(0,len(channelList)):
            channel=channelList[i]
            command+="outputMeasurementTerminalVoltage.u" + str(channel) + " "

        while state==True:

            #initialize empty lists
            values = []
            voltages = []
            values = hv.readBatchCommand(command)

            #this list will be filled with output from the power supply
            values = values[0:len(values)-1]

            for i in range(0,len(values)):
                #loop through list and extract the voltage (second to last value in each element)
                val = float(values[i].split(' ')[-2])

                #truncate each voltage after 1 decimal place
                val2 = float(f'{val:.2f}')

                #add voltage to list of voltages
                voltages.append(val2)

            #Send the completed list of voltages to the main class
            self.progress.emit(voltages)
          #  print(voltages)

            #500 msec wait
            QtTest.QTest.qWait(500)
        self.finished.emit()


#Main GUI class
class MyApp(QtWidgets.QWidget, Ui_MainWindow): #Change QtWidgets.QWidget to Qt.Widgets.QMainWindow if the form is a "Main Window"
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.setWindowTitle('ISEG')
        #self.setWindowIcon(QIcon('ScottIconic.png'))

        #Initialize the power supply by reading in, setting and applying voltages from "beamline_iseg.csv"
        self.initializeISEG()

        global state
        state = True

        #Initialize line edits the hard way
        self.volt0.valueChanged.connect(lambda: self.setFromGUI('Accelerator'))
        self.volt1.valueChanged.connect(lambda: self.setFromGUI('Quadrupole Lens Front'))
        self.volt2.valueChanged.connect(lambda: self.setFromGUI('Quadrupole Front Left'))
        self.volt3.valueChanged.connect(lambda: self.setFromGUI('Quadrupole Front Right'))
        self.volt4.valueChanged.connect(lambda: self.setFromGUI('Quadrupole Lens Left'))
        self.volt5.valueChanged.connect(lambda: self.setFromGUI('Quadrupole Back Right'))
        self.volt6.valueChanged.connect(lambda: self.setFromGUI('Quadrupole Back Left'))
        self.volt7.valueChanged.connect(lambda: self.setFromGUI('Lens Bottom'))
        self.volt8.valueChanged.connect(lambda: self.setFromGUI('Lens Right'))
        self.volt9.valueChanged.connect(lambda: self.setFromGUI('Lens Upper'))
        self.volt10.valueChanged.connect(lambda: self.setFromGUI('Lens Left'))
        self.volt11.valueChanged.connect(lambda: self.setFromGUI('MagneTOF'))

        #Initialize on/off buttons
        self.power0.clicked.connect(lambda: self.channelOn('Accelerator'))
        self.power1.clicked.connect(lambda: self.channelOn('Quadrupole Lens Front'))
        self.power2.clicked.connect(lambda: self.channelOn('Quadrupole Front Left'))
        self.power3.clicked.connect(lambda: self.channelOn('Quadrupole Front Right'))
        self.power4.clicked.connect(lambda: self.channelOn('Quadrupole Lens Left'))
        self.power5.clicked.connect(lambda: self.channelOn('Quadrupole Back Right'))
        self.power6.clicked.connect(lambda: self.channelOn('Quadrupole Back Left'))
        self.power7.clicked.connect(lambda: self.channelOn('Lens Bottom'))
        self.power8.clicked.connect(lambda: self.channelOn('Lens Right'))
        self.power9.clicked.connect(lambda: self.channelOn('Lens Upper'))
        self.power10.clicked.connect(lambda: self.channelOn('Lens Left'))
        self.power11.clicked.connect(lambda: self.channelOn('MagneTOF'))



        #Initialize ramp rate boxes
        #self.ramp0.returnPressed.connect(lambda: self.setRiseRate(0))
        #self.ramp1.returnPressed.connect(lambda: self.setRiseRate(1))
        #self.ramp2.returnPressed.connect(lambda: self.setRiseRate(2))
        #self.ramp3.returnPressed.connect(lambda: self.setRiseRate(3))
        #self.ramp4.returnPressed.connect(lambda: self.setRiseRate(4))

    #    self.automateButton.clicked.connect(self.automaticTuning)

       # self.voltageStep.clicked.connect(self.setStepSize)



     #   self.updateReads.clicked.connect(lambda: self.readAll())

        #Initialize file import features
  
       # self.importFileButton.clicked.connect(self.browsefiles)
        
            
      #  self.updateFromFile.clicked.connect(self.applyfromFile())

        #Initialize file export
        #self.saveToFile.clicked.connect(lambda: self.saveToCSV())
       # self.saveToFile.clicked.connect(self.browseSave)

        #Initialize Buttons to apply voltages and set all channels to zero
        # self.toZero.clicked.connect(lambda: self.setToZero)

       # self.readAll()
    def browsefiles(self):
        fname,_=QFileDialog.getOpenFileName(self,'Open File',default_dir)
        if fname:
            self.fileInput.setText(os.path.basename(fname))
            self.setFromFile(fname)
    def browseSave(self):
        if self.fileInput.text().strip():
            fname='/'+self.fileInput.text()+'.csv'
        else:
            today=date.today().strftime("%d-%m-%Y")
            hour=datetime.now().strftime("%H-%M-%S")
            fname = '/' + today+'-'+hour + '.csv'
        address=QFileDialog.getSaveFileName(self,'Save File',default_dir+fname,"Beamtune Files (*.CSV)")
        file = address[0]
        if file:
            self.df.to_csv(file, sep=',',index=False)
        
    #Import a File and save all of the data to a set of lists
    def importFile(self,fileName):
        #import a Json file "fileName"
        file = open(fileName, 'r')
        self.dic = json.load(file)

    #Set the voltage for a single channel
    def setFromGUI(self,name):

        num = self.dic["DC"][name]["GUI Number"]
        inputSpinBox = getattr(self,'volt{}'.format(num))

        #Change set voltage in list
        self.dic["DC"][name]["Set Voltage"]=inputSpinBox.value()

        #Set voltage on power supply
        self.setVoltages(name)

    def setVoltages(self,name):
        channel = self.dic["DC"][name]["Channel"]
        setV = self.dic["DC"][name]["Set Voltage"]
        num = self.dic["DC"][name]["GUI Number"]
        setOut = getattr(self,'set{}'.format(num))

        #Set voltage based on channel number and voltage from spin box
        hv.setSingleVoltage(channel, setV)

        #Read the current set voltage from the power supply
        setOut.setText(hv.readSetVoltage(channel)[0:-4] + ' V')

        #Update the Json file
        self.updateBuffer()

    def channelOn(self,name):
        channelStatus = self.dic["DC"][name]["State"]
        num = self.dic["DC"][name]["GUI Number"]
        button = getattr(self,'power{}'.format(num))
        channel = self.dic["DC"][name]["Channel"]

        if channelStatus == "Off":
            self.dic["DC"][name]["State"] = "On"
            button.setStyleSheet("background-color : rgb(0,170,0)")
            button.setText('On')
            hv.turnOn(channel)
            self.updateBuffer()

        elif channelStatus == "On":
            self.dic["DC"][name]["State"] = "Off"
            button.setStyleSheet("background-color : rgb(170,0,0)")
            button.setText('Off')
            hv.turnOff(channel)
            self.updateBuffer()

    #Read the Actual Voltage on an ISEG channel
    def readVoltages(self,name):
        num = self.dic["DC"][name]["GUI Number"]
        readOut = getattr(self,'read{}'.format(num))
        channel = self.dic["DC"][name]["Channel"]
        readOut.setText(hv.readActualVoltage(channel)[0:-4]+' V')

    def updateBuffer(self):
        with open('beamline.json', "w") as outfile:
            json.dump(self.dic, outfile, indent=4)

    def readAll(self):
        channels = []
        values = self.dic["DC"]
        for i in values:
            channels.append(self.dic["DC"][i]["Channel"])
        # Step 2: Create a QThread object
        self.thread = QThread()

        # Step 3: Create a worker object with VoltageRead function
        self.worker = VoltageRead()
        # Step 4: Move worker to the thread
        self.worker.moveToThread(self.thread)
        # Step 5: Connect signals and slots
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.worker.progress.connect(self.updateVoltageLabels)
        self.thread.started.connect(lambda: self.worker.readAllVoltages(channels))

        # Step 6: Start the thread
        self.thread.start()


    def updateVoltageLabels(self,voltages):
        for i in range(0,len(voltages)):
            readOut = getattr(self,'read{}'.format(i))
            readOut.setText(str(voltages[i]) +' V')

    def setStepSize(self):
        if self.radio_1V.isChecked():
            set = 1
        elif self.radio_5V.isChecked():
            set = 5
        elif self.radio_10V.isChecked():
            set = 10
        elif self.radio_50V.isChecked():
            set = 50
        elif self.radio_100V.isChecked():
            set = 100
        elif self.radio_250V.isChecked():
            set = 250
        elif self.radio_500V.isChecked():
            set = 500
        elif self.radio_1000V.isChecked():
            set = 1000
        for i in range(0,len(self.ls)):
            inputSpinBox = getattr(self,'volt{}'.format(i))
            inputSpinBox.setSingleStep(set)
 

#*****************The following are for setting voltages to all channels from an input file***********************

    #Initialize the ISEG power supply
    def initializeISEG(self):
        self.setFromFile(os.path.join(os.path.dirname(__file__),"beamline.json"))
       # self.readAllRampRates()

    #Set voltages from file input
    def setFromFile(self,inFile):
        #Import JSON file with electrode name, channel number, current set voltage, and status (on/off)
        self.importFile(inFile)

      #  self.selectChannelsOn() #This turns on channels when the GUI opens

        #Set Voltages from File
        self.setVoltagesfromFile()

        #Read the set voltages on the ISEG
        self.readSetVoltages()

        #Set the voltage to the spin box input
        self.setSpinBoxValue()

    #Set all of the voltages from an input file
    def setVoltagesfromFile(self):
        values = self.dic['DC']
        command = ''
        for i in values:
            command += "outputVoltage.u" + str(values[i]['Channel']) + " F " + str(values[i]['Set Voltage']) + " "
                     #Set voltage based on channel number and voltage from inputLabel
        hv.setBatchCommand(command)

    def setSpinBoxValue(self):
        values = self.dic['DC']
        for i in values:
            inputSpinBox = getattr(self,'volt{}'.format(values[i]["GUI Number"]))
            inputSpinBox.setValue(values[i]["Set Voltage"])

    def allChannelsOff(self):
        global state
        state = False
        command = ""
        values = self.dic['DC']
        for i in values:
            command += "outputSwitch.u" + str(values[i]["Channel"]) + " i 0 "
        hv.setBatchCommand(command)

    def selectChannelsOn(self):
        values = self.dic["DC"]
        command = ""
        for i in values:
            if values[i]["State"] == "On":
                button = getattr(self,'power{}'.format(i))
                button.setStyleSheet("background-color : rgb(0,170,0)")
                button.setText('On')
                command += "outputVoltage.u" + str(values[i]['Channel']) + " F " + str(values[i]['Set Voltage']) + " "
        hv.setBatchCommand(command)


    def readSetVoltages(self):
        values = self.dic["DC"]
        for i in values:
            setOut = getattr(self,'set{}'.format(values[i]["GUI Number"]))
            channel = values[i]["Channel"]
            #Read the current set voltage from the power supply
            setOut.setText(hv.readSetVoltage(channel)[0:-4] + ' V')

    #Set all Voltages to Zero
    def setToZero(self):
        values = self.dic["DC"]
        for i in values:
            values[i]["Set Voltage"]=0
        for i in range(0,len(values)):
            self.setVoltages(list(self.dic['DC'].keys())[i])

#**************This Section is for reading and adjusting the ramp rate***************

    #Read ramp rates of different power supplies
    def readAllRampRates(self):
        num = 0
        for i in range(0,2):
            ramp = getattr(self,'rampRead{}'.format(i))
            rate =float(hv.readRiseRate(num))
            rate = float(f'{rate:.1f}')
            ramp.setText(str(rate) + ' V/s')
            num+=100

    def setRiseRate(self,module):
        rate = getattr(self,'ramp{}'.format(module))
        inputRate = rate.text()
        module = module*100
        hv.setRiseRate(module, inputRate)
        self.readAllRampRates()



if __name__ == "__main__":
  app = QtWidgets.QApplication(sys.argv)
  window = MyApp()
  window.show()
  window.resize(0, 0)
  window.readAll()
  app.aboutToQuit.connect(MyApp.allChannelsOff)
  sys.exit(app.exec_())
