import uuid

from simulator import run_port_scan


def analyze(scenario, events):
    alerts = []

    if scenario == "port_scan":

        ports = []

        for event in events:
            ports.append(event["port"])

        unique_ports = set(ports)

        if len(unique_ports) >= 5:

            alert = {
                "alert_id": f"alert-{uuid.uuid4().hex[:8]}",
                "scenario": "port_scan",
                "severity": "HIGH",
                "message": (
                    f"Port scan detected across "
                    f"{len(unique_ports)} distinct ports"
                )
            }

            alerts.append(alert)

    return alerts


if __name__ == "__main__":

    test_events = [
        {"port": 21},
        {"port": 22},
        {"port": 23},
        {"port": 80},
        {"port": 443},
        {"port": 8080},
    ]

    alerts = analyze("port_scan", test_events)

    print("Alerts:")

    for alert in alerts:
        print(alert)