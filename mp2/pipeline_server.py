from socket import *
import random
import threading
import time

HOST = '127.0.0.1'
PORT = 8080

# Testing
# Set to True to simulate packet corruption
SIMULATE_CORRUPT = True
CORRUPTION_RATE = 0.1   # 10% of packets corrupted

class ReceiverState:
     CONNECTED = False
     EXPECTED_SEQ = None
     BUFFER_SIZE = 5    # Receiver advertised window (for flow control)
     USED_BUFFER = 0     # How much data is stored
     lock = threading.Lock()  # Locks buffer access for thread safety
     client_addr = None  # Store client addr for sending updates
     socket = None  # Socket reference
     last_rwnd_sent = None    # Track last advertised window

# helper function to make custom packet
def make_packet(seq, ack, rwnd, flags, payload: bytes) -> bytes:
     # Header with placeholder checksum = 0
     header = f"{seq}|{ack}|{rwnd}|{flags}|0|".encode()
     temp_packet = header + payload

     # Calculate checksum of entire packet
     checksum = checksum_calc(temp_packet)

     # Rebuild header with actual checksum
     header = f"{seq}|{ack}|{rwnd}|{flags}|{checksum}|".encode()
     final_packet = header + payload

     # Testing checksum functionality by intentionally corrupting packets
     if SIMULATE_CORRUPT and random.random() < CORRUPTION_RATE:
          print("[CORRUPT] Simulating packet corruption...")

          # Flip a random bit in payload
          if len(payload) > 0:
               header_len = len(header)
               corrupt_pos = random.randint(header_len, len(final_packet) - 1)
               packet_list = bytearray(final_packet)
               packet_list[corrupt_pos] ^= 0xFF    # Flip all bits in one byte
               final_packet = bytes(packet_list)

     return final_packet


def parse_packet(packet: bytes) -> dict:
     # Parse packet and verify checksum
     parts = packet.split(b'|', 5)

     if len(parts) < 5:
         raise ValueError("Malformed packet: not enough fields")
    
     try:
          seq = int(parts[0])
          ack = int(parts[1])
          rwnd = int(parts[2])
          flags = parts[3].decode()
          checksum = int(parts[4])
          payload = parts[5] if len(parts) > 5 else b''
     except (ValueError, IndexError) as e:
          raise ValueError(f"Malformed packet: {e}")
     
     # Verify checksum
     if not verify_checksum(packet, checksum):
          raise ValueError("[ERROR] Checksum verification failed - packet corrupted")
     
     return {
          'seq': seq,
          'ack': ack,
          'rwnd': rwnd,
          'flags': flags,
          'checksum': checksum,
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
          print(f"Received ACK from {addr}, connection established!!")
          ReceiverState.CONNECTED = True
          ReceiverState.EXPECTED_SEQ = pkt['seq']

def send_window_update():
     # Send window update to client with current rwnd
     # Called whenever buffer space is available
     if ReceiverState.client_addr and ReceiverState.socket and ReceiverState.EXPECTED_SEQ is not None:
          with ReceiverState.lock:
               avail_window = max(0, ReceiverState.BUFFER_SIZE - ReceiverState.USED_BUFFER)

               # Only send if window space become available
               if ReceiverState.last_rwnd_sent == 0 and avail_window > 0:
                    # Send packet with updated rwnd
                    update_window = make_packet(
                         seq = 0,
                         ack = ReceiverState.EXPECTED_SEQ,
                         rwnd = avail_window,
                         flags = "ACK", 
                         payload = b""
                    )

                    ReceiverState.socket.sendto(update_window, ReceiverState.client_addr)
                    ReceiverState.last_rwnd_sent = avail_window
                    print(f"[WINDOW UPDATE] Sent ACK with rwnd = {avail_window}")

def buffer_process():
     # Background thread that processes buffered data continuously.
     # Basically simulates consuming of data
     while True:
          time.sleep(0.3)     # Simulate time passing for data to be processed

          with ReceiverState.lock:
               # Simulate prcoessing of a packet
               if ReceiverState.USED_BUFFER > 0:
                    old_buffer = ReceiverState.USED_BUFFER
                    ReceiverState.USED_BUFFER -= 1
                    print(f"[BACKGROUND] Processed 1 packet. Current Buffer: {ReceiverState.USED_BUFFER}/{ReceiverState.BUFFER_SIZE}")

                    if old_buffer == ReceiverState.BUFFER_SIZE:
                         print(f"[BACKGROUND] Buffer was full but now has space, Sending window update...")

                         # Release lock before send to avoid deadlock
                         threading.Thread(target=send_window_update, daemon=True).start()

def checksum_calc(data: bytes) -> int:
     # Caculate simple checksum by summing all bytes
     checksum = 0

     # Process bytes into pairs
     for i in range(0, len(data), 2):
          if i + 1 < len(data):
               # Combine 2 bytes into 16bit word
               word = (data[i] << 8) + data[i + 1]
          else:
               # Pad odd number of bytes with 0
               word = data[i] << 8
          
          checksum += word

          # Carry around addition
          checksum = (checksum & 0xFFFF) + (checksum >> 16)

     # One's complement
     checksum = ~checksum & 0xFFFF

     return checksum

def verify_checksum(data: bytes, expected_checksum: int) -> bool:
     # Verify packet checksum by recreating packet with checksum = 0
     # calculating checksum and comparing
     parts = data.split(b'|', 5)
     if len(parts) < 5:
          return False
     
     # Rebuild packet w/ checksum = 0
     no_checksum_header = b'|'.join(parts[:4]) + b'|0|'
     if len(parts) > 5:
          no_checksum_pkt = no_checksum_header + parts[5]
     else:
          no_checksum_pkt = no_checksum_header

     # Calculate checksum
     calculated_checksum = checksum_calc(no_checksum_pkt)

     # Compare and return
     return calculated_checksum == expected_checksum


def main():
     serverSocket = socket(AF_INET, SOCK_DGRAM)
     serverSocket.bind((HOST, PORT))
     serverSocket.settimeout(0.5)
     print('Server ready')

     # Store socket in state for window updates
     ReceiverState.socket = serverSocket
     
     # Background thread for buffer processing
     processor_thread = threading.Thread(target=buffer_process, daemon = True)
     processor_thread.start()
     print("[BACKGROUND] Buffer processor started")

     # Stats
     pkts_received = 0
     pkts_corrupted = 0

     while True:
          try:
               data, addr = serverSocket.recvfrom(2048)  # receive packet + client address
          except timeout:
               # No packets received continue
               continue
          
          ReceiverState.client_addr = addr
          pkts_received += 1

          try:
               pkt = parse_packet(data)
          except ValueError as e:
               pkts_corrupted += 1
               print("Malformed packet, ignoring:", e)
               print(f"[CHECKSUM] Invalid - dropping packet")
               continue
          
          print("===================================================================")
          print("(1) Received packet:", pkt)

          # receive 3 way handshake to establish connection
          if not ReceiverState.CONNECTED:
              handle_handshake(serverSocket, pkt, addr)
              continue
          
          # After connection established, process data packets, send ACKs back
          if pkt['flags'] == "DATA" and ReceiverState.CONNECTED:
               with ReceiverState.lock:
                    # Flow Control: drop packet if receiver buffer is full
                    if ReceiverState.USED_BUFFER >= ReceiverState.BUFFER_SIZE:
                         print(f"[FLOW CONTROL] Receiver buffer full ({ReceiverState.USED_BUFFER}/{ReceiverState.BUFFER_SIZE})")
                         print("[FLOW CONTROL] Sending duplicate ACK with rwnd=0")
                         dupe_ack = make_packet(
                              seq = 0,
                              ack = ReceiverState.EXPECTED_SEQ,
                              rwnd = 0,      # Receiver is full so advertise rwnd as 0
                              flags = "ACK",
                              payload = b""
                         )
                         serverSocket.sendto(dupe_ack, addr)
                         ReceiverState.last_rwnd_sent = 0
                         continue
                    
                    # Go-Back-N in order delivery
                    if pkt['seq'] != ReceiverState.EXPECTED_SEQ:
                         print(f"""Out of order packet from {addr}. Expected seq {ReceiverState.EXPECTED_SEQ}, 
                              got {pkt['seq']}. Sending duplicate ACK.""")
                         
                         # send dupe ACKs for fast retransmit w/o waiting for a timeout
                         # Calculate available window
                         avail_window = max(0, ReceiverState.BUFFER_SIZE - ReceiverState.USED_BUFFER)
                         dupe_ack = make_packet(
                              seq = 0,
                              ack = ReceiverState.EXPECTED_SEQ,
                              rwnd = avail_window,
                              flags = "ACK",
                              payload = b""
                         )
                         serverSocket.sendto(dupe_ack, addr)
                         ReceiverState.last_rwnd_sent = avail_window
                         continue
                    
                    # Accept packet
                    ReceiverState.USED_BUFFER += 1
                    print(f"Accepted in order packet seq {pkt['seq']}")
                    print("BUFFER USED = ", ReceiverState.USED_BUFFER, "/", ReceiverState.BUFFER_SIZE)


                    # update expected seq
                    ReceiverState.EXPECTED_SEQ += 1

                    # Calculate available window
                    avail_window = max(0, ReceiverState.BUFFER_SIZE - ReceiverState.USED_BUFFER)

                    # send cumulative ACK
                    ack_packet = make_packet(
                         seq=0,
                         ack=ReceiverState.EXPECTED_SEQ,
                         rwnd= avail_window,
                         flags="ACK",
                         payload=b""
                    )
                    serverSocket.sendto(ack_packet, addr)
                    ReceiverState.last_rwnd_sent = avail_window
                    print(f"(2) Sent ACK for seq {pkt['seq']} to {addr}")
               # end of loop


if __name__ == "__main__":
    main()

