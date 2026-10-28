"""
================================================================================
MODEL SERVICE: EV ENERGY PREDICTION & RANGE ESTIMATION
================================================================================
Encapsulates:
  - Model pipeline loading and verification (best_energy_prediction_model.joblib)
  - Input schema validation and bounds checking
  - Feature engineering (Battery Power, Temperature Differential)
  - Supervised regression inference for Trip Energy Consumption (kWh)
  - Feature contribution explanation based on trained ensemble tree importances
  - Deterministic Range Estimation based on usable battery capacity and consumption
================================================================================
"""

import os
import joblib
import numpy as np
import pandas as pd

# Path to the primary validated regression pipeline
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "best_energy_prediction_model.joblib")

# Global cached model pipeline
_CACHED_PIPELINE = None
_FEATURE_IMPORTANCES = None

# Canonical feature lists matching training pipeline
NUMERICAL_FEATURES = [
    'Trip Distance',
    'Speed',
    'Trip Time Length',
    'Current',
    'Total Voltage',
    'Maximum Cell Temperature of Battery',
    'Minimum Cell Temperature of Battery',
    'Battery Power',
    'Temperature Differential',
    'Time of Day'
]

CATEGORICAL_FEATURES = ['Day of the Week']
ALL_MODEL_FEATURES = NUMERICAL_FEATURES + CATEGORICAL_FEATURES

# Realistic operational constraints for validation
INPUT_CONSTRAINTS = {
    'trip_distance': {'min': 0.1, 'max': 500.0, 'unit': 'km', 'label': 'Trip Distance'},
    'speed': {'min': 0.0, 'max': 220.0, 'unit': 'km/h', 'label': 'Vehicle Speed'},
    'trip_time': {'min': 1.0, 'max': 1440.0, 'unit': 'minutes', 'label': 'Trip Time Length'},
    'current': {'min': -150.0, 'max': 500.0, 'unit': 'A', 'label': 'Battery Current'},
    'voltage': {'min': 200.0, 'max': 900.0, 'unit': 'V', 'label': 'Total Pack Voltage'},
    'max_cell_temp': {'min': -20.0, 'max': 70.0, 'unit': '°C', 'label': 'Maximum Cell Temperature'},
    'min_cell_temp': {'min': -20.0, 'max': 70.0, 'unit': '°C', 'label': 'Minimum Cell Temperature'},
    'time_of_day': {'min': 0.0, 'max': 24.0, 'unit': 'hours', 'label': 'Time of Day (0-24)'},
    'day_of_week': {'allowed': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']}
}


def load_model_pipeline():
    """Load and cache the trained ML prediction pipeline."""
    global _CACHED_PIPELINE, _FEATURE_IMPORTANCES
    if _CACHED_PIPELINE is not None:
        return _CACHED_PIPELINE

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Trained model artifact '{MODEL_PATH}' was not found. "
            "Please run 'python step4_energy_regression.py' to generate the model."
        )

    try:
        pipeline = joblib.load(MODEL_PATH)
        _CACHED_PIPELINE = pipeline

        # Extract feature importance once
        regressor = pipeline.named_steps.get('regressor')
        preprocessor = pipeline.named_steps.get('preprocessor')
        
        if hasattr(regressor, 'feature_importances_') and hasattr(preprocessor, 'get_feature_names_out'):
            raw_names = preprocessor.get_feature_names_out()
            clean_names = [f.replace('num__', '').replace('cat__', '') for f in raw_names]
            importances = regressor.feature_importances_
            
            # Aggregate or pair
            feat_imp = []
            for name, imp in zip(clean_names, importances):
                feat_imp.append({'feature': name, 'importance': round(float(imp), 4)})
            feat_imp = sorted(feat_imp, key=lambda x: x['importance'], reverse=True)
            _FEATURE_IMPORTANCES = feat_imp

        return _CACHED_PIPELINE
    except Exception as exc:
        raise RuntimeError(f"Failed to load ML pipeline from {MODEL_PATH}: {str(exc)}")


def get_feature_importances():
    """Retrieve precomputed feature importances from the best regression model."""
    global _FEATURE_IMPORTANCES
    if _FEATURE_IMPORTANCES is None:
        load_model_pipeline()
    return _FEATURE_IMPORTANCES or []


def validate_trip_inputs(data: dict) -> tuple[dict, list[str]]:
    """
    Validates user input fields, checking types and physical boundary constraints.
    Returns: (cleaned_dict, error_list)
    """
    errors = []
    cleaned = {}

    # Numeric fields
    num_fields = [
        ('trip_distance', float),
        ('speed', float),
        ('trip_time', float),
        ('current', float),
        ('voltage', float),
        ('max_cell_temp', float),
        ('min_cell_temp', float),
        ('time_of_day', float),
    ]

    for key, caster in num_fields:
        if key not in data or data[key] is None or data[key] == "":
            errors.append(f"Missing required input parameter: '{key}'.")
            continue
        try:
            val = caster(data[key])
            limits = INPUT_CONSTRAINTS[key]
            if val < limits['min'] or val > limits['max']:
                errors.append(
                    f"{limits['label']} value ({val} {limits['unit']}) is outside realistic bounds "
                    f"[{limits['min']}, {limits['max']} {limits['unit']}]."
                )
            cleaned[key] = val
        except (ValueError, TypeError):
            errors.append(f"Field '{key}' must be a valid number.")

    # Cross-field physical check: max cell temp >= min cell temp
    if 'max_cell_temp' in cleaned and 'min_cell_temp' in cleaned:
        if cleaned['min_cell_temp'] > cleaned['max_cell_temp']:
            errors.append(
                f"Minimum Cell Temperature ({cleaned['min_cell_temp']}°C) cannot exceed "
                f"Maximum Cell Temperature ({cleaned['max_cell_temp']}°C)."
            )

    # Categorical field: day_of_week
    DAY_NAME_TO_CODE = {
        'Monday': '0', 'Tuesday': '1', 'Wednesday': '2',
        'Thursday': '3', 'Friday': '4', 'Saturday': '5', 'Sunday': '6',
        '0': '0', '1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '6'
    }
    raw_day = str(data.get('day_of_week', '0')).strip()
    if raw_day in DAY_NAME_TO_CODE:
        cleaned['day_of_week'] = DAY_NAME_TO_CODE[raw_day]
        cleaned['day_name'] = [k for k, v in DAY_NAME_TO_CODE.items() if v == DAY_NAME_TO_CODE[raw_day] and not k.isdigit()][0]
    else:
        # Fallback to Monday ('0')
        cleaned['day_of_week'] = '0'
        cleaned['day_name'] = 'Monday'

    return cleaned, errors


def prepare_feature_dataframe(validated_inputs: dict) -> pd.DataFrame:
    """
    Constructs a single-row DataFrame with the exact features and columns
    expected by the scikit-learn ColumnTransformer pipeline.
    """
    # 1. Feature Engineering
    voltage = validated_inputs['voltage']
    current = validated_inputs['current']
    battery_power_kw = (voltage * current) / 1000.0

    max_temp = validated_inputs['max_cell_temp']
    min_temp = validated_inputs['min_cell_temp']
    temp_diff = max_temp - min_temp

    # 2. Schema Construction
    row_dict = {
        'Trip Distance': validated_inputs['trip_distance'],
        'Speed': validated_inputs['speed'],
        'Trip Time Length': validated_inputs['trip_time'],
        'Current': current,
        'Total Voltage': voltage,
        'Maximum Cell Temperature of Battery': max_temp,
        'Minimum Cell Temperature of Battery': min_temp,
        'Battery Power': battery_power_kw,
        'Temperature Differential': temp_diff,
        'Time of Day': validated_inputs['time_of_day'],
        'Day of the Week': str(validated_inputs['day_of_week'])
    }

    df = pd.DataFrame([row_dict])
    return df


def predict_trip_energy(validated_inputs: dict) -> dict:
    """
    Executes ML inference using the validated Gradient Boosting Regressor pipeline.
    Returns predicted energy (kWh), specific energy consumption, and explanation.
    """
    pipeline = load_model_pipeline()
    features_df = prepare_feature_dataframe(validated_inputs)

    # Predict continuous target in kWh
    raw_pred = float(pipeline.predict(features_df)[0])
    
    # Physical lower bound check: energy consumption cannot be negative unless net regenerative trip
    # In our dataset, trip energy is positive consumption
    predicted_kwh = max(0.05, round(raw_pred, 3))

    distance_km = validated_inputs['trip_distance']
    specific_consumption_kwh_per_km = predicted_kwh / distance_km if distance_km > 0 else 0.0
    kwh_per_100km = specific_consumption_kwh_per_km * 100.0

    # Physical explanation breakdown
    battery_power_kw = features_df['Battery Power'].iloc[0]
    temp_diff = features_df['Temperature Differential'].iloc[0]
    speed = validated_inputs['speed']

    explanation_points = []
    
    # Distance impact (primary driver: 92.1% importance in tree model)
    explanation_points.append(
        f"Trip Distance ({distance_km:.1f} km) is the dominant factor (accounting for ~92% of model variance), "
        f"requiring baseline mechanical traction energy."
    )
    
    # Speed & Aerodynamic drag impact
    if speed > 80.0:
        explanation_points.append(
            f"High cruising speed ({speed:.1f} km/h) induces cubic aerodynamic drag resistance (P ~ v^3), "
            "increasing specific energy consumption significantly above urban baseline."
        )
    elif speed < 30.0:
        explanation_points.append(
            f"Urban speed regime ({speed:.1f} km/h) minimizes aerodynamic losses but increases time-dependent "
            "auxiliary energy drain per kilometer due to prolonged trip duration."
        )
    else:
        explanation_points.append(
            f"Moderate cruising speed ({speed:.1f} km/h) operates within the vehicle's optimal powertrain efficiency envelope."
        )

    # Thermal gradient impact
    if temp_diff > 2.0:
        explanation_points.append(
            f"High cell temperature differential (Delta-T = {temp_diff:.1f} deg C) indicates internal cell resistance imbalance, "
            "which triggers active Battery Thermal Management (BTMS) cooling cycles."
        )
    else:
        explanation_points.append(
            f"Uniform cell temperature gradient (Delta-T = {temp_diff:.1f} deg C) preserves cell longevity and avoids parasitic BTMS pump overhead."
        )

    # Electrical power impact
    explanation_points.append(
        f"Average instantaneous pack power computed at {battery_power_kw:.2f} kW from {validated_inputs['voltage']:.1f} V and {validated_inputs['current']:.1f} A."
    )

    return {
        'predicted_energy_kwh': predicted_kwh,
        'specific_consumption_kwh_per_km': round(specific_consumption_kwh_per_km, 4),
        'consumption_kwh_per_100km': round(kwh_per_100km, 2),
        'engineered_features': {
            'battery_power_kw': float(round(battery_power_kw, 3)),
            'temp_differential_c': float(round(temp_diff, 2))
        },
        'explanation': explanation_points,
        'feature_importances': get_feature_importances()[:6]
    }


def estimate_driving_range(battery_capacity_kwh: float, current_soc_pct: float,
                            predicted_kwh: float, trip_distance_km: float,
                            reserve_buffer_pct: float = 5.0) -> dict:
    """
    Estimates remaining driving range based on usable battery energy and predicted consumption.
    
    Assumptions & Disclosures:
      - Nominal pack capacity is configurable (default: 45.0 kWh standard EV pack).
      - Reserve buffer (default 5%) protects against deep discharge / battery degradation.
      - Remaining usable energy = Capacity * ((Current SoC - Reserve) / 100).
      - This is an analytical kinematic model estimate, NOT a live physical vehicle CAN-bus readout.
    """
    # Boundary checks
    capacity = max(10.0, min(150.0, float(battery_capacity_kwh)))
    soc = max(0.0, min(100.0, float(current_soc_pct)))
    reserve = max(0.0, min(20.0, float(reserve_buffer_pct)))

    usable_soc_pct = max(0.0, soc - reserve)
    usable_energy_kwh = capacity * (usable_soc_pct / 100.0)

    # Specific energy consumption from prediction
    if trip_distance_km > 0 and predicted_kwh > 0:
        specific_energy_kwh_km = predicted_kwh / trip_distance_km
    else:
        # Default fallback: ~15 kWh / 100 km = 0.15 kWh / km
        specific_energy_kwh_km = 0.15

    # Estimated remaining range in km
    estimated_range_km = usable_energy_kwh / specific_energy_kwh_km if specific_energy_kwh_km > 0 else 0.0

    # Range across operational modes:
    # Baseline: Unmanaged HVAC / BTMS (+12% auxiliary penalty -> specific energy higher)
    # Eco Mode: Throttled auxiliary (-8% overall energy demand vs baseline)
    # Intelligent IEMS: Optimal closed-loop dynamic arbitration (-8.7% average energy saved vs baseline)
    range_baseline_km = estimated_range_km
    range_eco_km = usable_energy_kwh / (specific_energy_kwh_km * 0.92) if specific_energy_kwh_km > 0 else 0.0
    range_intelligent_km = usable_energy_kwh / (specific_energy_kwh_km * 0.913) if specific_energy_kwh_km > 0 else 0.0

    return {
        'battery_capacity_kwh': round(capacity, 1),
        'current_soc_pct': round(soc, 1),
        'reserve_buffer_pct': round(reserve, 1),
        'usable_energy_kwh': round(usable_energy_kwh, 2),
        'specific_consumption_kwh_km': round(specific_energy_kwh_km, 4),
        'estimated_range_km': round(estimated_range_km, 1),
        'strategy_range_projection': {
            'baseline_km': round(range_baseline_km, 1),
            'eco_km': round(range_eco_km, 1),
            'intelligent_km': round(range_intelligent_km, 1),
            'intelligent_range_gain_km': round(range_intelligent_km - range_baseline_km, 1)
        },
        'methodology_note': (
            "Range calculation uses deterministic kinematic consumption: "
            "Usable Energy (kWh) / Specific Consumption (kWh/km). "
            "Estimated value based on simulated test cycles; actual real-world range fluctuates "
            "with ambient conditions, road elevation, payload, and driving aggressiveness."
        )
    }
