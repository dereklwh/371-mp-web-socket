from socket import *

HOST = '127.0.0.1'
PORT = 12000

class ReceiverState:
     CONNECTED = False
     EXPECTED_SEQ = None
     BUFFER_SIZE = 32    # Receiver advertised window (for flow control)
     USED_BUFFER = 0     # How much data is stored

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
               rwnd= ReceiverState.BUFFER_SIZE,
               flags="SYN-ACK",
               payload=b""
          )
          socket.sendto(syn_ack_packet, addr)
          print(f"Sent SYN-ACK to {addr}")
     
     # wait for ACK to establish connection
     if pkt['flags'] == "ACK" and pkt['ack'] == ReceiverState.EXPECTED_SEQ:
          print(f"Received ACK from {addr}, connection established")
          ReceiverState.CONNECTED = True

#TODO: implement checksum
def main():
     serverSocket = socket(AF_INET, SOCK_DGRAM)
     serverSocket.bind((HOST, PORT))
     print('Server ready')

     while True:
          data, addr = serverSocket.recvfrom(2048)  # receive packet + client address
          try:
               pkt = parse_packet(data)
          except Exception as e:
               print("Malformed packet, ignoring:", e)
               continue
          
          print("============================================================================")
          print("(1) Received packet:", pkt)

          # receive 3 way handshake to establish connection
          if not ReceiverState.CONNECTED:
              handle_handshake(serverSocket, pkt, addr)
              continue
          
          # After connection established, process data packets, send ACKs back
          if pkt['flags'] == "DATA" and ReceiverState.CONNECTED:
               # Flow COntrol: drop packet if receiver buffer is full
               if ReceiverState.USED_BUFFER >= ReceiverState.BUFFER_SIZE:
                    print("Receiver full - sending duplicate ACK")
                    dupe_ack = make_packet(
                         seq = 0,
                         ack = ReceiverState.EXPECTED_SEQ,
                         rwnd = max(0, ReceiverState.BUFFER_SIZE - ReceiverState.USED_BUFFER),
                         flags = "ACK",
                         payload = b""
                    )
                    serverSocket.sendto(dupe_ack, addr)
                    continue
               
               # Go-Back-N in order delivery
               if pkt['seq'] != ReceiverState.EXPECTED_SEQ:
                    print(f"""Out of order packet from {addr}. Expected seq {ReceiverState.EXPECTED_SEQ}, 
                          got {pkt['seq']}. Sending duplicate ACK.""")
                    
                    # send dupe ACKs for fast retransmit w/o waiting for a timeout
                    dupe_ack = make_packet(
                         seq = 0,
                         ack = ReceiverState.EXPECTED_SEQ,
                         rwnd = max(0, ReceiverState.BUFFER_SIZE - ReceiverState.USED_BUFFER),
                         flags = "ACK",
                         payload = b""
                    )
                    serverSocket.sendto(dupe_ack, addr)
                    continue
               
               # Accept packet
               ReceiverState.USED_BUFFER += len(pkt["payload"])
               print(f"Accepted in order packet seq {pkt['seq']}")

               # Simulate consumming data packet
               ReceiverState.USED_BUFFER = max(0, ReceiverState.USED_BUFFER - len(pkt["payload"]))

               # update expected seq
               ReceiverState.EXPECTED_SEQ += 1

               # send cumulative ACK
               ack_packet = make_packet(
                    seq=0,
                    ack=ReceiverState.EXPECTED_SEQ,
                    rwnd= max(0, ReceiverState.BUFFER_SIZE - ReceiverState.USED_BUFFER),
                    flags="ACK",
                    payload=b""
               )
               serverSocket.sendto(ack_packet, addr)
               print(f"(2) Sent ACK for seq {pkt['seq']} to {addr}")
          # end of loop


if __name__ == "__main__":
    main()

