"""
===============================================================================
ELECTRIC VEHICLE TRIP ENERGY CONSUMPTION - COMPREHENSIVE PIPELINE & EXPORT SCRIPT
===============================================================================
Project: Intelligent Auxiliary Energy Management Simulator for Electric Vehicles
Milestone: EV Trip Energy Consumption Prediction and Exploratory Data Analysis
===============================================================================
"""

import os
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

# Visual styling setup
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'axes.titleweight': 'bold',
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'figure.titlesize': 14,
    'figure.titleweight': 'bold',
    'axes.edgecolor': '#cccccc',
    'axes.linewidth': 0.8
})

def main():
    print("=" * 80)
    print("STEP 1: DATA ACQUISITION & DIMENSIONAL PROFILING")
    print("=" * 80)
    
    csv_file = "Electric Vehicle Trip Energy Consumption Data.csv"
    if not os.path.exists(csv_file):
        # Fallback to (1) if needed
        alt_csv = "Electric Vehicle Trip Energy Consumption Data(1).csv"
        if os.path.exists(alt_csv):
            csv_file = alt_csv
            
    df_raw = pd.read_csv(csv_file)
    print(f"Dataset Loaded Successfully: {csv_file}")
    print(f"Dataset Shape: {df_raw.shape[0]:,} rows, {df_raw.shape[1]} columns")
    print(f"Target Variable Identified: 'Trip Energy Consumption' (in kWh)")
    print(f"Total Unique Vehicles: {df_raw['Vehicle ID'].nunique()}")
    print("\nFirst 5 Rows:")
    print(df_raw.head())
    print("\nData Types:")
    print(df_raw.dtypes)

    print("\n" + "=" * 80)
    print("STEP 2: DATA QUALITY ANALYSIS")
    print("=" * 80)
    missing = df_raw.isnull().sum()
    duplicates = df_raw.duplicated().sum()
    print("Missing Values per Column:")
    print(missing)
    print(f"\nExact Duplicate Rows Detected: {duplicates}")
    print("\nUnique Values per Column:")
    for col in df_raw.columns:
        print(f" - {col:<38}: {df_raw[col].nunique():>5} unique values")
    
    print("\nDescriptive Statistical Summary:")
    print(df_raw.describe().T[['min', '25%', '50%', '75%', 'max', 'mean', 'std']])

    # Checking for physical domain anomalies
    print("\nPhysical Boundary Checks:")
    print(f" - Non-positive Trip Energy records (<=0): {(df_raw['Trip Energy Consumption'] <= 0).sum()}")
    print(f" - Non-positive Distance records (<=0)   : {(df_raw['Trip Distance'] <= 0).sum()}")
    print(f" - Negative Speed records (<0)           : {(df_raw['Speed'] < 0).sum()}")
    print(f" - Non-positive Total Voltage records    : {(df_raw['Total Voltage'] <= 0).sum()}")
    print(f" - Non-positive Trip Time Length (<=0)   : {(df_raw['Trip Time Length'] <= 0).sum()}")
    print(f" - Battery Cell Max Temp Range           : {df_raw['Maximum Cell Temperature of Battery'].min():.2f}°C to {df_raw['Maximum Cell Temperature of Battery'].max():.2f}°C")
    print(f" - Battery Cell Min Temp Range           : {df_raw['Minimum Cell Temperature of Battery'].min():.2f}°C to {df_raw['Minimum Cell Temperature of Battery'].max():.2f}°C")

    print("\n" + "=" * 80)
    print("STEP 3: DATA CLEANING")
    print("=" * 80)
    initial_rows = len(df_raw)
    df_cleaned = df_raw.drop_duplicates().copy()
    cleaned_rows = len(df_cleaned)
    print(f"Rows before cleaning: {initial_rows:,}")
    print(f"Rows after cleaning : {cleaned_rows:,} (Zero records dropped as dataset is structurally complete and unique)")

    print("\n" + "=" * 80)
    print("STEP 4: OUTLIER DETECTION AND TREATMENT (IQR WINSORIZATION)")
    print("=" * 80)
    
    numerical_predictors = [
        'Trip Distance', 'Speed', 'Trip Time Length',
        'Current', 'Total Voltage',
        'Maximum Cell Temperature of Battery',
        'Minimum Cell Temperature of Battery'
    ]

    # Pre-treatment boxplot visualization
    fig, axes = plt.subplots(2, 4, figsize=(18, 9))
    fig.suptitle("Outlier Analysis: Numerical Predictors Distribution (Pre-Treatment)", fontsize=14, y=0.98)
    axes_flat = axes.flatten()

    outlier_summary = []
    df_winsorized = df_cleaned.copy()

    for idx, col in enumerate(numerical_predictors):
        q1 = df_cleaned[col].quantile(0.25)
        q3 = df_cleaned[col].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers_pre = ((df_cleaned[col] < lower_bound) | (df_cleaned[col] > upper_bound)).sum()
        
        # Plot pre-treatment boxplot
        sns.boxplot(y=df_cleaned[col], ax=axes_flat[idx], color='#4575b4', flierprops=dict(marker='o', markerfacecolor='#d73027', alpha=0.5, markersize=4))
        axes_flat[idx].set_title(f"{col}", fontsize=10, fontweight='bold')
        axes_flat[idx].set_ylabel("")
        axes_flat[idx].grid(True, linestyle='--', alpha=0.5)

        # Capping / Winsorization (retaining sample size without data loss)
        df_winsorized[col] = df_winsorized[col].clip(lower=lower_bound, upper=upper_bound)
        outliers_post = ((df_winsorized[col] < lower_bound) | (df_winsorized[col] > upper_bound)).sum()

        outlier_summary.append({
            'Feature': col,
            'Q1': q1,
            'Q3': q3,
            'IQR': iqr,
            'Lower Fence': lower_bound,
            'Upper Fence': upper_bound,
            'Outliers (Pre)': outliers_pre,
            'Outliers (Post)': outliers_post
        })

    # Hide unused 8th subplot
    axes_flat[-1].axis('off')
    plt.tight_layout()
    plt.savefig("eda_figure_6_outlier_boxplots_pre.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(" -> Saved: eda_figure_6_outlier_boxplots_pre.png")

    outlier_df = pd.DataFrame(outlier_summary)
    print(outlier_df.to_string(index=False))

    # Post-treatment boxplot verification
    fig, axes = plt.subplots(2, 4, figsize=(18, 9))
    fig.suptitle("Outlier Verification: Numerical Predictors Distribution (Post-IQR Winsorization)", fontsize=14, y=0.98)
    axes_flat = axes.flatten()
    for idx, col in enumerate(numerical_predictors):
        sns.boxplot(y=df_winsorized[col], ax=axes_flat[idx], color='#2b83ba', flierprops=dict(marker='o', markerfacecolor='#1a9641', alpha=0.5, markersize=4))
        axes_flat[idx].set_title(f"{col} (Capped)", fontsize=10, fontweight='bold')
        axes_flat[idx].set_ylabel("")
        axes_flat[idx].grid(True, linestyle='--', alpha=0.5)
    axes_flat[-1].axis('off')
    plt.tight_layout()
    plt.savefig("eda_figure_6b_outlier_boxplots_post.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(" -> Saved: eda_figure_6b_outlier_boxplots_post.png")

    print("\n" + "=" * 80)
    print("STEP 5: FEATURE ENGINEERING")
    print("=" * 80)
    # Physical formulation 1: Battery Instantaneous Power = Total Voltage * Current
    df_winsorized['Battery Power'] = df_winsorized['Total Voltage'] * df_winsorized['Current']
    
    # Physical formulation 2: Cell Temperature Differential
    df_winsorized['Temperature Differential'] = (
        df_winsorized['Maximum Cell Temperature of Battery'] - 
        df_winsorized['Minimum Cell Temperature of Battery']
    )
    
    # Cyclic transformation for Time of Day (24-hour cycle)
    df_winsorized['sin_time'] = np.sin(2 * np.pi * df_winsorized['Time of Day'] / 24.0)
    df_winsorized['cos_time'] = np.cos(2 * np.pi * df_winsorized['Time of Day'] / 24.0)

    # For EDA benchmarking ONLY (NOT passed to ML to avoid target leakage)
    df_winsorized['Energy_per_Distance'] = df_winsorized['Trip Energy Consumption'] / df_winsorized['Trip Distance']
    
    print("Engineered Features:")
    print(" 1. Battery Power = Total Voltage * Current")
    print(" 2. Temperature Differential = Maximum Cell Temperature - Minimum Cell Temperature")
    print(" 3. Cyclic Time Features: sin_time = sin(2π * Time / 24), cos_time = cos(2π * Time / 24)")
    print(" 4. Energy_per_Distance = Trip Energy Consumption / Trip Distance (Strictly isolated for EDA only)")

    # Save cleaned dataset
    df_winsorized.to_csv("cleaned_ev_data.csv", index=False)
    print(" -> Persisted: cleaned_ev_data.csv")

    print("\n" + "=" * 80)
    print("STEP 6: EXPLORATORY DATA ANALYSIS (EDA) VISUALIZATIONS")
    print("=" * 80)

    # Figure 1: Distribution of Trip Energy Consumption
    plt.figure(figsize=(9, 5.5))
    sns.histplot(df_winsorized['Trip Energy Consumption'], kde=True, color='#2b83ba', bins=35, edgecolor='black', linewidth=0.6)
    plt.axvline(df_winsorized['Trip Energy Consumption'].mean(), color='#d73027', linestyle='--', linewidth=2, label=f"Mean: {df_winsorized['Trip Energy Consumption'].mean():.2f} kWh")
    plt.axvline(df_winsorized['Trip Energy Consumption'].median(), color='#fdae61', linestyle='-', linewidth=2, label=f"Median: {df_winsorized['Trip Energy Consumption'].median():.2f} kWh")
    plt.title("Figure 1: Distribution of EV Trip Energy Consumption (Target Variable)", fontsize=13, fontweight='bold', pad=12)
    plt.xlabel("Trip Energy Consumption (kWh)", fontsize=11)
    plt.ylabel("Frequency (Trip Count)", fontsize=11)
    plt.legend(frameon=True)
    plt.tight_layout()
    plt.savefig("eda_figure_1_target_distribution.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(" -> Saved: eda_figure_1_target_distribution.png")

    # Figure 2: Trip Energy Consumption vs Trip Distance
    plt.figure(figsize=(9, 5.5))
    sns.regplot(
        data=df_winsorized, 
        x='Trip Distance', 
        y='Trip Energy Consumption',
        scatter_kws={'alpha': 0.35, 'color': '#2b83ba', 's': 22},
        line_kws={'color': '#d73027', 'linewidth': 2.5, 'label': 'Linear Regression Trendline'}
    )
    plt.title("Figure 2: Trip Energy Consumption vs. Trip Distance", fontsize=13, fontweight='bold', pad=12)
    plt.xlabel("Trip Distance (km)", fontsize=11)
    plt.ylabel("Trip Energy Consumption (kWh)", fontsize=11)
    plt.legend(frameon=True, loc='upper left')
    plt.tight_layout()
    plt.savefig("eda_figure_2_energy_vs_distance.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(" -> Saved: eda_figure_2_energy_vs_distance.png")

    # Figure 3: Trip Energy Consumption vs Speed (Stratified by Distance)
    plt.figure(figsize=(9.5, 5.5))
    scatter = plt.scatter(
        df_winsorized['Speed'], 
        df_winsorized['Trip Energy Consumption'], 
        c=df_winsorized['Trip Distance'], 
        cmap='viridis', 
        alpha=0.45, 
        s=25
    )
    cbar = plt.colorbar(scatter)
    cbar.set_label('Trip Distance (km)', rotation=270, labelpad=15)
    plt.title("Figure 3: Trip Energy Consumption vs. Average Vehicle Speed", fontsize=13, fontweight='bold', pad=12)
    plt.xlabel("Vehicle Speed (km/h)", fontsize=11)
    plt.ylabel("Trip Energy Consumption (kWh)", fontsize=11)
    plt.tight_layout()
    plt.savefig("eda_figure_3_energy_vs_speed.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(" -> Saved: eda_figure_3_energy_vs_speed.png")

    # Figure 4: Battery Cell Thermal Analysis
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    scatter_t = axes[0].scatter(
        df_winsorized['Minimum Cell Temperature of Battery'],
        df_winsorized['Maximum Cell Temperature of Battery'],
        c=df_winsorized['Temperature Differential'],
        cmap='plasma',
        alpha=0.45,
        s=24
    )
    cb = fig.colorbar(scatter_t, ax=axes[0])
    cb.set_label('Cell Temperature Differential (°C)', rotation=270, labelpad=15)
    axes[0].plot([df_winsorized['Minimum Cell Temperature of Battery'].min(), df_winsorized['Maximum Cell Temperature of Battery'].max()],
                 [df_winsorized['Minimum Cell Temperature of Battery'].min(), df_winsorized['Maximum Cell Temperature of Battery'].max()],
                 '--', color='#555555', linewidth=1.5, label='Uniform Temperature (Max = Min)')
    axes[0].set_title("Cell Temperature Coupling (Min vs. Max °C)", fontsize=12, fontweight='bold')
    axes[0].set_xlabel("Minimum Cell Temperature of Battery (°C)", fontsize=11)
    axes[0].set_ylabel("Maximum Cell Temperature of Battery (°C)", fontsize=11)
    axes[0].legend(loc='upper left', frameon=True)

    sns.histplot(df_winsorized['Temperature Differential'], kde=True, color='#e66101', ax=axes[1], bins=30, edgecolor='black', linewidth=0.5)
    axes[1].axvline(df_winsorized['Temperature Differential'].mean(), color='#0571b0', linestyle='--', linewidth=2, label=f"Mean Delta: {df_winsorized['Temperature Differential'].mean():.2f}°C")
    axes[1].set_title("Distribution of Cell Temperature Differential", fontsize=12, fontweight='bold')
    axes[1].set_xlabel("Temperature Differential (°C)", fontsize=11)
    axes[1].set_ylabel("Frequency", fontsize=11)
    axes[1].legend(loc='upper right', frameon=True)
    
    fig.suptitle("Figure 4: Battery Thermal Distribution and Dynamics", fontsize=14, y=0.98)
    plt.tight_layout()
    plt.savefig("eda_figure_4_battery_thermal_dynamics.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(" -> Saved: eda_figure_4_battery_thermal_dynamics.png")

    # Figure 5: Correlation Heatmap
    corr_cols = [
        'Trip Energy Consumption', 'Trip Distance', 'Speed', 'Trip Time Length',
        'Current', 'Total Voltage', 'Battery Power',
        'Maximum Cell Temperature of Battery', 'Minimum Cell Temperature of Battery',
        'Temperature Differential', 'Energy_per_Distance'
    ]
    corr_mat = df_winsorized[corr_cols].corr()

    plt.figure(figsize=(11, 9))
    mask = np.triu(np.ones_like(corr_mat, dtype=bool), k=1)
    sns.heatmap(
        corr_mat, 
        annot=True, 
        fmt=".2f", 
        cmap='coolwarm', 
        vmin=-1, 
        vmax=1, 
        center=0,
        cbar_kws={"shrink": 0.8, "label": "Pearson Correlation Coefficient"},
        square=True,
        linewidths=0.7,
        linecolor='white'
    )
    plt.title("Figure 5: Pearson Correlation Heatmap of EV Operational & Electrical Parameters", pad=15, fontsize=13, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig("eda_figure_5_correlation_heatmap.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(" -> Saved: eda_figure_5_correlation_heatmap.png")

    # Figure 7: Temporal Energy Consumption by Hour of Day
    df_winsorized['Hour_Floor'] = df_winsorized['Time of Day'].astype(int)
    hourly_stats = df_winsorized.groupby('Hour_Floor')['Trip Energy Consumption'].agg(['mean', 'std', 'count']).reset_index()

    plt.figure(figsize=(10, 5.5))
    sns.barplot(data=hourly_stats, x='Hour_Floor', y='mean', color='#4575b4', edgecolor='black', linewidth=0.7)
    plt.errorbar(x=hourly_stats.index, y=hourly_stats['mean'], yerr=hourly_stats['std'] / np.sqrt(hourly_stats['count']), fmt='none', color='black', capsize=4, label='Standard Error (SEM)')
    plt.title("Figure 7: Mean EV Trip Energy Consumption across Time of Day (24-Hour Cycle)", fontsize=13, fontweight='bold', pad=12)
    plt.xlabel("Hour of the Day (0 to 23)", fontsize=11)
    plt.ylabel("Mean Trip Energy Consumption (kWh)", fontsize=11)
    plt.legend(frameon=True)
    plt.tight_layout()
    plt.savefig("eda_figure_7_temporal_hourly_profile.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(" -> Saved: eda_figure_7_temporal_hourly_profile.png")

    # Figure 8: Vehicle Specific Efficiency Comparison
    vehicle_eff = df_winsorized.groupby('Vehicle ID')['Energy_per_Distance'].mean().reset_index().sort_values(by='Energy_per_Distance')
    plt.figure(figsize=(12, 5))
    sns.barplot(data=vehicle_eff, x='Vehicle ID', y='Energy_per_Distance', palette='crest', edgecolor='black', linewidth=0.5, order=vehicle_eff['Vehicle ID'])
    plt.axhline(df_winsorized['Energy_per_Distance'].mean(), color='#d73027', linestyle='--', linewidth=1.5, label=f"Fleet Mean Efficiency: {df_winsorized['Energy_per_Distance'].mean():.3f} kWh/km")
    plt.title("Figure 8: Fleet Energy Efficiency Variance across 50 Electric Vehicles (EDA Benchmarking)", fontsize=13, fontweight='bold', pad=12)
    plt.xlabel("Vehicle ID (Ordered by Efficiency)", fontsize=11)
    plt.ylabel("Mean Specific Energy Consumption (kWh/km)", fontsize=11)
    plt.xticks(rotation=90, fontsize=8)
    plt.legend(frameon=True)
    plt.tight_layout()
    plt.savefig("eda_figure_8_vehicle_efficiency_benchmark.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(" -> Saved: eda_figure_8_vehicle_efficiency_benchmark.png")

    print("\nPearson Correlation with Target ('Trip Energy Consumption'):")
    pearson_target = corr_mat['Trip Energy Consumption'].drop('Trip Energy Consumption').sort_values(ascending=False)
    for k, v in pearson_target.items():
        print(f" - {k:<38}: {v:+.4f}")

    print("\n" + "=" * 80)
    print("STEP 7 & 8: MACHINE LEARNING PIPELINE & TRAIN-TEST SPLIT")
    print("=" * 80)

    features_num = [
        'Trip Distance', 'Speed', 'Trip Time Length',
        'Current', 'Total Voltage', 'Battery Power',
        'Maximum Cell Temperature of Battery', 'Minimum Cell Temperature of Battery',
        'Temperature Differential', 'sin_time', 'cos_time'
    ]
    features_cat = ['Day of the Week']

    X = df_winsorized[features_num + features_cat]
    y = df_winsorized['Trip Energy Consumption']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )

    print(f"X_train shape: {X_train.shape} | y_train shape: {y_train.shape} (80% Training Set)")
    print(f"X_test shape : {X_test.shape} | y_test shape : {y_test.shape} (20% Testing Set)")
    print("Preprocessors: StandardScaler for Numerical, OneHotEncoder for Categorical features")

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), features_num),
            ('cat', OneHotEncoder(drop='first', handle_unknown='ignore'), features_cat)
        ]
    )

    print("\n" + "=" * 80)
    print("STEP 9 & 10: MODEL TRAINING & QUANTITATIVE EVALUATION")
    print("=" * 80)

    candidate_models = {
        'Linear Regression': LinearRegression(),
        'Random Forest Regressor': RandomForestRegressor(n_estimators=100, random_state=42),
        'Gradient Boosting Regressor': GradientBoostingRegressor(n_estimators=100, random_state=42)
    }

    eval_records = []
    trained_pipes = {}
    test_predictions = {}

    for model_name, model_obj in candidate_models.items():
        pipeline = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('regressor', model_obj)
        ])
        
        # Fit strictly on training data
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        eval_records.append({
            'Model': model_name,
            'MAE (kWh)': mae,
            'RMSE (kWh)': rmse,
            'R² Score': r2
        })
        trained_pipes[model_name] = pipeline
        test_predictions[model_name] = y_pred

    comparison_df = pd.DataFrame(eval_records).sort_values(by='R² Score', ascending=False)
    comparison_df.to_csv("model_comparison_results.csv", index=False)
    print("Model Evaluation Comparison Table:")
    print(comparison_df.to_string(index=False))

    best_name = comparison_df.iloc[0]['Model']
    best_pipe = trained_pipes[best_name]
    best_preds = test_predictions[best_name]
    print(f"\nIdentified Best-Performing Model: '{best_name}'")
    print(f" - MAE : {comparison_df.iloc[0]['MAE (kWh)']:.4f} kWh")
    print(f" - RMSE: {comparison_df.iloc[0]['RMSE (kWh)']:.4f} kWh")
    print(f" - R²  : {comparison_df.iloc[0]['R² Score']:.4f}")

    # Serialize best model
    joblib.dump(best_pipe, "best_ev_energy_model.joblib")
    print(" -> Serialized Best Model to 'best_ev_energy_model.joblib'")

    print("\n" + "=" * 80)
    print("STEP 11: VISUAL MODEL EVALUATION")
    print("=" * 80)

    # Actual vs Predicted + Residuals + Comparison Bar Chart
    fig = plt.figure(figsize=(18, 5.5))

    # Subplot A: Actual vs Predicted Scatter with y = x line
    ax1 = plt.subplot(1, 3, 1)
    ax1.scatter(y_test, best_preds, alpha=0.35, color='#2b83ba', s=24, edgecolors='none')
    min_diag = min(y_test.min(), best_preds.min())
    max_diag = max(y_test.max(), best_preds.max())
    ax1.plot([min_diag, max_diag], [min_diag, max_diag], '--', color='#d73027', linewidth=2, label='Ideal Parity (y = x)')
    ax1.set_title(f"A. Actual vs Predicted ({best_name})", fontsize=12, fontweight='bold')
    ax1.set_xlabel("Actual Trip Energy Consumption (kWh)", fontsize=11)
    ax1.set_ylabel("Predicted Trip Energy Consumption (kWh)", fontsize=11)
    ax1.legend(loc='upper left', frameon=True)
    ax1.grid(True, linestyle='--', alpha=0.5)

    # Subplot B: Residual Error Distribution
    residuals = y_test - best_preds
    ax2 = plt.subplot(1, 3, 2)
    sns.histplot(residuals, kde=True, ax=ax2, color='#7b3294', bins=35, edgecolor='black', linewidth=0.5)
    ax2.axvline(0, color='black', linestyle='--', linewidth=1.5, label='Zero Error Reference')
    ax2.axvline(residuals.mean(), color='#d73027', linestyle=':', linewidth=1.8, label=f'Mean Error: {residuals.mean():.3f}')
    ax2.set_title("B. Residual Error Distribution (y_true - y_pred)", fontsize=12, fontweight='bold')
    ax2.set_xlabel("Residual Error (kWh)", fontsize=11)
    ax2.set_ylabel("Prediction Count", fontsize=11)
    ax2.legend(loc='upper right', frameon=True)
    ax2.grid(True, linestyle='--', alpha=0.5)

    # Subplot C: Model Metric Comparison
    ax3 = plt.subplot(1, 3, 3)
    x_indices = np.arange(len(comparison_df))
    width = 0.26
    ax3.bar(x_indices - width, comparison_df['MAE (kWh)'], width, label='MAE (kWh, lower is better)', color='#fdae61', edgecolor='black', linewidth=0.5)
    ax3.bar(x_indices, comparison_df['RMSE (kWh)'], width, label='RMSE (kWh, lower is better)', color='#d7191c', edgecolor='black', linewidth=0.5)
    ax3.bar(x_indices + width, comparison_df['R² Score'], width, label='R² Score (higher is better)', color='#2b83ba', edgecolor='black', linewidth=0.5)
    ax3.set_xticks(x_indices)
    ax3.set_xticklabels([m.replace(' Regressor', '\nRegressor') for m in comparison_df['Model']], fontsize=9)
    ax3.set_title("C. Model Benchmark Comparison", fontsize=12, fontweight='bold')
    ax3.set_ylabel("Metric Value", fontsize=11)
    ax3.legend(loc='upper right', frameon=True, fontsize=8.5)
    ax3.grid(True, linestyle='--', alpha=0.5)

    fig.suptitle("Visual Evaluation: Predictive Integrity & Residual Diagnostic", fontsize=14, y=0.98)
    plt.tight_layout()
    plt.savefig("eda_figure_9_model_evaluation_diagnostics.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(" -> Saved: eda_figure_9_model_evaluation_diagnostics.png")

    print("\n" + "=" * 80)
    print("STEP 12: FEATURE IMPORTANCE ANALYSIS")
    print("=" * 80)
    
    encoded_cat_names = list(best_pipe.named_steps['preprocessor'].named_transformers_['cat'].get_feature_names_out(features_cat))
    all_feature_names = features_num + encoded_cat_names
    importances = best_pipe.named_steps['regressor'].feature_importances_
    
    feat_imp_df = pd.DataFrame({
        'Feature': all_feature_names,
        'Importance': importances
    }).sort_values(by='Importance', ascending=True)

    plt.figure(figsize=(10, 6.5))
    plt.barh(feat_imp_df['Feature'], feat_imp_df['Importance'], color='#2b83ba', edgecolor='black', linewidth=0.6)
    plt.title(f"Feature Importance Contribution - {best_name}", fontsize=13, fontweight='bold', pad=12)
    plt.xlabel("Gini / Variance Reduction Importance Score", fontsize=11)
    plt.ylabel("Predictor Variable", fontsize=11)
    for idx, val in enumerate(feat_imp_df['Importance']):
        plt.text(val + 0.005, idx, f"{val:.4f}", va='center', fontsize=9)
    plt.xlim(0, max(feat_imp_df['Importance']) * 1.12)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig("eda_figure_10_feature_importance.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(" -> Saved: eda_figure_10_feature_importance.png")
    print(feat_imp_df.sort_values(by='Importance', ascending=False).to_string(index=False))

    print("\n" + "=" * 80)
    print("ALL CORE PIPELINE TASKS COMPLETED SUCCESSFULLY")
    print("=" * 80)

if __name__ == "__main__":
    main()
