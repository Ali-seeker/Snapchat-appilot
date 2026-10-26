import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import { Play, Pause, Square, AlertOctagon, CheckSquare, Eye, X } from 'lucide-react';

export default function ControlPanel({
  appState,
  isPaused,
  selectedTargets,
  onStartWorkflow,
  onPauseWorkflow,
  onResumeWorkflow,
  onEmergencyStop,
  disclosureAcknowledged
}) {
  const [showReviewModal, setShowReviewModal] = useState(false);

  const handleStartClick = () => {
    if (!disclosureAcknowledged) {
      alert("Please acknowledge the Setup & Transparency Disclosure first (FR-01).");
      return;
    }
    if (selectedTargets.length === 0) {
      alert("Please select at least one contact target from the list below.");
      return;
    }
    // Show confirmation review modal (FR-05)
    setShowReviewModal(true);
  };

  const handleConfirmAction = () => {
    setShowReviewModal(false);
    onStartWorkflow();
  };

  const isRunning = appState === 'RUNNING';
  const isStopped = appState === 'STOPPED';

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
          {/* Start Button */}
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

          {/* Pause / Resume */}
          {isRunning && (
            <button className="btn btn-warning" onClick={onPauseWorkflow}>
              <Pause size={17} />
              <span>Pause</span>
            </button>
          )}

          {isPaused && (
            <button className="btn btn-primary" onClick={onResumeWorkflow}>
              <Play size={17} />
              <span>Resume</span>
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

      {/* FR-05: Review Before Consequential Action Modal (Portaled to document.body) */}
      {showReviewModal && typeof document !== 'undefined' && createPortal(
        <div className="modal-overlay" onClick={() => setShowReviewModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
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
