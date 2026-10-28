import React, { useState, useEffect } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import OverviewView from './components/OverviewView';
import FriendsView from './components/FriendsView';
import StreakRemindersView from './components/StreakRemindersView';
import SnapRemindersView from './components/SnapRemindersView';
import ActivityView from './components/ActivityView';
import SettingsView from './components/SettingsView';
import LiveExecutionModal from './components/LiveExecutionModal';

const API_BASE = 'http://localhost:8000/api';

export default function App() {
  const {
    isConnected,
    appState,
    activeWorkflow,
    isPaused,
    isStopped,
    devices,
    snapchatVersion,
    contacts,
    setContacts,
    logs,
    setLogs,
    latency,
    sendEmergencyStop
  } = useWebSocket();

  const [activeTab, setActiveTab] = useState('home');
  const [selectedIds, setSelectedIds] = useState([]);
  const [executionModalOpen, setExecutionModalOpen] = useState(false);
  const [executionTitle, setExecutionTitle] = useState('');
  const [activeScenario, setActiveScenario] = useState(null);
  const [executionStartTime, setExecutionStartTime] = useState(null);

  // Fetch initial contacts & logs via REST
  useEffect(() => {
    fetch(`${API_BASE}/contacts`)
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) setContacts(data);
      })
      .catch(() => {});

    fetch(`${API_BASE}/logs`)
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) setLogs(data);
      })
      .catch(() => {});
  }, [setContacts, setLogs]);

  // Target selection handlers
  const handleToggleSelect = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleToggleSelectAll = (filteredIds, select) => {
    if (select) {
      setSelectedIds((prev) => Array.from(new Set([...prev, ...filteredIds])));
    } else {
      setSelectedIds((prev) => prev.filter((id) => !filteredIds.includes(id)));
    }
  };

  const handleAddContact = async (contactIn) => {
    try {
      const res = await fetch(`${API_BASE}/contacts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(contactIn)
      });
      const data = await res.json();
      if (!res.ok) {
        return { success: false, error: data.detail || 'Failed to add contact' };
      }
      setContacts((prev) => [...prev, data]);
      return { success: true };
    } catch (e) {
      return { success: false, error: e.message };
    }
  };

  const handleDeleteContact = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/contacts/${id}`, { method: 'DELETE' });
      if (res.ok) {
        setContacts((prev) => prev.filter((c) => c.id !== id));
        setSelectedIds((prev) => prev.filter((item) => item !== id));
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Workflow Trigger Controls
  const handleTriggerWorkflow = async (type, params = {}) => {
    try {
      setActiveScenario('live_workflow');
      setExecutionStartTime(Date.now());

      const titles = {
        follow: `Bulk Follow Automation (${params.mode === 'search' ? 'Username Search' : 'Quick Add Suggestions'})`,
        unfollow: `Smart Unfollow (${params.filter_type === 'no_streak' ? 'No Streak Filter' : 'Custom Target'})`,
        snap: 'Auto Snap Dispatch (Random Lens Filter)',
        snapscore: `Snapscore Booster (${params.cycles || 3} Cycles)`,
        chain: `Chained Routine: ${params.routine_type || 'Morning Growth'}`
      };
      setExecutionTitle(titles[type] || `Snapchat Automation: ${type}`);
      setExecutionModalOpen(true);

      const endpoints = {
        follow: `${API_BASE}/workflow/follow`,
        unfollow: `${API_BASE}/workflow/unfollow`,
        snap: `${API_BASE}/workflow/snap`,
        snapscore: `${API_BASE}/workflow/snapscore`,
        chain: `${API_BASE}/workflow/chain`
      };

      const payload = { ...params };
      if (type === 'follow' && params.mode === 'search') {
        payload.target_ids = (params.target_ids && params.target_ids.length > 0) ? params.target_ids : selectedIds;
      }
      if (type === 'unfollow' && params.filter_type === 'custom') {
        payload.custom_targets = (params.custom_targets && params.custom_targets.length > 0) ? params.custom_targets : selectedIds;
      }

      await fetch(endpoints[type], {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } catch (e) {
      console.error(e);
    }
  };

  const handlePauseWorkflow = async () => {
    try {
      await fetch(`${API_BASE}/control/pause`, { method: 'POST' });
    } catch (e) {
      console.error(e);
    }
  };

  const handleResumeWorkflow = async () => {
    try {
      await fetch(`${API_BASE}/control/resume`, { method: 'POST' });
    } catch (e) {
      console.error(e);
    }
  };

  const handleEmergencyStop = () => {
    sendEmergencyStop();
    fetch(`${API_BASE}/control/stop`, { method: 'POST' }).catch(console.error);
  };

  const handleReset = async () => {
    try {
      await fetch(`${API_BASE}/control/reset`, { method: 'POST' });
    } catch (e) {
      console.error(e);
    }
  };

  const handleClearLogs = async () => {
    setLogs([]);
    try {
      await fetch(`${API_BASE}/logs`, { method: 'DELETE' });
    } catch (e) {
      console.error(e);
    }
  };

  const connectedDevice = devices.find((d) => d.is_connected) || devices[0];

  return (
    <div className="dashboard-layout">
      {/* Navigation Sidebar matching reference design */}
      <Sidebar activeTab={activeTab} onSelectTab={setActiveTab} />

      {/* Main Content Viewport */}
      <main className="dashboard-main">
        {/* Top Header Bar */}
        <TopBar
          appState={appState}
          connectedDevice={connectedDevice}
          snapchatVersion={snapchatVersion}
          onReset={handleReset}
        />

        {/* Dynamic Views by Tab */}
        {activeTab === 'home' && (
          <OverviewView
            appState={appState}
            activeWorkflow={activeWorkflow}
            isPaused={isPaused}
            isStopped={isStopped}
            connectedDevice={connectedDevice}
            snapchatVersion={snapchatVersion}
            contactsCount={contacts.length}
            onTriggerWorkflow={handleTriggerWorkflow}
            onPauseWorkflow={handlePauseWorkflow}
            onResumeWorkflow={handleResumeWorkflow}
            onEmergencyStop={handleEmergencyStop}
          />
        )}

        {activeTab === 'friends' && (
          <FriendsView
            contacts={contacts}
            selectedIds={selectedIds}
            onToggleSelect={handleToggleSelect}
            onToggleSelectAll={handleToggleSelectAll}
            onAddContact={handleAddContact}
            onDeleteContact={handleDeleteContact}
            onTriggerWorkflow={handleTriggerWorkflow}
          />
        )}

        {activeTab === 'streaks' && (
          <StreakRemindersView
            onTriggerWorkflow={handleTriggerWorkflow}
          />
        )}

        {activeTab === 'snaps' && (
          <SnapRemindersView
            onTriggerWorkflow={handleTriggerWorkflow}
          />
        )}

        {activeTab === 'activity' && (
          <ActivityView
            logs={logs}
            onClearLogs={handleClearLogs}
          />
        )}

        {(activeTab === 'settings' || activeTab === 'help') && (
          <SettingsView
            connectedDevice={connectedDevice}
            snapchatVersion={snapchatVersion}
            onReset={handleReset}
          />
        )}
      </main>

      {/* Real-time Telemetry & Execution Modal */}
      <LiveExecutionModal
        isOpen={executionModalOpen}
        onClose={() => setExecutionModalOpen(false)}
        title={executionTitle}
        appState={appState}
        isPaused={isPaused}
        onPause={handlePauseWorkflow}
        onResume={handleResumeWorkflow}
        onEmergencyStop={handleEmergencyStop}
        logs={logs}
        startTime={executionStartTime}
      />
    </div>
  );
}
