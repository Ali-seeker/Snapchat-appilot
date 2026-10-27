import React, { useState } from 'react';
import { UserPlus, Search, UserCheck, Sparkles, AlertCircle } from 'lucide-react';

export default function BulkFollowCard({ isRunning, onTriggerWorkflow, selectedCount }) {
  const [mode, setMode] = useState('quick_add'); // 'quick_add' | 'search' | 'accept'
  const [count, setCount] = useState(10);

  const handleLaunch = () => {
    onTriggerWorkflow('follow', {
      mode,
      max_count: count
    });
  };

  return (
    <div className="glass-panel action-card">
      <div className="panel-header">
        <div className="panel-title">
          <UserPlus size={20} color="#38bdf8" />
          <span>Bulk Follow &amp; Add Friends</span>
        </div>
        <span className="badge badge-blue">Multi-Modal</span>
      </div>

      <div className="panel-body">
        <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '14px' }}>
          Follow candidates via Quick Add suggestions, bulk username search, or accept pending incoming requests.
        </p>

        {/* Mode Selector Tabs */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', background: 'rgba(15, 23, 42, 0.7)', padding: '4px', borderRadius: '8px' }}>
          <button
            type="button"
            className={`tab-btn ${mode === 'quick_add' ? 'active' : ''}`}
            onClick={() => setMode('quick_add')}
            disabled={isRunning}
          >
            <Sparkles size={14} />
            <span>Quick Add Suggestions</span>
          </button>
          <button
            type="button"
            className={`tab-btn ${mode === 'search' ? 'active' : ''}`}
            onClick={() => setMode('search')}
            disabled={isRunning}
          >
            <Search size={14} />
            <span>Search Username</span>
          </button>
          <button
            type="button"
            className={`tab-btn ${mode === 'accept' ? 'active' : ''}`}
            onClick={() => setMode('accept')}
            disabled={isRunning}
          >
            <UserCheck size={14} />
            <span>Accept Incoming</span>
          </button>
        </div>

        {/* Dynamic Controls based on Mode */}
        {mode === 'quick_add' && (
          <div style={{ marginBottom: '16px', padding: '12px', background: 'rgba(56, 189, 248, 0.05)', borderRadius: '8px', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
              <span style={{ fontSize: '0.84rem', color: '#cbd5e1' }}>Target Suggestions to Add:</span>
              <strong style={{ color: '#38bdf8', fontSize: '0.9rem' }}>{count} friends</strong>
            </div>
            <input
              type="range"
              min="3"
              max="25"
              value={count}
              onChange={(e) => setCount(parseInt(e.target.value))}
              disabled={isRunning}
              style={{ width: '100%', accentColor: '#38bdf8' }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#64748b' }}>
              <span>3 (Safe minimum)</span>
              <span>10 (Standard)</span>
              <span>25 (Max batch)</span>
            </div>
          </div>
        )}

        {mode === 'search' && (
          <div style={{ marginBottom: '16px', padding: '12px', background: 'rgba(56, 189, 248, 0.05)', borderRadius: '8px', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
            <span style={{ fontSize: '0.84rem', color: '#cbd5e1' }}>
              Will search &amp; add confirmed targets selected from list below (<strong>{selectedCount}</strong> selected).
            </span>
          </div>
        )}

        {mode === 'accept' && (
          <div style={{ marginBottom: '16px', padding: '12px', background: 'rgba(56, 189, 248, 0.05)', borderRadius: '8px', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
            <span style={{ fontSize: '0.84rem', color: '#cbd5e1' }}>
              Will scan <strong>"Added Me"</strong> section and automatically accept all pending follower requests.
            </span>
          </div>
        )}

        {/* Action Button */}
        <button
          className="btn btn-primary"
          style={{ width: '100%', padding: '10px 16px', fontSize: '0.92rem', fontWeight: 600, display: 'flex', justifyContent: 'center', gap: '8px' }}
          onClick={handleLaunch}
          disabled={isRunning || (mode === 'search' && selectedCount === 0)}
        >
          <UserPlus size={18} />
          <span>
            {mode === 'quick_add' ? `Start Quick Add (${count} Suggestions)` :
             mode === 'accept' ? 'Accept All Incoming Requests' :
             `Search & Add (${selectedCount} Targets)`}
          </span>
        </button>
      </div>
    </div>
  );
}
