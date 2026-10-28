import React, { useState, useEffect } from 'react';
import api from '../services/api';

export default function HistoryTab() {
  const [history, setHistory] = useState([]);
  const [allocationHistory, setAllocationHistory] = useState([]);
  const [activeSubTab, setActiveSubTab] = useState('allocations');
  const [loading, setLoading] = useState(true);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const res = await api.getHistory();
      if (res.success) {
        setHistory(res.history || []);
        setAllocationHistory(res.allocation_history || []);
      }
    } catch (err) {
      console.error('Error fetching history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleClear = async () => {
    if (window.confirm('Clear all power allocation and prediction audit history records?')) {
      try {
        await api.clearHistory();
        setHistory([]);
        setAllocationHistory([]);
      } catch (err) {
        alert('Failed to clear history: ' + err.message);
      }
    }
  };

  return (
    <div>
      <div className="top-header">
        <div className="header-title">
          <h1>Audit History & Event Logs</h1>
          <p>Chronological Database Records for Power Allocation Cycles & ML Energy Predictions</p>
        </div>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={fetchHistory} title="Refresh Logs">
            <i className="fa-solid fa-arrows-rotate"></i> Refresh
          </button>
          {(history.length > 0 || allocationHistory.length > 0) && (
            <button className="btn btn-danger" onClick={handleClear}>
              <i className="fa-solid fa-trash-can"></i> Clear All History
            </button>
          )}
        </div>
      </div>

      {/* Sub-tab selection */}
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem' }}>
        <button
          className={`btn ${activeSubTab === 'allocations' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveSubTab('allocations')}
        >
          <i className="fa-solid fa-network-wired"></i> Power Allocation Events ({allocationHistory.length})
        </button>
        <button
          className={`btn ${activeSubTab === 'predictions' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveSubTab('predictions')}
        >
          <i className="fa-solid fa-brain"></i> ML Energy Predictions ({history.length})
        </button>
      </div>

      <div className="glass-card">
        {loading ? (
          <p style={{ color: 'var(--text-muted)' }}>Loading audit records from database...</p>
        ) : activeSubTab === 'allocations' ? (
          allocationHistory.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
              <i className="fa-solid fa-network-wired" style={{ fontSize: '2.5rem', marginBottom: '1rem', opacity: 0.4 }}></i>
              <p>No power allocation events recorded yet.</p>
              <p style={{ fontSize: '0.8rem', marginTop: '0.5rem' }}>Run the Power Allocation Engine to generate audit logs.</p>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Duration</th>
                    <th>Usable Aux (Wh)</th>
                    <th>Allocated (Wh)</th>
                    <th>Battery Avoided (Wh)</th>
                    <th>Battery Fallback (Wh)</th>
                    <th>Utilization</th>
                  </tr>
                </thead>
                <tbody>
                  {allocationHistory.map((rec) => (
                    <tr key={rec.id}>
                      <td style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>
                        {new Date(rec.timestamp).toLocaleString()}
                      </td>
                      <td>{rec.duration_hours} hr</td>
                      <td>{rec.usable_aux_wh} Wh</td>
                      <td><span style={{ color: 'var(--accent-emerald)', fontWeight: 600 }}>{rec.total_allocated_wh} Wh</span></td>
                      <td><strong style={{ color: 'var(--accent-amber)' }}>{rec.battery_energy_avoided_wh} Wh</strong></td>
                      <td>{rec.main_battery_supplied_wh} Wh</td>
                      <td><span style={{ color: 'var(--accent-cyan)' }}>{rec.utilization_pct}%</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        ) : (
          history.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
              <i className="fa-solid fa-brain" style={{ fontSize: '2.5rem', marginBottom: '1rem', opacity: 0.4 }}></i>
              <p>No trip energy predictions recorded in this session.</p>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Summary</th>
                    <th>Distance</th>
                    <th>Speed</th>
                    <th>Predicted Energy</th>
                    <th>Estimated Range</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((rec, idx) => (
                    <tr key={rec.id || idx}>
                      <td style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>
                        {rec.timestamp || 'Recent'}
                      </td>
                      <td><strong>{rec.summary || rec.type}</strong></td>
                      <td>{rec.distance_km || '-'} km</td>
                      <td>{rec.speed_kmh || '-'} km/h</td>
                      <td>
                        <strong style={{ color: 'var(--accent-cyan)' }}>
                          {rec.predicted_kwh ? `${Number(rec.predicted_kwh).toFixed(2)} kWh` : '-'}
                        </strong>
                      </td>
                      <td>
                        <span style={{ color: 'var(--accent-emerald)' }}>
                          {rec.range_est_km ? `${Number(rec.range_est_km).toFixed(1)} km` : '-'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        )}
      </div>
    </div>
  );
}
