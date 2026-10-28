import React from 'react';
import { ShieldCheck, Radio, RotateCcw, AlertTriangle } from 'lucide-react';

export default function Header({ appState, activeWorkflow, isConnected, latency, snapchatVersion, onReset }) {
  const getStateClass = (state) => {
    switch (state) {
      case 'IDLE': return 'idle';
      case 'READY': return 'ready';
      case 'REVIEWING': return 'reviewing';
      case 'RUNNING': return 'running';
      case 'PAUSED': return 'paused';
      case 'STOPPED': return 'stopped';
      case 'COMPLETED': return 'completed';
      case 'FAILED': return 'failed';
      default: return 'idle';
    }
  };

  return (
    <header className="app-header">
      <div className="header-brand">
        <div className="brand-icon">
          <ShieldCheck size={26} color="#ffffff" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 className="brand-title">Appilot Companion</h1>
            <span
              style={{
                fontSize: '0.72rem',
                fontWeight: 700,
                color: '#000000',
                backgroundColor: '#FFFC00',
                padding: '2px 8px',
                borderRadius: '12px',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                boxShadow: '0 0 10px rgba(255, 252, 0, 0.35)',
                letterSpacing: '0.02em'
              }}
              title="Snapchat Target App Version"
            >
              👻 Snapchat v{snapchatVersion || '14.29.0.50'}
            </span>
          </div>
          <div className="brand-subtitle">
            Snapchat Assisted Management • Day 1 Verified Baseline
          </div>
        </div>
      </div>

      <div className="header-actions">
        {/* State Badge */}
        <div className={`status-pill ${getStateClass(appState)}`}>
          <span className="pulse-dot"></span>
          <span>{appState} {activeWorkflow ? `• ${activeWorkflow}` : ''}</span>
        </div>

        {/* WebSocket Health */}
        <div className="status-pill idle" style={{ fontSize: '0.78rem' }}>
          <Radio size={14} color={isConnected ? '#10b981' : '#ef4444'} />
          <span>{isConnected ? `WS Active (${latency}ms)` : 'WS Reconnecting...'}</span>
        </div>

        {/* Reset Button */}
        <button
          className="btn btn-secondary"
          onClick={onReset}
          title="Reset State Machine to IDLE"
          style={{ padding: '8px 14px' }}
        >
          <RotateCcw size={15} />
          <span>Reset</span>
        </button>
      </div>
    </header>
  );
}
