
import socket
import select
import time

PORTS = [5001, 5005, 5006]

sockets = []

for port in PORTS:
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind(("0.0.0.0", port))
    sockets.append(server)

print("QoS UDP Server Started")
print(f"Listening on ports: {PORTS}\n")

received_packets = {port: 0 for port in PORTS}
received_bytes = {port: 0 for port in PORTS}

try:
    while True:
        ready, _, _ = select.select(sockets, [], [])

        for server in ready:
            data, address = server.recvfrom(2048)
            port = server.getsockname()[1]

            received_packets[port] += 1
            received_bytes[port] += len(data)

            if port == 5005:
                traffic_class = "HIGH"
            elif port == 5001:
                traffic_class = "MEDIUM"
            else:
                traffic_class = "LOW"

            print(
                f"[{traffic_class}] Received "
                f"{len(data)} bytes from {address}"
            )

            # Echo the packet back to the client
            server.sendto(data, address)

except KeyboardInterrupt:
    print("\nServer stopped.")

finally:
    print("\n--- Server Statistics ---")

    for port in PORTS:
        print(
            f"Port {port}: "
            f"{received_packets[port]} packets, "
            f"{received_bytes[port]} bytes"
        )

    for server in sockets:
        server.close()
