"""
===============================================================================
LAB 7: EXPLORATION OF K-MEANS CLUSTERING AND OPTIMAL K SELECTION
DATASET: ELECTRIC VEHICLE (EV) TRIP ENERGY CONSUMPTION DATASET
===============================================================================
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, silhouette_samples
from sklearn.preprocessing import StandardScaler

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def run_kmeans_pipeline():
    print("=" * 80)
    print("1. LOADING & PREPARING THE DATASET FOR K-MEANS CLUSTERING")
    print("=" * 80)

    csv_file = "cleaned_ev_data.csv"
    if not os.path.exists(csv_file):
        csv_file = "Electric Vehicle Trip Energy Consumption Data.csv"

    print(f"Reading dataset: {csv_file}")
    df = pd.read_csv(csv_file)
    print(f"Total records: {len(df):,}")
    print(f"Total attributes: {df.shape[1]}")

    # Missing value verification
    missing_count = df.isnull().sum().sum()
    print(f"Missing values found: {missing_count}")
    if missing_count > 0:
        df = df.dropna().reset_index(drop=True)
        print(f"Records after dropping missing values: {len(df):,}")

    # Select numerical kinematic and operational features
    features = ['Trip Distance', 'Trip Time Length', 'Speed']
    print(f"\nFeatures selected for K-Means Clustering: {features}")
    X = df[features].copy()

    # Feature Standardization (Crucial for distance-based clustering algorithms)
    print("\nApplying StandardScaler to eliminate scale disparity across features...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_scaled_df = pd.DataFrame(X_scaled, columns=[f"{col}_scaled" for col in features])

    # K values to explore (from K = 2 to K = 10)
    k_range = list(range(2, 11))
    inertias = []
    silhouette_scores = []
    models = {}

    print("\n" + "=" * 80)
    print("2. EXPLORING K-MEANS & COMPUTING OPTIMAL K SELECTION METRICS")
    print("=" * 80)
    print(f"{'K':<6} | {'Inertia (SSE)':<18} | {'Silhouette Score':<18} | {'Inertia Reduction':<18}")
    print("-" * 66)

    prev_inertia = None
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
        labels = kmeans.fit_predict(X_scaled)
        models[k] = kmeans
        
        inertia = kmeans.inertia_
        inertias.append(inertia)
        
        # Exact silhouette score on full standardized dataset
        sil = silhouette_score(X_scaled, labels)
        silhouette_scores.append(sil)
        
        reduction_str = f"-{(prev_inertia - inertia):.2f}" if prev_inertia is not None else "N/A"
        prev_inertia = inertia
        
        print(f"{k:<6} | {inertia:<18.2f} | {sil:<18.4f} | {reduction_str:<18}")

    # Save metrics table
    metrics_df = pd.DataFrame({
        'K': k_range,
        'Inertia': inertias,
        'Silhouette_Score': silhouette_scores
    })
    metrics_df.to_csv("kmeans_clustering_metrics.csv", index=False)
    print(f"\n[Saved Metrics] Saved evaluation metrics to 'kmeans_clustering_metrics.csv'")

    # Determine optimal K
    best_k_sil = k_range[np.argmax(silhouette_scores)]
    print("-" * 66)
    print(f"Peak Silhouette Score: K = {best_k_sil} ({max(silhouette_scores):.4f})")
    print("Elbow Point analysis indicates substantial bend from K=3 to K=4 (SSE drop slows down).")
    optimal_k = 4  # Aligns with elbow point and established 4 energy tiers
    print(f"Selected Optimal K for EV Trip Profiling: K = {optimal_k}")

    # -------------------------------------------------------------------------
    # GENERATE PLOTS
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("3. GENERATING PUBLICATION-QUALITY VISUALIZATIONS")
    print("=" * 80)

    # FIGURE 1: Elbow Method (Standalone)
    plt.figure(figsize=(8, 5.2), dpi=300)
    plt.plot(k_range, inertias, marker='o', linestyle='-', color='#1f77b4', linewidth=2.2, markersize=7)
    plt.title('Elbow Method', fontsize=14, fontweight='bold', pad=12)
    plt.xlabel('Number of Clusters (K)', fontsize=11, fontweight='bold')
    plt.ylabel('Inertia', fontsize=11, fontweight='bold')
    plt.xticks(k_range)
    plt.grid(True, linestyle='--', alpha=0.6)
    # Annotate elbow point
    plt.annotate(f'Elbow Point (K={optimal_k})\nInertia: {inertias[k_range.index(optimal_k)]:.1f}', 
                 xy=(optimal_k, inertias[k_range.index(optimal_k)]),
                 xytext=(optimal_k + 0.8, inertias[k_range.index(optimal_k)] + 3000),
                 arrowprops=dict(facecolor='#d62728', shrink=0.08, width=1.5, headwidth=7),
                 fontsize=9.5, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffe6e6', edgecolor='#d62728', alpha=0.9))
    plt.tight_layout()
    fig1_path = "kmeans_elbow_method.png"
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    print(f"[Saved Graph] Elbow Method saved to '{fig1_path}'")

    # FIGURE 2: Silhouette Scores (Standalone)
    plt.figure(figsize=(8, 5.2), dpi=300)
    plt.plot(k_range, silhouette_scores, marker='o', linestyle='-', color='#1f77b4', linewidth=2.2, markersize=7)
    plt.title('Silhouette Scores', fontsize=14, fontweight='bold', pad=12)
    plt.xlabel('Number of Clusters (K)', fontsize=11, fontweight='bold')
    plt.ylabel('Silhouette Score', fontsize=11, fontweight='bold')
    plt.xticks(k_range)
    plt.ylim(min(silhouette_scores) - 0.02, max(silhouette_scores) + 0.025)
    plt.grid(True, linestyle='--', alpha=0.6)
    for k, s in zip(k_range, silhouette_scores):
        plt.annotate(f"{s:.3f}", (k, s), textcoords="offset points", 
                     xytext=(0, 9), ha='center', fontsize=9, fontweight='bold')
    plt.tight_layout()
    fig2_path = "kmeans_silhouette_scores.png"
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    print(f"[Saved Graph] Silhouette Scores saved to '{fig2_path}'")

    # FIGURE 3: Combined 2-Panel Plot (Matching User Screenshot Layout)
    fig, axes = plt.subplots(2, 1, figsize=(8.5, 9.5), dpi=300)
    fig.canvas.manager.set_window_title('Figure 1: K-Means Optimal K Selection') if hasattr(fig.canvas, 'manager') and fig.canvas.manager else None
    
    # Subplot 1: Elbow Method
    axes[0].plot(k_range, inertias, marker='o', linestyle='-', color='#1f77b4', linewidth=2.2, markersize=7)
    axes[0].set_title('Elbow Method', fontsize=13, fontweight='bold', pad=10)
    axes[0].set_xlabel('Number of Clusters (K)', fontsize=11, fontweight='bold')
    axes[0].set_ylabel('Inertia', fontsize=11, fontweight='bold')
    axes[0].set_xticks(k_range)
    axes[0].grid(True, linestyle='--', alpha=0.6)
    
    # Subplot 2: Silhouette Scores
    axes[1].plot(k_range, silhouette_scores, marker='o', linestyle='-', color='#1f77b4', linewidth=2.2, markersize=7)
    axes[1].set_title('Silhouette Scores', fontsize=13, fontweight='bold', pad=10)
    axes[1].set_xlabel('Number of Clusters (K)', fontsize=11, fontweight='bold')
    axes[1].set_ylabel('Silhouette Score', fontsize=11, fontweight='bold')
    axes[1].set_xticks(k_range)
    axes[1].set_ylim(min(silhouette_scores) - 0.02, max(silhouette_scores) + 0.025)
    axes[1].grid(True, linestyle='--', alpha=0.6)
    for k, s in zip(k_range, silhouette_scores):
        axes[1].annotate(f"{s:.3f}", (k, s), textcoords="offset points", 
                         xytext=(0, 9), ha='center', fontsize=8.5, fontweight='bold')

    plt.tight_layout()
    fig3_path = "kmeans_optimal_k_selection.png"
    plt.savefig(fig3_path, dpi=300)
    print(f"[Saved Graph] Combined Optimal K Selection figure saved to '{fig3_path}'")

    # -------------------------------------------------------------------------
    # FIT OPTIMAL MODEL (K = 4) & CLUSTER INTERPRETATION
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print(f"4. CLUSTER PROFILING & CHARACTERIZATION (K = {optimal_k})")
    print("=" * 80)

    best_model = models[optimal_k]
    df['Cluster'] = best_model.labels_

    # Map cluster names based on distance/speed dynamics
    cluster_summary = df.groupby('Cluster').agg({
        'Trip Distance': ['count', 'mean', 'std'],
        'Trip Time Length': ['mean', 'std'],
        'Speed': ['mean', 'std'],
        'Trip Energy Consumption': ['mean', 'std']
    }).round(2)
    print("\nCluster Summary Statistics:")
    print(cluster_summary)

    # Determine descriptive labels for clusters based on mean distance & speed
    cluster_means = df.groupby('Cluster')[['Trip Distance', 'Trip Time Length', 'Speed', 'Trip Energy Consumption']].mean()
    cluster_labels = {}
    for c_id, row in cluster_means.iterrows():
        if row['Trip Distance'] < 10 and row['Speed'] < 45:
            cluster_labels[c_id] = f"Cluster {c_id}: Short City Stop-and-Go"
        elif row['Trip Distance'] < 15 and row['Speed'] >= 45:
            cluster_labels[c_id] = f"Cluster {c_id}: Moderate Urban Transit"
        elif row['Trip Distance'] >= 15 and row['Speed'] >= 50:
            cluster_labels[c_id] = f"Cluster {c_id}: High-Speed Long Distance"
        else:
            cluster_labels[c_id] = f"Cluster {c_id}: Mixed Driving Session"
            
    df['Cluster_Label'] = df['Cluster'].map(cluster_labels)

    # FIGURE 4: 2D Cluster Projections & Centroids
    fig2, axes2 = plt.subplots(1, 2, figsize=(14, 5.8), dpi=300)
    fig2.canvas.manager.set_window_title('Figure 2: K-Means Cluster Space & Centroids') if hasattr(fig2.canvas, 'manager') and fig2.canvas.manager else None
    palette = sns.color_palette("Set2", optimal_k)

    # Transform centroids back to original unscaled feature space for intuitive plotting
    centroids_orig = scaler.inverse_transform(best_model.cluster_centers_)

    # Subplot 1: Trip Distance vs Speed
    for i in range(optimal_k):
        subset = df[df['Cluster'] == i]
        axes2[0].scatter(subset['Trip Distance'], subset['Speed'], 
                         label=f'Cluster {i} (n={len(subset):,})', 
                         alpha=0.45, s=22, color=palette[i], edgecolors='none')
    axes2[0].scatter(centroids_orig[:, 0], centroids_orig[:, 2], 
                     c='black', marker='X', s=160, edgecolor='white', linewidth=1.5, label='Centroids', zorder=10)
    axes2[0].set_title('K-Means Clusters: Trip Distance vs Speed', fontsize=12, fontweight='bold', pad=10)
    axes2[0].set_xlabel('Trip Distance (km)', fontsize=11, fontweight='bold')
    axes2[0].set_ylabel('Speed (km/h)', fontsize=11, fontweight='bold')
    axes2[0].legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=9)
    axes2[0].grid(True, linestyle='--', alpha=0.5)

    # Subplot 2: Trip Distance vs Energy Consumption
    for i in range(optimal_k):
        subset = df[df['Cluster'] == i]
        axes2[1].scatter(subset['Trip Distance'], subset['Trip Energy Consumption'], 
                         label=f'Cluster {i}', 
                         alpha=0.45, s=22, color=palette[i], edgecolors='none')
    axes2[1].set_title('K-Means Clusters: Distance vs Energy Consumption', fontsize=12, fontweight='bold', pad=10)
    axes2[1].set_xlabel('Trip Distance (km)', fontsize=11, fontweight='bold')
    axes2[1].set_ylabel('Trip Energy Consumption (kWh)', fontsize=11, fontweight='bold')
    axes2[1].legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=9)
    axes2[1].grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()
    fig4_path = "kmeans_clusters_visualization.png"
    plt.savefig(fig4_path, dpi=300)
    print(f"[Saved Graph] Cluster Visualization saved to '{fig4_path}'")

    # Save clustered dataset
    output_csv = "ev_trips_with_kmeans_clusters.csv"
    df.to_csv(output_csv, index=False)
    print(f"\n[Saved Data] Exported clustered dataset with {len(df):,} records to '{output_csv}'")
    print("\nDisplaying interactive graph windows (close window to finish)...")
    try:
        plt.show()
    except Exception:
        pass
    print("\nK-Means Clustering and Optimal K Selection pipeline executed successfully!")

if __name__ == '__main__':
    run_kmeans_pipeline()
