import React from 'react';
import { createPortal } from 'react-dom';
import {
  Terminal, CheckCircle2, AlertOctagon, Pause, Play, X, Loader2
} from 'lucide-react';

export default function LiveExecutionModal({
  isOpen,
  onClose,
  title,
  appState,
  isPaused,
  onPause,
  onResume,
  onEmergencyStop,
  logs = [],
  startTime = null
}) {
  if (!isOpen || typeof document === 'undefined') return null;

  const isRunning = appState === 'RUNNING';
  const isCompleted = appState === 'COMPLETED';
  const isStopped = appState === 'STOPPED';
  const isFailed = appState === 'FAILED';

  // Filter logs specifically for this execution session
  const executionLogs = logs.filter((l) => {
    const isEngine = l.workflow === 'Workflow Engine' || l.workflow.includes('Workflow') || l.workflow === 'Demo Engine';
    if (!isEngine) return false;
    if (startTime && l.timestamp) {
      return new Date(l.timestamp).getTime() >= (startTime - 2000);
    }
    return true;
  }).slice(0, 25);

  return createPortal(
    <div className="modal-overlay" onClick={() => (isRunning ? null : onClose())}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc' }}>
              {title || 'Live Workflow Execution'}
            </h3>
            <span
              className={`status-pill ${isRunning ? 'running' : isCompleted ? 'completed' : isPaused ? 'paused' : 'stopped'}`}
              style={{ fontSize: '0.75rem', padding: '3px 10px' }}
            >
              {appState}
            </span>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '4px', display: 'flex', alignItems: 'center' }}
            title="Close"
          >
            <X size={20} />
          </button>
        </div>

        {/* Progress Bar Animation */}
        <div style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
            <span style={{ fontSize: '0.84rem', color: '#cbd5e1', fontWeight: 500 }}>
              {isRunning ? 'Executing test steps...' : isCompleted ? 'Scenario Completed Successfully' : isPaused ? 'Execution Paused' : 'Stopped / Halted'}
            </span>
            <span style={{ fontSize: '0.78rem', color: '#38bdf8' }}>
              {executionLogs.length} step(s) logged
            </span>
          </div>
          <div style={{ width: '100%', height: '6px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '999px', overflow: 'hidden' }}>
            <div
              style={{
                height: '100%',
                width: isCompleted ? '100%' : isRunning ? '75%' : isPaused ? '50%' : '30%',
                background: isCompleted ? '#10b981' : isStopped ? '#ef4444' : isPaused ? '#f59e0b' : '#38bdf8',
                transition: 'width 0.4s ease, background 0.3s ease'
              }}
            />
          </div>
        </div>

        {/* Live Terminal Streaming Log */}
        <div
          style={{
            background: 'rgba(10, 14, 23, 0.95)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '8px',
            padding: '14px',
            minHeight: '140px',
            maxHeight: '220px',
            overflowY: 'auto',
            marginBottom: '18px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px'
          }}
        >
          {executionLogs.length === 0 ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#94a3b8', fontSize: '0.82rem', padding: '15px 0' }}>
              <Loader2 size={16} className="pulse-dot" />
              <span>Initializing test bench...</span>
            </div>
          ) : (
            executionLogs.map((log) => (
              <div key={log.id} style={{ fontSize: '0.82rem', display: 'flex', alignItems: 'flex-start', gap: '8px', color: '#f8fafc', lineHeight: '1.4' }}>
                <span
                  style={{
                    color:
                      log.result === 'COMPLETED' ? '#10b981' :
                      log.result === 'SKIPPED' ? '#fbbf24' :
                      log.result === 'UNKNOWN' ? '#94a3b8' :
                      log.result === 'FAILED' ? '#f87171' : '#38bdf8',
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    whiteSpace: 'nowrap',
                    marginTop: '2px'
                  }}
                >
                  [{log.result}]
                </span>
                <span style={{ flex: 1 }}>{log.message}</span>
              </div>
            ))
          )}
        </div>

        {/* Footer Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)' }}>
          {isRunning && (
            <div style={{ display: 'flex', gap: '10px' }}>
              <button className="btn btn-warning" onClick={onPause} style={{ padding: '8px 14px', fontSize: '0.85rem' }}>
                <Pause size={15} />
                <span>Pause</span>
              </button>
              <button className="btn btn-danger" onClick={onEmergencyStop} style={{ padding: '8px 14px', fontSize: '0.85rem' }}>
                <AlertOctagon size={15} />
                <span>Emergency Stop</span>
              </button>
            </div>
          )}

          {isPaused && (
            <div style={{ display: 'flex', gap: '10px' }}>
              <button className="btn btn-primary" onClick={onResume} style={{ padding: '8px 14px', fontSize: '0.85rem' }}>
                <Play size={15} />
                <span>Resume</span>
              </button>
              <button className="btn btn-danger" onClick={onEmergencyStop} style={{ padding: '8px 14px', fontSize: '0.85rem' }}>
                <AlertOctagon size={15} />
                <span>Emergency Stop</span>
              </button>
            </div>
          )}

          {(isCompleted || isStopped || isFailed) && (
            <button
              className="btn btn-primary"
              onClick={onClose}
              style={{ marginLeft: 'auto', padding: '9px 22px' }}
            >
              <CheckCircle2 size={16} />
              <span>Done / Close</span>
            </button>
          )}
        </div>
      </div>
    </div>,
    document.body
  );
}
