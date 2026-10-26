import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import {
  Play, Pause, AlertOctagon, CheckSquare, Eye, X,
  Terminal, CheckCircle2, Loader2, AlertTriangle
} from 'lucide-react';

export default function ControlPanel({
  appState,
  activeWorkflow,
  isPaused,
  selectedTargets,
  onStartWorkflow,
  onPauseWorkflow,
  onResumeWorkflow,
  onEmergencyStop,
  disclosureAcknowledged,
  logs = []
}) {
  const [modalOpen, setModalOpen] = useState(false);
  const [modalStage, setModalStage] = useState('review'); // 'review' | 'executing'

  const handleStartClick = () => {
    if (!disclosureAcknowledged) {
      alert("Please acknowledge the Setup & Transparency Disclosure first (FR-01).");
      return;
    }
    if (selectedTargets.length === 0) {
      alert("Please select at least one contact target from the list below.");
      return;
    }
    setModalStage('review');
    setModalOpen(true);
  };

  const handleConfirmAction = () => {
    setModalStage('executing');
    onStartWorkflow();
  };

  const isRunning = appState === 'RUNNING';
  const isStopped = appState === 'STOPPED';
  const isCompleted = appState === 'COMPLETED';

  // Filter logs for live execution view
  const executionLogs = logs.filter(
    (l) => l.workflow === 'Workflow Engine' || l.workflow.includes('Workflow')
  ).slice(0, 10);

  return (
    <div className="glass-panel" style={{ marginBottom: '24px' }}>
      <div className="panel-header">
        <div className="panel-title">
          <Play size={18} color="#10b981" />
          <span>FR-03 &amp; FR-05: Execution Controls &amp; Safety Review</span>
        </div>
        <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
          Selected: <strong style={{ color: '#38bdf8' }}>{selectedTargets.length}</strong> targets
        </span>
      </div>

      <div className="panel-body">
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
          {/* Start / Review Button */}
          {!isRunning && !isPaused && (
            <button
              className="btn btn-primary"
              onClick={handleStartClick}
              disabled={selectedTargets.length === 0}
            >
              <Eye size={17} />
              <span>Review &amp; Start ({selectedTargets.length})</span>
            </button>
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

          {/* Live Monitor Button if modal closed during run */}
          {(isRunning || isPaused) && !modalOpen && (
            <button
              className="btn btn-secondary"
              onClick={() => { setModalStage('executing'); setModalOpen(true); }}
            >
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

      {/* FR-05 & FR-09: Combined Confirmation & Live Execution Modal */}
      {modalOpen && typeof document !== 'undefined' && createPortal(
        <div className="modal-overlay" onClick={() => (isRunning ? null : setModalOpen(false))}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>

            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc' }}>
                  {modalStage === 'review' ? 'Confirm Consequential Action' : 'Live Workflow Execution'}
                </h3>
                {modalStage === 'executing' && (
                  <span className={`status-pill ${isRunning ? 'running' : isCompleted ? 'completed' : isPaused ? 'paused' : 'stopped'}`} style={{ fontSize: '0.75rem', padding: '3px 10px' }}>
                    {appState}
                  </span>
                )}
              </div>
              <button
                onClick={() => setModalOpen(false)}
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '4px', display: 'flex', alignItems: 'center' }}
                title="Close"
              >
                <X size={20} />
              </button>
            </div>

            {/* STAGE 1: REVIEW BEFORE ACTION */}
            {modalStage === 'review' && (
              <>
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

                <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '10px 12px', borderRadius: '8px', fontSize: '0.8rem', color: '#fca5a5', marginBottom: '20px' }}>
                  Note: In baseline mode, actual Snapchat friend changes are not autonomous. Assisted reminders/drafts will be staged safely.
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                  <button className="btn btn-secondary" onClick={() => setModalOpen(false)}>
                    Cancel
                  </button>
                  <button className="btn btn-primary" onClick={handleConfirmAction}>
                    <CheckSquare size={16} />
                    <span>Confirm &amp; Proceed</span>
                  </button>
                </div>
              </>
            )}

            {/* STAGE 2: LIVE EXECUTION PROGRESS */}
            {modalStage === 'executing' && (
              <>
                <div style={{ marginBottom: '14px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.84rem', color: '#cbd5e1', fontWeight: 500 }}>
                      {isRunning ? 'Processing targets in sequence...' : isCompleted ? 'All targets completed!' : isPaused ? 'Execution Paused' : 'Halted'}
                    </span>
                    <span style={{ fontSize: '0.78rem', color: '#38bdf8' }}>
                      {selectedTargets.length} target(s)
                    </span>
                  </div>

                  {/* Progress Bar Animation */}
                  <div style={{ width: '100%', height: '6px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '999px', overflow: 'hidden' }}>
                    <div
                      style={{
                        height: '100%',
                        width: isCompleted ? '100%' : isRunning ? '75%' : '40%',
                        background: isCompleted ? '#10b981' : isStopped ? '#ef4444' : '#38bdf8',
                        transition: 'width 0.4s ease, background 0.3s ease'
                      }}
                    />
                  </div>
                </div>

                {/* Real-time Terminal Log inside Modal */}
                <div style={{ background: 'rgba(10, 14, 23, 0.95)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '12px', maxHeight: '200px', overflowY: 'auto', marginBottom: '16px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {executionLogs.length === 0 ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#94a3b8', fontSize: '0.82rem', padding: '10px 0' }}>
                      <Loader2 size={16} className="pulse-dot" />
                      <span>Initiating workflow orchestrator...</span>
                    </div>
                  ) : (
                    executionLogs.map((log) => (
                      <div key={log.id} style={{ fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '8px', color: '#f8fafc' }}>
                        <span style={{ color: log.result === 'COMPLETED' ? '#10b981' : '#38bdf8', fontSize: '0.72rem', fontWeight: 600 }}>
                          [{log.result}]
                        </span>
                        <span>{log.message}</span>
                      </div>
                    ))
                  )}
                </div>

                {/* Modal Footer Controls */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)' }}>
                  {isRunning && (
                    <div style={{ display: 'flex', gap: '10px' }}>
                      <button className="btn btn-warning" onClick={onPauseWorkflow} style={{ padding: '8px 14px', fontSize: '0.85rem' }}>
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
                      <button className="btn btn-primary" onClick={onResumeWorkflow} style={{ padding: '8px 14px', fontSize: '0.85rem' }}>
                        <Play size={15} />
                        <span>Resume</span>
                      </button>
                      <button className="btn btn-danger" onClick={onEmergencyStop} style={{ padding: '8px 14px', fontSize: '0.85rem' }}>
                        <AlertOctagon size={15} />
                        <span>Emergency Stop</span>
                      </button>
                    </div>
                  )}

                  {(isCompleted || isStopped) && (
                    <button
                      className="btn btn-primary"
                      onClick={() => setModalOpen(false)}
                      style={{ marginLeft: 'auto', padding: '8px 20px' }}
                    >
                      <CheckCircle2 size={16} />
                      <span>Done / Close</span>
                    </button>
                  )}
                </div>
              </>
            )}

          </div>
        </div>,
        document.body
      )}
    </div>
  );
}
