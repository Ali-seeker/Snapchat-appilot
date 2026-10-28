import React, { useState } from 'react';
import {
  CheckCircle2,
  Smartphone,
  Zap,
  Calendar,
  UserPlus,
  Trash2,
  Flame,
  Send,
  ArrowRight,
  Play,
  Pause,
  Square,
  ShieldCheck,
  Sparkles
} from 'lucide-react';
import ghostHero from '../assets/ghost_hero.png';

export default function OverviewView({
  appState,
  activeWorkflow,
  isPaused,
  isStopped,
  connectedDevice,
  snapchatVersion,
  contactsCount,
  onTriggerWorkflow,
  onPauseWorkflow,
  onResumeWorkflow,
  onEmergencyStop,
  onOpenQuickModal
}) {
  const isRunning = appState === 'RUNNING';
  const [selectedEngine, setSelectedEngine] = useState('chain');

  return (
    <div className="page-container">
      {/* Hero Banner */}
      <div className="hero-banner">
        <div className="hero-content">
          <h1 className="hero-title">
            Automate Your Snapchat<br />and Stay Ahead!
          </h1>
          <p className="hero-subtitle">
            Add friends, manage streaks, send snaps and increase your Snapscore — all in one place.
          </p>
          <button
            type="button"
            className="hero-cta-btn"
            onClick={() => onTriggerWorkflow('chain', { routine_type: 'morning' })}
          >
            <span>Start Automation</span>
            <ArrowRight size={18} />
          </button>
        </div>

        <div className="hero-illustration">
          <img
            src={ghostHero}
            alt="Snapchat Automation Ghost"
            className="hero-ghost-img"
          />
        </div>
      </div>

      {/* 4 KPI Metric Cards */}
      <div className="kpi-grid">
        {/* 1. System Status */}
        <div className="kpi-card">
          <div className="kpi-icon-wrap green">
            <CheckCircle2 size={24} />
          </div>
          <div className="kpi-info">
            <span className="kpi-label">System Status</span>
            <span className="kpi-value">{isRunning ? 'Running' : 'Ready'}</span>
            <span className="kpi-sub">
              {isRunning && activeWorkflow ? activeWorkflow : 'All systems are working fine'}
            </span>
          </div>
        </div>

        {/* 2. Connected Account / Device */}
        <div className="kpi-card">
          <div className="kpi-icon-wrap blue">
            <Smartphone size={24} />
          </div>
          <div className="kpi-info">
            <span className="kpi-label">Connected Device</span>
            <span className="kpi-value">
              {connectedDevice ? (connectedDevice.model || connectedDevice.device_id) : 'Infinix X6817'}
            </span>
            <span className="kpi-sub">
              Snapchat v{snapchatVersion || '14.29.0.50'} Active
            </span>
          </div>
        </div>

        {/* 3. Active Tasks */}
        <div className="kpi-card">
          <div className="kpi-icon-wrap purple">
            <Zap size={24} />
          </div>
          <div className="kpi-info">
            <span className="kpi-label">Active Tasks</span>
            <span className="kpi-value">{isRunning ? '1' : '0'}</span>
            <span className="kpi-sub">{isRunning ? 'Executing right now' : 'Idle and ready'}</span>
          </div>
        </div>

        {/* 4. Scheduled Tasks */}
        <div className="kpi-card">
          <div className="kpi-icon-wrap pink">
            <Calendar size={24} />
          </div>
          <div className="kpi-info">
            <span className="kpi-label">Scheduled Tasks</span>
            <span className="kpi-value">3</span>
            <span className="kpi-sub">Will run later today</span>
          </div>
        </div>
      </div>

      {/* Overview Split Grid: Quick Actions & Today's Overview */}
      <div className="overview-split-grid">
        {/* Left: Quick Actions */}
        <div>
          <div className="section-title">
            <span>Quick Actions</span>
            <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 500 }}>
              Click any card to launch automation
            </span>
          </div>

          <div className="quick-actions-grid">
            {/* Add Friends (Yellow) */}
            <div
              className="action-box yellow"
              onClick={() => onTriggerWorkflow('follow', { mode: 'quick_add', max_count: 5 })}
              title="Click to trigger Bulk Follow"
            >
              <div className="action-top">
                <div className="action-icon-circle">
                  <UserPlus size={20} />
                </div>
                <div className="action-text">
                  <h4>Add Friends</h4>
                  <p>Bulk add new friends from suggestions or search</p>
                </div>
              </div>
              <div className="action-arrow">
                <ArrowRight size={20} />
              </div>
            </div>

            {/* Remove Friends (Purple) */}
            <div
              className="action-box purple"
              onClick={() => onTriggerWorkflow('unfollow', { filter_type: 'no_streak', days_threshold: 17, max_unfollow: 2 })}
              title="Click to trigger Smart Unfollow"
            >
              <div className="action-top">
                <div className="action-icon-circle">
                  <Trash2 size={20} />
                </div>
                <div className="action-text">
                  <h4>Remove Friends</h4>
                  <p>Smart filter and remove inactive or no-streak friends</p>
                </div>
              </div>
              <div className="action-arrow">
                <ArrowRight size={20} />
              </div>
            </div>

            {/* Streak Reminders / Booster (Green) */}
            <div
              className="action-box green"
              onClick={() => onTriggerWorkflow('snapscore', { cycles: 3, select_all: true, max_recipients: 5 })}
              title="Click to trigger Snapscore Booster"
            >
              <div className="action-top">
                <div className="action-icon-circle">
                  <Flame size={20} />
                </div>
                <div className="action-text">
                  <h4>Streak Reminders</h4>
                  <p>Boost snapscore &amp; maintain streaks automatically</p>
                </div>
              </div>
              <div className="action-arrow">
                <ArrowRight size={20} />
              </div>
            </div>

            {/* Snap Reminders / Dispatch (Blue) */}
            <div
              className="action-box blue"
              onClick={() => onTriggerWorkflow('snap', { random_filter: true, select_all: true, max_recipients: 5 })}
              title="Click to trigger Auto Snap Dispatch"
            >
              <div className="action-top">
                <div className="action-icon-circle">
                  <Send size={20} />
                </div>
                <div className="action-text">
                  <h4>Snap Reminders</h4>
                  <p>Send aesthetic lens filtered snaps on schedule</p>
                </div>
              </div>
              <div className="action-arrow">
                <ArrowRight size={20} />
              </div>
            </div>
          </div>
        </div>

        {/* Right: Today's Overview */}
        <div>
          <div className="section-title">
            <span>Today's Overview</span>
          </div>

          <div className="overview-card">
            <div className="overview-list">
              <div className="overview-row">
                <div className="overview-left">
                  <div className="overview-icon-small" style={{ background: '#DCFCE7', color: '#16A34A' }}>
                    <UserPlus size={16} />
                  </div>
                  <span>Friends Added</span>
                </div>
                <span className="overview-val val-green">12</span>
              </div>

              <div className="overview-row">
                <div className="overview-left">
                  <div className="overview-icon-small" style={{ background: '#FCE7F3', color: '#E11D48' }}>
                    <Trash2 size={16} />
                  </div>
                  <span>Friends Removed</span>
                </div>
                <span className="overview-val val-pink">5</span>
              </div>

              <div className="overview-row">
                <div className="overview-left">
                  <div className="overview-icon-small" style={{ background: '#FEF3C7', color: '#D97706' }}>
                    <Flame size={16} />
                  </div>
                  <span>Streak Reminders</span>
                </div>
                <span className="overview-val val-amber">4</span>
              </div>

              <div className="overview-row">
                <div className="overview-left">
                  <div className="overview-icon-small" style={{ background: '#E0F2FE', color: '#0284C7' }}>
                    <Send size={16} />
                  </div>
                  <span>Snap Reminders</span>
                </div>
                <span className="overview-val val-blue">3</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Executive Automation Launch & Emergency Controls */}
      <div className="white-panel" style={{ marginTop: '4px' }}>
        <div className="panel-header-row">
          <div className="panel-header-title">
            <h3>Enterprise Automation Hub</h3>
            <p>Select a workflow mode below to trigger live execution on the mobile device.</p>
          </div>

          {/* Emergency Stop & Pause controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {isRunning && !isPaused && (
              <button
                className="btn-secondary"
                onClick={onPauseWorkflow}
                title="Pause active automation"
              >
                <Pause size={15} />
                <span>Pause</span>
              </button>
            )}
            {isRunning && isPaused && (
              <button
                className="btn-primary"
                onClick={onResumeWorkflow}
                title="Resume paused automation"
              >
                <Play size={15} />
                <span>Resume</span>
              </button>
            )}
            <button
              className="btn-danger"
              onClick={onEmergencyStop}
              title="Instantly halt all automation actions"
            >
              <Square size={15} />
              <span>Emergency Stop</span>
            </button>
          </div>
        </div>

        {/* Workflow Quick Launcher Bar */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
          <button
            className="btn-secondary"
            style={{ justifyContent: 'flex-start', padding: '12px 16px' }}
            onClick={() => onTriggerWorkflow('follow', { mode: 'quick_add', max_count: 3 })}
          >
            <UserPlus size={18} style={{ color: '#F59E0B' }} />
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontWeight: 600, fontSize: '0.88rem' }}>Bulk Follow</div>
              <div style={{ fontSize: '0.74rem', color: '#64748b' }}>Quick Add Suggestions</div>
            </div>
          </button>

          <button
            className="btn-secondary"
            style={{ justifyContent: 'flex-start', padding: '12px 16px' }}
            onClick={() => onTriggerWorkflow('unfollow', { filter_type: 'no_streak', days_threshold: 17, max_unfollow: 2 })}
          >
            <Trash2 size={18} style={{ color: '#7C3AED' }} />
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontWeight: 600, fontSize: '0.88rem' }}>Smart Unfollow</div>
              <div style={{ fontSize: '0.74rem', color: '#64748b' }}>No-Streak &amp; Inactive Filter</div>
            </div>
          </button>

          <button
            className="btn-secondary"
            style={{ justifyContent: 'flex-start', padding: '12px 16px' }}
            onClick={() => onTriggerWorkflow('snap', { random_filter: true, select_all: true, max_recipients: 5 })}
          >
            <Send size={18} style={{ color: '#0284C7' }} />
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontWeight: 600, fontSize: '0.88rem' }}>Auto Snap</div>
              <div style={{ fontSize: '0.74rem', color: '#64748b' }}>Random Filter &amp; Send</div>
            </div>
          </button>

          <button
            className="btn-secondary"
            style={{ justifyContent: 'flex-start', padding: '12px 16px' }}
            onClick={() => onTriggerWorkflow('snapscore', { cycles: 2, select_all: true, max_recipients: 4 })}
          >
            <Flame size={18} style={{ color: '#16A34A' }} />
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontWeight: 600, fontSize: '0.88rem' }}>Score Booster</div>
              <div style={{ fontSize: '0.74rem', color: '#64748b' }}>Multi-cycle Safe Boost</div>
            </div>
          </button>

          <button
            className="btn-primary"
            style={{ justifyContent: 'flex-start', padding: '12px 16px' }}
            onClick={() => onTriggerWorkflow('chain', { routine_type: 'morning' })}
          >
            <Sparkles size={18} style={{ color: '#FFFC00' }} />
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontWeight: 600, fontSize: '0.88rem', color: '#fff' }}>Chained Routine</div>
              <div style={{ fontSize: '0.74rem', color: '#E2E8F0' }}>Snap + Quick Add Combined</div>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}
