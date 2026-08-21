import random
import uuid
from datetime import datetime

def run_port_scan(target_ip="127.0.0.1", num_ports=10):

    events = []

    for _ in range(num_ports):

        event = {
            "event_id": f"evt-{uuid.uuid4().hex[:8]}",
            "scenario": "port_scan",
            "timestamp": datetime.now().isoformat(),
            "src_ip": "127.0.0.1",
            "dst_ip": target_ip,
            "port": random.choice([
                21, 22, 23, 25, 53,
                80, 110, 443, 8080, 8443
            ])
        }

        events.append(event)

    return events

if __name__ == "__main__":

    events = run_port_scan()

    print(f"Generated {len(events)} events")

    for event in events:
        print(event)