from socket import *
import time
import random

HOST = '127.0.0.1'
PORT = 8080

RTO = 3.0   # timeout for retransmission in seconds
DUPE_ACK_THRESH = 3     # How many duplicate acks before retransmission

# Testing
# Set to True to simulate packet corruption
SIMULATE_CORRUPT = True
CORRUPTION_RATE = 0.1   # 10% of packets corrupted


class SenderState:
    CLOSED = 0
    SYN_SENT = 1
    CONNECTED = False

# helper function to make custom packet
def make_packet(seq, ack, rwnd, flags, payload: bytes) -> bytes:
    # Create header with placeholder checksum = 0
    header = f"{seq}|{ack}|{rwnd}|{flags}|0|".encode()
    temp_packet = header + payload

    # Calculate checksum
    checksum = checksum_calc(temp_packet)

    # Rebuild header with actual checksum
    header = f"{seq}|{ack}|{rwnd}|{flags}|{checksum}|".encode()
    final_packet = header + payload

    # Testing checksum functionality by intentionally corrupting packets
    if SIMULATE_CORRUPT and random.random() < CORRUPTION_RATE:
        print("[CORRUPT] Simulating packet corruption...")

        # Flip a random bit in payload
        if len(payload) > 0:
            corrupt_pos = random.randint(0, len(final_packet) - 1)
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
        raise ValueError("[ERROR] Checksum verification failed")
    
    return {
        'seq': seq,
        'ack': ack,
        'rwnd': rwnd,
        'flags': flags,
        'checksum': checksum,
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
    client.settimeout(2.0)  # Longer timeout for handshake
    
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

        try:
            data, addr = client.recvfrom(2048)
            pkt = parse_packet(data)
            print("Received packet:", pkt)
            if pkt['flags'] == "SYN-ACK":
                print("Received SYN-ACK from server.")
                break
        except ValueError as e:
            print(f"[ERROR] Checksum error during handshake: {e}")
            continue
        except timeout:
            print("Timeout waiting for SYN-ACK, retrying...")
            client.sendto(syn_packet, server_addr)
            continue
        
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
    # Client is used to send a packet to the server and receive a response
    client = socket(AF_INET, SOCK_DGRAM)
    client.settimeout(0.2)

    server_addr = (HOST, PORT)

    # First, perform three-way handshake to establish connection
    try:
        next_seq = perform_handshake(client, server_addr)
    except Exception as e:
        print(f"Handshake failed: {e}")
        return
    
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

    # Sliding window variables
    send_base = next_seq    # First unAcked Packet
    next_seq_num = next_seq # next packet that can be sent
    total_segments = len(segments)
    final_seq = next_seq + total_segments

    cwnd = 1
    rwnd = 32
    sent_times = {}     # To track send time
    buffered = {}       # seq -> payload
    dupe_ack_count = 0
    last_ack = send_base

    print(f"Total segments to send: {total_segments} (seq will range from {send_base} to {final_seq - 1})")

    i = 0   # index for next unsent segment
    iterations_without_progress = 0
    MAX_ITER_WITHOUT_PROGRESS = 50

    # Stats
    pkts_sent = 0
    pkts_retransmitted = 0
    corrupted_acks = 0
    acks_received = 0

    # Loop until all ACKs have been received for all segments
    while send_base < final_seq:
        # print(f"============================ DATA PACKET {send_base } of {total_segments} ============================")
        print("\n" + "="*70)
        print(f"LOOP: send_base={send_base}, next_seq_num={next_seq_num}, cwnd={cwnd}, rwnd={rwnd}")
        print(f"Buffered packets: {list(buffered.keys())}")
        print("="*70)

        # Check if done
        if send_base >= final_seq:
            print("[INFO] All packets ACKed! Exiting...")
            break
        
        # Track progress
        old_send_base = send_base
        
        # Send up to min(cwnd, rwnd) 
        effective_window = min(cwnd, rwnd)
        window_limit = send_base + effective_window

        print(f"[WINDOW] Effective window = min(cwnd={cwnd}, rwnd={rwnd}) = {effective_window}")
        print(f"[WINDOW] Can send up to seq {window_limit - 1}")

        # Send packets within window limit
        pkts_sent_this_round = 0
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
            pkts_sent += 1
            print(f"[SEND] Sent DATA seq = {next_seq_num}")

            buffered[next_seq_num] = payload
            sent_times[next_seq_num] = time.time()
            
            # Move to next item
            next_seq_num += 1
            i += 1
            pkts_sent_this_round += 1

        if pkts_sent_this_round == 0:
            if effective_window == 0:
                print("[FLOW CONTROL] Effective Window is 0, waiting for receiver to process data...")
            elif i >= total_segments:
                print("[INFO] All packets sent, waiting for final ACKs...")
            else:
                print("[INFO] No packets to send (all data sent, waiting for ACKs)")
        
        # Handle Timeouts
        if send_base in sent_times:
            if time.time() - sent_times[send_base] > RTO:
                print(f"[TIMEOUT] Timeout for send_base={send_base}. Retransmitting all unACKed packets...")

                # Multiplicative Decrease  (AIMD)
                cwnd = max(1, cwnd // 2)
                print(f"[AIMD] cwnd decreased to {cwnd}")

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
                        pkts_retransmitted += 1
                        print(f"[RETRANSMIT] Retransmitted seq = {seq}")

                dupe_ack_count = 0  # Reset dupe ACK count after time out
                continue
       
        # Receiving ACKs
        try:
            data, addr = client.recvfrom(2048)
            
            try:
                received = parse_packet(data)
                acks_received += 1
            except ValueError as e:
                print(f"[ERROR] {e} - ignoring corrupted ACK")
                corrupted_acks += 1
                continue 
            
        except timeout:
            # No ACK received, continue loop
            # Dont force new packets when receiver buffer is full
            if rwnd == 0 and len(buffered) > 0:
                print("[FLOW CONTROL] rwnd = 0, waiting for receiver to process...")
            continue

        if received:
            print(f"[RECV] Received packet: {received}")
            rwnd = max(0, received['rwnd'])     # update rwnd
            print(f"[FLOW CONTROL] Updated rwnd = {rwnd}")

            # Handle cumulative ACK
            if received['flags'] == "ACK":
                ack_num = received['ack']

                # If ACK acknowledges new data
                if ack_num > send_base:
                    print(f"[ACK] New ACK {ack_num} (was send_base={send_base})")

                    # remove buffered segments that are acked
                    remove_seqs = [s for s in buffered.keys() if s < ack_num]
                    for s in remove_seqs:
                        buffered.pop(s, None)
                        sent_times.pop(s, None)
                    print(f"[ACK] Removed {len(remove_seqs)} ACKed packets from buffer")

                    # slide window
                    send_base = ack_num
                    dupe_ack_count = 0
                    last_ack = ack_num

                    # Additive Increase (AIMD)
                    cwnd += 1
                    print(f"[AIMD] cwnd increased to {cwnd}")

                    # Check if done after ACK
                    if send_base >= final_seq:
                        print(f"[SUCCESS] send_base({send_base}) reached final_seq ({final_seq})")
                        break
                    
                # Handling dupe ACKs
                elif ack_num == last_ack:
                    dupe_ack_count += 1
                    print(f"[ACK] Duplicate ACK #{dupe_ack_count} for {ack_num}")
                    
                    if dupe_ack_count >= DUPE_ACK_THRESH:
                        print(f"\n[FAST RETRANSMIT] {DUPE_ACK_THRESH} duplicate ACKs detected: retransmitting send_base = {send_base}")

                        # Multiplicative Decrease (AIMD)
                        cwnd = max(1, cwnd // 2)
                        print(f"[AIMD] cwnd decreased to {cwnd}")

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
                            pkts_retransmitted += 1
                            print(f"[RETRANSMIT] Retransmitted seq = {send_base}")

                        dupe_ack_count = 0  # Reset dupe ACK count

        # Checking progress
        if send_base == old_send_base:
            iterations_without_progress += 1
            if iterations_without_progress >= MAX_ITER_WITHOUT_PROGRESS:
                print("[ERROR] No progress for 50 iterations")
                print(f"[ERROR] send_base={send_base}, buffered packets={list(buffered.keys())}")
                print(f"[ERROR] rwnd={rwnd}, cwnd={cwnd}")
                print("[ERROR] Possible deadlock, exiting...")
                break
        else:
            iterations_without_progress = 0

    # Final Stats
    if send_base >= final_seq:
        print("\n" + "="*70)
        print("[SUCCESS] All data packets send and ACKed")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("[ERROR] Not all packets ACKed")
        print(f"Expected final send_base: {next_seq + total_segments} Actual send_base: {send_base}")
        print("="*70)

    print(f"\n[STATS]")
    print(f"    Packets sent: {pkts_sent}")
    print(f"    Packets retransmitted: {pkts_retransmitted}")
    print(f"    Corrupted ACKs detected: {corrupted_acks}")
    print(f"    ACKs received: {acks_received}")
    print("="*70)


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
    # print("\n" + "="*70)
    # print("All data packets sent and acknowledged.")
    # print("="*70)
    
if __name__ == "__main__":
    main()
