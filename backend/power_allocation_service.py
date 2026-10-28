"""
================================================================================
POWER ALLOCATION SERVICE: INTELLIGENT AUXILIARY POWER ALLOCATION ENGINE
================================================================================
Core Optimization Engine:
  - Takes available power from harvested auxiliary sources (Regen, Solar, Vibration)
  - Accounts for DC-DC conversion efficiency & thermal losses (P_usable = P_gen * eta_conv)
  - Prioritizes eligible low-voltage electrical loads (Safety, Control, Telematics, Thermal, Cockpit)
  - Greedily allocates available usable power to highest-priority loads
  - Retains the Main Traction Battery as an uninterruptible fallback supply when enabled
  - Accurately tracks unmet demand when fallback is disabled
  - Strict energy conservation: No negative allocations, no double-counting
  - Calculates Battery Energy Avoided, Auxiliary Utilization %, and Unmet Demand
================================================================================
"""

import json
from datetime import datetime
from backend.database import get_connection
from backend.energy_sources_service import get_sources_summary, update_source

# Canonical demonstration loads (Total demand = 320.0 W)
DEFAULT_DEMO_LOADS = [
    (
        'load_sensors',
        'Sensors & Drive Dynamics Monitoring',
        'Safety & Control',
        1,
        40.0,
        12.0,
        1,
        1,
        'LiDAR, Radar, IMU, wheel speed sensors, and battery BMS sensor nodes.'
    ),
    (
        'load_ecu',
        'Low-Power Control Electronics (ECU / Gateway)',
        'Safety & Control',
        1,
        45.0,
        12.0,
        1,
        1,
        'Primary vehicle control unit, CAN/Ethernet gateway, and drive-by-wire controller.'
    ),
    (
        'load_telematics',
        'Communication & Telematics (V2X / GPS / 5G)',
        'Connectivity',
        2,
        25.0,
        12.0,
        1,
        0,
        'Vehicle telematics control unit (TCU), eCall, GPS positioning, and fleet diagnostics.'
    ),
    (
        'load_pump',
        'Battery Thermal Coolant Circulation Pump',
        'Thermal Management',
        3,
        65.0,
        12.0,
        1,
        0,
        'Auxiliary low-voltage coolant circulation pump for pack thermal equalization.'
    ),
    (
        'load_display',
        'Digital Instrument Cluster & Driver Display',
        'Cockpit & UI',
        4,
        50.0,
        12.0,
        1,
        0,
        'High-brightness driver digital instrument cluster and HUD module.'
    ),
    (
        'load_infotainment',
        'Center Infotainment & Cockpit Processor',
        'Infotainment',
        4,
        60.0,
        12.0,
        1,
        0,
        'Central cockpit computing unit, navigation processing, and audio amp.'
    ),
    (
        'load_amenities',
        'Auxiliary Cabin Amenities & USB-C Ports',
        'Convenience',
        5,
        35.0,
        12.0,
        1,
        0,
        'Passenger device charging ports (USB-PD) and interior ambient LEDs.'
    )
]


def reset_demo_loads():
    """Resets the loads table to canonical 7 demonstration loads (320 W total)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM loads")
        cursor.executemany("""
            INSERT INTO loads (
                id, name, category, priority, power_demand_w,
                voltage_v, enabled, critical, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, DEFAULT_DEMO_LOADS)
        conn.commit()


def get_all_loads():
    """Retrieve all configurable auxiliary electrical loads; seeds defaults if empty."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM loads ORDER BY priority ASC, power_demand_w DESC")
        rows = cursor.fetchall()

        if len(rows) == 0:
            reset_demo_loads()
            cursor.execute("SELECT * FROM loads ORDER BY priority ASC, power_demand_w DESC")
            rows = cursor.fetchall()

        loads = []
        for r in rows:
            loads.append({
                'id': r['id'],
                'name': r['name'],
                'category': r['category'],
                'priority': int(r['priority']),
                'power_demand_w': float(r['power_demand_w']),
                'voltage_v': float(r['voltage_v']),
                'enabled': bool(r['enabled']),
                'critical': bool(r['critical']),
                'description': r['description']
            })
        return loads


def add_or_update_load(load_data):
    """Create or modify an auxiliary electrical load configuration."""
    load_id = load_data.get('id')
    name = load_data.get('name', 'Custom Auxiliary Load')
    category = load_data.get('category', 'Auxiliary')
    priority = int(load_data.get('priority', 3))
    power_demand_w = max(0.0, float(load_data.get('power_demand_w', 30.0)))
    voltage_v = float(load_data.get('voltage_v', 12.0))
    enabled = 1 if load_data.get('enabled', True) else 0
    critical = 1 if load_data.get('critical', False) else 0
    description = load_data.get('description', '')

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO loads (
                id, name, category, priority, power_demand_w,
                voltage_v, enabled, critical, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                category = excluded.category,
                priority = excluded.priority,
                power_demand_w = excluded.power_demand_w,
                voltage_v = excluded.voltage_v,
                enabled = excluded.enabled,
                critical = excluded.critical,
                description = excluded.description
        """, (load_id, name, category, priority, power_demand_w, voltage_v, enabled, critical, description))
        conn.commit()

    return get_load_by_id(load_id)


def delete_load(load_id):
    """Remove a load from configuration."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM loads WHERE id = ?", (load_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_load_by_id(load_id):
    """Fetch single load definition."""
    loads = get_all_loads()
    for l in loads:
        if l['id'] == load_id:
            return l
    return None


def execute_power_allocation(duration_hours=1.0, allow_main_battery_fallback=True, dc_dc_efficiency=0.94):
    """
    Executes the deterministic, priority-ranked power allocation algorithm.
    Energy conservation law:
      Total Generated (W) = Usable Aux Power (W) + Conversion Loss (W)
      Total Demand (W) = Aux Power Allocated (W) + Main Battery Supplied (W) + Unmet Demand (W)
      Battery Energy Avoided (Wh) = Aux Power Allocated (W) * Duration (hours)
      Usable Energy (Wh) = Usable Aux Power (W) * Duration (hours)
    """
    duration_hours = max(0.01, min(24.0, float(duration_hours)))
    dc_dc_efficiency = max(0.50, min(1.0, float(dc_dc_efficiency)))

    # 1. Fetch available source telemetry
    sources_summary = get_sources_summary(dc_dc_efficiency)
    total_gen_w = sources_summary['total_generated_w']
    usable_aux_w = round(total_gen_w * dc_dc_efficiency, 2)
    conv_loss_w = round(total_gen_w - usable_aux_w, 2)

    # 2. Fetch and filter eligible loads
    all_loads = get_all_loads()
    active_loads = [l for l in all_loads if l['enabled']]

    # Sort strictly by priority (1 is highest priority), then critical flag, then load demand
    active_loads.sort(key=lambda x: (x['priority'], -int(x['critical']), -x['power_demand_w']))

    # 3. Greedy priority allocation
    remaining_usable_w = usable_aux_w
    load_allocations = []

    total_demand_w = 0.0
    total_allocated_w = 0.0
    total_battery_supplied_w = 0.0
    total_unmet_w = 0.0

    for l in active_loads:
        demand = l['power_demand_w']
        total_demand_w += demand

        # Power allocated from harvested auxiliary sources
        if remaining_usable_w >= demand:
            allocated_w = demand
            remaining_usable_w = round(remaining_usable_w - demand, 2)
        elif remaining_usable_w > 0.0:
            allocated_w = remaining_usable_w
            remaining_usable_w = 0.0
        else:
            allocated_w = 0.0

        total_allocated_w += allocated_w
        shortfall_w = round(demand - allocated_w, 2)

        # Main traction battery fallback
        if allow_main_battery_fallback:
            battery_supplied_w = shortfall_w
            unmet_w = 0.0
        else:
            battery_supplied_w = 0.0
            unmet_w = shortfall_w

        total_battery_supplied_w += battery_supplied_w
        total_unmet_w += unmet_w

        # Fractional coverage
        coverage_pct = round((allocated_w / demand * 100.0), 1) if demand > 0 else 100.0

        # Exact, honest supply source label
        if coverage_pct >= 99.9:
            supplied_by = '100% Auxiliary'
        elif allow_main_battery_fallback:
            supplied_by = 'Hybrid (Aux + Battery)' if coverage_pct > 0 else 'Main Battery'
        else:
            supplied_by = 'Partial Aux (Unmet Deficit)' if coverage_pct > 0 else 'Unmet (Load Shed)'

        load_allocations.append({
            'load_id': l['id'],
            'name': l['name'],
            'category': l['category'],
            'priority': l['priority'],
            'critical': l['critical'],
            'demand_w': round(demand, 2),
            'allocated_aux_w': round(allocated_w, 2),
            'battery_supplied_w': round(battery_supplied_w, 2),
            'unmet_w': round(unmet_w, 2),
            'coverage_pct': coverage_pct,
            'supplied_by': supplied_by
        })

    # Round power sums
    total_demand_w = round(total_demand_w, 2)
    total_allocated_w = round(total_allocated_w, 2)
    total_battery_supplied_w = round(total_battery_supplied_w, 2)
    total_unmet_w = round(total_unmet_w, 2)
    surplus_aux_w = round(max(0.0, remaining_usable_w), 2)

    # 4. Integrate across time window to obtain Energy in Watt-hours (Wh)
    # Energy (Wh) = Power (W) * Time (hours)
    total_gen_wh = round(total_gen_w * duration_hours, 2)
    usable_aux_wh = round(usable_aux_w * duration_hours, 2)
    conv_loss_wh = round(conv_loss_w * duration_hours, 2)
    total_demand_wh = round(total_demand_w * duration_hours, 2)
    total_allocated_wh = round(total_allocated_w * duration_hours, 2)
    battery_supplied_wh = round(total_battery_supplied_w * duration_hours, 2)
    battery_energy_avoided_wh = total_allocated_wh
    unmet_demand_wh = round(total_unmet_w * duration_hours, 2)
    surplus_aux_wh = round(surplus_aux_w * duration_hours, 2)

    # 5. Energy utilization metric
    utilization_pct = round((total_allocated_w / usable_aux_w * 100.0), 1) if usable_aux_w > 0 else 0.0
    utilization_pct = min(100.0, max(0.0, utilization_pct))

    # Clear surplus note
    if surplus_aux_w > 0:
        surplus_status_note = "Surplus usable auxiliary power is unallocated and left idle; no auxiliary storage battery buffer is installed in this model."
    else:
        surplus_status_note = "No surplus auxiliary energy; all usable harvested power was utilized by eligible loads."

    # 6. Build persistent result record
    now_iso = datetime.now().isoformat()
    result_record = {
        'timestamp': now_iso,
        'duration_hours': duration_hours,
        'allow_main_battery_fallback': allow_main_battery_fallback,
        'energy_accounting': {
            'total_generated_w': total_gen_w,
            'total_generated_wh': total_gen_wh,
            'usable_aux_w': usable_aux_w,
            'usable_aux_wh': usable_aux_wh,
            'conversion_loss_w': conv_loss_w,
            'conversion_loss_wh': conv_loss_wh,
            'dc_dc_efficiency': round(dc_dc_efficiency, 3),
            'total_demand_w': total_demand_w,
            'total_demand_wh': total_demand_wh,
            'total_allocated_w': total_allocated_w,
            'total_allocated_wh': total_allocated_wh,
            'main_battery_supplied_w': total_battery_supplied_w,
            'main_battery_supplied_wh': battery_supplied_wh,
            'battery_energy_avoided_wh': battery_energy_avoided_wh,
            'battery_energy_avoided_kwh': round(battery_energy_avoided_wh / 1000.0, 4),
            'unmet_demand_w': total_unmet_w,
            'unmet_demand_wh': unmet_demand_wh,
            'surplus_aux_w': surplus_aux_w,
            'surplus_aux_wh': surplus_aux_wh,
            'utilization_pct': utilization_pct,
            'surplus_status_note': surplus_status_note
        },
        'loads_allocated_count': len(active_loads),
        'load_allocations': load_allocations,
        'active_sources': sources_summary['sources']
    }

    # Persist in SQLite
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO allocation_history (
                timestamp, duration_hours, total_generated_w, total_generated_wh,
                usable_aux_w, usable_aux_wh, conversion_loss_wh,
                total_demand_w, total_demand_wh, total_allocated_w,
                total_allocated_wh, main_battery_supplied_w, main_battery_supplied_wh,
                battery_energy_avoided_wh, unmet_demand_wh, utilization_pct, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            now_iso, duration_hours, total_gen_w, total_gen_wh,
            usable_aux_w, usable_aux_wh, conv_loss_wh,
            total_demand_w, total_demand_wh, total_allocated_w,
            total_allocated_wh, total_battery_supplied_w, battery_supplied_wh,
            battery_energy_avoided_wh, unmet_demand_wh, utilization_pct,
            json.dumps(result_record)
        ))
        conn.commit()
        result_record['history_id'] = cursor.lastrowid

    return result_record


def apply_demo_scenario(scenario_id="A", allow_fallback=True, duration_hours=1.0):
    """
    Applies clearly labelled evaluation scenarios:
      Scenario A: Total Source Power = 430 W, Eff = 94%, Load Demand = 320 W
                  Usable: 404.2 W, Aux Allocated: 320 W, Fallback: 0 W, Surplus: 84.2 W, Loss: 25.8 W
      Scenario B: Total Source Power = 200 W, Eff = 94%, Load Demand = 320 W
                  Usable: 188.0 W, Aux Allocated: 188 W, Fallback: 132 W, Surplus: 0 W, Loss: 12.0 W
    """
    # 1. Reset loads to 7 default demonstration loads (sum = 320 W)
    reset_demo_loads()

    # 2. Configure source telemetry
    if scenario_id.upper() == "A":
        # Scenario A: 430 W total (220W Regen + 210W Solar + 0W Vibration)
        update_source('regen', {
            'enabled': True,
            'operating_status': 'active',
            'parameters': {'manual_power_w': 220.0, 'vehicle_mass_kg': 1650.0, 'speed_kmh': 55.0, 'deceleration_ms2': 1.8}
        })
        update_source('solar', {
            'enabled': True,
            'operating_status': 'active',
            'parameters': {'manual_power_w': 210.0, 'panel_area_m2': 1.85, 'solar_irradiance_wm2': 750.0}
        })
        update_source('vibration', {
            'enabled': False,
            'operating_status': 'disabled',
            'parameters': {'manual_power_w': 0.0}
        })
    elif scenario_id.upper() == "B":
        # Scenario B: 200 W total (100W Regen + 100W Solar + 0W Vibration)
        update_source('regen', {
            'enabled': True,
            'operating_status': 'active',
            'parameters': {'manual_power_w': 100.0, 'vehicle_mass_kg': 1650.0, 'speed_kmh': 40.0, 'deceleration_ms2': 1.0}
        })
        update_source('solar', {
            'enabled': True,
            'operating_status': 'active',
            'parameters': {'manual_power_w': 100.0, 'panel_area_m2': 1.5, 'solar_irradiance_wm2': 400.0}
        })
        update_source('vibration', {
            'enabled': False,
            'operating_status': 'disabled',
            'parameters': {'manual_power_w': 0.0}
        })

    # 3. Execute power allocation with 94% DC-DC efficiency
    return execute_power_allocation(
        duration_hours=duration_hours,
        allow_main_battery_fallback=allow_fallback,
        dc_dc_efficiency=0.94
    )


def get_allocation_history(limit=25):
    """Retrieve historical power allocation audit trail."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM allocation_history ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        records = []
        for r in rows:
            records.append({
                'id': r['id'],
                'timestamp': r['timestamp'],
                'duration_hours': r['duration_hours'],
                'total_generated_wh': r['total_generated_wh'],
                'usable_aux_wh': r['usable_aux_wh'],
                'conversion_loss_wh': r['conversion_loss_wh'],
                'total_allocated_wh': r['total_allocated_wh'],
                'main_battery_supplied_wh': r['main_battery_supplied_wh'],
                'battery_energy_avoided_wh': r['battery_energy_avoided_wh'],
                'unmet_demand_wh': r['unmet_demand_wh'],
                'utilization_pct': r['utilization_pct'],
                'details': json.loads(r['details_json']) if r['details_json'] else {}
            })
        return records


def clear_allocation_history():
    """Clear all historical allocation logs."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM allocation_history")
        conn.commit()
        return True
