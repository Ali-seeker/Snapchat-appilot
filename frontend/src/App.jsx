import React, { useState, useEffect } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import Header from './components/Header';
import SetupDisclosure from './components/SetupDisclosure';
import ControlPanel from './components/ControlPanel';
import TargetList from './components/TargetList';
import DemoRunner from './components/DemoRunner';
import AuditLogView from './components/AuditLogView';
import LiveExecutionModal from './components/LiveExecutionModal';
import ReminderDraftView from './components/ReminderDraftView';
import BulkFollowCard from './components/BulkFollowCard';
import BulkUnfollowCard from './components/BulkUnfollowCard';
import AutoSnapCard from './components/AutoSnapCard';
import SnapscoreBoosterCard from './components/SnapscoreBoosterCard';
import ChainedWorkflowCard from './components/ChainedWorkflowCard';

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

  const [disclosureAcknowledged, setDisclosureAcknowledged] = useState(false);
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
  const handleStartWorkflow = async (mode = 'live') => {
    try {
      setActiveScenario('workflow');
      setExecutionStartTime(Date.now());

      if (mode === 'live') {
        setExecutionTitle(`Live Snapchat Automation (${selectedIds.length} Targets)`);
        setExecutionModalOpen(true);
        await fetch(`${API_BASE}/live/run`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ target_ids: selectedIds, action: 'add' })
        });
      } else {
        setExecutionTitle(`Assisted Workflow (${selectedIds.length} Targets)`);
        setExecutionModalOpen(true);
        await fetch(`${API_BASE}/demo/run`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ scenario: 'success', target_ids: selectedIds })
        });
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleTriggerWorkflow = async (type, params = {}) => {
    try {
      setActiveScenario('live_workflow');
      setExecutionStartTime(Date.now());

      const titles = {
        follow: `Bulk Follow Automation (${params.mode || 'Quick Add'})`,
        unfollow: `Smart Unfollow (${params.filter_type || 'No Streak'})`,
        snap: 'Auto Snap Dispatch (Random Filter)',
        snapscore: `Snapscore Booster (${params.cycles || 3} Cycles)`,
        chain: `Chained Routine: ${params.routine_type || 'Morning Growth'}`
      };
      setExecutionTitle(titles[type] || `Snapchat Workflow: ${type}`);
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
        payload.target_ids = selectedIds;
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
      const scenarioTitles = {
        full_suite: 'Full Acceptance Test Suite',
        success: 'Test: Success Flow',
        duplicate: 'Test: Duplicate Target Rejection',
        inactivity_unknown: 'Test: Inactivity Policy & Data Provenance',
        failure: 'Test: Error Handling & Rollback Recovery'
      };
      setActiveScenario(scenario);
      setExecutionStartTime(Date.now());
      setExecutionTitle(scenarioTitles[scenario] || `Demo: ${scenario}`);
      setExecutionModalOpen(true);
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
    setLogs([]);
    try {
      await fetch(`${API_BASE}/logs`, { method: 'DELETE' });
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
        snapchatVersion={snapchatVersion}
        onReset={handleReset}
      />

      {/* FR-01: Setup & Disclosure */}
      <SetupDisclosure
        acknowledged={disclosureAcknowledged}
        onToggleAcknowledge={setDisclosureAcknowledged}
      />

      {/* Day 3 Production Automation Hub */}
      <div style={{ marginTop: '20px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f8fafc', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>🚀 Day 3 Production Automation Hub</span>
            </h2>
            <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: '2px 0 0 0' }}>
              One-click multi-modal follow, engagement-based unfollow, auto snap sending, and legitimate score booster.
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              style={{
                fontSize: '0.74rem',
                fontWeight: 600,
                color: '#facc15',
                background: 'rgba(250, 204, 21, 0.1)',
                border: '1px solid rgba(250, 204, 21, 0.3)',
                padding: '3px 8px',
                borderRadius: '6px',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px'
              }}
            >
              <span>👻</span>
              <span>Target: Snapchat v{snapchatVersion || '14.29.0.50'}</span>
            </span>
            <span className="badge badge-emerald">Resilient &amp; Anti-Ban</span>
          </div>
        </div>

        {/* 2-Column Responsive Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px', marginBottom: '16px' }}>
          <BulkFollowCard
            isRunning={appState === 'RUNNING'}
            onTriggerWorkflow={handleTriggerWorkflow}
            selectedCount={selectedIds.length}
          />
          <BulkUnfollowCard
            isRunning={appState === 'RUNNING'}
            onTriggerWorkflow={handleTriggerWorkflow}
            selectedTargets={selectedTargets}
          />
          <AutoSnapCard
            isRunning={appState === 'RUNNING'}
            onTriggerWorkflow={handleTriggerWorkflow}
          />
          <SnapscoreBoosterCard
            isRunning={appState === 'RUNNING'}
            onTriggerWorkflow={handleTriggerWorkflow}
          />
        </div>

        {/* Full-Width Chained Daily Routines */}
        <ChainedWorkflowCard
          isRunning={appState === 'RUNNING'}
          onTriggerWorkflow={handleTriggerWorkflow}
        />
      </div>

      {/* FR-03 & FR-05: Controls and Confirmation Review */}
      <ControlPanel
        appState={appState}
        activeWorkflow={activeWorkflow}
        isPaused={isPaused}
        selectedTargets={selectedTargets}
        onStartWorkflow={handleStartWorkflow}
        onPauseWorkflow={handlePauseWorkflow}
        onResumeWorkflow={handleResumeWorkflow}
        onEmergencyStop={handleEmergencyStop}
        disclosureAcknowledged={disclosureAcknowledged}
        logs={logs}
        devices={devices}
        snapchatVersion={snapchatVersion}
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

      {/* FR-07 & FR-08: Streak Reminders & Snap Drafts */}
      <div style={{ marginTop: '24px' }}>
        <ReminderDraftView contacts={contacts} />
      </div>

      {/* FR-12: Deterministic Demo Mode Runner */}
      <div style={{ marginTop: '24px' }}>
        <DemoRunner
          onRunDemo={handleRunDemo}
          isRunning={appState === 'RUNNING'}
          activeScenario={activeScenario}
        />
      </div>

      {/* FR-05 & FR-09: Live Execution Modal for Workflows & Demos */}
      <LiveExecutionModal
        isOpen={executionModalOpen}
        onClose={() => {
          setExecutionModalOpen(false);
          setActiveScenario(null);
        }}
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
