import React from 'react';
import { useApp } from '../context/AppContext';
import {
  GraduationCap,
  ShieldAlert,
  RotateCw,
  Settings,
  Sparkles,
  Zap,
} from 'lucide-react';

interface NavbarProps {
  onOpenSettings: () => void;
  onToggleDemoBar: () => void;
  showDemoBar: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  onOpenSettings,
  onToggleDemoBar,
  showDemoBar,
}) => {
  const { currentView, setView, connectionStatus, isLoading, refresh } = useApp();

  return (
    <header className="navbar">
      <div className="navbar-container">
        {/* Brand */}
        <div className="navbar-brand">
          <div className="logo-icon">
            <Sparkles className="icon-pulse" size={22} />
          </div>
          <div className="brand-text">
            <div className="brand-title">
              Smart Lab Companion
              <span className="badge-hackathon">APU 2026</span>
            </div>
            <div className="brand-subtitle">
              Intelligent Campus Wi-Fi & Lab Autonomous Agent
            </div>
          </div>
        </div>

        {/* View Switcher Persona Tabs */}
        <div className="view-switcher">
          <button
            type="button"
            className={`view-tab ${currentView === 'student' ? 'active' : ''}`}
            onClick={() => setView('student')}
          >
            <GraduationCap size={18} />
            <span>Student Companion (Raja)</span>
          </button>
          <button
            type="button"
            className={`view-tab ${currentView === 'staff' ? 'active' : ''}`}
            onClick={() => setView('staff')}
          >
            <ShieldAlert size={18} />
            <span>Staff IT Dashboard</span>
          </button>
        </div>

        {/* Right Actions & Status */}
        <div className="navbar-actions">
          {/* Connection status */}
          <div className={`status-pill status-${connectionStatus}`}>
            <span className="status-dot" />
            <span className="status-label">
              {connectionStatus === 'connected' && 'API Live'}
              {connectionStatus === 'connecting' && 'Connecting...'}
              {connectionStatus === 'disconnected' && 'Offline'}
            </span>
          </div>

          {/* Quick Refresh */}
          <button
            type="button"
            className={`action-btn ${isLoading ? 'btn-spinning' : ''}`}
            onClick={() => refresh()}
            title="Refresh state from backend"
          >
            <RotateCw size={17} />
          </button>

          {/* Demo Controls Bar Toggle */}
          <button
            type="button"
            className={`action-btn demo-btn ${showDemoBar ? 'active' : ''}`}
            onClick={onToggleDemoBar}
            title="Toggle Live Demo Controller"
          >
            <Zap size={17} />
            <span className="demo-btn-text">Demo Mode</span>
          </button>

          {/* Settings */}
          <button
            type="button"
            className="action-btn"
            onClick={onOpenSettings}
            title="API & System Settings"
          >
            <Settings size={17} />
          </button>
        </div>
      </div>
    </header>
  );
};
