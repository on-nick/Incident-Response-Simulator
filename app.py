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

    # 1. Generate events
    events = SCENARIOS[scenario]()

    # 2. Detect threats
    alerts = analyze(scenario, events)

    # 3. Execute response playbooks
    response_steps = []

    for alert in alerts:
        steps = execute_playbook(alert)
        response_steps.extend(steps)

   # Create incident record
    incident = {
        "scenario": scenario,
        "events": events,
        "alerts": alerts,
        "response": response_steps
    }

    # Save incident permanently
    save_incident(incident)

    # Return incident
    return jsonify(incident)
    



if __name__ == "__main__":
    app.run(debug=True)