import React, { useState, useEffect } from 'react';
import api from '../services/api';

export default function BatteryImpactTab() {
  const [impactData, setImpactData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchImpact = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getBatteryImpact();
      if (res.success && res.impact) {
        setImpactData(res.impact);
      }
    } catch (err) {
      console.error('Error fetching battery impact:', err);
      setError(err.message || 'Error communicating with backend');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchImpact();
  }, []);

  const session = impactData?.session_impact || {};
  const cumulative = impactData?.cumulative_impact || {};
  const notes = impactData?.engineering_notes || [];

  return (
    <div>
      <div className="top-header">
        <div className="header-title">
          <h1>Traction Battery Impact & Conservation Analysis</h1>
          <p>Evidence-Based High-Voltage Battery Relief, Range Parity Equivalence & Electrochemical Cycling Disclaimers</p>
        </div>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={fetchImpact} disabled={loading}>
            <i className={loading ? "fa-solid fa-spinner fa-spin" : "fa-solid fa-arrows-rotate"}></i> Refresh Impact
          </button>
        </div>
      </div>

      {error && (
        <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid var(--accent-red)', padding: '0.75rem 1rem', borderRadius: '8px', marginBottom: '1.5rem', color: 'var(--accent-red)' }}>
          {error}
        </div>
      )}

      {/* Primary KPI Grid */}
      <div className="stat-grid" style={{ marginBottom: '2rem' }}>
        <div className="glass-card stat-card">
          <div className="stat-header">
            <span>Direct Battery Energy Avoided</span>
            <i className="fa-solid fa-car-battery stat-icon" style={{ color: 'var(--accent-emerald)' }}></i>
          </div>
          <div className="stat-value" style={{ color: 'var(--accent-emerald)' }}>
            {session.battery_energy_avoided_wh || 0.0} <small style={{ fontSize: '1rem' }}>Wh</small>
          </div>
          <div className="stat-subtext">
            Preserved: {session.battery_energy_avoided_kwh || 0.0} kWh from main pack
          </div>
        </div>

        <div className="glass-card stat-card">
          <div className="stat-header">
            <span>Equivalent Range Conserved</span>
            <i className="fa-solid fa-road stat-icon" style={{ color: 'var(--accent-cyan)' }}></i>
          </div>
          <div className="stat-value" style={{ color: 'var(--accent-cyan)' }}>
            ~{session.equivalent_range_conserved_km || 0.0} <small style={{ fontSize: '1rem' }}>km</small>
          </div>
          <div className="stat-subtext">
            Baseline: {session.fleet_baseline_consumption_kwh_100km || 22.1} kWh / 100km
          </div>
        </div>

        <div className="glass-card stat-card">
          <div className="stat-header">
            <span>Ampere-Hour Throughput Avoided</span>
            <i className="fa-solid fa-atom stat-icon" style={{ color: 'var(--accent-purple)' }}></i>
          </div>
          <div className="stat-value" style={{ color: 'var(--accent-purple)' }}>
            {session.ah_throughput_avoided || 0.0} <small style={{ fontSize: '1rem' }}>Ah</small>
          </div>
          <div className="stat-subtext">
            Illustrative: V_nominal = {session.pack_nominal_voltage_v || 360} V
          </div>
        </div>

        <div className="glass-card stat-card">
          <div className="stat-header">
            <span>State-of-Charge (SoC) Preserved</span>
            <i className="fa-solid fa-battery-half stat-icon" style={{ color: 'var(--accent-amber)' }}></i>
          </div>
          <div className="stat-value" style={{ color: 'var(--accent-amber)' }}>
            +{session.soc_preserved_pct || 0.0}%
          </div>
          <div className="stat-subtext">
            On {session.pack_nominal_capacity_kwh || 50} kWh usable pack capacity
          </div>
        </div>
      </div>

      {/* Mathematical Formulation & Explicit Assumptions Card */}
      <div className="glass-card" style={{ marginBottom: '2rem' }}>
        <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <i className="fa-solid fa-calculator" style={{ color: 'var(--accent-cyan)' }}></i>
          Range Equivalence Calculation Formula & Baseline Assumptions
        </h3>

        <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1.25rem', borderRadius: '12px', border: '1px solid var(--border-glass)', marginBottom: '1.25rem' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.95rem', color: 'var(--accent-cyan)', marginBottom: '0.5rem' }}>
            Equivalent_Range_km = Battery_Energy_Avoided_kWh / Baseline_Consumption_Rate
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Equivalent_Range_km = ({session.battery_energy_avoided_kwh || 'E_avoided'} kWh) / (0.2215 kWh/km) = ~{session.equivalent_range_conserved_km || '0.0'} km
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
          <div style={{ padding: '0.75rem', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
            <strong style={{ color: 'var(--text-primary)', display: 'block', marginBottom: '0.25rem' }}>Baseline Fleet Consumption:</strong>
            Fixed at <strong>0.2215 kWh/km (22.15 kWh/100km)</strong> derived from empirical statistical profiling of the 10,151 vehicle trips dataset (cleaned_ev_data.csv).
          </div>
          <div style={{ padding: '0.75rem', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
            <strong style={{ color: 'var(--text-primary)', display: 'block', marginBottom: '0.25rem' }}>Calculated Parity (Not Road Test):</strong>
            This metric represents calculated energy parity. It demonstrates how much vehicle propulsion energy was spared by auxiliary harvesting; it is not a physical chassis dynamometer measurement.
          </div>
        </div>
      </div>

      {/* Cumulative Impact & Disclaimers */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
        <div className="glass-card">
          <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <i className="fa-solid fa-chart-line" style={{ color: 'var(--accent-emerald)' }}></i>
            Multi-Session Cumulative Impact Log
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.85rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0', borderBottom: '1px solid var(--border-glass)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Recorded Allocation Events:</span>
              <strong>{cumulative.total_allocation_cycles || 1}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0', borderBottom: '1px solid var(--border-glass)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Cumulative Energy Spared:</span>
              <strong style={{ color: 'var(--accent-emerald)' }}>
                {cumulative.cumulative_avoided_wh || 0.0} Wh ({cumulative.cumulative_avoided_kwh || 0.0} kWh)
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0', borderBottom: '1px solid var(--border-glass)' }}>
              <span style={{ color: 'var(--text-muted)' }}>Cumulative Range Parity:</span>
              <strong style={{ color: 'var(--accent-cyan)' }}>
                +{cumulative.cumulative_range_conserved_km || 0.0} km
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0' }}>
              <span style={{ color: 'var(--text-muted)' }}>Mean Auxiliary Utilization:</span>
              <strong>{cumulative.mean_auxiliary_utilization_pct || 0.0}%</strong>
            </div>
          </div>
        </div>

        <div className="glass-card">
          <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <i className="fa-solid fa-triangle-exclamation" style={{ color: 'var(--accent-amber)' }}></i>
            Engineering Methodology Disclaimers
          </h3>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.65rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            <li style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
              <i className="fa-solid fa-circle-check" style={{ color: 'var(--accent-emerald)', marginTop: '0.2rem' }}></i>
              <span><strong>Auxiliary Energy Avoided:</strong> Calculated directly from usable auxiliary power channeled to eligible loads, verified by strict energy conservation.</span>
            </li>
            <li style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
              <i className="fa-solid fa-info-circle" style={{ color: 'var(--accent-amber)', marginTop: '0.2rem' }}></i>
              <span><strong>Degradation Claims:</strong> Reduced Ah throughput and Joule heating are illustrative operational models. Numerical battery lifespan extensions cannot be claimed without accelerated electrochemical cycling validation.</span>
            </li>
            <li style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
              <i className="fa-solid fa-info-circle" style={{ color: 'var(--accent-cyan)', marginTop: '0.2rem' }}></i>
              <span><strong>Hardware Boundary:</strong> Direct vehicle battery management requires high-voltage contactor isolation, CAN bus integration, and AEC-Q100 automotive grade microcontrollers.</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
