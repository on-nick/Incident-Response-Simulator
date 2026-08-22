import json
import os


DATA_FILE = "data/incidents.json"


def load_incidents():
    """
    Load all incidents from the JSON file.
    """

    if not os.path.exists(DATA_FILE):
        return []

    with open(DATA_FILE, "r") as file:
        return json.load(file)


def save_incident(incident):
    """
    Append one incident to the existing incident history.
    """

    incidents = load_incidents()

    incidents.append(incident)

    os.makedirs("data", exist_ok=True)

    with open(DATA_FILE, "w") as file:
        json.dump(incidents, file, indent=4)