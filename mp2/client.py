from socket import *

# helper function to make custom packet
def make_packet(seq, ack, rwnd, flags, payload: bytes) -> bytes:
    header = f"{seq}|{ack}|{rwnd}|{flags}|".encode()
    return header + payload

# Client is used to send a packet to the server and receive a response
client = socket(AF_INET, SOCK_DGRAM)
server_addr = ('127.0.0.1', 12000)

# need to implement 3 way handshake:
# then simulate sending multiple packets with payload in accordance to rwnd/cwnd
# client handles cwnd
pkt = make_packet(seq=0, ack=0, rwnd=32, flags="SYN", payload=b"hi my name is derekkk")
client.sendto(pkt, server_addr)
data, addr = client.recvfrom(2048)
print("Server replied:", data.decode())
