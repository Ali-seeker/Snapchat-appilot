import React, { useState, useEffect } from 'react';
import {
  Bookmark,
  Plus,
  Trash2,
  Sparkles,
  Send,
  Info,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import EmojiKeyboard from './EmojiKeyboard';

const API_BASE = 'http://localhost:8000/api';

export default function ShortcutsManagerView({ onTriggerWorkflow }) {
  const [shortcuts, setShortcuts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [shortcutName, setShortcutName] = useState('');
  const [selectedEmoji, setSelectedEmoji] = useState('🤙');
  const [errorMsg, setErrorMsg] = useState('');

  const fetchShortcuts = async () => {
    try {
      const res = await fetch(`${API_BASE}/shortcuts`);
      if (res.ok) {
        const data = await res.json();
        setShortcuts(data);
      }
    } catch (e) {
      console.error('Failed to load shortcuts:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchShortcuts();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!shortcutName.trim()) {
      setErrorMsg('Please enter a shortcut name.');
      return;
    }
    if (!selectedEmoji.trim()) {
      setErrorMsg('Please select an emoji.');
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/shortcuts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: shortcutName.trim(),
          emoji: selectedEmoji.trim()
        })
      });

      if (res.ok) {
        setShowAddModal(false);
        setShortcutName('');
        setSelectedEmoji('🤙');
        setErrorMsg('');
        fetchShortcuts();
      } else {
        setErrorMsg('Failed to save shortcut');
      }
    } catch (err) {
      setErrorMsg('Network error saving shortcut');
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to remove this shortcut?')) return;
    try {
      const res = await fetch(`${API_BASE}/shortcuts/${id}`, { method: 'DELETE' });
      if (res.ok) {
        setShortcuts((prev) => prev.filter((s) => s.id !== id));
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleQuickDispatch = (shortcut) => {
    if (onTriggerWorkflow) {
      onTriggerWorkflow('snap', {
        random_filter: true,
        recipient_mode: 'shortcut',
        shortcut_emoji: shortcut.emoji
      });
    }
  };

  return (
    <div className="page-container">
      {/* Top Banner */}
      <div className="white-panel" style={{ marginBottom: '20px' }}>
        <div className="panel-header-row">
          <div className="panel-header-title">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '1.4rem' }}>📑</span>
              <h3 style={{ margin: 0 }}>Snapchat Shortcuts Manager</h3>
            </div>
            <p>
              Configure the exact emojis you created on your Snapchat phone app to enable instant 1-tap shortcut dispatches.
            </p>
          </div>

          <button
            className="btn-primary"
            onClick={() => {
              setErrorMsg('');
              setShowAddModal(true);
            }}
          >
            <Plus size={16} />
            <span>Add Shortcut</span>
          </button>
        </div>

        {/* How Shortcuts Work Info Box */}
        <div style={{
          display: 'flex',
          gap: '12px',
          alignItems: 'flex-start',
          background: 'linear-gradient(135deg, rgba(2, 132, 199, 0.05) 0%, rgba(124, 58, 237, 0.05) 100%)',
          border: '1px solid #bae6fd',
          borderRadius: '12px',
          padding: '14px 16px',
          marginTop: '10px'
        }}>
          <Info size={18} style={{ color: '#0284c7', flexShrink: 0, marginTop: '2px' }} />
          <div style={{ fontSize: '0.82rem', color: '#334155', lineHeight: '1.5' }}>
            <strong>How Snapchat Shortcuts Work:</strong> On your mobile phone, open Snapchat &gt; Take Snap &gt; Send To &gt; tap the '+' icon under the search bar to create a shortcut with an emoji. Then add that same emoji here in Appilot. When automation runs, Appilot taps that emoji tab, hits the shortcut's "Select All" button, and sends your Snap!
          </div>
        </div>
      </div>

      {/* Shortcuts List */}
      <div className="white-panel">
        <h4 style={{ fontSize: '1rem', fontWeight: 600, color: '#0f172a', marginBottom: '14px' }}>
          Configured Shortcuts ({shortcuts.length})
        </h4>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '30px', color: '#94a3b8' }}>Loading shortcuts...</div>
        ) : shortcuts.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 20px', color: '#64748b' }}>
            <Bookmark size={40} style={{ color: '#cbd5e1', marginBottom: '10px' }} />
            <p style={{ fontWeight: 600, margin: '0 0 6px 0' }}>No Shortcuts Added Yet</p>
            <p style={{ fontSize: '0.84rem', margin: 0 }}>
              Add the emoji of the shortcut you created on your phone to unlock automated shortcut sending.
            </p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '14px' }}>
            {shortcuts.map((sc) => (
              <div
                key={sc.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '16px 18px',
                  borderRadius: '14px',
                  border: '1px solid #e2e8f0',
                  background: '#ffffff',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                  transition: 'all 0.15s ease'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                  <div style={{
                    width: '50px',
                    height: '50px',
                    borderRadius: '14px',
                    background: '#f8fafc',
                    border: '1.5px solid #e2e8f0',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1.8rem',
                    boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.02)'
                  }}>
                    {sc.emoji}
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.96rem', color: '#0f172a' }}>
                      {sc.name}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', color: '#16a34a', marginTop: '3px' }}>
                      <CheckCircle2 size={13} />
                      <span>Mapped to Phone Bar ({sc.emoji})</span>
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <button
                    className="btn-primary"
                    style={{ padding: '6px 12px', fontSize: '0.78rem' }}
                    onClick={() => handleQuickDispatch(sc)}
                    title="Send a snap to this shortcut right now"
                  >
                    <Send size={13} />
                    <span>Send</span>
                  </button>

                  <button
                    className="icon-btn"
                    style={{ color: '#ef4444', width: '32px', height: '32px' }}
                    onClick={() => handleDelete(sc.id)}
                    title="Delete shortcut"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Shortcut Modal */}
      {showAddModal && (
        <div className="modal-backdrop" onClick={() => setShowAddModal(false)}>
          <div
            className="config-modal-card"
            style={{ maxWidth: '480px', maxHeight: 'calc(100vh - 40px)' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="config-modal-header">
              <div className="config-modal-title">
                <Bookmark size={20} color="#0284c7" />
                <h3 style={{ margin: 0, fontSize: '1.15rem' }}>Add Snapchat Shortcut</h3>
              </div>
              <button
                type="button"
                className="config-modal-close"
                onClick={() => setShowAddModal(false)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#94a3b8',
                  cursor: 'pointer',
                  padding: '6px'
                }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
              <div className="config-modal-body" style={{ flex: 1, overflowY: 'auto', paddingRight: '4px' }}>
                {errorMsg && (
                  <div style={{
                    padding: '8px 12px',
                    background: '#fef2f2',
                    border: '1px solid #fecaca',
                    borderRadius: '8px',
                    color: '#b91c1c',
                    fontSize: '0.82rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    marginBottom: '10px'
                  }}>
                    <AlertCircle size={15} />
                    <span>{errorMsg}</span>
                  </div>
                )}

                <div className="config-form-group" style={{ marginBottom: '12px' }}>
                  <label className="config-form-label" style={{ marginBottom: '4px' }}>Shortcut Label / Name</label>
                  <input
                    type="text"
                    placeholder="e.g. Friends & Streaks, College Buddies..."
                    value={shortcutName}
                    onChange={(e) => setShortcutName(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      borderRadius: '8px',
                      border: '1px solid #cbd5e1',
                      fontSize: '0.86rem'
                    }}
                    autoFocus
                  />
                </div>

                <div className="config-form-group" style={{ marginBottom: '6px' }}>
                  <label className="config-form-label" style={{ marginBottom: '4px' }}>
                    Choose Shortcut Emoji (Keyboard)
                  </label>
                  <div style={{ marginBottom: '6px', fontSize: '0.74rem', color: '#64748b' }}>
                    Pick the exact emoji assigned to this shortcut on your phone:
                  </div>
                  <EmojiKeyboard
                    selectedEmoji={selectedEmoji}
                    onSelectEmoji={(emoji) => setSelectedEmoji(emoji)}
                  />
                </div>
              </div>

              <div className="config-modal-footer">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowAddModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Save Shortcut
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

