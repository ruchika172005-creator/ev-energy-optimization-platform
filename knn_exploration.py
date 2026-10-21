"""
===============================================================================
LAB 5: EXPLORATION AND IMPLEMENTATION OF THE K-NEAREST NEIGHBORS (KNN) ALGORITHM
DATASET: ELECTRIC VEHICLE TRIP ENERGY CONSUMPTION DATASET
===============================================================================
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def run_knn_pipeline():
    print("=" * 80)
    print("1. LOADING & PREPARING THE DATASET")
    print("=" * 80)
    
    csv_file = "cleaned_ev_data.csv"
    if not os.path.exists(csv_file):
        csv_file = "Electric Vehicle Trip Energy Consumption Data.csv"
    
    print(f"Reading dataset: {csv_file}")
    df = pd.read_csv(csv_file)
    print(f"Total records: {len(df):,}")
    print(f"Total attributes: {df.shape[1]}")

    # Check missing values
    missing_count = df.isnull().sum().sum()
    print(f"Missing values found: {missing_count}")
    if missing_count > 0:
        df = df.dropna()
        print(f"Records after dropping missing values: {len(df):,}")

    # Define 4 classes based on Energy Consumption quartiles: a, b, c, d
    # a: Low, b: Moderate, c: High, d: Very High
    df['energy_class'] = pd.qcut(df['Trip Energy Consumption'], q=4, labels=['a', 'b', 'c', 'd'])
    
    print("\nTarget Class Distribution:")
    class_dist = df['energy_class'].value_counts().sort_index()
    for cls_name, count in class_dist.items():
        print(f"  Class '{cls_name}': {count} records ({count/len(df)*100:.2f}%)")

    # Select numerical features
    features = ['Trip Distance', 'Trip Time Length', 'Speed']
    print(f"\nFeatures selected for KNN: {features}")
    X = df[features]
    y = df['energy_class']

    # Encode target labels
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    # Train / Test split (80:20 stratified split)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.20, random_state=42, stratify=y_encoded
    )
    print(f"\nDataset Split (80:20):")
    print(f"  Training set: {len(X_train):,} records")
    print(f"  Testing set:  {len(X_test):,} records")

    # Feature Scaling with StandardScaler
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Evaluate multiple K values
    k_values = [1, 3, 5, 7, 9, 11]
    accuracy_results = {}

    print("\n" + "=" * 80)
    print("2. EVALUATING KNN FOR DIFFERENT K VALUES (Euclidean Distance)")
    print("=" * 80)
    print(f"{'K':<6} | {'Testing Accuracy (%)':<20}")
    print("-" * 30)

    for k in k_values:
        knn = KNeighborsClassifier(n_neighbors=k, metric='euclidean')
        knn.fit(X_train_scaled, y_train)
        acc = knn.score(X_test_scaled, y_test)
        accuracy_results[k] = acc
        print(f"{k:<6} | {acc * 100:.2f}%")

    best_k = max(accuracy_results, key=accuracy_results.get)
    best_acc = accuracy_results[best_k]
    print("-" * 30)
    print(f"Optimal K: {best_k} with Testing Accuracy: {best_acc * 100:.2f}%")

    # Generate Figure 1: KNN Accuracy for Different K Values
    plt.figure(figsize=(8, 5.5), dpi=300)
    plt.plot(list(accuracy_results.keys()), list(accuracy_results.values()), 
             marker='o', linestyle='-', color='#1f77b4', linewidth=2, markersize=7)
    plt.title('KNN Accuracy for Different K Values', fontsize=13, fontweight='bold', pad=12)
    plt.xlabel('Number of Neighbors (K)', fontsize=11, fontweight='bold')
    plt.ylabel('Accuracy', fontsize=11, fontweight='bold')
    plt.xticks(k_values)
    plt.grid(True, linestyle='--', alpha=0.6)
    for k, acc in accuracy_results.items():
        plt.annotate(f"{acc*100:.2f}%", (k, acc), textcoords="offset points", 
                     xytext=(0, 8), ha='center', fontsize=9, fontweight='bold')
    plt.tight_layout()
    fig1_path = "knn_accuracy_vs_k.png"
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    print(f"\n[Saved Graph] Figure 1 saved to '{fig1_path}'")

    # Fit best model for Classification Report & Confusion Matrix
    knn_best = KNeighborsClassifier(n_neighbors=best_k, metric='euclidean')
    knn_best.fit(X_train_scaled, y_train)
    y_pred = knn_best.predict(X_test_scaled)

    # Classification Report
    print("\n" + "=" * 80)
    print(f"3. CLASSIFICATION REPORT (K = {best_k})")
    print("=" * 80)
    report = classification_report(y_test, y_pred, target_names=['a', 'b', 'c', 'd'], digits=4)
    print(report)

    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    print("=" * 80)
    print(f"4. CONFUSION MATRIX (K = {best_k})")
    print("=" * 80)
    print("Predicted:   a      b      c      d")
    labels = ['a', 'b', 'c', 'd']
    for idx, row in enumerate(cm):
        print(f"Actual {labels[idx]}:  " + "  ".join(f"{val:>5}" for val in row))

    # Generate Figure 2: Confusion Matrix Heatmap
    plt.figure(figsize=(7, 6), dpi=300)
    sns.heatmap(cm, annot=True, fmt='d', cmap='flare', cbar=True,
                xticklabels=['a', 'b', 'c', 'd'],
                yticklabels=['a', 'b', 'c', 'd'],
                annot_kws={"size": 11, "weight": "normal"})
    plt.title(f'Confusion Matrix - KNN (K={best_k})', fontsize=13, fontweight='bold', pad=12)
    plt.xlabel('Predicted Class', fontsize=11, fontweight='bold')
    plt.ylabel('Actual Class', fontsize=11, fontweight='bold')
    plt.tight_layout()
    fig2_path = "knn_confusion_matrix.png"
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    print(f"\n[Saved Graph] Figure 2 saved to '{fig2_path}'")
    print("\nExecution completed successfully!")

if __name__ == '__main__':
    run_knn_pipeline()
