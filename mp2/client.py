from socket import *
import time

HOST = '127.0.0.1'
PORT = 8080

RTO = 3.0   # timeout for retransmission in seconds
DUPE_ACK_THRESH = 3     # How many duplicate acks before retransmission

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

#TODO: implement checksum
def main():
    # Client is used to send a packet to the server and receive a response
    client = socket(AF_INET, SOCK_DGRAM)
    client.settimeout(0.1)

    server_addr = (HOST, PORT)

    # First, perform three-way handshake to establish connection
    next_seq = perform_handshake(client, server_addr)

    # then simulate sending multiple packets with payload in accordance to rwnd/cwnd
    if SenderState.CONNECTED == False:
        print("Handshake failed, cannot send data.")
        return

    # Once connection is established, send data packets
    app_data = b"""_4&@=EFyR=R,?Q:3q&ir7rV22$7yE(
                #uFJ]H*Kjk57*21K=CAQ/t6)S?Ff4L
                JrU}E/md[(,Aq6d/DhQD3/3{3XRa]r
                """ * 20
    MAX_PAYLOAD_SIZE = 20  # max payload size per packet

    segments = [
        app_data[i:i + MAX_PAYLOAD_SIZE]
        for i in range(0, len(app_data), MAX_PAYLOAD_SIZE)
    ]
    print("Data to send segmented into packets:", len(segments))

    #TODO: implement go back n and aimd here
    # Sliding window variables
    send_base = next_seq    # First unAcked Packet
    next_seq_num = next_seq # next packet that can be sent
    total_segments = len(segments)

    cwnd = 1
    rwnd = 32
    sent_times = {}     # To track send time
    buffered = {}       # seq -> payload
    dupe_ack_count = 0

    print(f"Total segments to send: {total_segments} (seq will range from {send_base} to {send_base + total_segments - 1})")

    i = 0   # index for next unsent segment

    # Loop until all ACKs have been received for all segments
    while send_base < next_seq + total_segments:
        print(f"============================ DATA PACKET {send_base } of {total_segments} ============================")
        
        # Send up to min(cwnd, rwnd) 
        window_limit = send_base + min(cwnd, rwnd)

        # Send packets within window limit
        while i < total_segments and next_seq_num < window_limit:
            
            payload = segments[i]
            pkt = make_packet(
                seq = next_seq_num,
                ack = 0,
                rwnd = rwnd,
                flags = "DATA",
                payload = payload
            )

            client.sendto(pkt, server_addr)
            print(f"Sent DATA seq = {next_seq_num}")

            buffered[next_seq_num] = payload
            sent_times[next_seq_num] = time.time()
            
            # Move to next item
            next_seq_num += 1
            i += 1

        # Receiving ACKs
        try:
            data, addr = client.recvfrom(2048)
            received = parse_packet(data)
        except timeout:
            received = None

        if received:
            print("Received packet:", received)
            rwnd = max(0, received['rwnd'])     # update rwnd

            # Handle cumulative ACK
            if received['flags'] == "ACK":
                ack_num = received['ack']

                # If ACK acknowledges new data
                if ack_num > send_base:
                    print(f"New ACK {ack_num} (was send_base={send_base})")

                    # remove buffered segments that are acked
                    remove_seqs = [s for s in buffered.keys() if s < ack_num]
                    for s in remove_seqs:
                        buffered.pop(s, None)
                        sent_times.pop(s, None)

                    # slide window
                    send_base = ack_num
                    dupe_ack_count = 0

                    # Additive Increase (AIMD)
                    cwnd += 1
                    print(f"[AIMD] cwnd increased to {cwnd}")
                # Handling dupe ACKs
                elif ack_num == send_base:
                    dupe_ack_count += 1
                    print(f"Duplicate ACK #{dupe_ack_count} for {ack_num}")
                    if dupe_ack_count >= DUPE_ACK_THRESH:
                        print("Fast retransmit triggered: retransmitting send_base segment")

                        # Multiplicative Decrease (AIMD)
                        cwnd = max(1, cwnd // 2)
                        # Retransmit base segment
                        if send_base in buffered:
                            pkt = make_packet(
                                seq = send_base,
                                ack = 0,
                                rwnd = rwnd,
                                flags = "DATA",
                                payload = buffered[send_base]
                            )
                            client.sendto(pkt, server_addr)
                            sent_times[send_base] = time.time()     # Reset time for send_base segment
                        dupe_ack_count = 0  # Reset dupe ACK count

            # Handle Timeouts
            if send_base in sent_times:
                if time.time() - sent_times[send_base] > RTO:
                    print(f"Timeout for send_base={send_base}. Retransmitting all unACKed packets...")

                    # Multiplicative Decrease  (AIMD)
                    cwnd = max(1, cwnd // 2)
                    # Retransmit all segment from send base to next_seq_num - 1
                    for seq in range(send_base, next_seq_num):
                        if seq in buffered:
                            pkt = make_packet(
                                seq = seq,
                                ack = 0,
                                rwnd = rwnd,
                                flags = "DATA",
                                payload = buffered[seq]
                            )
                            client.sendto(pkt, server_addr)
                            sent_times[seq] = time.time()   # reset timers for each packet
                    
                    dupe_ack_count = 0  # Reset dupe ACK count after time out
            
            # Wait for window update when rwnd == 0
            if rwnd == 0:
                time.sleep(0.05)



    # seg_index = 0
    # cwnd = 1  # initial congestion window size

    # while seg_index < len(segments):
    #     # send packets according to cwnd
    #     print(f"============================ DATA PACKET {seg_index + 1} of {len(segments)} ============================")
    #     payload = segments[seg_index]
    #     pkt = make_packet(
    #         seq=next_seq,
    #         ack=0,
    #         rwnd=32,
    #         flags="DATA",
    #         payload=payload
    #     )
    #     client.sendto(pkt, server_addr)
    #     print(f"(1) Sent packet with seq={next_seq}, payload={payload}")

    #     seg_index += 1
    #     next_seq += 1

    #     # wait for ACK
    #     data, addr = client.recvfrom(2048)
    #     ack_pkt = parse_packet(data)
    #     print("(2) Received ACK packet:", ack_pkt)
    #     if ack_pkt['flags'] == "ACK":
    #         print(f"ACK received for seq={ack_pkt['ack']}")
    #         cwnd += 1 # AIMD not fully impented yet, TODO: dynamic adjust window size
    #         print("(3) [AIMD] Congestion window increased to:", cwnd)
    #     else:
    #         print("Unexpected packet received, expected ACK.")
    #         return
        
    # After sending all data packets, close the connection
    print("All data packets sent and acknowledged.")

if __name__ == "__main__":
    main()
