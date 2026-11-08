import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import {
  Flame,
  Radio,
  Users,
  Cpu,
  Globe,
  RotateCcw,
  CheckCircle2,
  Trash2,
  X,
  AlertTriangle,
  PlayCircle,
} from 'lucide-react';

interface DemoControllerProps {
  isOpen: boolean;
  onToggle: () => void;
}

export const DemoController: React.FC<DemoControllerProps> = ({ isOpen, onToggle }) => {
  const {
    triggerFault,
    recoverAll,
    resetDemo,
    activeFaultDescription,
    isLoading,
    state,
  } = useApp();

  const [activeStep, setActiveStep] = useState<number | null>(null);

  const openTicketsCount = state?.open_tickets.length ?? 0;
  const activeAdvisoriesCount = state?.active_advisories.length ?? 0;

  const handleStep = async (
    stepNum: number,
    action: () => Promise<void>
  ) => {
    setActiveStep(stepNum);
    await action();
  };

  return (
    <div className={`demo-controller ${isOpen ? 'expanded' : 'collapsed'}`}>
      <div className="demo-header" onClick={onToggle}>
        <div className="demo-header-title">
          <PlayCircle className="demo-icon" size={19} />
          <span className="demo-title-text">
            Hackathon Live Demo Story Controller
          </span>
          {activeFaultDescription ? (
            <span className="demo-active-fault-badge">
              <AlertTriangle size={13} /> {activeFaultDescription}
            </span>
          ) : (
            <span className="demo-healthy-badge">
              <CheckCircle2 size={13} /> Campus Operating Normally
            </span>
          )}
        </div>

        <div className="demo-header-meta">
          <span className="demo-stat">
            Tickets: <strong>{openTicketsCount}</strong>
          </span>
          <span className="demo-stat">
            Advisories: <strong>{activeAdvisoriesCount}</strong>
          </span>
          <button
            type="button"
            className="demo-close-btn"
            onClick={(e) => {
              e.stopPropagation();
              onToggle();
            }}
            title="Turn Demo Mode OFF"
          >
            <X size={15} />
            <span>Hide Demo Bar</span>
          </button>
        </div>
      </div>

      {isOpen && (
        <div className="demo-body">
          <p className="demo-desc">
            Trigger real-time fault scenarios to test detection rules, Gemini root-cause analysis,
            student rerouting advisories, and Telegram alerts:
          </p>

          <div className="demo-buttons-grid">
            {/* Step 1: Kill AP */}
            <button
              type="button"
              className={`demo-btn-item danger ${activeStep === 1 ? 'selected' : ''}`}
              disabled={isLoading}
              onClick={() => handleStep(1, () => triggerFault('kill-ap'))}
            >
              <Radio size={16} />
              <div className="demo-btn-content">
                <strong>1. Kill AP (ap-b-02)</strong>
                <span>Hardware failure in Block B</span>
              </div>
            </button>

            {/* Step 2: Congestion */}
            <button
              type="button"
              className={`demo-btn-item warning ${activeStep === 2 ? 'selected' : ''}`}
              disabled={isLoading}
              onClick={() => handleStep(2, () => triggerFault('congestion'))}
            >
              <Users size={16} />
              <div className="demo-btn-content">
                <strong>2. Congest Block A</strong>
                <span>180+ clients, high latency</span>
              </div>
            </button>

            {/* Step 3: Lab Down */}
            <button
              type="button"
              className={`demo-btn-item danger ${activeStep === 3 ? 'selected' : ''}`}
              disabled={isLoading}
              onClick={() => handleStep(3, () => triggerFault('lab-down'))}
            >
              <Flame size={16} />
              <div className="demo-btn-content">
                <strong>3. Networking Lab Down</strong>
                <span>Fails all APs in lab-network</span>
              </div>
            </button>

            {/* Step 4: IoT Fault */}
            <button
              type="button"
              className={`demo-btn-item warning ${activeStep === 4 ? 'selected' : ''}`}
              disabled={isLoading}
              onClick={() => handleStep(4, () => triggerFault('iot-fault'))}
            >
              <Cpu size={16} />
              <div className="demo-btn-content">
                <strong>4. IoT Reader Fault</strong>
                <span>Card reader hardware down</span>
              </div>
            </button>

            {/* Step 5: Uplink Outage */}
            <button
              type="button"
              className={`demo-btn-item critical ${activeStep === 5 ? 'selected' : ''}`}
              disabled={isLoading}
              onClick={() => handleStep(5, () => triggerFault('uplink'))}
            >
              <Globe size={16} />
              <div className="demo-btn-content">
                <strong>5. Campus Uplink Outage</strong>
                <span>Multiple blocks & labs offline</span>
              </div>
            </button>

            {/* Step 6: Recover All */}
            <button
              type="button"
              className={`demo-btn-item success ${activeStep === 6 ? 'selected' : ''}`}
              disabled={isLoading}
              onClick={() => handleStep(6, () => recoverAll())}
            >
              <RotateCcw size={16} />
              <div className="demo-btn-content">
                <strong>6. Recover Health</strong>
                <span>3 good readings auto-resolve</span>
              </div>
            </button>

            {/* Step 7: Reset All */}
            <button
              type="button"
              className="demo-btn-item reset"
              disabled={isLoading}
              onClick={() => handleStep(7, () => resetDemo())}
            >
              <Trash2 size={16} />
              <div className="demo-btn-content">
                <strong>Reset State</strong>
                <span>POST /admin/reset</span>
              </div>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
