import React from 'react';
import {
  Home,
  Users,
  Flame,
  Send,
  Activity,
  Settings,
  HelpCircle,
  Crown
} from 'lucide-react';
import ghostHero from '../assets/ghost_hero.png';

export default function Sidebar({ activeTab, onSelectTab }) {
  const navItems = [
    { id: 'home', label: 'Home', icon: Home },
    { id: 'friends', label: 'Friends', icon: Users },
    { id: 'streaks', label: 'Streak Reminders', icon: Flame },
    { id: 'snaps', label: 'Snap Reminders', icon: Send },
    { id: 'activity', label: 'Activity', icon: Activity },
    { id: 'settings', label: 'Settings', icon: Settings },
    { id: 'help', label: 'Help', icon: HelpCircle }
  ];

  return (
    <aside className="dashboard-sidebar">
      <div>
        {/* Logo */}
        <div className="sidebar-logo">
          <div className="logo-badge">
            <span style={{ fontSize: '1.25rem' }}>👻</span>
          </div>
          <span className="logo-text">Appilot</span>
        </div>

        {/* Navigation Items */}
        <nav className="sidebar-nav">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                type="button"
                className={`nav-item ${isActive ? 'active' : ''}`}
                onClick={() => onSelectTab(item.id)}
              >
                <div className="nav-icon">
                  <Icon size={19} />
                </div>
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Sidebar Footer Card */}
      <div className="sidebar-footer-card">
        <div className="crown-icon-wrap">
          <Crown size={22} color="#FACC15" fill="#FACC15" />
        </div>
        <div className="sidebar-footer-title">Stay Connected</div>
        <div className="sidebar-footer-sub">Keep Your Streaks Alive!</div>
        <img
          src={ghostHero}
          alt="Snapchat Ghost"
          className="sidebar-footer-ghost"
        />
      </div>
    </aside>
  );
}
