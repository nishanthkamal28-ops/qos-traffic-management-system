# QoS Traffic Management System – D1 (Member 2: Mininet + Testing)

## 1. Scope of Member 2 in D1
Maps to rubric rows: *Problem Understanding & Architecture* (network part), *Mininet + SDN Implementation* (topology, links, host/switch connectivity), *Initial Testing & Demo* (network verification). Integration rows are shared with Members 1 and 3.

## 2. Network architecture

```
h1 (Class A real-time)  --\
h2 (Class B streaming)  ----- s1 ====[bottleneck 10 Mbps, 10 ms, queue 100]==== s2 ---- h4 (UDP server)
h3 (Class C bulk)       --/
          100 Mbps / 1 ms access links                                  100 Mbps / 1 ms
```

- **Why a dumbbell:** all classes share one bottleneck, so congestion is easy to create and fairness between classes is directly measurable.
- **Controller:** remote OpenFlow 1.3 controller (Member 3, e.g. Ryu) at 127.0.0.1:6653, controlling s1 and s2.
- **Baseline mode:** `--baseline` runs the same topology with standalone learning switches (no SDN) – the comparison baseline for D2.

## 3. Interface contract (agree with Members 1 and 3)

| Host | IP | Traffic class | UDP dst port |
|------|----|---------------|--------------|
| h1 | 10.0.0.1 | A – real-time (small, frequent packets) | 5001 |
| h2 | 10.0.0.2 | B – streaming (medium) | 5002 |
| h3 | 10.0.0.3 | C – bulk (large, high rate) | 5003 |
| h4 | 10.0.0.4 | UDP server | – |

The controller can classify on UDP dst port (Member 3). Member 1's app must use these ports.

## 4. Link parameters
| Link | Bandwidth | Delay | Queue | Purpose |
|------|-----------|-------|-------|---------|
| host–switch | 100 Mbps | 1 ms | default | never the bottleneck |
| s1–s2 | 10 Mbps (configurable) | 10 ms | 100 pkts | congestion point |

Change with `--bw`, `--delay`, `--loss`, `--queue`.

## 5. How to run
```bash
# Terminal 1: SDN controller (Member 3's code)
ryu-manager controller.py          # listens on 6653

# Terminal 2: topology + CLI
sudo python3 topology.py

# Terminal 3: automated D1 tests
sudo python3 d1_tests.py           # SDN mode
sudo python3 d1_tests.py --baseline
sudo mn -c                         # cleanup between runs
```
Until the controller exists, use `--baseline` to validate the topology alone.

## 6. D1 test cases
| ID | Test | Expected |
|----|------|----------|
| T1 | `pingall` | 0% loss |
| T2 | Idle RTT h1→h4 | ≈ 24 ms (2×(1+10+1) ms) |
| T3 | One UDP flow at 80% of bottleneck | ~8 Mbps received, ~0% loss |
| T4 | Three UDP flows at 70% each (21 Mbps offered) | Total throughput capped near 10 Mbps, high loss → congestion confirmed |

Output saved to `results/d1_<mode>.txt`. Screenshots to capture for the demo: `net`/`dump` output, T1–T4 results, `ovs-ofctl -O OpenFlow13 dump-flows s1` (once the controller is running).

## 7. D1 demo checklist
- [ ] Topology starts, controller connects to s1 and s2
- [ ] `pingall` 0% loss
- [ ] Bottleneck verified (T3 vs T4)
- [ ] Baseline result recorded (no priority, all classes lose equally)
- [ ] Flow rules visible on switches (with Member 3)

## 8. Planned for D2 (not part of D1)
Controlled loss scenario (`--loss`), link failure (`link s1 s2 down`), per-class throughput/latency/loss/Jain's fairness measurements, SDN vs baseline comparison graphs.

