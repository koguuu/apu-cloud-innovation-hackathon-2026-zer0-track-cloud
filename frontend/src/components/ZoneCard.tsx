import React from 'react';
import type { ZoneStatus } from '../types';
import {
  Wifi,
  WifiOff,
  AlertCircle,
  Users,
  CheckCircle,
  Star,
  Cpu,
  MapPin
} from 'lucide-react';

interface ZoneCardProps {
  zone: ZoneStatus;
  isBest?: boolean;
}

export const ZoneCard: React.FC<ZoneCardProps> = ({ zone, isBest }) => {
  const isLab = zone.location_id.startsWith('lab-');
  const occupancyPct = Math.round(
    ((zone.seats_total - zone.seats_free) / zone.seats_total) * 100
  );

  const getWifiBadge = () => {
    switch (zone.wifi_health) {
      case 'good':
        return (
          <span className="badge badge-wifi-good">
            <Wifi size={14} /> Good Signal
          </span>
        );
      case 'degraded':
        return (
          <span className="badge badge-wifi-degraded">
            <AlertCircle size={14} /> Degraded
          </span>
        );
      case 'down':
        return (
          <span className="badge badge-wifi-down">
            <WifiOff size={14} /> Offline
          </span>
        );
      case 'unknown':
      default:
        return (
          <span className="badge badge-wifi-unknown" title="No telemetry sensors installed in this zone">
            <WifiOff size={14} /> No sensors
          </span>
        );
    }
  };

  const getOccupancyColor = () => {
    if (occupancyPct >= 90) return 'progress-full';
    if (occupancyPct >= 70) return 'progress-busy';
    return 'progress-available';
  };

  return (
    <div
      className={`zone-card ${isBest ? 'best-lab-card' : ''} ${
        zone.wifi_health === 'down' ? 'zone-offline' : ''
      }`}
    >
      {isBest && (
        <div className="best-ribbon">
          <Star size={13} fill="currentColor" /> Best Match for Raja
        </div>
      )}

      <div className="zone-card-header">
        <div className="zone-title-group">
          <div className="zone-name-row">
            <MapPin size={17} className="zone-pin-icon" />
            <h3 className="zone-name">{zone.name}</h3>
          </div>
          <span className="zone-type-tag">
            {isLab ? 'Computer Lab' : zone.location_id === 'library' ? 'Library' : 'Academic Block'}
          </span>
        </div>

        <div className="zone-score-badge" title="Campus Smart Recommendation Score">
          <span className="score-label">Score</span>
          <span className="score-value">{(zone.score * 100).toFixed(0)}</span>
        </div>
      </div>

      <div className="zone-badges-row">
        {getWifiBadge()}

        {zone.iot_devices_down > 0 ? (
          <span className="badge badge-iot-warning" title={`${zone.iot_devices_down} IoT device faulty`}>
            <Cpu size={14} /> {zone.iot_devices_down} IoT Down
          </span>
        ) : (
          <span className="badge badge-iot-ok">
            <CheckCircle size={14} /> IoT OK
          </span>
        )}
      </div>

      {/* Seats Occupancy Meter */}
      <div className="occupancy-section">
        <div className="occupancy-labels">
          <span className="occupancy-seats">
            <Users size={15} />
            <strong>{zone.seats_free}</strong> seats free
            <span className="seats-total">/ {zone.seats_total} total</span>
          </span>
          <span className="occupancy-pct">{occupancyPct}% full</span>
        </div>

        <div className="progress-bar-bg">
          <div
            className={`progress-bar-fill ${getOccupancyColor()}`}
            style={{ width: `${occupancyPct}%` }}
          />
        </div>
      </div>

    </div>
  );
};
