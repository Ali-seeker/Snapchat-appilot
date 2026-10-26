import React, { useState } from 'react';
import { Users, UserPlus, Trash2, CheckSquare, Square, Search, AlertCircle } from 'lucide-react';

export default function TargetList({
  contacts,
  selectedIds,
  onToggleSelect,
  onToggleSelectAll,
  onAddContact,
  onDeleteContact
}) {
  const [newUsername, setNewUsername] = useState('');
  const [newDisplayName, setNewDisplayName] = useState('');
  const [newNotes, setNewNotes] = useState('');
  const [search, setSearch] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const handleAdd = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    if (!newUsername.trim()) {
      setErrorMsg('Username cannot be empty');
      return;
    }
    const res = await onAddContact({
      username: newUsername,
      display_name: newDisplayName,
      notes: newNotes
    });
    if (res.success) {
      setNewUsername('');
      setNewDisplayName('');
      setNewNotes('');
    } else {
      setErrorMsg(res.error || 'Failed to add contact');
    }
  };

  const filtered = contacts.filter((c) =>
    c.username.toLowerCase().includes(search.toLowerCase()) ||
    (c.display_name && c.display_name.toLowerCase().includes(search.toLowerCase()))
  );

  const allSelected = filtered.length > 0 && filtered.every((c) => selectedIds.includes(c.id));

  return (
    <div className="glass-panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="panel-header">
        <div className="panel-title">
          <Users size={18} color="#38bdf8" />
          <span>FR-04: User-Curated Target List</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            className="btn btn-secondary"
            onClick={() => onToggleSelectAll(!allSelected)}
            style={{ padding: '6px 12px', fontSize: '0.8rem' }}
          >
            {allSelected ? <CheckSquare size={14} color="#38bdf8" /> : <Square size={14} />}
            <span>{allSelected ? 'Deselect All' : 'Select All'}</span>
          </button>
        </div>
      </div>

      <div className="panel-body" style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* Add Contact Form */}
        <form onSubmit={handleAdd} style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <input
            className="input-field"
            style={{ flex: '1 1 140px' }}
            placeholder="Username (e.g. sam_dev)"
            value={newUsername}
            onChange={(e) => { setNewUsername(e.target.value); setErrorMsg(''); }}
          />
          <input
            className="input-field"
            style={{ flex: '1 1 140px' }}
            placeholder="Display Name (Optional)"
            value={newDisplayName}
            onChange={(e) => setNewDisplayName(e.target.value)}
          />
          <button type="submit" className="btn btn-primary" style={{ padding: '10px 16px' }}>
            <UserPlus size={16} />
            <span>Add</span>
          </button>
        </form>

        {errorMsg && (
          <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '8px 12px', borderRadius: '6px', fontSize: '0.82rem', color: '#fca5a5', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={15} />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Search */}
        <div style={{ position: 'relative' }}>
          <input
            className="input-field"
            placeholder="Search curated contacts..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ paddingLeft: '34px' }}
          />
          <Search size={15} color="#64748b" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
        </div>

        {/* Table */}
        <div style={{ overflowY: 'auto', flex: 1, border: '1px solid var(--border-subtle)', borderRadius: '8px' }}>
          <table className="target-table">
            <thead>
              <tr>
                <th style={{ width: '40px' }}></th>
                <th>Username</th>
                <th>Display Name</th>
                <th>Last Active</th>
                <th style={{ width: '50px' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', color: '#64748b', padding: '24px' }}>
                    No contacts in curated list. Add one above.
                  </td>
                </tr>
              ) : (
                filtered.map((contact) => {
                  const isSelected = selectedIds.includes(contact.id);
                  return (
                    <tr key={contact.id} style={{ background: isSelected ? 'rgba(56, 189, 248, 0.05)' : 'transparent' }}>
                      <td>
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => onToggleSelect(contact.id)}
                          style={{ accentColor: '#38bdf8', cursor: 'pointer' }}
                        />
                      </td>
                      <td style={{ fontWeight: 600, color: '#f8fafc' }}>
                        @{contact.username}
                      </td>
                      <td style={{ color: '#94a3b8' }}>
                        {contact.display_name || '—'}
                      </td>
                      <td>
                        <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '4px', background: 'rgba(148, 163, 184, 0.1)', color: '#94a3b8' }}>
                          {contact.last_active_days !== null ? `${contact.last_active_days}d ago` : 'Unknown (Safe default)'}
                        </span>
                      </td>
                      <td>
                        <button
                          onClick={() => onDeleteContact(contact.id)}
                          style={{ background: 'transparent', border: 'none', color: '#f87171', cursor: 'pointer', padding: '4px' }}
                          title="Delete contact"
                        >
                          <Trash2 size={15} />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
