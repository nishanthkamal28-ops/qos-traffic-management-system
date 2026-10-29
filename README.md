# QoS Traffic Management System

A three-member Computer Networks mini-project that generates UDP traffic, creates congestion in a Mininet network, and explores SDN-based flow prioritization.

## Project status

This repository brings together the source files supplied for Members 1, 2, and 3. Member 2's baseline Mininet topology and tests have been run in an Ubuntu 26.04 VirtualBox VM. The captured report is in `member2/results/d1_baseline.txt`.

The three source packages currently use different UDP port mappings. See [Integration notes](#integration-notes) before combining the applications and controller.

## Repository layout

- `member1/` — UDP client, echo server, and the supplied sample CSV result.
- `member2/` — Mininet dumbbell topology, baseline/congestion test script, and test report.
- `member3-controller/` — Ryu OpenFlow 1.3 controller.

## Member 2: Mininet baseline

Ubuntu/Debian VM prerequisites:

```bash
sudo apt update
sudo apt install -y mininet openvswitch-switch iperf
```

Run the topology interactively without an SDN controller:

```bash
cd member2
sudo python3 topology.py --baseline
```

At the `mininet>` prompt, useful checks are:

```text
net
pingall
dump
exit
```

Run the automated baseline tests:

```bash
cd member2
sudo python3 d1_tests.py --baseline
```

The test writes `results/d1_baseline.txt`. To run in SDN mode, start a compatible Ryu controller listening on `127.0.0.1:6653`, then run `sudo python3 d1_tests.py` from `member2`.

## Member 1: UDP echo application

Start the server in one terminal:

```bash
python3 member1/server.py
```

In a second terminal, send a local HIGH-class sample:

```bash
python3 member1/client.py --class HIGH --host 127.0.0.1 --rate 1 --duration 10
```

The client appends measurements to `qos_results.csv` in its current working directory.

## Member 3: SDN controller

With Ryu installed in the environment, start the controller from the repository root:

```bash
ryu-manager member3-controller/qos_controller.py
```

The Mininet switches use OpenFlow 1.3 and the topology defaults to controller `127.0.0.1:6653`.

## Integration notes

The supplied modules need a shared port contract before the full UDP application is run through Mininet:

| Source | Port mapping in supplied code |
|---|---|
| Member 1 client | HIGH 5005, MEDIUM 5001, LOW 5006 |
| Member 1 server | listens on 5001, 5005, 5006 |
| Member 2 topology | h1 5001, h2 5002, h3 5003 |
| Member 2 D1 iperf tests | use 5001, 5002, 5003 |
| Member 3 controller | HIGH 5004/5005, MEDIUM 5001–5003, all other UDP ports LOW |

The Member 2 D1 script uses iperf and validates the Mininet network independently of Member 1's echo server. The supplied controller installs matching OpenFlow flows with different flow priorities; it does not yet configure Open vSwitch QoS queues. Coordinate these points across the team before claiming end-to-end dynamic QoS integration.

## Captured Member 2 baseline

The report in `member2/results/d1_baseline.txt` records:

- `pingall`: 0% packet loss.
- Idle h1→h4 RTT: 25.047 ms minimum, 26.722 ms average, 28.311 ms maximum.
- One UDP flow at 8 Mbps: 8.39 Mbit/s received, 0% loss.
- Three UDP flows offered at 7 Mbps each: roughly 3.1–3.4 Mbit/s received per flow, with 54–57% loss, confirming congestion at the 10 Mbps bottleneck.

The `sch_htb: quantum ... is big` messages seen on the VM are warnings; the run completed and wrote the above results.

