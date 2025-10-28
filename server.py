# Requirements:
# Respond to requests with following responses:

# Code	Message
# 200	OK
# 304	Not Modified
# 403	Forbidden
# 404	Not Found
# 505	HTTP Version Not Supported

from socket import *
import os
import datetime
from email.utils import parsedate_to_datetime # Allows parsing of HTTP timestamp

HOST = '127.0.0.1' # Loopback address (localhost)
PORT = 12000

STATUS_TEXT = {
    200: "OK",
    304: "Not Modified",
    403: "Forbidden",
    404: "Not Found",
    505: "HTTP Version Not Supported"
}

def get_headers(request):
    lines = request.split('\n')
    return lines

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

print (f'Listening on port {PORT}...')

# assume we are using http version 1.1
while True:
    # Server waits on client connections
    clientSocket, clientAddr = serverSocket.accept()

    # Get client request
    clientRequest = clientSocket.recv(1024).decode()
    print(clientRequest)
    print(get_request_line(clientRequest))
    html_version = get_html_version(clientRequest)

    headers = get_headers(clientRequest)

    # Splits the items in the first header line
    headerComponents = headers[0].split(' ')

    # Takes the path component of the header line
    path = headerComponents[1] if len(headerComponents) > 1 else '/'
    
    # Go through each header line except the first
    headerLines = {}
    for header in headers[1:]:
        if ': ' in header:
            key, value = header.split(': ', 1)
            headerLines[key.lower()] = value

    
    # Try to access server code
    if path.endswith('.py'):
        
        # Send HTTP response 403 Forbidden
        serverResponse = 'HTTP/1.1 403 Forbidden\n\n'

        print(serverResponse)
    
    # Open and display file test.html
    if path == '/test.html':
        filepath = '.' + path

        # Check last modified time of file
        file_ModifiedTime_Original = os.path.getmtime(filepath)
        file_ModifiedTime = datetime.datetime.fromtimestamp(
                            file_ModifiedTime_Original, 
                            tz = datetime.timezone.utc) # Allows for comparison against HTTP timestamp
        
        # print(file_ModifiedTime)

        if 'if-modified-since' in headerLines:
            
            # Extract HTTP timestamp from request
            http_fileTimestamp = parsedate_to_datetime(headerLines['if-modified-since'])

            # File has not been modified since date in request message
            if file_ModifiedTime <= http_fileTimestamp:
                
                # Send HTTP response 304 Not Modified
                serverResponse = 'HTTP/1.1 304 Not Modified\n\n'    
            
        else: 
            
            # Open and read contents of requested file
            fin = open(filepath)
            content = fin.read()
            fin.close()

            # Send HTTP response 200 OK
            serverResponse = 'HTTP/1.1 200 OK\n\n' + content

        print(serverResponse)
    
    # Try to access non existent file garbage.txt , 404 Not Found
    if path == '/garbage.txt':
        
        # Send HTTP response 404 Not Found
        serverResponse = 'HTTP/1.1 404 Not Found\n\n'

        print(serverResponse)
    
        clientSocket.sendall(serverResponse.encode())
        clientSocket.close()

    # HTTP 505 response
    # To test, use curl the following command: 
    # curl --http1.0 http://127.0.0.1:12000/
    if html_version != 'HTTP/1.1':
        serverResponse = 'HTTP/1.1 505 {}\n\n'.format(STATUS_TEXT[505])
        print(serverResponse)
        clientSocket.sendall(serverResponse.encode())
        clientSocket.close()
        continue

# Close server socket
serverSocket.close()

