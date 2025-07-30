import serial

ser = serial.Serial('COM7', baudrate=115200, timeout=1, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)

cmd = "*IDN?\r\n"
ser.write(cmd.encode('ascii'))

response = ser.readline().decode('ascii').strip()
print("Response:", repr(response))

# ser.close()