from socket import *

HOST = '127.0.0.1'
PORT = 12000
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind((HOST, PORT))

print('Server ready')

def parse_packet():
    pass

# server handles rwnd
while True:
    data, addr = serverSocket.recvfrom(2048)  # receive packet + client address
    sentence = data.decode()
    capitalized = sentence.upper().encode()
    serverSocket.sendto(capitalized, addr)
    print(f"Processed request from {addr}")
    print(f"data: {data}")

