import React from 'react';
import { useApp } from '../context/AppContext';
import { TicketCard } from './TicketCard';
import {
  ShieldAlert,
  Server,
  Users,
  Cpu,
  Wifi,
  Bell,
  CheckCircle2,
  AlertOctagon,
  Radio,
  Clock,
  Sparkles,
} from 'lucide-react';

export const StaffDashboard: React.FC = () => {
  const { state, resolveTicket } = useApp();

  const zones = state?.zones ?? [];
  const openTickets = state?.open_tickets ?? [];
  const notifications = state?.recent_notifications ?? [];
  const advisories = state?.active_advisories ?? [];

  const totalSeats = zones.reduce((acc, z) => acc + z.seats_total, 0);
  const freeSeats = zones.reduce((acc, z) => acc + z.seats_free, 0);
  const totalIotDown = zones.reduce((acc, z) => acc + z.iot_devices_down, 0);
  const degradedZonesCount = zones.filter(
    (z) => z.wifi_health === 'degraded' || z.wifi_health === 'down'
  ).length;

  return (
    <div className="staff-dashboard">
      {/* Header */}
      <section className="staff-header">
        <div>
          <div className="staff-badge">
            <ShieldAlert size={15} /> Campus Operations & IT Command Center
          </div>
          <h1 className="staff-title">Autonomous Infrastructure Health</h1>
          <p className="staff-subtitle">
            AI-driven continuous monitoring, multi-zone anomaly detection, and Gemini automated root cause diagnostics.
          </p>
        </div>

        <div className="agent-status-card">
          <div className="agent-indicator">
            <span className="agent-pulse-dot" />
            <Sparkles size={16} className="text-accent" />
            <strong>Autonomous Campus Agent</strong>
          </div>
          <p className="agent-subtext">3-streak threshold active • Gemini enrichment enabled</p>
        </div>
      </section>

      {/* KPI Stats Cards */}
      <section className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-icon-wrapper bg-blue">
            <Server size={20} />
          </div>
          <div className="kpi-details">
            <span className="kpi-label">Monitored Zones</span>
            <div className="kpi-value-row">
              <span className="kpi-value">{zones.length}</span>
              <span className="kpi-sub">Campus locations</span>
            </div>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-icon-wrapper bg-green">
            <Users size={20} />
          </div>
          <div className="kpi-details">
            <span className="kpi-label">Campus Seating</span>
            <div className="kpi-value-row">
              <span className="kpi-value">{freeSeats}</span>
              <span className="kpi-sub">/ {totalSeats} free</span>
            </div>
          </div>
        </div>

        <div className={`kpi-card ${openTickets.length > 0 ? 'kpi-alert' : ''}`}>
          <div className={`kpi-icon-wrapper ${openTickets.length > 0 ? 'bg-red' : 'bg-green'}`}>
            <AlertOctagon size={20} />
          </div>
          <div className="kpi-details">
            <span className="kpi-label">Active Incidents</span>
            <div className="kpi-value-row">
              <span className="kpi-value">{openTickets.length}</span>
              <span className="kpi-sub">{openTickets.length > 0 ? 'Action required' : 'All clear'}</span>
            </div>
          </div>
        </div>

        <div className={`kpi-card ${totalIotDown > 0 ? 'kpi-warning' : ''}`}>
          <div className={`kpi-icon-wrapper ${totalIotDown > 0 ? 'bg-amber' : 'bg-green'}`}>
            <Cpu size={20} />
          </div>
          <div className="kpi-details">
            <span className="kpi-label">IoT Devices Down</span>
            <div className="kpi-value-row">
              <span className="kpi-value">{totalIotDown}</span>
              <span className="kpi-sub">{degradedZonesCount} degraded APs</span>
            </div>
          </div>
        </div>
      </section>

      {/* Active Incidents & IT Tickets Section */}
      <section className="tickets-section">
        <div className="section-header">
          <div className="header-left">
            <h2 className="section-title">
              <AlertOctagon size={20} className="text-red" />
              Active Incidents & Gemini Diagnostic Tickets ({openTickets.length})
            </h2>
            <p className="section-desc">
              Tickets generated autonomously by engine rules and enriched by Gemini AI.
            </p>
          </div>
        </div>

        {openTickets.length > 0 ? (
          <div className="tickets-grid">
            {openTickets.map((ticket) => (
              <TicketCard
                key={ticket.ticket_id}
                ticket={ticket}
                onResolve={resolveTicket}
              />
            ))}
          </div>
        ) : (
          <div className="empty-tickets-card">
            <CheckCircle2 size={40} className="text-green" />
            <div className="empty-tickets-text">
              <h3>Zero Active Incidents</h3>
              <p>
                All Wi-Fi access points and IoT hardware readers across Block A, Block B, Library,
                and specialized labs are reporting healthy telemetry.
              </p>
            </div>
          </div>
        )}
      </section>

      {/* Detailed Campus Zones Table */}
      <section className="zones-table-section">
        <div className="section-header">
          <div>
            <h2 className="section-title">
              <Radio size={20} className="text-accent" />
              Campus Zones Telemetry Matrix
            </h2>
            <p className="section-desc">Comprehensive real-time view across all blocks and labs.</p>
          </div>
        </div>

        <div className="table-responsive">
          <table className="telemetry-table">
            <thead>
              <tr>
                <th>Zone / Location</th>
                <th>Category</th>
                <th>Capacity</th>
                <th>Current Occupancy</th>
                <th>Free Seats</th>
                <th>Wi-Fi Signal</th>
                <th>IoT Devices</th>
                <th>Health Score</th>
              </tr>
            </thead>
            <tbody>
              {zones.map((zone) => {
                const occupancy = zone.seats_total - zone.seats_free;
                const occPct = Math.round((occupancy / zone.seats_total) * 100);

                return (
                  <tr key={zone.location_id}>
                    <td>
                      <strong className="zone-table-name">{zone.name}</strong>
                      <div className="zone-table-id">{zone.location_id}</div>
                    </td>
                    <td>
                      <span className="zone-type-badge">
                        {zone.location_id.startsWith('lab-')
                          ? 'Specialized Lab'
                          : zone.location_id === 'library'
                          ? 'Library'
                          : 'Academic Block'}
                      </span>
                    </td>
                    <td>{zone.seats_total}</td>
                    <td>
                      <div className="table-occupancy">
                        <span>{occupancy} ({occPct}%)</span>
                        <div className="mini-progress-bg">
                          <div
                            className={`mini-progress-fill ${
                              occPct >= 90 ? 'bg-red' : occPct >= 70 ? 'bg-amber' : 'bg-green'
                            }`}
                            style={{ width: `${occPct}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td>
                      <strong className="text-seats-free">{zone.seats_free}</strong>
                    </td>
                    <td>
                      <span className={`table-badge badge-${zone.wifi_health}`}>
                        {zone.wifi_health === 'unknown' ? 'NO SENSORS' : zone.wifi_health.toUpperCase()}
                      </span>
                    </td>
                    <td>
                      {zone.iot_devices_down > 0 ? (
                        <span className="table-badge badge-down">
                          {zone.iot_devices_down} Faulty
                        </span>
                      ) : (
                        <span className="table-badge badge-good">Healthy</span>
                      )}
                    </td>
                    <td>
                      <div className="table-score">
                        <span className="score-num">{(zone.score * 100).toFixed(0)}</span>
                        <span className="score-max">/100</span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* Two Column Section: Outbound Telegram Feed & Advisories */}
      <section className="logs-two-col">
        {/* Telegram Admin Notifications */}
        <div className="log-panel">
          <div className="log-panel-header">
            <div className="panel-title-group">
              <Bell size={18} className="text-accent" />
              <h3>Telegram Admin Alerts Dispatch</h3>
            </div>
            <span className="panel-count">{notifications.length} alerts</span>
          </div>

          <div className="log-list">
            {notifications.length > 0 ? (
              notifications.map((notif) => (
                <div key={notif.notification_id} className="notification-item">
                  <div className="notif-header">
                    <span className="notif-id">{notif.notification_id}</span>
                    <span className="notif-ticket">Ticket: {notif.ticket_id}</span>
                    <span className={`delivery-pill ${notif.sent ? 'sent' : 'not-delivered'}`}>
                      {notif.sent ? 'Delivered to Admin' : 'Not delivered'}
                    </span>
                  </div>
                  <p className="notif-text">{notif.text}</p>
                  <div className="notif-time">
                    <Clock size={12} />
                    <span>{new Date(notif.created_at).toLocaleTimeString()}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="empty-log">No recent alerts dispatched.</div>
            )}
          </div>
        </div>

        {/* Student Advisories Feed */}
        <div className="log-panel">
          <div className="log-panel-header">
            <div className="panel-title-group">
              <Wifi size={18} className="text-accent" />
              <h3>Student Campus Advisories Broadcast</h3>
            </div>
            <span className="panel-count">{advisories.length} active</span>
          </div>

          <div className="log-list">
            {advisories.length > 0 ? (
              advisories.map((adv) => (
                <div key={adv.advisory_id} className="advisory-item">
                  <div className="adv-item-header">
                    <span className="adv-id">{adv.advisory_id}</span>
                    <span className={`adv-kind ${adv.kind}`}>
                      {adv.kind.toUpperCase()}
                    </span>
                  </div>
                  <p className="adv-message">{adv.message}</p>
                  {adv.suggested_location && (
                    <div className="adv-redirect">
                      Redirecting students to: <strong>{adv.suggested_location.toUpperCase()}</strong>
                    </div>
                  )}
                  <div className="adv-time">
                    <Clock size={12} />
                    <span>{new Date(adv.created_at).toLocaleTimeString()}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="empty-log">No active student advisories. Campus normal.</div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
};
