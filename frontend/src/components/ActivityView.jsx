import React, { useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  Trash2,
  RefreshCw,
  UserPlus,
  Flame,
  Send
} from 'lucide-react';

export default function ActivityView({
  logs = [],
  onClearLogs
}) {
  const [filter, setFilter] = useState('all');

  const filteredLogs = logs.filter((l) => {
    if (filter === 'completed') return l.result === 'COMPLETED';
    if (filter === 'failed') return l.result === 'FAILED';
    if (filter === 'pending') return l.result === 'SKIPPED';
    return true;
  });

  return (
    <div className="page-container">
      <div className="white-panel">
        {/* Header */}
        <div className="panel-header-row">
          <div className="panel-header-title">
            <h3>Activity History</h3>
            <p>Track all your automation runs, friend changes, and system events.</p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              className="btn-danger"
              onClick={onClearLogs}
              title="Clear all recorded history logs"
            >
              <Trash2 size={16} />
              <span>Clear History</span>
            </button>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="filter-tabs-row">
          <button
            className={`filter-tab ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All ({logs.length})
          </button>
          <button
            className={`filter-tab ${filter === 'completed' ? 'active' : ''}`}
            onClick={() => setFilter('completed')}
          >
            Completed ({logs.filter(l => l.result === 'COMPLETED').length})
          </button>
          <button
            className={`filter-tab ${filter === 'failed' ? 'active' : ''}`}
            onClick={() => setFilter('failed')}
          >
            Failed ({logs.filter(l => l.result === 'FAILED').length})
          </button>
          <button
            className={`filter-tab ${filter === 'pending' ? 'active' : ''}`}
            onClick={() => setFilter('pending')}
          >
            Pending / Skipped ({logs.filter(l => l.result === 'SKIPPED').length})
          </button>
        </div>

        {/* Activity Stream */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {filteredLogs.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '48px', color: '#94a3b8' }}>
              No automation activity logs recorded yet. Run a workflow to view real-time history!
            </div>
          ) : (
            filteredLogs.map((log, idx) => {
              const isSuccess = log.result === 'COMPLETED';
              const isFailed = log.result === 'FAILED';
              const timeStr = log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : 'Just now';

              return (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '16px 20px',
                    borderRadius: '12px',
                    border: '1px solid #e2e8f0',
                    background: '#ffffff',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.03)'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <div
                      style={{
                        width: '36px',
                        height: '36px',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        background: isSuccess ? '#DCFCE7' : isFailed ? '#FEE2E2' : '#FEF3C7',
                        color: isSuccess ? '#16A34A' : isFailed ? '#DC2626' : '#D97706'
                      }}
                    >
                      {isSuccess ? <CheckCircle2 size={19} /> : isFailed ? <XCircle size={19} /> : <Clock size={19} />}
                    </div>

                    <div>
                      <div style={{ fontWeight: 600, color: '#0f172a', fontSize: '0.92rem' }}>
                        {log.message || log.workflow}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.78rem', color: '#64748b', marginTop: '2px' }}>
                        <span style={{ fontWeight: 600, color: isSuccess ? '#16a34a' : isFailed ? '#dc2626' : '#d97706' }}>
                          {log.result}
                        </span>
                        <span>•</span>
                        <span>{timeStr}</span>
                        <span>•</span>
                        <span style={{ fontFamily: 'monospace' }}>{log.reason || 'ACTION_LOGGED'}</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    {log.workflow?.includes('Follow') && (
                      <span style={{ fontWeight: 700, color: '#16a34a', fontSize: '1rem' }}>+1</span>
                    )}
                    {log.workflow?.includes('Unfollow') && (
                      <span style={{ fontWeight: 700, color: '#dc2626', fontSize: '1rem' }}>-1</span>
                    )}
                    {log.workflow?.includes('Snap') && (
                      <span style={{ fontWeight: 700, color: '#0284c7', fontSize: '1rem' }}>📸</span>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
