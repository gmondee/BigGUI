from Exscript.protocols import Telnet

host = '192.168.103.103'
port = 23
password = 'VR'+'E63BB7'
netmask = '255.255.248.0'
idhcp = '0'  # 0 = static, 1 = DHCP


# Start telnet session
conn = Telnet()
conn.connect(host, port=port)
conn.set_prompt(r'\$')

def write(command):
  full_command = f"${command}\r\n"  # Add $ prefix and CRLF
  print(f"Sending: {full_command.strip()}")
  conn.execute(full_command)
  print(conn.response)

write('login '+password)



# # Close connection
# conn.close()
