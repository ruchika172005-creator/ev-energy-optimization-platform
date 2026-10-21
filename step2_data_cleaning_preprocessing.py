"""
================================================================================
STEP 2: DATA CLEANING & PRE-PROCESSING PIPELINE
================================================================================
Project: Electric Vehicle Trip Energy Consumption Prediction (Academic Research)
Objective:
  1. Systematic missing value audit and handling
  2. Duplicate detection and deduplication
  3. Outlier detection (IQR method) & Winsorization / capping treatment
  4. Categorical variable encoding (One-Hot Encoding for Day of the Week)
  5. Feature scaling (StandardScaler & MinMaxScaler comparison)
  6. Export of cleaned and model-ready scaled datasets
================================================================================
"""

import os
import sys
import functools
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Disable output buffering for immediate console feedback
print = functools.partial(print, flush=True)


def step2_data_cleaning_preprocessing():
    print("=" * 80)
    print("      STEP 2: DATA CLEANING & PRE-PROCESSING (STEP-BY-STEP EXECUTION)")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # 2.1: DATA INGESTION & STRUCTURAL INTEGRITY
    # -------------------------------------------------------------------------
    csv_file = "Electric Vehicle Trip Energy Consumption Data.csv"
    if not os.path.exists(csv_file):
        alt_csv = "Electric Vehicle Trip Energy Consumption Data(1).csv"
        if os.path.exists(alt_csv):
            csv_file = alt_csv
        else:
            raise FileNotFoundError(f"Could not locate dataset '{csv_file}' in {os.getcwd()}")

    print(f"\n[2.1] LOADING DATASET FROM: {csv_file}")
    df = pd.read_csv(csv_file)
    initial_rows, initial_cols = df.shape
    print(f" -> Initial Records (Rows): {initial_rows:,}")
    print(f" -> Initial Attributes (Cols): {initial_cols}")
    print(f" -> Memory Footprint: {df.memory_usage(deep=True).sum() / (1024 * 1024):.2f} MB")

    # -------------------------------------------------------------------------
    # 2.2: MISSING VALUE AUDIT & HANDLING
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("[2.2] MISSING VALUE AUDIT & HANDLING")
    print("-" * 80)

    null_summary = pd.DataFrame({
        'Feature': df.columns,
        'Null Count': df.isnull().sum().values,
        'Null Percentage (%)': (df.isnull().sum().values / len(df)) * 100
    })
    total_nulls = null_summary['Null Count'].sum()
    print(null_summary.to_string(index=False))
    print(f"\nTotal Missing Values Detected: {total_nulls}")

    if total_nulls > 0:
        print("Applying imputation strategy: Numerical -> Median, Categorical -> Mode...")
        for col in df.columns:
            if df[col].isnull().sum() > 0:
                if df[col].dtype in ['float64', 'int64']:
                    median_val = df[col].median()
                    df[col] = df[col].fillna(median_val)
                    print(f" - Filled missing values in '{col}' with median: {median_val}")
                else:
                    mode_val = df[col].mode()[0]
                    df[col] = df[col].fillna(mode_val)
                    print(f" - Filled missing values in '{col}' with mode: {mode_val}")
    else:
        print("Status: Zero missing values detected across all 13 features. Dataset is structurally complete.")

    # -------------------------------------------------------------------------
    # 2.3: DUPLICATE ROW DETECTION & REMOVAL
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("[2.3] DUPLICATE RECORD AUDIT")
    print("-" * 80)
    duplicate_count = df.duplicated().sum()
    print(f"Exact Duplicate Observations Identified: {duplicate_count}")
    if duplicate_count > 0:
        df = df.drop_duplicates().reset_index(drop=True)
        print(f" -> Removed {duplicate_count} duplicate rows. Remaining rows: {len(df):,}")
    else:
        print("Status: No duplicate rows present. Every trip telemetry record is unique.")

    # -------------------------------------------------------------------------
    # 2.4: OUTLIER DETECTION & TREATMENT (IQR WINSORIZATION / CAPPING)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("[2.4] OUTLIER DETECTION & TREATMENT VIA INTERQUARTILE RANGE (IQR)")
    print("-" * 80)
    print("Method: Tuckey's Fences: Lower = Q1 - 1.5*IQR, Upper = Q3 + 1.5*IQR")
    print("Treatment: Winsorization (capping extreme values at the bounds to prevent data loss)")

    numerical_features = [
        'Trip Distance',
        'Speed',
        'Trip Time Length',
        'Current',
        'Total Voltage',
        'Maximum Cell Temperature of Battery',
        'Minimum Cell Temperature of Battery'
    ]

    outlier_report = []
    df_treated = df.copy()

    for col in numerical_features:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower_fence = q1 - 1.5 * iqr
        upper_fence = q3 + 1.5 * iqr

        outliers_mask_pre = (df[col] < lower_fence) | (df[col] > upper_fence)
        outliers_pre_count = outliers_mask_pre.sum()
        outliers_pre_pct = (outliers_pre_count / len(df)) * 100

        # Apply Capping / Winsorization
        df_treated[col] = df_treated[col].clip(lower=lower_fence, upper=upper_fence)

        outliers_post_count = ((df_treated[col] < lower_fence) | (df_treated[col] > upper_fence)).sum()

        outlier_report.append({
            'Feature': col,
            'Q1 (25%)': round(q1, 3),
            'Q3 (75%)': round(q3, 3),
            'IQR': round(iqr, 3),
            'Lower Fence': round(lower_fence, 3),
            'Upper Fence': round(upper_fence, 3),
            'Outliers (Pre)': outliers_pre_count,
            'Pre (%)': f"{outliers_pre_pct:.2f}%",
            'Outliers (Post)': outliers_post_count
        })

    outlier_df = pd.DataFrame(outlier_report)
    print(outlier_df.to_string(index=False))
    print("\nStatus: All extreme values successfully capped within valid physical boundary fences.")

    # -------------------------------------------------------------------------
    # 2.5: CATEGORICAL VARIABLE ENCODING
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("[2.5] CATEGORICAL VARIABLE ENCODING")
    print("-" * 80)
    print("Feature Identified: 'Day of the Week' (Values 0 to 6)")
    print("Rationale: 'Day of the Week' is a nominal/cyclic categorical attribute.")
    print("Using One-Hot Encoding avoids imposing artificial linear ordinal hierarchy (e.g., Saturday > Monday).")

    day_mapping = {
        0: 'Monday',
        1: 'Tuesday',
        2: 'Wednesday',
        3: 'Thursday',
        4: 'Friday',
        5: 'Saturday',
        6: 'Sunday'
    }
    df_treated['Day_Name'] = df_treated['Day of the Week'].map(day_mapping)
    print("\nDistribution across Days of the Week:")
    day_counts = df_treated['Day_Name'].value_counts()
    for day, cnt in day_counts.items():
        print(f" - {day:<10}: {cnt:>5} trips ({cnt / len(df_treated) * 100:.1f}%)")

    # Apply One-Hot Encoding with drop_first=True to avoid dummy variable trap
    encoded_days = pd.get_dummies(df_treated['Day_Name'], prefix='Day', drop_first=True, dtype=int)
    print(f"\nGenerated One-Hot Encoded Columns ({len(encoded_days.columns)} dummy columns):")
    print(list(encoded_days.columns))

    # Combine back to treated dataframe
    df_encoded = pd.concat([df_treated, encoded_days], axis=1)

    # -------------------------------------------------------------------------
    # 2.6: FEATURE SCALING (STANDARD & MIN-MAX SCALING)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("[2.6] FEATURE SCALING")
    print("-" * 80)
    print("Evaluated Scaling Techniques:")
    print(" 1. StandardScaler (Z-score): Scales features to μ = 0, σ = 1 (Ideal for linear, ridge, neural nets)")
    print(" 2. MinMaxScaler: Scales features to [0, 1] range (Preserves zero entries and bounded intervals)")

    features_to_scale = [
        'Trip Distance',
        'Speed',
        'Trip Time Length',
        'Current',
        'Total Voltage',
        'Maximum Cell Temperature of Battery',
        'Minimum Cell Temperature of Battery',
        'Time of Day'
    ]

    std_scaler = StandardScaler()
    scaled_std_array = std_scaler.fit_transform(df_encoded[features_to_scale])
    df_scaled_std = pd.DataFrame(
        scaled_std_array, 
        columns=[f"{c}_standardized" for c in features_to_scale]
    )

    minmax_scaler = MinMaxScaler()
    scaled_minmax_array = minmax_scaler.fit_transform(df_encoded[features_to_scale])
    df_scaled_minmax = pd.DataFrame(
        scaled_minmax_array, 
        columns=[f"{c}_minmax" for c in features_to_scale]
    )

    # Scaling statistical comparison
    scale_comparison = []
    for col in features_to_scale:
        scale_comparison.append({
            'Feature': col,
            'Orig Mean': round(df_encoded[col].mean(), 2),
            'Orig Std': round(df_encoded[col].std(), 2),
            'Orig Min': round(df_encoded[col].min(), 2),
            'Orig Max': round(df_encoded[col].max(), 2),
            'StdScale Mean': round(df_scaled_std[f"{col}_standardized"].mean(), 4),
            'StdScale Std': round(df_scaled_std[f"{col}_standardized"].std(), 4),
            'MinMax Min': round(df_scaled_minmax[f"{col}_minmax"].min(), 4),
            'MinMax Max': round(df_scaled_minmax[f"{col}_minmax"].max(), 4)
        })

    print("\nFeature Scaling Verification Table:")
    print(pd.DataFrame(scale_comparison).to_string(index=False))

    # Construct complete preprocessed model-ready dataframe
    # Target variable 'Trip Energy Consumption' is kept in physical units (kWh)
    df_model_ready = pd.concat([
        df_encoded[['Trip Energy Consumption', 'Vehicle ID']],
        df_scaled_std,
        encoded_days
    ], axis=1)

    # -------------------------------------------------------------------------
    # 2.7: EXPORT CLEANED & PREPROCESSED DATASETS
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("[2.7] EXPORT PERSISTENCE")
    print("-" * 80)
    cleaned_out_path = "cleaned_ev_data.csv"
    preprocessed_out_path = "preprocessed_scaled_features.csv"

    df_encoded.to_csv(cleaned_out_path, index=False)
    df_model_ready.to_csv(preprocessed_out_path, index=False)

    print(f" -> Successfully exported cleaned dataset       : {os.path.abspath(cleaned_out_path)}")
    print(f"    Dimensions: {df_encoded.shape[0]:,} rows x {df_encoded.shape[1]} columns")
    print(f" -> Successfully exported scaled features matrix: {os.path.abspath(preprocessed_out_path)}")
    print(f"    Dimensions: {df_model_ready.shape[0]:,} rows x {df_model_ready.shape[1]} columns")

    print("\n" + "=" * 80)
    print("STEP 2 COMPLETED: ALL CLEANING, OUTLIER TREATMENT, ENCODING & SCALING VERIFIED")
    print("=" * 80)


if __name__ == "__main__":
    step2_data_cleaning_preprocessing()
