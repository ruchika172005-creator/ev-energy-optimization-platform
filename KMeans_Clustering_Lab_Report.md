# Title: Exploration of K-Means Clustering and Optimal K Selection

**Course:** Research Design and Data Analysis (BDA402-7N)  
**Topic:** LAB 7: K-MEANS CLUSTERING AND OPTIMAL K SELECTION  
**Dataset:** Electric Vehicle (EV) Trip Energy Consumption Dataset  

---

## 2. Aim
To implement the **unsupervised K-Means clustering algorithm** on the real-world **Electric Vehicle (EV) Trip Energy Consumption dataset**, systematically explore clustering behavior across multiple cluster configurations ($K = 2 \text{ to } 10$), determine the optimal number of clusters using the **Elbow Method (Inertia / Within-Cluster Sum of Squares)** and **Silhouette Score Analysis**, and analyze the resulting operational driving profiles and energy consumption patterns.

---

## 3. Dataset Description
The **Electric Vehicle Trip Energy Consumption Dataset** captures telemetry gathered during real-world electric vehicle operations across dynamic urban, suburban, and arterial driving scenarios. Maintaining experimental consistency with the previous laboratories (KNN Exploration and Decision Tree Pruning), the cleaned telemetry dataset was utilized.

### Key Dataset Attributes:
- **Total Records:** 10,151 interaction trips
- **Total Features:** 20 preprocessed attributes (including physical, kinematic, and electrical features)
- **Missing Values:** 0 missing values (complete data integrity across all 10,151 rows)

### Primary Operational Variables:
- `Trip Distance`: Total spatial distance traversed during the trip (km)
- `Trip Time Length`: Total trip duration (minutes)
- `Speed`: Average operating velocity of the electric vehicle (km/h)
- `Current`: Operating electrical current draw from the traction battery pack (A)
- `Total Voltage`: Terminal battery voltage (V)
- `Maximum / Minimum Cell Temperature`: Peak and base battery cell thermal states (°C)
- `Trip Energy Consumption`: Net electric energy expended during the driving cycle (kWh)

---

## 4. Features Selected for Clustering
To cluster EV driving behaviors into meaningful operational trip profiles, three fundamental kinematic and temporal driving dynamics features were selected:

| Feature | Description | Measurement Unit | Domain Significance |
| :--- | :--- | :--- | :--- |
| `Trip Distance` | Cumulative distance covered per trip | Kilometers ($\text{km}$) | Distinguishes short intra-city trips from long-distance arterial transits. |
| `Trip Time Length` | Total elapsed driving session duration | Minutes ($\text{min}$) | Reflects traffic congestion, idling, and route duration. |
| `Speed` | Average operational vehicle velocity | Kilometers per hour ($\text{km/h}$) | Characterizes stop-and-go city cycles vs. free-flowing highway cruising. |

---

## 5. Data Preprocessing & Feature Standardization
Because K-Means is a distance-based clustering algorithm that relies directly on Euclidean distance calculations, differences in feature scales can bias cluster assignments toward features with larger numerical magnitudes (e.g., speed and duration dominating distance).

1. **Missing Value Audit:** Confirmed zero null or unrecorded values across the 10,151 rows.
2. **Feature Standardization (`StandardScaler`):** Features were transformed using standard z-score normalization:
   $$z = \frac{x - \mu}{\sigma}$$
   where $\mu$ is the empirical feature mean and $\sigma$ is the standard deviation. This maps every feature to zero mean ($\mu = 0$) and unit variance ($\sigma^2 = 1$), ensuring equal weighting across kinematic dimensions.

---

## 6. K-Means Algorithm Fundamentals & Optimal K Selection Criteria

### 6.1 K-Means Objective Function (Inertia / WCSS)
K-Means partitions $n$ samples into $K$ disjoint clusters $C = \{C_1, C_2, \dots, C_K\}$, minimizing the **Within-Cluster Sum of Squares (Inertia / SSE)**:
$$\text{Inertia} = \sum_{j=1}^{K} \sum_{x \in C_j} \| x - \mu_j \|^2$$
where $\mu_j$ represents the centroid (mean vector) of cluster $C_j$.

### 6.2 The Elbow Method
As $K$ increases, inertia monotonically decreases because clusters become smaller and centroids move closer to individual samples. The **Elbow Method** identifies the inflection point (the "elbow") where adding further clusters yields diminishing returns in inertia reduction:
$$\Delta \text{Inertia}(K) = \text{Inertia}(K-1) - \text{Inertia}(K)$$

### 6.3 Silhouette Score Analysis
The **Silhouette Coefficient** measures both cohesion (how close a point is to points in its own cluster) and separation (how far a point is from points in neighboring clusters):
$$s(i) = \frac{b(i) - a(i)}{\max(a(i), b(i))}$$
where:
- $a(i)$ is the mean intra-cluster distance of sample $i$ to all other points in the same cluster.
- $b(i)$ is the mean nearest-cluster distance of sample $i$ to points in the closest distinct cluster.
- $s(i) \in [-1, +1]$: Values closer to $+1$ indicate dense, well-separated clusters; values near $0$ represent overlapping cluster boundaries; negative values denote misclassified points.

---

## 7. Experimental Results: Metric Evaluation Across K = 2 to 10

The K-Means clustering pipeline was evaluated for all cluster counts from $K = 2$ to $K = 10$ ($n\_init=10$, random state fixed to 42 for complete reproducibility):

| Number of Clusters ($K$) | Inertia ($\text{SSE}$) | Inertia Reduction ($\Delta \text{Inertia}$) | Silhouette Score | Evaluation Notes |
| :---: | :---: | :---: | :---: | :--- |
| **2** | 20,479.35 | — | 0.330 | Under-segmented: collapses distinct driving styles |
| **3** | 14,790.83 | -5,688.52 | 0.348 | Substantial inertia reduction; moderate separation |
| **4** | **9,946.76** | **-4,844.07** | **0.406** | **Pronounced Elbow Point; sharp silhouette leap** |
| **5** | **8,255.84** | -1,690.92 | **0.410** | **Peak Silhouette Score; inertia drop flattens** |
| **6** | 7,203.66 | -1,052.18 | 0.409 | Diminishing returns in variance reduction |
| **7** | 6,380.72 | -822.94 | 0.382 | Separation deteriorates; over-fragmentation begins |
| **8** | 5,687.51 | -693.21 | 0.360 | Further decline in silhouette coefficient |
| **9** | 5,176.59 | -510.92 | 0.342 | Lowest silhouette score in upper range |
| **10** | 4,662.21 | -514.38 | 0.356 | Excessive cluster fragmentation |

---

## 8. Graphs: Optimal K Selection Visualizations

### 8.1 Figure 1: Elbow Method (Inertia vs. Number of Clusters K)
![Figure 1: Elbow Method](kmeans_elbow_method.png)

#### Graph Analysis:
- The inertia drops precipitously from $K=2$ ($20,479.35$) to $K=3$ ($14,790.83$, $\Delta = -5,688.52$) and continuously down to $K=4$ ($9,946.76$, $\Delta = -4,844.07$).
- From $K=4$ to $K=5$, the rate of inertia reduction drops abruptly to only $-1,690.92$, and flattens further beyond $K=5$ ($-1,052.18$ for $K=6$, $-822.94$ for $K=7$).
- This produces a distinct **Elbow Point at $K=4$**, signifying that 4 clusters capture the bulk of data variance without excessive model complexity.

---

### 8.2 Figure 2: Silhouette Scores (Silhouette Score vs. Number of Clusters K)
![Figure 2: Silhouette Scores](kmeans_silhouette_scores.png)

#### Graph Analysis:
- For $K=2$ and $K=3$, the silhouette scores remain modest at $0.330$ and $0.348$, indicating ambiguous cluster boundaries and poor internal cohesion.
- At **$K=4$**, the silhouette score exhibits a sharp, dramatic upward inflection to **$0.406$** (+0.058 jump), followed by its peak at **$K=5$ ($0.410$)**.
- Beyond $K=6$, the silhouette score plunges monotonically to $0.382$ ($K=7$), $0.360$ ($K=8$), and $0.342$ ($K=9$).
- Both the Elbow Method and Silhouette Analysis converge strongly on **$K = 4$** (and $K = 5$) as the mathematically optimal cluster configuration.

---

### 8.3 Figure 3: Combined Optimal K Selection (Dual-Panel Evaluation)
![Figure 3: Combined Optimal K Selection](kmeans_optimal_k_selection.png)

The dual-panel visual confirms the simultaneous intersection of the elbow curvature knee and the silhouette score plateau at $K=4$. Moreover, selecting **$K = 4$** establishes direct theoretical continuity with the **4 balanced energy consumption quartile classes ($a, b, c, d$)** established in the preceding KNN and Decision Tree laboratory investigations.

---

## 9. Final Optimal Model Profiling ($K = 4$)

Fitting the final K-Means model with $K = 4$ partitions the 10,151 EV trips into four distinct operational driving regimes:

| Cluster | Trip Count ($n$) | Share (%) | Mean Distance (km) | Mean Duration (min) | Mean Speed (km/h) | Mean Energy Consumption (kWh) | Assigned Operational Driving Profile |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **0** | 2,656 | 26.16% | $13.69 \pm 6.40$ | $26.12 \pm 9.42$ | $35.48 \pm 20.29$ | $3.03 \pm 1.66$ | **Moderate Urban Commute** |
| **1** | 1,622 | 15.98% | $15.73 \pm 9.05$ | $11.23 \pm 5.17$ | $135.53 \pm 22.91$ | $3.33 \pm 2.14$ | **High-Speed Express / Highway Sprint** |
| **2** | 1,814 | 17.87% | $38.94 \pm 7.76$ | $58.10 \pm 12.35$ | $42.50 \pm 35.06$ | $8.35 \pm 2.79$ | **Long-Distance / Heavy Transit Trip** |
| **3** | 4,059 | 39.99% | $12.85 \pm 6.19$ | $54.21 \pm 15.68$ | $16.89 \pm 22.96$ | $2.84 \pm 1.57$ | **Congested City Stop-and-Go Driving** |

---

## 10. Figure 4: Cluster Space Visualization and Centroids

![Figure 4: Cluster Space Visualization](kmeans_clusters_visualization.png)

### Visual Analysis:
1. **Trip Distance vs. Speed:**
   - **Cluster 1 (Orange):** Forms a distinct high-velocity cluster centered at an average speed of $135.53\text{ km/h}$, representing high-speed arterial and express driving.
   - **Cluster 3 (Pink):** Represents congested, slow urban driving with low average speeds ($16.89\text{ km/h}$) and high trip durations.
   - **Cluster 0 (Green):** Occupies the intermediate speed band ($35.48\text{ km/h}$), characterizing steady suburban flow.
   - **Cluster 2 (Purple):** Clearly separates along the horizontal axis, capturing extended trips exceeding $30\text{ km}$ (mean $38.94\text{ km}$).
   - The black cross markers ($\mathbf{X}$) mark the calculated cluster centroids in original physical units.

2. **Trip Distance vs. Energy Consumption:**
   - Short and moderate urban trips (Clusters 0, 1, and 3) exhibit modest energy demand ($2.84\text{ to } 3.33\text{ kWh}$).
   - In stark contrast, Long-Distance Transit (Cluster 2) exhibits heavily elevated energy depletion (mean $8.35\text{ kWh}$, reaching up to $20.8\text{ kWh}$), demonstrating the strong direct physical coupling between cumulative distance, trip duration, and EV traction battery energy draw.

---

## 11. Key Observations & Findings
1. **Unsupervised Grouping Capability:** K-Means successfully extracted meaningful, well-separated driving and energy profiles from the unlabeled EV telemetry dataset without requiring supervisory target labels.
2. **Feature Standardization Necessity:** Transforming `Trip Distance`, `Trip Time Length`, and `Speed` using `StandardScaler` prevented feature scale dominance and ensured spherical cluster formation in normalized Euclidean space.
3. **Elbow Method Efficacy:** Inertia decreased steeply from $20,479.35$ ($K=2$) down to $9,946.76$ ($K=4$). Beyond $K=4$, the rate of decrease curtailed drastically, establishing $K=4$ as the natural elbow inflection point.
4. **Silhouette Score Confirmation:** The silhouette score achieved a major positive leap from $0.348$ ($K=3$) to $0.406$ ($K=4$), reaching its global peak at $K=5$ ($0.410$).
5. **Cross-Laboratory Consistency:** The mathematical convergence on $K=4$ directly substantiates the 4 energy consumption quartile classes ($a, b, c, d$) formulated in the KNN and Decision Tree laboratories.
6. **Identification of Express Driving:** Cluster 1 ($n=1,622$, 15.98%) isolates high-velocity driving trips with an average speed of $135.53\text{ km/h}$ and rapid trip completion ($11.23\text{ min}$).
7. **Traffic Congestion Separation:** Cluster 3 represents the largest segment ($n=4,059$, 39.99%), characterized by protracted durations ($54.21\text{ min}$) and low operational speeds ($16.89\text{ km/h}$), reflecting heavy urban congestion.
8. **Heavy Energy Consumers Isolated:** Cluster 2 ($n=1,814$) cleanly encapsulates high-distance ($38.94\text{ km}$) and high-energy ($8.35\text{ kWh}$) journeys, providing critical segmentation for EV battery thermal management.
9. **Cluster Centroid Interpretability:** Centroids transformed back to original physical engineering units provide actionable thresholds for on-board EV energy management controllers.
10. **Dimensional Separability:** The 2D scatter plots demonstrate robust spatial boundary demarcation across kinematic and energy dimensions.

---

## 12. Conclusion
The **K-Means clustering algorithm** and **Optimal K Selection analysis** were successfully implemented and evaluated on the **Electric Vehicle Trip Energy Consumption dataset**.

Using both the **Elbow Method** and **Silhouette Score Analysis**, $K = 4$ was identified as the optimal number of clusters, achieving an **Inertia of 9,946.76** and a **Silhouette Score of 0.406**. The 4 identified clusters accurately segmented 10,151 vehicle trips into four realistic operational profiles:
- **Congested City Driving** ($39.99\%$, $16.89\text{ km/h}$, $2.84\text{ kWh}$)
- **Moderate Urban Commute** ($26.16\%$, $35.48\text{ km/h}$, $3.03\text{ kWh}$)
- **High-Speed Express Transit** ($15.98\%$, $135.53\text{ km/h}$, $3.33\text{ kWh}$)
- **Long-Distance Heavy Transit** ($17.87\%$, $38.94\text{ km}$, $8.35\text{ kWh}$)

This unsupervised segmentation provides a robust empirical foundation for predictive energy modeling, dynamic range forecasting, and adaptive EV battery thermal regulation.
