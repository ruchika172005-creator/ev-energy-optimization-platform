import React, { useState, useEffect } from 'react';
import api from '../services/api';

export default function SettingsTab() {
  const [settings, setSettings] = useState({
    dc_dc_efficiency: '0.94',
    bus_voltage_v: '12.0',
    operating_mode: 'demonstration_simulation',
    main_battery_nominal_voltage_v: '360.0',
    fleet_avg_consumption_kwh_per_km: '0.2215',
    allow_main_battery_fallback: 'true',
    safety_interlock_active: 'true'
  });
  const [msg, setMsg] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadSettings() {
      try {
        const res = await api.getSettings();
        if (res.success && res.settings) {
          setSettings(prev => ({ ...prev, ...res.settings }));
        }
      } catch (err) {
        console.error('Error loading settings:', err);
      } finally {
        setLoading(false);
      }
    }
    loadSettings();
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setMsg(null);
    try {
      const res = await api.updateSettings(settings);
      if (res.success) {
        setMsg('System settings saved successfully!');
        setTimeout(() => setMsg(null), 3000);
      }
    } catch (err) {
      setMsg(`Save failed: ${err.message}`);
    }
  };

  return (
    <div>
      <div className="top-header">
        <div className="header-title">
          <h1>System Configuration & Parameters</h1>
          <p>Auxiliary Bus Voltage, DC-DC Conversion Thresholds & Operating Mode</p>
        </div>
      </div>

      <div className="glass-card" style={{ maxWidth: '800px' }}>
        {msg && (
          <div style={{
            background: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid var(--border-glow-emerald)',
            borderRadius: '8px',
            padding: '0.75rem 1rem',
            marginBottom: '1.5rem',
            fontSize: '0.85rem',
            color: 'var(--text-emerald)'
          }}>
            <i className="fa-solid fa-circle-check" style={{ marginRight: '0.5rem' }}></i>
            {msg}
          </div>
        )}

        <form onSubmit={handleSave}>
          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">Operating Environment</label>
              <select
                className="form-control"
                value={settings.operating_mode}
                onChange={(e) => setSettings({ ...settings, operating_mode: e.target.value })}
              >
                <option value="demonstration_simulation">Demonstration / Model Simulation</option>
                <option value="sensor_telemetry_live">Hardware Sensor Telemetry (Interface Ready)</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">DC-DC Buck Converter Efficiency (η)</label>
              <input
                type="number"
                step="0.01"
                min="0.70"
                max="0.99"
                className="form-control"
                value={settings.dc_dc_efficiency}
                onChange={(e) => setSettings({ ...settings, dc_dc_efficiency: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Low-Voltage Auxiliary Bus (V)</label>
              <select
                className="form-control"
                value={settings.bus_voltage_v}
                onChange={(e) => setSettings({ ...settings, bus_voltage_v: e.target.value })}
              >
                <option value="12.0">12V DC Low-Voltage Architecture</option>
                <option value="48.0">48V DC Mild-Hybrid / Auxiliary Bus</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Main Traction Pack Voltage (V)</label>
              <input
                type="number"
                step="1"
                min="200"
                max="900"
                className="form-control"
                value={settings.main_battery_nominal_voltage_v}
                onChange={(e) => setSettings({ ...settings, main_battery_nominal_voltage_v: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Fleet Baseline Consumption (kWh/km)</label>
              <input
                type="number"
                step="0.001"
                className="form-control"
                value={settings.fleet_avg_consumption_kwh_per_km}
                onChange={(e) => setSettings({ ...settings, fleet_avg_consumption_kwh_per_km: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Main Battery Fallback Supply</label>
              <select
                className="form-control"
                value={settings.allow_main_battery_fallback}
                onChange={(e) => setSettings({ ...settings, allow_main_battery_fallback: e.target.value })}
              >
                <option value="true">Allowed (Uninterruptible Supply)</option>
                <option value="false">Disabled (Strict Auxiliary Only)</option>
              </select>
            </div>
          </div>

          <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            <button type="submit" className="btn btn-primary">
              <i className="fa-solid fa-floppy-disk"></i> Save System Settings
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
