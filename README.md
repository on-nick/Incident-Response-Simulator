# Incident Response Simulator

A Flask-based training tool that simulates security incidents, runs them
through a rule-based detection engine, and executes automated response
playbooks — the same shape of pipeline a real SOC (security operations
center) uses, small enough to run and inspect on your own machine.

## Features

- **Four scenarios**: port scan, SYN flood (lite), brute-force login,
  malware beacon — each generates realistic synthetic event data.
- **Rule-based detection** with per-scenario thresholds (all four scenarios
  correctly produce alerts and trigger a response — see "What changed"
  below).
- **Automated response playbooks** — each alert triggers a scenario-specific
  sequence of response steps (block IP, lock account, isolate host, etc.).
- **Live streaming simulation** — watch events arrive one at a time, then
  detection and response fire in real time, over Server-Sent Events.
- **AI-generated incident summaries** — a short, analyst-style write-up per
  incident. Uses the Claude API if `ANTHROPIC_API_KEY` is set; otherwise
  falls back to a dependable rule-based summary automatically.
- **Metrics dashboard** — detection rate, average detection latency, average
  response time, a per-scenario breakdown, and a response-time trend chart.
- **SQLite persistence** — incident history survives restarts and handles
  concurrent writes safely (previously a flat JSON file rewritten in full on
  every save).

## Running it

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000**.

To enable real AI-generated summaries (optional):
```bash
cp .env.example .env
# then edit .env and set ANTHROPIC_API_KEY=sk-ant-...
```
Without a key, the app runs exactly the same — summaries just come from the
rule-based fallback instead of the API.

## Running tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```
32 tests cover the detection engine (all four scenarios, threshold
boundaries), the safety guardrail, and every API route (valid/invalid input,
error handling).

## Project layout

```
app.py            - Flask routes, request validation, error handlers, SSE stream
simulator.py      - generates event data for all four scenarios (target-aware)
detector.py       - per-scenario detection dispatch table
responder.py      - playbook definitions + execution
alert.py          - Alert data class
safety.py         - target whitelist guardrail (loopback + lab addresses)
storage.py        - SQLite persistence
ai_summary.py     - AI summary generation with rule-based fallback
config.py         - thresholds, feature flags, env-driven settings
tests/            - pytest suite
templates/        - index.html, about.html
static/           - style.css, script.js
```





## Known limitations

This is a training and portfolio project, not a production security product.
- Detection thresholds are simple and static, not adaptive or ML-based.
- Response actions are simulated and logged, not wired into a real firewall,
  EDR, or identity provider.
- The AI-generated summary quality depends on whether `ANTHROPIC_API_KEY` is
  configured; without it, summaries come from a template.
- Live packet simulation (`simulator.run_live_port_test`) is restricted to
  loopback and explicitly whitelisted private addresses only, and is not
  wired into the main `/api/simulate` flow.
- SQLite is appropriate for a single-user demo; a multi-user deployment
  would want a proper database server and authentication, neither of which
  this project implements.
