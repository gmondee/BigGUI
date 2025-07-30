import serial

ser = serial.Serial('COM7', baudrate=19200, timeout=.25, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)

cmd = "*IDN?\r\n"
ser.write(cmd.encode('utf-8'))

response = ser.readline().decode('utf-8').strip()
print("Response:", repr(response))

ser.close()