import React, { useState } from 'react';
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
  const [unfollowCount, setUnfollowCount] = useState(2);

  // Score Booster State
  const [boosterCycles, setBoosterCycles] = useState(3);
  const [boosterRecipients, setBoosterRecipients] = useState(5);

  // Auto Snap State
  const [randomLens, setRandomLens] = useState(true);
  const [snapRecipients, setSnapRecipients] = useState(5);

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
      onConfirm('unfollow', {
        filter_type: unfollowFilter,
        days_threshold: unfollowFilter === 'inactive' ? 17 : 0,
        max_unfollow: parseInt(unfollowCount, 10) || 2
      });
    } else if (actionType === 'streak_booster') {
      onConfirm('snapscore', {
        cycles: parseInt(boosterCycles, 10) || 3,
        select_all: true,
        max_recipients: parseInt(boosterRecipients, 10) || 5
      });
    } else if (actionType === 'auto_snap') {
      onConfirm('snap', {
        random_filter: randomLens,
        select_all: true,
        max_recipients: parseInt(snapRecipients, 10) || 5
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
                {actionType === 'streak_booster' && 'Streak Reminders / Snapscore Booster'}
                {actionType === 'auto_snap' && 'Snap Reminders / Auto Snap Dispatch'}
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

        <form onSubmit={handleSubmit}>
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
                    No Streak Friends
                  </button>
                  <button
                    type="button"
                    className={`preset-chip ${unfollowFilter === 'inactive' ? 'active' : ''}`}
                    onClick={() => setUnfollowFilter('inactive')}
                  >
                    Inactive (17+ Days)
                  </button>
                </div>
              </div>

              <div className="config-form-group">
                <label className="config-form-label">Max Friends to Unfollow</label>
                <div className="preset-chip-group">
                  {[2, 5, 10].map((cnt) => (
                    <button
                      key={cnt}
                      type="button"
                      className={`preset-chip ${unfollowCount === cnt ? 'active' : ''}`}
                      onClick={() => setUnfollowCount(cnt)}
                    >
                      {cnt} Contacts
                    </button>
                  ))}
                </div>
              </div>

              <div className="safety-note-box">
                <ShieldCheck size={18} color="#7C3AED" style={{ flexShrink: 0, marginTop: '2px' }} />
                <div>
                  Contacts with active streak flames are strictly safeguarded and will never be unfollowed.
                </div>
              </div>
            </>
          )}

          {/* ================= STREAK BOOSTER CONFIG ================= */}
          {actionType === 'streak_booster' && (
            <>
              <div className="config-form-group">
                <label className="config-form-label">Booster Execution Cycles</label>
                <div className="preset-chip-group">
                  {[1, 3, 5].map((c) => (
                    <button
                      key={c}
                      type="button"
                      className={`preset-chip ${boosterCycles === c ? 'active' : ''}`}
                      onClick={() => setBoosterCycles(c)}
                    >
                      {c} {c === 1 ? 'Cycle' : 'Cycles'}
                    </button>
                  ))}
                </div>
              </div>

              <div className="config-form-group">
                <label className="config-form-label">Recipients per Cycle</label>
                <div className="preset-chip-group">
                  {[5, 10, 15].map((r) => (
                    <button
                      key={r}
                      type="button"
                      className={`preset-chip ${boosterRecipients === r ? 'active' : ''}`}
                      onClick={() => setBoosterRecipients(r)}
                    >
                      Up to {r} Friends
                    </button>
                  ))}
                </div>
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
                <label className="config-form-label">Recipients</label>
                <div className="preset-chip-group">
                  {[3, 5, 10].map((r) => (
                    <button
                      key={r}
                      type="button"
                      className={`preset-chip ${snapRecipients === r ? 'active' : ''}`}
                      onClick={() => setSnapRecipients(r)}
                    >
                      {r} Recipients
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}

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
