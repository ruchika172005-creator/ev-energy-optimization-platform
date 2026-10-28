import React, { useState, useEffect } from 'react';
import api from '../services/api';

export default function EnergyFlowTab() {
  const [summary, setSummary] = useState(null);
  const [allocation, setAllocation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const sumRes = await api.getEnergySummary();
      if (sumRes.success) {
        setSummary(sumRes);
        if (sumRes.last_allocation && sumRes.last_allocation.load_allocations && sumRes.last_allocation.load_allocations.length > 0) {
          setAllocation(sumRes.last_allocation);
        } else {
          // If no allocation was run yet, execute allocation to populate data
          const allocRes = await api.allocatePower({ duration_hours: 1.0, allow_main_battery_fallback: true });
          if (allocRes.success) {
            setAllocation(allocRes.allocation);
          }
        }
      }
    } catch (err) {
      console.error('Error loading energy flow data:', err);
      setError(err.message || 'Error communicating with backend');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const sources = summary?.sources_summary?.sources || allocation?.active_sources || [];
  const energyAcc = allocation?.energy_accounting || summary?.last_allocation?.energy_accounting || {};
  const loads = allocation?.load_allocations || [];
  const duration = allocation?.duration_hours || 1.0;

  return (
    <div>
      <div className="top-header">
        <div className="header-title">
          <h1>Energy Flow & Subsystem Power Path</h1>
          <p>End-to-End Power Path: Source Input → DC-DC Conversion Losses → Usable Auxiliary Power → Load Allocations → Battery Fallback / Surplus</p>
        </div>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={loadData} disabled={loading}>
            <i className={loading ? "fa-solid fa-spinner fa-spin" : "fa-solid fa-arrows-rotate"}></i> Refresh Flow
          </button>
        </div>
      </div>

      {error && (
        <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid var(--accent-red)', padding: '0.75rem 1rem', borderRadius: '8px', marginBottom: '1.5rem', color: 'var(--accent-red)' }}>
          {error}
        </div>
      )}

      {/* Visual Energy Flow Schematic (W and Wh) */}
      <div className="glass-card" style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <i className="fa-solid fa-arrows-split-up-and-left" style={{ color: 'var(--accent-cyan)' }}></i>
            End-to-End Power & Energy Flow Path
          </h3>
          <span className="badge-pill" style={{ color: 'var(--accent-purple)', borderColor: 'var(--border-glow-purple)' }}>
            Interval T = {duration} hour ({duration * 60} min)
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.5rem', alignItems: 'stretch' }}>
          {/* Stage 1: Harvesting Sources */}
          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1.25rem', borderRadius: '14px', border: '1px solid var(--border-glow-cyan)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.75rem' }}>
                Stage 1: Harvested Sources
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                {sources.map(s => (
                  <div key={s.id} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', padding: '0.35rem 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                    <span>{s.name.split(' ')[0]} {s.name.split(' ')[1]}</span>
                    <div style={{ textAlign: 'right' }}>
                      <strong style={{ color: s.enabled ? 'var(--accent-cyan)' : 'var(--text-muted)' }}>
                        {s.current_power_w} W
                      </strong>
                      <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                        {(s.current_power_w * duration).toFixed(1)} Wh
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: '0.75rem', borderTop: '1px solid var(--border-glass)', fontWeight: 700, marginTop: '0.75rem' }}>
              <span>Total Harvested:</span>
              <div style={{ textAlign: 'right' }}>
                <span style={{ color: 'var(--accent-cyan)' }}>{energyAcc.total_generated_w || 430.0} W</span>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                  {energyAcc.total_generated_wh || 430.0} Wh
                </div>
              </div>
            </div>
          </div>

          {/* Stage 2: Converter Stage */}
          <div style={{ textAlign: 'center', background: 'rgba(0,0,0,0.3)', padding: '1.25rem', borderRadius: '14px', border: '1px solid var(--border-glass)', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--accent-purple)', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.5rem' }}>
              Stage 2: DC-DC Conversion Stage
            </div>
            <div style={{ fontSize: '1.9rem', fontWeight: 800, color: 'var(--accent-purple)', marginBottom: '0.1rem' }}>
              {((energyAcc.dc_dc_efficiency || 0.94) * 100).toFixed(0)}%
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>Synchronous Buck to 12V Bus</div>
            <div style={{ background: 'rgba(239, 68, 68, 0.1)', color: 'var(--accent-red)', padding: '0.4rem 0.8rem', borderRadius: '6px', fontSize: '0.78rem', width: '100%', marginBottom: '0.6rem' }}>
              Conversion Loss: <strong>{energyAcc.conversion_loss_w || 25.8} W</strong> ({energyAcc.conversion_loss_wh || 25.8} Wh)
            </div>
            <div style={{ color: 'var(--accent-emerald)', fontWeight: 700, fontSize: '0.9rem' }}>
              Usable Aux: {energyAcc.usable_aux_w || 404.2} W ({energyAcc.usable_aux_wh || 404.2} Wh)
            </div>
          </div>

          {/* Stage 3: Low-Voltage Loads & Fallback */}
          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1.25rem', borderRadius: '14px', border: '1px solid var(--border-glow-emerald)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--accent-emerald)', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.75rem' }}>
                Stage 3: Subsystem Supply
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.82rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Auxiliary Supplied:</span>
                  <strong style={{ color: 'var(--accent-emerald)' }}>
                    {energyAcc.total_allocated_w || 320.0} W ({energyAcc.total_allocated_wh || 320.0} Wh)
                  </strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Main Battery Fallback:</span>
                  <strong style={{ color: energyAcc.main_battery_supplied_w > 0 ? 'var(--accent-amber)' : 'var(--text-muted)' }}>
                    {energyAcc.main_battery_supplied_w || 0.0} W ({energyAcc.main_battery_supplied_wh || 0.0} Wh)
                  </strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Surplus Auxiliary:</span>
                  <strong style={{ color: 'var(--accent-cyan)' }}>
                    {energyAcc.surplus_aux_w || 0.0} W ({energyAcc.surplus_aux_wh || 0.0} Wh)
                  </strong>
                </div>
                {energyAcc.unmet_demand_w > 0 && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--accent-red)' }}>
                    <span>Unmet Deficit:</span>
                    <strong>{energyAcc.unmet_demand_w} W ({energyAcc.unmet_demand_wh} Wh)</strong>
                  </div>
                )}
              </div>
            </div>
            <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '0.75rem', display: 'flex', justifyContent: 'space-between', fontWeight: 700, marginTop: '0.75rem' }}>
              <span>Total Demand:</span>
              <div style={{ textAlign: 'right' }}>
                <span>{energyAcc.total_demand_w || 320.0} W</span>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                  {energyAcc.total_demand_wh || 320.0} Wh
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Surplus Status Explanation Callout */}
        <div style={{ marginTop: '1.25rem', padding: '0.75rem 1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px solid var(--border-glass)', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
          <i className="fa-solid fa-circle-info" style={{ color: 'var(--accent-cyan)', marginRight: '0.5rem' }}></i>
          <strong>Surplus Energy Accounting Note: </strong>
          {energyAcc.surplus_status_note || "Surplus usable auxiliary energy is unallocated and left idle; no low-voltage battery storage buffer is configured in this vehicle circuit model. Surplus is not back-fed into the high-voltage pack without validated bidirectional charger hardware."}
        </div>
      </div>

      {/* Category Distribution Breakdown (Populated from Actual Allocation Results) */}
      <div className="glass-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <i className="fa-solid fa-chart-pie" style={{ color: 'var(--accent-cyan)' }}></i>
            Electrical Subsystem Power Allocation Distribution ({loads.length} Loads Active)
          </h3>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Real-time allocations matching current source & priority state
          </span>
        </div>

        {loading ? (
          <p style={{ color: 'var(--text-muted)', padding: '1.5rem', textAlign: 'center' }}>Loading load distribution data...</p>
        ) : loads.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
            <i className="fa-solid fa-plug" style={{ fontSize: '1.8rem', marginBottom: '0.5rem', opacity: 0.5 }}></i>
            <p>No active load allocations recorded. Navigate to "Intelligent Power Allocation" to configure loads and run the allocation engine.</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
            {loads.map(la => {
              const coverage = typeof la.coverage_pct === 'number' ? la.coverage_pct : 0;
              return (
                <div key={la.load_id} style={{ background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: '10px', border: '1px solid var(--border-glass)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>{la.name}</span>
                    <span className="badge-pill" style={{ fontSize: '0.65rem' }}>
                      P{la.priority} {la.critical ? '• Critical' : ''}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '0.6rem' }}>
                    {la.category} | Demand: <strong>{la.demand_w} W</strong> ({(la.demand_w * duration).toFixed(1)} Wh)
                  </div>

                  {/* Progress Bar */}
                  <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.08)', borderRadius: '4px', overflow: 'hidden', display: 'flex', marginBottom: '0.4rem' }}>
                    <div style={{ width: `${Math.min(100, coverage)}%`, height: '100%', background: 'var(--accent-emerald)' }} title={`Aux: ${la.allocated_aux_w} W`}></div>
                    {la.battery_supplied_w > 0 && (
                      <div style={{ width: `${Math.min(100, 100 - coverage)}%`, height: '100%', background: 'var(--accent-amber)' }} title={`Main Battery: ${la.battery_supplied_w} W`}></div>
                    )}
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
                    <span>Aux: <strong style={{ color: 'var(--accent-emerald)' }}>{la.allocated_aux_w} W</strong></span>
                    <span>Battery: <strong style={{ color: la.battery_supplied_w > 0 ? 'var(--accent-amber)' : 'var(--text-muted)' }}>{la.battery_supplied_w} W</strong></span>
                    <span>Coverage: <strong>{coverage}%</strong></span>
                  </div>

                  <div style={{ marginTop: '0.5rem', textAlign: 'right' }}>
                    <span className="badge-pill" style={{
                      fontSize: '0.65rem',
                      borderColor: la.supplied_by.includes('100%') ? 'var(--border-glow-emerald)' : 'var(--border-glass)',
                      color: la.supplied_by.includes('100%') ? 'var(--accent-emerald)' : (la.supplied_by.includes('Unmet') ? 'var(--accent-red)' : 'var(--accent-amber)')
                    }}>
                      {la.supplied_by}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
