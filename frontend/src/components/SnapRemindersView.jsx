import React, { useState } from 'react';
import {
  Send,
  Plus,
  Clock,
  Sparkles,
  Users,
  MoreVertical,
  CheckCircle2,
  Camera
} from 'lucide-react';

import { useEffect } from 'react';

export default function SnapRemindersView({
  onTriggerWorkflow
}) {
  const [schedules, setSchedules] = useState([
    { id: 1, name: 'Best Friend', schedule: 'Daily • 6:00 PM', filter: 'Vibrant Glow', active: true },
    { id: 2, name: 'Family Group', schedule: 'Daily • 8:30 PM', filter: 'Golden Hour', active: true },
    { id: 3, name: 'College Friends', schedule: 'Mon, Wed, Fri • 7:00 PM', filter: 'Film Grain', active: false },
    { id: 4, name: 'Work Group', schedule: 'Tue, Thu • 9:00 AM', filter: 'Clean Soft', active: true }
  ]);

  const [randomFilter, setRandomFilter] = useState(true);
  const [shortcuts, setShortcuts] = useState([]);
  const [selectedShortcut, setSelectedShortcut] = useState('🤙');
  const [dispatchMode, setDispatchMode] = useState('count'); // 'count' | 'select_all' | 'shortcut'

  useEffect(() => {
    fetch('http://localhost:8000/api/shortcuts')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data) && data.length > 0) {
          setShortcuts(data);
          setSelectedShortcut(data[0].emoji);
        }
      })
      .catch(() => { });
  }, []);

  const handleSendNow = () => {
    onTriggerWorkflow('snap', {
      random_filter: randomFilter,
      recipient_mode: dispatchMode,
      shortcut_emoji: dispatchMode === 'shortcut' ? selectedShortcut : null,
      select_all: dispatchMode === 'select_all',
      max_recipients: dispatchMode === 'select_all' ? 999 : 5
    });
  };

  const toggleSchedule = (id) => {
    setSchedules((prev) =>
      prev.map((s) => (s.id === id ? { ...s, active: !s.active } : s))
    );
  };

  return (
    <div className="page-container">
      {/* Top Card: Filter & Quick Dispatch */}
      <div className="white-panel">
        <div className="panel-header-row">
          <div className="panel-header-title">
            <h3>Snap Send &amp; Auto Dispatch</h3>
            <p>Schedule snaps to send automatically with aesthetic lens filters.</p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              className="btn-primary"
              onClick={handleSendNow}
            >
              <Send size={16} />
              <span>Send Snap Now</span>
            </button>
          </div>
        </div>

        {/* Recipient Mode Selection Pill Bar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', background: '#f8fafc', padding: '12px 18px', borderRadius: '12px', border: '1px solid #e2e8f0', marginBottom: '12px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Users size={17} style={{ color: '#0284c7' }} />
            <span style={{ fontWeight: 600, fontSize: '0.88rem', color: '#0f172a' }}>Dispatch Target:</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <button
              className={`filter-tab ${dispatchMode === 'count' ? 'active' : ''}`}
              onClick={() => setDispatchMode('count')}
            >
              🔥 Streak Friends (Top 5)
            </button>
            <button
              className={`filter-tab ${dispatchMode === 'select_all' ? 'active' : ''}`}
              onClick={() => setDispatchMode('select_all')}
            >
              ⚡ Select All (All Friends)
            </button>
            {shortcuts.map((sc) => (
              <button
                key={sc.id}
                className={`filter-tab ${dispatchMode === 'shortcut' && selectedShortcut === sc.emoji ? 'active' : ''}`}
                onClick={() => {
                  setDispatchMode('shortcut');
                  setSelectedShortcut(sc.emoji);
                }}
              >
                {sc.emoji} {sc.name}
              </button>
            ))}
          </div>
        </div>

        {/* Filter Selection Pill Bar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', background: '#f8fafc', padding: '12px 18px', borderRadius: '12px', border: '1px solid #e2e8f0', marginBottom: '20px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={17} style={{ color: '#7c3aed' }} />
            <span style={{ fontWeight: 600, fontSize: '0.88rem', color: '#0f172a' }}>Filter Setting:</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              className={`filter-tab ${randomFilter ? 'active' : ''}`}
              onClick={() => setRandomFilter(true)}
            >
              🎲 Random Aesthetic Lens Swipe (Recommended)
            </button>
            <button
              className={`filter-tab ${!randomFilter ? 'active' : ''}`}
              onClick={() => setRandomFilter(false)}
            >
              Standard Natural Camera
            </button>
          </div>
        </div>

        {/* Schedules List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {schedules.map((item) => (
            <div
              key={item.id}
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
                  className="contact-avatar"
                  style={{
                    background: item.active ? 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)' : '#cbd5e1'
                  }}
                >
                  <Users size={17} />
                </div>
                <div>
                  <div style={{ fontWeight: 600, color: '#0f172a', fontSize: '0.94rem' }}>
                    {item.name}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: '#64748b', marginTop: '2px' }}>
                    <Clock size={13} />
                    <span>{item.schedule}</span>
                    <span>•</span>
                    <span style={{ color: '#7c3aed', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '2px' }}>
                      <Sparkles size={12} /> {item.filter}
                    </span>
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <span
                  className={`badge-status ${item.active ? 'badge-active' : 'badge-paused'}`}
                >
                  {item.active ? 'Active' : 'Paused'}
                </span>

                {/* Toggle switch */}
                <label className="switch">
                  <input
                    type="checkbox"
                    checked={item.active}
                    onChange={() => toggleSchedule(item.id)}
                  />
                  <span className="slider"></span>
                </label>

                <button
                  className="icon-btn"
                  style={{ width: '32px', height: '32px' }}
                  title="Options"
                >
                  <MoreVertical size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
