import ActionConfigModal from './ActionConfigModal';
import React, { useState } from 'react';
import {
  Flame,
  Plus,
  Clock,
  MoreVertical,
  CheckCircle2,
  Play
} from 'lucide-react';

export default function StreakRemindersView({
  onTriggerWorkflow
}) {
  const [reminders, setReminders] = useState([
    { id: 1, name: 'Ayesha Khan', schedule: 'Daily • 8:00 PM', active: true, streak: 42 },
    { id: 2, name: 'Sara Malik', schedule: 'Daily • 9:00 PM', active: true, streak: 18 },
    { id: 3, name: 'Usman Ali', schedule: 'Daily • 10:00 PM', active: false, streak: 7 },
    { id: 4, name: 'Zainab Noor', schedule: 'Daily • 7:30 PM', active: true, streak: 89 },
    { id: 5, name: 'Mr. Jalil', schedule: 'Daily • 11:00 PM', active: true, streak: 1 }
  ]);

  const [showAddModal, setShowAddModal] = useState(false);
  const [newName, setNewName] = useState('');
  const [newTime, setNewTime] = useState('8:00 PM');
  const [configModalOpen, setConfigModalOpen] = useState(false);

  const toggleReminder = (id) => {
    setReminders((prev) =>
      prev.map((r) => (r.id === id ? { ...r, active: !r.active } : r))
    );
  };

  const handleAddSubmit = (e) => {
    e.preventDefault();
    if (!newName.trim()) return;
    setReminders((prev) => [
      ...prev,
      {
        id: Date.now(),
        name: newName.trim(),
        schedule: `Daily • ${newTime}`,
        active: true,
        streak: 1
      }
    ]);
    setNewName('');
    setShowAddModal(false);
  };

  return (
    <div className="page-container">
      <div className="white-panel">
        {/* Header */}
        <div className="panel-header-row">
          <div className="panel-header-title">
            <h3>Snapscore Booster</h3>
            <p>Boost snapscore & maintain active streaks automatically.</p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              className="btn-secondary"
              onClick={() => setConfigModalOpen(true)}
              title="Configure and trigger active streak boost"
            >
              <Flame size={16} style={{ color: '#ea580c' }} />
              <span>Run Streak Multiplier</span>
            </button>

            <button
              className="btn-primary"
              onClick={() => setShowAddModal(true)}
            >
              <Plus size={16} />
              <span>Add New Reminder</span>
            </button>
          </div>
        </div>

        {/* Reminders List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {reminders.map((reminder) => (
            <div
              key={reminder.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '16px 20px',
                borderRadius: '12px',
                border: '1px solid #e2e8f0',
                background: '#ffffff',
                boxShadow: '0 1px 3px rgba(0,0,0,0.03)'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                <div
                  className="contact-avatar"
                  style={{
                    background: reminder.active ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)' : '#cbd5e1'
                  }}
                >
                  {reminder.name.charAt(0)}
                </div>
                <div>
                  <div style={{ fontWeight: 600, color: '#0f172a', fontSize: '0.94rem' }}>
                    {reminder.name}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: '#64748b', marginTop: '2px' }}>
                    <Clock size={13} />
                    <span>{reminder.schedule}</span>
                    <span>•</span>
                    <span style={{ color: '#ea580c', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '2px' }}>
                      <Flame size={12} /> {reminder.streak}d streak
                    </span>
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <span
                  className={`badge-status ${reminder.active ? 'badge-active' : 'badge-paused'}`}
                >
                  {reminder.active ? 'Active' : 'Paused'}
                </span>

                {/* Toggle switch */}
                <label className="switch">
                  <input
                    type="checkbox"
                    checked={reminder.active}
                    onChange={() => toggleReminder(reminder.id)}
                  />
                  <span className="slider"></span>
                </label>

                <button
                  className="icon-btn"
                  style={{ width: '32px', height: '32px' }}
                  title="Options"
                >
                  <MoreVertical size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Add Reminder Modal */}
      {showAddModal && (
        <div className="modal-backdrop">
          <div className="modal-dialog">
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '6px' }}>Schedule Snapscore Booster</h3>
            <p style={{ fontSize: '0.82rem', color: '#64748b', marginBottom: '18px' }}>
              Create an automated snapscore booster routine for a friend.
            </p>

            <form onSubmit={handleAddSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '0.82rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Friend Name</label>
                <input
                  type="text"
                  placeholder="e.g. Ayesha Khan"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', border: '1px solid #cbd5e1', outline: 'none' }}
                  required
                />
              </div>

              <div>
                <label style={{ fontSize: '0.82rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>Reminder Time</label>
                <input
                  type="text"
                  placeholder="e.g. 8:00 PM"
                  value={newTime}
                  onChange={(e) => setNewTime(e.target.value)}
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
                  Save Reminder
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <ActionConfigModal
        isOpen={configModalOpen}
        actionType="streak_booster"
        onClose={() => setConfigModalOpen(false)}
        onConfirm={(type, params) => onTriggerWorkflow(type, params)}
      />
    </div>
  );
}
