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

# helper function to get HTTP request line
def get_request_line(request):
    lines = request.split('\r\n')
    if len(lines) > 0:
        return lines[0]
    return ''

# helper function to get HTTP version from request line
def get_html_version(request):
    request_line = get_request_line(request)
    parts = request_line.split(' ')
    if len(parts) == 3:
        return parts[2]
    return ''

# Socket creation (TCP)
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind((HOST, PORT))
serverSocket.listen(5)

print ('The server is ready to receive')

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
    # To test, use curl the following command: 
    # curl --http1.0 http://127.0.0.1:12000/
    if html_version != 'HTTP/1.1':
        serverResponse = 'HTTP/1.1 505 {}\n\n'.format(STATUS_TEXT[505])
        print(serverResponse)
        clientSocket.sendall(serverResponse.encode())
        clientSocket.close()
        continue
    else:
        # Send HTTP response
        serverResponse = 'HTTP/1.1 200 OK\n\nHello World'
        print(serverResponse)
        clientSocket.sendall(serverResponse.encode())
        clientSocket.close()

# Close server socket
serverSocket.close()

