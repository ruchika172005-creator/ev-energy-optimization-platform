/**
 * AI-POWERED EV AUXILIARY ENERGY MANAGEMENT API CLIENT
 * Connects React Frontend to Flask REST API (port 5000)
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000';

async function request(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
  const defaultHeaders = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  };

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...(options.headers || {})
    }
  };

  try {
    const res = await fetch(url, config);
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || data.error || `HTTP error ${res.status}`);
    }
    return data;
  } catch (err) {
    console.error(`API Error [${endpoint}]:`, err);
    throw err;
  }
}

export const api = {
  // System Health
  getHealth: () => request('/api/health'),

  // 1. Auxiliary Energy Sources
  getEnergySources: () => request('/api/energy/sources'),
  updateEnergySource: (sourceData) =>
    request('/api/energy/sources', {
      method: 'POST',
      body: JSON.stringify(sourceData)
    }),

  // 2. Electrical Loads Configuration
  getEnergyLoads: () => request('/api/energy/loads'),
  saveEnergyLoad: (loadData) =>
    request('/api/energy/loads', {
      method: 'POST',
      body: JSON.stringify(loadData)
    }),
  deleteEnergyLoad: (loadId) =>
    request(`/api/energy/loads/${loadId}`, {
      method: 'DELETE'
    }),

  // 3. Intelligent Power Allocation Engine
  allocatePower: (params = {}) =>
    request('/api/energy/allocate', {
      method: 'POST',
      body: JSON.stringify(params)
    }),
  runDemoScenario: (scenario = 'A', allowFallback = true, durationHours = 1.0) =>
    request('/api/energy/demo-scenario', {
      method: 'POST',
      body: JSON.stringify({
        scenario,
        allow_main_battery_fallback: allowFallback,
        duration_hours: durationHours
      })
    }),
  resetDemoLoads: () =>
    request('/api/energy/loads/reset', {
      method: 'POST'
    }),

  // 4. Energy Summary & Battery Impact
  getEnergySummary: () => request('/api/energy/summary'),
  getBatteryImpact: () => request('/api/battery/impact'),

  // 5. Supporting Module: ML Energy Prediction
  predictTrip: (tripData) =>
    request('/api/predict', {
      method: 'POST',
      body: JSON.stringify(tripData)
    }),

  // 6. Supporting Module: Fleet Data & EDA
  getDatasetSummary: () => request('/api/analysis/summary'),
  getVisualizations: () => request('/api/analysis/visualizations'),
  getFigureUrl: (filename) => `${API_BASE}/api/figures/${filename}`,

  // 7. Supporting Module: Model Diagnostics & Leaderboard
  getModelBenchmarks: () => request('/api/models/metrics'),

  // 8. Audit History & Logs
  getHistory: () => request('/api/history'),
  clearHistory: () => request('/api/history', { method: 'DELETE' }),

  // 9. System Settings
  getSettings: () => request('/api/settings'),
  updateSettings: (settingsData) =>
    request('/api/settings', {
      method: 'POST',
      body: JSON.stringify(settingsData)
    })
};

export default api;
