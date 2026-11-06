import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import type { BackendState } from '../types';
import {
  fetchState,
  checkHealth,
  resolveTicket as apiResolveTicket,
  resetCampus as apiResetCampus,
  simulateKillAp,
  simulateCongestion,
  simulateLabDown,
  simulateUplinkOutage,
  simulateIotFault,
  simulateHealthyCampus,
  type ApiConfig,
  DEFAULT_CONFIG,
} from '../services/api';

export type ViewMode = 'student' | 'staff';
export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected';

interface AppContextType {
  state: BackendState | null;
  isLoading: boolean;
  error: string | null;
  connectionStatus: ConnectionStatus;
  lastUpdated: Date | null;
  autoRefresh: boolean;
  refreshInterval: number;
  currentView: ViewMode;
  apiConfig: ApiConfig;
  activeFaultDescription: string | null;
  // Actions
  refresh: () => Promise<void>;
  resolveTicket: (ticketId: string) => Promise<void>;
  resetDemo: () => Promise<void>;
  triggerFault: (type: 'kill-ap' | 'congestion' | 'lab-down' | 'uplink' | 'iot-fault') => Promise<void>;
  recoverAll: () => Promise<void>;
  setView: (view: ViewMode) => void;
  updateConfig: (newConfig: Partial<ApiConfig>) => void;
  setAutoRefresh: (enabled: boolean) => void;
  setRefreshInterval: (intervalMs: number) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<BackendState | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('connecting');
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);
  const [refreshInterval, setRefreshInterval] = useState<number>(2000);
  const [currentView, setCurrentView] = useState<ViewMode>('student');
  const [activeFaultDescription, setActiveFaultDescription] = useState<string | null>(null);

  const [apiConfig, setApiConfig] = useState<ApiConfig>(() => {
    const saved = localStorage.getItem('smart_lab_config');
    if (saved) {
      try {
        return { ...DEFAULT_CONFIG, ...JSON.parse(saved) };
      } catch {
        // fallback
      }
    }
    return DEFAULT_CONFIG;
  });

  const timerRef = useRef<number | null>(null);

  const updateConfig = (newConfig: Partial<ApiConfig>) => {
    setApiConfig((prev) => {
      const merged = { ...prev, ...newConfig };
      localStorage.setItem('smart_lab_config', JSON.stringify(merged));
      return merged;
    });
  };

  const refresh = useCallback(async () => {
    try {
      const data = await fetchState(apiConfig);
      setState(data);
      setConnectionStatus('connected');
      setLastUpdated(new Date());
      setError(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      setError(msg);
      // Double check if health responds
      try {
        await checkHealth(apiConfig);
        setConnectionStatus('connected');
      } catch {
        setConnectionStatus('disconnected');
      }
    } finally {
      setIsLoading(false);
    }
  }, [apiConfig]);

  // Initial load
  useEffect(() => {
    refresh();
  }, [refresh]);

  // Auto polling
  useEffect(() => {
    if (!autoRefresh) {
      if (timerRef.current) clearInterval(timerRef.current);
      return;
    }

    timerRef.current = window.setInterval(() => {
      refresh();
    }, refreshInterval);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [autoRefresh, refreshInterval, refresh]);

  const resolveTicket = async (ticketId: string) => {
    try {
      await apiResolveTicket(ticketId, apiConfig);
      // Optimistic update
      if (state) {
        setState({
          ...state,
          open_tickets: state.open_tickets.filter((t) => t.ticket_id !== ticketId),
        });
      }
      await refresh();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to resolve ticket';
      alert(`Error resolving ticket: ${msg}`);
      throw err;
    }
  };

  const resetDemo = async () => {
    try {
      await apiResetCampus(apiConfig);
      setActiveFaultDescription(null);
      await refresh();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to reset demo';
      alert(`Error resetting demo: ${msg}`);
      throw err;
    }
  };

  const triggerFault = async (type: 'kill-ap' | 'congestion' | 'lab-down' | 'uplink' | 'iot-fault') => {
    try {
      setIsLoading(true);
      if (type === 'kill-ap') {
        setActiveFaultDescription('Hardware failure on ap-b-02 (Block B)');
        await simulateKillAp('ap-b-02', 'block-b', apiConfig);
      } else if (type === 'congestion') {
        setActiveFaultDescription('Severe network congestion in Block A');
        await simulateCongestion('block-a', 'ap-a-01', apiConfig);
      } else if (type === 'lab-down') {
        setActiveFaultDescription('Networking Lab APs dropped (lab-network)');
        await simulateLabDown('lab-network', apiConfig);
      } else if (type === 'uplink') {
        setActiveFaultDescription('ISP Uplink failure (Campus-wide Outage)');
        await simulateUplinkOutage(apiConfig);
      } else if (type === 'iot-fault') {
        setActiveFaultDescription('IoT Card Reader fault (reader-net-01)');
        await simulateIotFault('reader-net-01', 'lab-network', apiConfig);
      }
      await refresh();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to trigger fault';
      alert(`Simulation error: ${msg}`);
    } finally {
      setIsLoading(false);
    }
  };

  const recoverAll = async () => {
    try {
      setIsLoading(true);
      setActiveFaultDescription(null);
      await simulateHealthyCampus(apiConfig);
      await refresh();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to recover';
      alert(`Recovery error: ${msg}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AppContext.Provider
      value={{
        state,
        isLoading,
        error,
        connectionStatus,
        lastUpdated,
        autoRefresh,
        refreshInterval,
        currentView,
        apiConfig,
        activeFaultDescription,
        refresh,
        resolveTicket,
        resetDemo,
        triggerFault,
        recoverAll,
        setView: setCurrentView,
        updateConfig,
        setAutoRefresh,
        setRefreshInterval,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = (): AppContextType => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
