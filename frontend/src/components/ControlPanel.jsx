import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import {
  Play, Pause, AlertOctagon, CheckSquare, Eye, X, Terminal, Smartphone, Sparkles
} from 'lucide-react';

export default function ControlPanel({
  appState,
  isPaused,
  selectedTargets,
  onStartWorkflow,
  onPauseWorkflow,
  onResumeWorkflow,
  onEmergencyStop,
  disclosureAcknowledged,
  onViewLiveProgress,
  devices = []
}) {
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [executionMode, setExecutionMode] = useState('live'); // 'live' or 'demo'

  const handleStartClick = () => {
    if (!disclosureAcknowledged) {
      alert("Please acknowledge the Setup & Transparency Disclosure first (FR-01).");
      return;
    }
    if (selectedTargets.length === 0) {
      alert("Please select at least one contact target from the list below.");
      return;
    }
    setShowReviewModal(true);
  };

  const handleConfirmAction = () => {
    setShowReviewModal(false);
    onStartWorkflow(executionMode);
  };

  const isRunning = appState === 'RUNNING';
  const isStopped = appState === 'STOPPED';
  const connectedDevice = devices.find((d) => d.is_connected) || devices[0];

  return (
    <div className="glass-panel" style={{ marginBottom: '24px' }}>
      <div className="panel-header">
        <div className="panel-title">
          <Play size={18} color="#10b981" />
          <span>FR-03 &amp; FR-05: Execution Controls &amp; Safety Review</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {connectedDevice && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', color: '#10b981', background: 'rgba(16, 185, 129, 0.1)', padding: '3px 8px', borderRadius: '4px' }}>
              <Smartphone size={13} />
              <span>Connected: {connectedDevice.model || connectedDevice.device_id}</span>
            </div>
          )}
          <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            Selected: <strong style={{ color: '#38bdf8' }}>{selectedTargets.length}</strong> targets
          </span>
        </div>
      </div>

      <div className="panel-body">
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
          {/* Mode Switcher Pill */}
          {!isRunning && !isPaused && (
            <div style={{ display: 'flex', background: 'rgba(15, 23, 42, 0.8)', padding: '3px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <button
                type="button"
                onClick={() => setExecutionMode('live')}
                style={{
                  padding: '6px 14px',
                  fontSize: '0.82rem',
                  fontWeight: 600,
                  borderRadius: '6px',
                  border: 'none',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: executionMode === 'live' ? '#38bdf8' : 'transparent',
                  color: executionMode === 'live' ? '#0a0e17' : '#94a3b8',
                  transition: 'all 0.2s ease'
                }}
              >
                <Smartphone size={14} />
                <span>Live Device Mode</span>
              </button>
              <button
                type="button"
                onClick={() => setExecutionMode('demo')}
                style={{
                  padding: '6px 14px',
                  fontSize: '0.82rem',
                  fontWeight: 600,
                  borderRadius: '6px',
                  border: 'none',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: executionMode === 'demo' ? '#a855f7' : 'transparent',
                  color: executionMode === 'demo' ? '#0a0e17' : '#94a3b8',
                  transition: 'all 0.2s ease'
                }}
              >
                <Sparkles size={14} />
                <span>Simulation Mode</span>
              </button>
            </div>
          )}

          {/* Start / Review Button */}
          {!isRunning && !isPaused && (
            <>
              <button
                className="btn btn-primary"
                onClick={handleStartClick}
                disabled={selectedTargets.length === 0}
                style={{
                  background: executionMode === 'live'
                    ? 'linear-gradient(135deg, #0284c7, #0ea5e9)'
                    : 'linear-gradient(135deg, #7e22ce, #a855f7)',
                  borderColor: executionMode === 'live' ? '#38bdf8' : '#c084fc',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  transition: 'all 0.25s ease'
                }}
              >
                <Eye size={17} />
                <span>
                  Review &amp; Start ({selectedTargets.length}) • {executionMode === 'live' ? 'Live Phone' : 'Simulation'}
                </span>
              </button>
              <span style={{ fontSize: '0.78rem', color: executionMode === 'live' ? '#38bdf8' : '#c084fc', display: 'flex', alignItems: 'center', gap: '4px' }}>
                Mode: <strong>{executionMode === 'live' ? '⚡ Real Android Device' : '🧪 In-Browser Simulation'}</strong>
              </span>
            </>
          )}

          {/* Pause / Resume Controls */}
          {isRunning && (
            <button className="btn btn-warning" onClick={onPauseWorkflow}>
              <Pause size={17} />
              <span>Pause Execution</span>
            </button>
          )}

          {isPaused && (
            <button className="btn btn-primary" onClick={onResumeWorkflow}>
              <Play size={17} />
              <span>Resume Execution</span>
            </button>
          )}

          {/* View Live Progress Button */}
          {(isRunning || isPaused) && onViewLiveProgress && (
            <button className="btn btn-secondary" onClick={onViewLiveProgress}>
              <Terminal size={16} color="#38bdf8" />
              <span>View Live Progress</span>
            </button>
          )}

          {/* Prominent Emergency STOP Button (FR-03) */}
          <button
            className="btn btn-danger"
            onClick={onEmergencyStop}
            style={{ marginLeft: 'auto', padding: '12px 24px', fontSize: '1rem' }}
          >
            <AlertOctagon size={20} />
            <span>EMERGENCY STOP</span>
          </button>
        </div>
      </div>

      {/* FR-05: Review Before Consequential Action Modal */}
      {showReviewModal && typeof document !== 'undefined' && createPortal(
        <div className="modal-overlay" onClick={() => setShowReviewModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc' }}>
                Confirm Consequential Action
              </h3>
              <button
                onClick={() => setShowReviewModal(false)}
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '4px', display: 'flex', alignItems: 'center' }}
                title="Close"
              >
                <X size={20} />
              </button>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
              <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Target Device:</span>
              <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#38bdf8', background: 'rgba(56, 189, 248, 0.1)', padding: '2px 8px', borderRadius: '4px' }}>
                {connectedDevice ? (connectedDevice.model || connectedDevice.device_id) : '08265372BO000706'}
              </span>
              <span style={{ fontSize: '0.78rem', color: executionMode === 'live' ? '#10b981' : '#a855f7', fontWeight: 600, marginLeft: 'auto' }}>
                {executionMode === 'live' ? 'LIVE SNAPCHAT AUTOMATION' : 'SIMULATION BENCH'}
              </span>
            </div>

            <p style={{ fontSize: '0.86rem', color: '#94a3b8', marginBottom: '16px', lineHeight: '1.4' }}>
              In accordance with <strong>FR-05 (Review before consequential action)</strong>, you must explicitly confirm targets before initiating assistance.
            </p>

            <div style={{ background: 'rgba(15, 23, 42, 0.7)', padding: '12px', borderRadius: '8px', marginBottom: '16px', maxHeight: '140px', overflowY: 'auto' }}>
              <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#64748b', marginBottom: '6px' }}>
                Target Recipients ({selectedTargets.length}):
              </div>
              <ul style={{ listStyle: 'none', padding: 0 }}>
                {selectedTargets.map((t) => (
                  <li key={t.id} style={{ fontSize: '0.85rem', color: '#38bdf8', marginBottom: '4px' }}>
                    • @{t.username} {t.display_name ? `(${t.display_name})` : ''}
                  </li>
                ))}
              </ul>
            </div>

            <div style={{ background: executionMode === 'live' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', border: `1px solid ${executionMode === 'live' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`, padding: '10px 12px', borderRadius: '8px', fontSize: '0.8rem', color: executionMode === 'live' ? '#6ee7b7' : '#fca5a5', marginBottom: '20px' }}>
              {executionMode === 'live'
                ? "Live Mode: Will launch Snapchat on your device, search each confirmed username, tap Add, and enforce anti-ban human pacing between requests."
                : "Simulation Mode: Staged in local database and verified against synthetic telemetry without modifying your Snapchat account."}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button className="btn btn-secondary" onClick={() => setShowReviewModal(false)}>
                Cancel
              </button>
              <button className="btn btn-primary" onClick={handleConfirmAction}>
                <CheckSquare size={16} />
                <span>Confirm &amp; Proceed</span>
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}
