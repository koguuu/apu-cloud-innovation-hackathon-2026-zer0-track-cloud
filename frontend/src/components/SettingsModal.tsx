import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { checkHealth } from '../services/api';
import { X, CheckCircle, AlertCircle, Save, Sliders, RefreshCw } from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const {
    apiConfig,
    updateConfig,
    autoRefresh,
    setAutoRefresh,
    refreshInterval,
    setRefreshInterval,
    refresh,
  } = useApp();

  const [baseUrl, setBaseUrl] = useState(apiConfig.baseUrl);
  const [dashboardKey, setDashboardKey] = useState(apiConfig.dashboardKey || '');
  const [ingestKey, setIngestKey] = useState(apiConfig.ingestKey || '');
  const [pollInterval, setPollInterval] = useState(refreshInterval);
  const [isPollingEnabled, setIsPollingEnabled] = useState(autoRefresh);
  const [testResult, setTestResult] = useState<{ ok: boolean; msg: string } | null>(null);
  const [isTesting, setIsTesting] = useState(false);

  if (!isOpen) return null;

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      const res = await checkHealth({ baseUrl, dashboardKey, ingestKey });
      setTestResult({
        ok: true,
        msg: `Connection successful! Backend status: ${res.status} at ${res.time}`,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Connection failed';
      setTestResult({ ok: false, msg });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSave = () => {
    updateConfig({
      baseUrl,
      dashboardKey,
      ingestKey,
    });
    setAutoRefresh(isPollingEnabled);
    setRefreshInterval(pollInterval);
    refresh();
    onClose();
  };

  return (
    <div className="modal-overlay">
      <div className="modal-dialog">
        <div className="modal-header">
          <div className="modal-title-group">
            <Sliders size={20} className="text-accent" />
            <h2>System & API Settings</h2>
          </div>
          <button type="button" className="modal-close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          <div className="form-group">
            <label htmlFor="baseUrl" className="form-label">
              Backend API Base URL
            </label>
            <input
              id="baseUrl"
              type="text"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="http://localhost:8000"
              className="form-input"
            />
            <span className="form-hint">
              Target Starlette / Uvicorn server address (default: http://localhost:8000).
            </span>
          </div>

          <div className="form-group">
            <label htmlFor="dashboardKey" className="form-label">
              Dashboard API Key (X-API-Key)
            </label>
            <input
              id="dashboardKey"
              type="password"
              value={dashboardKey}
              onChange={(e) => setDashboardKey(e.target.value)}
              placeholder="Leave blank for local dev mode"
              className="form-input"
            />
            <span className="form-hint">
              Matches DASHBOARD_API_KEY in backend .env. Protects /state and ticket resolution.
            </span>
          </div>

          <div className="form-group">
            <label htmlFor="ingestKey" className="form-label">
              Ingest API Key (Optional)
            </label>
            <input
              id="ingestKey"
              type="password"
              value={ingestKey}
              onChange={(e) => setIngestKey(e.target.value)}
              placeholder="Matches INGEST_API_KEY"
              className="form-input"
            />
            <span className="form-hint">
              Used when injecting faults or sending event batches from the browser.
            </span>
          </div>

          <div className="form-row">
            <div className="form-group flex-1">
              <label htmlFor="refreshRate" className="form-label">
                Polling Interval
              </label>
              <select
                id="refreshRate"
                value={pollInterval}
                onChange={(e) => setPollInterval(Number(e.target.value))}
                className="form-select"
              >
                <option value={1000}>1 Second (Fast Demo)</option>
                <option value={2000}>2 Seconds (Recommended)</option>
                <option value={5000}>5 Seconds</option>
                <option value={10000}>10 Seconds</option>
              </select>
            </div>

            <div className="form-group flex-1 flex-center-vertical">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={isPollingEnabled}
                  onChange={(e) => setIsPollingEnabled(e.target.checked)}
                />
                <span>Auto-refresh enabled</span>
              </label>
            </div>
          </div>

          {/* Test connection output */}
          {testResult && (
            <div className={`test-result-box ${testResult.ok ? 'test-success' : 'test-fail'}`}>
              {testResult.ok ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
              <span>{testResult.msg}</span>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button
            type="button"
            className="btn-secondary"
            onClick={handleTestConnection}
            disabled={isTesting}
          >
            <RefreshCw size={16} className={isTesting ? 'btn-spinning' : ''} />
            <span>{isTesting ? 'Testing...' : 'Test Connection'}</span>
          </button>

          <div className="footer-actions-right">
            <button type="button" className="btn-cancel" onClick={onClose}>
              Cancel
            </button>
            <button type="button" className="btn-save" onClick={handleSave}>
              <Save size={16} />
              <span>Save & Apply</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
