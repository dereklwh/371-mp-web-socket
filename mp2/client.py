from socket import *

HOST = '127.0.0.1'
PORT = 12000

class SenderState:
    CLOSED = 0
    SYN_SENT = 1
    CONNECTED = False

# helper function to make custom packet
def make_packet(seq, ack, rwnd, flags, payload: bytes) -> bytes:
    header = f"{seq}|{ack}|{rwnd}|{flags}|".encode()
    return header + payload

def parse_packet(packet: bytes) -> dict:
    header, payload = packet.split(b'|', 4)[:4], packet.split(b'|', 4)[4]
    seq = int(header[0])
    ack = int(header[1])
    rwnd = int(header[2])
    flags = header[3].decode()
    return {
        'seq': seq,
        'ack': ack,
        'rwnd': rwnd,
        'flags': flags,
        'payload': payload
    }

def perform_handshake(client, server_addr):
    """
    Perform a three-way handshake with the server.
    1) SYN
    2) SYN-ACK
    3) ACK
    """
    print("Performing three-way handshake...")
    # Step 1: Send SYN
    syn_seq = 0
    syn_packet = make_packet(
        seq=syn_seq,
        ack=0,
        rwnd=32,
        flags="SYN",
        payload=b""
    )
    client.sendto(syn_packet, server_addr)

    # Step 2: Receive SYN-ACK
    while True:
        data, addr = client.recvfrom(2048)
        pkt = parse_packet(data)
        print("Received packet:", pkt)
        if pkt['flags'] == "SYN-ACK":
            print("Received SYN-ACK from server.")
            break
        else:
            print("Unexpected packet, waiting for SYN-ACK...")
    
    # Step 3: Send ACK
    ack_packet = make_packet(
        seq=syn_seq + 1,
        ack=pkt['seq'] + 1,
        rwnd=32,
        flags="ACK",
        payload=b""
    )
    print("Sending ACK to server...", ack_packet)

    client.sendto(ack_packet, server_addr)
    # connection established, ++seq number for next data packet
    print("Sent ACK to server.")
    print("Three-way handshake completed. Connection established.")
    SenderState.CONNECTED = True
    
    # return the next sequence number
    return syn_seq + 1

def main():
    # Client is used to send a packet to the server and receive a response
    client = socket(AF_INET, SOCK_DGRAM)
    server_addr = (HOST, PORT)

    # need to implement 3 way handshake:
    next_seq = perform_handshake(client, server_addr)

    # then simulate sending multiple packets with payload in accordance to rwnd/cwnd
    # client handles cwnd
    if SenderState.CONNECTED == True:
        print("Connection established, sending data...")
        pkt = make_packet(seq=0, ack=0, rwnd=32, flags="DATA", payload=b"hi my name is derekkk")
        client.sendto(pkt, server_addr)
        data, addr = client.recvfrom(2048)
        print("Server replied:", data.decode())

if __name__ == "__main__":
    main()
