from socket import *
import os
import datetime
from email.utils import parsedate_to_datetime  # Allows parsing of HTTP timestamp

HOST = '127.0.0.1'
PORT = 12000

STATUS_TEXT = {
    200: "OK",
    304: "Not Modified",
    403: "Forbidden",
    404: "Not Found",
    505: "HTTP Version Not Supported"
}

# --- Helpers ---
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

# helper function to get HTTP method from request line
# use this to handle specific methods like GET, POST, etc.
# for this server, we only care about GET
def get_method(request):
    request_line = get_request_line(request)
    parts = request_line.split(' ')
    if len(parts) >= 1:
        return parts[0]
    return ''

def get_headers_dict(request):
    headers = get_headers(clientRequest)
    headerLines = {}
    for header in headers[1:]:
        if ': ' in header:
            key, value = header.split(': ', 1)
            headerLines[key.lower()] = value
    return headers

# --- Socket setup ---
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind((HOST, PORT))
serverSocket.listen(5)

print(f'Listening on port {PORT}...')

# assume we are using http version 1.1
while True:
    clientSocket, clientAddr = serverSocket.accept()
    clientRequest = clientSocket.recv(1024).decode()
    print(clientRequest)

    request_line = get_request_line(clientRequest)
    print(request_line)

    html_version = get_html_version(clientRequest)
    headerComponents = request_line.split(' ')
    path = headerComponents[1] if len(headerComponents) >= 2 else '/'
    headers = get_headers_dict(clientRequest)

    # --- Handle responses ---
    if html_version != 'HTTP/1.1':
        print('html version', html_version)
        serverResponse = f'HTTP/1.1 505 {STATUS_TEXT[505]}\n\n'

    elif '..' in path or '/secret/' in path:
        serverResponse = f'HTTP/1.1 403 {STATUS_TEXT[403]}\n\n'

    elif path == '/':
        content = 'Welcome to Derek and Kevin\'s server!'
        serverResponse = f'HTTP/1.1 200 {STATUS_TEXT[200]}\n\n{content}'

    elif path == '/test.html':
        filepath = '.' + path
        if os.path.exists(filepath):
            file_ModifiedTime = datetime.datetime.fromtimestamp(
                os.path.getmtime(filepath), tz=datetime.timezone.utc
            )

            if 'if-modified-since' in headers:
                http_fileTimestamp = parsedate_to_datetime(headers['if-modified-since'])
                if file_ModifiedTime <= http_fileTimestamp:
                    serverResponse = f'HTTP/1.1 304 {STATUS_TEXT[304]}\n\n'
                else:
                    with open(filepath) as fin:
                        content = fin.read()
                    serverResponse = f'HTTP/1.1 200 {STATUS_TEXT[200]}\n\n{content}'
            else:
                with open(filepath) as fin:
                    content = fin.read()
                serverResponse = f'HTTP/1.1 200 {STATUS_TEXT[200]}\n\n{content}'
        else:
            serverResponse = f'HTTP/1.1 404 {STATUS_TEXT[404]}\n\n'

    elif path == '/garbage.txt':
        serverResponse = f'HTTP/1.1 404 {STATUS_TEXT[404]}\n\n'

    else:
        serverResponse = f'HTTP/1.1 404 {STATUS_TEXT[404]}\n\n'

    print(serverResponse)
    clientSocket.sendall(serverResponse.encode())
    clientSocket.close()

serverSocket.close()
