from detector import analyze
from simulator import run_port_scan


# Response playbooks for each scenario
PLAYBOOKS = {
    "port_scan": [
        "Log source IP",
        "Investigate scanning activity",
        "Block source IP",
        "Create incident record"
    ],

    "syn_flood_lite": [
        "Log source IP",
        "Check connection volume",
        "Apply rate limiting",
        "Create incident record"
    ],

    "brute_force_login": [
        "Log source IP",
        "Review failed login attempts",
        "Temporarily lock affected account",
        "Create incident record"
    ],

    "malware_beacon": [
        "Log source IP",
        "Investigate beacon activity",
        "Isolate affected host",
        "Create incident record"
    ]
}


def execute_playbook(alert):
    """
    Execute the response playbook associated
    with a security alert.
    """

    scenario = alert["scenario"]

    # Get the playbook for this scenario.
    # If it doesn't exist, return an empty list.
    steps = PLAYBOOKS.get(scenario, [])

    completed_steps = []

    for step in steps:

        completed_steps.append({
            "step": step,
            "status": "done"
        })

    return completed_steps


if __name__ == "__main__":

    # Generate simulated port-scan events
    events = run_port_scan()

    print("Generated events:")
    print(len(events))

    # Analyze the events
    alerts = analyze("port_scan", events)

    print("\nAlerts:")
    print(alerts)

    # Execute response playbooks
    for alert in alerts:

        print("\nExecuting playbook...")

        completed_steps = execute_playbook(alert)

        for step in completed_steps:
            print(step)