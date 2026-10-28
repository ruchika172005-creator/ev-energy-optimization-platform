"""
================================================================================
AI-POWERED AUXILIARY ENERGY HARVESTING & INTELLIGENT POWER ALLOCATION SYSTEM FOR EVS
================================================================================
Flask REST API & Unified Server
Technology Stack:
  - Backend: Python 3 / Flask 3.x REST API with SQLite Persistence
  - ML Pipeline: Scikit-learn (ColumnTransformer + GradientBoostingRegressor)
  - Frontend: React 18 + Vite (and fallback dashboard)
================================================================================
"""

import os
import sys
import json
from flask import Flask, request, jsonify, render_template, send_file, Response

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Import modular backend services
from backend.database import get_connection
from backend.energy_sources_service import (
    get_all_sources,
    update_source,
    get_sources_summary
)
from backend.power_allocation_service import (
    get_all_loads,
    add_or_update_load,
    delete_load,
    reset_demo_loads,
    apply_demo_scenario,
    execute_power_allocation,
    get_allocation_history,
    clear_allocation_history
)
from backend.battery_impact_service import calculate_battery_impact
from backend.model_service import (
    load_model_pipeline,
    validate_trip_inputs,
    predict_trip_energy,
    estimate_driving_range,
    get_feature_importances
)
from backend.metrics_service import (
    get_regression_benchmark_metrics,
    get_research_lab_benchmarks
)
from backend.history_service import (
    add_prediction_record,
    add_allocation_record,
    get_all_history,
    clear_all_history
)
from backend.analysis_service import (
    get_dataset_summary,
    get_visualizations_catalog
)

FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")

app = Flask(
    __name__,
    static_folder=FRONTEND_DIST if os.path.exists(FRONTEND_DIST) else None,
    static_url_path=""
)

# Robust CORS headers for cross-origin React frontend (port 3000 / 5173)
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = Response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
        return response


@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response


# =============================================================================
# WEB INTERFACE ROUTE & ROOT STATUS
# =============================================================================
@app.route("/")
def index():
    """
    Serves the primary React application from frontend/dist, or returns
    system health JSON if requested via API headers.
    """
    wants_json = (
        request.args.get('format') == 'json' or
        request.headers.get('Accept') == 'application/json'
    )
    if wants_json:
        return health_check()

    dist_index = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.exists(dist_index):
        return send_file(dist_index)
    return health_check()


@app.route("/<path:path>")
def serve_frontend_assets(path):
    """Serves compiled React JS, CSS, and asset bundles from frontend/dist."""
    dist_file = os.path.join(FRONTEND_DIST, path)
    if os.path.exists(dist_file):
        return send_file(dist_file)
    # SPA fallback to index.html for client-side routing
    dist_index = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.exists(dist_index):
        return send_file(dist_index)
    return health_check()


# =============================================================================
# HEALTH CHECK & SYSTEM STATUS
# =============================================================================
@app.route("/health", methods=["GET"])
@app.route("/api/health", methods=["GET"])
def health_check():
    """System status and model integrity readiness check."""
    model_loaded = False
    model_name = "None"
    model_err = None

    try:
        pipe = load_model_pipeline()
        model_name = pipe.named_steps['regressor'].__class__.__name__
        model_loaded = True
    except Exception as e:
        model_err = str(e)

    dataset_available = (
        os.path.exists(os.path.join(BASE_DIR, "cleaned_ev_data.csv")) or
        os.path.exists(os.path.join(BASE_DIR, "Electric Vehicle Trip Energy Consumption Data.csv"))
    )

    return jsonify({
        'status': 'healthy' if model_loaded else 'degraded',
        'application': 'Auxiliary Energy Harvesting and Intelligent Power Allocation System for Electric Vehicles',
        'version': '3.0.0',
        'model_status': {
            'loaded': model_loaded,
            'regressor': model_name,
            'error': model_err
        },
        'dataset_available': dataset_available,
        'backend': 'Flask 3.x / Scikit-Learn 1.9 / SQLite3',
        'features': [
            'Auxiliary Energy Source Monitoring (Regen, Solar, Vibration)',
            'Intelligent Power Allocation Engine (Priority-Ranked Load Matching)',
            'Battery Energy Avoidance & Lifecycle Accounting',
            'Supervised ML Trip Energy Prediction (Supporting Module)',
            'Fleet EDA & Research Visualizations'
        ]
    })


# =============================================================================
# 1. AUXILIARY ENERGY SOURCES ENDPOINTS
# =============================================================================
@app.route("/api/energy/sources", methods=["GET"])
def api_get_sources():
    """Retrieve all monitored auxiliary energy harvesting sources."""
    sources = get_all_sources()
    summary = get_sources_summary()
    return jsonify({
        'success': True,
        'sources': sources,
        'summary': summary
    })


@app.route("/api/energy/sources", methods=["POST"])
def api_update_source():
    """
    Update operating parameters or manual test inputs for an energy source.
    Body JSON: { "source_id": "regen"|"solar"|"vibration", "parameters": {...}, "enabled": true }
    """
    data = request.get_json(silent=True) or {}
    source_id = data.get('source_id')
    if not source_id:
        return jsonify({'success': False, 'error': 'Missing required parameter: source_id'}), 400

    updated = update_source(source_id, data)
    if not updated:
        return jsonify({'success': False, 'error': f"Source '{source_id}' not found"}), 404

    return jsonify({
        'success': True,
        'source': updated,
        'summary': get_sources_summary()
    })


# =============================================================================
# 2. ELECTRICAL LOADS MANAGEMENT ENDPOINTS
# =============================================================================
@app.route("/api/energy/loads", methods=["GET"])
def api_get_loads():
    """Retrieve all configured auxiliary electrical loads."""
    loads = get_all_loads()
    return jsonify({
        'success': True,
        'count': len(loads),
        'loads': loads
    })


@app.route("/api/energy/loads", methods=["POST"])
def api_save_load():
    """Add or modify an auxiliary electrical load definition."""
    data = request.get_json(silent=True) or {}
    if not data.get('id') or not data.get('name'):
        return jsonify({'success': False, 'error': 'Fields "id" and "name" are required'}), 400

    saved_load = add_or_update_load(data)
    return jsonify({
        'success': True,
        'load': saved_load
    })


@app.route("/api/energy/loads/<load_id>", methods=["DELETE"])
def api_delete_load(load_id):
    """Delete a custom auxiliary electrical load."""
    deleted = delete_load(load_id)
    return jsonify({
        'success': deleted,
        'message': f"Load '{load_id}' deleted" if deleted else "Load not found"
    })


@app.route("/api/energy/loads/reset", methods=["POST"])
def api_reset_loads():
    """Reset loads table to the 7 canonical demonstration loads (320 W total)."""
    reset_demo_loads()
    loads = get_all_loads()
    return jsonify({
        'success': True,
        'message': 'Demonstration loads reset successfully to 320 W baseline.',
        'count': len(loads),
        'loads': loads
    })


# =============================================================================
# 3. INTELLIGENT POWER ALLOCATION ENGINE ENDPOINT
# =============================================================================
@app.route("/api/energy/allocate", methods=["POST"])
def api_allocate_power():
    """
    Executes the Intelligent Power Allocation Engine:
      1. Computes total usable auxiliary power after DC-DC conversion.
      2. Ranks active electrical loads by priority (Priority 1 = highest).
      3. Allocates available power without exceeding limits.
      4. Retains main traction battery as fallback supply for unmet demand when enabled.
      5. Records full energy accounting in database and audit log.
    """
    data = request.get_json(silent=True) or {}
    duration_hours = float(data.get('duration_hours', 1.0))
    allow_main_battery_fallback = bool(data.get('allow_main_battery_fallback', True))
    dc_dc_efficiency = float(data.get('dc_dc_efficiency', 0.94))

    try:
        allocation_result = execute_power_allocation(
            duration_hours=duration_hours,
            allow_main_battery_fallback=allow_main_battery_fallback,
            dc_dc_efficiency=dc_dc_efficiency
        )

        # Also add to unified audit trail
        add_allocation_record(allocation_result)

        return jsonify({
            'success': True,
            'allocation': allocation_result
        })
    except Exception as exc:
        return jsonify({
            'success': False,
            'error': f"Power allocation failed: {str(exc)}"
        }), 500


@app.route("/api/energy/demo-scenario", methods=["POST"])
def api_demo_scenario():
    """
    Sets up and executes a reliable evaluation scenario:
      Scenario A: 430W source -> 404.2W usable -> 320W load demand -> 84.2W surplus, 0W fallback
      Scenario B: 200W source -> 188.0W usable -> 320W load demand -> 0W surplus, 132W fallback
    """
    data = request.get_json(silent=True) or {}
    scenario_id = str(data.get('scenario', 'A')).upper()
    allow_fallback = bool(data.get('allow_main_battery_fallback', True))
    duration_hours = float(data.get('duration_hours', 1.0))

    try:
        allocation_result = apply_demo_scenario(
            scenario_id=scenario_id,
            allow_fallback=allow_fallback,
            duration_hours=duration_hours
        )
        add_allocation_record(allocation_result)

        return jsonify({
            'success': True,
            'scenario': scenario_id,
            'message': f"Demonstration Scenario {scenario_id} applied and evaluated successfully.",
            'allocation': allocation_result
        })
    except Exception as exc:
        return jsonify({
            'success': False,
            'error': f"Applying scenario {scenario_id} failed: {str(exc)}"
        }), 500


# =============================================================================
# 4. ENERGY SYSTEM SUMMARY & BATTERY IMPACT
# =============================================================================
@app.route("/api/energy/summary", methods=["GET"])
def api_energy_summary():
    """High-level summary of active sources, total demand, and recent allocation."""
    sources_sum = get_sources_summary()
    loads = get_all_loads()
    total_load_demand_w = sum(l['power_demand_w'] for l in loads if l['enabled'])

    history = get_allocation_history(limit=1)
    if history:
        last_alloc = history[0]['details']
    else:
        # Automatically run baseline allocation so system never returns null allocation
        last_alloc = execute_power_allocation(duration_hours=1.0, allow_main_battery_fallback=True)
        add_allocation_record(last_alloc)

    return jsonify({
        'success': True,
        'sources_summary': sources_sum,
        'total_configured_load_demand_w': round(total_load_demand_w, 2),
        'last_allocation': last_alloc
    })


@app.route("/api/battery/impact", methods=["GET"])
def api_battery_impact():
    """Evaluates battery energy avoided, range preserved, and lifecycle indicators."""
    impact = calculate_battery_impact()
    return jsonify({
        'success': True,
        'impact': impact
    })


# =============================================================================
# 5. SUPPORTING MODULE: ML ENERGY PREDICTION (PRESERVED)
# =============================================================================
@app.route("/predict", methods=["POST"])
@app.route("/api/predict", methods=["POST"])
def api_predict():
    """
    Supporting Component: Baseline vehicle trip traction energy prediction
    using trained GradientBoostingRegressor pipeline on 10,151 trips dataset.
    """
    data = request.get_json(silent=True) or {}
    cleaned, errors = validate_trip_inputs(data)

    if errors:
        return jsonify({
            'success': False,
            'errors': errors
        }), 400

    try:
        prediction_res = predict_trip_energy(cleaned)

        range_res = None
        cap = float(data.get('battery_capacity', data.get('battery_capacity_kwh', 45.0)))
        soc = float(data.get('soc', data.get('current_soc_pct', 80.0)))
        try:
            range_res = estimate_driving_range(
                battery_capacity_kwh=cap,
                current_soc_pct=soc,
                predicted_kwh=prediction_res['predicted_energy_kwh'],
                trip_distance_km=cleaned['trip_distance']
            )
        except Exception:
            pass

        # Record in history
        history_rec = add_prediction_record(cleaned, prediction_res, range_res)

        return jsonify({
            'success': True,
            'prediction': prediction_res,
            'range_estimation': range_res,
            'inputs_echo': cleaned,
            'history_id': history_rec.get('id')
        })
    except Exception as exc:
        return jsonify({
            'success': False,
            'error': f"Prediction execution failed: {str(exc)}"
        }), 500


@app.route("/api/range-estimate", methods=["POST"])
def api_range_estimate():
    """Dedicated driving range estimation based on battery capacity and consumption."""
    data = request.get_json(silent=True) or {}
    try:
        capacity = float(data.get('battery_capacity_kwh', 45.0))
        soc = float(data.get('current_soc_pct', 80.0))
        predicted_kwh = float(data.get('predicted_energy_kwh', 3.5))
        distance_km = float(data.get('trip_distance_km', 15.0))
        reserve = float(data.get('reserve_buffer_pct', 5.0))

        range_res = estimate_driving_range(
            battery_capacity_kwh=capacity,
            current_soc_pct=soc,
            predicted_kwh=predicted_kwh,
            trip_distance_km=distance_km,
            reserve_buffer_pct=reserve
        )
        return jsonify({'success': True, 'range': range_res})
    except Exception as exc:
        return jsonify({'success': False, 'error': f"Range estimation failed: {str(exc)}"}), 400


# =============================================================================
# 6. SUPPORTING MODULE: FLEET DATASET & EDA
# =============================================================================
@app.route("/analysis/summary", methods=["GET"])
@app.route("/api/analysis/summary", methods=["GET"])
def api_dataset_summary():
    """Fleet dataset statistical profiling across 10,151 trips."""
    summary = get_dataset_summary()
    return jsonify({'success': True, 'summary': summary})


@app.route("/analysis/visualizations", methods=["GET"])
@app.route("/api/analysis/visualizations", methods=["GET"])
def api_visualizations():
    """Catalog of research figures generated during EDA and ML benchmarking."""
    catalog = get_visualizations_catalog()
    return jsonify({'success': True, 'count': len(catalog), 'visualizations': catalog})


@app.route("/api/figures/<path:filename>", methods=["GET"])
def api_serve_figure(filename):
    """Securely serves saved publication figure PNGs."""
    safe_filename = os.path.basename(filename)
    fig_path = os.path.join(BASE_DIR, safe_filename)
    if os.path.exists(fig_path) and safe_filename.endswith(('.png', '.jpg', '.jpeg', '.svg')):
        return send_file(fig_path, mimetype='image/png')
    return jsonify({'error': 'Figure not found'}), 404


# =============================================================================
# 7. SUPPORTING MODULE: ML BENCHMARKS & DIAGNOSTICS
# =============================================================================
@app.route("/models/metrics", methods=["GET"])
@app.route("/api/models/metrics", methods=["GET"])
def api_model_performance():
    """Supervised regression benchmarks (GBR vs RF vs Ridge vs DT vs KNN)."""
    try:
        metrics = get_regression_benchmark_metrics()
        return jsonify({'success': True, 'metrics': metrics})
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


# =============================================================================
# 8. AUDIT HISTORY & PERSISTENCE
# =============================================================================
@app.route("/api/history", methods=["GET", "DELETE"])
def api_history():
    """Audit Trail: History of power allocation events and predictions."""
    if request.method == "DELETE":
        clear_allocation_history()
        clear_all_history()
        return jsonify({'success': True, 'message': 'All audit history cleared successfully.'})

    unified_history = get_all_history()
    alloc_history = get_allocation_history(limit=50)

    return jsonify({
        'success': True,
        'count': len(unified_history),
        'history': unified_history,
        'allocation_history': alloc_history
    })


# =============================================================================
# 9. SYSTEM SETTINGS
# =============================================================================
@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    """Configure converter efficiency, operating mode, and safety interlocks."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            for k, v in data.items():
                cursor.execute("""
                    INSERT INTO system_settings (key, value) VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """, (k, str(v)))
            conn.commit()

        cursor.execute("SELECT key, value FROM system_settings")
        rows = cursor.fetchall()
        settings = {r['key']: r['value'] for r in rows}

    return jsonify({'success': True, 'settings': settings})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=" * 80)
    print(" STARTING AI-POWERED AUXILIARY ENERGY HARVESTING & POWER ALLOCATION SERVER")
    print(f" REST API Server running locally at: http://127.0.0.1:{port}")
    print("=" * 80)
    app.run(host="0.0.0.0", port=port, debug=False)
