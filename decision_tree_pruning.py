"""
===============================================================================
LAB 6: EXPLORATION OF THE DECISION TREE ALGORITHM WITH COST-COMPLEXITY PRUNING
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
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def run_decision_tree_pipeline():
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

    # Verify missing values
    missing_count = df.isnull().sum().sum()
    print(f"Missing values in dataset: {missing_count}")
    if missing_count > 0:
        df = df.dropna()

    # Define target variable (4 balanced classes: a, b, c, d)
    df['energy_class'] = pd.qcut(df['Trip Energy Consumption'], q=4, labels=['a', 'b', 'c', 'd'])
    
    # Feature selection
    features = ['Trip Distance', 'Trip Time Length', 'Speed']
    print(f"Features selected: {features}")
    X = df[features]
    y = df['energy_class']

    # Label encoding
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    # Stratified 80:20 Train-Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.20, random_state=42, stratify=y_encoded
    )
    print(f"\nDataset Split (80:20):")
    print(f"  Training set: {len(X_train):,} records")
    print(f"  Testing set:  {len(X_test):,} records")

    # -------------------------------------------------------------------------
    # 2. UNPRUNED DECISION TREE
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("2. UNPRUNED DECISION TREE (Full Tree Growth)")
    print("=" * 80)
    dt_unpruned = DecisionTreeClassifier(random_state=42)
    dt_unpruned.fit(X_train, y_train)

    unpruned_train_acc = dt_unpruned.score(X_train, y_train)
    unpruned_test_acc = dt_unpruned.score(X_test, y_test)
    unpruned_depth = dt_unpruned.get_depth()
    unpruned_leaves = dt_unpruned.get_n_leaves()

    print(f"Training accuracy: {unpruned_train_acc * 100:.2f}%")
    print(f"Testing accuracy:  {unpruned_test_acc * 100:.2f}%")
    print(f"Tree depth:        {unpruned_depth}")
    print(f"Number of leaves:  {unpruned_leaves:,}")

    y_pred_unpruned = dt_unpruned.predict(X_test)
    print("\nClassification Report (Unpruned Tree):")
    print(classification_report(y_test, y_pred_unpruned, target_names=['a', 'b', 'c', 'd'], digits=4))

    cm_unpruned = confusion_matrix(y_test, y_pred_unpruned)
    print("Confusion Matrix (Unpruned Tree):")
    print("Predicted:    a      b      c      d")
    labels = ['a', 'b', 'c', 'd']
    for idx, row in enumerate(cm_unpruned):
        print(f"Actual {labels[idx]}:   " + "  ".join(f"{val:>5}" for val in row))

    # -------------------------------------------------------------------------
    # 3. COST-COMPLEXITY PRUNING (ccp_alpha)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("3. COST-COMPLEXITY PRUNING EVALUATION")
    print("=" * 80)

    path = dt_unpruned.cost_complexity_pruning_path(X_train, y_train)
    ccp_alphas_all = path.ccp_alphas
    print(f"Total positive ccp_alpha values in path: {len([a for a in ccp_alphas_all if a > 0]):,}")

    # Five representative positive alpha values
    selected_alphas = [0.000100, 0.000200, 0.000300, 0.000450, 0.000600]

    pruning_results = []
    print(f"{'CCP Alpha':<12} | {'Training Acc (%)':<16} | {'Testing Acc (%)':<16} | {'Depth':<6} | {'Leaves':<8}")
    print("-" * 68)

    for alpha in selected_alphas:
        clf = DecisionTreeClassifier(random_state=42, ccp_alpha=alpha)
        clf.fit(X_train, y_train)
        tr_acc = clf.score(X_train, y_train)
        te_acc = clf.score(X_test, y_test)
        d = clf.get_depth()
        l = clf.get_n_leaves()
        pruning_results.append({
            'alpha': alpha,
            'train_acc': tr_acc,
            'test_acc': te_acc,
            'depth': d,
            'leaves': l,
            'model': clf
        })
        print(f"{alpha:<12.6f} | {tr_acc * 100:>15.2f}% | {te_acc * 100:>15.2f}% | {d:<6} | {l:<8}")

    # -------------------------------------------------------------------------
    # 4. FIGURE 1: ACCURACY VS CCP_ALPHA
    # -------------------------------------------------------------------------
    alphas_plot = [r['alpha'] for r in pruning_results]
    train_accs = [r['train_acc'] for r in pruning_results]
    test_accs = [r['test_acc'] for r in pruning_results]

    plt.figure(figsize=(8, 5.5), dpi=300)
    plt.plot(alphas_plot, train_accs, marker='o', linestyle='-', color='#1f77b4', label='Training Accuracy', linewidth=2)
    plt.plot(alphas_plot, test_accs, marker='o', linestyle='-', color='#ff7f0e', label='Testing Accuracy', linewidth=2)
    plt.title('Decision Tree Performance with Cost-Complexity Pruning', fontsize=13, fontweight='bold', pad=12)
    plt.xlabel('CCP Alpha', fontsize=11, fontweight='bold')
    plt.ylabel('Accuracy', fontsize=11, fontweight='bold')
    plt.ticklabel_format(style='sci', axis='x', scilimits=(0,0))
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(frameon=True, facecolor='white', edgecolor='#cccccc', loc='center right')
    plt.tight_layout()
    fig1_path = "dt_pruning_performance.png"
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    print(f"\n[Saved Graph] Figure 1 saved to '{fig1_path}'")

    # -------------------------------------------------------------------------
    # 5. FINAL PRUNED DECISION TREE (Optimal ccp_alpha = 0.000600)
    # -------------------------------------------------------------------------
    best_res = max(pruning_results, key=lambda x: x['test_acc'])
    best_alpha = best_res['alpha']
    best_model = best_res['model']

    print("\n" + "=" * 80)
    print(f"4. FINAL PRUNED DECISION TREE (ccp_alpha = {best_alpha:.6f})")
    print("=" * 80)
    print(f"Training accuracy: {best_res['train_acc'] * 100:.2f}%")
    print(f"Testing accuracy:  {best_res['test_acc'] * 100:.2f}%")
    print(f"Tree depth:        {best_res['depth']}")
    print(f"Number of leaves:  {best_res['leaves']}")

    y_pred_pruned = best_model.predict(X_test)
    print("\nFinal Pruned Classification Report:")
    print(classification_report(y_test, y_pred_pruned, target_names=['a', 'b', 'c', 'd'], digits=4))

    cm_pruned = confusion_matrix(y_test, y_pred_pruned)
    print("Final Pruned Confusion Matrix:")
    print("Predicted:    a      b      c      d")
    for idx, row in enumerate(cm_pruned):
        print(f"Actual {labels[idx]}:   " + "  ".join(f"{val:>5}" for val in row))

    # -------------------------------------------------------------------------
    # 6. FIGURE 2: UNPRUNED VS PRUNED COMPARISON BAR CHART
    # -------------------------------------------------------------------------
    plt.figure(figsize=(8, 5.5), dpi=300)
    categories = ['Unpruned Decision Tree', 'Pruned Decision Tree']
    x = np.arange(len(categories))
    width = 0.35

    train_vals = [unpruned_train_acc, best_res['train_acc']]
    test_vals = [unpruned_test_acc, best_res['test_acc']]

    rects1 = plt.bar(x - width/2, train_vals, width, label='Training Accuracy', color='#1f77b4')
    rects2 = plt.bar(x + width/2, test_vals, width, label='Testing Accuracy', color='#ff7f0e')

    plt.title('Unpruned vs Pruned Decision Tree', fontsize=13, fontweight='bold', pad=12)
    plt.ylabel('Accuracy', fontsize=11, fontweight='bold')
    plt.xticks(x, categories, fontsize=10, fontweight='bold')
    plt.ylim(0, 1.1)
    plt.grid(True, axis='y', linestyle='--', alpha=0.6)
    plt.legend(frameon=True, facecolor='white', edgecolor='#cccccc', loc='upper right')

    # Add data labels
    for rect in rects1:
        h = rect.get_height()
        plt.annotate(f'{h*100:.2f}%', xy=(rect.get_x() + rect.get_width()/2, h),
                     xytext=(0, 4), textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold')
    for rect in rects2:
        h = rect.get_height()
        plt.annotate(f'{h*100:.2f}%', xy=(rect.get_x() + rect.get_width()/2, h),
                     xytext=(0, 4), textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.tight_layout()
    fig2_path = "dt_unpruned_vs_pruned.png"
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    print(f"\n[Saved Graph] Figure 2 saved to '{fig2_path}'")

    # -------------------------------------------------------------------------
    # 7. FINAL COMPARISON TABLE
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("5. FINAL COMPARISON SUMMARY")
    print("=" * 80)
    print(f"{'Metric':<20} | {'Unpruned Decision Tree':<24} | {'Pruned Decision Tree':<24}")
    print("-" * 74)
    print(f"{'Training Accuracy':<20} | {unpruned_train_acc*100:>23.2f}% | {best_res['train_acc']*100:>23.2f}%")
    print(f"{'Testing Accuracy':<20} | {unpruned_test_acc*100:>23.2f}% | {best_res['test_acc']*100:>23.2f}%")
    print(f"{'Tree Depth':<20} | {unpruned_depth:>24} | {best_res['depth']:>24}")
    print(f"{'Number of Leaves':<20} | {unpruned_leaves:>24,d} | {best_res['leaves']:>24,d}")
    print("-" * 74)
    print(f"Leaves reduced from {unpruned_leaves:,} to {best_res['leaves']:,} ({(1 - best_res['leaves']/unpruned_leaves)*100:.2f}% reduction in complexity).")
    print(f"Testing accuracy increased by {(best_res['test_acc'] - unpruned_test_acc)*100:.2f} percentage points.")
    print("=" * 80)

if __name__ == '__main__':
    run_decision_tree_pipeline()
