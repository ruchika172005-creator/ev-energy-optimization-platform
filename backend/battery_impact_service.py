"""
================================================================================
BATTERY IMPACT SERVICE: ENERGY CONSERVATION & DEGRADATION MITIGATION
================================================================================
Calculates:
  - Direct traction battery energy avoided (Wh and kWh)
  - Equivalent driving range conserved using verified fleet empirical metrics
  - Reduction in cyclic ampere-hour (Ah) throughput on high-voltage cells
  - State-of-Charge (SoC) retention benefits
  - Transparent engineering disclaimers regarding battery life extension
================================================================================
"""

import os
from backend.database import get_connection
from backend.power_allocation_service import get_allocation_history

# Empirical fleet baseline constants from cleaned_ev_data.csv (10,151 trips)
FLEET_AVG_CONSUMPTION_KWH_PER_KM = 0.2215   # 22.15 kWh / 100km
NOMINAL_PACK_VOLTAGE_V = 360.0              # Nominal high-voltage traction pack
NOMINAL_PACK_CAPACITY_KWH = 50.0            # Usable pack capacity (kWh)
PACK_INTERNAL_RESISTANCE_OHM = 0.085        # Typical internal DC resistance (Ohms)


def calculate_battery_impact(allocation_record=None):
    """
    Computes rigorous battery energy conservation and lifecycle indicators.
    If no record passed, evaluates the latest allocation or aggregate history.
    """
    if allocation_record is None:
        history = get_allocation_history(limit=1)
        if history:
            allocation_record = history[0]['details']
        else:
            allocation_record = {}

    energy_acc = allocation_record.get('energy_accounting', {})
    energy_avoided_wh = float(energy_acc.get('battery_energy_avoided_wh', 0.0))
    energy_avoided_kwh = energy_avoided_wh / 1000.0

    # 1. Equivalent driving distance conserved
    # Range (km) = Avoided Energy (kWh) / Consumption (kWh/km)
    equivalent_range_km = (energy_avoided_kwh / FLEET_AVG_CONSUMPTION_KWH_PER_KM) if FLEET_AVG_CONSUMPTION_KWH_PER_KM > 0 else 0.0

    # 2. State of Charge (SoC) preservation
    # Delta SoC (%) = (Avoided Energy / Total Usable Pack Capacity) * 100%
    soc_preserved_pct = (energy_avoided_kwh / NOMINAL_PACK_CAPACITY_KWH * 100.0) if NOMINAL_PACK_CAPACITY_KWH > 0 else 0.0

    # 3. Cyclic Ampere-Hour (Ah) throughput avoided
    # Ah avoided = Avoided Energy (Wh) / Nominal Pack Voltage (V)
    ah_throughput_avoided = (energy_avoided_wh / NOMINAL_PACK_VOLTAGE_V) if NOMINAL_PACK_VOLTAGE_V > 0 else 0.0

    # 4. Thermal Joule heating avoided in high-voltage pack (I^2 * R * t)
    # Average current avoided I_avg = P_avoided / V_nom
    # Heat avoided Q_joules = I^2 * R * (t_seconds)
    duration_hrs = float(allocation_record.get('duration_hours', 1.0))
    duration_sec = duration_hrs * 3600.0
    p_avoided_w = float(energy_acc.get('total_allocated_w', 0.0))
    i_avg_a = (p_avoided_w / NOMINAL_PACK_VOLTAGE_V) if NOMINAL_PACK_VOLTAGE_V > 0 else 0.0
    joule_heat_avoided_wh = (i_avg_a ** 2 * PACK_INTERNAL_RESISTANCE_OHM * duration_sec) / 3600.0

    # 5. Cumulative lifetime stats across all recorded sessions
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total_cycles,
                SUM(battery_energy_avoided_wh) as cum_avoided_wh,
                SUM(usable_aux_wh) as cum_usable_wh,
                AVG(utilization_pct) as avg_utilization
            FROM allocation_history
        """)
        row = cursor.fetchone()
        total_cycles = row['total_cycles'] or 0
        cum_avoided_wh = row['cum_avoided_wh'] or 0.0
        cum_avoided_kwh = cum_avoided_wh / 1000.0
        cum_range_km = cum_avoided_kwh / FLEET_AVG_CONSUMPTION_KWH_PER_KM if FLEET_AVG_CONSUMPTION_KWH_PER_KM > 0 else 0.0
        avg_utilization = row['avg_utilization'] or 0.0

    return {
        'session_impact': {
            'battery_energy_avoided_wh': round(energy_avoided_wh, 2),
            'battery_energy_avoided_kwh': round(energy_avoided_kwh, 4),
            'equivalent_range_conserved_km': round(equivalent_range_km, 2),
            'soc_preserved_pct': round(soc_preserved_pct, 2),
            'ah_throughput_avoided': round(ah_throughput_avoided, 3),
            'joule_heat_avoided_wh': round(joule_heat_avoided_wh, 3),
            'pack_nominal_voltage_v': NOMINAL_PACK_VOLTAGE_V,
            'pack_nominal_capacity_kwh': NOMINAL_PACK_CAPACITY_KWH,
            'fleet_baseline_consumption_kwh_100km': round(FLEET_AVG_CONSUMPTION_KWH_PER_KM * 100.0, 1)
        },
        'cumulative_impact': {
            'total_allocation_cycles': total_cycles,
            'cumulative_avoided_wh': round(cum_avoided_wh, 2),
            'cumulative_avoided_kwh': round(cum_avoided_kwh, 3),
            'cumulative_range_conserved_km': round(cum_range_km, 2),
            'mean_auxiliary_utilization_pct': round(avg_utilization, 1)
        },
        'engineering_notes': [
            "Equivalent range conservation is an energy parity metric based on verified fleet consumption (22.15 kWh/100km).",
            "Ampere-hour throughput reduction mitigates secondary electrochemical solid-electrolyte interphase (SEI) growth.",
            "All battery life improvements represent potential operational benefits; experimental degradation validation is required for long-term cycling claims."
        ]
    }
