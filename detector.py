"""
detector.py
-----------
Rule-based detection engine. analyze(scenario, events) dispatches to a
per-scenario detector function via the DETECTORS table below, rather
than a long if/elif chain — adding a 5th scenario later just means
writing one function and registering it here.

Each detector function takes the raw event list for one simulation run
and returns a list of alert dicts (usually 0 or 1 element).
"""
import uuid

from alert import Alert
from config import THRESHOLDS, SEVERITY_BY_SCENARIO


def _make_alert(scenario, message):
    alert = Alert(
        scenario=scenario,
        severity=SEVERITY_BY_SCENARIO.get(scenario, "MEDIUM"),
        message=message,
    )
    return {
        "alert_id": f"alert-{uuid.uuid4().hex[:8]}",
        **alert.to_dict(),
    }


def _detect_port_scan(events):
    ports = {e["port"] for e in events if "port" in e}
    threshold = THRESHOLDS["port_scan"]["distinct_ports"]

    if len(ports) >= threshold:
        return [_make_alert(
            "port_scan",
            f"Port scan detected across {len(ports)} distinct ports "
            f"(threshold: {threshold})",
        )]
    return []


def _detect_syn_flood(events):
    threshold = THRESHOLDS["syn_flood_lite"]["event_count"]

    if len(events) >= threshold:
        dst_port = events[0].get("dst_port", "?") if events else "?"
        return [_make_alert(
            "syn_flood_lite",
            f"SYN flood pattern detected — {len(events)} SYN packets "
            f"observed to port {dst_port} (threshold: {threshold})",
        )]
    return []


def _detect_brute_force(events):
    failed = [e for e in events if e.get("result") == "failed"]
    threshold = THRESHOLDS["brute_force_login"]["failed_attempts"]

    if len(failed) >= threshold:
        usernames = {e.get("username") for e in failed if e.get("username")}
        return [_make_alert(
            "brute_force_login",
            f"Credential brute-force detected — {len(failed)} failed "
            f"login attempts across {len(usernames)} distinct username(s) "
            f"(threshold: {threshold})",
        )]
    return []


def _detect_malware_beacon(events):
    threshold = THRESHOLDS["malware_beacon"]["beacon_count"]

    if len(events) >= threshold:
        dst_port = events[0].get("dst_port", "?") if events else "?"
        protocol = events[0].get("protocol", "?") if events else "?"
        return [_make_alert(
            "malware_beacon",
            f"Periodic beacon activity detected — {len(events)} callbacks "
            f"over {protocol} to port {dst_port}, consistent with "
            f"malware command-and-control traffic (threshold: {threshold})",
        )]
    return []


DETECTORS = {
    "port_scan": _detect_port_scan,
    "syn_flood_lite": _detect_syn_flood,
    "brute_force_login": _detect_brute_force,
    "malware_beacon": _detect_malware_beacon,
}


def analyze(scenario, events):
    """Dispatch to the correct per-scenario detector. Returns an empty
    list (never raises) for an unrecognized scenario or empty event list,
    so callers don't need extra guards."""
    if not events:
        return []

    detector_fn = DETECTORS.get(scenario)
    if detector_fn is None:
        return []

    return detector_fn(events)


if __name__ == "__main__":
    test_events = [
        {"port": 21}, {"port": 22}, {"port": 23},
        {"port": 80}, {"port": 443}, {"port": 8080},
    ]
    print("port_scan alerts:", analyze("port_scan", test_events))
