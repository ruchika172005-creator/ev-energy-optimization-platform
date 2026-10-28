import React, { useState, useEffect } from 'react';
import api from '../services/api';

export default function PowerAllocationTab({ onAllocationUpdated }) {
  const [loads, setLoads] = useState([]);
  const [durationHours, setDurationHours] = useState(1.0);
  const [allowFallback, setAllowFallback] = useState(true);
  const [dcEfficiency, setDcEfficiency] = useState(0.94);
  const [allocationResult, setAllocationResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // New load form modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [newLoad, setNewLoad] = useState({
    id: '',
    name: '',
    category: 'Safety & Control',
    priority: 3,
    power_demand_w: 30,
    voltage_v: 12.0,
    critical: false,
    description: ''
  });

  const fetchLoadsAndRun = async () => {
    try {
      setLoading(true);
      setError(null);
      // Fetch current configured loads
      const loadsRes = await api.getEnergyLoads();
      if (loadsRes.success) {
        setLoads(loadsRes.loads || []);
      }
      // Execute initial allocation
      const allocRes = await api.allocatePower({
        duration_hours: durationHours,
        allow_main_battery_fallback: allowFallback,
        dc_dc_efficiency: dcEfficiency
      });
      if (allocRes.success && allocRes.allocation) {
        setAllocationResult(allocRes.allocation);
        if (onAllocationUpdated) onAllocationUpdated(allocRes.allocation);
      }
    } catch (err) {
      console.error('Error initializing allocation:', err);
      setError(err.message || 'Error communicating with backend server.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLoadsAndRun();
  }, []);

  const handleRunAllocation = async () => {
    setLoading(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await api.allocatePower({
        duration_hours: durationHours,
        allow_main_battery_fallback: allowFallback,
        dc_dc_efficiency: dcEfficiency
      });
      if (res.success && res.allocation) {
        setAllocationResult(res.allocation);
        setSuccessMsg(`Power allocation evaluated successfully over ${durationHours} hr window.`);
        if (onAllocationUpdated) onAllocationUpdated(res.allocation);
        setTimeout(() => setSuccessMsg(null), 3500);
      } else {
        setError(res.error || 'Allocation execution failed');
      }
    } catch (err) {
      setError(err.message || 'Error executing allocation with backend.');
    } finally {
      setLoading(false);
    }
  };

  const handleApplyScenario = async (scenarioId) => {
    setLoading(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await api.runDemoScenario(scenarioId, allowFallback, durationHours);
      if (res.success && res.allocation) {
        setAllocationResult(res.allocation);
        setDcEfficiency(0.94);
        setSuccessMsg(`Applied Evaluation Scenario ${scenarioId}: ${scenarioId === 'A' ? '430W Harvested -> 320W Demand (Surplus)' : '200W Harvested -> 320W Demand (Battery Fallback)'}`);
        // Refresh loads
        const loadsRes = await api.getEnergyLoads();
        if (loadsRes.success) setLoads(loadsRes.loads);
        if (onAllocationUpdated) onAllocationUpdated(res.allocation);
        setTimeout(() => setSuccessMsg(null), 4000);
      } else {
        setError(res.error || `Failed to apply Scenario ${scenarioId}`);
      }
    } catch (err) {
      setError(err.message || `Error applying Scenario ${scenarioId}`);
    } finally {
      setLoading(false);
    }
  };

  const handleResetDefaults = async () => {
    setLoading(true);
    setError(null);
    try {
      await api.resetDemoLoads();
      await handleApplyScenario('A');
      setSuccessMsg('Reset all loads and sources to canonical demonstration baseline (Scenario A).');
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err) {
      setError(err.message || 'Reset failed');
      setLoading(false);
    }
  };

  const handleToggleLoad = async (load) => {
    try {
      await api.saveEnergyLoad({
        ...load,
        enabled: !load.enabled
      });
      const loadsRes = await api.getEnergyLoads();
      if (loadsRes.success) setLoads(loadsRes.loads);
      handleRunAllocation();
    } catch (err) {
      alert(`Toggle failed: ${err.message}`);
    }
  };

  const handleDeleteLoad = async (loadId) => {
    if (window.confirm('Delete this load configuration?')) {
      try {
        await api.deleteEnergyLoad(loadId);
        const loadsRes = await api.getEnergyLoads();
        if (loadsRes.success) setLoads(loadsRes.loads);
        handleRunAllocation();
      } catch (err) {
        alert(`Delete failed: ${err.message}`);
      }
    }
  };

  const handleCreateLoad = async (e) => {
    e.preventDefault();
    if (!newLoad.name) return;
    const loadId = newLoad.id || `load_${Date.now()}`;
    try {
      await api.saveEnergyLoad({
        ...newLoad,
        id: loadId,
        enabled: true
      });
      setShowAddModal(false);
      setNewLoad({
        id: '',
        name: '',
        category: 'Safety & Control',
        priority: 3,
        power_demand_w: 30,
        voltage_v: 12.0,
        critical: false,
        description: ''
      });
      const loadsRes = await api.getEnergyLoads();
      if (loadsRes.success) setLoads(loadsRes.loads);
      handleRunAllocation();
    } catch (err) {
      alert(`Error creating load: ${err.message}`);
    }
  };

  const energyAcc = allocationResult?.energy_accounting || {};
  const rows = allocationResult?.load_allocations || loads.map(l => ({
    load_id: l.id,
    name: l.name,
    category: l.category,
    priority: l.priority,
    critical: l.critical,
    demand_w: l.power_demand_w,
    allocated_aux_w: 0.0,
    battery_supplied_w: allowFallback ? l.power_demand_w : 0.0,
    unmet_w: allowFallback ? 0.0 : l.power_demand_w,
    coverage_pct: 0.0,
    supplied_by: 'Pending Allocation Run'
  }));

  return (
    <div>
      <div className="top-header">
        <div className="header-title">
          <h1>Intelligent Power Allocation Engine</h1>
          <p>Priority-Ranked Matching of Harvested Auxiliary Energy to Low-Voltage Electrical Loads</p>
        </div>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={() => setShowAddModal(true)}>
            <i className="fa-solid fa-plus"></i> Add Eligible Load
          </button>
          <button className="btn btn-secondary" onClick={handleResetDefaults} title="Reset to Canonical 320W Demonstration Loads">
            <i className="fa-solid fa-rotate-left"></i> Reset Demo Baseline
          </button>
          <button className="btn btn-primary" onClick={handleRunAllocation} disabled={loading}>
            <i className={loading ? "fa-solid fa-spinner fa-spin" : "fa-solid fa-bolt"}></i>
            {loading ? 'Evaluating Model...' : 'Re-Run Allocation'}
          </button>
        </div>
      </div>

      {/* Evaluation Scenarios Banner */}
      <div className="glass-card" style={{ marginBottom: '1.5rem', background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.08), rgba(139, 92, 246, 0.06))', border: '1px solid var(--border-glow-cyan)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
              <span className="badge-pill" style={{ color: 'var(--accent-cyan)', borderColor: 'var(--border-glow-cyan)' }}>
                Phase 2 Evaluation Presets
              </span>
              <strong style={{ fontSize: '0.95rem' }}>Quick-Demonstration Scenarios</strong>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Test deterministic mathematical behavior across surplus generation vs. battery fallback deficit.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <button
              className="btn btn-secondary"
              style={{ fontSize: '0.82rem', borderColor: 'var(--accent-emerald)' }}
              onClick={() => handleApplyScenario('A')}
              disabled={loading}
            >
              <i className="fa-solid fa-play" style={{ color: 'var(--accent-emerald)' }}></i>
              Scenario A: 430W Harvest → 320W Demand (Surplus)
            </button>
            <button
              className="btn btn-secondary"
              style={{ fontSize: '0.82rem', borderColor: 'var(--accent-amber)' }}
              onClick={() => handleApplyScenario('B')}
              disabled={loading}
            >
              <i className="fa-solid fa-play" style={{ color: 'var(--accent-amber)' }}></i>
              Scenario B: 200W Harvest → 320W Demand (Battery Fallback)
            </button>
          </div>
        </div>
      </div>

      {/* Notifications */}
      {error && (
        <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid var(--accent-red)', padding: '0.75rem 1rem', borderRadius: '8px', marginBottom: '1.25rem', color: 'var(--accent-red)', fontSize: '0.85rem' }}>
          <i className="fa-solid fa-circle-exclamation" style={{ marginRight: '0.5rem' }}></i>
          {error}
        </div>
      )}

      {successMsg && (
        <div style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid var(--border-glow-emerald)', padding: '0.75rem 1rem', borderRadius: '8px', marginBottom: '1.25rem', color: 'var(--text-emerald)', fontSize: '0.85rem' }}>
          <i className="fa-solid fa-circle-check" style={{ marginRight: '0.5rem' }}></i>
          {successMsg}
        </div>
      )}

      {/* Interactive Controls Bar */}
      <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem', alignItems: 'center' }}>
          <div>
            <label className="form-label">
              <span>Allocation Window (Hours)</span>
              <span style={{ color: 'var(--accent-cyan)' }}>{durationHours} hr ({durationHours * 60} min)</span>
            </label>
            <input
              type="range"
              min="0.25"
              max="5.0"
              step="0.25"
              value={durationHours}
              onChange={(e) => setDurationHours(Number(e.target.value))}
            />
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              Interval T: Energy (Wh) = Power (W) × {durationHours} hr
            </div>
          </div>

          <div>
            <label className="form-label">
              <span>DC-DC Converter Efficiency (η)</span>
              <span style={{ color: 'var(--accent-purple)' }}>{(dcEfficiency * 100).toFixed(0)}%</span>
            </label>
            <input
              type="range"
              min="0.75"
              max="0.99"
              step="0.01"
              value={dcEfficiency}
              onChange={(e) => setDcEfficiency(Number(e.target.value))}
            />
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              Synchronous buck stage to low-voltage bus
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            <label className="form-label">Main Battery Fallback Supply</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginTop: '0.25rem' }}>
              <input
                type="checkbox"
                id="fallback_chk"
                checked={allowFallback}
                onChange={(e) => setAllowFallback(e.target.checked)}
                style={{ width: '18px', height: '18px', cursor: 'pointer' }}
              />
              <label htmlFor="fallback_chk" style={{ fontSize: '0.85rem', cursor: 'pointer', color: allowFallback ? 'var(--accent-emerald)' : 'var(--accent-amber)' }}>
                {allowFallback ? 'Enabled (Supplies Deficit)' : 'Disabled (Tracks Unmet Demand)'}
              </label>
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              {allowFallback ? 'Main battery covers load deficit' : 'Shortfall reported as unmet demand'}
            </div>
          </div>
        </div>
      </div>

      {/* Energy Accounting KPI Banner */}
      {allocationResult && (
        <div className="result-banner" style={{ marginBottom: '1.5rem' }}>
          <div className="result-item">
            <span className="result-label">Available Source Power</span>
            <span className="result-value" style={{ color: 'var(--accent-cyan)' }}>
              {energyAcc.total_generated_w} <small style={{ fontSize: '0.9rem' }}>W</small>
            </span>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
              Energy: {energyAcc.total_generated_wh} Wh
            </span>
          </div>

          <div className="result-item">
            <span className="result-label">Usable Power (Post-Loss)</span>
            <span className="result-value" style={{ color: 'var(--accent-purple)' }}>
              {energyAcc.usable_aux_w} <small style={{ fontSize: '0.9rem' }}>W</small>
            </span>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
              Loss: {energyAcc.conversion_loss_w} W ({energyAcc.conversion_loss_wh} Wh)
            </span>
          </div>

          <div className="result-item">
            <span className="result-label">Aux Power Allocated</span>
            <span className="result-value" style={{ color: 'var(--accent-emerald)' }}>
              {energyAcc.total_allocated_w} <small style={{ fontSize: '0.9rem' }}>W</small>
            </span>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
              Avoided: {energyAcc.battery_energy_avoided_wh} Wh
            </span>
          </div>

          <div className="result-item">
            <span className="result-label">Battery Fallback Draw</span>
            <span className="result-value" style={{ color: energyAcc.main_battery_supplied_w > 0 ? 'var(--accent-amber)' : 'var(--text-muted)' }}>
              {energyAcc.main_battery_supplied_w} <small style={{ fontSize: '0.9rem' }}>W</small>
            </span>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
              Fallback Energy: {energyAcc.main_battery_supplied_wh} Wh
            </span>
          </div>

          <div className="result-item">
            <span className="result-label">
              {energyAcc.unmet_demand_w > 0 ? 'Unmet Load Demand' : 'Surplus Aux Power'}
            </span>
            <span className="result-value" style={{ color: energyAcc.unmet_demand_w > 0 ? 'var(--accent-red)' : 'var(--accent-cyan)' }}>
              {energyAcc.unmet_demand_w > 0 ? `${energyAcc.unmet_demand_w} W` : `${energyAcc.surplus_aux_w} W`}
            </span>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
              {energyAcc.unmet_demand_w > 0 ? `Deficit: ${energyAcc.unmet_demand_wh} Wh` : `Surplus: ${energyAcc.surplus_aux_wh} Wh`}
            </span>
          </div>
        </div>
      )}

      {/* Allocation Breakdown Table */}
      <div className="glass-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <i className="fa-solid fa-list-check" style={{ color: 'var(--accent-cyan)' }}></i>
            Prioritized Load Allocation Matrix ({rows.length} Configured Loads)
          </h3>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Sorted strictly by Priority (1 = Critical Safety First)
          </span>
        </div>

        <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr>
                <th>Priority</th>
                <th>Load Name & Category</th>
                <th>Demand (W)</th>
                <th>Allocated from Aux (W)</th>
                <th>Main Battery Draw (W)</th>
                <th>Aux Coverage</th>
                <th>Supply Source</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
                    <i className="fa-solid fa-spinner fa-spin" style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}></i>
                    <div>Evaluating priority allocation engine...</div>
                  </td>
                </tr>
              ) : rows.length === 0 ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
                    <i className="fa-solid fa-plug-circle-xmark" style={{ fontSize: '2rem', marginBottom: '0.75rem', opacity: 0.5 }}></i>
                    <div>No loads currently configured. Click "Reset Demo Baseline" to restore default loads.</div>
                  </td>
                </tr>
              ) : (
                rows.map((la) => {
                  const coverage = typeof la.coverage_pct === 'number' ? la.coverage_pct : 0;
                  return (
                    <tr key={la.load_id}>
                      <td>
                        <span className="badge-pill" style={{
                          borderColor: la.priority === 1 ? 'var(--border-glow-cyan)' : 'var(--border-glass)',
                          color: la.priority === 1 ? 'var(--accent-cyan)' : 'var(--text-secondary)'
                        }}>
                          Priority {la.priority} {la.critical ? '(Critical)' : ''}
                        </span>
                      </td>
                      <td>
                        <strong>{la.name}</strong>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{la.category}</div>
                      </td>
                      <td>
                        <strong>{la.demand_w} W</strong>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{(la.demand_w * durationHours).toFixed(1)} Wh</div>
                      </td>
                      <td>
                        <span style={{ color: 'var(--accent-emerald)', fontWeight: 600 }}>
                          {la.allocated_aux_w} W
                        </span>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{(la.allocated_aux_w * durationHours).toFixed(1)} Wh</div>
                      </td>
                      <td>
                        <span style={{ color: la.battery_supplied_w > 0 ? 'var(--accent-amber)' : 'var(--text-muted)', fontWeight: la.battery_supplied_w > 0 ? 600 : 400 }}>
                          {la.battery_supplied_w} W
                        </span>
                        {la.battery_supplied_w > 0 && (
                          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{(la.battery_supplied_w * durationHours).toFixed(1)} Wh</div>
                        )}
                        {la.unmet_w > 0 && (
                          <div style={{ fontSize: '0.72rem', color: 'var(--accent-red)', fontWeight: 600 }}>Unmet: {la.unmet_w} W</div>
                        )}
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <div style={{ flex: 1, height: '6px', minWidth: '60px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                            <div style={{ width: `${Math.min(100, coverage)}%`, height: '100%', background: coverage >= 100 ? 'var(--accent-emerald)' : (coverage > 0 ? 'var(--accent-amber)' : 'rgba(255,255,255,0.2)') }}></div>
                          </div>
                          <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>{coverage}%</span>
                        </div>
                      </td>
                      <td>
                        <span className="badge-pill" style={{
                          borderColor: la.supplied_by.includes('100%') ? 'var(--border-glow-emerald)' : (la.supplied_by.includes('Unmet') ? 'rgba(239, 68, 68, 0.4)' : 'var(--border-glass)'),
                          color: la.supplied_by.includes('100%') ? 'var(--accent-emerald)' : (la.supplied_by.includes('Unmet') ? 'var(--accent-red)' : 'var(--accent-amber)')
                        }}>
                          {la.supplied_by}
                        </span>
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: '0.4rem' }}>
                          <button
                            className="btn btn-secondary"
                            style={{ padding: '0.25rem 0.5rem', fontSize: '0.72rem' }}
                            onClick={() => {
                              const original = loads.find(x => x.id === la.load_id);
                              if (original) handleToggleLoad(original);
                            }}
                            title="Toggle Load Enabled/Disabled"
                          >
                            <i className="fa-solid fa-power-off"></i>
                          </button>
                          <button
                            className="btn btn-danger"
                            style={{ padding: '0.25rem 0.5rem', fontSize: '0.72rem' }}
                            onClick={() => handleDeleteLoad(la.load_id)}
                            title="Delete Load"
                          >
                            <i className="fa-solid fa-trash"></i>
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Load Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '540px' }}>
            <button className="modal-close" onClick={() => setShowAddModal(false)}>
              <i className="fa-solid fa-xmark"></i>
            </button>
            <h3 style={{ marginBottom: '1rem' }}>Configure New Auxiliary Load</h3>
            <form onSubmit={handleCreateLoad}>
              <div className="form-grid">
                <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                  <label className="form-label">Load Name</label>
                  <input
                    type="text"
                    className="form-control"
                    required
                    placeholder="e.g. Ultrasonic Proximity Sensors"
                    value={newLoad.name}
                    onChange={(e) => setNewLoad({ ...newLoad, name: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Category</label>
                  <select
                    className="form-control"
                    value={newLoad.category}
                    onChange={(e) => setNewLoad({ ...newLoad, category: e.target.value })}
                  >
                    <option value="Safety & Control">Safety & Control</option>
                    <option value="Connectivity">Connectivity</option>
                    <option value="Thermal Management">Thermal Management</option>
                    <option value="Cockpit & UI">Cockpit & UI</option>
                    <option value="Infotainment">Infotainment</option>
                    <option value="Convenience">Convenience</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Priority (1 = Highest)</label>
                  <select
                    className="form-control"
                    value={newLoad.priority}
                    onChange={(e) => setNewLoad({ ...newLoad, priority: Number(e.target.value) })}
                  >
                    <option value="1">Priority 1 (Critical Safety & ECU)</option>
                    <option value="2">Priority 2 (Essential Comms & V2X)</option>
                    <option value="3">Priority 3 (Thermal Coolant Pump)</option>
                    <option value="4">Priority 4 (Cockpit & Infotainment)</option>
                    <option value="5">Priority 5 (Accessories & Non-critical)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Power Demand (Watts)</label>
                  <input
                    type="number"
                    className="form-control"
                    required
                    min="1"
                    max="500"
                    value={newLoad.power_demand_w}
                    onChange={(e) => setNewLoad({ ...newLoad, power_demand_w: Number(e.target.value) })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Bus Voltage (V)</label>
                  <input
                    type="number"
                    className="form-control"
                    value={newLoad.voltage_v}
                    onChange={(e) => setNewLoad({ ...newLoad, voltage_v: Number(e.target.value) })}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowAddModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Save Load to System
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
