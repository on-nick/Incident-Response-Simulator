import random
import uuid
from datetime import datetime
randoms = random.randint(1,225)
event_id = str(uuid.uuid4().hex[:8])
timestamp= datetime.now().isoformat()
def make_fake_event():
    event={
    "event_id": f"evt-{event_id}",
    "scenario":"port-scan",
    "time-stamp": timestamp,
    "src_ip":f"192.168.1.{randoms}",
    "port": random.randint(20,100)
      }
    return event
# Initialize an empty list to store events
events = []

# Generate 10 fake events and append them to the events list
for _ in range(10):
    events.append(make_fake_event())

# Print all generated events
print("Generated Events:")
for event in events:
    print(event)

# Initialize a counter for port scan events
port_scan_count = 0

# Count the number of port scan events
for event in events:
    if event["scenario"] == "port-scan":  # Check if the scenario is "port-scan"
        port_scan_count += 1

# Print the total number of port scan events
print(f"\nTotal port scan events: {port_scan_count}")

# Collect all ports from the events
ports = []
for event in events:
    ports.append(event["port"])

# Get unique ports using a set
unique_ports = set(ports)

# Print summary of events and ports
print("\nSummary:")
print(f"Total events: {len(events)}")
print(f"Port scan events: {port_scan_count}")
print(f"{len(unique_ports)} distinct ports out of {len(ports)} total ports")
