"""
simulator.py
------------
Generates synthetic security-event data for each scenario. All four
scenario functions accept `target_ip` so a caller (app.py) can pass
through whatever the user specified in the UI, after it's been checked
by safety.check_target(). No packets are sent by these — they only
build event dictionaries, which is enough to exercise detection and
response logic.

run_live_port_test() is the one function that sends a real packet, and
even then only ever to a target that has already passed the safety
check.
"""
import random
import uuid
from datetime import datetime, timezone

from scapy.all import IP, TCP, send

from safety import check_target


def _now():
    return datetime.now(timezone.utc).isoformat()


def _synthetic_src_ip():
    return f"192.168.1.{random.randint(1, 254)}"


def run_port_scan(target_ip="127.0.0.1", num_ports=10):
    events = []
    ports = random.sample(
        [21, 22, 23, 25, 53, 80, 110, 443, 8080, 8443],
        k=min(num_ports, 10),
    )
    for port in ports:
        events.append({
            "event_id": f"evt-{uuid.uuid4().hex[:8]}",
            "scenario": "port_scan",
            "timestamp": _now(),
            "src_ip": _synthetic_src_ip(),
            "dst_ip": target_ip,
            "port": port,
        })
    return events


def run_syn_flood_lite(target_ip="127.0.0.1", num_events=10):
    events = []
    for _ in range(num_events):
        events.append({
            "event_id": f"evt-{uuid.uuid4().hex[:8]}",
            "scenario": "syn_flood_lite",
            "timestamp": _now(),
            "src_ip": _synthetic_src_ip(),
            "dst_ip": target_ip,
            "dst_port": 80,
        })
    return events


def run_brute_force_login(target_ip="127.0.0.1", num_attempts=10):
    events = []
    usernames = ["admin", "root", "user", "test"]
    for _ in range(num_attempts):
        events.append({
            "event_id": f"evt-{uuid.uuid4().hex[:8]}",
            "scenario": "brute_force_login",
            "timestamp": _now(),
            "src_ip": _synthetic_src_ip(),
            "dst_ip": target_ip,
            "username": random.choice(usernames),
            "result": "failed",
        })
    return events


def run_malware_beacon(target_ip="127.0.0.1", num_events=10):
    events = []
    src_ip = _synthetic_src_ip()
    for _ in range(num_events):
        events.append({
            "event_id": f"evt-{uuid.uuid4().hex[:8]}",
            "scenario": "malware_beacon",
            "timestamp": _now(),
            "src_ip": src_ip,
            "dst_ip": target_ip,
            "dst_port": random.choice([80, 443]),
            "protocol": "HTTPS",
        })
    return events


def run_live_port_test(target_ip="127.0.0.1", port=80):
    """Sends one real SYN packet. Only ever called against a target that
    has already passed safety.check_target()."""
    ok, reason = check_target(target_ip)
    if not ok:
        raise ValueError(reason)

    packet = IP(dst=target_ip) / TCP(dport=port, flags="S")
    send(packet, verbose=False)

    return {
        "target": target_ip,
        "port": port,
        "protocol": "TCP",
        "flags": "SYN",
        "mode": "live",
    }


SCENARIOS = {
    "port_scan": run_port_scan,
    "syn_flood_lite": run_syn_flood_lite,
    "brute_force_login": run_brute_force_login,
    "malware_beacon": run_malware_beacon,
}
