"""
================================================================================
HISTORY SERVICE: RUN RECORDING & AUDIT LOG PERSISTENCE
================================================================================
Maintains an audit trail of:
  - Intelligent Power Allocation events (Energy harvested, allocated, battery avoided)
  - Baseline ML trip energy predictions and range estimations
  - Persistent JSON and SQLite access
================================================================================
"""

import os
import json
import time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_FILE = os.path.join(BASE_DIR, "prediction_history.json")
MAX_RECORDS = 100


def _load_raw_history() -> list:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_raw_history(records: list):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(records[:MAX_RECORDS], f, indent=2)
    except Exception as e:
        print(f"Warning: could not save history log: {e}")


def add_allocation_record(allocation_result: dict) -> dict:
    """Records an intelligent power allocation event."""
    records = _load_raw_history()
    now = datetime.now()
    energy_acc = allocation_result.get('energy_accounting', {})

    record = {
        'id': f"alloc_{int(time.time() * 1000)}",
        'type': 'Power Allocation',
        'timestamp': now.strftime("%Y-%m-%d %H:%M:%S"),
        'summary': f"Avoided {energy_acc.get('battery_energy_avoided_wh', 0):.1f} Wh Main Battery Draw",
        'total_generated_wh': energy_acc.get('total_generated_wh', 0),
        'usable_aux_wh': energy_acc.get('usable_aux_wh', 0),
        'total_allocated_wh': energy_acc.get('total_allocated_wh', 0),
        'battery_energy_avoided_wh': energy_acc.get('battery_energy_avoided_wh', 0),
        'utilization_pct': energy_acc.get('utilization_pct', 0),
        'duration_hours': allocation_result.get('duration_hours', 1.0),
        'details': energy_acc
    }

    records.insert(0, record)
    _save_raw_history(records)
    return record


def add_prediction_record(inputs: dict, prediction_result: dict, range_result: dict = None) -> dict:
    """Records a single trip energy prediction event."""
    records = _load_raw_history()
    now = datetime.now()

    record = {
        'id': f"pred_{int(time.time() * 1000)}",
        'type': 'Energy Prediction',
        'timestamp': now.strftime("%Y-%m-%d %H:%M:%S"),
        'summary': f"{inputs.get('trip_distance')} km @ {inputs.get('speed')} km/h",
        'distance_km': float(inputs.get('trip_distance', 0)),
        'speed_kmh': float(inputs.get('speed', 0)),
        'predicted_kwh': float(prediction_result.get('predicted_energy_kwh', 0)),
        'consumption_kwh_100km': float(prediction_result.get('consumption_kwh_per_100km', 0)),
        'range_est_km': float(range_result.get('estimated_range_km', 0)) if range_result else None,
        'details': {
            'voltage_v': inputs.get('voltage'),
            'current_a': inputs.get('current'),
            'max_temp_c': inputs.get('max_cell_temp')
        }
    }

    records.insert(0, record)
    _save_raw_history(records)
    return record


def get_all_history() -> list:
    """Retrieve full chronological run history."""
    return _load_raw_history()


def clear_all_history() -> bool:
    """Erase stored run history."""
    try:
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        return True
    except Exception:
        return False
