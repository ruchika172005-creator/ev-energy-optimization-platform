"""
================================================================================
STEP 4: EV ENERGY CONSUMPTION REGRESSION PIPELINE
================================================================================
Project: Intelligent Energy Management System for Electric Vehicles
Stage: Supervised Machine Learning Energy Consumption Regression (Continuous Target)
Target: "Trip Energy Consumption" (kWh)

Models Evaluated:
  1. Linear Regression (Baseline Parametric)
  2. Random Forest Regressor (Non-linear Ensemble Bagging)
  3. Gradient Boosting Regressor (Non-linear Ensemble Boosting)

Protocol:
  - 80% Train / 20% Test split with fixed random_state (42)
  - Zero target leakage: all transformations fitted exclusively on training set
  - Pipeline & ColumnTransformer architecture
  - Multi-metric evaluation: MAE, RMSE, R²
  - High-resolution comparative and diagnostic plots
================================================================================
"""

import os
import sys
import functools
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Disable output buffering for immediate console feedback
print = functools.partial(print, flush=True)

# Set plotting aesthetic
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8


def calculate_rmse(y_true, y_pred):
    """Calculate Root Mean Squared Error across scikit-learn versions."""
    try:
        from sklearn.metrics import root_mean_squared_error
        return root_mean_squared_error(y_true, y_pred)
    except ImportError:
        return np.sqrt(mean_squared_error(y_true, y_pred))


def run_step4_energy_regression():
    print("=" * 80)
    print("      STEP 4: EV TRIP ENERGY CONSUMPTION REGRESSION BENCHMARK")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # 1. DATA INGESTION & AUDIT
    # -------------------------------------------------------------------------
    print("\n[1] DATA INGESTION & SELECTION")
    print("-" * 80)
    
    # Priority: cleaned dataset first, fallback to raw dataset
    cleaned_file = "cleaned_ev_data.csv"
    raw_file = "Electric Vehicle Trip Energy Consumption Data.csv"
    
    if os.path.exists(cleaned_file):
        dataset_path = cleaned_file
        print(f"Loading cleaned dataset: {cleaned_file}")
    elif os.path.exists(raw_file):
        dataset_path = raw_file
        print(f"Loading raw dataset: {raw_file}")
    else:
        raise FileNotFoundError(f"Neither '{cleaned_file}' nor '{raw_file}' was found in the workspace.")

    df = pd.read_csv(dataset_path)
    print(f"Dataset shape: {df.shape[0]:,} rows x {df.shape[1]} columns")

    # -------------------------------------------------------------------------
    # 2. FEATURE ENGINEERING (PHYSICAL & OPERATIONAL ATTRIBUTES)
    # -------------------------------------------------------------------------
    print("\n[2] FEATURE ENGINEERING & CANDIDATE SELECTION")
    print("-" * 80)

    # Calculate Battery Power (kW) = Total Voltage (V) * Current (A) / 1000
    if 'Battery Power' not in df.columns:
        if 'Total Voltage' in df.columns and 'Current' in df.columns:
            df['Battery Power'] = (df['Total Voltage'] * df['Current']) / 1000.0
            print(" -> Engineered 'Battery Power' = (Total Voltage * Current) / 1000 [kW]")
        else:
            raise KeyError("Cannot calculate 'Battery Power': 'Total Voltage' or 'Current' missing.")
    else:
        print(" -> 'Battery Power' already present in dataset.")

    # Calculate Temperature Differential = Max Temp - Min Temp
    if 'Temperature Differential' not in df.columns:
        if ('Maximum Cell Temperature of Battery' in df.columns and 
            'Minimum Cell Temperature of Battery' in df.columns):
            df['Temperature Differential'] = (
                df['Maximum Cell Temperature of Battery'] - df['Minimum Cell Temperature of Battery']
            )
            print(" -> Engineered 'Temperature Differential' = Max Cell Temp - Min Cell Temp [°C]")
        else:
            raise KeyError("Cannot calculate 'Temperature Differential': Battery temperature columns missing.")
    else:
        print(" -> 'Temperature Differential' already present in dataset.")

    # Ensure Day of the Week is categorical
    # If Day_Name is present, we use Day of the Week as discrete category
    if 'Day of the Week' in df.columns:
        day_col = 'Day of the Week'
    elif 'Day_Name' in df.columns:
        day_col = 'Day_Name'
    else:
        day_col = None

    # Candidate feature definitions
    target_col = 'Trip Energy Consumption'
    numerical_features = [
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
    categorical_features = [day_col] if day_col is not None else []
    selected_features = numerical_features + categorical_features

    # Safety checks: Confirm no target leakage features
    forbidden_features = ['Energy_per_Distance', 'Vehicle ID', target_col]
    for feat in forbidden_features:
        if feat in selected_features:
            selected_features.remove(feat)

    print(f"\nTarget Variable: '{target_col}' (Continuous Regression Target, physical unit: kWh)")
    print(f"Selected Features ({len(selected_features)} attributes):")
    for idx, feat in enumerate(selected_features, 1):
        feat_type = "Categorical" if feat in categorical_features else "Numerical"
        print(f"  {idx:2d}. {feat:<38} [{feat_type}]")

    # Isolate X and y
    X = df[selected_features].copy()
    y = df[target_col].copy()

    # Drop any NaN records if present
    valid_mask = ~(X.isnull().any(axis=1) | y.isnull())
    if (~valid_mask).sum() > 0:
        print(f"Dropping {(~valid_mask).sum()} records with missing values.")
        X = X[valid_mask]
        y = y[valid_mask]

    # Convert categorical feature to string for robust OneHotEncoding
    if categorical_features:
        for c in categorical_features:
            X[c] = X[c].astype(str)

    # -------------------------------------------------------------------------
    # 3. TRAIN / TEST SPLIT (80% / 20%)
    # -------------------------------------------------------------------------
    print("\n[3] TRAIN / TEST PARTITION")
    print("-" * 80)
    RANDOM_STATE = 42
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_STATE
    )

    print(f"Train size: {X_train.shape[0]:,} samples (80.0%)")
    print(f"Test size:  {X_test.shape[0]:,} samples (20.0%)")
    print(f"Feature matrix columns: {X_train.shape[1]}")
    print(f"Target statistics (Train) - Mean: {y_train.mean():.3f} kWh, Std: {y_train.std():.3f} kWh, Min: {y_train.min():.3f} kWh, Max: {y_train.max():.3f} kWh")
    print(f"Target statistics (Test)  - Mean: {y_test.mean():.3f} kWh, Std: {y_test.std():.3f} kWh, Min: {y_test.min():.3f} kWh, Max: {y_test.max():.3f} kWh")

    # -------------------------------------------------------------------------
    # 4. PREPROCESSING PIPELINE & COLUMN TRANSFORMER
    # -------------------------------------------------------------------------
    print("\n[4] DATA PREPROCESSING PIPELINE")
    print("-" * 80)
    print("Architecture: Scikit-learn ColumnTransformer")
    print(" -> Numerical features: StandardScaler (mean=0, variance=1) fitted ONLY on X_train")
    if categorical_features:
        print(f" -> Categorical features ({categorical_features}): OneHotEncoder(drop='first', handle_unknown='ignore') fitted ONLY on X_train")
    print(" -> Target Leakage Guarantee: Preprocessor fitted solely on training split.")

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numerical_features),
            ('cat', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'), categorical_features)
        ],
        remainder='drop'
    )

    # -------------------------------------------------------------------------
    # 5. MODEL TRAINING & BENCHMARKING
    # -------------------------------------------------------------------------
    print("\n[5] MODEL TRAINING & COMPARATIVE BENCHMARK")
    print("-" * 80)

    candidate_models = {
        "Linear Regression": LinearRegression(),
        "Random Forest Regressor": RandomForestRegressor(n_estimators=100, random_state=RANDOM_STATE, n_jobs=-1),
        "Gradient Boosting Regressor": GradientBoostingRegressor(n_estimators=100, random_state=RANDOM_STATE)
    }

    results = []
    fitted_pipelines = {}
    test_predictions = {}

    for name, model in candidate_models.items():
        print(f"Training {name}...", end=" ", flush=True)
        pipe = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('regressor', model)
        ])
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)
        
        # Calculate regression metrics
        mae = mean_absolute_error(y_test, y_pred)
        rmse = calculate_rmse(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        results.append({
            'Model': name,
            'MAE': mae,
            'RMSE': rmse,
            'R²': r2
        })
        fitted_pipelines[name] = pipe
        test_predictions[name] = y_pred
        print(f"Done. (MAE={mae:.4f} kWh, RMSE={rmse:.4f} kWh, R²={r2:.4f})")

    results_df = pd.DataFrame(results)

    # -------------------------------------------------------------------------
    # 6. EVALUATION RESULTS & METRIC INTERPRETATION
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("MODEL PERFORMANCE COMPARISON TABLE")
    print("=" * 80)
    print(f"{'Model':<30} | {'MAE (kWh)':<10} | {'RMSE (kWh)':<10} | {'R²':<8}")
    print("-" * 80)
    for _, row in results_df.iterrows():
        print(f"{row['Model']:<30} | {row['MAE']:<10.4f} | {row['RMSE']:<10.4f} | {row['R²']:<8.4f}")
    print("=" * 80)

    print("\nMETRIC DEFINITIONS & INTERPRETATION:")
    print("  • MAE  (Mean Absolute Error): Average absolute magnitude of prediction errors in kWh.")
    print("         Measures typical prediction error directly in physical units. Lower is better.")
    print("  • RMSE (Root Mean Squared Error): Square root of mean squared errors in kWh.")
    print("         Penalizes larger outliers and extreme prediction misses more severely. Lower is better.")
    print("  • R²   (Coefficient of Determination): Proportion of variance in Trip Energy Consumption")
    print("         accounted for by the model features. 1.0 represents a perfect model fit. Higher is better.")

    # -------------------------------------------------------------------------
    # 7. BEST MODEL IDENTIFICATION
    # -------------------------------------------------------------------------
    # Best model selection prioritized by lowest RMSE, lowest MAE, highest R²
    best_row = results_df.sort_values(by=['RMSE', 'MAE'], ascending=[True, True]).iloc[0]
    best_model_name = best_row['Model']
    best_mae = best_row['MAE']
    best_rmse = best_row['RMSE']
    best_r2 = best_row['R²']
    best_pipeline = fitted_pipelines[best_model_name]
    best_preds = test_predictions[best_model_name]

    print("\n" + "*" * 80)
    print(f"BEST MODEL IDENTIFIED: {best_model_name.upper()}")
    print("*" * 80)
    print(f"Selection Rationale: Lowest RMSE ({best_rmse:.4f} kWh), Lowest MAE ({best_mae:.4f} kWh), and Highest R² ({best_r2:.4f})")

    # -------------------------------------------------------------------------
    # 8. PERSISTENCE OF RESULTS & ARTIFACTS
    # -------------------------------------------------------------------------
    print("\n[8] SAVING EXPERIMENTAL RESULTS & ARTIFACTS")
    print("-" * 80)

    # 8.1 Model comparison results
    res_path = "regression_model_results.csv"
    results_df.to_csv(res_path, index=False)
    print(f" -> Saved model comparison metrics : {os.path.abspath(res_path)}")

    # 8.2 Predictions dataframe
    residuals = y_test.values - best_preds
    pred_df = pd.DataFrame({
        'Actual Energy': y_test.values,
        'Predicted Energy': best_preds,
        'Residual': residuals
    })
    pred_path = "predictions_best_model.csv"
    pred_df.to_csv(pred_path, index=False)
    print(f" -> Saved best model predictions   : {os.path.abspath(pred_path)}")

    # 8.3 Persist best model pipeline
    model_path = "best_energy_prediction_model.joblib"
    joblib.dump(best_pipeline, model_path)
    print(f" -> Saved trained pipeline artifact: {os.path.abspath(model_path)}")

    # -------------------------------------------------------------------------
    # 9. FEATURE IMPORTANCE ANALYSIS
    # -------------------------------------------------------------------------
    print("\n[9] FEATURE IMPORTANCE & PHYSICAL ATTRIBUTE RANKING")
    print("-" * 80)

    # Extract transformed feature names
    fitted_preprocessor = best_pipeline.named_steps['preprocessor']
    regressor = best_pipeline.named_steps['regressor']
    
    transformed_feature_names = fitted_preprocessor.get_feature_names_out()
    # Clean feature names for presentation (remove prefixes num__ and cat__)
    clean_feature_names = [
        f.replace('num__', '').replace('cat__', '') for f in transformed_feature_names
    ]

    has_tree_importance = hasattr(regressor, 'feature_importances_')
    
    if has_tree_importance:
        importances = regressor.feature_importances_
        importance_df = pd.DataFrame({
            'Feature': clean_feature_names,
            'Importance': importances
        }).sort_values(by='Importance', ascending=False).reset_index(drop=True)
        print("Feature Importance Ranking (Tree Ensemble Gini/Split Contribution):")
    else:
        # Standardized coefficients for Linear Regression
        importances = np.abs(regressor.coef_)
        importance_df = pd.DataFrame({
            'Feature': clean_feature_names,
            'Importance': importances,
            'Raw_Coefficient': regressor.coef_
        }).sort_values(by='Importance', ascending=False).reset_index(drop=True)
        print("Feature Importance Ranking (Absolute Standardized Regression Coefficients):")

    for rank, row in importance_df.head(10).iterrows():
        print(f"  {rank+1:2d}. {row['Feature']:<35}: {row['Importance']:.4f}")

    # -------------------------------------------------------------------------
    # 10. PUBLICATION-QUALITY VISUALIZATIONS
    # -------------------------------------------------------------------------
    print("\n[10] GENERATING PUBLICATION-QUALITY GRAPHS")
    print("-" * 80)

    # GRAPH 1: regression_model_comparison.png
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    metrics_info = [
        ('MAE', 'Mean Absolute Error (kWh) - Lower is Better', '#2b5c8f', axes[0]),
        ('RMSE', 'Root Mean Squared Error (kWh) - Lower is Better', '#d95f02', axes[1]),
        ('R²', 'Coefficient of Determination (R²) - Higher is Better', '#2ca02c', axes[2])
    ]

    for metric_name, title, color, ax in metrics_info:
        bars = ax.bar(results_df['Model'], results_df[metric_name], color=color, alpha=0.85, width=0.55, edgecolor='#333333')
        ax.set_title(title, fontsize=12, fontweight='bold', pad=12)
        ax.set_ylabel(metric_name, fontsize=11, fontweight='bold')
        ax.tick_params(axis='x', rotation=15, labelsize=10)
        ax.grid(axis='y', linestyle='--', alpha=0.5)

        # Highlight best performer
        if metric_name in ['MAE', 'RMSE']:
            best_idx = results_df[metric_name].idxmin()
        else:
            best_idx = results_df[metric_name].idxmax()
        bars[best_idx].set_edgecolor('black')
        bars[best_idx].set_linewidth(2.0)

        # Value annotations
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f"{height:.4f}",
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 4),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.suptitle("Comparative Regression Performance across EV Energy Consumption Models", 
                 fontsize=14, fontweight='bold', y=1.03)
    plt.tight_layout()
    g1_path = "regression_model_comparison.png"
    plt.savefig(g1_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f" -> Saved [1/4]: {g1_path}")

    # GRAPH 2: actual_vs_predicted_best_model.png
    plt.figure(figsize=(8, 7))
    plt.scatter(y_test, best_preds, alpha=0.45, color='#1f77b4', edgecolors='none', s=35, label='Test Trip Predictions')
    min_val = min(y_test.min(), best_preds.min())
    max_val = max(y_test.max(), best_preds.max())
    padding = (max_val - min_val) * 0.05
    line_range = np.linspace(min_val - padding, max_val + padding, 100)
    plt.plot(line_range, line_range, color='#d62728', linestyle='--', linewidth=2, label='Perfect Prediction (1:1 Line)')
    
    plt.title(f"Actual vs. Predicted Trip Energy Consumption\nBest Model: {best_model_name} (R² = {best_r2:.4f}, RMSE = {best_rmse:.4f} kWh)",
              fontsize=13, fontweight='bold', pad=12)
    plt.xlabel("Actual Trip Energy Consumption (kWh)", fontsize=11, fontweight='bold')
    plt.ylabel("Predicted Trip Energy Consumption (kWh)", fontsize=11, fontweight='bold')
    plt.xlim(min_val - padding, max_val + padding)
    plt.ylim(min_val - padding, max_val + padding)
    plt.legend(frameon=True, facecolor='white', loc='upper left', fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    g2_path = "actual_vs_predicted_best_model.png"
    plt.savefig(g2_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f" -> Saved [2/4]: {g2_path}")

    # GRAPH 3: residual_plot_best_model.png
    fig, (ax_res, ax_hist) = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={'width_ratios': [2, 1]})
    
    # Scatter of residuals vs predicted values
    ax_res.scatter(best_preds, residuals, alpha=0.45, color='#9467bd', edgecolors='none', s=35)
    ax_res.axhline(0, color='#d62728', linestyle='--', linewidth=2)
    ax_res.set_title(f"Residual Plot ({best_model_name})\nResidual = Actual - Predicted", fontsize=12, fontweight='bold')
    ax_res.set_xlabel("Predicted Trip Energy Consumption (kWh)", fontsize=11, fontweight='bold')
    ax_res.set_ylabel("Residual (kWh)", fontsize=11, fontweight='bold')
    ax_res.grid(True, linestyle='--', alpha=0.6)

    # Histogram of residuals
    sns.histplot(residuals, kde=True, ax=ax_hist, color='#9467bd', bins=30, edgecolor='black', alpha=0.6)
    ax_hist.axvline(0, color='#d62728', linestyle='--', linewidth=2)
    ax_hist.set_title("Residual Distribution", fontsize=12, fontweight='bold')
    ax_hist.set_xlabel("Residual Error (kWh)", fontsize=11, fontweight='bold')
    ax_hist.set_ylabel("Frequency", fontsize=11, fontweight='bold')
    ax_hist.grid(True, linestyle='--', alpha=0.6)

    plt.suptitle(f"Error Diagnostic Analysis for Best Model: {best_model_name}", fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout()
    g3_path = "residual_plot_best_model.png"
    plt.savefig(g3_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f" -> Saved [3/4]: {g3_path}")

    # GRAPH 4: feature_importance_best_model.png
    plt.figure(figsize=(10, 6))
    top_n = min(12, len(importance_df))
    plot_df = importance_df.head(top_n).sort_values(by='Importance', ascending=True)
    
    colors = plt.cm.viridis(np.linspace(0.2, 0.85, len(plot_df)))
    bars = plt.barh(plot_df['Feature'], plot_df['Importance'], color=colors, edgecolor='#333333', height=0.65)
    
    # Label formatting
    if has_tree_importance:
        plt.xlabel("Relative Importance Score", fontsize=11, fontweight='bold')
        plt.title(f"Top {top_n} Feature Importances\nBest Model: {best_model_name}", fontsize=13, fontweight='bold', pad=12)
    else:
        plt.xlabel("Absolute Standardized Coefficient (|β|)", fontsize=11, fontweight='bold')
        plt.title(f"Top {top_n} Standardized Coefficients\nBest Model: {best_model_name}", fontsize=13, fontweight='bold', pad=12)

    for bar in bars:
        width = bar.get_width()
        plt.annotate(f"{width:.4f}",
                     xy=(width, bar.get_y() + bar.get_height() / 2),
                     xytext=(5, 0),
                     textcoords="offset points",
                     ha='left', va='center', fontsize=9, fontweight='bold')

    plt.grid(axis='x', linestyle='--', alpha=0.6)
    plt.tight_layout()
    g4_path = "feature_importance_best_model.png"
    plt.savefig(g4_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f" -> Saved [4/4]: {g4_path}")

    # -------------------------------------------------------------------------
    # 11. RESEARCH SUMMARY & PROJECT INTEGRATION
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 4 RESEARCH SUMMARY")
    print("=" * 80)
    print(f"1. Best Model               : {best_model_name}")
    print(f"2. Mean Absolute Error (MAE): {best_mae:.4f} kWh")
    print(f"3. Root Mean Squared (RMSE) : {best_rmse:.4f} kWh")
    print(f"4. Coefficient of Det. (R² ): {best_r2:.4f} ({best_r2 * 100:.2f}% variance explained)")
    print("5. Most Important Features  :")
    for i, r in importance_df.head(4).iterrows():
        print(f"    - {r['Feature']}: {r['Importance']:.4f}")
    print("\n6. Contribution to Project   :")
    print("   The regression model provides a data-driven prediction of EV trip energy")
    print("   consumption. The predicted energy demand can subsequently be used as an input")
    print("   to the proposed intelligent auxiliary energy-management simulator.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_step4_energy_regression()
