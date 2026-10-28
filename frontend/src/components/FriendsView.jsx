import React, { useState } from 'react';
import {
  Search,
  UserPlus,
  Trash2,
  Eye,
  Check,
  Plus,
  Flame,
  Clock
} from 'lucide-react';

export default function FriendsView({
  contacts = [],
  selectedIds = [],
  onToggleSelect,
  onToggleSelectAll,
  onAddContact,
  onDeleteContact,
  onTriggerWorkflow
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [activeFilterTab, setActiveFilterTab] = useState('all');
  const [showAddModal, setShowAddModal] = useState(false);
  const [newUsername, setNewUsername] = useState('');
  const [newDisplayName, setNewDisplayName] = useState('');

  // Filtering
  const filteredContacts = contacts.filter((c) => {
    const matchesSearch =
      c.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.display_name.toLowerCase().includes(searchTerm.toLowerCase());

    if (!matchesSearch) return false;

    if (activeFilterTab === 'active') return c.status === 'confirmed';
    if (activeFilterTab === 'inactive') return c.status === 'dormant' || c.status === 'pending';
    if (activeFilterTab === 'unknown') return c.status === 'unknown';
    return true;
  });

  const allSelected = filteredContacts.length > 0 && filteredContacts.every((c) => selectedIds.includes(c.id));

  const handleAddSubmit = (e) => {
    e.preventDefault();
    if (!newUsername.trim()) return;
    onAddContact({
      username: newUsername.trim(),
      display_name: newDisplayName.trim() || newUsername.trim()
    });
    setNewUsername('');
    setNewDisplayName('');
    setShowAddModal(false);
  };

  return (
    <div className="page-container">
      <div className="white-panel">
        {/* Header */}
        <div className="panel-header-row">
          <div className="panel-header-title">
            <h3>Friend Management</h3>
            <p>Select friends to add, remove, or monitor in bulk.</p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              className="btn-primary"
              onClick={() => setShowAddModal(true)}
            >
              <Plus size={16} />
              <span>Add Target Contact</span>
            </button>
          </div>
        </div>

        {/* Search Bar */}
        <div className="search-input-wrap">
          <Search size={18} style={{ color: '#94a3b8' }} />
          <input
            type="text"
            placeholder="Search friends by name or username..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        {/* Filter Tabs */}
        <div className="filter-tabs-row">
          <button
            className={`filter-tab ${activeFilterTab === 'all' ? 'active' : ''}`}
            onClick={() => setActiveFilterTab('all')}
          >
            All ({contacts.length})
          </button>
          <button
            className={`filter-tab ${activeFilterTab === 'active' ? 'active' : ''}`}
            onClick={() => setActiveFilterTab('active')}
          >
            Active ({contacts.filter(c => c.status === 'confirmed').length})
          </button>
          <button
            className={`filter-tab ${activeFilterTab === 'inactive' ? 'active' : ''}`}
            onClick={() => setActiveFilterTab('inactive')}
          >
            Inactive ({contacts.filter(c => c.status === 'dormant' || c.status === 'pending').length})
          </button>
          <button
            className={`filter-tab ${activeFilterTab === 'unknown' ? 'active' : ''}`}
            onClick={() => setActiveFilterTab('unknown')}
          >
            Unknown ({contacts.filter(c => c.status === 'unknown').length})
          </button>
        </div>

        {/* Table */}
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: '40px' }}>
                  <input
                    type="checkbox"
                    checked={allSelected}
                    onChange={(e) => onToggleSelectAll(filteredContacts.map(c => c.id), e.target.checked)}
                    style={{ cursor: 'pointer', width: '16px', height: '16px' }}
                  />
                </th>
                <th>Friend</th>
                <th>Status</th>
                <th>Streak Info</th>
                <th>Last Active</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredContacts.length === 0 ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: '36px', color: '#94a3b8' }}>
                    No contacts match your current search and filter criteria.
                  </td>
                </tr>
              ) : (
                filteredContacts.map((contact) => {
                  const isChecked = selectedIds.includes(contact.id);
                  return (
                    <tr key={contact.id} style={{ background: isChecked ? 'rgba(124, 58, 237, 0.04)' : 'transparent' }}>
                      <td>
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => onToggleSelect(contact.id)}
                          style={{ cursor: 'pointer', width: '16px', height: '16px' }}
                        />
                      </td>
                      <td>
                        <div className="avatar-cell">
                          <div className="contact-avatar">
                            {contact.display_name.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <div style={{ fontWeight: 600, color: '#0f172a' }}>{contact.display_name}</div>
                            <div style={{ fontSize: '0.78rem', color: '#64748b' }}>@{contact.username}</div>
                          </div>
                        </div>
                      </td>
                      <td>
                        <span className={`badge-status ${
                          contact.status === 'confirmed' ? 'badge-active' :
                          contact.status === 'dormant' ? 'badge-inactive' : 'badge-pending'
                        }`}>
                          {contact.status === 'confirmed' ? 'Active' :
                           contact.status === 'dormant' ? 'Inactive' : 'Pending'}
                        </span>
                      </td>
                      <td>
                        {contact.streak_days ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.84rem', color: '#ea580c', fontWeight: 600 }}>
                            <Flame size={15} />
                            <span>{contact.streak_days} days</span>
                          </div>
                        ) : (
                          <span style={{ fontSize: '0.82rem', color: '#94a3b8' }}>No Streak</span>
                        )}
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.82rem', color: '#64748b' }}>
                          <Clock size={14} />
                          <span>{contact.last_interaction ? new Date(contact.last_interaction).toLocaleDateString() : 'Recent'}</span>
                        </div>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <button
                          className="btn-danger"
                          style={{ padding: '4px 10px', fontSize: '0.78rem' }}
                          onClick={() => onDeleteContact(contact.id)}
                          title="Delete contact"
                        >
                          <Trash2 size={13} />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Footer Actions */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '20px', paddingTop: '16px', borderTop: '1px solid #f1f5f9', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ fontSize: '0.88rem', color: '#475569' }}>
            <strong>{selectedIds.length}</strong> friend(s) selected
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              className="btn-secondary"
              disabled={selectedIds.length === 0}
              onClick={() => onTriggerWorkflow('unfollow', { filter_type: 'custom', target_ids: selectedIds })}
            >
              <Trash2 size={16} style={{ color: '#ef4444' }} />
              <span>Unfollow Selected</span>
            </button>

            <button
              className="btn-primary"
              disabled={selectedIds.length === 0}
              onClick={() => onTriggerWorkflow('follow', { mode: 'search', target_ids: selectedIds })}
            >
              <UserPlus size={16} />
              <span>Bulk Add Selected</span>
            </button>
          </div>
        </div>
      </div>

      {/* Add Contact Modal */}
      {showAddModal && (
        <div className="modal-backdrop">
          <div className="modal-dialog">
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '6px' }}>Add Target Friend</h3>
            <p style={{ fontSize: '0.82rem', color: '#64748b', marginBottom: '18px' }}>
              Add a Snapchat friend username and display name to target list.
            </p>

            <form onSubmit={handleAddSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '0.82rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Username (@)</label>
                <input
                  type="text"
                  placeholder="e.g. alex.dev"
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', border: '1px solid #cbd5e1', outline: 'none' }}
                  required
                />
              </div>

              <div>
                <label style={{ fontSize: '0.82rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Display Name</label>
                <input
                  type="text"
                  placeholder="e.g. Alex (Lead Engineer)"
                  value={newDisplayName}
                  onChange={(e) => setNewDisplayName(e.target.value)}
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', border: '1px solid #cbd5e1', outline: 'none' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowAddModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                >
                  Add Friend Target
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
