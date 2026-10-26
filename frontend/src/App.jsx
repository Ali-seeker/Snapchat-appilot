import React, { useState, useEffect } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import Header from './components/Header';
import SetupDisclosure from './components/SetupDisclosure';
import ControlPanel from './components/ControlPanel';
import TargetList from './components/TargetList';
import DemoRunner from './components/DemoRunner';
import AuditLogView from './components/AuditLogView';
import SnapscoreGate from './components/SnapscoreGate';

const API_BASE = 'http://localhost:8000/api';

export default function App() {
  const {
    isConnected,
    appState,
    activeWorkflow,
    isPaused,
    isStopped,
    devices,
    contacts,
    setContacts,
    logs,
    setLogs,
    latency,
    sendEmergencyStop
  } = useWebSocket();

  const [disclosureAcknowledged, setDisclosureAcknowledged] = useState(false);
  const [selectedIds, setSelectedIds] = useState([]);

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

  const handleToggleSelectAll = (select) => {
    if (select) {
      setSelectedIds(contacts.map((c) => c.id));
    } else {
      setSelectedIds([]);
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

  // Workflow Controls
  const handleStartWorkflow = async () => {
    try {
      await fetch(`${API_BASE}/demo/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario: 'success', target_ids: selectedIds })
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

  const handleEmergencyStop = async () => {
    sendEmergencyStop();
    try {
      await fetch(`${API_BASE}/control/stop`, { method: 'POST' });
    } catch (e) {
      console.error(e);
    }
  };

  const handleReset = async () => {
    try {
      await fetch(`${API_BASE}/control/reset`, { method: 'POST' });
    } catch (e) {
      console.error(e);
    }
  };

  const handleRunDemo = async (scenario) => {
    try {
      await fetch(`${API_BASE}/demo/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario, target_ids: selectedIds })
      });
    } catch (e) {
      console.error(e);
    }
  };

  const handleClearLogs = async () => {
    try {
      await fetch(`${API_BASE}/logs`, { method: 'DELETE' });
      setLogs([]);
    } catch (e) {
      console.error(e);
    }
  };

  const selectedTargets = contacts.filter((c) => selectedIds.includes(c.id));

  return (
    <div className="app-layout">
      {/* Header with State Machine badge */}
      <Header
        appState={appState}
        activeWorkflow={activeWorkflow}
        isConnected={isConnected}
        latency={latency}
        onReset={handleReset}
      />

      {/* FR-01: Setup & Disclosure */}
      <SetupDisclosure
        acknowledged={disclosureAcknowledged}
        onToggleAcknowledge={setDisclosureAcknowledged}
      />

      {/* FR-03 & FR-05: Controls and Confirmation Review */}
      <ControlPanel
        appState={appState}
        isPaused={isPaused}
        selectedTargets={selectedTargets}
        onStartWorkflow={handleStartWorkflow}
        onPauseWorkflow={handlePauseWorkflow}
        onResumeWorkflow={handleResumeWorkflow}
        onEmergencyStop={handleEmergencyStop}
        disclosureAcknowledged={disclosureAcknowledged}
      />

      {/* Two-Column Grid: Contacts (FR-04) & Audit Logs (FR-09, FR-10) */}
      <div className="dashboard-grid">
        <TargetList
          contacts={contacts}
          selectedIds={selectedIds}
          onToggleSelect={handleToggleSelect}
          onToggleSelectAll={handleToggleSelectAll}
          onAddContact={handleAddContact}
          onDeleteContact={handleDeleteContact}
        />

        <AuditLogView logs={logs} onClearLogs={handleClearLogs} />
      </div>

      {/* FR-12: Deterministic Demo Mode Runner */}
      <div style={{ marginTop: '24px' }}>
        <DemoRunner
          onRunDemo={handleRunDemo}
          isRunning={appState === 'RUNNING'}
        />
      </div>

      {/* FR-13: Snapscore Feature Gate */}
      <SnapscoreGate />
    </div>
  );
}
