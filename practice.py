import random
import uuid
import json
from datetime import datetime


def make_fake_event():
    randoms = random.randint(1, 225)
    event_id = str(uuid.uuid4().hex[:8])
    timestamp = datetime.now().isoformat()

    event = {
        "event_id": f"evt-{event_id}",
        "scenario": "port_scan",
        "timestamp": timestamp,
        "src_ip": f"192.168.1.{randoms}",
        "port": random.randint(20, 100)
    }

    return event


# Generate 10 fake events
events = []

for _ in range(10):
    events.append(make_fake_event())


# Print generated events
print("Generated Events:")

for event in events:
    print(event)


# Count port scan events
port_scan_count = 0

for event in events:
    if event["scenario"] == "port_scan":
        port_scan_count += 1


print(f"\nTotal port scan events: {port_scan_count}")


# Collect ports
ports = []

for event in events:
    ports.append(event["port"])


# Find unique ports
unique_ports = set(ports)


print("\nSummary:")
print(f"Total events: {len(events)}")
print(f"Port scan events: {port_scan_count}")
print(f"{len(unique_ports)} distinct ports out of {len(ports)} total ports")


# Save events
def save_events(events):
    with open("data/incidents.json", "w") as file:
        json.dump(events, file, indent=4)


# Load events
def load_events():
    with open("data/incidents.json", "r") as file:
        return json.load(file)


# Save generated events
save_events(events)

print("\nEvents saved successfully.")


# Load saved events
loaded_events = load_events()

print(f"Loaded {len(loaded_events)} events from JSON.")