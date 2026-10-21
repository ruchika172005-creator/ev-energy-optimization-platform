"""
===============================================================================
ELECTRIC VEHICLE TRIP ENERGY CONSUMPTION - EXPLORATORY DATA ANALYSIS (EDA)
===============================================================================
Dataset: Electric Vehicle Trip Energy Consumption Data.csv
Flow:
  1. Energy Analysis (Energy vs Distance + Energy vs Speed)
  2. Battery/Thermal Analysis (Battery Cell Temperature Dynamics)
  3. Correlation Analysis (Correlation Heatmap)
  4. Outlier Analysis (Boxplots for Energy, Distance, Speed, Current)
===============================================================================
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set global visual aesthetics
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Segoe UI', 'DejaVu Sans', 'Helvetica', 'Arial'],
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'axes.titleweight': 'bold',
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'figure.titlesize': 14,
    'figure.titleweight': 'bold',
    'axes.edgecolor': '#cccccc',
    'axes.linewidth': 0.8
})


def calculate_iqr_outliers(df, column):
    """Calculate IQR bounds and count outliers for a numeric column."""
    q1 = df[column].quantile(0.25)
    q3 = df[column].quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]
    return {
        'q1': q1,
        'q3': q3,
        'iqr': iqr,
        'lower_bound': lower_bound,
        'upper_bound': upper_bound,
        'count': len(outliers),
        'pct': (len(outliers) / len(df)) * 100
    }


def main():
    print("=" * 80)
    print("      ELECTRIC VEHICLE TRIP ENERGY CONSUMPTION - EDA REPORT")
    print("=" * 80)

    file_path = "Electric Vehicle Trip Energy Consumption Data.csv"
    if not os.path.exists(file_path):
        print(f"Error: Dataset '{file_path}' not found.")
        return

    # Load Data
    df = pd.read_csv(file_path)
    output_dir = "."

    # Feature Engineering
    df['Energy_per_Distance'] = np.where(df['Trip Distance'] > 0, df['Trip Energy Consumption'] / df['Trip Distance'], np.nan)
    df['Temp_Delta'] = df['Maximum Cell Temperature of Battery'] - df['Minimum Cell Temperature of Battery']
    df['Calculated_Power_kW'] = (df['Total Voltage'] * df['Current']) / 1000.0

    print(f"\n[DATASET OVERVIEW]")
    print(f" - Total Trip Records : {df.shape[0]:,}")
    print(f" - Total Features     : {df.shape[1]}")
    print(f" - Unique Vehicles    : {df['Vehicle ID'].nunique()}")
    print(f" - Missing Values     : {df.isnull().sum().sum()}")

    # =========================================================================
    # 1. ENERGY ANALYSIS
    # =========================================================================
    print("\n" + "=" * 80)
    print(" 1. ENERGY ANALYSIS")
    print("=" * 80)
    print(f" - Mean Trip Energy Consumption : {df['Trip Energy Consumption'].mean():.3f} kWh (Median: {df['Trip Energy Consumption'].median():.3f})")
    print(f" - Mean Trip Distance           : {df['Trip Distance'].mean():.2f} km (Max: {df['Trip Distance'].max():.2f} km)")
    print(f" - Mean Specific Energy Rate    : {df['Energy_per_Distance'].mean():.4f} kWh/km")
    
    # Visualization: Energy vs Distance + Energy vs Speed
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle("1. Energy Analysis: Consumption Dynamics", fontsize=15, y=0.98)

    # Plot 1A: Energy vs Distance
    sns.regplot(
        data=df, 
        x='Trip Distance', 
        y='Trip Energy Consumption', 
        ax=axes[0],
        scatter_kws={'alpha': 0.35, 'color': '#1f77b4', 's': 20},
        line_kws={'color': '#e6550d', 'linewidth': 2.2, 'label': 'Linear Fit'}
    )
    axes[0].set_title("Energy Consumption vs. Trip Distance")
    axes[0].set_xlabel("Trip Distance (km)")
    axes[0].set_ylabel("Trip Energy Consumption (kWh)")
    axes[0].legend(loc='upper left', frameon=True)

    # Plot 1B: Energy vs Speed
    scatter = axes[1].scatter(
        df['Speed'], 
        df['Trip Energy Consumption'], 
        c=df['Trip Distance'], 
        cmap='viridis', 
        alpha=0.45, 
        s=22
    )
    cbar = fig.colorbar(scatter, ax=axes[1])
    cbar.set_label('Trip Distance (km)', rotation=270, labelpad=15)
    axes[1].set_title("Energy Consumption vs. Speed (Colored by Distance)")
    axes[1].set_xlabel("Average Speed")
    axes[1].set_ylabel("Trip Energy Consumption (kWh)")

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "eda_1_energy_analysis.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print(" -> Saved: eda_1_energy_analysis.png")

    # =========================================================================
    # 2. BATTERY / THERMAL ANALYSIS
    # =========================================================================
    print("\n" + "=" * 80)
    print(" 2. BATTERY / THERMAL ANALYSIS")
    print("=" * 80)
    print(f" - Min Cell Temp Range : {df['Minimum Cell Temperature of Battery'].min():.1f}°C to {df['Minimum Cell Temperature of Battery'].max():.1f}°C (Mean: {df['Minimum Cell Temperature of Battery'].mean():.2f}°C)")
    print(f" - Max Cell Temp Range : {df['Maximum Cell Temperature of Battery'].min():.1f}°C to {df['Maximum Cell Temperature of Battery'].max():.1f}°C (Mean: {df['Maximum Cell Temperature of Battery'].mean():.2f}°C)")
    print(f" - Avg Cell Temp Delta : {df['Temp_Delta'].mean():.2f}°C (Max Delta: {df['Temp_Delta'].max():.2f}°C)")
    print(f" - Operating Voltage   : {df['Total Voltage'].mean():.2f} V [Min: {df['Total Voltage'].min():.1f} V, Max: {df['Total Voltage'].max():.1f} V]")

    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle("2. Battery & Thermal Analysis", fontsize=15, y=0.98)

    # Plot 2A: Min vs Max Cell Temperature
    scatter_temp = axes[0].scatter(
        df['Minimum Cell Temperature of Battery'],
        df['Maximum Cell Temperature of Battery'],
        c=df['Temp_Delta'],
        cmap='magma',
        alpha=0.5,
        s=25
    )
    cbar_temp = fig.colorbar(scatter_temp, ax=axes[0])
    cbar_temp.set_label('Thermal Differential (°C)', rotation=270, labelpad=15)
    # Add parity line y=x
    min_val = min(df['Minimum Cell Temperature of Battery'].min(), df['Maximum Cell Temperature of Battery'].min())
    max_val = max(df['Minimum Cell Temperature of Battery'].max(), df['Maximum Cell Temperature of Battery'].max())
    axes[0].plot([min_val, max_val], [min_val, max_val], '--', color='#555555', alpha=0.7, label='Uniform Temp (Max = Min)')
    axes[0].set_title("Battery Cell Temp: Min vs. Max Temperature (°C)")
    axes[0].set_xlabel("Minimum Cell Temperature (°C)")
    axes[0].set_ylabel("Maximum Cell Temperature (°C)")
    axes[0].legend(loc='upper left', frameon=True)

    # Plot 2B: Cell Temperature Differential Distribution
    sns.histplot(
        df['Temp_Delta'], 
        kde=True, 
        color='#2b8cbe', 
        bins=30, 
        ax=axes[1],
        edgecolor='white',
        linewidth=0.5
    )
    axes[1].axvline(df['Temp_Delta'].mean(), color='#e6550d', linestyle='--', linewidth=2, label=f"Mean Delta ({df['Temp_Delta'].mean():.2f}°C)")
    axes[1].axvline(df['Temp_Delta'].median(), color='#2ca02c', linestyle=':', linewidth=2, label=f"Median Delta ({df['Temp_Delta'].median():.2f}°C)")
    axes[1].set_title("Distribution of Cell Temperature Differential (Max - Min)")
    axes[1].set_xlabel("Temperature Differential (°C)")
    axes[1].set_ylabel("Trip Frequency")
    axes[1].legend(loc='upper right', frameon=True)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "eda_2_battery_thermal_analysis.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print(" -> Saved: eda_2_battery_thermal_analysis.png")

    # =========================================================================
    # 3. CORRELATION ANALYSIS
    # =========================================================================
    print("\n" + "=" * 80)
    print(" 3. CORRELATION ANALYSIS")
    print("=" * 80)
    
    feature_cols = [
        'Trip Energy Consumption', 'Trip Distance', 'Speed', 'Trip Time Length',
        'Total Voltage', 'Current', 'Maximum Cell Temperature of Battery',
        'Minimum Cell Temperature of Battery', 'Temp_Delta', 'Energy_per_Distance'
    ]
    corr_matrix = df[feature_cols].corr()

    print("Correlations with Trip Energy Consumption:")
    energy_corr = corr_matrix['Trip Energy Consumption'].drop('Trip Energy Consumption').sort_values(ascending=False)
    for feat, val in energy_corr.items():
        print(f" - {feat:<40}: {val:+.4f}")

    # Visualization: Heatmap
    plt.figure(figsize=(11, 8.5))
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
    cmap = sns.diverging_palette(230, 20, as_cmap=True)
    sns.heatmap(
        corr_matrix, 
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
    plt.title("3. Correlation Heatmap - EV Telemetry & Energy Dynamics", pad=15, fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "eda_3_correlation_heatmap.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print(" -> Saved: eda_3_correlation_heatmap.png")

    # =========================================================================
    # 4. OUTLIER ANALYSIS (BOXPLOTS)
    # =========================================================================
    print("\n" + "=" * 80)
    print(" 4. OUTLIER ANALYSIS")
    print("=" * 80)

    target_outlier_cols = [
        'Trip Energy Consumption',
        'Trip Distance',
        'Speed',
        'Current'
    ]

    for col in target_outlier_cols:
        stats = calculate_iqr_outliers(df, col)
        print(f"Outlier Stats for '{col}':")
        print(f"   Q1: {stats['q1']:.2f} | Q3: {stats['q3']:.2f} | IQR: {stats['iqr']:.2f}")
        print(f"   Lower Fence: {stats['lower_bound']:.2f} | Upper Fence: {stats['upper_bound']:.2f}")
        print(f"   Outliers Count: {stats['count']:,} ({stats['pct']:.2f}% of data)\n")

    # Visualization: 2x2 Boxplots Grid
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("4. Outlier Analysis: Key EV Metric Distributions & Boxplots", fontsize=15, y=0.98)

    palette_colors = ['#3182bd', '#31a354', '#756bb1', '#e6550d']
    units = ['kWh', 'km', 'km/h or index', 'A']

    for i, (col, color, unit) in enumerate(zip(target_outlier_cols, palette_colors, units)):
        ax = axes[i // 2, i % 2]
        
        # Boxplot with custom styling
        box = sns.boxplot(
            y=df[col], 
            ax=ax, 
            color=color, 
            width=0.4,
            fliersize=4,
            flierprops=dict(marker='o', markerfacecolor='#e41a1c', alpha=0.5, markeredgecolor='none'),
            boxprops=dict(alpha=0.75, edgecolor='black', linewidth=1.2),
            whiskerprops=dict(color='black', linewidth=1.2),
            capprops=dict(color='black', linewidth=1.2),
            medianprops=dict(color='#ffd700', linewidth=2.2)  # Gold median line
        )
        
        # Overlay mean marker
        mean_val = df[col].mean()
        median_val = df[col].median()
        ax.axhline(mean_val, color='#000000', linestyle='--', linewidth=1.2, label=f'Mean: {mean_val:.2f}')
        
        ax.set_title(f"{col}", fontsize=13, fontweight='bold', pad=10)
        ax.set_ylabel(f"{col} ({unit})" if unit else col, fontsize=11)
        ax.set_xlabel("")
        ax.grid(True, linestyle='--', alpha=0.6)
        
        # Add summary stats text badge
        iqr_info = calculate_iqr_outliers(df, col)
        stats_text = f"Median: {median_val:.2f}\nMean: {mean_val:.2f}\nOutliers: {iqr_info['count']} ({iqr_info['pct']:.1f}%)"
        ax.text(
            0.95, 0.95, stats_text,
            transform=ax.transAxes,
            verticalalignment='top',
            horizontalalignment='right',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='#aaaaaa', alpha=0.9),
            fontsize=9
        )
        ax.legend(loc='lower right', frameon=True, fontsize=9)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "eda_4_outlier_boxplots.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print(" -> Saved: eda_4_outlier_boxplots.png")

    print("\n" + "=" * 80)
    print("                     EDA PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()
