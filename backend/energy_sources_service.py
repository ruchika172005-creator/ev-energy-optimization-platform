"""
================================================================================
ENERGY SOURCES SERVICE: AUXILIARY ENERGY HARVESTING & MONITORING
================================================================================
Monitors, calculates, and records power and energy from:
  A. Regenerative braking kinetic energy recovery
  B. Rooftop solar photovoltaic generation
  C. Optional chassis vibration energy harvesting (experimental estimate)

Includes rigorous kinematic, thermodynamic, and solar irradiance models,
input validation, data quality flags, and transparent calculation assumptions.
================================================================================
"""

import json
from datetime import datetime
from backend.database import get_connection


def get_all_sources():
    """Retrieve all auxiliary energy harvesting sources with current telemetry."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sources")
        rows = cursor.fetchall()

        sources = []
        for r in rows:
            params = {}
            try:
                params = json.loads(r['parameters_json']) if r['parameters_json'] else {}
            except Exception:
                pass

            sources.append({
                'id': r['id'],
                'name': r['name'],
                'source_type': r['source_type'],
                'enabled': bool(r['enabled']),
                'operating_status': r['operating_status'],
                'rated_power_w': float(r['rated_power_w']),
                'current_power_w': float(r['current_power_w']),
                'accumulated_energy_wh': float(r['accumulated_energy_wh']),
                'efficiency': float(r['efficiency']),
                'measurement_method': r['measurement_method'],
                'data_quality': r['data_quality'],
                'parameters': params,
                'last_updated': r['last_updated']
            })
        return sources


def calculate_source_power(source_id, params):
    """
    Computes instantaneous electrical power output (Watts) from physical principles.
    Returns: (computed_power_w, efficiency, method, quality, notes)
    """
    if source_id == 'regen':
        # Regenerative braking kinematic recovery model
        mass_kg = float(params.get('vehicle_mass_kg', 1650.0))
        speed_kmh = max(0.0, float(params.get('speed_kmh', 50.0)))
        decel_ms2 = max(0.0, float(params.get('deceleration_ms2', 1.5)))
        regen_fraction = min(1.0, max(0.0, float(params.get('regen_fraction', 0.70))))
        eta_motor = min(1.0, max(0.5, float(params.get('motor_generator_efficiency', 0.88))))
        eta_inv = min(1.0, max(0.5, float(params.get('inverter_efficiency', 0.94))))

        # Direct override power if manual/telemetry input
        if 'manual_power_w' in params and params['manual_power_w'] is not None:
            power_w = max(0.0, float(params['manual_power_w']))
            eff = eta_motor * eta_inv
            method = 'demonstration_input'
            quality = 'demonstration_mode'
            notes = "Manual test input for regenerative power."
        else:
            # Kinematic calculation: P_mech = m * a * v
            v_ms = speed_kmh / 3.6
            p_kinetic_w = mass_kg * decel_ms2 * v_ms
            eff = eta_motor * eta_inv
            # Auxiliary bus tap limit: typically 200W - 600W channeled to LV auxiliary buffer
            power_w = min(600.0, p_kinetic_w * regen_fraction * eff * 0.05)
            method = 'kinematic_model'
            quality = 'verified_model'
            notes = f"Calculated from m={mass_kg}kg, v={speed_kmh}km/h, a={decel_ms2}m/s²."

        return max(0.0, round(power_w, 2)), round(eff, 3), method, quality, notes

    elif source_id == 'solar':
        # Solar Photovoltaic model
        area_m2 = max(0.1, min(5.0, float(params.get('panel_area_m2', 1.85))))
        irradiance = max(0.0, min(1400.0, float(params.get('solar_irradiance_wm2', 750.0))))
        cell_eff = max(0.05, min(0.35, float(params.get('cell_efficiency', 0.21))))
        mppt_eff = max(0.80, min(1.0, float(params.get('mppt_efficiency', 0.96))))
        cell_temp = float(params.get('cell_temp_c', 28.0))
        temp_coeff = float(params.get('temp_coefficient', -0.0038))
        shading = min(1.0, max(0.0, float(params.get('shading_loss_factor', 0.05))))

        if 'manual_power_w' in params and params['manual_power_w'] is not None:
            power_w = max(0.0, float(params['manual_power_w']))
            method = 'demonstration_input'
            quality = 'demonstration_mode'
            notes = "Manual test input for solar power."
        else:
            # P = Area * G * eta_cell * eta_mppt * (1 + gamma*(T - 25)) * (1 - shading)
            temp_factor = 1.0 + temp_coeff * (cell_temp - 25.0)
            power_w = area_m2 * irradiance * cell_eff * mppt_eff * max(0.7, temp_factor) * (1.0 - shading)
            method = 'model_estimate'
            quality = 'verified_model'
            notes = f"Solar model: G={irradiance}W/m², A={area_m2}m², eta={cell_eff*100:.1f}%."

        overall_eff = cell_eff * mppt_eff
        return max(0.0, round(power_w, 2)), round(overall_eff, 3), method, quality, notes

    elif source_id == 'vibration':
        # Vibration harvesting experimental estimation
        stroke_v = max(0.0, min(2.0, float(params.get('suspension_stroke_velocity_ms', 0.12))))
        damping_c = max(50.0, min(1000.0, float(params.get('damping_coefficient_nsm', 220.0))))
        eff = max(0.10, min(0.70, float(params.get('transducer_efficiency', 0.45))))

        if 'manual_power_w' in params and params['manual_power_w'] is not None:
            power_w = max(0.0, float(params['manual_power_w']))
            method = 'demonstration_input'
            quality = 'demonstration_mode'
            notes = "Manual test input for suspension vibration harvester."
        else:
            # Power = 4 wheels * 0.5 * c * v^2 * eta
            power_w = 4.0 * 0.5 * damping_c * (stroke_v ** 2) * eff
            power_w = min(50.0, power_w)  # Physical limit for micro-kinetic harvesters
            method = 'research_estimate'
            quality = 'experimental_estimate'
            notes = "Research estimate based on ISO-8608 suspension dynamics. Experimental only."

        return max(0.0, round(power_w, 2)), round(eff, 3), method, quality, notes

    return 0.0, 0.0, 'unknown', 'unknown', 'Unrecognized source'


def update_source(source_id, update_data):
    """Update source configuration, active power, and parameters in SQLite."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sources WHERE id = ?", (source_id,))
        row = cursor.fetchone()
        if not row:
            return None

        # Merge existing parameters
        existing_params = {}
        try:
            existing_params = json.loads(row['parameters_json']) if row['parameters_json'] else {}
        except Exception:
            pass

        new_params = update_data.get('parameters', {})
        merged_params = {**existing_params, **new_params}

        # Handle direct fields
        enabled = int(update_data.get('enabled', row['enabled']))
        status = update_data.get('operating_status', row['operating_status'])
        if not enabled:
            status = 'disabled'
        elif status == 'disabled' and enabled:
            status = 'active'

        # Re-evaluate power if enabled
        if enabled:
            calc_p, eff, method, quality, notes = calculate_source_power(source_id, merged_params)
            merged_params['last_notes'] = notes
            current_p = calc_p
        else:
            current_p = 0.0
            eff = float(row['efficiency'])
            method = row['measurement_method']
            quality = row['data_quality']

        # Update accumulated energy if duration or delta_energy provided
        acc_energy = float(row['accumulated_energy_wh'])
        if 'delta_energy_wh' in update_data:
            acc_energy += float(update_data['delta_energy_wh'])
        elif 'duration_hours' in update_data and enabled:
            acc_energy += current_p * float(update_data['duration_hours'])

        now_iso = datetime.now().isoformat()
        cursor.execute("""
            UPDATE sources
            SET enabled = ?, operating_status = ?, current_power_w = ?,
                accumulated_energy_wh = ?, efficiency = ?, measurement_method = ?,
                data_quality = ?, parameters_json = ?, last_updated = ?
            WHERE id = ?
        """, (
            enabled, status, current_p, acc_energy, eff, method,
            quality, json.dumps(merged_params), now_iso, source_id
        ))
        conn.commit()

    return get_source_by_id(source_id)


def get_source_by_id(source_id):
    """Retrieve single source details."""
    sources = get_all_sources()
    for s in sources:
        if s['id'] == source_id:
            return s
    return None


def get_sources_summary(dc_dc_efficiency=0.94):
    """
    Computes system-level auxiliary power and energy totals across all active sources.
    Accounts for conversion losses through DC-DC buck/boost stage.
    """
    sources = get_all_sources()

    total_generated_w = 0.0
    total_accumulated_wh = 0.0
    active_sources_count = 0

    for s in sources:
        if s['enabled'] and s['operating_status'] != 'disabled':
            total_generated_w += s['current_power_w']
            total_accumulated_wh += s['accumulated_energy_wh']
            active_sources_count += 1

    # Usable power after conversion stage
    usable_power_w = total_generated_w * dc_dc_efficiency
    conversion_loss_w = total_generated_w - usable_power_w

    usable_energy_wh = total_accumulated_wh * dc_dc_efficiency
    conversion_loss_wh = total_accumulated_wh - usable_energy_wh

    return {
        'total_generated_w': round(total_generated_w, 2),
        'usable_power_w': round(usable_power_w, 2),
        'conversion_loss_w': round(conversion_loss_w, 2),
        'total_accumulated_wh': round(total_accumulated_wh, 2),
        'usable_energy_wh': round(usable_energy_wh, 2),
        'conversion_loss_wh': round(conversion_loss_wh, 2),
        'dc_dc_efficiency': round(dc_dc_efficiency, 3),
        'active_sources_count': active_sources_count,
        'sources': sources
    }
