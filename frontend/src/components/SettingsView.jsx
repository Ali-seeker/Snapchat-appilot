import React, { useState } from 'react';
import {
  Smartphone,
  ShieldCheck,
  ChevronRight,
  HelpCircle,
  RotateCcw,
  Sliders,
  CheckCircle2,
  Lock,
  Wifi
} from 'lucide-react';

export default function SettingsView({
  connectedDevice,
  snapchatVersion,
  onReset
}) {
  const [activeTab, setActiveTab] = useState('account');

  return (
    <div className="page-container">
      <div className="white-panel">
        {/* Header */}
        <div className="panel-header-row">
          <div className="panel-header-title">
            <h3>Settings &amp; Platform Config</h3>
            <p>Manage connected devices, Snapchat version lock, and safety policies.</p>
          </div>
        </div>

        {/* Setting Tabs */}
        <div className="filter-tabs-row">
          {['account', 'permissions', 'notifications', 'privacy'].map((t) => (
            <button
              key={t}
              className={`filter-tab ${activeTab === t ? 'active' : ''}`}
              onClick={() => setActiveTab(t)}
            >
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>

        {/* Snapchat Connection Card */}
        <div
          style={{
            background: 'linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%)',
            border: '1px solid #FDE68A',
            borderRadius: '16px',
            padding: '24px',
            marginBottom: '24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '16px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div
              style={{
                width: '52px',
                height: '52px',
                borderRadius: '50%',
                background: '#FFFC00',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.6rem',
                boxShadow: '0 4px 12px rgba(255, 252, 0, 0.4)'
              }}
            >
              👻
            </div>

            <div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: '#92400e' }}>
                Snapchat Application Connection
              </div>
              <div style={{ fontSize: '0.84rem', color: '#b45309', marginTop: '2px' }}>
                Active Target: <strong>Snapchat v{snapchatVersion || '14.29.0.50'}</strong> (Build 322522)
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', color: '#16a34a', marginTop: '4px', fontWeight: 600 }}>
                <CheckCircle2 size={14} />
                <span>Device: {connectedDevice ? (connectedDevice.model || connectedDevice.device_id) : 'Infinix X6817 (Connected)'}</span>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span
              style={{
                background: '#DCFCE7',
                color: '#16A34A',
                fontWeight: 700,
                fontSize: '0.8rem',
                padding: '6px 14px',
                borderRadius: '999px',
                border: '1px solid #BBF7D0'
              }}
            >
              Hardware Linked
            </span>
          </div>
        </div>

        {/* List of Config Items */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {/* Item 1: Automation Settings */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '18px 20px',
              borderRadius: '12px',
              border: '1px solid #e2e8f0',
              background: '#ffffff',
              cursor: 'pointer'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: '#F1F5F9', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#475569' }}>
                <Sliders size={20} />
              </div>
              <div>
                <div style={{ fontWeight: 600, color: '#0f172a', fontSize: '0.94rem' }}>Automation Settings</div>
                <div style={{ fontSize: '0.8rem', color: '#64748b' }}>Humanized jitter delays (1.2s - 3.5s) &amp; anti-ban pacing</div>
              </div>
            </div>
            <ChevronRight size={18} style={{ color: '#94a3b8' }} />
          </div>

          {/* Item 2: Help & Support */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '18px 20px',
              borderRadius: '12px',
              border: '1px solid #e2e8f0',
              background: '#ffffff',
              cursor: 'pointer'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: '#F1F5F9', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#475569' }}>
                <HelpCircle size={20} />
              </div>
              <div>
                <div style={{ fontWeight: 600, color: '#0f172a', fontSize: '0.94rem' }}>Help &amp; Documentation</div>
                <div style={{ fontSize: '0.8rem', color: '#64748b' }}>Operator guides, troubleshooting &amp; platform rules</div>
              </div>
            </div>
            <ChevronRight size={18} style={{ color: '#94a3b8' }} />
          </div>

          {/* Item 3: Reset Data */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '18px 20px',
              borderRadius: '12px',
              border: '1px solid #e2e8f0',
              background: '#ffffff',
              cursor: 'pointer'
            }}
            onClick={onReset}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: '#FEE2E2', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#DC2626' }}>
                <RotateCcw size={20} />
              </div>
              <div>
                <div style={{ fontWeight: 600, color: '#dc2626', fontSize: '0.94rem' }}>Reset State Machine</div>
                <div style={{ fontSize: '0.8rem', color: '#64748b' }}>Restore system state machine back to IDLE</div>
              </div>
            </div>
            <ChevronRight size={18} style={{ color: '#94a3b8' }} />
          </div>
        </div>
      </div>
    </div>
  );
}
