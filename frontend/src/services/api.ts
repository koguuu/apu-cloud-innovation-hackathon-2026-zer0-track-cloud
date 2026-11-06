import type { BackendState, HealthResponse, IngestResponse } from '../types';

export interface ApiConfig {
  baseUrl: string;
  dashboardKey?: string;
  ingestKey?: string;
}

export const DEFAULT_CONFIG: ApiConfig = {
  baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  dashboardKey: import.meta.env.VITE_DASHBOARD_API_KEY || '',
  ingestKey: import.meta.env.VITE_INGEST_API_KEY || '',
};

function getHeaders(key?: string): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  if (key && key.trim()) {
    headers['X-API-Key'] = key.trim();
  }
  return headers;
}

export async function fetchState(config: ApiConfig = DEFAULT_CONFIG): Promise<BackendState> {
  const url = `${config.baseUrl.replace(/\/$/, '')}/state`;
  const res = await fetch(url, {
    method: 'GET',
    headers: getHeaders(config.dashboardKey),
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => '');
    throw new Error(`Failed to fetch state (${res.status}): ${errorText || res.statusText}`);
  }

  return res.json();
}

export async function checkHealth(config: ApiConfig = DEFAULT_CONFIG): Promise<HealthResponse> {
  const url = `${config.baseUrl.replace(/\/$/, '')}/health`;
  const res = await fetch(url, {
    method: 'GET',
  });

  if (!res.ok) {
    throw new Error(`Health check failed (${res.status})`);
  }

  return res.json();
}

export async function resolveTicket(
  ticketId: string,
  config: ApiConfig = DEFAULT_CONFIG
): Promise<unknown> {
  const url = `${config.baseUrl.replace(/\/$/, '')}/tickets/${encodeURIComponent(ticketId)}/resolve`;
  const res = await fetch(url, {
    method: 'POST',
    headers: getHeaders(config.dashboardKey),
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => '');
    throw new Error(`Failed to resolve ticket (${res.status}): ${errorText || res.statusText}`);
  }

  return res.json();
}

export async function resetCampus(config: ApiConfig = DEFAULT_CONFIG): Promise<{ status: string }> {
  const url = `${config.baseUrl.replace(/\/$/, '')}/admin/reset`;
  const res = await fetch(url, {
    method: 'POST',
    headers: getHeaders(config.ingestKey),
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => '');
    throw new Error(`Failed to reset campus (${res.status}): ${errorText || res.statusText}`);
  }

  return res.json();
}

export async function sendEventsBatch(
  events: unknown[],
  config: ApiConfig = DEFAULT_CONFIG
): Promise<IngestResponse> {
  const url = `${config.baseUrl.replace(/\/$/, '')}/events/batch`;
  const res = await fetch(url, {
    method: 'POST',
    headers: getHeaders(config.ingestKey),
    body: JSON.stringify(events),
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => '');
    throw new Error(`Failed to send event batch (${res.status}): ${errorText || res.statusText}`);
  }

  return res.json();
}

// ---------------------------------------------------------------------------
// Simulation helpers (generates the required 3 consecutive readings)
// ---------------------------------------------------------------------------

function makeEventId(): string {
  return 'sim-' + Math.random().toString(36).substring(2, 11) + '-' + Date.now();
}

function getTimestamp(): string {
  return new Date().toISOString();
}

export async function simulateKillAp(
  apId: string = 'ap-b-02',
  locationId: string = 'block-b',
  config: ApiConfig = DEFAULT_CONFIG
): Promise<IngestResponse> {
  // 3 bad telemetry readings to trip detection rule
  const events = [1, 2, 3].map(() => ({
    event_type: 'wifi_telemetry',
    event_id: makeEventId(),
    timestamp: getTimestamp(),
    location_id: locationId,
    ap_id: apId,
    metrics: {
      latency_ms: 920,
      packet_loss_pct: 100,
      rssi_dbm: -92,
      clients: 38,
    },
    syslog: ['RADIO_FAILURE: interface wlan0 unresponsive', 'BEACON_LOSS: timeout'],
  }));

  return sendEventsBatch(events, config);
}

export async function simulateCongestion(
  locationId: string = 'block-a',
  apId: string = 'ap-a-01',
  config: ApiConfig = DEFAULT_CONFIG
): Promise<IngestResponse> {
  // High latency, low loss, good RSSI, 150+ clients
  const events = [1, 2, 3].map(() => ({
    event_type: 'wifi_telemetry',
    event_id: makeEventId(),
    timestamp: getTimestamp(),
    location_id: locationId,
    ap_id: apId,
    metrics: {
      latency_ms: 380,
      packet_loss_pct: 1.5,
      rssi_dbm: -55,
      clients: 180,
    },
    syslog: ['QUEUE_OVERFLOW: client buffer full', 'CHANNEL_UTIL: 96%'],
  }));

  return sendEventsBatch(events, config);
}

export async function simulateLabDown(
  labId: string = 'lab-network',
  config: ApiConfig = DEFAULT_CONFIG
): Promise<IngestResponse> {
  // All APs in the lab dead
  const aps = labId === 'lab-network' ? ['ap-n-01', 'ap-n-02'] : ['ap-ai-01', 'ap-ai-02'];
  const events: unknown[] = [];

  for (const ap of aps) {
    for (let i = 0; i < 3; i++) {
      events.push({
        event_type: 'wifi_telemetry',
        event_id: makeEventId(),
        timestamp: getTimestamp(),
        location_id: labId,
        ap_id: ap,
        metrics: {
          latency_ms: 999,
          packet_loss_pct: 100,
          rssi_dbm: -95,
          clients: 10,
        },
        syslog: ['SWITCH_LINK_DOWN: port ge-0/0/1 carrier lost'],
      });
    }
  }

  return sendEventsBatch(events, config);
}

export async function simulateUplinkOutage(
  config: ApiConfig = DEFAULT_CONFIG
): Promise<IngestResponse> {
  // Fail APs across 3+ locations (Block A, Block B, Labs)
  const targets = [
    { loc: 'block-a', ap: 'ap-a-01' },
    { loc: 'block-a', ap: 'ap-a-02' },
    { loc: 'block-b', ap: 'ap-b-01' },
    { loc: 'block-b', ap: 'ap-b-02' },
    { loc: 'lab-ai', ap: 'ap-ai-01' },
    { loc: 'lab-cyber', ap: 'ap-cy-01' },
    { loc: 'lab-network', ap: 'ap-n-01' },
  ];

  const events: unknown[] = [];
  for (const t of targets) {
    for (let i = 0; i < 3; i++) {
      events.push({
        event_type: 'wifi_telemetry',
        event_id: makeEventId(),
        timestamp: getTimestamp(),
        location_id: t.loc,
        ap_id: t.ap,
        metrics: {
          latency_ms: 950,
          packet_loss_pct: 100,
          rssi_dbm: -88,
          clients: 25,
        },
        syslog: ['DNS_RESOLV_FAIL: upstream gateway unreachable'],
      });
    }
  }

  return sendEventsBatch(events, config);
}

export async function simulateIotFault(
  deviceId: string = 'reader-net-01',
  locationId: string = 'lab-network',
  config: ApiConfig = DEFAULT_CONFIG
): Promise<IngestResponse> {
  const events = [1, 2, 3].map(() => ({
    event_type: 'iot_health',
    event_id: makeEventId(),
    timestamp: getTimestamp(),
    location_id: locationId,
    device_id: deviceId,
    device_type: 'card_reader',
    status: 'down',
    detail: 'Hardware tamper alert / power failure',
  }));

  return sendEventsBatch(events, config);
}

export async function simulateHealthyCampus(
  config: ApiConfig = DEFAULT_CONFIG
): Promise<IngestResponse> {
  // Send 3 good readings across all locations so all tripped tickets auto-resolve
  const apList = [
    { loc: 'block-a', ap: 'ap-a-01' },
    { loc: 'block-a', ap: 'ap-a-02' },
    { loc: 'block-b', ap: 'ap-b-01' },
    { loc: 'block-b', ap: 'ap-b-02' },
    { loc: 'library', ap: 'ap-lib-01' },
    { loc: 'lab-ai', ap: 'ap-ai-01' },
    { loc: 'lab-cyber', ap: 'ap-cy-01' },
    { loc: 'lab-network', ap: 'ap-n-01' },
    { loc: 'lab-network', ap: 'ap-n-02' },
    { loc: 'lab-iot', ap: 'ap-i-01' },
  ];

  const deviceList = [
    { loc: 'lab-network', id: 'reader-net-01', type: 'card_reader' },
    { loc: 'lab-ai', id: 'reader-ai-01', type: 'card_reader' },
    { loc: 'lab-cyber', id: 'reader-cy-01', type: 'card_reader' },
    { loc: 'lab-iot', id: 'reader-iot-01', type: 'card_reader' },
  ];

  const events: unknown[] = [];

  for (const a of apList) {
    for (let i = 0; i < 3; i++) {
      events.push({
        event_type: 'wifi_telemetry',
        event_id: makeEventId(),
        timestamp: getTimestamp(),
        location_id: a.loc,
        ap_id: a.ap,
        metrics: {
          latency_ms: 25 + Math.floor(Math.random() * 20),
          packet_loss_pct: 0.1,
          rssi_dbm: -52,
          clients: 28,
        },
        syslog: [],
      });
    }
  }

  for (const d of deviceList) {
    for (let i = 0; i < 3; i++) {
      events.push({
        event_type: 'iot_health',
        event_id: makeEventId(),
        timestamp: getTimestamp(),
        location_id: d.loc,
        device_id: d.id,
        device_type: d.type,
        status: 'ok',
        detail: 'Normal operation',
      });
    }
  }

  return sendEventsBatch(events, config);
}
