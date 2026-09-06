const scenarioSelect = document.getElementById('scenario');
const targetInput = document.getElementById('target');
const runButton = document.getElementById('run-button');
const runButtonLabel = document.getElementById('run-button-label');
const clearButton = document.getElementById('clear-button');
const feed = document.getElementById('feed');
const toastContainer = document.getElementById('toast-container');

const liveStream = document.getElementById('live-stream');
const liveStreamLabel = document.getElementById('live-stream-label');
const liveEvents = document.getElementById('live-events');
const liveAlert = document.getElementById('live-alert');
const liveResponse = document.getElementById('live-response');
const liveResponseSteps = document.getElementById('live-response-steps');
const liveSummary = document.getElementById('live-summary');

const SEV_CLASS = { MEDIUM: 'sev-medium', HIGH: 'sev-high', CRITICAL: 'sev-critical' };

function showToast(message) {
  const el = document.createElement('div');
  el.className = 'toast';
  el.textContent = message;
  toastContainer.appendChild(el);
  setTimeout(() => el.remove(), 5000);
}

function fmtTime(iso) {
  try {
    return new Date(iso).toLocaleTimeString('en-US', { hour12: false });
  } catch {
    return '';
  }
}

// ---------------------------------------------------------------------
// Incident cards (persisted history)
// ---------------------------------------------------------------------
function renderIncidentCard(incident) {
  const alert = (incident.alerts || [])[0];
  const card = document.createElement('div');
  card.className = 'incident-card' + (alert ? ` ${SEV_CLASS[alert.severity] || ''}` : '');

  const summaryText = incident.ai_summary ? incident.ai_summary.text : '';
  const summarySource = incident.ai_summary && incident.ai_summary.source === 'ai'
    ? 'AI-generated summary' : 'Auto-generated summary (rule-based)';

  card.innerHTML = `
    <div class="incident-head">
      <span class="incident-scenario">${incident.scenario.replace(/_/g, ' ')}</span>
      <span class="incident-time">${fmtTime(incident.timestamp)}</span>
    </div>
    ${summaryText ? `<p class="incident-summary">${escapeHtml(summaryText)}</p>` : ''}
    ${!alert ? '<p class="no-alert-note">Below detection threshold — no alert raised.</p>' : ''}
    <div class="incident-meta">
      <span><b>target</b> ${incident.target || '—'}</span>
      <span><b>events</b> ${(incident.events || []).length}</span>
      <span><b>alerts</b> ${(incident.alerts || []).length}</span>
      <span><b>detect</b> ${incident.metrics ? incident.metrics.detection_latency_ms.toFixed(2) : '—'} ms</span>
      <span><b>respond</b> ${incident.metrics ? incident.metrics.response_time_ms.toFixed(2) : '—'} ms</span>
    </div>
  `;
  return card;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

async function loadIncidentHistory() {
  try {
    const res = await fetch('/api/incidents');
    if (!res.ok) throw new Error('Failed to load incidents');
    const incidents = await res.json();

    feed.innerHTML = '';
    if (incidents.length === 0) {
      feed.innerHTML = '<p class="feed-empty">No incidents yet. Run a simulation to populate the feed.</p>';
      return incidents;
    }
    incidents.slice().reverse().forEach(incident => feed.appendChild(renderIncidentCard(incident)));
    return incidents;
  } catch (err) {
    showToast('Could not load incident history.');
    return [];
  }
}

// ---------------------------------------------------------------------
// Metrics + trend chart
// ---------------------------------------------------------------------
async function loadMetrics() {
  try {
    const res = await fetch('/api/metrics');
    if (!res.ok) throw new Error('metrics failed');
    const m = await res.json();

    document.getElementById('m-total').textContent = m.total_incidents;
    document.getElementById('m-rate').textContent = m.total_incidents ? `${m.detection_rate}%` : '—';
    document.getElementById('m-latency').textContent = m.total_incidents ? `${m.average_detection_latency_ms} ms` : '—';
    document.getElementById('m-response').textContent = m.total_incidents ? `${m.average_response_time_ms} ms` : '—';

    const bars = document.getElementById('scenario-bars');
    const entries = Object.entries(m.by_scenario || {});
    bars.innerHTML = entries.length ? entries.map(([scenario, s]) => {
      const pct = s.count ? Math.round((s.detected / s.count) * 100) : 0;
      return `
        <div class="scenario-bar-row">
          <div class="scenario-bar-label">
            <span>${scenario.replace(/_/g, ' ')}</span>
            <span>${s.detected}/${s.count}</span>
          </div>
          <div class="scenario-bar-track">
            <div class="scenario-bar-fill" style="width:${pct}%"></div>
          </div>
        </div>`;
    }).join('') : '<p class="feed-empty" style="padding:0;">No data yet</p>';
  } catch (err) {
    showToast('Could not load metrics.');
  }
}

function renderTrendChart(incidents) {
  const svg = document.getElementById('trend-chart');
  const recent = incidents.slice(-12);
  if (recent.length < 2) {
    svg.innerHTML = '';
    return;
  }

  const values = recent.map(i => (i.metrics && i.metrics.response_time_ms) || 0);
  const max = Math.max(...values, 1);
  const w = 260, h = 70, pad = 6;
  const stepX = (w - pad * 2) / (values.length - 1);

  const points = values.map((v, i) => {
    const x = pad + i * stepX;
    const y = h - pad - (v / max) * (h - pad * 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');

  svg.innerHTML = `
    <polyline points="${points}" fill="none" stroke="var(--signal)" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />
    ${values.map((v, i) => {
      const x = pad + i * stepX;
      const y = h - pad - (v / max) * (h - pad * 2);
      return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="2.2" fill="var(--signal)" />`;
    }).join('')}
  `;
}

// ---------------------------------------------------------------------
// Health pill
// ---------------------------------------------------------------------
async function loadHealth() {
  const pill = document.getElementById('health-pill');
  if (!pill) return;
  try {
    const res = await fetch('/api/health');
    const h = await res.json();
    pill.textContent = h.status === 'ok'
      ? `online · ${h.incident_count} incidents · ${Math.round(h.uptime_seconds)}s up`
      : 'degraded';
    pill.className = 'health-pill ' + (h.status === 'ok' ? 'ok' : 'degraded');
  } catch {
    pill.textContent = 'unreachable';
    pill.className = 'health-pill degraded';
  }
}

// ---------------------------------------------------------------------
// Streaming simulation run
// ---------------------------------------------------------------------
function resetLiveStream(scenario, target) {
  liveStream.hidden = false;
  liveStreamLabel.textContent = `Running ${scenario.replace(/_/g, ' ')} against ${target}…`;
  liveEvents.innerHTML = '';
  liveAlert.hidden = true;
  liveAlert.innerHTML = '';
  liveResponse.hidden = true;
  liveResponseSteps.innerHTML = '';
  liveSummary.hidden = true;
  liveSummary.innerHTML = '';
}

function parseSseChunk(chunk) {
  // Each SSE message looks like: "event: TYPE\ndata: {...}\n\n"
  const lines = chunk.split('\n');
  let eventType = 'message';
  let data = '';
  for (const line of lines) {
    if (line.startsWith('event:')) eventType = line.slice(6).trim();
    if (line.startsWith('data:')) data += line.slice(5).trim();
  }
  return { eventType, data };
}

async function runSimulationStreamed() {
  const scenario = scenarioSelect.value;
  const target = targetInput.value.trim() || '127.0.0.1';

  runButton.disabled = true;
  runButtonLabel.textContent = 'Running…';
  resetLiveStream(scenario, target);

  let eventCount = 0;

  try {
    const res = await fetch('/api/simulate/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario, target }),
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      showToast(body.error || 'Simulation failed to start.');
      liveStream.hidden = true;
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let boundary;
      while ((boundary = buffer.indexOf('\n\n')) !== -1) {
        const chunk = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        if (!chunk.trim()) continue;

        const { eventType, data } = parseSseChunk(chunk);
        let payload;
        try {
          payload = JSON.parse(data);
        } catch {
          continue;
        }

        if (eventType === 'event') {
          eventCount += 1;
          const line = document.createElement('div');
          line.className = 'live-event-line';
          line.textContent = `#${eventCount} ${payload.event_id || ''} ${payload.src_ip || ''} → ${payload.dst_ip || ''}`;
          liveEvents.appendChild(line);
          liveEvents.scrollTop = liveEvents.scrollHeight;

        } else if (eventType === 'alert') {
          liveAlert.hidden = false;
          const sevVar = { MEDIUM: '--sev-medium', HIGH: '--sev-high', CRITICAL: '--sev-critical' }[payload.severity] || '--sev-high';
          liveAlert.style.borderLeftColor = `var(${sevVar})`;
          liveAlert.innerHTML = `<strong>${payload.severity}</strong> — ${escapeHtml(payload.message)}`;

        } else if (eventType === 'response_step') {
          liveResponse.hidden = false;
          const step = document.createElement('div');
          step.className = 'live-response-step';
          step.textContent = payload.step;
          liveResponseSteps.appendChild(step);

        } else if (eventType === 'summary') {
          liveSummary.hidden = false;
          const sourceLabel = payload.source === 'ai' ? 'AI-generated summary' : 'Auto-generated summary (rule-based)';
          liveSummary.innerHTML = `${escapeHtml(payload.text)}<span class="summary-source">${sourceLabel}</span>`;

        } else if (eventType === 'done') {
          liveStreamLabel.textContent = `Completed ${scenario.replace(/_/g, ' ')} against ${target}`;
          const incidents = await loadIncidentHistory();
          await loadMetrics();
          renderTrendChart(incidents);
          await loadHealth();

        } else if (eventType === 'error') {
          showToast(payload.error || 'Simulation error.');
        }
      }
    }
  } catch (err) {
    showToast('Lost connection during simulation.');
  } finally {
    runButton.disabled = false;
    runButtonLabel.textContent = 'Run simulation';
  }
}

// ---------------------------------------------------------------------
// Clear history
// ---------------------------------------------------------------------
async function clearHistory() {
  if (!confirm('Clear all stored incident history? This cannot be undone.')) return;
  try {
    const res = await fetch('/api/incidents', { method: 'DELETE' });
    if (!res.ok) throw new Error('failed');
    liveStream.hidden = true;
    await loadIncidentHistory();
    await loadMetrics();
    renderTrendChart([]);
    showToast('Incident history cleared.');
  } catch {
    showToast('Could not clear history.');
  }
}

// ---------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------
runButton.addEventListener('click', runSimulationStreamed);
clearButton.addEventListener('click', clearHistory);

(async function init() {
  const incidents = await loadIncidentHistory();
  await loadMetrics();
  renderTrendChart(incidents);
  await loadHealth();
  setInterval(loadHealth, 15000);
})();
