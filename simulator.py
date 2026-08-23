import random
import uuid
from datetime import datetime

from scapy.all import IP, TCP, send
from safety import is_safe_target


def run_port_scan(target_ip="127.0.0.1", num_ports=10):

    events = []

    for _ in range(num_ports):

        event = {
            "event_id": f"evt-{uuid.uuid4().hex[:8]}",
            "scenario": "port_scan",
            "timestamp": datetime.now().isoformat(),
            "src_ip": f"192.168.1.{random.randint(1, 254)}",
            "dst_ip": target_ip,
            "port": random.choice([
                21, 22, 23, 25, 53,
                80, 110, 443, 8080, 8443
            ])
        }

        events.append(event)

    return events


def run_syn_flood_lite(target_ip="127.0.0.1", num_events=10):

    events = []

    for _ in range(num_events):

        event = {
            "event_id": f"evt-{uuid.uuid4().hex[:8]}",
            "scenario": "syn_flood_lite",
            "timestamp": datetime.now().isoformat(),
            "src_ip": f"192.168.1.{random.randint(1, 254)}",
            "dst_ip": target_ip,
            "dst_port": 80
        }

        events.append(event)

    return events


def run_brute_force_login(target_ip="127.0.0.1", num_attempts=10):

    events = []

    for _ in range(num_attempts):

        event = {
            "event_id": f"evt-{uuid.uuid4().hex[:8]}",
            "scenario": "brute_force_login",
            "timestamp": datetime.now().isoformat(),
            "src_ip": f"192.168.1.{random.randint(1, 254)}",
            "dst_ip": target_ip,
            "username": random.choice([
                "admin",
                "root",
                "user",
                "test"
            ]),
            "result": "failed"
        }

        events.append(event)

    return events


def run_malware_beacon(target_ip="127.0.0.1", num_events=10):

    events = []

    for _ in range(num_events):

        event = {
            "event_id": f"evt-{uuid.uuid4().hex[:8]}",
            "scenario": "malware_beacon",
            "timestamp": datetime.now().isoformat(),
            "src_ip": "192.168.1.50",
            "dst_ip": target_ip,
            "dst_port": random.choice([80, 443]),
            "protocol": "HTTPS"
        }

        events.append(event)

    return events


def run_live_port_test(target_ip="127.0.0.1", port=80):

    if not is_safe_target(target_ip):

        raise ValueError(
            "Live mode only allows target 127.0.0.1"
        )

    packet = IP(dst=target_ip) / TCP(
        dport=port,
        flags="S"
    )

    send(packet, verbose=False)

    return {
        "target": target_ip,
        "port": port,
        "protocol": "TCP",
        "flags": "SYN",
        "mode": "live"
    }


SCENARIOS = {
    "port_scan": run_port_scan,
    "syn_flood_lite": run_syn_flood_lite,
    "brute_force_login": run_brute_force_login,
    "malware_beacon": run_malware_beacon
}


if __name__ == "__main__":

    print("Available scenarios:")

    for scenario in SCENARIOS:
        print("-", scenario)

    print("\nTesting malware_beacon:")

    events = SCENARIOS["malware_beacon"]()

    print(f"Generated {len(events)} events")

    for event in events:
        print(event)

    print("\nTesting live localhost packet:")

    result = run_live_port_test(
        target_ip="127.0.0.1",
        port=80
    )

    print(result)