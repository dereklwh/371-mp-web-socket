# Requirements:
# Respond to requests with following responses:

# Code	Message
# 200	OK
# 304	Not Modified
# 403	Forbidden
# 404	Not Found
# 505	HTTP Version Not Supported

from socket import *

HOST = '127.0.0.1' # Loopback address (localhost)
PORT = 12000

# Socket creation
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind((HOST, PORT))
serverSocket.listen(5)

print ('The server is ready to receive')

while True:
    # Server waits on client connections
    clientSocket, clientAddr = serverSocket.accept()

    # Get client request
    clientRequest =clientSocket.recv(1024).decode()
    print(clientRequest)

    # Send HTTP response
    serverResponse = 'HTTP/1.1 200 OK\n\nHello World'
    print(serverResponse)
    clientSocket.sendall(serverResponse.encode())
    clientSocket.close()

# Close server socket
serverSocket.close()

