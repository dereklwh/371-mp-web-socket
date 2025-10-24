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

print (f'Listening on port {PORT}...')

while True:
    # Server waits on client connections
    clientSocket, clientAddr = serverSocket.accept()

    # Get client request
    clientRequest = clientSocket.recv(1024).decode()
    #print(clientRequest)

    # Splits headers by line 
    headers = clientRequest.split('\n')

    # Splits the items in the first header line
    headerComponents = headers[0].split(' ')

    # Takes the path component of the header line
    path = headerComponents[1]
    
    # Open and display file
    if path == '/test.html':
        fin = open('test.html')
        content = fin.read()
        fin.close()

        # Send HTTP response 200 OK
        serverResponse = 'HTTP/1.1 200 OK\n\n' + content

        print(serverResponse)
    
    if path == '/garbage.txt':
        
        # Send HTTP response 404 Not Found
        serverResponse = 'HTTP/1.1 404 Not Found\n\n'

        print(serverResponse)

    clientSocket.sendall(serverResponse.encode())
    clientSocket.close()
    

# Close server socket
serverSocket.close()

