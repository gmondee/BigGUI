import socket
import time

HOST = "192.168.1.102"  # 8742のIP
PORT = 23

IAC  = bytes([255])
DO   = bytes([253])
WILL = bytes([251])

# Telnet options
ECHO = bytes([1])
SUPPRESS_GO_AHEAD = bytes([3])

with socket.create_connection((HOST, PORT), timeout=2) as s:
    s.settimeout(2)

    # NewportからのTelnet negotiationを読む
    greeting = s.recv(1024)
    print("greeting raw:", repr(greeting))
    print("greeting hex:", greeting.hex())

    # WILL ECHO / WILL SUPPRESS-GO-AHEAD に対して DO で返す
    s.sendall(IAC + DO + ECHO + IAC + DO + SUPPRESS_GO_AHEAD)

    # コマンド送信
    s.sendall(b"1MV+\r\n")
    time.sleep(5)
    s.sendall(b"1ST\r\n")
    s.sendall(b"1TP?\r\n")

    reply = s.recv(1024)
    print("reply raw:", repr(reply))
    print("reply text:", reply.decode("ascii", errors="replace"))