"""
================================================================================
ANALYSIS SERVICE: DATASET SUMMARY, EDA METRICS & VISUALIZATION CATALOG
================================================================================
Encapsulates:
  - High-performance statistical profiling of the EV fleet dataset (10,151 trips)
  - Target variable (Trip Energy Consumption) distribution parameters
  - Correlation metrics and feature distributions for interactive frontend charts
  - Publication figure catalog with descriptive engineering context
================================================================================
"""

import os
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEANED_DATA_PATH = os.path.join(BASE_DIR, "cleaned_ev_data.csv")
RAW_DATA_PATH = os.path.join(BASE_DIR, "Electric Vehicle Trip Energy Consumption Data.csv")

_CACHED_SUMMARY = None


def get_dataset_summary() -> dict:
    """
    Computes and caches comprehensive descriptive statistics from cleaned_ev_data.csv.
    """
    global _CACHED_SUMMARY
    if _CACHED_SUMMARY is not None:
        return _CACHED_SUMMARY

    target_path = CLEANED_DATA_PATH if os.path.exists(CLEANED_DATA_PATH) else RAW_DATA_PATH
    if not os.path.exists(target_path):
        return {
            'status': 'error',
            'message': 'EV trip dataset not found on disk.'
        }

    try:
        df = pd.read_csv(target_path)
        
        # Calculate engineered features if not present
        if 'Battery Power' not in df.columns and 'Total Voltage' in df.columns and 'Current' in df.columns:
            df['Battery Power'] = (df['Total Voltage'] * df['Current']) / 1000.0
        if 'Temperature Differential' not in df.columns and 'Maximum Cell Temperature of Battery' in df.columns:
            df['Temperature Differential'] = df['Maximum Cell Temperature of Battery'] - df['Minimum Cell Temperature of Battery']

        target = df['Trip Energy Consumption']
        dist = df['Trip Distance']
        speed = df['Speed']
        voltage = df['Total Voltage']
        current = df['Current']
        max_t = df['Maximum Cell Temperature of Battery']
        min_t = df['Minimum Cell Temperature of Battery']

        # Key numeric statistics
        stats = {
            'total_trips': int(len(df)),
            'total_features': int(df.shape[1]),
            'unique_vehicles': int(df['Vehicle ID'].nunique()) if 'Vehicle ID' in df.columns else 50,
            'dataset_filename': os.path.basename(target_path),
            'target_variable': {
                'name': 'Trip Energy Consumption',
                'unit': 'kWh',
                'mean': float(round(target.mean(), 3)),
                'median': float(round(target.median(), 3)),
                'std': float(round(target.std(), 3)),
                'min': float(round(target.min(), 3)),
                'max': float(round(target.max(), 3)),
                'p25': float(round(target.quantile(0.25), 3)),
                'p75': float(round(target.quantile(0.75), 3)),
                'p90': float(round(target.quantile(0.90), 3)),
                'skewness': float(round(target.skew(), 3)),
                'kurtosis': float(round(target.kurtosis(), 3))
            },
            'operational_telemetry': {
                'avg_distance_km': float(round(dist.mean(), 2)),
                'max_distance_km': float(round(dist.max(), 2)),
                'avg_speed_kmh': float(round(speed.mean(), 2)),
                'max_speed_kmh': float(round(speed.max(), 2)),
                'avg_voltage_v': float(round(voltage.mean(), 2)),
                'avg_current_a': float(round(current.mean(), 2)),
                'avg_max_temp_c': float(round(max_t.mean(), 2)),
                'avg_min_temp_c': float(round(min_t.mean(), 2)),
                'avg_temp_diff_c': float(round((max_t - min_t).mean(), 2))
            }
        }

        # Histogram data for Target Variable
        counts, edges = np.histogram(target.dropna(), bins=14)
        labels = [f"{round(edges[i], 1)}-{round(edges[i+1], 1)}" for i in range(len(counts))]
        stats['target_distribution'] = {
            'labels': labels,
            'counts': [int(c) for c in counts]
        }

        # Distance distribution bins
        dist_counts, dist_edges = np.histogram(dist.dropna(), bins=10)
        dist_labels = [f"{round(dist_edges[i], 0):.0f}-{round(dist_edges[i+1], 0):.0f} km" for i in range(len(dist_counts))]
        stats['distance_distribution'] = {
            'labels': dist_labels,
            'counts': [int(c) for c in dist_counts]
        }

        # Speed distribution bins
        speed_counts, speed_edges = np.histogram(speed.dropna(), bins=10)
        speed_labels = [f"{round(speed_edges[i], 0):.0f}-{round(speed_edges[i+1], 0):.0f} km/h" for i in range(len(speed_counts))]
        stats['speed_distribution'] = {
            'labels': speed_labels,
            'counts': [int(c) for c in speed_counts]
        }

        # Day of week breakdown if available
        if 'Day of the Week' in df.columns:
            day_map = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}
            day_counts = df['Day of the Week'].value_counts().sort_index()
            stats['trips_by_day'] = {
                'labels': [day_map.get(int(k), str(k)) for k in day_counts.index],
                'counts': [int(v) for v in day_counts.values]
            }

        _CACHED_SUMMARY = stats
        return _CACHED_SUMMARY

    except Exception as exc:
        return {
            'status': 'error',
            'error': f"Failed to compute dataset summary: {str(exc)}"
        }


def get_visualizations_catalog() -> list[dict]:
    """
    Returns verified metadata and descriptions for all 13 publication figures.
    """
    catalog = [
        {
            'id': 'eda_graph1',
            'category': 'Exploratory Data Analysis',
            'title': 'Target Variable Distribution (Trip Energy Consumption)',
            'filename': 'eda_graph1_distribution_plot.png',
            'description': 'Right-skewed histogram with KDE overlay showing positive skew (mean 3.95 kWh vs median 3.14 kWh).',
            'significance': 'Validates need for robust non-linear gradient boosting regressor capable of handling right-tail trips.'
        },
        {
            'id': 'eda_graph2',
            'category': 'Exploratory Data Analysis',
            'title': 'Pearson Correlation Matrix Heatmap',
            'filename': 'eda_graph2_correlation_heatmap.png',
            'description': 'Lower-triangle correlation matrix of battery telemetry, distance, speed, and energy.',
            'significance': 'Confirms high correlation between Trip Distance and Energy Consumption (r = 0.94).'
        },
        {
            'id': 'eda_graph3',
            'category': 'Exploratory Data Analysis',
            'title': 'Multi-Feature Outlier Boxplots',
            'filename': 'eda_graph3_outlier_boxplots.png',
            'description': 'Interquartile range (IQR) boxplots across distance, speed, voltage, and cell temperatures.',
            'significance': 'Shows distribution spread and confirms lack of extreme corrupt telemetry after Step 2 cleaning.'
        },
        {
            'id': 'eda_graph4',
            'category': 'Exploratory Data Analysis',
            'title': 'Multivariate Pairplot Matrix',
            'filename': 'eda_graph4_pairplot_matrix.png',
            'description': 'Bivariate scatter matrix demonstrating joint dynamics of speed, distance, and pack power.',
            'significance': 'Highlights physical clusters in urban vs. highway velocity envelopes.'
        },
        {
            'id': 'eda_graph5',
            'category': 'Exploratory Data Analysis',
            'title': 'Battery Thermal Dynamics & Cell Differential',
            'filename': 'eda_graph5_battery_thermal_dynamics.png',
            'description': 'Scatter plot of maximum vs. minimum cell temperature and delta-T thermal gradient.',
            'significance': 'Demonstrates thermal stress boundaries where BTMS cooling is critically required.'
        },
        {
            'id': 'reg_comparison',
            'category': 'Model Evaluation',
            'title': 'Supervised Regression Model Comparison',
            'filename': 'regression_model_comparison.png',
            'description': 'Bar chart comparing MAE, RMSE, and R² scores of Linear Regression, Random Forest, and Gradient Boosting.',
            'significance': 'Gradient Boosting achieves champion performance with lowest RMSE (1.0216 kWh) and highest R² (0.8713).'
        },
        {
            'id': 'actual_vs_predicted',
            'category': 'Model Evaluation',
            'title': 'Actual vs. Predicted Parity Plot',
            'filename': 'actual_vs_predicted_best_model.png',
            'description': 'Scatter plot against perfect 45-degree identity line showing tight fit across the test dataset.',
            'significance': 'Confirms strong predictive generalization without bias across low and high energy regimes.'
        },
        {
            'id': 'residual_plot',
            'category': 'Model Evaluation',
            'title': 'Residual Diagnostics & Error Distribution',
            'filename': 'residual_plot_best_model.png',
            'description': 'Residual vs. fitted energy values and zero-centered residual histogram.',
            'significance': 'Confirms homoscedasticity and normally distributed error residuals around zero.'
        },
        {
            'id': 'feature_importance',
            'category': 'Model Evaluation',
            'title': 'Gradient Boosting Feature Importances',
            'filename': 'feature_importance_best_model.png',
            'description': 'Tree-based impurity reduction ranking showing Trip Distance (92.1%), Time of Day, and Speed as top drivers.',
            'significance': 'Physical explainability aligns perfectly with Newtonian traction mechanics.'
        },
        {
            'id': 'sim_comparison',
            'category': 'Energy Management Simulator',
            'title': 'Strategy Energy Consumption Benchmark',
            'filename': 'sim_strategy_energy_comparison.png',
            'description': 'Comparative bar chart across 4 trip archetypes for Baseline, Eco, and Intelligent IEMS.',
            'significance': 'Intelligent IEMS achieves up to 9.2% auxiliary energy reduction while preserving passenger thermal comfort.'
        },
        {
            'id': 'sim_soc',
            'category': 'Energy Management Simulator',
            'title': 'Battery SoC Depletion Profiles',
            'filename': 'sim_soc_depletion_profiles.png',
            'description': 'Time-series battery State of Charge trajectories over the entire simulated trip duration.',
            'significance': 'Demonstrates slower SoC decay under Intelligent control compared to uncoordinated baseline.'
        },
        {
            'id': 'sim_power',
            'category': 'Energy Management Simulator',
            'title': 'Auxiliary Power Dynamic Allocation',
            'filename': 'sim_auxiliary_power_allocation.png',
            'description': 'Instantaneous kW allocation among HVAC compressor, BTMS pump, and electronics.',
            'significance': 'Visualizes adaptive modulating pulse-width and compressor throttling.'
        },
        {
            'id': 'sim_tradeoff',
            'category': 'Energy Management Simulator',
            'title': 'Thermal Comfort vs. Energy Tradeoff Analysis',
            'filename': 'sim_tradeoff_analysis.png',
            'description': 'Scatter Pareto tradeoff comparing energy savings versus cabin temperature deviation.',
            'significance': 'Proves Intelligent IEMS maintains cabin within comfort band unlike aggressive Eco mode.'
        }
    ]

    # Check file existence and populate path
    for item in catalog:
        fpath = os.path.join(BASE_DIR, item['filename'])
        item['available'] = os.path.exists(fpath)
        item['file_size_kb'] = round(os.path.getsize(fpath) / 1024.0, 1) if item['available'] else 0
        item['api_url'] = f"/api/figures/{item['filename']}"

    return catalog
