from isegHV import isegHV
import os
import sys
ip = '169.254.55.226'
hv = isegHV(ip)

print(hv.readSetVoltage(100))


