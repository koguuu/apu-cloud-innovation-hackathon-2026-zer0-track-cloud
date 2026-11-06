import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { ZoneCard } from './ZoneCard';
import type { ZoneStatus } from '../types';
import {
  Compass,
  AlertTriangle,
  CheckCircle,
  Sparkles,
  BookOpen,
  ArrowRight,
  TrendingUp,
  MapPin,
  Clock,
  ShieldCheck,
  Send,
  Zap,
} from 'lucide-react';

export const StudentView: React.FC = () => {
  const { state } = useApp();
  const [filterType, setFilterType] = useState<'all' | 'labs' | 'blocks'>('labs');
  const [selectedLabNotification, setSelectedLabNotification] = useState<string | null>(null);

  // Stretch feature state: "What should I pursue next?"
  const [customQuestion, setCustomQuestion] = useState('');
  const [aiAnswer, setAiAnswer] = useState<string | null>(null);
  const [selectedModuleTrack, setSelectedModuleTrack] = useState<'iot' | 'ai' | 'networking'>('iot');

  const bestLab = state?.best_lab;
  const activeAdvisories = state?.active_advisories ?? [];
  const zones = state?.zones ?? [];

  const filteredZones = zones.filter((z) => {
    if (filterType === 'labs') return z.location_id.startsWith('lab-');
    if (filterType === 'blocks') return !z.location_id.startsWith('lab-');
    return true;
  });

  const handleSelectLab = (lab: ZoneStatus) => {
    setSelectedLabNotification(`Directing Raja to ${lab.name}. Walkway routing active: Floor 3 East Wing.`);
    setTimeout(() => setSelectedLabNotification(null), 5000);
  };

  const generateGuidance = (track: 'iot' | 'ai' | 'networking', question?: string) => {
    if (track === 'iot') {
      setAiAnswer(
        question
          ? `Based on your 24 lab hours in the IoT Lab and question "${question}": You have strong fundamentals in sensor telemetry and MQTT bus architecture. We recommend advancing into Edge Computing with FreeRTOS and Secure Gateway Firmware in Lab IoT.`
          : 'Based on your 24 hours in the IoT Lab: You have mastered Microcontroller Interfacing and Protocol Decoding. Your optimal next milestone is Module IOT-304: Distributed Sensor Networks & Cloud Integration in IoT Lab.'
      );
    } else if (track === 'ai') {
      setAiAnswer(
        'Based on your 18 hours in the AI Lab: You completed Deep Learning Inference on TensorRT. Your recommended next step is Module AI-402: Autonomous Edge Robotics & Vision Transformers in AI Lab.'
      );
    } else {
      setAiAnswer(
        'Based on your 12 hours in the Networking Lab: You verified BGP Peering and VLAN Trunking. We suggest enrolling in Module NET-301: Software-Defined Networking (SDN) & OpenFlow automation.'
      );
    }
  };

  return (
    <div className="student-view">
      {/* Toast Notification */}
      {selectedLabNotification && (
        <div className="toast-notification">
          <CheckCircle size={18} />
          <span>{selectedLabNotification}</span>
        </div>
      )}

      {/* Hero Welcome Header */}
      <section className="student-hero">
        <div className="hero-content">
          <div className="hero-badge">
            <Compass size={15} /> Student Navigator & Companion
          </div>
          <h1 className="hero-title">
            Welcome back, <span className="highlight-name">Raja</span> 👋
          </h1>
          <p className="hero-subtitle">
            Autonomous campus telemetry watches all APU labs so you always find a free seat and
            high-speed Wi-Fi.
          </p>
        </div>

        <div className="student-stats-card">
          <div className="stat-pill">
            <span className="stat-label">Student ID</span>
            <span className="stat-value">s_9f2c41ab</span>
          </div>
          <div className="stat-pill">
            <span className="stat-label">Logged Lab Time</span>
            <span className="stat-value">62 Hours</span>
          </div>
          <div className="stat-pill">
            <span className="stat-label">Favorite Lab</span>
            <span className="stat-value">IoT & AI Labs</span>
          </div>
        </div>
      </section>

      {/* Active Advisories Banner (Incident Alerts & Rerouting) */}
      {activeAdvisories.length > 0 && (
        <section className="advisories-section">
          {activeAdvisories.map((adv) => (
            <div key={adv.advisory_id} className="advisory-banner incident-banner">
              <div className="advisory-icon-wrapper">
                <AlertTriangle size={24} className="icon-pulse" />
              </div>
              <div className="advisory-body">
                <div className="advisory-title-row">
                  <span className="advisory-badge">Active Campus Incident Advisory</span>
                  <span className="advisory-id">{adv.advisory_id}</span>
                </div>
                <p className="advisory-text">{adv.message}</p>
                {adv.suggested_location && (
                  <div className="advisory-reroute">
                    <Zap size={15} />
                    <span>
                      Rerouting recommendation: Head to{' '}
                      <strong>{adv.suggested_location.toUpperCase()}</strong> for guaranteed seating and healthy Wi-Fi.
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </section>
      )}

      {/* Hero Recommendation: Best Lab Right Now */}
      <section className="best-lab-section">
        <div className="section-header">
          <div>
            <h2 className="section-title">
              <Sparkles size={20} className="text-accent" /> Recommended Lab for You Right Now
            </h2>
            <p className="section-desc">
              Ranked dynamically by free seats, Wi-Fi latency, and IoT hardware health.
            </p>
          </div>
        </div>

        {bestLab ? (
          <div className="best-lab-hero-card">
            <div className="hero-card-left">
              <div className="badge-featured">Top Recommendation</div>
              <h3 className="hero-lab-name">{bestLab.name}</h3>
              <div className="hero-lab-meta">
                <span className="meta-item">
                  <MapPin size={16} /> APU Technology Wing
                </span>
                <span className="meta-item">
                  <Clock size={16} /> Open Now (Closes 21:00)
                </span>
                <span className="meta-item">
                  <ShieldCheck size={16} /> Wi-Fi Verified 100% Operational
                </span>
              </div>

              <div className="hero-seats-row">
                <div className="seats-counter">
                  <span className="seats-large">{bestLab.seats_free}</span>
                  <span className="seats-subtext">Free Seats Available (out of {bestLab.seats_total})</span>
                </div>
                <div className="health-counter">
                  <span className="health-score-large">{(bestLab.score * 100).toFixed(0)}</span>
                  <span className="health-subtext">Optimal Match Score</span>
                </div>
              </div>

              <button
                type="button"
                className="btn-head-to-lab"
                onClick={() => handleSelectLab(bestLab)}
              >
                <span>Navigate Raja Here</span>
                <ArrowRight size={18} />
              </button>
            </div>

            <div className="hero-card-right">
              <div className="lab-radar-box">
                <div className="radar-metric">
                  <span className="radar-label">Wi-Fi Status</span>
                  <span className="radar-value text-green">Good ({bestLab.wifi_health.toUpperCase()})</span>
                </div>
                <div className="radar-metric">
                  <span className="radar-label">IoT Telemetry</span>
                  <span className="radar-value text-green">All Devices Healthy</span>
                </div>
                <div className="radar-metric">
                  <span className="radar-label">Current Occupancy</span>
                  <span className="radar-value">
                    {Math.round(((bestLab.seats_total - bestLab.seats_free) / bestLab.seats_total) * 100)}%
                  </span>
                </div>
                <div className="radar-metric">
                  <span className="radar-label">Noise & Disturbance</span>
                  <span className="radar-value text-green">Low (Quiet Study)</span>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="no-lab-warning">
            <AlertTriangle size={24} />
            <div>
              <strong>No Optimal Labs Available Currently</strong>
              <p>All labs are either congested, undergoing maintenance, or affected by campus network outage.</p>
            </div>
          </div>
        )}
      </section>

      {/* Campus All Zones & Labs Directory */}
      <section className="directory-section">
        <div className="directory-header">
          <div>
            <h2 className="section-title">Explore All Campus Labs & Zones</h2>
            <p className="section-desc">Real-time occupancy and network signals across campus</p>
          </div>

          <div className="filter-pill-group">
            <button
              type="button"
              className={`filter-pill ${filterType === 'labs' ? 'active' : ''}`}
              onClick={() => setFilterType('labs')}
            >
              Specialized Labs
            </button>
            <button
              type="button"
              className={`filter-pill ${filterType === 'blocks' ? 'active' : ''}`}
              onClick={() => setFilterType('blocks')}
            >
              Academic Blocks
            </button>
            <button
              type="button"
              className={`filter-pill ${filterType === 'all' ? 'active' : ''}`}
              onClick={() => setFilterType('all')}
            >
              All Zones ({zones.length})
            </button>
          </div>
        </div>

        <div className="zones-grid">
          {filteredZones.map((zone) => (
            <ZoneCard
              key={zone.location_id}
              zone={zone}
              isBest={zone.location_id === bestLab?.location_id}
              onSelect={handleSelectLab}
            />
          ))}
        </div>
      </section>

      {/* Stretch Feature: Raja's Lab Record & "What should I pursue next?" Advisor */}
      <section className="learning-advisor-section">
        <div className="advisor-header">
          <div className="advisor-title-group">
            <BookOpen className="advisor-icon" size={24} />
            <div>
              <h2 className="section-title">
                Raja's Lab Record & Learning Pathway
                <span className="badge-stretch">Stretch Feature</span>
              </h2>
              <p className="section-desc">
                Anonymized lab hours turn into smart guidance: "What should I pursue next?"
              </p>
            </div>
          </div>
        </div>

        <div className="advisor-grid">
          {/* Left: Lab Hours Tracker */}
          <div className="hours-card">
            <h3 className="hours-card-title">
              <TrendingUp size={18} /> Verified Hands-on Hours
            </h3>
            <div className="hours-list">
              <div
                className={`hour-row ${selectedModuleTrack === 'iot' ? 'selected' : ''}`}
                onClick={() => {
                  setSelectedModuleTrack('iot');
                  generateGuidance('iot');
                }}
              >
                <div className="hour-info">
                  <strong>Internet of Things (IoT Lab)</strong>
                  <span>24 hours • Completed 4 modules</span>
                </div>
                <div className="hour-pill">24 hrs</div>
              </div>

              <div
                className={`hour-row ${selectedModuleTrack === 'ai' ? 'selected' : ''}`}
                onClick={() => {
                  setSelectedModuleTrack('ai');
                  generateGuidance('ai');
                }}
              >
                <div className="hour-info">
                  <strong>Artificial Intelligence (AI Lab)</strong>
                  <span>18 hours • Completed 3 modules</span>
                </div>
                <div className="hour-pill">18 hrs</div>
              </div>

              <div
                className={`hour-row ${selectedModuleTrack === 'networking' ? 'selected' : ''}`}
                onClick={() => {
                  setSelectedModuleTrack('networking');
                  generateGuidance('networking');
                }}
              >
                <div className="hour-info">
                  <strong>Computer Networking (Networking Lab)</strong>
                  <span>12 hours • Completed 2 modules</span>
                </div>
                <div className="hour-pill">12 hrs</div>
              </div>
            </div>
          </div>

          {/* Right: AI Guidance Dialogue */}
          <div className="guidance-card">
            <div className="guidance-card-header">
              <Sparkles size={18} className="text-accent" />
              <strong>Gemini Career & Skill Pathway Advisor</strong>
            </div>

            <div className="guidance-body">
              <p className="guidance-prompt">
                {aiAnswer ||
                  'Based on your 24 hours in the IoT Lab: You have mastered Microcontroller Interfacing and Protocol Decoding. Your optimal next milestone is Module IOT-304: Distributed Sensor Networks & Cloud Integration in IoT Lab.'}
              </p>

              <form
                className="guidance-input-form"
                onSubmit={(e) => {
                  e.preventDefault();
                  if (customQuestion.trim()) {
                    generateGuidance(selectedModuleTrack, customQuestion);
                  }
                }}
              >
                <input
                  type="text"
                  placeholder="Ask Raja's companion: What should I pursue next?"
                  value={customQuestion}
                  onChange={(e) => setCustomQuestion(e.target.value)}
                  className="guidance-input"
                />
                <button type="submit" className="btn-send-guidance" title="Send question">
                  <Send size={16} />
                </button>
              </form>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
