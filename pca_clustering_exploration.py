"""
===============================================================================
LAB 8: PRINCIPAL COMPONENT ANALYSIS (PCA) & K-MEANS CLUSTERING EXPLORATION
DATASET: ELECTRIC VEHICLE (EV) TRIP ENERGY CONSUMPTION DATASET
===============================================================================
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def run_pca_clustering_pipeline():
    print("=" * 80)
    print("1. LOADING & PREPARING THE DATASET FOR PCA AND CLUSTERING")
    print("=" * 80)

    csv_file = "cleaned_ev_data.csv"
    if not os.path.exists(csv_file):
        csv_file = "Electric Vehicle Trip Energy Consumption Data.csv"

    print(f"Reading dataset: {csv_file}")
    df = pd.read_csv(csv_file)
    print(f"Total records: {len(df):,}")
    print(f"Total attributes: {df.shape[1]}")

    # Missing value audit
    missing_count = df.isnull().sum().sum()
    print(f"Missing values found: {missing_count}")
    if missing_count > 0:
        df = df.dropna().reset_index(drop=True)
        print(f"Records after dropping missing values: {len(df):,}")

    # Select operational telemetry features
    features = [
        'Trip Distance', 
        'Trip Time Length', 
        'Speed', 
        'Current', 
        'Total Voltage', 
        'Trip Energy Consumption'
    ]
    print(f"\nFeatures selected for PCA: {features}")
    X = df[features].copy()

    # Feature Standardization (Mandatory for PCA to avoid variance dominance)
    print("\nStandardizing features with StandardScaler (zero mean, unit variance)...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # -------------------------------------------------------------------------
    # 2. PRINCIPAL COMPONENT ANALYSIS (PCA)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("2. PRINCIPAL COMPONENT ANALYSIS (DIMENSIONALITY REDUCTION)")
    print("=" * 80)

    pca = PCA(n_components=2, random_state=42)
    X_pca = pca.fit_transform(X_scaled)

    evr = pca.explained_variance_ratio_
    cum_evr = np.cumsum(evr)

    print(f"Explained Variance Ratio:")
    print(f"  PC1: {evr[0]:.4f} ({evr[0]*100:.2f}%)")
    print(f"  PC2: {evr[1]:.4f} ({evr[1]*100:.2f}%)")
    print(f"  Total Retained Variance: {cum_evr[1]:.4f} ({cum_evr[1]*100:.2f}%)")

    # PCA Component Loadings (Feature Contributions)
    loadings_df = pd.DataFrame(
        pca.components_.T,
        columns=['PC1', 'PC2'],
        index=features
    )
    print("\nPrincipal Component Loadings (Feature Weights):")
    print(loadings_df.round(4))

    # -------------------------------------------------------------------------
    # 3. K-MEANS CLUSTERING ON PCA-PROJECTED SPACE
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("3. K-MEANS CLUSTERING ON REDUCED PC1-PC2 SPACE (K = 3)")
    print("=" * 80)

    k_clusters = 3
    kmeans = KMeans(n_clusters=k_clusters, random_state=42, n_init=10, max_iter=300)
    cluster_labels = kmeans.fit_predict(X_pca)

    df['Cluster'] = cluster_labels
    df['PC1'] = X_pca[:, 0]
    df['PC2'] = X_pca[:, 1]

    # Evaluate Clustering Performance
    sil_score = silhouette_score(X_pca, cluster_labels)
    print(f"K-Means (K={k_clusters}) Inertia: {kmeans.inertia_:.2f}")
    print(f"K-Means (K={k_clusters}) Silhouette Score: {sil_score:.4f}")

    print("\nCluster Distribution:")
    dist = df['Cluster'].value_counts().sort_index()
    for c_id, count in dist.items():
        print(f"  Cluster {c_id}: {count:,} trips ({count/len(df)*100:.2f}%)")

    # Cluster Centroids in PCA space
    print("\nCluster Centroids in PC1-PC2 Space:")
    centroids = kmeans.cluster_centers_
    for idx, c in enumerate(centroids):
        print(f"  Centroid {idx}: PC1 = {c[0]:.3f}, PC2 = {c[1]:.3f}")

    # -------------------------------------------------------------------------
    # 4. GENERATE VISUALIZATIONS (MATCHING USER'S REFERRAL TEMPLATE)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("4. GENERATING PUBLICATION-QUALITY PLOTS")
    print("=" * 80)

    # FIGURE 1: PCA Explained Variance (Bar Chart - Exact Layout from Reference)
    fig1, ax1 = plt.subplots(figsize=(7.5, 5.2), dpi=300)
    fig1.canvas.manager.set_window_title('Figure 1: PCA Explained Variance') if hasattr(fig1.canvas, 'manager') and fig1.canvas.manager else None

    pc_names = ['PC1', 'PC2']
    bars = ax1.bar(pc_names, evr, color='#4c72b0', width=0.68, edgecolor='none')
    ax1.set_title('PCA Explained Variance', fontsize=13, fontweight='bold', pad=12)
    ax1.set_ylabel('Explained Variance Ratio', fontsize=11, fontweight='bold')
    ax1.set_ylim(0.0, 0.40)
    ax1.grid(False)  # Clean aesthetic matching reference

    # Annotate bar values
    for bar in bars:
        height = bar.get_height()
        ax1.annotate(f'{height:.3f}',
                     xy=(bar.get_x() + bar.get_width() / 2, height),
                     xytext=(0, 4),
                     textcoords="offset points",
                     ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()
    fig1_path = "pca_explained_variance.png"
    plt.savefig(fig1_path, dpi=300)
    print(f"[Saved Graph] PCA Explained Variance saved to '{fig1_path}'")

    # FIGURE 2: K-Means Clusters Visualized Using PCA (Scatter Plot with Viridis Colorbar)
    fig2, ax2 = plt.subplots(figsize=(8.5, 6.2), dpi=300)
    fig2.canvas.manager.set_window_title('Figure 2: K-Means Clusters Visualized Using PCA') if hasattr(fig2.canvas, 'manager') and fig2.canvas.manager else None

    scatter = ax2.scatter(
        X_pca[:, 0], 
        X_pca[:, 1], 
        c=cluster_labels, 
        cmap='viridis', 
        s=18, 
        alpha=0.65, 
        edgecolors='none'
    )
    
    # Plot cluster centroids
    ax2.scatter(
        centroids[:, 0], 
        centroids[:, 1], 
        c='white', 
        marker='X', 
        s=120, 
        edgecolor='black', 
        linewidth=1.5, 
        zorder=10,
        label='Centroids'
    )

    ax2.set_title('K-Means Clusters Visualized Using PCA', fontsize=13, fontweight='bold', pad=12)
    ax2.set_xlabel('Principal Component 1', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Principal Component 2', fontsize=11, fontweight='bold')
    ax2.grid(True, linestyle='--', alpha=0.5)

    # Colorbar matching reference layout
    cbar = plt.colorbar(scatter, ax=ax2)
    cbar.set_label('Cluster', fontsize=11, fontweight='bold', rotation=270, labelpad=15)
    cbar.set_ticks(np.linspace(0, k_clusters - 1, 9))

    plt.tight_layout()
    fig2_path = "kmeans_pca_clusters.png"
    plt.savefig(fig2_path, dpi=300)
    print(f"[Saved Graph] K-Means Clusters Visualized Using PCA saved to '{fig2_path}'")

    # FIGURE 3: Combined Report Figure (Dual-Panel for Lab Documentation)
    fig3, axes = plt.subplots(1, 2, figsize=(15, 6.0), dpi=300)
    fig3.canvas.manager.set_window_title('Figure 3: PCA & Clustering Summary') if hasattr(fig3.canvas, 'manager') and fig3.canvas.manager else None

    # Subplot A: Explained Variance
    bars3 = axes[0].bar(pc_names, evr, color='#4c72b0', width=0.6, edgecolor='none')
    axes[0].set_title('PCA Explained Variance Ratio', fontsize=12, fontweight='bold', pad=10)
    axes[0].set_ylabel('Explained Variance Ratio', fontsize=11, fontweight='bold')
    axes[0].set_ylim(0.0, 0.42)
    for bar in bars3:
        height = bar.get_height()
        axes[0].annotate(f'{height:.2%}',
                         xy=(bar.get_x() + bar.get_width() / 2, height),
                         xytext=(0, 4), textcoords="offset points",
                         ha='center', va='bottom', fontsize=9.5, fontweight='bold')
    axes[0].grid(True, linestyle='--', alpha=0.5)

    # Subplot B: Scatter Plot with Centroids
    sc3 = axes[1].scatter(X_pca[:, 0], X_pca[:, 1], c=cluster_labels, cmap='viridis', s=16, alpha=0.6, edgecolors='none')
    axes[1].scatter(centroids[:, 0], centroids[:, 1], c='red', marker='X', s=140, edgecolor='white', linewidth=1.5, zorder=10, label='Centroids')
    axes[1].set_title(f'K-Means Clusters in PC1-PC2 Space (K={k_clusters})', fontsize=12, fontweight='bold', pad=10)
    axes[1].set_xlabel('Principal Component 1', fontsize=11, fontweight='bold')
    axes[1].set_ylabel('Principal Component 2', fontsize=11, fontweight='bold')
    axes[1].legend(loc='upper right')
    axes[1].grid(True, linestyle='--', alpha=0.5)
    cbar3 = plt.colorbar(sc3, ax=axes[1])
    cbar3.set_label('Cluster', fontsize=10, fontweight='bold', rotation=270, labelpad=12)

    plt.tight_layout()
    fig3_path = "pca_clustering_combined_report.png"
    plt.savefig(fig3_path, dpi=300)
    print(f"[Saved Graph] Combined Report Figure saved to '{fig3_path}'")

    # -------------------------------------------------------------------------
    # 5. DATA EXPORT & PROFILING
    # -------------------------------------------------------------------------
    cluster_profile = df.groupby('Cluster').agg({
        'Trip Distance': ['count', 'mean'],
        'Trip Time Length': ['mean'],
        'Speed': ['mean'],
        'Current': ['mean'],
        'Total Voltage': ['mean'],
        'Trip Energy Consumption': ['mean']
    }).round(2)
    print("\n" + "=" * 80)
    print("5. QUANTITATIVE CLUSTER PROFILE (PHYSICAL DOMAIN METRICS)")
    print("=" * 80)
    print(cluster_profile)

    # Save outputs
    out_csv = "ev_trips_pca_clusters.csv"
    df.to_csv(out_csv, index=False)
    print(f"\n[Saved Data] Exported PCA-clustered dataset to '{out_csv}'")

    # Save summary metrics
    metrics_df = pd.DataFrame({
        'Metric': ['PC1 Explained Variance', 'PC2 Explained Variance', 'Cumulative 2-Component Variance', 'K-Means K', 'Silhouette Score', 'Inertia'],
        'Value': [f"{evr[0]:.4f}", f"{evr[1]:.4f}", f"{cum_evr[1]:.4f}", k_clusters, f"{sil_score:.4f}", f"{kmeans.inertia_:.2f}"]
    })
    metrics_df.to_csv("pca_clustering_summary_metrics.csv", index=False)
    print(f"[Saved Metrics] Exported metrics summary to 'pca_clustering_summary_metrics.csv'")

    print("\nDisplaying interactive graph windows (close windows to finish)...")
    try:
        plt.show()
    except Exception:
        pass
    print("\nPCA and Clustering exploration pipeline executed successfully!")

if __name__ == '__main__':
    run_pca_clustering_pipeline()
