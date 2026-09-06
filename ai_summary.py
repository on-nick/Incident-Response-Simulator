"""
ai_summary.py
-------------
Generates a short, human-readable incident summary — the kind a SOC
analyst would write in a ticket. If ANTHROPIC_API_KEY is set (via
config.py / .env), it calls the Claude API for a genuinely generated
summary. If not, it falls back to a template-based summary built from
the incident data, so the feature degrades gracefully rather than
breaking the app for anyone who clones the repo without a key.

The API key is read server-side only (via config.py) and never sent to
or exposed in the frontend.
"""
import json

from config import AI_SUMMARIES_ENABLED, ANTHROPIC_API_KEY

_SYSTEM_PROMPT = (
    "You are a security analyst writing a brief incident note for a "
    "SOC ticket. Given JSON describing a simulated security incident "
    "(scenario, events, alerts, response steps), write a 2-3 sentence "
    "plain-English summary: what happened, why it was flagged, and what "
    "was done about it. Be concise and factual. Do not use markdown "
    "formatting, headers, or bullet points — plain prose only."
)


def _fallback_summary(incident):
    """Rule-based summary used when no API key is configured, or if the
    API call fails for any reason. Deliberately simple and dependable."""
    scenario = incident.get("scenario", "unknown").replace("_", " ")
    alerts = incident.get("alerts", [])
    response = incident.get("response", [])
    event_count = len(incident.get("events", []))

    if not alerts:
        return (
            f"A {scenario} simulation generated {event_count} event(s) "
            f"but did not cross any detection threshold — no alert was "
            f"raised and no response playbook ran."
        )

    alert = alerts[0]
    severity = alert.get("severity", "UNKNOWN")
    message = alert.get("message", "")
    step_count = len(response)

    return (
        f"A {severity.lower()}-severity {scenario} incident was detected: "
        f"{message}. {step_count} automated response step(s) were executed "
        f"in reaction to the {event_count} observed event(s)."
    )


def _call_claude(incident):
    """Attempts a real API call. Returns None on any failure so the
    caller can fall back cleanly — this function must never raise."""
    try:
        import urllib.request
        import urllib.error

        body = json.dumps({
            "model": "claude-sonnet-4-6",
            "max_tokens": 200,
            "system": _SYSTEM_PROMPT,
            "messages": [
                {"role": "user", "content": json.dumps(incident, default=str)}
            ],
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            parts = [
                block.get("text", "")
                for block in data.get("content", [])
                if block.get("type") == "text"
            ]
            text = "".join(parts).strip()
            return text or None

    except Exception:
        # Network error, bad key, rate limit, malformed response, etc.
        # We never want a broken/missing AI summary to fail the whole
        # simulation request — fall back instead.
        return None


def generate_summary(incident):
    """Public entry point. Always returns a string, never raises."""
    if AI_SUMMARIES_ENABLED:
        result = _call_claude(incident)
        if result:
            return {"text": result, "source": "ai"}

    return {"text": _fallback_summary(incident), "source": "rule_based"}
