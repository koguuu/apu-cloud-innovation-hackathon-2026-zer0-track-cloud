import React, { useState } from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { Navbar } from './components/Navbar';
import { DemoController } from './components/DemoController';
import { StudentView } from './components/StudentView';
import { StaffDashboard } from './components/StaffDashboard';
import { SettingsModal } from './components/SettingsModal';
import { AlertCircle, Terminal, RefreshCw } from 'lucide-react';
import './App.css';

const MainContent: React.FC = () => {
  const { currentView, connectionStatus, refresh, isLoading } = useApp();
  const [showSettings, setShowSettings] = useState(false);
  const [showDemoBar, setShowDemoBar] = useState(true);

  return (
    <div className="app-layout">
      <Navbar
        onOpenSettings={() => setShowSettings(true)}
        onToggleDemoBar={() => setShowDemoBar(!showDemoBar)}
        showDemoBar={showDemoBar}
      />

      {/* Demo Controls Bar */}
      <DemoController
        isOpen={showDemoBar}
        onToggle={() => setShowDemoBar(!showDemoBar)}
      />

      {/* Offline Alert Banner */}
      {connectionStatus === 'disconnected' && (
        <div className="backend-offline-banner">
          <div className="banner-left">
            <AlertCircle size={20} className="icon-pulse" />
            <div>
              <strong>Cannot Connect to Backend API</strong>
              <p>
                The frontend is trying to reach <code>http://localhost:8000</code>. Make sure the
                Starlette backend is running:
              </p>
            </div>
          </div>
          <div className="banner-cmd">
            <Terminal size={15} />
            <code>cd backend && uvicorn app.main:app --port 8000</code>
          </div>
          <button
            type="button"
            className="btn-retry-conn"
            onClick={() => refresh()}
            disabled={isLoading}
          >
            <RefreshCw size={15} className={isLoading ? 'btn-spinning' : ''} />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* Main Views */}
      <main className="main-content">
        {currentView === 'student' ? <StudentView /> : <StaffDashboard />}
      </main>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
      />

      {/* Footer */}
      <footer className="app-footer">
        <div className="footer-container">
          <div className="footer-left">
            <strong>Smart Lab Companion</strong> · APU Cloud Innovation Hackathon 2026
            <span className="track-tag">Track: Intelligent Automation & Digital Transformation</span>
          </div>
          <div className="footer-right">
            <span>Frontend by <strong>Pang Zai Yong</strong></span>
            <span className="footer-sep">·</span>
            <span>AI Root-Cause Agent (Gemini)</span>
            <span className="footer-sep">·</span>
            <span>Campus Telemetry Simulator</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AppProvider>
      <MainContent />
    </AppProvider>
  );
};

export default App;
