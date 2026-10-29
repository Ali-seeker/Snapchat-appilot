import React, { useState, useEffect } from 'react';
import { Bell, Flame, CheckCircle, Clock, Trash2, Plus, Sparkles, AlertCircle } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

export default function ReminderDraftView({ contacts }) {
  const [reminders, setReminders] = useState([]);
  const [recipient, setRecipient] = useState('');
  const [time, setTime] = useState('20:00 (Daily)');
  const [draft, setDraft] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const fetchReminders = async () => {
    try {
      const res = await fetch(`${API_BASE}/reminders`);
      if (res.ok) {
        const data = await res.json();
        setReminders(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchReminders();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    if (!recipient.trim()) {
      setErrorMsg('Please select or specify a recipient');
      return;
    }
    if (!draft.trim()) {
      setErrorMsg('Please write a draft caption or checklist task');
      return;
    }

    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/reminders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contact_id: '1',
          recipient_label: recipient.startsWith('@') ? recipient : `@${recipient}`,
          reminder_time: time,
          draft_text: draft
        })
      });
      if (res.ok) {
        const created = await res.json();
        setReminders((prev) => [...prev, created]);
        setDraft('');
      } else {
        setErrorMsg('Failed to save reminder');
      }
    } catch (e) {
      setErrorMsg(e.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggle = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/reminders/${id}/toggle`, { method: 'POST' });
      if (res.ok) {
        const updated = await res.json();
        setReminders((prev) => prev.map((r) => (r.id === id ? updated : r)));
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/reminders/${id}`, { method: 'DELETE' });
      if (res.ok) {
        setReminders((prev) => prev.filter((r) => r.id !== id));
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="glass-panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="panel-header">
        <div className="panel-title">
          <Flame size={18} color="#f59e0b" />
          <span>FR-07 & FR-08: Snapscore Booster & Snap Drafts</span>
        </div>
        <span style={{ fontSize: '0.75rem', color: '#94a3b8', background: 'rgba(245, 158, 11, 0.1)', padding: '2px 8px', borderRadius: '4px' }}>
          Day 2 Core Workflow
        </span>
      </div>

      <div className="panel-body" style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '14px', overflowY: 'auto' }}>
        {/* Policy Safe Disclosure */}
        <div style={{ background: 'rgba(56, 189, 248, 0.08)', border: '1px solid rgba(56, 189, 248, 0.2)', padding: '8px 12px', borderRadius: '6px', fontSize: '0.8rem', color: '#7dd3fc', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sparkles size={14} />
          <span>User-controlled checklist. Prepares intended message reminders without autonomous spamming.</span>
        </div>

        {/* Creation Form */}
        <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <select
              className="input-field"
              style={{ flex: '1 1 140px', background: '#0f172a', color: '#f8fafc' }}
              value={recipient}
              onChange={(e) => setRecipient(e.target.value)}
            >
              <option value="">-- Select Recipient --</option>
              {contacts.map((c) => (
                <option key={c.id} value={c.username}>
                  @{c.username} {c.display_name ? `(${c.display_name})` : ''}
                </option>
              ))}
            </select>

            <input
              className="input-field"
              style={{ flex: '1 1 120px' }}
              placeholder="Time (e.g. 21:00 Daily)"
              value={time}
              onChange={(e) => setTime(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              className="input-field"
              style={{ flex: 1 }}
              placeholder="Draft Snap caption or streak checklist notes..."
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
            />
            <button type="submit" disabled={isLoading} className="btn btn-primary" style={{ padding: '8px 16px' }}>
              <Plus size={15} />
              <span>Add</span>
            </button>
          </div>

          {errorMsg && (
            <div style={{ color: '#f87171', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <AlertCircle size={14} />
              <span>{errorMsg}</span>
            </div>
          )}
        </form>

        {/* Reminders / Drafts List */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px', overflowY: 'auto' }}>
          {reminders.length === 0 ? (
            <div style={{ textAlign: 'center', color: '#64748b', padding: '24px', fontSize: '0.85rem' }}>
              No snapscore booster reminders configured. Create a reminder above.
            </div>
          ) : (
            reminders.map((r) => (
              <div
                key={r.id}
                style={{
                  background: r.is_completed ? 'rgba(34, 197, 94, 0.05)' : 'rgba(15, 23, 42, 0.6)',
                  border: `1px solid ${r.is_completed ? 'rgba(34, 197, 94, 0.3)' : 'var(--border-subtle)'}`,
                  borderRadius: '6px',
                  padding: '10px 12px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '12px'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1 }}>
                  <button
                    onClick={() => handleToggle(r.id)}
                    style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: r.is_completed ? '#22c55e' : '#64748b' }}
                    title={r.is_completed ? 'Mark pending' : 'Mark completed'}
                  >
                    <CheckCircle size={18} />
                  </button>
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontWeight: 600, color: '#f8fafc', fontSize: '0.88rem' }}>{r.recipient_label}</span>
                      <span style={{ fontSize: '0.72rem', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Clock size={12} /> {r.reminder_time}
                      </span>
                    </div>
                    <span style={{ fontSize: '0.82rem', color: r.is_completed ? '#94a3b8' : '#cbd5e1', textDecoration: r.is_completed ? 'line-through' : 'none' }}>
                      {r.draft_text}
                    </span>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span
                    style={{
                      fontSize: '0.7rem',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      background: r.is_completed ? 'rgba(34, 197, 94, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                      color: r.is_completed ? '#4ade80' : '#fbbf24'
                    }}
                  >
                    {r.is_completed ? 'Completed' : 'Needs user action'}
                  </span>
                  <button
                    onClick={() => handleDelete(r.id)}
                    style={{ background: 'transparent', border: 'none', color: '#f87171', cursor: 'pointer', padding: '4px' }}
                    title="Delete reminder"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
