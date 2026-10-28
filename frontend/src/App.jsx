import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ExecutiveDashboard from './components/ExecutiveDashboard';
import AuxiliarySourcesTab from './components/AuxiliarySourcesTab';
import PowerAllocationTab from './components/PowerAllocationTab';
import EnergyFlowTab from './components/EnergyFlowTab';
import BatteryImpactTab from './components/BatteryImpactTab';
import PredictionTab from './components/PredictionTab';
import FleetEdaTab from './components/FleetEdaTab';
import BenchmarksTab from './components/BenchmarksTab';
import HistoryTab from './components/HistoryTab';
import SettingsTab from './components/SettingsTab';
import api from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [healthStatus, setHealthStatus] = useState(null);

  useEffect(() => {
    async function checkHealth() {
      try {
        const res = await api.getHealth();
        setHealthStatus(res);
      } catch (err) {
        console.error('Health check error:', err);
      }
    }
    checkHealth();
  }, []);

  return (
    <div className="app-container">
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        healthStatus={healthStatus}
      />

      <main className="main-content">
        {activeTab === 'dashboard' && (
          <ExecutiveDashboard onNavigate={(tab) => setActiveTab(tab)} />
        )}

        {activeTab === 'sources' && (
          <AuxiliarySourcesTab />
        )}

        {activeTab === 'allocation' && (
          <PowerAllocationTab />
        )}

        {activeTab === 'energy_flow' && (
          <EnergyFlowTab />
        )}

        {activeTab === 'battery_impact' && (
          <BatteryImpactTab />
        )}

        {activeTab === 'ml_prediction' && (
          <PredictionTab />
        )}

        {activeTab === 'fleet_eda' && (
          <FleetEdaTab />
        )}

        {activeTab === 'diagnostics' && (
          <BenchmarksTab />
        )}

        {activeTab === 'history' && (
          <HistoryTab />
        )}

        {activeTab === 'settings' && (
          <SettingsTab />
        )}
      </main>
    </div>
  );
}
