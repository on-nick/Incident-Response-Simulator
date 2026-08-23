async function runSimulation() {

    const scenario =
        document.getElementById("scenario").value;

    const target =
        document.getElementById("target").value;

    runButton.disabled = true;

    runButton.textContent = "Running...";

    try {

        const response = await fetch("/api/simulate", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                scenario: scenario,
                target: target
            })

        });

        const data = await response.json();

        if (!response.ok) {

            alert(data.error || "Simulation failed");

            return;
        }

        addIncidentCard(data);

        await loadMetrics();

    } catch (error) {

        console.error("Error:", error);

        alert("Could not connect to the server.");

    } finally {

        runButton.disabled = false;

        runButton.textContent = "Run Simulation";
    }
}


function addIncidentCard(incident) {

    const feed =
        document.getElementById("feed");

    const card =
        document.createElement("div");

    card.className = "incident-card";

    const severity =
        incident.alerts.length > 0
            ? incident.alerts[0].severity
            : "NONE";

    card.innerHTML = `
        <h3>
            ${incident.scenario}
        </h3>

        <p>
            Incident ID:
            ${incident.incident_id}
        </p>

        <p>
            Severity:
            ${severity}
        </p>

        <p>
            Events:
            ${incident.events.length}
        </p>

        <p>
            Alerts:
            ${incident.alerts.length}
        </p>

        <p>
            Response Steps:
            ${incident.response.length}
        </p>

        <p>
            Time:
            ${incident.timestamp}
        </p>
    `;

    feed.prepend(card);
}


async function loadIncidents() {

    try {

        const response =
            await fetch("/api/incidents");

        const incidents =
            await response.json();

        if (!response.ok) {

            console.error(
                "Failed to load incidents"
            );

            return;
        }

        const feed =
            document.getElementById("feed");

        feed.innerHTML = "";

        if (incidents.length === 0) {

            feed.innerHTML = `
                <p>No incidents yet.</p>
            `;

            return;
        }

        incidents.reverse().forEach(incident => {

            addIncidentCard(incident);

        });

    } catch (error) {

        console.error(
            "Error loading incidents:",
            error
        );

    }
}


async function loadMetrics() {

    try {

        const response =
            await fetch("/api/metrics");

        const metrics =
            await response.json();

        if (!response.ok) {

            console.error(
                "Failed to load metrics"
            );

            return;
        }

        document.getElementById(
            "total-incidents"
        ).textContent =
            metrics.total_incidents;

        document.getElementById(
            "detection-rate"
        ).textContent =
            `${metrics.detection_rate}%`;

        document.getElementById(
            "detection-latency"
        ).textContent =
            `${metrics.average_detection_latency_ms} ms`;

        document.getElementById(
            "response-time"
        ).textContent =
            `${metrics.average_response_time_ms} ms`;

    } catch (error) {

        console.error(
            "Error loading metrics:",
            error
        );

    }
}


const runButton =
    document.getElementById("run-button");

runButton.addEventListener(
    "click",
    runSimulation
);


window.addEventListener(
    "DOMContentLoaded",
    () => {

        loadIncidents();

        loadMetrics();

    }

);
document
    .getElementById("clear-feed")
    .addEventListener("click", () => {

        document.getElementById("feed").innerHTML = `
            <p>Feed cleared from view.</p>
        `;

    });