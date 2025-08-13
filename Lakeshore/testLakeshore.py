import serial
from serial.tools import list_ports
import time

sn = 'AB0PEW5NA' #for testing only
device_list = list_ports.comports()
for dev in device_list:
  if dev.serial_number==sn:
      port=dev.device

TEST_COMMAND = b'*IDN?\r\n' 
# ENQUIRE_COMMAND = b'\x05'

def test_connection():
    try:
        with serial.Serial(port,9600, timeout=0.2, bytesize=7, parity="O") as ser:
            print(f"Connected to {port} at {9600} baud.")

            # Flush buffers
            ser.reset_input_buffer()
            ser.reset_output_buffer()

            print(f"Sending command: {TEST_COMMAND}")
            ser.write(TEST_COMMAND)

            time.sleep(0.2)  # Give device time to respond

            response = ser.read_all()
            print(f"Response:{response.decode()}")
            # print(response)
            if "LSCI" not in response.decode():
                print("error")
                return
            # import ipdb; ipdb.set_trace()
            

    except ZeroDivisionError as E:
        print(E)

def test_connections():
    lakeshores = {}
    for dev in device_list:
        try:
            with serial.Serial(dev.device, 9600, timeout=0.2, bytesize=7, parity="O") as ser:
                    
                print(f"Connected to {dev.device} at {9600} baud.")

                # Flush buffers
                ser.reset_input_buffer()
                ser.reset_output_buffer()

                print(f"Sending command: {TEST_COMMAND}")
                ser.write(TEST_COMMAND)

                time.sleep(0.2)  # Give device time to respond

                response = ser.read_all()
                print(f"Response:{response.decode()}")
                # print(response)
                if "LSCI" not in response.decode():
                    print("error")
                else:
                    params = {}
                    import ipdb; ipdb.set_trace()
                    minmax = Write(ser,b"MNMX?\r\n")
                    params["min"] = minmax.split()[0]
                    lakeshores[dev.device]=params
        except:
            pass
    return lakeshores

def Write(ser:serial.Serial, command:bytes):
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    print(f"Sending command: {command}")
    ser.write(command)

    time.sleep(0.2)  # Give device time to respond

    response = ser.read_all()
    print(f"Response:{response.decode()}")
    return response.decode()


test_connection()
lakeshores = test_connections()