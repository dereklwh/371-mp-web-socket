from socket import *

class ReceiverState:
     CONNECTED = False
     EXPECTED_SEQ = None

HOST = '127.0.0.1'
PORT = 12000


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

def handle_handshake(socket, pkt, addr):
     if pkt['flags'] == "SYN":
          print(f"Received SYN from {addr}")
     # send SYN-ACK
          ReceiverState.EXPECTED_SEQ = pkt['seq'] + 1
          syn_ack_packet = make_packet(
               seq=0,
               ack=ReceiverState.EXPECTED_SEQ,
               rwnd=32,
               flags="SYN-ACK",
               payload=b""
          )
          socket.sendto(syn_ack_packet, addr)
          print(f"Sent SYN-ACK to {addr}")
     
     # wait for ACK to establish connection
     if pkt['flags'] == "ACK" and pkt['ack'] == 1:
          print(f"Received ACK from {addr}, connection established")
          ReceiverState.CONNECTED = True

    
def main():

     serverSocket = socket(AF_INET, SOCK_DGRAM)
     serverSocket.bind((HOST, PORT))
     print('Server ready')
     # server handles rwnd
     while True:
          data, addr = serverSocket.recvfrom(2048)  # receive packet + client address
          pkt = parse_packet(data)
          print("expected seq:", ReceiverState.EXPECTED_SEQ)

          # receive 3 way handshake to establish connection
          if not ReceiverState.CONNECTED:
              handle_handshake(serverSocket, pkt, addr)
          

          if pkt['flags'] == "DATA" and ReceiverState.CONNECTED:
               sentence = data.decode()
               capitalized = sentence.upper().encode()
               serverSocket.sendto(capitalized, addr)
               print(f"Processed request from {addr}")
               print(f"data: {data}")

if __name__ == "__main__":
    main()

