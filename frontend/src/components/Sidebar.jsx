import React from 'react';

const navItems = [
  { id: 'dashboard', label: 'Executive Dashboard', icon: 'fa-solid fa-gauge-high' },
  { id: 'sources', label: 'Auxiliary Energy Sources', icon: 'fa-solid fa-solar-panel' },
  { id: 'allocation', label: 'Intelligent Power Allocation', icon: 'fa-solid fa-network-wired' },
  { id: 'energy_flow', label: 'Energy Flow & Loads', icon: 'fa-solid fa-arrow-right-arrow-left' },
  { id: 'battery_impact', label: 'Battery Impact & Efficiency', icon: 'fa-solid fa-car-battery' },
  { id: 'ml_prediction', label: 'ML Energy Prediction', icon: 'fa-solid fa-brain' },
  { id: 'fleet_eda', label: 'Fleet Data & EDA', icon: 'fa-solid fa-chart-column' },
  { id: 'diagnostics', label: 'Model Diagnostics', icon: 'fa-solid fa-microchip' },
  { id: 'history', label: 'Audit History & Logs', icon: 'fa-solid fa-clock-rotate-left' },
  { id: 'settings', label: 'System Settings', icon: 'fa-solid fa-gear' }
];

export default function Sidebar({ activeTab, setActiveTab, healthStatus }) {
  const isHealthy = healthStatus?.status === 'healthy';

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-icon">
          <i className="fa-solid fa-bolt-lightning"></i>
        </div>
        <div className="brand-text">
          <h2>EV-IEMS <span className="badge-pill">v3.0</span></h2>
          <p>Aux Energy & Allocation</p>
        </div>
      </div>

      <nav className="nav-menu">
        {navItems.map((item) => (
          <button
            key={item.id}
            className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
            onClick={() => setActiveTab(item.id)}
          >
            <i className={item.icon}></i>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="status-indicator">
          <div className={`status-dot ${isHealthy ? '' : 'degraded'}`}></div>
          <div className="status-text">
            <strong>{isHealthy ? 'Backend Connected' : 'Connecting...'}</strong>
            <span>Flask API (Port 5000)</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
