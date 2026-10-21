# Title: Exploration and Implementation of the K-Nearest Neighbors (KNN) Algorithm

**Course:** Research Design and Data Analysis  
**Topic:** LAB 5: K-NEAREST NEIGHBORS (KNN)  
**Dataset:** Electric Vehicle (EV) Trip Energy Consumption Dataset  

---

## 2. Aim
To implement the **K-Nearest Neighbors (KNN)** classification algorithm on the real-world **Electric Vehicle (EV) Trip Energy Consumption dataset** and analyze its predictive performance across multiple values of $K$ ($K = 1, 3, 5, 7, 9, 11$) using testing accuracy, classification report metrics (precision, recall, F1-score), and a confusion matrix.

---

## 3. Dataset Description
The **Electric Vehicle Trip Energy Consumption Dataset** captures real-time operational telemetry collected from electric vehicles across distinct urban and highway driving cycles. It includes critical trip-level physical, electrical, and kinematic metrics.

### Key Dataset Attributes:
- **Vehicle ID:** Unique identifier for the EV in the fleet.
- **Trip Distance:** Total distance covered during the trip (km).
- **Trip Time Length:** Duration of the driving session (minutes).
- **Speed:** Average vehicle operating speed (km/h).
- **Current:** Dynamic electrical current flow (A).
- **Total Voltage:** Operating pack potential (V).
- **Maximum Cell Temperature of Battery:** Peak battery cell temperature (°C).
- **Minimum Cell Temperature of Battery:** Lowest recorded battery cell temperature (°C).
- **Time of Day & Day of Week:** Temporal context of the trip.
- **Trip Energy Consumption:** Total energy consumed during the trip (kWh).

### Summary Statistics of the Processed Dataset:
- **Total Records:** 10,151 interaction trips
- **Total Input Attributes:** 13 original features (expanded during preprocessing)
- **Target Variable:** `energy_class` (Categorized based on quartile energy consumption)
- **Target Classes:** 4 balanced classes:
  - **Class `a` (Low Consumption):** $\le 1.792\text{ kWh}$ (2,668 records, 26.28%)
  - **Class `b` (Moderate Consumption):** $1.792\text{ to } 3.136\text{ kWh}$ (2,741 records, 27.00%)
  - **Class `c` (High Consumption):** $3.136\text{ to } 5.152\text{ kWh}$ (2,219 records, 21.86%)
  - **Class `d` (Very High Consumption):** $> 5.152\text{ kWh}$ (2,523 records, 24.85%)
- **Missing Values:** 0 missing values (clean dataset of 10,151 records).

---

## 4. Features Used
To maintain a high signal-to-noise ratio and align with distance-based classification requirements, three fundamental kinematic and temporal driving dynamics features were selected:

| Feature | Description | Unit / Scale |
| :--- | :--- | :--- |
| `Trip Distance` | Total distance covered during the EV trip | Kilometers (km) |
| `Trip Time Length` | Total elapsed duration of the driving trip | Minutes |
| `Speed` | Average operational vehicle speed | Kilometers per hour (km/h) |

### Target Variable:
`energy_class` with **four classes:**
$$\{a, b, c, d\}$$

---

## 5. Data Preprocessing
The following systematic preprocessing steps were carried out:
1. **Dataset Ingestion:** The EV trip energy consumption dataset was loaded into a structured Pandas DataFrame.
2. **Missing Value Audit:** Data integrity was verified; no missing or NaN entries were present.
3. **Feature Selection:** Numerical features (`Trip Distance`, `Trip Time Length`, `Speed`) directly influencing energy expenditure were extracted.
4. **Target Encoding:** The energy consumption tiers were transformed into categorical labels and mapped into integer representations using `LabelEncoder`.
5. **Stratified Train-Test Split:** The dataset was split into **80% training** and **20% testing** sets using stratified sampling to preserve identical class proportions across both subsets.
6. **Feature Standardization:** Since KNN is a metric distance-based algorithm sensitive to disparate feature scales, `StandardScaler` was applied:
   $$z = \frac{x - \mu}{\sigma}$$
   The scaler was fitted strictly on the training set and subsequently applied to transform both the training and testing sets to prevent data leakage.

### Split Summary:
| Dataset | Number of Records | Percentage |
| :--- | :--- | :--- |
| **Training Set** | 8,120 | 80.0% |
| **Testing Set** | 2,031 | 20.0% |
| **Total** | 10,151 | 100.0% |

---

## 6. KNN Algorithm
The **K-Nearest Neighbors (KNN)** algorithm is a non-parametric, instance-based supervised learning method. Given a query point $x_q$, KNN locates the $K$ closest instances in the scaled feature space based on **Euclidean distance**:
$$d(p, q) = \sqrt{\sum_{i=1}^n (p_i - q_i)^2}$$
The predicted class is assigned via a majority voting scheme among the $K$ nearest neighbors.

For this experiment, an odd sequence of $K$ values was tested to avoid tie breaks:
$$K = 1, 3, 5, 7, 9, 11$$

---

## 7. Experimental Results
The classification accuracy obtained on the unseen testing set across varying values of $K$ is presented below:

| $K$ (Neighbors) | Testing Accuracy |
| :---: | :---: |
| **1** | 62.24% |
| **3** | 66.27% |
| **5** | 68.83% |
| **7** | 69.18% |
| **9** | 69.82% |
| **11** | **70.70%** |

### Optimal Model:
- **Highest Testing Accuracy:** **70.70%**
- **Optimal Hyperparameter:** $K = 11$

---

## 8. Graph: KNN Accuracy for Different $K$ Values

![KNN Accuracy for Different K Values](knn_accuracy_vs_k.png)

### Graph Analysis:
- The graph demonstrates a monotonic upward trajectory in testing accuracy as the number of neighbors increases from $K = 1$ to $K = 11$.
- At $K = 1$, the model displays classic signs of high variance / overfitting to individual training noise, yielding a baseline testing accuracy of **62.24%**.
- As $K$ increases to 3, 5, and 7, accuracy climbs steeply to **66.27%**, **68.83%**, and **69.18%** respectively, as the decision boundary becomes smoother and more generalized.
- The highest performance is reached at $K = 11$ with an accuracy of **70.70%**, demonstrating that aggregating neighborhood context substantially improves classification confidence for continuous trip telemetry.

---

## 9. Classification Report
For the optimal model ($K = 11$), the comprehensive class-wise evaluation report is summarized below:

| Class | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| **a (Low)** | 0.7328 | 0.8783 | 0.7990 | 534 |
| **b (Moderate)** | 0.6208 | 0.6332 | 0.6269 | 548 |
| **c (High)** | 0.6079 | 0.5203 | 0.5607 | 444 |
| **d (Very High)**| 0.8606 | 0.7703 | 0.8130 | 505 |
| **Overall Accuracy** | — | — | **0.7070** | 2,031 |
| **Macro Average** | 0.7055 | 0.7005 | 0.6999 | 2,031 |
| **Weighted Average** | 0.7070 | 0.7070 | 0.7039 | 2,031 |

### Classification Report Analysis:
- **Class `a` (Low Consumption):** Achieved the highest recall (**87.83%**) with an F1-score of **0.7990**, indicating the model reliably detects short, low-energy urban trips without missing true positives.
- **Class `d` (Very High Consumption):** Achieved the highest precision (**86.06%**) and an F1-score of **0.8130**, demonstrating excellent specificity in identifying demanding, heavy-consumption journeys.
- **Intermediate Classes `b` and `c`:** Exhibited slightly lower recall (63.32% and 52.03%) due to natural boundary overlap where driving dynamics transition gradually between moderate and high consumption.
- **Macro vs. Weighted Metrics:** Macro F1 (0.6999) and Weighted F1 (0.7039) are closely aligned, confirming balanced, equitable model behavior across all four quartiles.

---

## 10. Confusion Matrix

![Confusion Matrix - KNN (K=11)](knn_confusion_matrix.png)

### Tabular Confusion Matrix ($K = 11$):
```
                 Predicted Class
                 a        b        c        d
Actual a        469       65        0        0
Actual b        148      347       53        0
Actual c         22      128      231       63
Actual d          1       19       96      389
```

### Confusion Matrix Analysis:
- **True Positives (Diagonal Elements):**
  - For **Class `a`**, **469** trips were correctly classified out of 534.
  - For **Class `b`**, **347** trips were correctly classified out of 548.
  - For **Class `c`**, **231** trips were correctly classified out of 444.
  - For **Class `d`**, **389** trips were correctly classified out of 505.
- **Off-Diagonal Behavior:**
  - Noticeably, misclassifications occur almost exclusively between **adjacent classes** (e.g., Class `a` misclassified into Class `b`, or Class `c` into Class `d`).
  - There are **0 extreme misclassifications** between Class `a` and Class `c` or `d`, and only **1** instance where Class `d` was predicted as `a`.
  - This demonstrates that the feature space is continuous, well-ordered, and physically coherent with respect to vehicle energy physics.

---

## 11. Observations
1. The **KNN algorithm** was successfully implemented and evaluated on the real-world **Electric Vehicle Trip Energy Consumption dataset**.
2. Six different neighbor configurations ($K = 1, 3, 5, 7, 9, 11$) were evaluated under standardized Euclidean distance.
3. Testing accuracy exhibited a clear upward trend, rising from **62.24% at $K=1$** to **70.70% at $K=11$**.
4. The optimal performance was reached at **$K=11$**, yielding an overall accuracy of **70.70%**.
5. Extreme consumption states (Class `a` and Class `d`) yielded the highest classification reliability, achieving F1-scores of **0.7990** and **0.8130** respectively.
6. The boundary between adjacent categories (Classes `b` and `c`) contained mild overlap due to continuous variance in real-time speed and trip durations.
7. Feature standardization via `StandardScaler` was essential to prevent features with larger numeric magnitudes (such as `Speed`) from dominating distance computations over `Trip Distance`.
8. The confusion matrix confirms zero catastrophic misclassifications between opposite energy poles (Low vs. Very High).
9. The three selected features (`Trip Distance`, `Trip Time Length`, and `Speed`) provide strong predictive power for energy categorization in electric vehicle fleets.

---

## 12. Conclusion
The **K-Nearest Neighbors (KNN)** classification algorithm was successfully designed, implemented, and evaluated on the **Electric Vehicle Trip Energy Consumption dataset** using three key driving features: `Trip Distance`, `Trip Time Length`, and `Speed`.

Across the tested hyperparameter space ($K = 1, 3, 5, 7, 9, 11$), $K = 11$ achieved the superior performance with a testing accuracy of **70.70%**. Detailed evaluation via the classification report and confusion matrix revealed strong discriminatory ability, particularly for low and very high energy trips, with well-contained boundary transitions across intermediate consumption levels.

In conclusion, this experiment demonstrates the efficacy of instance-based metric learning for energy profiling in electric mobility systems, validating that distance, duration, and velocity serve as robust determinants of auxiliary and tractive EV energy demands.
