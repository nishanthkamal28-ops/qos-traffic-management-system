
import socket
import time
import argparse
import csv
import os
import struct
import statistics
import select

# Traffic class and destination port configuration
TRAFFIC_CLASSES = {
    "HIGH": {"port": 5005},
    "MEDIUM": {"port": 5001},
    "LOW": {"port": 5006}
}

HEADER_SIZE = 12
CSV_FILE = "qos_results.csv"

# Command-line arguments
parser = argparse.ArgumentParser(
    description="QoS UDP Traffic Generator and Performance Monitor"
)

parser.add_argument(
    "--class",
    dest="traffic_class",
    choices=["HIGH", "MEDIUM", "LOW"],
    required=True,
    help="Traffic priority class"
)

parser.add_argument(
    "--rate",
    type=float,
    default=1.0,
    help="Target UDP payload rate in Mbps"
)

parser.add_argument(
    "--size",
    type=int,
    default=1200,
    help="UDP payload size in bytes"
)

parser.add_argument(
    "--duration",
    type=float,
    default=10,
    help="Test duration in seconds"
)

parser.add_argument(
    "--host",
    default="127.0.0.1",
    help="IP address of the UDP server"
)

args = parser.parse_args()

# Validate arguments
if args.rate <= 0:
    parser.error("Rate must be greater than zero")

if not 128 <= args.size <= 1400:
    parser.error("Packet size must be between 128 and 1400 bytes")

if args.duration <= 0:
    parser.error("Duration must be greater than zero")

# Configuration
SERVER_IP = args.host
SERVER_PORT = TRAFFIC_CLASSES[args.traffic_class]["port"]
PACKET_SIZE = args.size
DURATION = args.duration

# Calculate interval between packets.
# This targets the UDP payload rate, excluding network headers.
interval = PACKET_SIZE * 8 / (args.rate * 1_000_000)

# Create UDP socket
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.bind(("0.0.0.0", 0))
client.setblocking(False)

# Performance statistics
sent_times = {}
rtts = []
sent_packets = 0
received_packets = 0
received_bytes = 0

start = time.monotonic()
next_send = start
end_time = start + DURATION

print("\n========== QoS UDP Traffic Generator ==========")
print(f"Traffic Class: {args.traffic_class}")
print(f"Server: {SERVER_IP}:{SERVER_PORT}")
print(f"Target Rate: {args.rate} Mbps")
print(f"Packet Size: {PACKET_SIZE} bytes")
print(f"Duration: {DURATION} seconds")
print("================================================\n")


def process_responses():
    """Receive echoed packets and calculate RTT."""
    global received_packets, received_bytes

    while True:
        try:
            data, _ = client.recvfrom(2048)
        except BlockingIOError:
            break
        except OSError:
            break

        if len(data) < HEADER_SIZE:
            continue

        try:
            seq, timestamp = struct.unpack("!Id", data[:HEADER_SIZE])
        except struct.error:
            continue

        if seq in sent_times:
            rtt_ms = (time.monotonic() - sent_times.pop(seq)) * 1000

            rtts.append(rtt_ms)
            received_packets += 1
            received_bytes += len(data)


try:
    while time.monotonic() < end_time:
        now = time.monotonic()

        # Generate the next packet when scheduled
        if now >= next_send:
            seq = sent_packets
            timestamp = time.monotonic()

            header = struct.pack("!Id", seq, timestamp)
            packet = header + b"x" * (PACKET_SIZE - HEADER_SIZE)

            try:
                client.sendto(packet, (SERVER_IP, SERVER_PORT))

                sent_times[seq] = timestamp
                sent_packets += 1

            except OSError as error:
                print(f"Send error: {error}")

            next_send += interval

            # Avoid trying to catch up by sending a sudden burst
            if next_send < time.monotonic():
                next_send = time.monotonic() + interval

        process_responses()

        # Wait briefly for network activity
        time.sleep(0.0001)

    # Allow up to two seconds for outstanding echo responses
    drain_end = time.monotonic() + 2

    while sent_times and time.monotonic() < drain_end:
        readable, _, _ = select.select([client], [], [], 0.01)

        if readable:
            process_responses()

finally:
    client.close()


# Calculate final statistics
elapsed = time.monotonic() - start

lost_packets = sent_packets - received_packets

loss_percent = (
    lost_packets / sent_packets * 100
    if sent_packets > 0 else 0
)

throughput_mbps = (
    received_bytes * 8 / elapsed / 1_000_000
    if elapsed > 0 else 0
)

average_rtt = statistics.mean(rtts) if rtts else None
minimum_rtt = min(rtts) if rtts else None
maximum_rtt = max(rtts) if rtts else None


# Display results
print("\n=============== PERFORMANCE RESULTS ===============")
print(f"Traffic Class: {args.traffic_class}")
print(f"Packets Sent: {sent_packets}")
print(f"Echo Responses Received: {received_packets}")
print(f"Estimated Packet Loss: {loss_percent:.2f}%")
print(f"Echo Throughput: {throughput_mbps:.3f} Mbps")

if rtts:
    print(f"Average RTT: {average_rtt:.3f} ms")
    print(f"Minimum RTT: {minimum_rtt:.3f} ms")
    print(f"Maximum RTT: {maximum_rtt:.3f} ms")
else:
    print("No RTT measurements available.")

print("====================================================")


# Save results to CSV
file_exists = (
    os.path.isfile(CSV_FILE)
    and os.path.getsize(CSV_FILE) > 0
)

with open(CSV_FILE, "a", newline="") as file:
    writer = csv.writer(file)

    if not file_exists:
        writer.writerow([
            "Timestamp",
            "Traffic Class",
            "Server IP",
            "Destination Port",
            "Target Rate (Mbps)",
            "Packet Size (bytes)",
            "Duration (seconds)",
            "Packets Sent",
            "Echo Responses Received",
            "Estimated Packet Loss (%)",
            "Echo Throughput (Mbps)",
            "Average RTT (ms)",
            "Minimum RTT (ms)",
            "Maximum RTT (ms)"
        ])

    writer.writerow([
        time.strftime("%Y-%m-%d %H:%M:%S"),
        args.traffic_class,
        SERVER_IP,
        SERVER_PORT,
        args.rate,
        PACKET_SIZE,
        DURATION,
        sent_packets,
        received_packets,
        round(loss_percent, 2),
        round(throughput_mbps, 3),
        round(average_rtt, 3) if average_rtt is not None else "",
        round(minimum_rtt, 3) if minimum_rtt is not None else "",
        round(maximum_rtt, 3) if maximum_rtt is not None else ""
    ])

print(f"\nResults saved to {CSV_FILE}")
print(f"CSV location: {os.path.abspath(CSV_FILE)}")
