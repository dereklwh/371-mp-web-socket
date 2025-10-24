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

STATUS_TEXT = {
    200: "OK",
    304: "Not Modified",
    403: "Forbidden",
    404: "Not Found",
    505: "HTTP Version Not Supported"
}

# Socket creation
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind((HOST, PORT))
serverSocket.listen(5)

print ('The server is ready to receive')

# helper function to get HTTP request line
def get_request_line(request):
    lines = request.split('\r\n')
    if len(lines) > 0:
        return lines[0]
    return ''

def get_html_version(request):
    request_line = get_request_line(request)
    parts = request_line.split(' ')
    if len(parts) == 3:
        return parts[2]
    return ''

# assume we are using http version 1.1
while True:
    # Server waits on client connections
    clientSocket, clientAddr = serverSocket.accept()

    # Get client request
    clientRequest =clientSocket.recv(1024).decode()
    print(clientRequest)
    print(get_request_line(clientRequest))
    html_version = get_html_version(clientRequest)

    # HTTP 505 response
    if html_version != 'HTTP/1.0':
        serverResponse = 'HTTP/1.1 505 HTTP Version Not Supported\n\n505 HTTP Version Not Supported'
        print(serverResponse)
        clientSocket.sendall(serverResponse.encode())
        clientSocket.close()
        continue

    # Send HTTP response
    serverResponse = 'HTTP/1.1 200 OK\n\nHello World'
    print(serverResponse)
    clientSocket.sendall(serverResponse.encode())
    clientSocket.close()

# Close server socket
serverSocket.close()

