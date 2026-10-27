import React, { useState } from 'react';
import { Camera, Wand2, Users, Send } from 'lucide-react';

export default function AutoSnapCard({ isRunning, onTriggerWorkflow }) {
  const [randomFilter, setRandomFilter] = useState(true);
  const [selectAll, setSelectAll] = useState(true);
  const [maxRecipients, setMaxRecipients] = useState(15);

  const handleLaunch = () => {
    onTriggerWorkflow('snap', {
      random_filter: randomFilter,
      select_all: selectAll,
      max_recipients: maxRecipients
    });
  };

  return (
    <div className="glass-panel action-card">
      <div className="panel-header">
        <div className="panel-title">
          <Camera size={20} color="#eab308" />
          <span>Auto Snap Dispatch</span>
        </div>
        <span className="badge badge-amber">Camera Live</span>
      </div>

      <div className="panel-body">
        <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '14px' }}>
          Captures a photo, applies a random aesthetic lens/filter, selects friends, and sends the Snap.
        </p>

        {/* Feature Switches */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '16px' }}>
          <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', background: 'rgba(234, 179, 8, 0.05)', borderRadius: '8px', border: '1px solid rgba(234, 179, 8, 0.2)', cursor: 'pointer' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Wand2 size={16} color="#eab308" />
              <div>
                <div style={{ fontSize: '0.84rem', fontWeight: 600, color: '#f8fafc' }}>Random Aesthetic Filter</div>
                <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Swipes preview to apply lens/color filters</div>
              </div>
            </div>
            <input
              type="checkbox"
              checked={randomFilter}
              onChange={(e) => setRandomFilter(e.target.checked)}
              disabled={isRunning}
              style={{ width: '18px', height: '18px', accentColor: '#eab308', cursor: 'pointer' }}
            />
          </label>

          <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', background: 'rgba(234, 179, 8, 0.05)', borderRadius: '8px', border: '1px solid rgba(234, 179, 8, 0.2)', cursor: 'pointer' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Users size={16} color="#eab308" />
              <div>
                <div style={{ fontSize: '0.84rem', fontWeight: 600, color: '#f8fafc' }}>Select All Friends</div>
                <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Dispatches to all available contacts/shortcuts</div>
              </div>
            </div>
            <input
              type="checkbox"
              checked={selectAll}
              onChange={(e) => setSelectAll(e.target.checked)}
              disabled={isRunning}
              style={{ width: '18px', height: '18px', accentColor: '#eab308', cursor: 'pointer' }}
            />
          </label>
        </div>

        {/* Action Button */}
        <button
          className="btn"
          style={{ width: '100%', background: '#eab308', color: '#0f172a', padding: '10px 16px', fontSize: '0.92rem', fontWeight: 700, display: 'flex', justifyContent: 'center', gap: '8px', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
          onClick={handleLaunch}
          disabled={isRunning}
        >
          <Send size={18} />
          <span>Capture &amp; Send Snap Now</span>
        </button>
      </div>
    </div>
  );
}
