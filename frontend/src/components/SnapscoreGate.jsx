import React from 'react';
import { Lock, ShieldAlert } from 'lucide-react';

export default function SnapscoreGate() {
  return (
    <div className="glass-panel" style={{ marginTop: '24px', background: 'rgba(30, 41, 59, 0.4)' }}>
      <div className="panel-body" style={{ display: 'flex', alignItems: 'center', gap: '14px', padding: '16px 20px' }}>
        <div style={{ background: 'rgba(239, 68, 68, 0.15)', padding: '10px', borderRadius: '10px' }}>
          <ShieldAlert size={22} color="#f87171" />
        </div>
        <div>
          <div style={{ fontWeight: 600, fontSize: '0.92rem', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>FR-13: Snapscore Feature Gate</span>
            <span style={{ fontSize: '0.72rem', background: 'rgba(239, 68, 68, 0.2)', color: '#fca5a5', padding: '2px 8px', borderRadius: '4px', textTransform: 'uppercase' }}>
              Enforced Policy Gate
            </span>
          </div>
          <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '3px' }}>
            This application does <strong>not</strong> artificially boost, inflate, or manipulate Snapscore metrics. Artificial score tampering violates Snapchat policies and will lead to immediate account restrictions.
          </p>
        </div>
      </div>
    </div>
  );
}
