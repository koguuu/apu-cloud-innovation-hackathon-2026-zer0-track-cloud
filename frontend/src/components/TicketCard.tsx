import React, { useState } from 'react';
import type { Ticket, RootCause } from '../types';
import {
  AlertTriangle,
  Bot,
  Wrench,
  CheckCircle2,
  Clock,
  Radio,
  Cpu,
  MapPin,
} from 'lucide-react';

interface TicketCardProps {
  ticket: Ticket;
  onResolve: (ticketId: string) => Promise<void>;
}

export const TicketCard: React.FC<TicketCardProps> = ({ ticket, onResolve }) => {
  const [resolving, setResolving] = useState(false);

  const handleResolve = async () => {
    try {
      setResolving(true);
      await onResolve(ticket.ticket_id);
    } finally {
      setResolving(false);
    }
  };

  const formatRootCause = (cause: RootCause): string => {
    switch (cause) {
      case 'ap_hardware_failure':
        return 'AP Hardware Failure';
      case 'isp_uplink_outage':
        return 'ISP Uplink Outage (Campus-wide)';
      case 'congestion':
        return 'Network Congestion';
      case 'iot_device_fault':
        return 'IoT Device Fault';
      default:
        return 'Unclassified Anomaly';
    }
  };

  const getRootCauseBadgeClass = (cause: RootCause): string => {
    switch (cause) {
      case 'isp_uplink_outage':
        return 'badge-cause-outage';
      case 'ap_hardware_failure':
        return 'badge-cause-ap';
      case 'congestion':
        return 'badge-cause-congestion';
      case 'iot_device_fault':
        return 'badge-cause-iot';
      default:
        return 'badge-cause-unknown';
    }
  };

  return (
    <div className={`ticket-card severity-${ticket.severity}`}>
      <div className="ticket-card-header">
        <div className="ticket-meta-left">
          <span className="ticket-id-tag">{ticket.ticket_id}</span>
          <span className={`severity-badge sev-${ticket.severity}`}>
            <AlertTriangle size={13} /> {ticket.severity.toUpperCase()} PRIORITY
          </span>
          <span className={`root-cause-badge ${getRootCauseBadgeClass(ticket.root_cause)}`}>
            {formatRootCause(ticket.root_cause)}
          </span>
        </div>

        <div className="ticket-time">
          <Clock size={13} />
          <span>{new Date(ticket.created_at).toLocaleTimeString()}</span>
        </div>
      </div>

      <div className="ticket-location-row">
        <div className="location-item">
          <MapPin size={15} className="item-icon" />
          <span className="location-name">{ticket.location_id.toUpperCase()}</span>
        </div>

        {ticket.affected_aps.length > 0 && (
          <div className="location-item">
            <Radio size={15} className="item-icon" />
            <span>Affected APs: <strong>{ticket.affected_aps.join(', ')}</strong></span>
          </div>
        )}

        {ticket.affected_devices.length > 0 && (
          <div className="location-item">
            <Cpu size={15} className="item-icon" />
            <span>Devices: <strong>{ticket.affected_devices.join(', ')}</strong></span>
          </div>
        )}
      </div>

      {/* Gemini AI Root Cause Explanation Box */}
      <div className="gemini-explanation-box">
        <div className="gemini-header">
          <div className="gemini-badge">
            <Bot size={15} />
            <span>Gemini Root-Cause Intelligence</span>
          </div>
          <span className="gemini-tag">Automated Diagnosis</span>
        </div>
        <p className="gemini-text">{ticket.explanation}</p>
      </div>

      {/* Recommended Action */}
      <div className="recommended-action-box">
        <div className="action-header">
          <Wrench size={15} />
          <strong>Recommended IT Action:</strong>
        </div>
        <p className="action-text">{ticket.recommended_action}</p>
      </div>

      {/* Action Footer */}
      <div className="ticket-card-actions">
        <button
          type="button"
          className="btn-resolve-ticket"
          onClick={handleResolve}
          disabled={resolving || ticket.status === 'resolved'}
        >
          <CheckCircle2 size={16} />
          <span>{resolving ? 'Resolving Ticket...' : 'Mark Incident Resolved'}</span>
        </button>
      </div>
    </div>
  );
};
