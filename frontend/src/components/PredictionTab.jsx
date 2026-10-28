import React, { useState } from 'react';
import api from '../services/api';

export default function PredictionTab({ onPredictionLogged }) {
  const [formData, setFormData] = useState({
    speed: 55,
    distance: 25,
    ambient_temp: 18,
    heating: 0,
    ac: 1,
    cabin_temp: 21,
    battery_capacity: 50,
    soc: 85,
    payload: 150,
    elevation_diff: 20,
    driving_style: 'normal'
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'number' ? Number(value) : value
    }));
  };

  const handlePredict = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.predictTrip(formData);
      if (res.success) {
        setResult(res);
        if (onPredictionLogged) onPredictionLogged();
      } else {
        setError(res.error || 'Prediction failed');
      }
    } catch (err) {
      setError(err.message || 'Error communicating with backend server.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="top-header">
        <div className="header-title">
          <h1>Trip Energy Consumption Predictor</h1>
          <p>Real-Time Inference using Trained Scikit-Learn Gradient Boosting Pipeline</p>
        </div>
      </div>

      <div className="glass-card" style={{ marginBottom: '2rem' }}>
        <form onSubmit={handlePredict}>
          <div className="form-grid">
            <div className="form-group">
              <label className="form-label">
                <span>Average Speed</span>
                <span style={{ color: 'var(--accent-cyan)' }}>{formData.speed} km/h</span>
              </label>
              <input
                type="number"
                name="speed"
                className="form-control"
                value={formData.speed}
                min="5"
                max="160"
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">
                <span>Trip Distance</span>
                <span style={{ color: 'var(--accent-cyan)' }}>{formData.distance} km</span>
              </label>
              <input
                type="number"
                name="distance"
                step="0.1"
                className="form-control"
                value={formData.distance}
                min="0.5"
                max="500"
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">
                <span>Ambient Temperature</span>
                <span style={{ color: 'var(--accent-amber)' }}>{formData.ambient_temp} °C</span>
              </label>
              <input
                type="number"
                name="ambient_temp"
                className="form-control"
                value={formData.ambient_temp}
                min="-25"
                max="50"
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">
                <span>Cabin Target Temp</span>
                <span>{formData.cabin_temp} °C</span>
              </label>
              <input
                type="number"
                name="cabin_temp"
                className="form-control"
                value={formData.cabin_temp}
                min="16"
                max="30"
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label className="form-label">
                <span>Cabin Heating</span>
              </label>
              <select name="heating" className="form-control" value={formData.heating} onChange={handleChange}>
                <option value="0">Off (0 kW)</option>
                <option value="1">On (~2.5 - 5 kW)</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">
                <span>Air Conditioning (A/C)</span>
              </label>
              <select name="ac" className="form-control" value={formData.ac} onChange={handleChange}>
                <option value="0">Off (0 kW)</option>
                <option value="1">On (~1.5 - 3 kW)</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">
                <span>Battery Pack Capacity</span>
                <span>{formData.battery_capacity} kWh</span>
              </label>
              <input
                type="number"
                name="battery_capacity"
                className="form-control"
                value={formData.battery_capacity}
                min="15"
                max="150"
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label className="form-label">
                <span>Current State of Charge (SoC)</span>
                <span style={{ color: 'var(--accent-emerald)' }}>{formData.soc} %</span>
              </label>
              <input
                type="number"
                name="soc"
                className="form-control"
                value={formData.soc}
                min="5"
                max="100"
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label className="form-label">
                <span>Payload (Passengers + Cargo)</span>
                <span>{formData.payload} kg</span>
              </label>
              <input
                type="number"
                name="payload"
                className="form-control"
                value={formData.payload}
                min="0"
                max="800"
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label className="form-label">
                <span>Elevation Gain / Loss</span>
                <span>{formData.elevation_diff} m</span>
              </label>
              <input
                type="number"
                name="elevation_diff"
                className="form-control"
                value={formData.elevation_diff}
                min="-1500"
                max="1500"
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label className="form-label">
                <span>Driving Style</span>
              </label>
              <select name="driving_style" className="form-control" value={formData.driving_style} onChange={handleChange}>
                <option value="normal">Normal / Balanced</option>
                <option value="eco">Eco-Conscious Smooth</option>
                <option value="aggressive">Aggressive Dynamic</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              <i className={loading ? "fa-solid fa-spinner fa-spin" : "fa-solid fa-calculator"}></i>
              {loading ? 'Evaluating Model...' : 'Calculate Predicted Energy & Range'}
            </button>
            {error && <span style={{ color: 'var(--accent-red)', fontSize: '0.85rem' }}>{error}</span>}
          </div>
        </form>
      </div>

      {/* Results Display */}
      {result && (
        <div className="glass-card" style={{ animation: 'fadeIn 0.3s ease' }}>
          <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <i className="fa-solid fa-chart-pie" style={{ color: 'var(--accent-emerald)' }}></i>
            Prediction Output & Range Breakdown
          </h3>

          <div className="result-banner">
            <div className="result-item">
              <span className="result-label">Predicted Trip Energy</span>
              <span className="result-value">
                {result.prediction.predicted_energy_kwh.toFixed(2)} <small style={{ fontSize: '1.1rem' }}>kWh</small>
              </span>
            </div>

            <div className="result-item">
              <span className="result-label">Consumption Rate</span>
              <span className="result-value" style={{ color: 'var(--accent-emerald)' }}>
                {result.prediction.consumption_kwh_per_100km.toFixed(1)} <small style={{ fontSize: '1.1rem' }}>kWh/100km</small>
              </span>
            </div>

            {result.range_estimation && (
              <div className="result-item">
                <span className="result-label">Estimated Remaining Range</span>
                <span className="result-value" style={{ color: 'var(--accent-amber)' }}>
                  {result.range_estimation.estimated_range_km.toFixed(1)} <small style={{ fontSize: '1.1rem' }}>km</small>
                </span>
              </div>
            )}

            {result.range_estimation && (
              <div className="result-item">
                <span className="result-label">SoC After Trip</span>
                <span className="result-value" style={{ color: 'var(--accent-purple)' }}>
                  {result.range_estimation.final_soc_pct.toFixed(1)} <small style={{ fontSize: '1.1rem' }}>%</small>
                </span>
              </div>
            )}
          </div>

          {/* Feature Importances */}
          {result.prediction.feature_importances && (
            <div style={{ marginTop: '2rem' }}>
              <h4 style={{ fontSize: '0.92rem', marginBottom: '1rem', color: 'var(--text-secondary)' }}>
                Top Contributing Feature Importances (GradientBoosting)
              </h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.75rem' }}>
                {Object.entries(result.prediction.feature_importances).slice(0, 6).map(([feat, val]) => (
                  <div key={feat} style={{ background: 'rgba(255,255,255,0.03)', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: '0.35rem' }}>
                      <span style={{ color: 'var(--text-primary)', textTransform: 'capitalize' }}>{feat.replace(/_/g, ' ')}</span>
                      <strong style={{ color: 'var(--accent-cyan)' }}>{(Number(val) * 100).toFixed(1)}%</strong>
                    </div>
                    <div style={{ width: '100%', height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', overflow: 'hidden' }}>
                      <div style={{ width: `${Math.min(100, Number(val) * 100 * 1.5)}%`, height: '100%', background: 'var(--accent-cyan)' }}></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
