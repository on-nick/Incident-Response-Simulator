"""
config.py
---------
Central place for tunable values so nobody has to hunt through detector.py
or app.py to find a magic number. Reads optional overrides from environment
variables (via a .env file in development) so secrets and per-deploy tuning
never need to be hardcoded or committed.
"""
import os
from dotenv import load_dotenv

load_dotenv()  # loads .env if present; harmless no-op if it isn't


def _env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------
# Detection thresholds — how many events of a given scenario must occur
# before the detector raises an alert. Lower = more sensitive (more
# false positives). Higher = less sensitive (more missed detections).
# ---------------------------------------------------------------------
THRESHOLDS = {
    "port_scan": {
        "distinct_ports": _env_int("THRESHOLD_PORT_SCAN_PORTS", 5),
    },
    "syn_flood_lite": {
        "event_count": _env_int("THRESHOLD_SYN_FLOOD_EVENTS", 10),
    },
    "brute_force_login": {
        "failed_attempts": _env_int("THRESHOLD_BRUTE_FORCE_ATTEMPTS", 5),
    },
    "malware_beacon": {
        "beacon_count": _env_int("THRESHOLD_MALWARE_BEACON_COUNT", 3),
    },
}

SEVERITY_BY_SCENARIO = {
    "port_scan": "MEDIUM",
    "syn_flood_lite": "HIGH",
    "brute_force_login": "HIGH",
    "malware_beacon": "CRITICAL",
}

# ---------------------------------------------------------------------
# Safety: which addresses simulations are allowed to target.
# 127.0.0.1 is always implicitly allowed. Add any additional lab-only
# private addresses here (must be RFC1918 or loopback — enforced in
# safety.py regardless of what's listed here).
# ---------------------------------------------------------------------
LAB_TARGETS = {"127.0.0.1"}

# ---------------------------------------------------------------------
# Feature flags / integrations
# ---------------------------------------------------------------------
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
AI_SUMMARIES_ENABLED = bool(ANTHROPIC_API_KEY)

RATE_LIMIT_SIMULATE = os.environ.get("RATE_LIMIT_SIMULATE", "20 per minute")

DATABASE_PATH = os.environ.get("DATABASE_PATH", "data/incidents.db")

APP_START_TIME = None  # set at app startup in app.py, used by /api/health
