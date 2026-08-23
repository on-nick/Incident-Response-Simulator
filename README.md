# Incident Response Simulation Tool

A Python-based cybersecurity project that simulates security incidents, detects suspicious activity, generates alerts, executes automated response playbooks, and displays the results through a web dashboard.

This project was built as a learning and development challenge to practice Python, Flask, cybersecurity concepts, APIs, data persistence, JavaScript, and basic incident response automation.

---

## 🚀 Features

- Fake cybersecurity event generation
- Multiple attack scenario simulations
- Port scan detection
- Brute-force login simulation
- SYN flood simulation
- Malware beacon simulation
- Automated alert generation
- Automated response playbooks
- Incident history persistence
- Detection and response metrics
- Flask REST API
- Interactive web dashboard
- Localhost-only live packet simulation using Scapy
- Input validation and error handling

---

## 🛡️ Simulated Scenarios

### Port Scan

Generates multiple connection events against different ports.

The detector checks the number of unique ports and generates an alert when the threshold is exceeded.

### SYN Flood Lite

Generates repeated SYN-style connection events to simulate suspicious connection behavior.

### Brute Force Login

Generates repeated failed login attempts using common usernames.

### Malware Beacon

Simulates periodic communication between a potentially compromised host and a remote destination.

---

## 🧠 Architecture

```text
                    Web Dashboard
                         │
                         ▼
                    Flask API
                         │
                         ▼
                    Simulator
                         │
                         ▼
                     Detector
                         │
                         ▼
                       Alert
                         │
                         ▼
                     Responder
                         │
                         ▼
                  Incident Storage
                         │
                         ▼
                    JSON Database
