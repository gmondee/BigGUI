# -*- coding: utf-8 -*-
"""
Created on Tue Jun 14 12:29:50 2022

@author: Scott Moroch
"""

import os
import sys

class isegHV:
    
    #Initialize function
    def __init__(self, ip):
        self.ip = ip
    
    #General SNMP Walk Function 
    def walk(self, cmd):
        sts = os.popen("C:\\usr\\bin\\snmpwalk.exe -v 2c -m +WIENER-CRATE-MIB -c guru " + self.ip + " " + cmd)
        ret = sts.read().split('\n')
        return ret[0:-1]

    #General SNMP Get function
    def get(self, cmd):
       # sts = os.popen("C:\\usr\\bin\\snmpget.exe -v 2c -m +WIENER-CRATE-MIB -c public " + self.ip + " " + cmd)
        sts = os.popen("C:\\usr\\bin\\snmpget.exe -v 2c -m +WIENER-CRATE-MIB -c public " + self.ip + " " + cmd)
        ret = sts.read().split(' ')[-2]
        return ret
    
    #General SNMP Set Function
    def set(self, cmd):
        sts = os.popen("C:\\usr\\bin\\snmpset.exe -v 2c -m +WIENER-CRATE-MIB -c guru " + self.ip + " " + cmd)
        ret = sts.read().split(' ')[-2]
        return ret    
    
    #Set a voltage on a particular channel
    def setSingleVoltage(self, channel, voltage):
        com = "outputVoltage.u" + str(channel) + " F " +str(voltage)
        return self.set(com)
        
    #Turn on High Voltage output for a particular channel
    def turnOn(self, channel):
        com="outputSwitch.u" + str(channel) + " i 1"
        return self.set(com)
    
    #Turn off output for a channel
    def turnOff(self,channel):
        com="outputSwitch.u" + str(channel) + " i 0"
        return self.set(com)
    
    #Read a Set Voltage on a channel
    def readSetVoltage(self,channel):
        com = "outputVoltage.u" + str(channel)
        return self.get(com)
    
    #Read the actual voltage output of a channel
    def readActualVoltage(self,channel):
        com = "outputMeasurementTerminalVoltage.u" + str(channel)
        return self.get(com)
    
    #Read the rate of rise (V/s) for a channel
    def readRiseRate(self, channel):
        com="outputVoltageRiseRate.u" + str(channel)
        return self.get(com)
    
    #Change the rate of rise (V/s) for a channel. This will change it for the whole module
    def setRiseRate(self, channel,rate):
        com="outputVoltageRiseRate.u" + str(channel) + " F " + str(rate)
        return self.set(com)
    
    def setBatchCommand(self,cmd):
        return self.set(cmd)
    
    def readBatchCommand(self,cmd):
        sts = os.popen("C:\\usr\\bin\\snmpget.exe -v 2c -m +WIENER-CRATE-MIB -c public " + self.ip + " " + cmd)
        ret = sts.read().split('\n')
        return ret
    
    
  #  def voltageSweep(self, channel, v1, v2)
        