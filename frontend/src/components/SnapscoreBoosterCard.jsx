import React, { useState } from 'react';
import { Rocket, Zap, Info, ShieldCheck, Flame } from 'lucide-react';

export default function SnapscoreBoosterCard({ isRunning, onTriggerWorkflow }) {
  const [cycles, setCycles] = useState(3);
  const [selectAll, setSelectAll] = useState(true);

  const estimatedPointsPerCycle = 15;
  const totalEstimatedPoints = cycles * estimatedPointsPerCycle;

  const handleLaunch = () => {
    onTriggerWorkflow('snapscore', {
      cycles,
      select_all: selectAll,
      cooldown_seconds: 15
    });
  };

  return (
    <div className="glass-panel action-card">
      <div className="panel-header">
        <div className="panel-title">
          <Rocket size={20} color="#a855f7" />
          <span>Snapscore Algorithmic Booster</span>
        </div>
        <span className="badge badge-purple">Legitimate Growth</span>
      </div>

      <div className="panel-body">
        {/* Research Explainer Banner */}
        <div style={{ background: 'rgba(168, 85, 247, 0.08)', border: '1px solid rgba(168, 85, 247, 0.25)', borderRadius: '8px', padding: '12px 14px', marginBottom: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <Info size={16} color="#a855f7" />
            <strong style={{ fontSize: '0.82rem', color: '#f8fafc' }}>Research &amp; Mechanics: How Snapscore Works</strong>
          </div>
          <p style={{ fontSize: '0.76rem', color: '#cbd5e1', lineHeight: '1.4', margin: 0 }}>
            Text chats do <strong>not</strong> increase score (0 pts). Snapscore only grows from sending and opening photo Snaps (+1 pt per recipient). Multi-recipient dispatch with organic filters is the safe, legitimate accelerator.
          </p>
        </div>

        {/* Cycles Selector */}
        <div style={{ marginBottom: '14px', padding: '10px 14px', background: 'rgba(15, 23, 42, 0.7)', borderRadius: '8px', border: '1px solid rgba(168, 85, 247, 0.2)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
            <span style={{ fontSize: '0.84rem', color: '#cbd5e1' }}>Automated Dispatch Cycles:</span>
            <strong style={{ color: '#c084fc', fontSize: '0.92rem' }}>{cycles} Cycles</strong>
          </div>
          <input
            type="range"
            min="1"
            max="10"
            value={cycles}
            onChange={(e) => setCycles(parseInt(e.target.value))}
            disabled={isRunning}
            style={{ width: '100%', accentColor: '#a855f7' }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#64748b', marginTop: '4px' }}>
            <span>1 Cycle (~15 pts)</span>
            <span>3 Cycles (~45 pts)</span>
            <span>10 Cycles (~150 pts)</span>
          </div>
        </div>

        {/* Estimation & Safety Badge */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', padding: '0 4px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', color: '#10b981' }}>
            <ShieldCheck size={15} />
            <span>Anti-ban 15s cooldown pacing active</span>
          </div>
          <div style={{ fontSize: '0.82rem', color: '#f8fafc' }}>
            Estimated Gain: <strong style={{ color: '#c084fc' }}>+{totalEstimatedPoints} pts</strong>
          </div>
        </div>

        {/* Action Button */}
        <button
          className="btn"
          style={{ width: '100%', background: '#a855f7', color: '#fff', padding: '10px 16px', fontSize: '0.92rem', fontWeight: 700, display: 'flex', justifyContent: 'center', gap: '8px', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
          onClick={handleLaunch}
          disabled={isRunning}
        >
          <Zap size={18} />
          <span>Launch Snapscore Booster (+{totalEstimatedPoints} pts)</span>
        </button>
      </div>
    </div>
  );
}
