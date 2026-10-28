import React, { useState, useEffect } from 'react';
import api from '../services/api';

export default function AuxiliarySourcesTab() {
  const [sources, setSources] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editingSource, setEditingSource] = useState(null);
  const [formParams, setFormParams] = useState({});
  const [saveMsg, setSaveMsg] = useState(null);

  const fetchSources = async () => {
    try {
      setLoading(true);
      const res = await api.getEnergySources();
      if (res.success) {
        setSources(res.sources);
        setSummary(res.summary);
      }
    } catch (err) {
      console.error('Error fetching sources:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSources();
  }, []);

  const handleToggleEnable = async (source) => {
    try {
      const res = await api.updateEnergySource({
        source_id: source.id,
        enabled: !source.enabled,
        operating_status: !source.enabled ? 'active' : 'disabled'
      });
      if (res.success) {
        fetchSources();
      }
    } catch (err) {
      alert(`Toggle failed: ${err.message}`);
    }
  };

  const handleOpenEdit = (source) => {
    setEditingSource(source);
    setFormParams({ ...(source.parameters || {}), manual_power_w: source.current_power_w });
    setSaveMsg(null);
  };

  const handleSaveParams = async (e) => {
    e.preventDefault();
    if (!editingSource) return;
    try {
      const res = await api.updateEnergySource({
        source_id: editingSource.id,
        enabled: true,
        parameters: formParams
      });
      if (res.success) {
        setSaveMsg('Parameters updated successfully and power re-evaluated!');
        fetchSources();
        setTimeout(() => setEditingSource(null), 1200);
      }
    } catch (err) {
      setSaveMsg(`Error: ${err.message}`);
    }
  };

  return (
    <div>
      <div className="top-header">
        <div className="header-title">
          <h1>Auxiliary Energy Source Monitoring</h1>
          <p>Kinematic Regenerative Braking, Rooftop Solar PV, and Experimental Vibration Harvesters</p>
        </div>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={fetchSources} title="Refresh Telemetry">
            <i className="fa-solid fa-arrows-rotate"></i> Refresh Sources
          </button>
        </div>
      </div>

      {/* Sources Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        {sources.map((s) => (
          <div key={s.id} className="glass-card" style={{ opacity: s.enabled ? 1 : 0.65, borderTop: s.enabled ? '3px solid var(--accent-cyan)' : '3px solid var(--border-glass)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
              <div>
                <span className="badge-pill" style={{
                  color: s.source_type === 'vibration' ? 'var(--accent-purple)' : 'var(--accent-cyan)',
                  borderColor: s.source_type === 'vibration' ? 'var(--border-glow-purple)' : 'var(--border-glow-cyan)'
                }}>
                  {s.source_type.replace('_', ' ').toUpperCase()}
                </span>
                <h3 style={{ fontSize: '1.15rem', marginTop: '0.4rem' }}>{s.name}</h3>
              </div>
              <button
                className={`btn ${s.enabled ? 'btn-danger' : 'btn-primary'}`}
                style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}
                onClick={() => handleToggleEnable(s)}
              >
                {s.enabled ? 'Disable Source' : 'Enable Source'}
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', background: 'rgba(0,0,0,0.25)', padding: '0.85rem', borderRadius: '10px', marginBottom: '1rem' }}>
              <div>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Available Power</span>
                <div style={{ fontSize: '1.4rem', fontWeight: 700, color: s.enabled ? 'var(--accent-cyan)' : 'var(--text-muted)' }}>
                  {s.current_power_w} W
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Total Harvested</span>
                <div style={{ fontSize: '1.4rem', fontWeight: 700, color: s.enabled ? 'var(--accent-emerald)' : 'var(--text-muted)' }}>
                  {s.accumulated_energy_wh} Wh
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Conversion Efficiency</span>
                <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>
                  {(s.efficiency * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Status</span>
                <div style={{ fontSize: '0.9rem', fontWeight: 600, color: s.enabled ? 'var(--accent-emerald)' : 'var(--accent-amber)', textTransform: 'capitalize' }}>
                  {s.operating_status}
                </div>
              </div>
            </div>

            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.35rem', marginBottom: '1rem' }}>
              <div><strong>Method:</strong> <code>{s.measurement_method}</code></div>
              <div><strong>Data Quality:</strong> <span style={{ color: s.data_quality === 'verified_model' ? 'var(--accent-emerald)' : 'var(--accent-amber)' }}>{s.data_quality}</span></div>
              <div><strong>Rated Peak Limit:</strong> {s.rated_power_w} W</div>
            </div>

            <button className="btn btn-secondary" style={{ width: '100%', fontSize: '0.82rem' }} onClick={() => handleOpenEdit(s)}>
              <i className="fa-solid fa-sliders"></i> Tune Physics Parameters & Manual Input
            </button>
          </div>
        ))}
      </div>

      {/* DC-DC Bus Converter Stage Summary */}
      {summary && (
        <div className="glass-card">
          <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <i className="fa-solid fa-bolt" style={{ color: 'var(--accent-amber)' }}></i>
            Auxiliary Power Bus & Converter Aggregation
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.25rem' }}>
            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Total Raw Harvested</span>
              <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{summary.total_generated_w} W</div>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Accumulated: {summary.total_accumulated_wh} Wh</span>
            </div>
            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>DC-DC Converter Stage</span>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                {(summary.dc_dc_efficiency * 100).toFixed(1)}%
              </div>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Synchronous Buck/Boost Stage</span>
            </div>
            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Conversion Thermal Loss</span>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent-red)' }}>
                {summary.conversion_loss_w} W
              </div>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Loss: {summary.conversion_loss_wh} Wh</span>
            </div>
            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Net Usable Power for Loads</span>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent-emerald)' }}>
                {summary.usable_power_w} W
              </div>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Usable: {summary.usable_energy_wh} Wh</span>
            </div>
          </div>
        </div>
      )}

      {/* Parameter Edit Modal */}
      {editingSource && (
        <div className="modal-overlay" onClick={() => setEditingSource(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '600px' }}>
            <button className="modal-close" onClick={() => setEditingSource(null)}>
              <i className="fa-solid fa-xmark"></i>
            </button>
            <h3 style={{ marginBottom: '0.5rem' }}>Tune Source: {editingSource.name}</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '1.25rem' }}>
              Adjust kinematic, solar, or manual input parameters to simulate dynamic operating environments.
            </p>

            <form onSubmit={handleSaveParams}>
              <div className="form-grid">
                {editingSource.id === 'regen' && (
                  <>
                    <div className="form-group">
                      <label className="form-label">Vehicle Speed (km/h)</label>
                      <input
                        type="number"
                        className="form-control"
                        value={formParams.speed_kmh || 55}
                        onChange={(e) => setFormParams({ ...formParams, speed_kmh: Number(e.target.value) })}
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Deceleration (m/s²)</label>
                      <input
                        type="number"
                        step="0.1"
                        className="form-control"
                        value={formParams.deceleration_ms2 || 1.8}
                        onChange={(e) => setFormParams({ ...formParams, deceleration_ms2: Number(e.target.value) })}
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Vehicle Mass (kg)</label>
                      <input
                        type="number"
                        className="form-control"
                        value={formParams.vehicle_mass_kg || 1650}
                        onChange={(e) => setFormParams({ ...formParams, vehicle_mass_kg: Number(e.target.value) })}
                      />
                    </div>
                  </>
                )}

                {editingSource.id === 'solar' && (
                  <>
                    <div className="form-group">
                      <label className="form-label">Solar Irradiance (W/m²)</label>
                      <input
                        type="number"
                        className="form-control"
                        value={formParams.solar_irradiance_wm2 || 750}
                        onChange={(e) => setFormParams({ ...formParams, solar_irradiance_wm2: Number(e.target.value) })}
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Rooftop Panel Area (m²)</label>
                      <input
                        type="number"
                        step="0.05"
                        className="form-control"
                        value={formParams.panel_area_m2 || 1.85}
                        onChange={(e) => setFormParams({ ...formParams, panel_area_m2: Number(e.target.value) })}
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Cell Efficiency (η)</label>
                      <input
                        type="number"
                        step="0.01"
                        className="form-control"
                        value={formParams.cell_efficiency || 0.21}
                        onChange={(e) => setFormParams({ ...formParams, cell_efficiency: Number(e.target.value) })}
                      />
                    </div>
                  </>
                )}

                {editingSource.id === 'vibration' && (
                  <>
                    <div className="form-group">
                      <label className="form-label">Stroke Velocity (m/s)</label>
                      <input
                        type="number"
                        step="0.01"
                        className="form-control"
                        value={formParams.suspension_stroke_velocity_ms || 0.12}
                        onChange={(e) => setFormParams({ ...formParams, suspension_stroke_velocity_ms: Number(e.target.value) })}
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Transducer Efficiency</label>
                      <input
                        type="number"
                        step="0.05"
                        className="form-control"
                        value={formParams.transducer_efficiency || 0.45}
                        onChange={(e) => setFormParams({ ...formParams, transducer_efficiency: Number(e.target.value) })}
                      />
                    </div>
                  </>
                )}

                <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                  <label className="form-label">
                    <span>Direct Manual Power Override (W)</span>
                    <span style={{ color: 'var(--accent-amber)', fontSize: '0.72rem' }}>Demonstration Mode</span>
                  </label>
                  <input
                    type="number"
                    className="form-control"
                    placeholder="Leave blank to use physics model"
                    value={formParams.manual_power_w !== undefined ? formParams.manual_power_w : ''}
                    onChange={(e) => setFormParams({
                      ...formParams,
                      manual_power_w: e.target.value === '' ? null : Number(e.target.value)
                    })}
                  />
                </div>
              </div>

              {saveMsg && <div style={{ color: 'var(--accent-emerald)', fontSize: '0.82rem', marginBottom: '1rem' }}>{saveMsg}</div>}

              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setEditingSource(null)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Apply & Recalculate Power
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
