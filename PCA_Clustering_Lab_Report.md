# Title: Principal Component Analysis (PCA) and K-Means Clustering

**Course:** Research Design and Data Analysis (BDA402-7N)  
**Topic:** LAB 8: PRINCIPAL COMPONENT ANALYSIS (PCA) & CLUSTERING  
**Dataset:** Electric Vehicle (EV) Trip Energy Consumption Dataset  

---

## 2. Aim
To implement **Principal Component Analysis (PCA)** for unsupervised dimensionality reduction on the multidimensional **Electric Vehicle (EV) Trip Energy Consumption dataset**, project high-dimensional telemetry into orthogonal principal components ($PC_1$ and $PC_2$), analyze the **explained variance ratio**, perform **K-Means clustering ($K=3$)** in the lower-dimensional latent space, and evaluate the spatial separation, clustering quality, and physical domain interpretations of the resulting EV driving clusters.

---

## 3. Dataset Description
The experiment utilizes the processed **Electric Vehicle Trip Energy Consumption Dataset**, capturing trip-level kinematics, electrical characteristics, and energy consumption metrics across real-world driving interactions.

### Summary Statistics:
- **Total Records:** 10,151 unique trip observations
- **Missing Values:** 0 missing values
- **Features Analyzed:** 6 key operational and electrical attributes:
  1. `Trip Distance` (km)
  2. `Trip Time Length` (minutes)
  3. `Speed` (km/h)
  4. `Current` (A)
  5. `Total Voltage` (V)
  6. `Trip Energy Consumption` (kWh)

---

## 4. Mathematical Foundations

### 4.1 Feature Standardization
Because PCA seeks directions of maximum variance in the data, attributes with larger measurement scales or higher intrinsic variances (e.g., `Speed` in km/h vs. `Trip Energy Consumption` in kWh) would disproportionately dominate the eigenvectors.  
Standardization is performed using **Z-score normalization**:
$$z_j = \frac{x_j - \mu_j}{\sigma_j}$$
ensuring that every feature possesses zero mean ($\mu = 0$) and unit variance ($\sigma^2 = 1$).

### 4.2 Covariance Matrix & Eigen-Decomposition
For a standardized data matrix $\mathbf{X} \in \mathbb{R}^{n \times p}$ with $n=10,151$ samples and $p=6$ features, the sample covariance matrix $\mathbf{\Sigma}$ is given by:
$$\mathbf{\Sigma} = \frac{1}{n-1} \mathbf{X}^T \mathbf{X}$$

Eigen-decomposition resolves $\mathbf{\Sigma}$ into eigenvalues $\lambda_i$ and corresponding orthogonal eigenvectors $\mathbf{v}_i$:
$$\mathbf{\Sigma} \mathbf{v}_i = \lambda_i \mathbf{v}_i \quad \text{for } i \in \{1, 2, \dots, p\}$$

Sorted in descending order of explained variance:
$$\lambda_1 \ge \lambda_2 \ge \dots \ge \lambda_p \ge 0$$

### 4.3 Explained Variance Ratio
The proportion of total sample variance accounted for by the $k$-th principal component is:
$$\text{EVR}_k = \frac{\lambda_k}{\sum_{j=1}^{p} \lambda_j}$$

The cumulative explained variance retained by the 2-component projection ($PC_1, PC_2$) is:
$$\text{Cumulative EVR} = \text{EVR}_1 + \text{EVR}_2$$

### 4.4 K-Means Clustering in Latent Space
K-Means partitions the 2D projected coordinates $\mathbf{Z} = \mathbf{X} \mathbf{V}_2 \in \mathbb{R}^{n \times 2}$ into $K=3$ disjoint clusters by minimizing the within-cluster sum of squares (Inertia):
$$\text{Inertia} = \sum_{j=1}^{K} \sum_{\mathbf{z} \in C_j} \|\mathbf{z} - \boldsymbol{\mu}_j\|^2$$

---

## 5. Experimental Results

### 5.1 PCA Explained Variance Ratio
Applying PCA to the 6 standardized telemetry features yields:

| Principal Component | Eigenvalue ($\lambda_i$) | Explained Variance Ratio | Cumulative Variance |
| :---: | :---: | :---: | :---: |
| **$PC_1$** | **2.062** | **34.37% (0.3437)** | **34.37%** |
| **$PC_2$** | **1.979** | **32.98% (0.3298)** | **67.36%** |

> **Finding:** The first two principal components jointly capture **67.36%** of the total variance across all 6 physical dimensions, providing a highly representative low-dimensional compression of the EV driving dynamics.

---

### 5.2 Component Loadings (Feature Contributions)
The component loading matrix $\mathbf{V}_2$ details the linear combination of original features defining each axis:

| Feature | $PC_1$ Loading | $PC_2$ Loading | Dominant Physical Interpretation |
| :--- | :---: | :---: | :--- |
| `Trip Distance` | **+0.6625** | +0.0047 | Primary driver of $PC_1$ (Distance scale) |
| `Trip Energy Consumption` | **+0.6671** | +0.0427 | Primary driver of $PC_1$ (Energy expenditure) |
| `Trip Time Length` | +0.3030 | -0.4279 | Secondary driver across both components |
| `Speed` | +0.0171 | **+0.6123** | Primary driver of $PC_2$ (Kinetic velocity) |
| `Current` | +0.0977 | **+0.6260** | Primary driver of $PC_2$ (Dynamic electrical load) |
| `Total Voltage` | -0.1202 | -0.2197 | Minor inverse load relationship |

#### Interpretative Takeaway:
- **Axis 1 ($PC_1$ - "Trip Magnitude & Energy Expended"):** Heavily aligned with `Trip Distance` ($+0.6625$) and `Trip Energy Consumption` ($+0.6671$). Positive values denote long, energy-intensive journeys.
- **Axis 2 ($PC_2$ - "Dynamic Driving Intensity & Power Draw"):** Heavily aligned with `Speed` ($+0.6123$) and `Current` ($+0.6260$). Positive values represent aggressive, high-speed, high-amperage acceleration sessions.

---

## 6. Graphs & Visualizations

### 6.1 Figure 1: PCA Explained Variance
![Figure 1: PCA Explained Variance](pca_explained_variance.png)

#### Graph Analysis:
- The bar chart clearly depicts the variance distribution across the two principal components.
- $PC_1$ captures **34.37%** of the system variance, while $PC_2$ accounts for **32.98%**.
- The nearly balanced variance distribution indicates that spatial trip extent ($PC_1$) and kinematic driving aggressiveness ($PC_2$) are two distinct, orthogonal dimensions of electric vehicle operation.

---

### 6.2 Figure 2: K-Means Clusters Visualized Using PCA
![Figure 2: K-Means Clusters Visualized Using PCA](kmeans_pca_clusters.png)

#### Graph Analysis:
- The 10,151 electric vehicle trips are projected into the orthogonal $PC_1 - PC_2$ feature plane and colored by their assigned cluster ($K=3$, `viridis` palette).
- The three clusters partition the latent space into cohesive, continuous operational regimes:
  - **Cluster 0 (Purple / Dark Violet):** Extends along positive $PC_1$, capturing high-magnitude, long-distance trips.
  - **Cluster 1 (Teal / Blue-Green):** Occupies positive $PC_2$, isolating high-speed, high-current operating cycles.
  - **Cluster 2 (Yellow):** Concentrated in the negative quadrant ($PC_1 < 0, PC_2 < 0$), representing low-distance, low-speed congested urban driving.
- White crosses with black outlines ($\mathbf{X}$) mark the calculated cluster centroids in latent space.

---

### 6.3 Figure 3: Combined PCA & Clustering Overview
![Figure 3: Combined Report Overview](pca_clustering_combined_report.png)

---

## 7. Quantitative Cluster Profiles & Physical Domain Analysis

Profiling the original physical metrics grouped by the $K=3$ latent clusters:

| Cluster | Trip Count ($n$) | Share (%) | Mean Distance (km) | Mean Duration (min) | Mean Speed (km/h) | Mean Current (A) | Mean Energy (kWh) | Physical Driving Regime |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **0** | 2,115 | 20.84% | **$36.63 \pm 8.21$** | $55.42 \pm 12.87$ | $44.18 \pm 33.12$ | $5.12 \pm 6.84$ | **$8.17 \pm 2.82$** | **Long-Distance / Heavy Energy Transit** |
| **1** | 2,251 | 22.18% | $15.63 \pm 8.82$ | $13.41 \pm 6.19$ | **$124.72 \pm 24.19$** | **$16.48 \pm 8.92$** | $3.52 \pm 2.08$ | **High-Speed Express / High-Power Driving** |
| **2** | 5,785 | 56.99% | $12.45 \pm 5.92$ | $51.08 \pm 14.93$ | $19.24 \pm 21.05$ | $3.29 \pm 4.18$ | $2.58 \pm 1.49$ | **Congested Urban Commute / Low Power** |

### Evaluation Metrics:
- **K-Means Inertia (SSE):** $15,058.45$
- **Silhouette Score:** **$0.4486$** (indicates strong cluster compactness and separation in the 2D projected space)

---

## 8. Outlier Sensitivity Note: Cleaned vs. Uncleaned Data
In uncurated sensor telemetry (as observed in initial raw acquisitions), measurement errors—such as erroneous negative latitude readings (e.g., $-645^\circ$)—can artificially inflate raw variance. When PCA is applied without standard outlier treatment, extreme outliers skew eigenvectors and compress 99.9% of normal records into a microscopic corner.  
Applying systematic IQR Winsorization and Z-score standardization completely resolves this distortion, allowing PCA to faithfully uncover the intrinsic geometry of real EV operations.

---

## 9. Observations & Key Insights
1. **Effective Dimensionality Reduction:** Reducing 6 correlated telemetry attributes to 2 orthogonal components preserved **67.36%** of total system variance.
2. **Clear Orthogonal Latent Dimensions:** $PC_1$ represents trip spatial scale and energy consumption, while $PC_2$ represents kinematic velocity and instantaneous electrical draw.
3. **Clustering Efficiency in Latent Space:** Performing K-Means directly on the 2D principal plane achieved a high **Silhouette Score of 0.4486**, with clear visual separation.
4. **Dominant Urban Commute Segment:** Over **56.99%** of all recorded trips belong to Cluster 2 (congested urban stop-and-go driving with low average speed of $19.24\text{ km/h}$).
5. **Express Driving Isolation:** Cluster 1 ($22.18\%$) cleanly isolates high-speed express journeys ($124.72\text{ km/h}$) requiring high current draws ($16.48\text{ A}$).
6. **Heavy Energy Segment:** Cluster 0 ($20.84\%$) captures long journeys ($36.63\text{ km}$) consuming more than triple the energy ($8.17\text{ kWh}$) of short city trips ($2.58\text{ kWh}$).
7. **Actionable Insights for EV Control:** The resulting 2D cluster map provides clear decision boundaries for on-board Battery Management Systems (BMS) to adapt cooling strategies and state-of-charge predictions in real time.

---

## 10. Conclusion
Principal Component Analysis (PCA) and K-Means clustering were successfully executed on the Electric Vehicle Trip Energy Consumption dataset. The first two principal components retained **67.36%** of total variance, reducing complexity while preserving essential physical relationships. K-Means clustering with $K=3$ in the PC1–PC2 coordinate space yielded a **Silhouette Score of 0.4486**, successfully segregating vehicle trips into Congested Urban, High-Speed Express, and Long-Distance Heavy Energy profiles.
