import uuid
from datetime import datetime

from flask import Flask, jsonify, request, render_template

from simulator import SCENARIOS
from detector import analyze
from responder import execute_playbook
from storage import save_incident, load_incidents
app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/about")
def about():
    return "Incident Response Simulation Tool"


@app.route("/api/ping")
def ping():
    return jsonify({
        "status": "alive"
    })


@app.route("/api/echo", methods=["POST"])
def echo():
    data = request.get_json()

    return jsonify(data)

@app.route("/api/incidents", methods=["GET"])
def get_incidents():

    incidents = load_incidents()

    return jsonify(incidents)

@app.route("/api/simulate", methods=["POST"])
def simulate():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body must contain JSON"
        }), 400

    scenario = data.get("scenario")

    if not scenario:
        return jsonify({
            "error": "Scenario is required"
        }), 400

    if scenario not in SCENARIOS:
        return jsonify({
            "error": "Unknown scenario",
            "available_scenarios": list(SCENARIOS.keys())
        }), 400

    # -------------------------
    # 1. Generate events
    # -------------------------

    events = SCENARIOS[scenario]()

    # -------------------------
    # 2. Detect threats
    # -------------------------

    detection_start = datetime.now()

    alerts = analyze(scenario, events)

    detection_end = datetime.now()

    detection_latency = (
        detection_end - detection_start
    ).total_seconds() * 1000

    # -------------------------
    # 3. Execute response
    # -------------------------

    response_start = datetime.now()

    response_steps = []

    for alert in alerts:
        steps = execute_playbook(alert)
        response_steps.extend(steps)

    response_end = datetime.now()

    response_time = (
        response_end - response_start
    ).total_seconds() * 1000

    # -------------------------
    # 4. Create incident
    # -------------------------

    incident = {
        "incident_id": f"inc-{uuid.uuid4().hex[:8]}",
        "timestamp": datetime.now().isoformat(),
        "scenario": scenario,
        "events": events,
        "alerts": alerts,
        "response": response_steps,
        "metrics": {
            "detection_latency_ms": detection_latency,
            "response_time_ms": response_time
        }
    }

    # -------------------------
    # 5. Save incident
    # -------------------------

    save_incident(incident)

    # -------------------------
    # 6. Return result
    # -------------------------

    return jsonify(incident)


@app.route("/api/metrics", methods=["GET"])
def get_metrics():

    incidents = load_incidents()

    total_incidents = len(incidents)

    if total_incidents == 0:
        return jsonify({
            "total_incidents": 0,
            "detection_rate": 0,
            "average_detection_latency_ms": 0,
            "average_response_time_ms": 0
        })

    detected_incidents = 0

    detection_latencies = []
    response_times = []

    for incident in incidents:

        # Count incidents that generated at least one alert
        if incident.get("alerts"):
            detected_incidents += 1

        metrics = incident.get("metrics", {})

        detection_latency = metrics.get(
            "detection_latency_ms"
        )

        response_time = metrics.get(
            "response_time_ms"
        )

        if detection_latency is not None:
            detection_latencies.append(detection_latency)

        if response_time is not None:
            response_times.append(response_time)

    # Calculate detection rate
    detection_rate = (
        detected_incidents / total_incidents
    ) * 100

    # Calculate averages
    average_detection_latency = (
        sum(detection_latencies) / len(detection_latencies)
        if detection_latencies
        else 0
    )

    average_response_time = (
        sum(response_times) / len(response_times)
        if response_times
        else 0
    )

    return jsonify({
        "total_incidents": total_incidents,
        "detected_incidents": detected_incidents,
        "detection_rate": round(detection_rate, 2),
        "average_detection_latency_ms": round(
            average_detection_latency, 2
        ),
        "average_response_time_ms": round(
            average_response_time, 2
        )
    })

if __name__ == "__main__":
    app.run(debug=True)