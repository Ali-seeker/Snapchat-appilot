import React, { useState } from 'react';
import { UserMinus, Flame, Clock, Users, ShieldAlert } from 'lucide-react';

export default function BulkUnfollowCard({ isRunning, onTriggerWorkflow, selectedTargets = [] }) {
  const [filterType, setFilterType] = useState('no_streak'); // 'no_streak' | 'inactive' | 'custom'
  const [daysThreshold, setDaysThreshold] = useState(17);
  const [maxUnfollow, setMaxUnfollow] = useState(10);

  const handleLaunch = () => {
    onTriggerWorkflow('unfollow', {
      filter_type: filterType,
      days_threshold: daysThreshold,
      max_unfollow: maxUnfollow,
      custom_targets: selectedTargets.map((t) => t.username)
    });
  };

  return (
    <div className="glass-panel action-card">
      <div className="panel-header">
        <div className="panel-title">
          <UserMinus size={20} color="#f43f5e" />
          <span>Smart Bulk Unfollow</span>
        </div>
        <span className="badge badge-rose">Engagement Clean</span>
      </div>

      <div className="panel-body">
        <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '14px' }}>
          Automatically unfollow friends without active streak, dormant accounts, or customized target lists.
        </p>

        {/* Filter Selection Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginBottom: '16px' }}>
          <button
            type="button"
            className={`filter-card-btn ${filterType === 'no_streak' ? 'active-rose' : ''}`}
            onClick={() => setFilterType('no_streak')}
            disabled={isRunning}
          >
            <Flame size={18} color={filterType === 'no_streak' ? '#f43f5e' : '#94a3b8'} />
            <div style={{ fontSize: '0.82rem', fontWeight: 600, marginTop: '4px' }}>No Streak</div>
            <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Missing 🔥 emoji</div>
          </button>

          <button
            type="button"
            className={`filter-card-btn ${filterType === 'inactive' ? 'active-rose' : ''}`}
            onClick={() => setFilterType('inactive')}
            disabled={isRunning}
          >
            <Clock size={18} color={filterType === 'inactive' ? '#f43f5e' : '#94a3b8'} />
            <div style={{ fontSize: '0.82rem', fontWeight: 600, marginTop: '4px' }}>Inactive</div>
            <div style={{ fontSize: '0.7rem', color: '#64748b' }}>&gt;{daysThreshold} days dormant</div>
          </button>

          <button
            type="button"
            className={`filter-card-btn ${filterType === 'custom' ? 'active-rose' : ''}`}
            onClick={() => setFilterType('custom')}
            disabled={isRunning}
          >
            <Users size={18} color={filterType === 'custom' ? '#f43f5e' : '#94a3b8'} />
            <div style={{ fontSize: '0.82rem', fontWeight: 600, marginTop: '4px' }}>Custom List</div>
            <div style={{ fontSize: '0.7rem', color: '#64748b' }}>{selectedTargets.length} selected</div>
          </button>
        </div>

        {/* Additional Config */}
        {filterType === 'inactive' && (
          <div style={{ marginBottom: '14px', padding: '10px 14px', background: 'rgba(244, 63, 94, 0.05)', borderRadius: '8px', border: '1px solid rgba(244, 63, 94, 0.2)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
              <span style={{ fontSize: '0.82rem', color: '#cbd5e1' }}>Inactivity Threshold:</span>
              <strong style={{ color: '#f43f5e', fontSize: '0.88rem' }}>{daysThreshold} Days</strong>
            </div>
            <input
              type="range"
              min="7"
              max="60"
              value={daysThreshold}
              onChange={(e) => setDaysThreshold(parseInt(e.target.value))}
              disabled={isRunning}
              style={{ width: '100%', accentColor: '#f43f5e' }}
            />
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', padding: '0 4px' }}>
          <span style={{ fontSize: '0.82rem', color: '#94a3b8' }}>Max Friends to Remove in Session:</span>
          <select
            value={maxUnfollow}
            onChange={(e) => setMaxUnfollow(parseInt(e.target.value))}
            disabled={isRunning}
            style={{ background: '#0f172a', border: '1px solid #334155', color: '#f8fafc', padding: '4px 8px', borderRadius: '6px', fontSize: '0.82rem' }}
          >
            <option value={3}>3 (Gentle)</option>
            <option value={5}>5 (Safe)</option>
            <option value={10}>10 (Standard)</option>
            <option value={20}>20 (Aggressive)</option>
          </select>
        </div>

        {/* Action Button */}
        <button
          className="btn"
          style={{ width: '100%', background: '#f43f5e', color: '#fff', padding: '10px 16px', fontSize: '0.92rem', fontWeight: 600, display: 'flex', justifyContent: 'center', gap: '8px', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
          onClick={handleLaunch}
          disabled={isRunning || (filterType === 'custom' && selectedTargets.length === 0)}
        >
          <UserMinus size={18} />
          <span>
            {filterType === 'no_streak' ? `Unfollow Non-Streak Friends (Up to ${maxUnfollow})` :
             filterType === 'inactive' ? `Unfollow Inactive >${daysThreshold}d (Up to ${maxUnfollow})` :
             `Unfollow ${selectedTargets.length} Selected Friends`}
          </span>
        </button>
      </div>
    </div>
  );
}
