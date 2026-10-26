import React from 'react';
import { FlaskConical, CheckCircle2, AlertTriangle, CopyCheck, HelpCircle, Loader2 } from 'lucide-react';

export default function DemoRunner({ onRunDemo, isRunning, activeScenario }) {
  const scenarios = [
    {
      id: 'full_suite',
      name: 'Run Full Test Suite',
      desc: 'Executes Success, Duplicates, Inactivity, and Timeout Recovery sequentially.',
      icon: <FlaskConical size={16} color="#38bdf8" />,
      primary: true
    },
    {
      id: 'success',
      name: 'Test Success Flow',
      desc: 'Simulates target review and safe local reminder generation.',
      icon: <CheckCircle2 size={16} color="#10b981" />
    },
    {
      id: 'duplicate',
      name: 'Test Duplicate Rejection',
      desc: 'Attempts duplicate target injection to verify normalization rules.',
      icon: <CopyCheck size={16} color="#f59e0b" />
    },
    {
      id: 'inactivity_unknown',
      name: 'Test Inactivity Policy',
      desc: 'Verifies unverified last-active data is marked strictly as Unknown.',
      icon: <HelpCircle size={16} color="#a855f7" />
    },
    {
      id: 'failure',
      name: 'Test Error & Recovery',
      desc: 'Simulates timeout and asserts safe recovery without data corruption.',
      icon: <AlertTriangle size={16} color="#f43f5e" />
    }
  ];

  return (
    <div className="glass-panel">
      <div className="panel-header">
        <div className="panel-title">
          <FlaskConical size={18} color="#a855f7" />
          <span>FR-12: Deterministic Demo Mode</span>
        </div>
        <span style={{ fontSize: '0.78rem', color: '#a855f7', fontWeight: 600 }}>
          SYNTHETIC TEST BENCH
        </span>
      </div>

      <div className="panel-body">
        <p style={{ fontSize: '0.84rem', color: '#94a3b8', marginBottom: '16px' }}>
          Test all acceptance criteria using synthetic telemetry without modifying any live account.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
          {scenarios.map((sc) => {
            const isThisRunning = isRunning && activeScenario === sc.id;
            return (
              <button
                key={sc.id}
                className={`btn ${sc.primary ? 'btn-primary' : 'btn-secondary'} ${isThisRunning ? 'demo-btn-active' : ''}`}
                disabled={isRunning}
                onClick={() => onRunDemo(sc.id)}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  textAlign: 'left',
                  padding: '12px',
                  height: 'auto',
                  gap: '6px',
                  cursor: isRunning ? 'not-allowed' : 'pointer',
                  position: 'relative'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600, fontSize: '0.88rem' }}>
                    {isThisRunning ? <Loader2 size={16} className="spin" color="#38bdf8" /> : sc.icon}
                    <span>{sc.name}</span>
                  </div>
                  {isThisRunning && (
                    <span style={{ fontSize: '0.68rem', background: '#38bdf8', color: '#0a0e17', fontWeight: 700, padding: '2px 6px', borderRadius: '4px' }}>
                      RUNNING
                    </span>
                  )}
                </div>
                <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)', lineHeight: '1.3' }}>
                  {sc.desc}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
