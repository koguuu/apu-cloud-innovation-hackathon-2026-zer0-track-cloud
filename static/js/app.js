/**
 * Campus Wi-Fi Health - Frontend Application Controller
 * Handles real-time polling, Chart.js updates, Antigravity pipeline event streams,
 * scenario injection, and Gemini Root Cause Analysis ticket views.
 */

// Global State
let latencyChartInstance = null;
let packetLossChartInstance = null;
let lastKnownEventsCount = 0;
let currentSnapshot = {};
let latestTicket = null;
let isLogStreamPaused = false;
let selectedLogSeverity = 'ALL';
let selectedLogAp = 'ALL';
let lastRenderedLogsCount = 0;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  initCharts();
  initLucide();
  pollDashboardData();
  // Poll every 1500ms
  setInterval(pollDashboardData, 1500);
});

function initLucide() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

// -------------------------------------------------------------
// 1. Chart.js Initialization
// -------------------------------------------------------------
function initCharts() {
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 400 },
    scales: {
      x: {
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        ticks: { color: '#64748b', font: { size: 10 } }
      },
      y: {
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        ticks: { color: '#64748b', font: { size: 10 } },
        beginAtZero: true
      }
    },
    plugins: {
      legend: {
        position: 'top',
        labels: { color: '#cbd5e1', boxWidth: 12, font: { size: 11 } }
      }
    }
  };

  // Latency Chart
  const ctxLatency = document.getElementById('latencyChart').getContext('2d');
  latencyChartInstance = new Chart(ctxLatency, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          label: 'Block A (Main Hall)',
          borderColor: '#38bdf8',
          backgroundColor: 'rgba(56, 189, 248, 0.1)',
          borderWidth: 2,
          tension: 0.3,
          data: []
        },
        {
          label: 'Block B (Labs)',
          borderColor: '#f43f5e',
          backgroundColor: 'rgba(244, 63, 94, 0.1)',
          borderWidth: 2,
          tension: 0.3,
          data: []
        },
        {
          label: 'Library (Quiet Study)',
          borderColor: '#a855f7',
          backgroundColor: 'rgba(168, 85, 247, 0.1)',
          borderWidth: 2,
          tension: 0.3,
          data: []
        }
      ]
    },
    options: chartOptions
  });

  // Packet Loss Chart
  const ctxLoss = document.getElementById('packetLossChart').getContext('2d');
  packetLossChartInstance = new Chart(ctxLoss, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          label: 'Block A Loss %',
          borderColor: '#38bdf8',
          backgroundColor: 'rgba(56, 189, 248, 0.1)',
          borderWidth: 2,
          tension: 0.3,
          data: []
        },
        {
          label: 'Block B Loss %',
          borderColor: '#f43f5e',
          backgroundColor: 'rgba(244, 63, 94, 0.1)',
          borderWidth: 2,
          tension: 0.3,
          data: []
        },
        {
          label: 'Library Loss %',
          borderColor: '#a855f7',
          backgroundColor: 'rgba(168, 85, 247, 0.1)',
          borderWidth: 2,
          tension: 0.3,
          data: []
        }
      ]
    },
    options: {
      ...chartOptions,
      scales: {
        ...chartOptions.scales,
        y: {
          ...chartOptions.scales.y,
          max: 100
        }
      }
    }
  });
}

// -------------------------------------------------------------
// 2. Real-Time Polling & UI Update
// -------------------------------------------------------------
async function pollDashboardData() {
  try {
    const fetchPromises = [
      fetch('/api/status').then(r => r.json()),
      fetch('/api/telemetry/history').then(r => r.json()),
      fetch('/api/pipeline/events?limit=40').then(r => r.json()),
      fetch('/api/tickets').then(r => r.json())
    ];

    if (!isLogStreamPaused) {
      fetchPromises.push(
        fetch(`/api/logs/live?limit=35&severity=${selectedLogSeverity}&ap_id=${selectedLogAp}`).then(r => r.json())
      );
    }

    const [statusRes, historyRes, eventsRes, ticketsRes, logsRes] = await Promise.all(fetchPromises);

    currentSnapshot = statusRes.probes || {};
    updateHeaderAndScenario(statusRes);
    updateStudentAdvisories(statusRes.advisories);
    updateAPCards(currentSnapshot);
    updateCharts(historyRes);
    updatePipelineTerminal(eventsRes);
    updateTickets(ticketsRes);

    if (logsRes && !isLogStreamPaused) {
      updateInterpretedLogs(logsRes);
    }

    initLucide();
  } catch (err) {
    console.error('Error polling dashboard telemetry:', err);
  }
}

// Update Header Badges & Scenario State
function updateHeaderAndScenario(statusData) {
  const scenBadge = document.getElementById('active-scenario-badge');
  const scenName = (statusData.active_scenario && statusData.active_scenario.name) || 'NORMAL';
  scenBadge.innerText = scenName;

  if (scenName === 'NORMAL') {
    scenBadge.className = 'px-2.5 py-1 rounded-md bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-mono font-semibold';
  } else if (scenName === 'BLOCK_B_HARDWARE_FAILURE') {
    scenBadge.className = 'px-2.5 py-1 rounded-md bg-rose-500/20 text-rose-400 border border-rose-500/30 font-mono font-semibold animate-pulse';
  } else if (scenName === 'CAMPUS_ISP_OUTAGE') {
    scenBadge.className = 'px-2.5 py-1 rounded-md bg-amber-500/20 text-amber-400 border border-amber-500/30 font-mono font-semibold animate-pulse';
  } else {
    scenBadge.className = 'px-2.5 py-1 rounded-md bg-orange-500/20 text-orange-400 border border-orange-500/30 font-mono font-semibold animate-pulse';
  }

  // Header Counters
  document.getElementById('header-tickets-count').innerText = statusData.open_tickets_count || 0;
  
  const gem = statusData.gemini_engine || {};
  const gemBadge = document.getElementById('gemini-engine-mode');
  if (gem.has_key && gem.last_status === 'SUCCESS') {
    gemBadge.innerText = `LIVE API (${(gem.model || '1.5-FLASH').toUpperCase()})`;
    gemBadge.className = 'font-semibold text-emerald-400 font-mono';
  } else if (gem.has_key && gem.last_status === 'FAILED') {
    gemBadge.innerText = 'KEY ERROR (FALLBACK)';
    gemBadge.className = 'font-semibold text-rose-400 font-mono animate-pulse';
  } else if (gem.has_key) {
    gemBadge.innerText = `KEY SET (${(gem.model || '1.5-FLASH').toUpperCase()})`;
    gemBadge.className = 'font-semibold text-sky-400 font-mono';
  } else {
    gemBadge.innerText = 'AIOps ENGINE (HYBRID)';
    gemBadge.className = 'font-semibold text-indigo-400 font-mono';
  }
}

// -------------------------------------------------------------
// 3. Student Study Zone Advisory Cards
// -------------------------------------------------------------
function updateStudentAdvisories(adv) {
  if (!adv) return;
  document.getElementById('advisory-headline').innerText = adv.headline || 'All systems nominal';
  document.getElementById('advisory-time').innerText = adv.last_updated || 'Just now';

  const container = document.getElementById('study-zones-container');
  if (!container || !adv.zones) return;

  const zones = adv.zones;
  let html = '';

  for (const [zoneName, z] of Object.entries(zones)) {
    let recBadgeClass = 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
    let progressBg = 'bg-emerald-500';
    let cardBorder = 'border-slate-800';

    if (z.recommendation === 'AVOID') {
      recBadgeClass = 'bg-rose-500/20 text-rose-400 border-rose-500/30';
      progressBg = 'bg-rose-500';
      cardBorder = 'border-rose-500/40 bg-rose-950/10';
    } else if (z.recommendation === 'MODERATE') {
      recBadgeClass = 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      progressBg = 'bg-amber-500';
      cardBorder = 'border-amber-500/40 bg-amber-950/10';
    }

    html += `
      <div class="glass-panel rounded-xl p-4 border ${cardBorder} flex flex-col justify-between space-y-3 transition hover:border-slate-600">
        <div>
          <div class="flex items-center justify-between mb-2">
            <h3 class="font-bold text-sm text-white flex items-center gap-1.5">
              <i data-lucide="map-pin" class="w-4 h-4 text-slate-400"></i>
              ${zoneName}
            </h3>
            <span class="text-[10px] font-mono px-2 py-0.5 rounded-full font-bold border ${recBadgeClass}">
              ${z.recommendation}
            </span>
          </div>

          <!-- Quality Score Progress Bar -->
          <div class="space-y-1 mb-2.5">
            <div class="flex justify-between text-xs">
              <span class="text-slate-400">Wi-Fi Quality Index:</span>
              <span class="font-mono font-bold text-slate-200">${z.quality_score}%</span>
            </div>
            <div class="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
              <div class="${progressBg} h-1.5 rounded-full transition-all duration-500" style="width: ${z.quality_score}%"></div>
            </div>
          </div>

          <p class="text-xs text-slate-300 leading-snug">${z.status_text}</p>
        </div>

        <div class="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
          <span class="flex items-center gap-1 text-slate-300 font-medium truncate">
            <i data-lucide="sparkles" class="w-3.5 h-3.5 text-indigo-400 flex-shrink-0"></i>
            ${z.best_for}
          </span>
          <span class="font-mono text-xs text-slate-400 ml-2 whitespace-nowrap">${z.avg_latency_ms} ms</span>
        </div>
      </div>
    `;
  }

  container.innerHTML = html;
}

// -------------------------------------------------------------
// 4. Access Point Telemetry Cards
// -------------------------------------------------------------
function updateAPCards(probes) {
  const container = document.getElementById('ap-cards-container');
  if (!container) return;

  let html = '';
  for (const [apId, p] of Object.entries(probes)) {
    let statusBadge = '<span class="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono text-xs border border-emerald-500/30">ONLINE</span>';
    let cardPulse = 'pulse-radar-healthy';
    let borderColor = 'border-slate-800';

    if (p.status === 'CRITICAL_FAILURE') {
      statusBadge = '<span class="px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 font-mono text-xs border border-rose-500/30 animate-pulse">HARDWARE CRASH</span>';
      cardPulse = 'pulse-radar-danger';
      borderColor = 'border-rose-500/50 bg-rose-950/15';
    } else if (p.status === 'CONGESTED') {
      statusBadge = '<span class="px-2 py-0.5 rounded bg-orange-500/20 text-orange-400 font-mono text-xs border border-orange-500/30">CONGESTED</span>';
      borderColor = 'border-orange-500/40 bg-orange-950/10';
    } else if (p.status === 'DEGRADED') {
      statusBadge = '<span class="px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 font-mono text-xs border border-amber-500/30">DEGRADED</span>';
      borderColor = 'border-amber-500/40 bg-amber-950/10';
    }

    const latColor = p.latency_ms > 140 ? 'text-rose-400' : (p.latency_ms > 45 ? 'text-amber-400' : 'text-emerald-400');
    const lossColor = p.packet_loss_pct > 12 ? 'text-rose-400' : (p.packet_loss_pct > 3 ? 'text-amber-400' : 'text-emerald-400');
    const clientPct = Math.min(100, Math.round((p.connected_clients / p.max_capacity) * 100));

    html += `
      <div class="glass-panel rounded-2xl p-4 border ${borderColor} space-y-3.5 transition">
        <!-- Header -->
        <div class="flex items-start justify-between">
          <div class="flex items-center space-x-2.5">
            <div class="relative flex items-center justify-center w-8 h-8 rounded-lg bg-slate-800/80 border border-slate-700">
              <span class="w-3 h-3 rounded-full ${p.status === 'CRITICAL_FAILURE' ? 'bg-rose-500' : 'bg-emerald-500'} ${cardPulse}"></span>
            </div>
            <div>
              <h3 class="text-xs font-bold text-white tracking-wide">${p.name}</h3>
              <p class="text-[11px] text-slate-400 font-mono">${p.ap_id} &bull; ${p.ip}</p>
            </div>
          </div>
          <div>${statusBadge}</div>
        </div>

        <!-- Telemetry Gauges Grid -->
        <div class="grid grid-cols-3 gap-2 bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80 text-center">
          <div>
            <div class="text-[10px] text-slate-400 uppercase tracking-wider">Latency</div>
            <div class="text-sm font-bold font-mono ${latColor}">${p.latency_ms} <span class="text-[10px]">ms</span></div>
          </div>
          <div>
            <div class="text-[10px] text-slate-400 uppercase tracking-wider">Pkt Loss</div>
            <div class="text-sm font-bold font-mono ${lossColor}">${p.packet_loss_pct}<span class="text-[10px]">%</span></div>
          </div>
          <div>
            <div class="text-[10px] text-slate-400 uppercase tracking-wider">Signal</div>
            <div class="text-sm font-bold font-mono text-slate-200">${p.rssi_dbm} <span class="text-[10px]">dBm</span></div>
          </div>
        </div>

        <!-- Client Capacity Meter -->
        <div class="space-y-1">
          <div class="flex justify-between text-xs text-slate-400">
            <span class="flex items-center gap-1">
              <i data-lucide="users" class="w-3 h-3"></i> Connected Students:
            </span>
            <span class="font-mono text-slate-200 font-bold">${p.connected_clients} / ${p.max_capacity} (${clientPct}%)</span>
          </div>
          <div class="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div class="${clientPct > 85 ? 'bg-orange-500' : 'bg-blue-500'} h-1.5 rounded-full transition-all" style="width: ${clientPct}%"></div>
          </div>
        </div>

        <!-- AP Metadata & Syslog Action -->
        <div class="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
          <span class="font-mono text-[10px] text-slate-500">${p.model}</span>
          <button onclick="openSyslogModal('${p.ap_id}')" class="text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1 hover:underline">
            <i data-lucide="terminal" class="w-3 h-3"></i> View Syslog
          </button>
        </div>
      </div>
    `;
  }

  container.innerHTML = html;
}

// -------------------------------------------------------------
// 5. Chart.js Data Feed
// -------------------------------------------------------------
function updateCharts(history) {
  if (!history || !latencyChartInstance || !packetLossChartInstance) return;

  const apA = history['AP-A101'] || [];
  const apB = history['AP-B204'] || [];
  const apLib = history['AP-LIB-G'] || [];

  const maxLen = Math.max(apA.length, apB.length, apLib.length);
  const labels = apA.map(item => item.timestamp.split(' ')[1] || '');

  latencyChartInstance.data.labels = labels;
  latencyChartInstance.data.datasets[0].data = apA.map(i => i.latency_ms);
  latencyChartInstance.data.datasets[1].data = apB.map(i => i.latency_ms);
  latencyChartInstance.data.datasets[2].data = apLib.map(i => i.latency_ms);
  latencyChartInstance.update('none');

  packetLossChartInstance.data.labels = labels;
  packetLossChartInstance.data.datasets[0].data = apA.map(i => i.packet_loss_pct);
  packetLossChartInstance.data.datasets[1].data = apB.map(i => i.packet_loss_pct);
  packetLossChartInstance.data.datasets[2].data = apLib.map(i => i.packet_loss_pct);
  packetLossChartInstance.update('none');
}

// -------------------------------------------------------------
// 6. Antigravity Event Pipeline Terminal Log
// -------------------------------------------------------------
function updatePipelineTerminal(events) {
  const terminal = document.getElementById('pipeline-terminal');
  if (!terminal || !events) return;

  // Only update if count changed or empty
  if (events.length === lastKnownEventsCount) return;
  lastKnownEventsCount = events.length;

  let html = '';
  // Events are returned newest first, but let's reverse to show chronological order
  const chrono = [...events].reverse();

  for (const e of chrono) {
    let colorClass = 'text-slate-400';
    let tag = `[${e.event_type}]`;

    if (e.level === 'ALERT') {
      colorClass = 'text-amber-400 font-medium';
    } else if (e.level === 'SUCCESS') {
      colorClass = 'text-emerald-400 font-medium';
    } else if (e.level === 'ERROR') {
      colorClass = 'text-rose-400 font-bold';
    } else if (e.event_type === 'ANTIGRAVITY_STREAM') {
      colorClass = 'text-sky-400';
    }

    html += `
      <div class="leading-relaxed hover:bg-slate-900/40 p-1 rounded transition">
        <span class="text-slate-600 font-mono text-[10px] select-none">${e.timestamp}</span>
        <span class="${colorClass}">${tag} ${e.message}</span>
      </div>
    `;
  }

  terminal.innerHTML = html;
  terminal.scrollTop = terminal.scrollHeight;
}

// -------------------------------------------------------------
// 7. Gemini Root Cause Analysis & IT Support Ticket
// -------------------------------------------------------------
function updateTickets(tickets) {
  const container = document.getElementById('ticket-card-content');
  const historyContainer = document.getElementById('tickets-history-list');
  const actionContainer = document.getElementById('active-ticket-actions');
  const countSpan = document.getElementById('ticket-history-count');
  
  if (!tickets || tickets.length === 0) {
    container.innerHTML = `
      <div class="flex flex-col items-center justify-center py-16 text-slate-500 space-y-2">
        <i data-lucide="check-circle" class="w-10 h-10 text-emerald-500/50"></i>
        <p class="text-sm font-semibold text-slate-400">All Campus Access Points Nominal</p>
        <p class="text-xs text-slate-500">Antigravity continuous background pipeline active. No open incidents.</p>
      </div>
    `;
    actionContainer.innerHTML = '';
    historyContainer.innerHTML = '<p class="text-xs text-slate-500 italic">No historical incident tickets recorded yet.</p>';
    countSpan.innerText = '0 tickets';
    return;
  }

  countSpan.innerText = `${tickets.length} tickets recorded`;

  // Pick top open ticket or newest
  const activeTicket = tickets.find(t => t.status === 'OPEN') || tickets[0];
  latestTicket = activeTicket;

  let sevBadgeClass = 'bg-rose-500/20 text-rose-400 border-rose-500/30';
  if (activeTicket.severity && activeTicket.severity.includes('P3')) {
    sevBadgeClass = 'bg-amber-500/20 text-amber-400 border-amber-500/30';
  } else if (activeTicket.severity && activeTicket.severity.includes('Info')) {
    sevBadgeClass = 'bg-blue-500/20 text-blue-400 border-blue-500/30';
  }

  // Action Buttons
  actionContainer.innerHTML = `
    <button onclick="exportTicket('${activeTicket.ticket_id}', 'markdown')" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition flex items-center gap-1">
      <i data-lucide="download" class="w-3.5 h-3.5"></i> Export .MD
    </button>
    <button onclick="exportTicket('${activeTicket.ticket_id}', 'json')" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition flex items-center gap-1">
      <i data-lucide="code" class="w-3.5 h-3.5"></i> JSON
    </button>
    ${activeTicket.status === 'OPEN' ? `
      <button onclick="resolveTicket('${activeTicket.ticket_id}')" class="px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md transition flex items-center gap-1">
        <i data-lucide="check" class="w-3.5 h-3.5"></i> Resolve
      </button>
    ` : '<span class="text-xs text-emerald-400 font-bold px-2 py-1 bg-emerald-500/20 rounded border border-emerald-500/30">RESOLVED</span>'}
  `;

  // Remediation Steps
  const stepsHtml = (activeTicket.remediation_steps || []).map((step, idx) => `
    <li class="flex items-start space-x-2 text-xs text-slate-300">
      <span class="w-4 h-4 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-mono text-[10px] flex-shrink-0 mt-0.5">${idx + 1}</span>
      <span>${step}</span>
    </li>
  `).join('');

  container.innerHTML = `
    <div class="space-y-3">
      <!-- Title & Badges -->
      <div>
        <div class="flex items-center space-x-2 mb-1 flex-wrap gap-1">
          <span class="text-xs font-mono font-bold text-indigo-400">${activeTicket.ticket_id}</span>
          <span class="text-[10px] px-2 py-0.5 rounded font-bold border ${sevBadgeClass}">${activeTicket.severity}</span>
          <span class="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">Confidence: ${activeTicket.ai_confidence_pct}%</span>
          <span class="text-[10px] text-slate-400 font-mono ml-auto">${activeTicket.created_at}</span>
        </div>
        <h4 class="text-base font-bold text-white leading-tight">${activeTicket.title}</h4>
      </div>

      <!-- Root Cause Technical Explanation -->
      <div class="bg-indigo-950/20 border border-indigo-500/30 rounded-xl p-3 space-y-1">
        <div class="text-[11px] font-bold text-indigo-300 uppercase tracking-wider flex items-center gap-1">
          <i data-lucide="cpu" class="w-3.5 h-3.5 text-indigo-400"></i>
          Root Cause Analysis (RCA) Multi-Point Evidence:
        </div>
        <p class="text-xs text-slate-200 leading-relaxed">${activeTicket.root_cause_explanation}</p>
      </div>

      <!-- Blast Radius & Affected Nodes -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
        <div class="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
          <span class="text-slate-400 block text-[10px] uppercase tracking-wider">Affected AP Nodes:</span>
          <span class="font-mono text-slate-200 font-semibold">${(activeTicket.affected_nodes || []).join(', ') || 'None'}</span>
        </div>
        <div class="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
          <span class="text-slate-400 block text-[10px] uppercase tracking-wider">Estimated Blast Radius:</span>
          <span class="text-slate-200 font-medium">${activeTicket.blast_radius || 'N/A'}</span>
        </div>
      </div>

      <!-- Engineering Remediation Protocol -->
      <div class="space-y-1.5 pt-1">
        <div class="text-[11px] font-bold text-slate-300 uppercase tracking-wider">Automated Remediation Protocol (NOC Action Items):</div>
        <ul class="space-y-1.5 bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
          ${stepsHtml}
        </ul>
      </div>
    </div>
  `;

  // History list
  historyContainer.innerHTML = tickets.map(t => `
    <div class="flex items-center justify-between text-xs p-2 rounded-lg bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition">
      <div class="flex items-center space-x-2 truncate">
        <span class="font-mono text-[10px] text-indigo-400">${t.ticket_id}</span>
        <span class="font-medium text-slate-200 truncate">${t.title}</span>
      </div>
      <div class="flex items-center space-x-2 flex-shrink-0 ml-2">
        <span class="text-[10px] font-mono ${t.status === 'OPEN' ? 'text-rose-400' : 'text-emerald-400'}">${t.status}</span>
        <span class="text-[10px] text-slate-500">${t.created_at.split(' ')[1] || ''}</span>
      </div>
    </div>
  `).join('');
}

// -------------------------------------------------------------
// 8. Scenario Injector Handler
// -------------------------------------------------------------
async function injectScenario(scenarioName) {
  try {
    const res = await fetch('/api/scenarios/inject', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario: scenarioName })
    });
    const data = await res.json();
    console.log('[Scenario Injector]', data);
    ();
  } catch (err) {
    alert('Failed to inject scenario: ' + err.message);
  }
}

// -------------------------------------------------------------
// 9. Ticket Actions: Resolve & Export
// -------------------------------------------------------------
async function resolveTicket(ticketId) {
  try {
    const res = await fetch(`/api/tickets/${ticketId}/resolve`, { method: 'POST' });
    const data = await res.json();
    console.log('[Ticket Resolved]', data);
    pollDashboardData();
  } catch (err) {
    alert('Failed to resolve ticket: ' + err.message);
  }
}

function exportTicket(ticketId, format) {
  window.open(`/api/export/ticket/${ticketId}?format=${format}`, '_blank');
}

// -------------------------------------------------------------
// 10. Modals: Gemini Config & AP Syslog
// -------------------------------------------------------------
function openConfigModal() {
  document.getElementById('config-modal').classList.remove('hidden');
  const feedback = document.getElementById('gemini-modal-feedback');
  if (feedback) {
    feedback.className = 'hidden';
    feedback.innerHTML = '';
  }
}

function closeConfigModal() {
  document.getElementById('config-modal').classList.add('hidden');
}

async function saveGeminiKey() {
  const key = document.getElementById('gemini-key-input').value.trim();
  const feedback = document.getElementById('gemini-modal-feedback');
  const btn = document.getElementById('save-key-btn');
  const btnText = document.getElementById('save-key-text');

  if (!key) {
    feedback.className = 'rounded-xl p-3 text-xs bg-amber-500/20 text-amber-300 border border-amber-500/30';
    feedback.innerHTML = '⚠️ Please enter an API key or click "Clear Key" to use local mode.';
    return;
  }

  if (btn) btn.disabled = true;
  if (btnText) btnText.innerText = 'Validating with Google Cloud...';

  try {
    const res = await fetch('/api/config/gemini-key', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: key })
    });
    const data = await res.json();

    if (res.ok && data.status === 'OK') {
      feedback.className = 'rounded-xl p-3 text-xs bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 space-y-1';
      feedback.innerHTML = `
        <div class="font-bold flex items-center gap-1.5">
          <i data-lucide="check-circle" class="w-4 h-4 text-emerald-400"></i>
          Authentication Successful!
        </div>
        <div>${data.message}</div>
        <div class="text-[11px] text-emerald-400 font-mono">Active Model: ${data.model}</div>
      `;
      pollDashboardData();
      initLucide();
      setTimeout(() => {
        closeConfigModal();
      }, 1600);
    } else {
      feedback.className = 'rounded-xl p-3 text-xs bg-rose-500/20 text-rose-300 border border-rose-500/30 space-y-1';
      feedback.innerHTML = `
        <div class="font-bold flex items-center gap-1.5">
          <i data-lucide="alert-octagon" class="w-4 h-4 text-rose-400"></i>
          Google Cloud Validation Failed
        </div>
        <div>${data.message || 'Key rejected by Google Cloud.'}</div>
        <div class="text-[10px] text-slate-400 font-mono mt-1">Please verify your key at aistudio.google.com/apikey.</div>
      `;
      initLucide();
    }
  } catch (err) {
    feedback.className = 'rounded-xl p-3 text-xs bg-rose-500/20 text-rose-300 border border-rose-500/30';
    feedback.innerHTML = `Network error contacting local server: ${err.message}`;
  } finally {
    if (btn) btn.disabled = false;
    if (btnText) btnText.innerText = 'Save & Test Validation';
  }
}

async function clearGeminiKey() {
  const feedback = document.getElementById('gemini-modal-feedback');
  document.getElementById('gemini-key-input').value = '';
  try {
    const res = await fetch('/api/config/gemini-key', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: '' })
    });
    const data = await res.json();
    feedback.className = 'rounded-xl p-3 text-xs bg-blue-500/20 text-blue-300 border border-blue-500/30';
    feedback.innerHTML = `ℹ️ API Key cleared. Reverted to Deterministic Local AIOps Engine.`;
    pollDashboardData();
  } catch (err) {
    alert('Failed to clear key: ' + err.message);
  }
}

function openSyslogModal(apId) {
  const modal = document.getElementById('syslog-modal');
  const title = document.getElementById('syslog-modal-title');
  const body = document.getElementById('syslog-modal-body');

  const ap = currentSnapshot[apId];
  if (!ap) return;

  title.innerText = `AP Syslog & Kernel Telemetry: ${ap.name} (${ap.ap_id})`;
  
  const entries = ap.syslog_entries || [];
  if (entries.length === 0) {
    body.innerHTML = '<p class="text-slate-500 italic">No recent log entries.</p>';
  } else {
    body.innerHTML = entries.map(log => `
      <div class="hover:bg-slate-900/60 p-1 rounded font-mono text-xs">
        <span class="${log.includes('[CRIT]') || log.includes('[ALERT]') ? 'text-rose-400 font-bold' : (log.includes('[WARN]') ? 'text-amber-400' : 'text-slate-300')}">${log}</span>
      </div>
    `).join('');
  }

  modal.classList.remove('hidden');
  initLucide();
}

function closeSyslogModal() {
  document.getElementById('syslog-modal').classList.add('hidden');
}

// -------------------------------------------------------------
// 11. Live Log Interpretability & Initial AI Results
// -------------------------------------------------------------
function updateInterpretedLogs(logs) {
  const container = document.getElementById('interpreted-logs-container');
  if (!container || !logs) return;

  if (logs.length === 0) {
    container.innerHTML = `
      <div class="p-8 text-center text-slate-500 space-y-1">
        <i data-lucide="radio" class="w-8 h-8 mx-auto text-slate-600"></i>
        <p class="text-xs">No logs matching selected filters.</p>
      </div>
    `;
    return;
  }

  let html = '';
  for (const item of logs) {
    let sevBadge = '<span class="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[10px] font-mono font-bold">NOMINAL</span>';
    let cardBorder = 'border-slate-800/80 bg-slate-900/60';
    let accentDot = 'bg-emerald-400';

    if (item.severity === 'CRITICAL') {
      sevBadge = '<span class="px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30 text-[10px] font-mono font-bold animate-pulse">CRITICAL</span>';
      cardBorder = 'border-rose-500/40 bg-rose-950/15';
      accentDot = 'bg-rose-500';
    } else if (item.severity === 'WARNING') {
      sevBadge = '<span class="px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30 text-[10px] font-mono font-bold">WARNING</span>';
      cardBorder = 'border-amber-500/40 bg-amber-950/15';
      accentDot = 'bg-amber-400';
    }

    const ai = item.initial_ai_result || {};
    const featureWeights = ai.feature_weights || {};
    const signalsHtml = Object.entries(featureWeights).map(([k, v]) => `
      <span class="inline-flex items-center gap-1 bg-slate-900/90 border border-slate-700/80 rounded px-1.5 py-0.5 text-[10px] text-slate-300 font-mono">
        <span class="text-slate-400">${k}:</span>
        <span class="text-purple-300 font-semibold">${Math.round(v * 100)}%</span>
      </span>
    `).join('');

    html += `
      <div class="glass-panel rounded-xl p-3.5 border ${cardBorder} space-y-2.5 transition hover:border-slate-600">
        <!-- Top Metadata Row -->
        <div class="flex items-center justify-between flex-wrap gap-2 text-xs">
          <div class="flex items-center space-x-2">
            <span class="w-2 h-2 rounded-full ${accentDot}"></span>
            <span class="font-mono text-slate-400 text-[11px]">${item.timestamp}</span>
            <span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-mono text-[10px] font-semibold">${item.ap_id}</span>
            ${sevBadge}
          </div>

          <div class="flex items-center space-x-2">
            <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30 font-semibold">
              ${item.ai_classification}
            </span>
            <span class="text-[10px] font-mono text-slate-400">
              Confidence: <strong class="text-purple-300">${ai.confidence_pct}%</strong>
            </span>
          </div>
        </div>

        <!-- Raw Syslog Content -->
        <div class="bg-slate-950/90 border border-slate-800/80 rounded-lg p-2 font-mono text-[11px] text-slate-300 overflow-x-auto select-all">
          ${escapeHtml(item.raw_log)}
        </div>

        <!-- Initial AI Result (Explainable AI / Interpretability Card) -->
        <div class="bg-purple-950/25 border border-purple-500/30 rounded-xl p-3 space-y-2">
          <div class="flex items-start space-x-2">
            <div class="p-1 rounded bg-purple-500/20 text-purple-400 flex-shrink-0 mt-0.5">
              <i data-lucide="sparkles" class="w-3.5 h-3.5"></i>
            </div>
            <div class="space-y-1 w-full">
              <div class="flex items-center justify-between">
                <h4 class="text-xs font-bold text-purple-200">
                  Initial AI Insight: ${escapeHtml(ai.summary || '')}
                </h4>
              </div>
              <p class="text-[11px] text-slate-300 leading-relaxed">
                ${escapeHtml(ai.interpretability_explanation || '')}
              </p>
            </div>
          </div>

          <!-- Feature Signals & Recommended Triage -->
          <div class="pt-2 border-t border-purple-500/20 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-[11px]">
            <div class="flex items-center flex-wrap gap-1">
              <span class="text-[10px] text-slate-400 uppercase font-semibold mr-1">Signal Weights:</span>
              ${signalsHtml}
            </div>
            <div class="text-[11px] text-slate-300 sm:text-right">
              <span class="text-purple-300 font-medium">Triage:</span> ${escapeHtml(ai.recommended_triage || 'N/A')}
            </div>
          </div>
        </div>
      </div>
    `;
  }

  container.innerHTML = html;
}

function escapeHtml(text) {
  if (!text) return '';
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function toggleLogPause() {
  isLogStreamPaused = !isLogStreamPaused;
  const btn = document.getElementById('log-pause-btn');
  const text = document.getElementById('log-pause-text');
  const icon = document.getElementById('log-pause-icon');

  if (isLogStreamPaused) {
    text.innerText = 'Resume Stream';
    btn.className = 'flex items-center space-x-1.5 bg-amber-600 hover:bg-amber-500 text-white px-3 py-1.5 rounded-lg transition font-medium';
    icon.setAttribute('data-lucide', 'play');
  } else {
    text.innerText = 'Pause Stream';
    btn.className = 'flex items-center space-x-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded-lg border border-slate-700 transition';
    icon.setAttribute('data-lucide', 'pause');
    pollDashboardData();
  }
  initLucide();
}

function applyLogFilters() {
  selectedLogAp = document.getElementById('log-filter-ap').value;
  selectedLogSeverity = document.getElementById('log-filter-sev').value;
  pollDashboardData();
}

// Custom Log Tester
function openCustomLogModal() {
  document.getElementById('custom-log-modal').classList.remove('hidden');
}

function closeCustomLogModal() {
  document.getElementById('custom-log-modal').classList.add('hidden');
  document.getElementById('custom-log-result').classList.add('hidden');
}

function setLogPreset(presetId) {
  const input = document.getElementById('custom-log-input');
  const apSelect = document.getElementById('custom-log-ap');

  if (presetId === 1) {
    input.value = "[CRIT] ath11k_pci 0000:01:00.0: Target firmware crashed! (assert: 0xDEADBEEF, pc: 0x8003F412)";
    apSelect.value = "AP-B204";
  } else if (presetId === 2) {
    input.value = "[WARN] netmon: WAN border gateway 10.14.0.1 BGP peer flapping (NREN optical hold timer expired)";
    apSelect.value = "GATEWAY";
  } else if (presetId === 3) {
    input.value = "[WARN] wlan0: High BSS co-channel interference detected (airtime duty cycle 97.4%)";
    apSelect.value = "AP-LIB-G";
  } else if (presetId === 4) {
    input.value = "[INFO] hostapd: STA authenticated successfully (AES-CCMP / 802.11ax)";
    apSelect.value = "AP-A101";
  }
}

async function runCustomLogInterpretation() {
  const rawLog = document.getElementById('custom-log-input').value.trim();
  const apId = document.getElementById('custom-log-ap').value;
  const resultContainer = document.getElementById('custom-log-result');

  if (!rawLog) {
    alert('Please enter or select a log string first.');
    return;
  }

  try {
    const res = await fetch('/api/logs/interpret', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ log: rawLog, ap_id: apId })
    });
    const data = await res.json();

    const ai = data.initial_ai_result || {};
    const signalsHtml = Object.entries(ai.feature_weights || {}).map(([k, v]) => `
      <span class="bg-slate-900 border border-slate-700 rounded px-1.5 py-0.5 text-[10px] text-slate-300 font-mono">
        ${k}: <strong class="text-purple-300">${Math.round(v * 100)}%</strong>
      </span>
    `).join(' ');

    resultContainer.innerHTML = `
      <div class="glass-panel rounded-xl p-3 bg-purple-950/30 border border-purple-500/40 space-y-2">
        <div class="flex items-center justify-between text-xs">
          <span class="font-bold text-purple-300 flex items-center gap-1.5">
            <i data-lucide="sparkles" class="w-3.5 h-3.5"></i>
            Initial AI Classification: ${data.ai_classification}
          </span>
          <span class="font-mono text-xs text-slate-300">Confidence: <strong>${ai.confidence_pct}%</strong></span>
        </div>
        <p class="text-xs text-white font-medium">${escapeHtml(ai.summary)}</p>
        <p class="text-xs text-slate-300 leading-relaxed">${escapeHtml(ai.interpretability_explanation)}</p>
        <div class="pt-1.5 border-t border-purple-500/20 flex flex-wrap items-center justify-between gap-1 text-[11px]">
          <div class="flex items-center gap-1">
            <span class="text-slate-400 text-[10px]">Signal Weights:</span>
            ${signalsHtml}
          </div>
          <div class="text-slate-200">
            <strong>Triage:</strong> ${escapeHtml(ai.recommended_triage)}
          </div>
        </div>
      </div>
    `;
    resultContainer.classList.remove('hidden');
    initLucide();
  } catch (err) {
    alert('Failed to interpret log: ' + err.message);
  }
}
