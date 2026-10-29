import React, { useState, useEffect } from 'react';
import { Bookmark } from 'lucide-react';
import { createPortal } from 'react-dom';
import {
  UserPlus,
  Trash2,
  Flame,
  Send,
  X,
  Users,
  Search,
  CheckCircle2,
  ShieldCheck,
  Sparkles,
  Info
} from 'lucide-react';

export default function ActionConfigModal({
  isOpen,
  onClose,
  actionType,
  onConfirm
}) {
  if (!isOpen || typeof document === 'undefined') return null;

  // Add Friends State
  const [addMode, setAddMode] = useState('quick_add'); // 'quick_add' | 'target'
  const [friendCount, setFriendCount] = useState(5);
  const [targetUsername, setTargetUsername] = useState('');

  // Remove Friends State
  const [unfollowFilter, setUnfollowFilter] = useState('no_streak');
  const [unfollowCount, setUnfollowCount] = useState(5);
  const [unfollowCustomCount, setUnfollowCustomCount] = useState('');
  const [unfollowSelectAll, setUnfollowSelectAll] = useState(false);
  const [inactiveDays, setInactiveDays] = useState(14);
  const [customInactiveDays, setCustomInactiveDays] = useState('');

  // Shortcuts list
  const [shortcuts, setShortcuts] = useState([]);

  useEffect(() => {
    if (isOpen) {
      fetch('http://localhost:8000/api/shortcuts')
        .then((res) => res.json())
        .then((data) => {
          if (Array.isArray(data)) {
            setShortcuts(data);
            if (data.length > 0) {
              setSnapShortcutEmoji(data[0].emoji);
              setBoosterShortcutEmoji(data[0].emoji);
            }
          }
        })
        .catch(() => {});
    }
  }, [isOpen]);

  // Score Booster State
  const [boosterCycles, setBoosterCycles] = useState(3);
  const [boosterCustomCycles, setBoosterCustomCycles] = useState('');
  const [boosterRecipients, setBoosterRecipients] = useState(5);
  const [boosterMode, setBoosterMode] = useState('count'); // 'count' | 'select_all' | 'shortcut'
  const [boosterShortcutEmoji, setBoosterShortcutEmoji] = useState('🤙');
  const [boosterCustomCount, setBoosterCustomCount] = useState('');

  // Auto Snap State
  const [randomLens, setRandomLens] = useState(true);
  const [snapRecipients, setSnapRecipients] = useState(5);
  const [snapMode, setSnapMode] = useState('count'); // 'count' | 'select_all' | 'shortcut'
  const [snapShortcutEmoji, setSnapShortcutEmoji] = useState('🤙');
  const [snapCustomCount, setSnapCustomCount] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();

    if (actionType === 'add_friends') {
      if (addMode === 'quick_add') {
        onConfirm('follow', {
          mode: 'quick_add',
          max_count: parseInt(friendCount, 10) || 5
        });
      } else {
        const cleanUser = targetUsername.trim().replace(/^@/, '');
        if (!cleanUser) {
          alert('Please enter a valid Snapchat username.');
          return;
        }
        onConfirm('follow', {
          mode: 'search',
          target_ids: [cleanUser],
          max_count: 1
        });
      }
    } else if (actionType === 'remove_friends') {
      const finalDays = customInactiveDays ? (parseInt(customInactiveDays, 10) || 14) : (parseInt(inactiveDays, 10) || 14);
      let count = 5;
      if (unfollowSelectAll) {
        count = 999;
      } else if (unfollowCustomCount) {
        count = parseInt(unfollowCustomCount, 10) || 5;
      } else {
        count = parseInt(unfollowCount, 10) || 5;
      }
      onConfirm('unfollow', {
        filter_type: unfollowFilter,
        days_threshold: unfollowFilter === 'inactive' ? finalDays : 0,
        max_unfollow: count,
        select_all: unfollowSelectAll
      });
    } else if (actionType === 'streak_booster') {
      const rec = boosterCustomCount ? (parseInt(boosterCustomCount, 10) || 5) : (parseInt(boosterRecipients, 10) || 5);
      const finalCycles = boosterCustomCycles ? (parseInt(boosterCustomCycles, 10) || 1) : (parseInt(boosterCycles, 10) || 3);
      onConfirm('snapscore', {
        cycles: Math.max(1, finalCycles),
        recipient_mode: boosterMode,
        shortcut_emoji: boosterMode === 'shortcut' ? (boosterShortcutEmoji || shortcuts[0]?.emoji || '🤙') : null,
        select_all: boosterMode === 'select_all',
        max_recipients: boosterMode === 'select_all' ? 999 : rec
      });
    } else if (actionType === 'auto_snap') {
      const rec = snapCustomCount ? (parseInt(snapCustomCount, 10) || 5) : (parseInt(snapRecipients, 10) || 5);
      onConfirm('snap', {
        random_filter: randomLens,
        recipient_mode: snapMode,
        shortcut_emoji: snapMode === 'shortcut' ? (snapShortcutEmoji || shortcuts[0]?.emoji || '🤙') : null,
        select_all: snapMode === 'select_all',
        max_recipients: snapMode === 'select_all' ? 999 : rec
      });
    }

    onClose();
  };

  return createPortal(
    <div className="modal-backdrop" onClick={onClose}>
      <div className="config-modal-card" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="config-modal-header">
          <div className="config-modal-title">
            <div
              className="config-modal-icon-badge"
              style={{
                background:
                  actionType === 'add_friends' ? '#FEF3C7' :
                    actionType === 'remove_friends' ? '#EDE9FE' :
                      actionType === 'streak_booster' ? '#DCFCE7' : '#E0F2FE'
              }}
            >
              {actionType === 'add_friends' && <UserPlus size={22} color="#D97706" />}
              {actionType === 'remove_friends' && <Trash2 size={22} color="#7C3AED" />}
              {actionType === 'streak_booster' && <Flame size={22} color="#16A34A" />}
              {actionType === 'auto_snap' && <Send size={22} color="#0284C7" />}
            </div>
            <div>
              <h3>
                {actionType === 'add_friends' && 'Add Friends Automation'}
                {actionType === 'remove_friends' && 'Smart Remove Friends'}
                {actionType === 'streak_booster' && 'Snapscore Booster'}
                {actionType === 'auto_snap' && 'Snap Send / Auto Snap Dispatch'}
              </h3>
              <p>
                {actionType === 'add_friends' && 'Configure bulk Quick Add suggestions or search a specific friend.'}
                {actionType === 'remove_friends' && 'Clean up inactive contacts or non-streak followers.'}
                {actionType === 'streak_booster' && 'Automate snap cycles to maintain streaks & grow score.'}
                {actionType === 'auto_snap' && 'Dispatch snaps with optional lens filters on schedule.'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: '6px'
            }}
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
          <div className="config-modal-body">
          {/* ================= ADD FRIENDS CONFIG ================= */}
          {actionType === 'add_friends' && (
            <>
              {/* Mode Switcher */}
              <div className="config-mode-toggle">
                <button
                  type="button"
                  className={`config-mode-btn ${addMode === 'quick_add' ? 'active' : ''}`}
                  onClick={() => setAddMode('quick_add')}
                >
                  <Users size={16} />
                  <span>Bulk Quick Add</span>
                </button>
                <button
                  type="button"
                  className={`config-mode-btn ${addMode === 'target' ? 'active' : ''}`}
                  onClick={() => setAddMode('target')}
                >
                  <Search size={16} />
                  <span>Target Friend</span>
                </button>
              </div>

              {/* Sub-form: Bulk Quick Add */}
              {addMode === 'quick_add' && (
                <div className="config-form-group">
                  <label className="config-form-label">
                    Number of Friends to Add
                  </label>
                  <div className="preset-chip-group">
                    {[3, 5, 10, 15].map((cnt) => (
                      <button
                        key={cnt}
                        type="button"
                        className={`preset-chip ${friendCount === cnt ? 'active' : ''}`}
                        onClick={() => setFriendCount(cnt)}
                      >
                        {cnt} Friends
                      </button>
                    ))}
                  </div>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={friendCount}
                    onChange={(e) => setFriendCount(Math.max(1, Math.min(20, parseInt(e.target.value, 10) || 1)))}
                    className="config-input-styled"
                    placeholder="Custom count (1 - 20)"
                  />
                  <div className="safety-note-box" style={{ marginTop: '12px' }}>
                    <ShieldCheck size={18} color="#7C3AED" style={{ flexShrink: 0, marginTop: '2px' }} />
                    <div>
                      <strong>Snapchat v14.29 Safety Profile:</strong> Recommended 3-10 additions per session with organic human touch jitter to prevent algorithmic throttling.
                    </div>
                  </div>
                </div>
              )}

              {/* Sub-form: Target Friend Search */}
              {addMode === 'target' && (
                <div className="config-form-group">
                  <label className="config-form-label">
                    Snapchat Target Username
                  </label>
                  <div style={{ position: 'relative' }}>
                    <span
                      style={{
                        position: 'absolute',
                        left: '14px',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        color: '#94a3b8',
                        fontWeight: 600
                      }}
                    >
                      @
                    </span>
                    <input
                      type="text"
                      value={targetUsername}
                      onChange={(e) => setTargetUsername(e.target.value)}
                      placeholder="username (e.g. alex_smith)"
                      className="config-input-styled"
                      style={{ paddingLeft: '32px' }}
                      autoFocus
                    />
                  </div>
                  <div className="safety-note-box" style={{ marginTop: '12px' }}>
                    <Info size={18} color="#7C3AED" style={{ flexShrink: 0, marginTop: '2px' }} />
                    <div>
                      Appilot will open Snapchat's search bar, type <strong>@{targetUsername.trim() || 'username'}</strong>, inspect the result card, and tap the Add Friend button.
                    </div>
                  </div>
                </div>
              )}
            </>
          )}

          {/* ================= REMOVE FRIENDS CONFIG ================= */}
          {actionType === 'remove_friends' && (
            <>
              <div className="config-form-group">
                <label className="config-form-label">Filter Criteria</label>
                <div className="preset-chip-group">
                  <button
                    type="button"
                    className={`preset-chip ${unfollowFilter === 'no_streak' ? 'active' : ''}`}
                    onClick={() => setUnfollowFilter('no_streak')}
                  >
                    🔥 No Streak Friends
                  </button>
                  <button
                    type="button"
                    className={`preset-chip ${unfollowFilter === 'inactive' ? 'active' : ''}`}
                    onClick={() => setUnfollowFilter('inactive')}
                  >
                    ⏳ Inactive Friends ({customInactiveDays || inactiveDays}+ Days)
                  </button>
                </div>

                {unfollowFilter === 'inactive' && (
                  <div style={{ background: '#f8fafc', padding: '12px 14px', borderRadius: '10px', border: '1px solid #e2e8f0', marginTop: '10px' }}>
                    <label className="config-form-label" style={{ fontSize: '0.8rem', color: '#475569', marginBottom: '6px' }}>
                      Inactivity Days Threshold
                    </label>
                    <div className="preset-chip-group" style={{ marginBottom: '8px' }}>
                      {[7, 14, 30, 60].map((d) => (
                        <button
                          key={d}
                          type="button"
                          className={`preset-chip ${!customInactiveDays && inactiveDays === d ? 'active' : ''}`}
                          onClick={() => {
                            setInactiveDays(d);
                            setCustomInactiveDays('');
                          }}
                        >
                          {d} Days
                        </button>
                      ))}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '0.8rem', color: '#64748b' }}>Custom days:</span>
                      <input
                        type="number"
                        min="1"
                        max="365"
                        placeholder="e.g. 17"
                        value={customInactiveDays}
                        onChange={(e) => setCustomInactiveDays(e.target.value)}
                        style={{ width: '80px', padding: '6px 10px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.82rem' }}
                      />
                      <span style={{ fontSize: '0.78rem', color: '#64748b' }}>days inactive</span>
                    </div>
                  </div>
                )}
              </div>

              <div className="config-form-group">
                <label className="config-form-label">Max Friends to Unfollow</label>
                <div className="preset-chip-group" style={{ marginBottom: '8px' }}>
                  {[3, 5, 10].map((cnt) => (
                    <button
                      key={cnt}
                      type="button"
                      className={`preset-chip ${!unfollowSelectAll && !unfollowCustomCount && unfollowCount === cnt ? 'active' : ''}`}
                      onClick={() => {
                        setUnfollowCount(cnt);
                        setUnfollowSelectAll(false);
                        setUnfollowCustomCount('');
                      }}
                    >
                      {cnt} Contacts
                    </button>
                  ))}
                  <button
                    type="button"
                    className={`preset-chip ${unfollowSelectAll ? 'active' : ''}`}
                    onClick={() => {
                      setUnfollowSelectAll(true);
                      setUnfollowCustomCount('');
                    }}
                    style={{
                      background: unfollowSelectAll ? '#fee2e2' : undefined,
                      borderColor: unfollowSelectAll ? '#ef4444' : undefined,
                      color: unfollowSelectAll ? '#b91c1c' : undefined,
                      fontWeight: 600
                    }}
                  >
                    ⚡ All Eligible Friends
                  </button>
                </div>
                {!unfollowSelectAll && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '0.8rem', color: '#64748b' }}>Custom count:</span>
                    <input
                      type="number"
                      min="1"
                      max="500"
                      placeholder="e.g. 7"
                      value={unfollowCustomCount}
                      onChange={(e) => {
                        setUnfollowCustomCount(e.target.value);
                        setUnfollowSelectAll(false);
                      }}
                      style={{ width: '80px', padding: '6px 10px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.82rem' }}
                    />
                  </div>
                )}
              </div>

              <div className="safety-note-box">
                <ShieldCheck size={18} color="#7C3AED" style={{ flexShrink: 0, marginTop: '2px' }} />
                <div>
                  Contacts with active streak flames (🔥) are strictly safeguarded and will never be unfollowed.
                </div>
              </div>
            </>
          )}

          {/* ================= STREAK BOOSTER CONFIG ================= */}
          {actionType === 'streak_booster' && (
            <>
              <div className="config-form-group">
                <label className="config-form-label">Booster Execution Cycles</label>
                <div className="preset-chip-group" style={{ marginBottom: '8px' }}>
                  {[1, 2, 3, 5, 10].map((c) => (
                    <button
                      key={c}
                      type="button"
                      className={`preset-chip ${!boosterCustomCycles && boosterCycles === c ? 'active' : ''}`}
                      onClick={() => {
                        setBoosterCycles(c);
                        setBoosterCustomCycles('');
                      }}
                    >
                      {c} {c === 1 ? 'Cycle' : 'Cycles'}
                    </button>
                  ))}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '0.8rem', color: '#64748b' }}>Custom cycles:</span>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    placeholder="e.g. 7"
                    value={boosterCustomCycles}
                    onChange={(e) => {
                      setBoosterCustomCycles(e.target.value);
                      if (e.target.value) {
                        setBoosterCycles(parseInt(e.target.value, 10) || 1);
                      }
                    }}
                    style={{ width: '80px', padding: '6px 10px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.82rem' }}
                  />
                  {boosterCustomCycles && (
                    <span style={{ fontSize: '0.78rem', color: '#16a34a', fontWeight: 600 }}>
                      ⚡ {boosterCustomCycles} {parseInt(boosterCustomCycles, 10) === 1 ? 'cycle' : 'cycles'} targeted
                    </span>
                  )}
                </div>
              </div>

              <div className="config-form-group">
                <label className="config-form-label">Recipient Mode per Cycle</label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginBottom: '10px' }}>
                  <button
                    type="button"
                    className={`preset-chip ${boosterMode === 'count' ? 'active' : ''}`}
                    onClick={() => setBoosterMode('count')}
                    style={{ justifyContent: 'center' }}
                  >
                    🔥 Streak Friends
                  </button>
                  <button
                    type="button"
                    className={`preset-chip ${boosterMode === 'select_all' ? 'active' : ''}`}
                    onClick={() => setBoosterMode('select_all')}
                    style={{ justifyContent: 'center' }}
                  >
                    ⚡ Select All
                  </button>
                  <button
                    type="button"
                    className={`preset-chip ${boosterMode === 'shortcut' ? 'active' : ''}`}
                    onClick={() => setBoosterMode('shortcut')}
                    style={{ justifyContent: 'center' }}
                  >
                    🤙 Shortcut
                  </button>
                </div>

                {boosterMode === 'count' && (
                  <div>
                    <div className="preset-chip-group" style={{ marginBottom: '8px' }}>
                      {[5, 10, 15].map((r) => (
                        <button
                          key={r}
                          type="button"
                          className={`preset-chip ${!boosterCustomCount && boosterRecipients === r ? 'active' : ''}`}
                          onClick={() => {
                            setBoosterRecipients(r);
                            setBoosterCustomCount('');
                          }}
                        >
                          Up to {r} Friends
                        </button>
                      ))}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '0.8rem', color: '#64748b' }}>Custom count:</span>
                      <input
                        type="number"
                        min="1"
                        max="50"
                        placeholder="e.g. 8"
                        value={boosterCustomCount}
                        onChange={(e) => setBoosterCustomCount(e.target.value)}
                        style={{ width: '80px', padding: '6px 10px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.82rem' }}
                      />
                    </div>
                    <div style={{ fontSize: '0.76rem', color: '#64748b', marginTop: '8px', display: 'flex', alignItems: 'center', gap: '5px' }}>
                      <Info size={13} color="#0284c7" />
                      <span>Dispatches to contacts on the Send To screen who have an active <strong>🔥 Streak</strong>.</span>
                    </div>
                  </div>
                )}

                {boosterMode === 'select_all' && (
                  <div style={{ padding: '10px 14px', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '10px', fontSize: '0.82rem', color: '#166534' }}>
                    ⚡ Dispatches each cycle by tapping <strong>'Select All'</strong> on the Send To screen.
                  </div>
                )}

                {boosterMode === 'shortcut' && (
                  <div>
                    <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '8px' }}>
                      Select the shortcut matching your phone app:
                    </div>
                    {shortcuts.length === 0 ? (
                      <div style={{ padding: '8px 12px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', fontSize: '0.8rem', color: '#b91c1c' }}>
                        No shortcuts configured. Add one in Snap Shortcuts tab!
                      </div>
                    ) : (
                      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                        {shortcuts.map((sc) => (
                          <button
                            key={sc.id}
                            type="button"
                            className={`preset-chip ${boosterShortcutEmoji === sc.emoji ? 'active' : ''}`}
                            onClick={() => setBoosterShortcutEmoji(sc.emoji)}
                            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                          >
                            <span style={{ fontSize: '1.2rem' }}>{sc.emoji}</span>
                            <span>{sc.name}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="safety-note-box">
                <Flame size={18} color="#16A34A" style={{ flexShrink: 0, marginTop: '2px' }} />
                <div>
                  Each cycle captures a fresh camera snap, selects top streak recipients, and dispatches with 15s cooldown pacing.
                </div>
              </div>
            </>
          )}

          {/* ================= AUTO SNAP CONFIG ================= */}
          {actionType === 'auto_snap' && (
            <>
              <div className="config-form-group">
                <label className="config-form-label">Filter &amp; Lens Selection</label>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '12px 14px',
                    background: '#f8fafc',
                    borderRadius: '12px',
                    border: '1px solid #e2e8f0',
                    cursor: 'pointer'
                  }}
                  onClick={() => setRandomLens(!randomLens)}
                >
                  <input
                    type="checkbox"
                    checked={randomLens}
                    onChange={(e) => setRandomLens(e.target.checked)}
                    style={{ width: '18px', height: '18px', cursor: 'pointer', accentColor: 'var(--primary)' }}
                  />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '0.88rem', fontWeight: 600, color: '#0f172a' }}>
                      Apply Aesthetic Lens Carousel
                    </div>
                    <div style={{ fontSize: '0.78rem', color: '#64748b' }}>
                      Picks a trending face lens before taking snap
                    </div>
                  </div>
                  <Sparkles size={18} color="#0284c7" />
                </div>
              </div>

              <div className="config-form-group">
                <label className="config-form-label">Recipient Selection</label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginBottom: '10px' }}>
                  <button
                    type="button"
                    className={`preset-chip ${snapMode === 'count' ? 'active' : ''}`}
                    onClick={() => setSnapMode('count')}
                    style={{ justifyContent: 'center' }}
                  >
                    🔥 Streak Friends
                  </button>
                  <button
                    type="button"
                    className={`preset-chip ${snapMode === 'select_all' ? 'active' : ''}`}
                    onClick={() => setSnapMode('select_all')}
                    style={{ justifyContent: 'center' }}
                  >
                    ⚡ Select All
                  </button>
                  <button
                    type="button"
                    className={`preset-chip ${snapMode === 'shortcut' ? 'active' : ''}`}
                    onClick={() => setSnapMode('shortcut')}
                    style={{ justifyContent: 'center' }}
                  >
                    🤙 Shortcut
                  </button>
                </div>

                {snapMode === 'count' && (
                  <div>
                    <div className="preset-chip-group" style={{ marginBottom: '8px' }}>
                      {[3, 5, 10].map((r) => (
                        <button
                          key={r}
                          type="button"
                          className={`preset-chip ${!snapCustomCount && snapRecipients === r ? 'active' : ''}`}
                          onClick={() => {
                            setSnapRecipients(r);
                            setSnapCustomCount('');
                          }}
                        >
                          {r} Friends
                        </button>
                      ))}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '0.8rem', color: '#64748b' }}>Custom count:</span>
                      <input
                        type="number"
                        min="1"
                        max="50"
                        placeholder="e.g. 7"
                        value={snapCustomCount}
                        onChange={(e) => setSnapCustomCount(e.target.value)}
                        style={{ width: '80px', padding: '6px 10px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.82rem' }}
                      />
                    </div>
                    <div style={{ fontSize: '0.76rem', color: '#64748b', marginTop: '8px', display: 'flex', alignItems: 'center', gap: '5px' }}>
                      <Info size={13} color="#0284c7" />
                      <span>Dispatches to contacts on the Send To screen who have an active <strong>🔥 Streak</strong>.</span>
                    </div>
                  </div>
                )}

                {snapMode === 'select_all' && (
                  <div style={{ padding: '10px 14px', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '10px', fontSize: '0.82rem', color: '#166534' }}>
                    ⚡ Taps the <strong>'Select All'</strong> button on your Send To screen to select all friends at once!
                  </div>
                )}

                {snapMode === 'shortcut' && (
                  <div>
                    <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '8px' }}>
                      Choose your phone shortcut emoji:
                    </div>
                    {shortcuts.length === 0 ? (
                      <div style={{ padding: '8px 12px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', fontSize: '0.8rem', color: '#b91c1c' }}>
                        No shortcuts configured yet. Add one in Snap Shortcuts tab!
                      </div>
                    ) : (
                      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                        {shortcuts.map((sc) => (
                          <button
                            key={sc.id}
                            type="button"
                            className={`preset-chip ${snapShortcutEmoji === sc.emoji ? 'active' : ''}`}
                            onClick={() => setSnapShortcutEmoji(sc.emoji)}
                            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                          >
                            <span style={{ fontSize: '1.2rem' }}>{sc.emoji}</span>
                            <span>{sc.name}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </>
          )}

          </div>

          {/* Modal Footer Actions */}
          <div className="config-modal-footer">
            <button
              type="button"
              className="btn-secondary"
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
            >
              <CheckCircle2 size={16} />
              <span>
                {actionType === 'add_friends' && 'Start Adding Friends ➔'}
                {actionType === 'remove_friends' && 'Start Safe Unfollow ➔'}
                {actionType === 'streak_booster' && 'Launch Score Booster ➔'}
                {actionType === 'auto_snap' && 'Dispatch Snaps ➔'}
              </span>
            </button>
          </div>
        </form>
      </div>
    </div>,
    document.body
  );
}
