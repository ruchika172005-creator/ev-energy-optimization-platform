"""
================================================================================
DATABASE MODULE: EV AUXILIARY ENERGY & POWER ALLOCATION PERSISTENCE
================================================================================
Manages persistent SQLite storage for:
  - Auxiliary energy harvesting sources (Regen, Solar, Vibration)
  - Configurable electrical loads and priority tables
  - Power allocation audit history and energy conservation logs
  - System settings and operating configuration
================================================================================
"""

import os
import json
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "ev_auxiliary_energy.db")


def get_connection():
    """Create and return a thread-safe connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes tables and seeds default sources and loads if empty."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # 1. Sources table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                source_type TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                operating_status TEXT DEFAULT 'active',
                rated_power_w REAL DEFAULT 0.0,
                current_power_w REAL DEFAULT 0.0,
                accumulated_energy_wh REAL DEFAULT 0.0,
                efficiency REAL DEFAULT 0.85,
                measurement_method TEXT DEFAULT 'demonstration_input',
                data_quality TEXT DEFAULT 'verified_model',
                parameters_json TEXT DEFAULT '{}',
                last_updated TEXT
            )
        """)

        # 2. Electrical loads table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loads (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                priority INTEGER NOT NULL,
                power_demand_w REAL NOT NULL,
                voltage_v REAL DEFAULT 12.0,
                enabled INTEGER DEFAULT 1,
                critical INTEGER DEFAULT 0,
                description TEXT
            )
        """)

        # 3. Allocation history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS allocation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                duration_hours REAL DEFAULT 1.0,
                total_generated_w REAL NOT NULL,
                total_generated_wh REAL NOT NULL,
                usable_aux_w REAL NOT NULL,
                usable_aux_wh REAL NOT NULL,
                conversion_loss_wh REAL NOT NULL,
                total_demand_w REAL NOT NULL,
                total_demand_wh REAL NOT NULL,
                total_allocated_w REAL NOT NULL,
                total_allocated_wh REAL NOT NULL,
                main_battery_supplied_w REAL NOT NULL,
                main_battery_supplied_wh REAL NOT NULL,
                battery_energy_avoided_wh REAL NOT NULL,
                unmet_demand_wh REAL DEFAULT 0.0,
                utilization_pct REAL NOT NULL,
                details_json TEXT NOT NULL
            )
        """)

        # 4. System Settings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        # Seed default sources if empty
        cursor.execute("SELECT COUNT(*) FROM sources")
        if cursor.fetchone()[0] == 0:
            now_iso = datetime.now().isoformat()
            default_sources = [
                (
                    'regen',
                    'Regenerative Braking Energy Recovery',
                    'regenerative_braking',
                    1,
                    'active',
                    450.0,
                    220.0,
                    165.0,
                    0.82,
                    'kinematic_model',
                    'verified_model',
                    json.dumps({
                        'vehicle_mass_kg': 1650.0,
                        'speed_kmh': 55.0,
                        'deceleration_ms2': 1.8,
                        'regen_fraction': 0.70,
                        'motor_generator_efficiency': 0.88,
                        'inverter_efficiency': 0.94,
                        'description': 'Kinetic energy recovery during vehicle deceleration events.'
                    }),
                    now_iso
                ),
                (
                    'solar',
                    'Rooftop Solar Photovoltaic Generation',
                    'solar_pv',
                    1,
                    'active',
                    380.0,
                    210.0,
                    157.5,
                    0.205,
                    'model_estimate',
                    'verified_model',
                    json.dumps({
                        'panel_area_m2': 1.85,
                        'solar_irradiance_wm2': 750.0,
                        'cell_efficiency': 0.21,
                        'mppt_efficiency': 0.96,
                        'cell_temp_c': 28.0,
                        'temp_coefficient': -0.0038,
                        'shading_loss_factor': 0.05,
                        'description': 'High-efficiency monocrystalline rooftop solar with MPPT tracking.'
                    }),
                    now_iso
                ),
                (
                    'vibration',
                    'Regenerative Suspension Vibration Harvester (Optional)',
                    'vibration',
                    0,
                    'disabled',
                    35.0,
                    0.0,
                    0.0,
                    0.45,
                    'research_estimate',
                    'experimental_estimate',
                    json.dumps({
                        'road_roughness_class': 'ISO_Class_C',
                        'suspension_stroke_velocity_ms': 0.12,
                        'transducer_type': 'electromagnetic_linear',
                        'transducer_efficiency': 0.45,
                        'damping_coefficient_nsm': 220.0,
                        'description': 'Electromagnetic kinetic energy recovery from chassis vibration. Clearly labelled as experimental estimate.'
                    }),
                    now_iso
                )
            ]
            cursor.executemany("""
                INSERT INTO sources (
                    id, name, source_type, enabled, operating_status,
                    rated_power_w, current_power_w, accumulated_energy_wh,
                    efficiency, measurement_method, data_quality,
                    parameters_json, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, default_sources)

        # Seed default loads if empty
        cursor.execute("SELECT COUNT(*) FROM loads")
        if cursor.fetchone()[0] == 0:
            default_loads = [
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
            cursor.executemany("""
                INSERT INTO loads (
                    id, name, category, priority, power_demand_w,
                    voltage_v, enabled, critical, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, default_loads)

        # Seed default settings if empty
        cursor.execute("SELECT COUNT(*) FROM system_settings")
        if cursor.fetchone()[0] == 0:
            default_settings = [
                ('dc_dc_efficiency', '0.94'),
                ('bus_voltage_v', '12.0'),
                ('operating_mode', 'demonstration_simulation'),
                ('main_battery_nominal_voltage_v', '360.0'),
                ('fleet_avg_consumption_kwh_per_km', '0.2215'),
                ('allow_main_battery_fallback', 'true'),
                ('safety_interlock_active', 'true')
            ]
            cursor.executemany("INSERT INTO system_settings (key, value) VALUES (?, ?)", default_settings)

        conn.commit()


# Initialize database automatically on module import
init_db()
