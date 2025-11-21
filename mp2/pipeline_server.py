from socket import *

serverPort = 12000
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverPort))

print('Server ready')

while True:
    data, addr = serverSocket.recvfrom(2048)  # receive packet + client address
    sentence = data.decode()
    capitalized = sentence.upper().encode()
    serverSocket.sendto(capitalized, addr)
    print(f"Processed request from {addr}")
    
