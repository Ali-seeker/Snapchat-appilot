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
  ShieldCheck,
  Zap,
  X,
  RotateCw
} from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

export default function ScheduleView({ onTriggerWorkflow }) {
  const [schedules, setSchedules] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [deviceConnected, setDeviceConnected] = useState(true);
  const [shortcuts, setShortcuts] = useState([]);
  const [filterTab, setFilterTab] = useState('all'); // all | active | paused

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
    } catch (e) { }
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
      title: title.trim() || `Scheduled ${automationType === 'snapscore' ? 'Snapscore Booster' : automationType === 'snap' ? 'Snap Send' : automationType === 'follow' ? 'Add Friends' : 'Remove Friends'}`,
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
      } else {
        alert('Failed to save schedule');
      }
    } catch (e) {
      alert('Network error saving schedule');
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to remove this scheduled automation?')) return;
    try {
      const res = await fetch(`${API_BASE}/schedules/${id}`, { method: 'DELETE' });
      if (res.ok) {
        setSchedules((prev) => prev.filter((s) => s.id !== id));
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleToggle = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/schedules/${id}/toggle`, { method: 'POST' });
      if (res.ok) {
        const updated = await res.json();
        setSchedules((prev) => prev.map((s) => (s.id === id ? updated : s)));
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleRunNow = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/schedules/${id}/run_now`, { method: 'POST' });
      const data = await res.json();
      if (res.ok) {
        alert(`Schedule '${data.title}' triggered immediately on your connected device!`);
        fetchSchedules();
      }
    } catch (e) {
      alert('Could not trigger schedule run.');
    }
  };

  const activeCount = schedules.filter(s => s.is_active).length;
  const pausedCount = schedules.filter(s => !s.is_active).length;
  const offlineWarnings = schedules.filter(s => s.last_status === 'DEVICE_OFFLINE').length;

  const displayedSchedules = schedules.filter((item) => {
    if (filterTab === 'active') return item.is_active;
    if (filterTab === 'paused') return !item.is_active;
    return true;
  });

  return (
    <div className="page-container">
      {/* 4 KPI Metric Cards */}
      <div className="kpi-grid" style={{ marginBottom: '20px' }}>
        {/* 1. Active Schedules */}
        <div className="kpi-card">
          <div className="kpi-icon-wrap purple">
            <Calendar size={22} />
          </div>
          <div className="kpi-info">
            <span className="kpi-label">Active Schedules</span>
            <span className="kpi-value">{activeCount} Configured</span>
            <span className="kpi-sub">Monitored in background</span>
          </div>
        </div>

        {/* 2. Connected Device */}
        <div className="kpi-card">
          <div className={`kpi-icon-wrap ${deviceConnected ? 'green' : 'pink'}`}>
            {deviceConnected ? <SmartphoneCharging size={22} /> : <Smartphone size={22} />}
          </div>
          <div className="kpi-info">
            <span className="kpi-label">Phone Connectivity</span>
            <span className="kpi-value" style={{ color: deviceConnected ? '#16a34a' : '#ea580c' }}>
              {deviceConnected ? 'Connected' : 'Offline'}
            </span>
            <span className="kpi-sub">
              {deviceConnected ? 'Ready for auto dispatch' : 'Reconnect via USB debugging'}
            </span>
          </div>
        </div>

        {/* 3. Offline Safeguard */}
        <div className="kpi-card">
          <div className="kpi-icon-wrap blue">
            <ShieldCheck size={22} />
          </div>
          <div className="kpi-info">
            <span className="kpi-label">Offline Safeguard</span>
            <span className="kpi-value" style={{ color: offlineWarnings > 0 ? '#dc2626' : '#0284c7' }}>
              {offlineWarnings > 0 ? `${offlineWarnings} Handled` : '100% Protected'}
            </span>
            <span className="kpi-sub">No crash if phone offline</span>
          </div>
        </div>

        {/* 4. Scheduler Engine */}
        <div className="kpi-card">
          <div className="kpi-icon-wrap green">
            <Zap size={22} />
          </div>
          <div className="kpi-info">
            <span className="kpi-label">Scheduler Daemon</span>
            <span className="kpi-value">Active</span>
            <span className="kpi-sub">Checks schedule every 15s</span>
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
          background: 'linear-gradient(135deg, rgba(2, 132, 199, 0.04) 0%, rgba(124, 58, 237, 0.04) 100%)',
          border: '1px solid #bae6fd',
          borderRadius: '12px',
          padding: '12px 16px',
          marginBottom: '18px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <ShieldCheck size={20} color="#0284c7" style={{ flexShrink: 0 }} />
          <div style={{ fontSize: '0.84rem', color: '#334155', lineHeight: '1.45' }}>
            <strong>Device Offline Protection:</strong> If your mobile phone is disconnected when a schedule is due, Appilot safely halts execution, marks the event as <code>DEVICE_OFFLINE</code>, and alerts you without misclicking or throwing errors.
          </div>
        </div>

        {/* Filter Pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          {[
            { id: 'all', label: `All Schedules (${schedules.length})` },
            { id: 'active', label: `Active (${activeCount})` },
            { id: 'paused', label: `Paused (${pausedCount})` }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilterTab(tab.id)}
              style={{
                border: 'none',
                background: filterTab === tab.id ? '#7c3aed' : '#f1f5f9',
                color: filterTab === tab.id ? '#ffffff' : '#475569',
                padding: '6px 14px',
                borderRadius: '999px',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Schedules Cards Grid */}
        {displayedSchedules.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '48px 24px', color: '#64748b' }}>
            <Calendar size={48} style={{ opacity: 0.3, margin: '0 auto 12px' }} />
            <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: '#0f172a', marginBottom: '4px' }}>
              {filterTab === 'all' ? 'No Schedules Configured' : `No ${filterTab} schedules found`}
            </h4>
            <p style={{ fontSize: '0.86rem', marginBottom: '16px' }}>
              Click the <strong>'Create New Schedule'</strong> button above to automate tasks on your calendar.
            </p>
            <button className="btn-primary" onClick={() => setShowModal(true)}>
              <Plus size={16} />
              <span>Create Schedule</span>
            </button>
          </div>
        ) : (
          <div className="schedule-cards-grid">
            {displayedSchedules.map((item) => {
              const isBooster = item.automation_type === 'snapscore';
              const isSnap = item.automation_type === 'snap';
              const isFollow = item.automation_type === 'follow';
              const isUnfollow = item.automation_type === 'unfollow';

              const typeKey = isBooster ? 'booster' : isSnap ? 'snap' : isFollow ? 'follow' : 'unfollow';
              const typeLabel = isBooster ? 'Snapscore Booster' : isSnap ? 'Snap Send' : isFollow ? 'Add Friends' : 'Remove Friends';

              return (
                <div
                  key={item.id}
                  className={`schedule-card ${!item.is_active ? 'paused' : ''}`}
                >
                  <div>
                    {/* Top Header */}
                    <div className="schedule-card-top">
                      <div className="schedule-card-identity">
                        <div className={`schedule-icon-avatar ${typeKey}`}>
                          {isBooster && <Flame size={22} />}
                          {isSnap && <Send size={22} />}
                          {isFollow && <UserPlus size={22} />}
                          {isUnfollow && <UserMinus size={22} />}
                        </div>
                        <div>
                          <h4 className="schedule-card-title">{item.title}</h4>
                          <span className={`schedule-type-chip ${typeKey}`}>
                            {typeLabel}
                          </span>
                        </div>
                      </div>

                      {/* Active/Pause Switch */}
                      <label className="switch" title={item.is_active ? 'Active' : 'Paused'}>
                        <input
                          type="checkbox"
                          checked={item.is_active}
                          onChange={() => handleToggle(item.id)}
                        />
                        <span className="slider"></span>
                      </label>
                    </div>

                    {/* Time & Date Box */}
                    <div className="schedule-timing-box">
                      <div className="schedule-timing-item">
                        <Calendar size={14} color="#64748b" />
                        <span>Date: <strong>{item.date}</strong></span>
                      </div>
                      <div className="schedule-timing-item">
                        <Clock size={14} color="#64748b" />
                        <span>Time: <strong>{item.start_time}</strong> {item.end_time ? `➔ ${item.end_time}` : ''}</span>
                        <span style={{
                          marginLeft: 'auto',
                          fontSize: '0.72rem',
                          padding: '2px 8px',
                          background: item.frequency === 'daily' ? '#f3e8ff' : '#f1f5f9',
                          color: item.frequency === 'daily' ? '#7c3aed' : '#475569',
                          borderRadius: '6px',
                          fontWeight: 600
                        }}>
                          {item.frequency === 'daily' ? '🔁 Daily Repeat' : '⚡ Run Once'}
                        </span>
                      </div>
                    </div>

                    {/* Configured Routine Parameters */}
                    <div className="schedule-params-pillbox">
                      {isBooster && (
                        <span>⚡ <strong>{item.params?.cycles || 3} Cycles</strong> • Target: {item.params?.recipient_mode === 'shortcut' ? `Shortcut (${item.params?.shortcut_emoji || '🤙'})` : item.params?.recipient_mode === 'select_all' ? 'Select All' : 'Streak Friends'}</span>
                      )}
                      {isSnap && (
                        <span>📸 <strong>Filter:</strong> {item.params?.random_filter ? 'Aesthetic Lens' : 'None'} • Mode: {item.params?.recipient_mode?.toUpperCase()}</span>
                      )}
                      {isFollow && (
                        <span>👥 <strong>{item.params?.mode === 'search' ? `Target @${item.params?.target_ids?.[0]}` : `Quick Add (${item.params?.max_count || 5})`}</strong></span>
                      )}
                      {isUnfollow && (
                        <span>🗑️ <strong>Filter:</strong> {item.params?.filter_type} • Limit: {item.params?.select_all ? 'ALL' : item.params?.max_unfollow}</span>
                      )}
                    </div>
                  </div>

                  {/* Card Footer: Status & Actions */}
                  <div className="schedule-card-footer">
                    <div>
                      {item.last_status === 'DEVICE_OFFLINE' && (
                        <span className="schedule-status-badge offline" title={item.last_error || 'Mobile phone was disconnected'}>
                          <AlertTriangle size={12} /> Phone Offline
                        </span>
                      )}
                      {item.last_status === 'COMPLETED' && (
                        <span className="schedule-status-badge completed">
                          <CheckCircle2 size={12} /> Success
                        </span>
                      )}
                      {item.last_status === 'RUNNING' && (
                        <span className="schedule-status-badge running">
                          <RefreshCw size={12} className="spin" /> Running
                        </span>
                      )}
                      {(!item.last_status || item.last_status === 'PENDING') && (
                        <span className="schedule-status-badge pending">
                          <Clock size={12} /> Pending
                        </span>
                      )}
                    </div>

                    <div className="schedule-action-group">
                      <button
                        className="btn-schedule-run"
                        onClick={() => handleRunNow(item.id)}
                        title="Trigger this schedule immediately on connected phone"
                      >
                        <Play size={13} fill="#16a34a" />
                        <span>Run Now</span>
                      </button>

                      <button
                        className="btn-schedule-delete"
                        onClick={() => handleDelete(item.id)}
                        title="Delete Schedule"
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
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
                <p style={{ fontSize: '0.82rem', color: '#64748b' }}>Configure routine parameters, date, and execution timing.</p>
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
                      <span style={{ fontSize: '0.82rem', color: '#475569' }}>Booster Cycles:</span>
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
                    {boosterMode === 'shortcut' && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                        <span style={{ fontSize: '0.82rem', color: '#475569' }}>Shortcut Emoji:</span>
                        {shortcuts.length > 0 ? (
                          <div style={{ display: 'flex', gap: '6px' }}>
                            {shortcuts.map((sc) => (
                              <button
                                key={sc.id}
                                type="button"
                                onClick={() => setShortcutEmoji(sc.emoji)}
                                className={`preset-chip ${shortcutEmoji === sc.emoji ? 'active' : ''}`}
                                style={{ padding: '4px 10px' }}
                              >
                                {sc.emoji} {sc.name}
                              </button>
                            ))}
                          </div>
                        ) : (
                          <input
                            type="text"
                            value={shortcutEmoji}
                            onChange={(e) => setShortcutEmoji(e.target.value)}
                            style={{ width: '60px', padding: '4px 8px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                          />
                        )}
                      </div>
                    )}
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
                    {unfollowFilter === 'inactive' && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '0.82rem', color: '#475569' }}>Inactive Days Threshold:</span>
                        <input
                          type="number"
                          min="1"
                          max="365"
                          value={unfollowDays}
                          onChange={(e) => setUnfollowDays(e.target.value)}
                          style={{ width: '80px', padding: '6px 10px', borderRadius: '8px', border: '1px solid #cbd5e1' }}
                        />
                      </div>
                    )}
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
