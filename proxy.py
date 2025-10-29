from socket import *

PROXY_HOST = '127.0.0.1'
PROXY_PORT = 8080

ORIGIN_HOST = '127.0.0.1'
ORIGIN_PORT = 12000

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


def parse_request_line_for_path(request):
    request_line = get_request_line(request)
    parts = request_line.split(' ')
    if len(parts) == 3:
        path = parts[1]
        # get string after 127.0.0.1:12000
        return path
    return '/'

# --- Socket setup ---
proxySocket = socket(AF_INET, SOCK_STREAM)
proxySocket.bind((PROXY_HOST, PROXY_PORT))
proxySocket.listen(5)
print(f'Proxy server listening on port {PROXY_PORT}...')

while True:
    clientSocket, clientAddr = proxySocket.accept()
    print(f'Accepted connection from {clientAddr}')
    clientRequest = clientSocket.recv(4096).decode()
    print(f'Received request:\n{clientRequest}')

    request_line = get_request_line(clientRequest)
    print('Request line: ', request_line)

    processed_request = parse_request_line_for_path(clientRequest)
    print('Processed request path: ', processed_request)

    # connect to origin server
    print('Attempting to connect to origin server...')
    try: 
        originSocket = socket(AF_INET, SOCK_STREAM)
        originSocket.connect((ORIGIN_HOST, ORIGIN_PORT))
        originSocket.sendall(clientRequest.encode())

        # receive response from origin server
        print('Sent request to origin server, waiting for response...')
        originResponse = originSocket.recv(4096).decode()
        print(f'Received response from origin server:\n{originResponse}')

        # send response back to client
        clientSocket.sendall(originResponse.encode())
    except Exception as e:
        print('Error connecting to origin server:', e)
    finally:
        originSocket.close()
        clientSocket.close()


