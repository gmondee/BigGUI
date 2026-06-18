"""Quantum Composer connection diagnostic — self-contained (pyserial only).

The old QC stopped connecting after a cable swap (its USB serial number changed, and the
baud rate may no longer match what BigGUI hard-codes). This script makes NO assumptions:
it lists every serial port, then probes each port across all the QC's supported baud rates,
sends ``*IDN?``, and prints whatever comes back — flagging anything that looks like a
Quantum Composer. Use it to rediscover the right (port, baud) and the unit's identity.

Run:  python qc_connection_test.py            # scan everything
      python qc_connection_test.py --port COM5    # only that port
      python qc_connection_test.py --port /dev/cu.usbserial-XXXX --baud 19200

Handles two real quirks: at the wrong baud the unit returns nothing (we bail fast), and the
first command after opening can return a stale "?1" / an RS-232 echo (we retry and read a
few lines).
"""

import argparse
import sys

try:
  import serial
  from serial.tools import list_ports
except ImportError:
  sys.exit("pyserial is required:  pip install pyserial")

# QC supported rates (manual): 4800/9600/19200/38400/57600/115200. The new 9550-24 runs at
# 115200; the old 8-channel historically used 19200. Order is just a speed hint.
BAUDS = (115200, 38400, 19200, 57600, 9600, 4800)

# Substrings that mark a reply as a Quantum Composer (IDN looks like "QC,9518,...").
QC_MARKERS = ("QC", "QUANTUM", "9550", "9520", "9518", "9512", "9510", "8550", "955")


def list_all_ports():
  ports = list(list_ports.comports())
  print(f"=== serial ports ({len(ports)}) ===")
  if not ports:
    print("  (none found)")
  for p in ports:
    vidpid = f"{p.vid:04x}:{p.pid:04x}" if p.vid is not None else "----:----"
    print(f"  {p.device:34s} {vidpid}  sn={p.serial_number}  {p.manufacturer} {p.product}")
  return ports


def probe(port, baud, timeout=0.4):
  """Open port@baud, send *IDN?, return (list_of_response_lines, looks_like_qc)."""
  lines = []
  try:
    with serial.Serial(port, baud, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                       stopbits=serial.STOPBITS_ONE, timeout=timeout, exclusive=True) as ser:
      ser.reset_input_buffer()
      ser.reset_output_buffer()
      for attempt in range(3):
        ser.write(b"*IDN?\r\n")
        got_any = False
        for _ in range(3):  # read past a stale "?1" / echoed command line
          raw = ser.readline()
          if not raw:
            break
          line = raw.decode("ascii", errors="replace").strip()
          got_any = True
          if line:
            lines.append(line)
            if any(m in line.upper() for m in QC_MARKERS):
              return lines, True
        if not got_any and attempt == 0:
          break  # silence at the first attempt => wrong baud, move on
  except (OSError, serial.SerialException) as exc:
    return [f"<error: {exc}>"], False
  return lines, False


def main(argv=None):
  ap = argparse.ArgumentParser(description="Scan serial ports/baud rates for a Quantum Composer")
  ap.add_argument("--port", help="probe only this port (default: all)")
  ap.add_argument("--baud", type=int, help="probe only this baud (default: all supported)")
  ap.add_argument("--timeout", type=float, default=0.4, help="per-read timeout in seconds")
  args = ap.parse_args(argv)

  ports = list_all_ports()
  candidates = [args.port] if args.port else [p.device for p in ports]
  bauds = (args.baud,) if args.baud else BAUDS

  print("\n=== probing *IDN? ===")
  found = []
  for dev in candidates:
    for baud in bauds:
      replies, is_qc = probe(dev, baud, timeout=args.timeout)
      if replies:
        tag = "  <-- QUANTUM COMPOSER" if is_qc else ""
        print(f"  {dev} @ {baud}: {replies}{tag}")
      if is_qc:
        found.append((dev, baud, replies[-1]))
        break  # got it on this port; no need to try slower bauds

  print("\n=== result ===")
  if found:
    for dev, baud, idn in found:
      print(f"  FOUND: port={dev}  baud={baud}  IDN={idn!r}")
  else:
    print("  No Quantum Composer responded. Check: powered on & finished its boot sequence,")
    print("  the right USB cable/driver, nothing else holding the port, and the data cable.")
  return 0 if found else 1


if __name__ == "__main__":
  sys.exit(main())