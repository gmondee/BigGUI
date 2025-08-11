import serial
from serial.tools import list_ports
import time

pid = 8963
device_list = serial.tools.list_ports.comports()
for dev in device_list:
  if dev.pid==pid:
      port=dev.device

TEST_COMMAND = b'PR1\r\n' 
ENQUIRE_COMMAND = b'\x05'

def test_connection():
    try:
        with serial.Serial(port,19200, timeout=0.2) as ser:
            print(f"Connected to {port} at {19200} baud.")

            # Flush buffers
            ser.reset_input_buffer()
            ser.reset_output_buffer()

            print(f"Sending command: {TEST_COMMAND}")
            ser.write(TEST_COMMAND)

            time.sleep(0.2)  # Give device time to respond

            response = ser.read_all()
            print("Response:")
            print(response)
            if "\x06" not in response.decode():
                print("error")
                return
            ser.write(ENQUIRE_COMMAND)
            time.sleep(.3)
            response2 = ser.read_all()
            print("Response:", response2)
            # import ipdb; ipdb.set_trace()
            

    except ZeroDivisionError as E:
        print(E)

test_connection()