import React, { useState } from 'react';
import { Info, AlertCircle, CheckCircle2, ChevronDown, ChevronUp } from 'lucide-react';

export default function SetupDisclosure({ acknowledged, onToggleAcknowledge }) {
  const [expanded, setExpanded] = useState(true);

  return (
    <div className="glass-panel" style={{ marginBottom: '24px' }}>
      <div className="panel-header" onClick={() => setExpanded(!expanded)} style={{ cursor: 'pointer' }}>
        <div className="panel-title">
          <Info size={19} color="#38bdf8" />
          <span>FR-01: Setup &amp; Transparency Disclosure</span>
          {acknowledged && (
            <span style={{ fontSize: '0.78rem', color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px', marginLeft: '8px' }}>
              <CheckCircle2 size={14} /> Acknowledged
            </span>
          )}
        </div>
        <button className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: '0.8rem' }}>
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>

      {expanded && (
        <div className="panel-body">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '16px' }}>
            <div style={{ background: 'rgba(56, 189, 248, 0.06)', border: '1px solid rgba(56, 189, 248, 0.2)', padding: '14px', borderRadius: '8px' }}>
              <div style={{ fontWeight: '600', color: '#38bdf8', marginBottom: '6px', fontSize: '0.9rem' }}>
                1. Manual vs. Assisted Boundary
              </div>
              <p style={{ fontSize: '0.82rem', color: '#cbd5e1', lineHeight: '1.4' }}>
                This prototype does <strong>not</strong> autonomously send Snaps or mass-modify friends. Actions require manual user dispatch in Snapchat or explicit in-app confirmation.
              </p>
            </div>

            <div style={{ background: 'rgba(245, 158, 11, 0.06)', border: '1px solid rgba(245, 158, 11, 0.2)', padding: '14px', borderRadius: '8px' }}>
              <div style={{ fontWeight: '600', color: '#f59e0b', marginBottom: '6px', fontSize: '0.9rem' }}>
                2. Privacy &amp; Credential Safety
              </div>
              <p style={{ fontSize: '0.82rem', color: '#cbd5e1', lineHeight: '1.4' }}>
                We <strong>never</strong> request, store, or intercept your Snapchat password, session tokens, or private media. Only locally curated contact lists are processed.
              </p>
            </div>

            <div style={{ background: 'rgba(239, 68, 68, 0.06)', border: '1px solid rgba(239, 68, 68, 0.2)', padding: '14px', borderRadius: '8px' }}>
              <div style={{ fontWeight: '600', color: '#ef4444', marginBottom: '6px', fontSize: '0.9rem' }}>
                3. Platform Policy Notice
              </div>
              <p style={{ fontSize: '0.82rem', color: '#cbd5e1', lineHeight: '1.4' }}>
                Snapchat strictly restricts bot automation. This tool provides deterministic simulation, local reminders, and transparent audit logging only.
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', fontSize: '0.88rem' }}>
              <input
                type="checkbox"
                checked={acknowledged}
                onChange={(e) => onToggleAcknowledge(e.target.checked)}
                style={{ width: '18px', height: '18px', accentColor: '#38bdf8' }}
              />
              <span>I acknowledge the assisted nature and policy boundaries of this prototype</span>
            </label>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>Requirement Gate: FR-01</span>
          </div>
        </div>
      )}
    </div>
  );
}
