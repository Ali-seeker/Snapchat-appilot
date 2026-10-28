import React from 'react';
import { Bell, Smartphone, RotateCcw } from 'lucide-react';

export default function TopBar({
  appState,
  connectedDevice,
  snapchatVersion,
  onReset
}) {
  const isRunning = appState === 'RUNNING';

  return (
    <header className="dashboard-topbar">
      <div className="topbar-greeting">
        <h2>
          <span>Hello, User!</span>
          <span>👋</span>
        </h2>
        <p>Let's keep your Snapchat game strong!</p>
      </div>

      <div className="topbar-actions">
        {/* Snapchat Target Version Badge */}
        <div className="snap-version-pill" title="Target Snapchat Application Build">
          <span>👻</span>
          <span>Snapchat v{snapchatVersion || '14.29.0.50'}</span>
        </div>

        {/* Connected Device Pill */}
        <div className="device-status-pill">
          <span className="pulse-indicator" style={{ background: isRunning ? '#38bdf8' : '#22c55e' }}></span>
          <Smartphone size={14} style={{ color: '#64748b' }} />
          <span>{connectedDevice ? (connectedDevice.model || connectedDevice.device_id) : 'Infinix X6817 (Connected)'}</span>
        </div>

        {/* Reset State Action */}
        <button
          className="icon-btn"
          onClick={onReset}
          title="Reset State Machine to IDLE"
        >
          <RotateCcw size={16} />
        </button>

        {/* Notification Bell */}
        <button className="icon-btn" title="Notifications">
          <Bell size={17} />
        </button>

        {/* User Profile */}
        <div className="user-profile-btn">
          <div className="user-avatar">U</div>
          <span>Demo User</span>
        </div>
      </div>
    </header>
  );
}
