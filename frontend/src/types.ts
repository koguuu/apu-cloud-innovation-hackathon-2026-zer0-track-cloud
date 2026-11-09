export type RootCause =
  | 'ap_hardware_failure'
  | 'isp_uplink_outage'
  | 'congestion'
  | 'iot_device_fault'
  | 'unknown';

export type WifiHealth = 'good' | 'degraded' | 'down' | 'unknown';
export type TicketSeverity = 'low' | 'medium' | 'high';
export type TicketStatus = 'open' | 'resolved';
export type AdvisoryKind = 'incident' | 'recovery';

export interface ZoneStatus {
  location_id: string;
  name: string;
  updated_at: string;
  seats_total: number;
  seats_free: number;
  wifi_health: WifiHealth;
  iot_devices_down: number;
  score: number;
}

export interface Ticket {
  ticket_id: string;
  created_at: string;
  severity: TicketSeverity;
  location_id: string;
  affected_aps: string[];
  affected_devices: string[];
  root_cause: RootCause;
  explanation: string;
  recommended_action: string;
  status: TicketStatus;
  resolved_at?: string | null;
  resolution_note?: string | null;
}

export interface Advisory {
  advisory_id: string;
  created_at: string;
  kind: AdvisoryKind;
  ticket_id: string;
  message: string;
  affected_locations: string[];
  suggested_location?: string | null;
}

export interface Notification {
  notification_id: string;
  created_at: string;
  channel: 'telegram';
  ticket_id: string;
  text: string;
  sent: boolean;
  error?: string | null;
}

export interface BackendState {
  updated_at: string;
  zones: ZoneStatus[];
  best_lab: ZoneStatus | null;
  open_tickets: Ticket[];
  active_advisories: Advisory[];
  recent_notifications: Notification[];
}

export interface HealthResponse {
  status: string;
  time: string;
}

export interface IngestResponse {
  accepted: number;
  duplicates: number;
  tickets_opened: string[];
  tickets_resolved: string[];
  rejected?: Array<{ index: number; error: string; details?: unknown }>;
}

export interface StudentModuleRecord {
  module_id: string;
  title: string;
  lab_type: 'ai' | 'cybersecurity' | 'networking' | 'iot';
  hours: number;
  status: 'completed' | 'in_progress' | 'recommended';
  level: string;
}
