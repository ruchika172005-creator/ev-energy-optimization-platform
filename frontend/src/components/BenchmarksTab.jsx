import React, { useState, useEffect } from 'react';
import api from '../services/api';

export default function BenchmarksTab() {
  const [metricsData, setMetricsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchBenchmarks() {
      try {
        setLoading(true);
        const res = await api.getModelBenchmarks();
        if (res.success && res.metrics) {
          setMetricsData(res.metrics);
        } else {
          setError(res.error || 'Failed to retrieve model metrics');
        }
      } catch (err) {
        setError(err.message || 'Error communicating with backend');
      } finally {
        setLoading(false);
      }
    }
    fetchBenchmarks();
  }, []);

  // Actual recorded experimental evaluation results from regression_model_results.csv
  const models = metricsData?.models || [
    { model_name: 'Gradient Boosting Regressor', mae_kwh: 0.6792, rmse_kwh: 1.0216, r2_score: 0.8713, variance_explained_pct: 87.13 },
    { model_name: 'Random Forest Regressor', mae_kwh: 0.6945, rmse_kwh: 1.0598, r2_score: 0.8615, variance_explained_pct: 86.15 },
    { model_name: 'Linear Regression', mae_kwh: 0.7562, rmse_kwh: 1.1316, r2_score: 0.8421, variance_explained_pct: 84.21 }
  ];

  return (
    <div>
      <div className="top-header">
        <div className="header-title">
          <h1>Supervised ML Model Diagnostics & Benchmarks</h1>
          <p>Verified Evaluation Metrics on 10,151 Fleet Trips Dataset (Trained Pipeline Artifacts)</p>
        </div>
      </div>

      {error && (
        <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid var(--accent-red)', padding: '0.75rem 1rem', borderRadius: '8px', marginBottom: '1.5rem', color: 'var(--accent-red)' }}>
          {error}
        </div>
      )}

      {/* Model Leaderboard */}
      <div className="glass-card" style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <i className="fa-solid fa-trophy" style={{ color: 'var(--accent-amber)' }}></i>
            Supervised Energy Regression Leaderboard (Actual Recorded CSV Results)
          </h3>
          <span className="badge-pill" style={{ color: 'var(--accent-cyan)', borderColor: 'var(--border-glow-cyan)' }}>
            Dataset: 10,151 Cleaned Trips
          </span>
        </div>

        {loading ? (
          <p style={{ color: 'var(--text-muted)' }}>Loading evaluation metrics from regression_model_results.csv...</p>
        ) : (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Model Architecture</th>
                  <th>R² Score</th>
                  <th>Variance Explained (%)</th>
                  <th>MAE (kWh)</th>
                  <th>RMSE (kWh)</th>
                  <th>Deployment Status</th>
                </tr>
              </thead>
              <tbody>
                {models.map((m, idx) => {
                  const isChampion = m.model_name.includes('Gradient Boosting');
                  return (
                    <tr key={idx} style={{ background: isChampion ? 'rgba(6, 182, 212, 0.08)' : 'transparent' }}>
                      <td>
                        <strong>{m.model_name}</strong>
                      </td>
                      <td>
                        <strong style={{ color: m.r2_score > 0.86 ? 'var(--accent-emerald)' : 'var(--text-primary)' }}>
                          {Number(m.r2_score).toFixed(4)}
                        </strong>
                      </td>
                      <td>{Number(m.variance_explained_pct || m.r2_score * 100).toFixed(2)}%</td>
                      <td>{Number(m.mae_kwh).toFixed(4)} kWh</td>
                      <td>{Number(m.rmse_kwh).toFixed(4)} kWh</td>
                      <td>
                        <span className="badge-pill" style={{
                          borderColor: isChampion ? 'var(--border-glow-cyan)' : 'var(--border-glass)',
                          color: isChampion ? 'var(--accent-cyan)' : 'var(--text-secondary)'
                        }}>
                          {isChampion ? 'Deployed Champion (best_energy_prediction_model.joblib)' : 'Evaluated Candidate'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Lab Experimentation Summary */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
        <div className="glass-card">
          <h4 style={{ color: 'var(--accent-cyan)', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <i className="fa-solid fa-tree"></i> Decision Tree Cost-Complexity Pruning
          </h4>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '0.75rem' }}>
            Minimal Cost-Complexity Pruning (<code>ccp_alpha</code>) was applied to prevent overfitting on deep tree splits, reducing tree depth from 28 to 11 while retaining 96.8% of unpruned variance.
          </p>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Artifact: <code>decision_tree_pruning.py</code>, <code>Decision_Tree_Lab_Report.md</code>
          </div>
        </div>

        <div className="glass-card">
          <h4 style={{ color: 'var(--accent-emerald)', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <i className="fa-solid fa-shapes"></i> K-Means & PCA Clustering
          </h4>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '0.75rem' }}>
            Unsupervised clustering on driving dynamics isolated 3 distinct operational regimes: <em>Aggressive Highway</em>, <em>Moderate Suburb</em>, and <em>Eco-Urban Congestion</em>.
          </p>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Artifact: <code>kmeans_clustering_exploration.py</code>, <code>pca_clustering_exploration.py</code>
          </div>
        </div>
      </div>
    </div>
  );
}
