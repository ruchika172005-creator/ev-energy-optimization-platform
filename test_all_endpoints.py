"""
Comprehensive End-to-End Test Suite for Phase 2 Evaluation.
Tests Scenario A, Scenario B (with and without fallback), zero generation,
conservation laws, edge cases, and ML model diagnostics.
"""

import json
from app import app
from backend.power_allocation_service import apply_demo_scenario, reset_demo_loads

def test_phase2_evaluation():
    client = app.test_client()
    print("=" * 80)
    print("PHASE 2 EVALUATION: COMPREHENSIVE FLASK REST API TEST SUITE")
    print("=" * 80)

    # 1. Health check
    print("\n[TEST 1] System Health & Model Readiness (GET /api/health)")
    res = client.get('/api/health')
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'healthy'
    assert data['model_status']['loaded'] is True
    print("  -> PASSED: Health status healthy, Scikit-learn GBR model loaded.")

    # 2. SCENARIO A: 430W Generation -> 320W Demand
    print("\n[TEST 2] DEMO SCENARIO A: 430W Harvest -> 320W Demand, Eff=94%, 1 Hr")
    res_a = client.post('/api/energy/demo-scenario', json={
        'scenario': 'A',
        'allow_main_battery_fallback': True,
        'duration_hours': 1.0
    })
    assert res_a.status_code == 200
    alloc_a = res_a.get_json()['allocation']['energy_accounting']

    print(f"  * Total Generated:    {alloc_a['total_generated_w']} W ({alloc_a['total_generated_wh']} Wh)")
    print(f"  * Conversion Loss:    {alloc_a['conversion_loss_w']} W ({alloc_a['conversion_loss_wh']} Wh)")
    print(f"  * Usable Aux Power:   {alloc_a['usable_aux_w']} W ({alloc_a['usable_aux_wh']} Wh)")
    print(f"  * Total Load Demand:  {alloc_a['total_demand_w']} W ({alloc_a['total_demand_wh']} Wh)")
    print(f"  * Aux Allocated:      {alloc_a['total_allocated_w']} W ({alloc_a['total_allocated_wh']} Wh)")
    print(f"  * Battery Fallback:   {alloc_a['main_battery_supplied_w']} W ({alloc_a['main_battery_supplied_wh']} Wh)")
    print(f"  * Surplus Usable:     {alloc_a['surplus_aux_w']} W ({alloc_a['surplus_aux_wh']} Wh)")
    print(f"  * Battery Avoided:    {alloc_a['battery_energy_avoided_wh']} Wh")

    # Strict numerical assertions matching prompt requirements
    assert alloc_a['total_generated_w'] == 430.0
    assert alloc_a['usable_aux_w'] == 404.2
    assert alloc_a['conversion_loss_w'] == 25.8
    assert alloc_a['total_demand_w'] == 320.0
    assert alloc_a['total_allocated_w'] == 320.0
    assert alloc_a['main_battery_supplied_w'] == 0.0
    assert alloc_a['surplus_aux_w'] == 84.2
    assert alloc_a['battery_energy_avoided_wh'] == 320.0
    print("  -> PASSED: Scenario A matches all expected numerical values exactly!")

    # 3. SCENARIO B: 200W Generation -> 320W Demand (Fallback ENABLED)
    print("\n[TEST 3] DEMO SCENARIO B: 200W Harvest -> 320W Demand, Eff=94%, Fallback=ON")
    res_b = client.post('/api/energy/demo-scenario', json={
        'scenario': 'B',
        'allow_main_battery_fallback': True,
        'duration_hours': 1.0
    })
    assert res_b.status_code == 200
    alloc_b = res_b.get_json()['allocation']['energy_accounting']

    print(f"  * Total Generated:    {alloc_b['total_generated_w']} W ({alloc_b['total_generated_wh']} Wh)")
    print(f"  * Conversion Loss:    {alloc_b['conversion_loss_w']} W ({alloc_b['conversion_loss_wh']} Wh)")
    print(f"  * Usable Aux Power:   {alloc_b['usable_aux_w']} W ({alloc_b['usable_aux_wh']} Wh)")
    print(f"  * Total Load Demand:  {alloc_b['total_demand_w']} W ({alloc_b['total_demand_wh']} Wh)")
    print(f"  * Aux Allocated:      {alloc_b['total_allocated_w']} W ({alloc_b['total_allocated_wh']} Wh)")
    print(f"  * Battery Fallback:   {alloc_b['main_battery_supplied_w']} W ({alloc_b['main_battery_supplied_wh']} Wh)")
    print(f"  * Surplus Usable:     {alloc_b['surplus_aux_w']} W ({alloc_b['surplus_aux_wh']} Wh)")
    print(f"  * Unmet Demand:       {alloc_b['unmet_demand_w']} W ({alloc_b['unmet_demand_wh']} Wh)")

    # Strict numerical assertions matching prompt requirements
    assert alloc_b['total_generated_w'] == 200.0
    assert alloc_b['usable_aux_w'] == 188.0
    assert alloc_b['conversion_loss_w'] == 12.0
    assert alloc_b['total_demand_w'] == 320.0
    assert alloc_b['total_allocated_w'] == 188.0
    assert alloc_b['main_battery_supplied_w'] == 132.0
    assert alloc_b['surplus_aux_w'] == 0.0
    assert alloc_b['unmet_demand_w'] == 0.0
    assert alloc_b['battery_energy_avoided_wh'] == 188.0
    print("  -> PASSED: Scenario B with battery fallback matches expected values exactly!")

    # 4. SCENARIO B with Fallback DISABLED (Reporting Unmet Demand)
    print("\n[TEST 4] DEMO SCENARIO B: Fallback=DISABLED (Testing Unmet Demand Reporting)")
    res_b_nofallback = client.post('/api/energy/demo-scenario', json={
        'scenario': 'B',
        'allow_main_battery_fallback': False,
        'duration_hours': 1.0
    })
    assert res_b_nofallback.status_code == 200
    alloc_b_nf = res_b_nofallback.get_json()['allocation']['energy_accounting']

    assert alloc_b_nf['main_battery_supplied_w'] == 0.0, "Main battery supplied energy when fallback was disabled!"
    assert alloc_b_nf['unmet_demand_w'] == 132.0, "Unmet demand was not accurately reported!"
    assert alloc_b_nf['unmet_demand_wh'] == 132.0, "Unmet demand Wh was not accurately integrated!"
    print("  -> PASSED: With fallback disabled, 132 W / 132 Wh deficit is accurately reported as unmet demand.")

    # 5. Load Management & Custom Load Addition
    print("\n[TEST 5] Configure Eligible Load & Table Update")
    res_add = client.post('/api/energy/loads', json={
        'id': 'test_lidar_sensor',
        'name': 'Test Solid-State LiDAR Sensor',
        'category': 'Safety & Control',
        'priority': 1,
        'power_demand_w': 35.0,
        'voltage_v': 12.0,
        'critical': True
    })
    assert res_add.status_code == 200
    loads_res = client.get('/api/energy/loads')
    assert loads_res.get_json()['count'] == 8
    print("  -> PASSED: Added new load 'test_lidar_sensor', count increased to 8.")

    # Clean up test load
    client.delete('/api/energy/loads/test_lidar_sensor')

    # 6. Edge Case: Zero Generation (All sources disabled)
    print("\n[TEST 6] Edge Case: Zero Auxiliary Generation (Sources Off)")
    client.post('/api/energy/sources', json={'source_id': 'regen', 'enabled': False})
    client.post('/api/energy/sources', json={'source_id': 'solar', 'enabled': False})
    client.post('/api/energy/sources', json={'source_id': 'vibration', 'enabled': False})

    res_zero = client.post('/api/energy/allocate', json={'duration_hours': 1.0, 'allow_main_battery_fallback': True})
    assert res_zero.status_code == 200
    zero_acc = res_zero.get_json()['allocation']['energy_accounting']
    assert zero_acc['total_allocated_w'] == 0.0
    assert zero_acc['main_battery_supplied_w'] == zero_acc['total_demand_w']
    assert zero_acc['battery_energy_avoided_wh'] == 0.0
    print("  -> PASSED: With 0W generation, 100% of demand safely fell back to main battery.")

    # Restore Scenario A
    apply_demo_scenario('A')

    # 7. Energy Summary & Battery Impact (Never Null)
    print("\n[TEST 7] Energy Summary & Battery Impact (GET /api/energy/summary & /api/battery/impact)")
    res_sum = client.get('/api/energy/summary')
    assert res_sum.status_code == 200
    assert res_sum.get_json()['last_allocation'] is not None

    res_imp = client.get('/api/battery/impact')
    assert res_imp.status_code == 200
    imp = res_imp.get_json()['impact']['session_impact']
    assert imp['battery_energy_avoided_wh'] == 320.0
    assert imp['equivalent_range_conserved_km'] == round(0.32 / 0.2215, 2)
    print(f"  -> PASSED: Battery energy avoided {imp['battery_energy_avoided_wh']} Wh -> {imp['equivalent_range_conserved_km']} km range parity.")

    # 8. Model Diagnostics (Verifying Actual CSV Numbers)
    print("\n[TEST 8] Model Diagnostics Leaderboard (GET /api/models/metrics)")
    res_diag = client.get('/api/models/metrics')
    assert res_diag.status_code == 200
    models = res_diag.get_json()['metrics']['models']

    gbr = next(m for m in models if 'Gradient Boosting' in m['model_name'])
    rf = next(m for m in models if 'Random Forest' in m['model_name'])
    lr = next(m for m in models if 'Linear Regression' in m['model_name'])

    assert gbr['r2_score'] == 0.8713
    assert gbr['rmse_kwh'] == 1.0216
    assert gbr['mae_kwh'] == 0.6792

    assert rf['r2_score'] == 0.8615
    assert rf['rmse_kwh'] == 1.0598

    assert lr['r2_score'] == 0.8421
    assert lr['rmse_kwh'] == 1.1316
    print(f"  -> PASSED: Diagnosed actual recorded metrics: GBR R²=0.8713, RF R²=0.8615, LR R²=0.8421.")

    print("\n" + "=" * 80)
    print("ALL 8 PHASE 2 EVALUATION TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 80)

if __name__ == '__main__':
    test_phase2_evaluation()
