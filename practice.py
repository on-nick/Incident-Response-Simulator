import random
import uuid
from datetime import datetime
randoms = random.randint(1,225)
event_id = str(uuid.uuid4().hex[:8])
timestamp= datetime.now().isoformat()

def make_fake_event():
    event={
    "event_id": f"evt-{event_id}",
    "scenario ":"port-scan",
    "time-stamp": timestamp,
    "src_ip":f"192.168.1.{randoms}"
      }
    return event
for _ in range(5):
    print(make_fake_event())
