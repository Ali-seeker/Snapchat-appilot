import React from 'react';
import { Layers, Sunrise, RefreshCw, Sparkles, ArrowRight } from 'lucide-react';

export default function ChainedWorkflowCard({ isRunning, onTriggerWorkflow }) {
  const handleLaunch = (routineType) => {
    onTriggerWorkflow('chain', {
      routine_type: routineType
    });
  };

  return (
    <div className="glass-panel action-card">
      <div className="panel-header">
        <div className="panel-title">
          <Layers size={20} color="#10b981" />
          <span>Chained &amp; Scheduled Daily Routines</span>
        </div>
        <span className="badge badge-emerald">Multi-Stage</span>
      </div>

      <div className="panel-body">
        <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '14px' }}>
          Execute combined automated routines with built-in human pauses between stages for 100% organic behavior.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '12px' }}>
          {/* Preset 1: Morning Growth */}
          <div style={{ background: 'rgba(15, 23, 42, 0.7)', border: '1px solid rgba(16, 185, 129, 0.2)', borderRadius: '10px', padding: '14px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <Sunrise size={18} color="#10b981" />
                <strong style={{ fontSize: '0.88rem', color: '#f8fafc' }}>Morning Growth Routine</strong>
              </div>
              <p style={{ fontSize: '0.76rem', color: '#94a3b8', lineHeight: '1.4', marginBottom: '12px' }}>
                1. Auto Snap with random filter to all friends.<br />
                2. Rest 5 seconds.<br />
                3. Quick Add 5 suggested friends.
              </p>
            </div>
            <button
              className="btn btn-secondary"
              style={{ width: '100%', fontSize: '0.82rem', padding: '8px 12px', borderColor: '#10b981', color: '#10b981' }}
              onClick={() => handleLaunch('morning')}
              disabled={isRunning}
            >
              <span>Run Morning Routine</span>
              <ArrowRight size={14} />
            </button>
          </div>

          {/* Preset 2: Score & Clean */}
          <div style={{ background: 'rgba(15, 23, 42, 0.7)', border: '1px solid rgba(168, 85, 247, 0.2)', borderRadius: '10px', padding: '14px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <RefreshCw size={18} color="#a855f7" />
                <strong style={{ fontSize: '0.88rem', color: '#f8fafc' }}>Score &amp; Clean Routine</strong>
              </div>
              <p style={{ fontSize: '0.76rem', color: '#94a3b8', lineHeight: '1.4', marginBottom: '12px' }}>
                1. Snapscore Booster (3 cycles = +45 pts).<br />
                2. Rest 8 seconds.<br />
                3. Unfollow 5 friends missing streak (🔥).
              </p>
            </div>
            <button
              className="btn btn-secondary"
              style={{ width: '100%', fontSize: '0.82rem', padding: '8px 12px', borderColor: '#a855f7', color: '#c084fc' }}
              onClick={() => handleLaunch('score_and_clean')}
              disabled={isRunning}
            >
              <span>Run Score &amp; Clean</span>
              <ArrowRight size={14} />
            </button>
          </div>

          {/* Preset 3: All-in-One Power Suite */}
          <div style={{ background: 'rgba(15, 23, 42, 0.7)', border: '1px solid rgba(56, 189, 248, 0.2)', borderRadius: '10px', padding: '14px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <Sparkles size={18} color="#38bdf8" />
                <strong style={{ fontSize: '0.88rem', color: '#f8fafc' }}>All-in-One Power Suite</strong>
              </div>
              <p style={{ fontSize: '0.76rem', color: '#94a3b8', lineHeight: '1.4', marginBottom: '12px' }}>
                1. Auto Snap dispatch.<br />
                2. Quick Add suggestions.<br />
                3. Accept incoming followers.<br />
                4. Unfollow dormant friends (&gt;17d).
              </p>
            </div>
            <button
              className="btn btn-secondary"
              style={{ width: '100%', fontSize: '0.82rem', padding: '8px 12px', borderColor: '#38bdf8', color: '#38bdf8' }}
              onClick={() => handleLaunch('all_in_one')}
              disabled={isRunning}
            >
              <span>Run Complete Suite</span>
              <ArrowRight size={14} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
