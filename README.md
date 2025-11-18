# 371-mp-web-socket

## Overview
We have developed a minimal connection-based web server and proxy using web sockets. This project is meant to demonstrate key networking concepts such as socket programming, multithreading, and HTTP request/repsonse handling.

### Web server
The web server serves as the origin server, responding to client requests forwarded by proxy. It hosts example content for testing the proxy's functionality.

### Proxy Server
The server lives between the client and the origin web server to process requests/responses from each side. It does not host the example 

#### Features
- Custom HTTP Response Code Handling: Implements logic for handling the HTTP response codes (200, 304, 403, 404, 505)
- URL parsing: accepts incoming client connections and extracts the request message
- Connection management: creates new socket to origin server for each request and then closes it once the connection is complete.
- Thread safety: each client handled in independent thread
- Request forwarding: properly reconstructs http request and forwards request to origin server
- Response Handling: after receiving the response from origin server, forward response to client

## Testing the proxy and origin server

### Prereqs
- Python 3.x installed

### Steps
1. Start origin and proxy server by running the following commands:

```
python server.py
python proxy.py
```

2. Test basic proxy forwarding in the CLI
```
curl -x http://127.0.0.1:8080 http://127.0.0.1:12000/

curl http://127.0.0.1:8080 http://127.0.0.1:12000/test.html

curl http://127.0.0.1:8080 http://127.0.0.1:12000/garbage.html
```

### Expected Output
- for valid requests, the server should return the requested content
- for invalid requests, the server should return appropriate error message