import React from 'react';
import { Terminal, Trash2, Filter } from 'lucide-react';

export default function AuditLogView({ logs, onClearLogs }) {
  const getTagClass = (status) => {
    switch (status) {
      case 'COMPLETED': return 'completed';
      case 'CANCELLED': return 'cancelled';
      case 'FAILED': return 'failed';
      case 'SKIPPED': return 'skipped';
      case 'UNKNOWN': return 'unknown';
      default: return 'unknown';
    }
  };

  return (
    <div className="glass-panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="panel-header">
        <div className="panel-title">
          <Terminal size={18} color="#10b981" />
          <span>FR-09 &amp; FR-10: Live Telemetry &amp; Audit Log</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>
            {logs.length} entries recorded
          </span>
          <button
            className="btn btn-secondary"
            onClick={onClearLogs}
            style={{ padding: '4px 8px', fontSize: '0.75rem' }}
            title="Clear logs"
          >
            <Trash2 size={13} />
          </button>
        </div>
      </div>

      <div className="panel-body" style={{ flex: 1, padding: '14px', display: 'flex', flexDirection: 'column' }}>
        <div className="log-stream" style={{ flex: 1 }}>
          {logs.length === 0 ? (
            <div style={{ textAlign: 'center', color: '#64748b', padding: '30px 0' }}>
              No audit events logged yet. Execute an action or demo above.
            </div>
          ) : (
            logs.map((log) => {
              const timeStr = new Date(log.timestamp).toLocaleTimeString();
              return (
                <div key={log.id} className="log-entry">
                  <span className="log-time">{timeStr}</span>
                  <span className={`log-tag ${getTagClass(log.result)}`}>
                    {log.result}
                  </span>
                  <div style={{ flex: 1 }}>
                    <div style={{ color: '#f8fafc', fontWeight: 500, fontSize: '0.84rem' }}>
                      <span style={{ color: '#38bdf8', marginRight: '6px' }}>[{log.workflow}]</span>
                      {log.message}
                    </div>
                    {log.reason_code && (
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '2px' }}>
                        Reason Code: <code>{log.reason_code}</code>
                      </div>
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
