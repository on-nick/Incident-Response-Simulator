"""
app.py
------
Flask routes for the Incident Response Simulator.
or rule-based fallback) summary.
"""
import json
import logging
import time
import uuid
from datetime import datetime, timezone

from flask import Flask, jsonify, request, render_template, Response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from simulator import SCENARIOS
from detector import analyze
from responder import execute_playbook
from safety import check_target
from ai_summary import generate_summary
import storage
import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("ir_simulator")

app = Flask(__name__)
app.start_time = time.time()

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)


# ---------------------------------------------------------------------
# Error handlers — make sure nothing ever surfaces as a raw traceback
# or Flask's default HTML error page, since this is a JSON API.
# ---------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not found"}), 404
    return e


@app.errorhandler(429)
def rate_limited(e):
    return jsonify({"error": "Too many requests. Please slow down."}), 429


@app.errorhandler(500)
def server_error(e):
    logger.exception("Unhandled server error")
    return jsonify({"error": "Internal server error"}), 500


# ---------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html", ai_enabled=config.AI_SUMMARIES_ENABLED)


@app.route("/about")
def about():
    return render_template("about.html")


# ---------------------------------------------------------------------
# Health / status
# ---------------------------------------------------------------------
@app.route("/api/health")
def health():
    try:
        incident_count = storage.count_incidents()
        db_ok = True
    except Exception:
        logger.exception("Health check: database unavailable")
        incident_count = None
        db_ok = False

    uptime_s = round(time.time() - app.start_time, 1)

    return jsonify({
        "status": "ok" if db_ok else "degraded",
        "uptime_seconds": uptime_s,
        "incident_count": incident_count,
        "ai_summaries_enabled": config.AI_SUMMARIES_ENABLED,
    })


@app.route("/api/ping")
def ping():
    return jsonify({"status": "alive"})


@app.route("/api/echo", methods=["POST"])
def echo():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400
    return jsonify(data)


# ---------------------------------------------------------------------
# Incidents
# ---------------------------------------------------------------------
@app.route("/api/incidents", methods=["GET"])
def get_incidents():
    try:
        incidents = storage.load_incidents()
        return jsonify(incidents)
    except Exception:
        logger.exception("Failed to load incidents")
        return jsonify({"error": "Could not load incident history"}), 500


@app.route("/api/incidents", methods=["DELETE"])
def delete_incidents():
    try:
        storage.clear_incidents()
        logger.info("Incident history cleared by %s", get_remote_address())
        return jsonify({"status": "cleared"})
    except Exception:
        logger.exception("Failed to clear incidents")
        return jsonify({"error": "Could not clear incident history"}), 500


# ---------------------------------------------------------------------
# Core simulation logic (shared by /api/simulate and the streaming route)
# ---------------------------------------------------------------------
def _validate_request(data):
    """Returns (scenario, target, error_response_or_None)."""
    if not data:
        return None, None, (jsonify({"error": "Request body must contain JSON"}), 400)

    scenario = data.get("scenario")
    if not scenario:
        return None, None, (jsonify({"error": "'scenario' is required"}), 400)

    if scenario not in SCENARIOS:
        return None, None, (jsonify({
            "error": f"Unknown scenario '{scenario}'",
            "available_scenarios": list(SCENARIOS.keys()),
        }), 400)

    target = data.get("target", "127.0.0.1") or "127.0.0.1"
    is_safe, reason = check_target(target)
    if not is_safe:
        return None, None, (jsonify({"error": reason}), 400)

    return scenario, target, None


def _build_incident(scenario, target, events):
    detection_start = time.perf_counter()
    alerts = analyze(scenario, events)
    detection_latency_ms = (time.perf_counter() - detection_start) * 1000

    response_start = time.perf_counter()
    response_steps = []
    for alert in alerts:
        response_steps.extend(execute_playbook(alert))
    response_time_ms = (time.perf_counter() - response_start) * 1000

    incident = {
        "incident_id": f"inc-{uuid.uuid4().hex[:8]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scenario": scenario,
        "target": target,
        "events": events,
        "alerts": alerts,
        "response": response_steps,
        "metrics": {
            "detection_latency_ms": round(detection_latency_ms, 3),
            "response_time_ms": round(response_time_ms, 3),
        },
    }

    summary = generate_summary(incident)
    incident["ai_summary"] = summary

    return incident


@app.route("/api/simulate", methods=["POST"])
@limiter.limit(config.RATE_LIMIT_SIMULATE)
def simulate():
    data = request.get_json(silent=True)
    scenario, target, error = _validate_request(data)
    if error:
        return error

    try:
        events = SCENARIOS[scenario](target_ip=target)
    except Exception:
        logger.exception("Simulation failed for scenario=%s target=%s", scenario, target)
        return jsonify({"error": "Simulation failed"}), 500

    incident = _build_incident(scenario, target, events)

    try:
        storage.save_incident(incident)
    except Exception:
        logger.exception("Failed to save incident %s", incident["incident_id"])
        return jsonify({"error": "Incident generated but could not be saved"}), 500

    logger.info(
        "scenario=%s target=%s events=%d alerts=%d response_steps=%d",
        scenario, target, len(events), len(incident["alerts"]), len(incident["response"]),
    )

    return jsonify(incident)


@app.route("/api/simulate/stream", methods=["POST"])
@limiter.limit(config.RATE_LIMIT_SIMULATE)
def simulate_stream():
    """Server-Sent Events variant: streams each event as it's generated,
    then detection results, response steps, and the final incident with
    its AI summary. Consumed by the frontend via fetch() + a stream
    reader (not EventSource, since we need to POST a body)."""
    data = request.get_json(silent=True)
    scenario, target, error = _validate_request(data)
    if error:
        body, status = error
        return jsonify(json.loads(body.get_data())), status

    def sse(event_type, payload):
        return f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"

    def generate():
        try:
            events = SCENARIOS[scenario](target_ip=target)
        except Exception:
            logger.exception("Streaming simulation failed for scenario=%s", scenario)
            yield sse("error", {"error": "Simulation failed"})
            return

        for event in events:
            yield sse("event", event)
            time.sleep(0.12)  # small pacing delay so the stream is visibly "live"

        incident = _build_incident(scenario, target, events)

        try:
            storage.save_incident(incident)
        except Exception:
            logger.exception("Failed to save streamed incident")
            yield sse("error", {"error": "Incident generated but could not be saved"})
            return

        for alert in incident["alerts"]:
            yield sse("alert", alert)
            time.sleep(0.1)

        for step in incident["response"]:
            yield sse("response_step", step)
            time.sleep(0.08)

        yield sse("summary", incident["ai_summary"])
        yield sse("done", incident)

        logger.info(
            "STREAM scenario=%s target=%s events=%d alerts=%d",
            scenario, target, len(events), len(incident["alerts"]),
        )

    return Response(generate(), mimetype="text/event-stream")


# ---------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------
@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    try:
        incidents = storage.load_incidents()
    except Exception:
        logger.exception("Failed to load incidents for metrics")
        return jsonify({"error": "Could not load metrics"}), 500

    total_incidents = len(incidents)

    if total_incidents == 0:
        return jsonify({
            "total_incidents": 0,
            "detected_incidents": 0,
            "total_alerts": 0,
            "detection_rate": 0,
            "average_detection_latency_ms": 0,
            "average_response_time_ms": 0,
            "by_scenario": {},
        })

    detected_incidents = 0
    total_alerts = 0
    detection_latencies = []
    response_times = []
    by_scenario = {}

    for incident in incidents:
        scenario = incident.get("scenario", "unknown")
        by_scenario.setdefault(scenario, {"count": 0, "detected": 0})
        by_scenario[scenario]["count"] += 1

        alerts = incident.get("alerts") or []
        total_alerts += len(alerts)
        if alerts:
            detected_incidents += 1
            by_scenario[scenario]["detected"] += 1

        metrics = incident.get("metrics", {})
        if metrics.get("detection_latency_ms") is not None:
            detection_latencies.append(metrics["detection_latency_ms"])
        if metrics.get("response_time_ms") is not None:
            response_times.append(metrics["response_time_ms"])

    detection_rate = (detected_incidents / total_incidents) * 100
    avg_latency = sum(detection_latencies) / len(detection_latencies) if detection_latencies else 0
    avg_response = sum(response_times) / len(response_times) if response_times else 0

    return jsonify({
        "total_incidents": total_incidents,
        "detected_incidents": detected_incidents,
        "total_alerts": total_alerts,
        "detection_rate": round(detection_rate, 2),
        "average_detection_latency_ms": round(avg_latency, 2),
        "average_response_time_ms": round(avg_response, 2),
        "by_scenario": by_scenario,
    })


if __name__ == "__main__":
    storage.init_db()
    logger.info("Starting Incident Response Simulator (AI summaries: %s)",
                "enabled" if config.AI_SUMMARIES_ENABLED else "disabled (fallback mode)")
    app.run(debug=True)
