"""
STEP 1: Data Acquisition and Initial Profiling
Project: Electric Vehicle Trip Energy Consumption Prediction (Academic ESE/Research Project)
"""

import os
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Disable output buffering so output appears instantly in terminal
import functools
print = functools.partial(print, flush=True)

import pandas as pd

def step1_data_acquisition():
    # 1. File path identification
    csv_filename = "Electric Vehicle Trip Energy Consumption Data.csv"
    
    # Fallback check if file is named with suffix
    if not os.path.exists(csv_filename):
        alt_filename = "Electric Vehicle Trip Energy Consumption Data(1).csv"
        if os.path.exists(alt_filename):
            csv_filename = alt_filename
            
    if not os.path.exists(csv_filename):
        raise FileNotFoundError(
            f"Dataset not found at '{csv_filename}'. "
            f"Please verify the CSV is in the working directory: {os.getcwd()}"
        )

    abs_path = os.path.abspath(csv_filename)
    file_size_mb = os.path.getsize(abs_path) / (1024 * 1024)
    
    print("=" * 80)
    print("STEP 1: DATA ACQUISITION & INITIAL PROFILING")
    print("=" * 80)
    print(f"Dataset File Name : {os.path.basename(abs_path)}")
    print(f"Absolute File Path: {abs_path}")
    print(f"File Size         : {file_size_mb:.2f} MB")

    # 2. Load Dataset
    df = pd.read_csv(abs_path)

    # 3. Dimensionality & Structure
    print("\n[1. DIMENSIONS & SHAPE]")
    print(f"Total Records (Rows)   : {df.shape[0]:,}")
    print(f"Total Attributes (Cols): {df.shape[1]}")

    # 4. Target & Key Entity Verification
    print("\n[2. TARGET & ENTITY PROFILE]")
    target_col = "Trip Energy Consumption"
    if target_col in df.columns:
        print(f"Primary Target Variable: '{target_col}' (Unit: kWh)")
    else:
        print(f"WARNING: Target variable '{target_col}' not explicitly found.")

    if "Vehicle ID" in df.columns:
        print(f"Unique Vehicles in Fleet: {df['Vehicle ID'].nunique()}")

    # 5. Column Schema & Data Types
    print("\n[3. COLUMN NAMES & DATA TYPES]")
    schema_df = pd.DataFrame({
        "Data Type": df.dtypes.astype(str),
        "Non-Null Count": df.notnull().sum(),
        "Null Count": df.isnull().sum(),
        "Unique Values": df.nunique()
    })
    print(schema_df.to_string())

    # 6. First 5 Rows Inspection
    print("\n[4. FIRST 5 OBSERVATIONS (HEAD)]")
    print(df.head().to_string())

    # 7. Metadata Assessment
    print("\n[5. METADATA ASSESSMENT]")
    print("All required operational telemetry, electrical states, and thermal indicators")
    print("are self-contained in this tabular file. No external metadata files are needed.")
    print("=" * 80)

if __name__ == "__main__":
    step1_data_acquisition()
