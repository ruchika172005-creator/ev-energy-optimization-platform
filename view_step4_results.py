"""
================================================================================
VIEW STEP 4 REGRESSION RESULTS
================================================================================
"""
import os
import sys
import pandas as pd
import joblib

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

print("=" * 80)
print("             STEP 4: SAVED REGRESSION EXPERIMENT RESULTS")
print("=" * 80)

# 1. Benchmark Table
results_file = "regression_model_results.csv"
if os.path.exists(results_file):
    df_res = pd.read_csv(results_file)
    print("\nMODEL PERFORMANCE COMPARISON:")
    print("-" * 80)
    print(f"{'Model':<30} | {'MAE (kWh)':<10} | {'RMSE (kWh)':<10} | {'R²':<8}")
    print("-" * 80)
    for _, row in df_res.iterrows():
        print(f"{row['Model']:<30} | {row['MAE']:<10.4f} | {row['RMSE']:<10.4f} | {row['R²']:<8.4f}")
    print("-" * 80)
else:
    print(f"\n[!] Missing file: {results_file}")

# 2. Best Model & Saved Pipeline
model_file = "best_energy_prediction_model.joblib"
if os.path.exists(model_file):
    pipeline = joblib.load(model_file)
    regressor = pipeline.named_steps['regressor']
    print(f"\nPersisted Model Pipeline : {model_file}")
    print(f"Loaded Regressor Class   : {regressor.__class__.__name__}")
else:
    print(f"\n[!] Missing file: {model_file}")

# 3. Sample Predictions
pred_file = "predictions_best_model.csv"
if os.path.exists(pred_file):
    df_preds = pd.read_csv(pred_file)
    print(f"\nTest Set Predictions Sample ({len(df_preds):,} total test samples):")
    print("-" * 80)
    print(df_preds.head(8).to_string(index=False))
else:
    print(f"\n[!] Missing file: {pred_file}")

# 4. Generated Graphs
print("\nGenerated Graph Artifacts:")
for img in [
    "regression_model_comparison.png",
    "actual_vs_predicted_best_model.png",
    "residual_plot_best_model.png",
    "feature_importance_best_model.png"
]:
    status = "EXISTS" if os.path.exists(img) else "MISSING"
    print(f" - {img:<35} [{status}]")

print("=" * 80)
