from socket import *

client = socket(AF_INET, SOCK_DGRAM)
server_addr = ('127.0.0.1', 12000)

client.sendto(b'hello server', server_addr)
data, addr = client.recvfrom(2048)
print("Server replied:", data.decode())
