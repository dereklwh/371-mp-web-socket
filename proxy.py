from socket import *

PROXY_HOST = '127.0.0.1'
PROXY_PORT = 8080

def handle_client_connection(clientSocket):
    request = clientSocket.recv(4096).decode()
    print(f'Received request:\n{request}')

    # Here you would typically parse the request, forward it to the target server,
    # receive the response, and send it back to the client.
    # For simplicity, we'll just send a basic HTTP response back.

    http_response = """\HTTP/1.1 200 OK
    Content-Type: text/plain
    Hello from the proxy server!
    """
    clientSocket.sendall(http_response.encode())
    clientSocket.close()

    clientSocket, clientAddr = proxySocket.accept()
    print(f'Accepted connection from {clientAddr}')

# --- Socket setup ---
proxySocket = socket(AF_INET, SOCK_STREAM)
proxySocket.bind((PROXY_HOST, PROXY_PORT))
proxySocket.listen(5)
print(f'Proxy server listening on port {PROXY_PORT}...')

while True:

