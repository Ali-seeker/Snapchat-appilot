import React, { useState, useEffect } from 'react';
import {
  Calendar,
  Clock,
  Play,
  Trash2,
  Plus,
  Flame,
  Send,
  UserPlus,
  UserMinus,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Info,
  Smartphone,
  SmartphoneCharging,
  Sliders,
  ChevronRight,
  ShieldCheck,
  Zap,
  X
} from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

export default function ScheduleView({ onTriggerWorkflow }) {
  const [schedules, setSchedules] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [deviceConnected, setDeviceConnected] = useState(true);
  const [shortcuts, setShortcuts] = useState([]);

  // Form State
  const [title, setTitle] = useState('');
  const [automationType, setAutomationType] = useState('snapscore'); // snapscore | snap | follow | unfollow
  const [selectedDate, setSelectedDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [startTime, setStartTime] = useState('20:00');
  const [endTime, setEndTime] = useState('');
  const [frequency, setFrequency] = useState('daily'); // once | daily

  // Automation-specific parameters
  const [cycles, setCycles] = useState(3);
  const [boosterMode, setBoosterMode] = useState('count');
  const [boosterRecipients, setBoosterRecipients] = useState(5);
  const [shortcutEmoji, setShortcutEmoji] = useState('🤙');

  const [randomFilter, setRandomFilter] = useState(true);
  const [snapMode, setSnapMode] = useState('count');
  const [snapRecipients, setSnapRecipients] = useState(5);

  const [followMode, setFollowMode] = useState('quick_add');
  const [followCount, setFollowCount] = useState(5);
  const [targetUsername, setTargetUsername] = useState('');

  const [unfollowFilter, setUnfollowFilter] = useState('no_streak');
  const [unfollowDays, setUnfollowDays] = useState(14);
  const [unfollowCount, setUnfollowCount] = useState(5);
  const [unfollowSelectAll, setUnfollowSelectAll] = useState(false);

  // Fetch schedules, device status, and shortcuts
  const fetchSchedules = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/schedules`);
      if (res.ok) {
        const data = await res.json();
        setSchedules(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchStatus = async () => {
    try {
      const devRes = await fetch(`${API_BASE}/devices`);
      if (devRes.ok) {
        const devs = await devRes.json();
        setDeviceConnected(Array.isArray(devs) && devs.length > 0 && devs.some(d => d.is_connected));
      }
      const scRes = await fetch(`${API_BASE}/shortcuts`);
      if (scRes.ok) {
        const scData = await scRes.json();
        if (Array.isArray(scData) && scData.length > 0) {
          setShortcuts(scData);
          setShortcutEmoji(scData[0].emoji);
        }
      }
    } catch (e) {}
  };

  useEffect(() => {
    fetchSchedules();
    fetchStatus();
    const timer = setInterval(() => {
      fetchSchedules();
      fetchStatus();
    }, 12000);
    return () => clearInterval(timer);
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();

    let params = {};
    if (automationType === 'snapscore') {
      params = {
        cycles: parseInt(cycles, 10) || 3,
        recipient_mode: boosterMode,
        select_all: boosterMode === 'select_all',
        max_recipients: boosterMode === 'select_all' ? 999 : (parseInt(boosterRecipients, 10) || 5),
        shortcut_emoji: boosterMode === 'shortcut' ? shortcutEmoji : null
      };
    } else if (automationType === 'snap') {
      params = {
        random_filter: randomFilter,
        recipient_mode: snapMode,
        select_all: snapMode === 'select_all',
        max_recipients: snapMode === 'select_all' ? 999 : (parseInt(snapRecipients, 10) || 5),
        shortcut_emoji: snapMode === 'shortcut' ? shortcutEmoji : null
      };
    } else if (automationType === 'follow') {
      params = {
        mode: followMode,
        target_ids: followMode === 'search' ? [targetUsername.trim().replace(/^@/, '')] : [],
        max_count: parseInt(followCount, 10) || 5
      };
    } else if (automationType === 'unfollow') {
      params = {
        filter_type: unfollowFilter,
        days_threshold: unfollowFilter === 'inactive' ? (parseInt(unfollowDays, 10) || 14) : 0,
        max_unfollow: unfollowSelectAll ? 999 : (parseInt(unfollowCount, 10) || 5),
        select_all: unfollowSelectAll
      };
    }

    const payload = {
      title: title.trim() || `Scheduled ${automationType.toUpperCase()}`,
      automation_type: automationType,
      params,
      date: selectedDate,
      start_time: startTime,
      end_time: endTime.trim() || null,
      frequency
    };

    try {
      const res = await fetch(`${API_BASE}/schedules`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setShowModal(false);
        setTitle('');
        fetchSchedules();
      }
    } catch (e) {
      alert('Failed to save schedule.');
    }
  };

  const handleToggle = async (id) => {
    try {
      await fetch(`${API_BASE}/schedules/${id}/toggle`, { method: 'POST' });
      fetchSchedules();
    } catch (e) {}
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this schedule?')) return;
    try {
      await fetch(`${API_BASE}/schedules/${id}`, { method: 'DELETE' });
      fetchSchedules();
    } catch (e) {}
  };

  const handleRunNow = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/schedules/${id}/run_now`, { method: 'POST' });
      const data = await res.json();
      if (res.ok) {
        alert(`Schedule '${data.title}' launched immediately on connected phone!`);
        fetchSchedules();
      }
    } catch (e) {
      alert('Could not trigger schedule run.');
    }
  };

  const activeCount = schedules.filter(s => s.is_active).length;
  const offlineWarnings = schedules.filter(s => s.last_status === 'DEVICE_OFFLINE').length;

  return (
    <div className="page-container">
      {/* Top Banner Stats */}
      <div className="grid-3" style={{ marginBottom: '16px' }}>
        <div className="stats-card">
          <div className="stats-content">
            <span className="stats-label">Active Schedules</span>
            <div className="stats-value" style={{ color: '#0284c7' }}>{activeCount}</div>
            <span className="stats-sub">Monitored in background</span>
          </div>
          <div className="stats-icon-wrap" style={{ background: '#e0f2fe', color: '#0284c7' }}>
            <Clock size={24} />
          </div>
        </div>

        <div className="stats-card">
          <div className="stats-content">
            <span className="stats-label">Phone Connectivity</span>
            <div className="stats-value" style={{ color: deviceConnected ? '#16a34a' : '#ea580c' }}>
              {deviceConnected ? 'Connected' : 'Offline'}
            </div>
            <span className="stats-sub">
              {deviceConnected ? 'Ready for automated dispatch' : 'Re-connect phone via USB'}
            </span>
          </div>
          <div className="stats-icon-wrap" style={{ background: deviceConnected ? '#dcfce7' : '#ffedd5', color: deviceConnected ? '#16a34a' : '#ea580c' }}>
            {deviceConnected ? <SmartphoneCharging size={24} /> : <Smartphone size={24} />}
          </div>
        </div>

        <div className="stats-card">
          <div className="stats-content">
            <span className="stats-label">Offline Safeguard</span>
            <div className="stats-value" style={{ color: offlineWarnings > 0 ? '#dc2626' : '#16a34a' }}>
              {offlineWarnings > 0 ? `${offlineWarnings} Missed` : '100% Protected'}
            </div>
            <span className="stats-sub">No crashes if phone disconnected</span>
          </div>
          <div className="stats-icon-wrap" style={{ background: '#f3e8ff', color: '#9333ea' }}>
            <ShieldCheck size={24} />
          </div>
        </div>
      </div>

      {/* Main Panel */}
      <div className="white-panel">
        <div className="panel-header-row">
          <div className="panel-header-title">
            <h3>Automated Automation Scheduler</h3>
            <p>Schedule Snapscore Boosters, Snap Sends, or Friend cleanup to run unattended at specific dates &amp; times.</p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              className="btn-secondary"
              onClick={fetchSchedules}
              disabled={isLoading}
              title="Refresh schedules list"
            >
              <RefreshCw size={15} className={isLoading ? 'spin' : ''} />
              <span>Refresh</span>
            </button>

            <button
              className="btn-primary"
              onClick={() => setShowModal(true)}
            >
              <Plus size={16} />
              <span>Create New Schedule</span>
            </button>
          </div>
        </div>

        {/* Safety Edge Case Disclosure */}
        <div style={{
          background: '#f8fafc',
          border: '1px solid #e2e8f0',
          borderRadius: '12px',
          padding: '12px 16px',
          marginBottom: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <Info size={18} color="#0284c7" style={{ flexShrink: 0 }} />
          <div style={{ fontSize: '0.84rem', color: '#475569', lineHeight: '1.4' }}>
            <strong>Device Offline Protection:</strong> If your mobile phone is disconnected when a schedule is due, Appilot safely halts execution, marks the event as <code>DEVICE_OFFLINE</code>, and alerts you without misclicking or throwing errors.
          </div>
        </div>

        {/* Schedules List */}
        {schedules.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '48px 24px', color: '#64748b' }}>
            <Calendar size={48} style={{ opacity: 0.3, margin: '0 auto 12px' }} />
            <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: '#0f172a', marginBottom: '4px' }}>No Schedules Configured</h4>
            <p style={{ fontSize: '0.86rem' }}>Click the <strong>'Create New Schedule'</strong> button above to automate tasks on your calendar.</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {schedules.map((item) => {
              const isBooster = item.automation_type === 'snapscore';
              const isSnap = item.automation_type === 'snap';
              const isFollow = item.automation_type === 'follow';
              const isUnfollow = item.automation_type === 'unfollow';

              return (
                <div
                  key={item.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '16px 20px',
                    borderRadius: '14px',
                    border: '1px solid #e2e8f0',
                    background: item.is_active ? '#ffffff' : '#f8fafc',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
                    flexWrap: 'wrap',
                    gap: '12px',
                    opacity: item.is_active ? 1 : 0.75
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px', minWidth: '280px' }}>
                    <div
                      style={{
                        width: '42px',
                        height: '42px',
                        borderRadius: '10px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        background: isBooster ? '#dcfce7' : isSnap ? '#e0f2fe' : isFollow ? '#fef3c7' : '#fce7f3',
                        color: isBooster ? '#16a34a' : isSnap ? '#0284c7' : isFollow ? '#d97706' : '#e11d48'
                      }}
                    >
                      {isBooster && <Flame size={20} />}
                      {isSnap && <Send size={20} />}
                      {isFollow && <UserPlus size={20} />}
                      {isUnfollow && <UserMinus size={20} />}
                    </div>

                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontWeight: 700, fontSize: '0.96rem', color: '#0f172a' }}>{item.title}</span>
                        <span
                          style={{
                            fontSize: '0.72rem',
                            padding: '2px 8px',
                            borderRadius: '999px',
                            fontWeight: 600,
                            background: isBooster ? '#dcfce7' : isSnap ? '#e0f2fe' : isFollow ? '#fef3c7' : '#fce7f3',
                            color: isBooster ? '#166534' : isSnap ? '#0369a1' : isFollow ? '#92400e' : '#9d174d'
                          }}
                        >
                          {isBooster && 'Snapscore Booster'}
                          {isSnap && 'Snap Send'}
                          {isFollow && 'Add Friends'}
                          {isUnfollow && 'Remove Friends'}
                        </span>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.8rem', color: '#64748b', marginTop: '4px' }}>
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                          <Calendar size={13} /> {item.date}
                        </span>
                        <span>•</span>
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                          <Clock size={13} /> {item.start_time} {item.end_time ? `➔ ${item.end_time}` : ''}
                        </span>
                        <span>•</span>
                        <span style={{ textTransform: 'capitalize', fontWeight: 600, color: '#334155' }}>
                          {item.frequency === 'daily' ? 'Repeats Daily' : 'Runs Once'}
                        </span>
                      </div>

                      {/* Params summary tag */}
                      <div style={{ marginTop: '6px', fontSize: '0.76rem', color: '#475569' }}>
                        {isBooster && (
                          <span>⚡ {item.params?.cycles || 3} Cycles • Target: {item.params?.recipient_mode?.toUpperCase()} {item.params?.shortcut_emoji || ''}</span>
                        )}
                        {isSnap && (
                          <span>📸 Filter: {item.params?.random_filter ? 'Aesthetic Lens' : 'None'} • Mode: {item.params?.recipient_mode?.toUpperCase()}</span>
                        )}
                        {isFollow && (
                          <span>👥 {item.params?.mode === 'search' ? `Target @${item.params?.target_ids?.[0]}` : `Quick Add up to ${item.params?.max_count || 5}`}</span>
                        )}
                        {isUnfollow && (
                          <span>🗑️ Filter: {item.params?.filter_type} • Limit: {item.params?.select_all ? 'ALL' : item.params?.max_unfollow}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Status & Actions */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                    {/* Status Badge */}
                    {item.last_status === 'DEVICE_OFFLINE' && (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: '#fee2e2', color: '#b91c1c', padding: '4px 10px', borderRadius: '8px', fontSize: '0.78rem', fontWeight: 600 }} title={item.last_error || 'Device was offline'}>
                        <AlertTriangle size={13} /> Phone Disconnected
                      </span>
                    )}
                    {item.last_status === 'COMPLETED' && (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: '#dcfce7', color: '#16a34a', padding: '4px 10px', borderRadius: '8px', fontSize: '0.78rem', fontWeight: 600 }}>
                        <CheckCircle2 size={13} /> Success
                      </span>
                    )}
                    {item.last_status === 'RUNNING' && (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: '#f3e8ff', color: '#9333ea', padding: '4px 10px', borderRadius: '8px', fontSize: '0.78rem', fontWeight: 600 }}>
                        <RefreshCw size={13} className="spin" /> Executing...
                      </span>
                    )}
                    {(!item.last_status || item.last_status === 'PENDING') && (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: '#f1f5f9', color: '#475569', padding: '4px 10px', borderRadius: '8px', fontSize: '0.78rem', fontWeight: 600 }}>
                        <Clock size={13} /> Pending
                      </span>
                    )}

                    {/* Toggle Active */}
                    <label className="switch" title={item.is_active ? 'Active' : 'Paused'}>
                      <input
                        type="checkbox"
                        checked={item.is_active}
                        onChange={() => handleToggle(item.id)}
                      />
                      <span className="slider"></span>
                    </label>

                    {/* Manual Immediate Run Button */}
                    <button
                      className="icon-btn"
                      onClick={() => handleRunNow(item.id)}
                      title="Run Schedule Now (Test dispatch)"
                      style={{ color: '#0284c7' }}
                    >
                      <Play size={16} fill="#0284c7" />
                    </button>

                    {/* Delete button */}
                    <button
                      className="icon-btn"
                      onClick={() => handleDelete(item.id)}
                      title="Delete Schedule"
                      style={{ color: '#ef4444' }}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Creation Modal */}
      {showModal && (
        <div className="modal-backdrop" onClick={() => setShowModal(false)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '580px', maxHeight: '90vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#0f172a' }}>Schedule Automation</h3>
                <p style={{ fontSize: '0.82rem', color: '#64748b' }}>Configure task parameters, date, and execution timing.</p>
              </div>
              <button onClick={() => setShowModal(false)} style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#94a3b8' }}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* Title */}
              <div>
                <label className="config-form-label">Schedule Title</label>
                <input
                  type="text"
                  placeholder="e.g. Daily Nightly Snapscore Boost"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="input-field"
                  style={{ width: '100%' }}
                />
              </div>

              {/* Automation Type Tabs */}
              <div>
                <label className="config-form-label">Select Target Automation</label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
                  {[
                    { id: 'snapscore', label: 'Snapscore', icon: Flame, color: '#16a34a' },
                    { id: 'snap', label: 'Snap Send', icon: Send, color: '#0284c7' },
                    { id: 'follow', label: 'Add Friends', icon: UserPlus, color: '#d97706' },
                    { id: 'unfollow', label: 'Remove', icon: UserMinus, color: '#e11d48' },
                  ].map((tab) => {
                    const Icon = tab.icon;
                    const isActive = automationType === tab.id;
                    return (
                      <button
                        key={tab.id}
                        type="button"
                        onClick={() => setAutomationType(tab.id)}
                        className={`preset-chip ${isActive ? 'active' : ''}`}
                        style={{ justifyContent: 'center', padding: '10px 8px', flexDirection: 'column', gap: '4px' }}
                      >
                        <Icon size={18} color={isActive ? '#ffffff' : tab.color} />
                        <span style={{ fontSize: '0.78rem' }}>{tab.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Dynamic Automation Settings */}
              <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#334155', marginBottom: '10px' }}>
                  ⚙️ Automation Parameters
                </div>

                {automationType === 'snapscore' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span style={{ fontSize: '0.82rem', color: '#475569' }}>Cycles Count:</span>
                      <input
                        type="number"
                        min="1"
                        max="50"
                        value={cycles}
                        onChange={(e) => setCycles(e.target.value)}
                        style={{ width: '80px', padding: '6px 10px', borderRadius: '8px', border: '1px solid #cbd5e1' }}
                      />
                    </div>
                    <div>
                      <span style={{ fontSize: '0.82rem', color: '#475569', display: 'block', marginBottom: '6px' }}>Recipient Mode:</span>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        {['count', 'select_all', 'shortcut'].map((m) => (
                          <button
                            key={m}
                            type="button"
                            className={`preset-chip ${boosterMode === m ? 'active' : ''}`}
                            onClick={() => setBoosterMode(m)}
                          >
                            {m === 'count' ? '🔥 Streak Friends' : m === 'select_all' ? '⚡ Select All' : '🤙 Shortcut'}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {automationType === 'snap' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.82rem', color: '#334155', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={randomFilter}
                        onChange={(e) => setRandomFilter(e.target.checked)}
                      />
                      <span>Apply Aesthetic Trending Lens Filter</span>
                    </label>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      {['count', 'select_all', 'shortcut'].map((m) => (
                        <button
                          key={m}
                          type="button"
                          className={`preset-chip ${snapMode === m ? 'active' : ''}`}
                          onClick={() => setSnapMode(m)}
                        >
                          {m === 'count' ? 'Top Friends' : m === 'select_all' ? 'Select All' : 'Shortcut'}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {automationType === 'follow' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        type="button"
                        className={`preset-chip ${followMode === 'quick_add' ? 'active' : ''}`}
                        onClick={() => setFollowMode('quick_add')}
                      >
                        Quick Add Suggestions
                      </button>
                      <button
                        type="button"
                        className={`preset-chip ${followMode === 'search' ? 'active' : ''}`}
                        onClick={() => setFollowMode('search')}
                      >
                        Search Username
                      </button>
                    </div>
                    {followMode === 'quick_add' ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '0.82rem', color: '#475569' }}>Max to Add:</span>
                        <input
                          type="number"
                          min="1"
                          max="20"
                          value={followCount}
                          onChange={(e) => setFollowCount(e.target.value)}
                          style={{ width: '80px', padding: '6px 10px', borderRadius: '8px', border: '1px solid #cbd5e1' }}
                        />
                      </div>
                    ) : (
                      <input
                        type="text"
                        placeholder="Snapchat Username (e.g. john_doe)"
                        value={targetUsername}
                        onChange={(e) => setTargetUsername(e.target.value)}
                        className="input-field"
                        style={{ width: '100%' }}
                      />
                    )}
                  </div>
                )}

                {automationType === 'unfollow' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        type="button"
                        className={`preset-chip ${unfollowFilter === 'no_streak' ? 'active' : ''}`}
                        onClick={() => setUnfollowFilter('no_streak')}
                      >
                        No Streak Friends
                      </button>
                      <button
                        type="button"
                        className={`preset-chip ${unfollowFilter === 'inactive' ? 'active' : ''}`}
                        onClick={() => setUnfollowFilter('inactive')}
                      >
                        Inactive Friends
                      </button>
                    </div>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.82rem', color: '#334155', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={unfollowSelectAll}
                        onChange={(e) => setUnfollowSelectAll(e.target.checked)}
                      />
                      <span>⚡ Remove All Matching Friends (Select All)</span>
                    </label>
                  </div>
                )}
              </div>

              {/* Date & Time Settings */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
                <div>
                  <label className="config-form-label">Scheduled Date</label>
                  <input
                    type="date"
                    value={selectedDate}
                    onChange={(e) => setSelectedDate(e.target.value)}
                    className="input-field"
                    style={{ width: '100%' }}
                    required
                  />
                </div>

                <div>
                  <label className="config-form-label">Start Time</label>
                  <input
                    type="time"
                    value={startTime}
                    onChange={(e) => setStartTime(e.target.value)}
                    className="input-field"
                    style={{ width: '100%' }}
                    required
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
                <div>
                  <label className="config-form-label">Window End Time (Optional)</label>
                  <input
                    type="time"
                    value={endTime}
                    onChange={(e) => setEndTime(e.target.value)}
                    className="input-field"
                    style={{ width: '100%' }}
                    placeholder="e.g. 21:00"
                  />
                </div>

                <div>
                  <label className="config-form-label">Frequency</label>
                  <select
                    value={frequency}
                    onChange={(e) => setFrequency(e.target.value)}
                    className="input-field"
                    style={{ width: '100%' }}
                  >
                    <option value="once">Run Once</option>
                    <option value="daily">Repeat Daily</option>
                  </select>
                </div>
              </div>

              {/* Submit Buttons */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                >
                  <Calendar size={16} />
                  <span>Save Schedule</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

