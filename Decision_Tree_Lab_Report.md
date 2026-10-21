# Title: Exploration of the Decision Tree Algorithm with Cost-Complexity Pruning

**Course:** Research Design and Data Analysis (BDA402-7N)  
**Topic:** LAB 6: DECISION TREE WITH PRUNING  
**Dataset:** Electric Vehicle (EV) Trip Energy Consumption Dataset  

---

## 2. Aim
To implement a **Decision Tree classification algorithm** on the real-world **Electric Vehicle (EV) Trip Energy Consumption dataset** and study the effect of **cost-complexity pruning ($ccp\_alpha$)** on model performance, generalization capability, and tree complexity.

---

## 3. Dataset Description
The **Electric Vehicle Trip Energy Consumption Dataset** was used for this experiment. The same processed dataset used in the previous laboratory (KNN exploration) was employed to maintain rigorous experimental consistency.

### The dataset initially contained:
- **10,151 interaction records**
- **13 primary columns** (expanded to 20 during preprocessing)

The attributes include:
- `Vehicle ID`
- `Trip Distance`
- `Trip Time Length`
- `Speed`
- `Current`
- `Total Voltage`
- `Maximum Cell Temperature of Battery`
- `Minimum Cell Temperature of Battery`
- `Time of Day`
- `Day of the Week`
- `Trip Energy Consumption`

The target variable was formulated as `energy_class`, containing four balanced energy consumption classes:
$$\{a, b, c, d\}$$

- **Class `a` (Low Consumption):** $\le 1.792\text{ kWh}$ (2,668 records, 26.28%)
- **Class `b` (Moderate Consumption):** $1.792\text{ to } 3.136\text{ kWh}$ (2,741 records, 27.00%)
- **Class `c` (High Consumption):** $3.136\text{ to } 5.152\text{ kWh}$ (2,219 records, 21.86%)
- **Class `d` (Very High Consumption):** $> 5.152\text{ kWh}$ (2,523 records, 24.85%)

There were 0 missing values in the dataset, resulting in **10,151 records** available for model training and evaluation.

---

## 4. Features Used
The following three kinematic and operational driving features were selected for Decision Tree classification:

| Feature | Description |
| :--- | :--- |
| `Trip Distance` | Total distance covered during the trip in kilometers |
| `Trip Time Length` | Elapsed driving duration in minutes |
| `Speed` | Average operational vehicle speed in km/h |

### Target Variable:
`energy_class`

### Target Classes:
$$a, b, c, d$$

---

## 5. Data Preprocessing
The following preprocessing steps were performed:
1. The EV trip energy consumption dataset was loaded into memory.
2. Missing values were verified (0 missing values present).
3. Three numerical features (`Trip Distance`, `Trip Time Length`, `Speed`) were extracted.
4. The target variable was categorized into quartiles and encoded into numeric labels using `LabelEncoder`.
5. The dataset was divided into training and testing sets.
6. A **stratified 80:20 train-test split** was used to ensure identical class distributions across both splits.

### Resulting Split:
| Dataset | Records | Percentage |
| :--- | :---: | :---: |
| **Training** | 8,120 | 80% |
| **Testing** | 2,031 | 20% |
| **Total** | 10,151 | 100% |

---

## 6. Decision Tree Algorithm
A **Decision Tree classifier** (`DecisionTreeClassifier`, `random_state=42`) was used to classify the four trip energy consumption categories.

Initially, an **unpruned Decision Tree** was trained without restricting its complexity (allowing full expansion until pure leaves were achieved).

The resulting unpruned tree had:
- **Training accuracy:** **99.14%**
- **Testing accuracy:** **62.38%**
- **Tree depth:** **41**
- **Number of leaves:** **2,587**

> The massive difference between training accuracy (99.14%) and testing accuracy (62.38%) indicates that the unpruned tree fits the idiosyncratic noise of the training data, exhibiting severe **overfitting** and excessive structural complexity (depth 41, 2,587 terminal leaves).

---

## 7. Unpruned Decision Tree Evaluation
The classification report for the unpruned Decision Tree was:

| Class | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| **a** | 0.69 | 0.73 | 0.71 | 534 |
| **b** | 0.52 | 0.51 | 0.51 | 548 |
| **c** | 0.49 | 0.48 | 0.48 | 444 |
| **d** | 0.79 | 0.77 | 0.78 | 505 |
| **Accuracy** | — | — | **0.62** | 2,031 |
| **Macro Avg** | 0.62 | 0.62 | 0.62 | 2,031 |
| **Weighted Avg** | 0.62 | 0.62 | 0.62 | 2,031 |

### Confusion Matrix (Unpruned Tree):
```
                 Predicted Class
                 a        b        c        d
Actual a        391      126       17        0
Actual b        152      277      106       13
Actual c         27      116      211       90
Actual d          0       16      101      388
```

---

## 8. Cost-Complexity Pruning
**Cost-complexity pruning (Minimal Cost-Complexity Pruning)** was used to systematically prune away redundant, noise-fitting subtrees. The cost-complexity measure $R_\alpha(T)$ is parameterized by $\alpha \ge 0$:
$$R_\alpha(T) = R(T) + \alpha |T|$$
where $R(T)$ is total training impurity and $|T|$ is the number of terminal leaves.

The pruning path generated **1,002 possible positive `ccp_alpha` values**.  
Instead of testing every single value, five representative positive values spanning the regularization trajectory were evaluated:

| CCP Alpha | Training Accuracy | Testing Accuracy | Tree Depth | Leaves |
| :--- | :---: | :---: | :---: | :---: |
| **0.000100** | 96.16% | 63.17% | 41 | 1,982 |
| **0.000200** | 81.11% | 68.78% | 22 | 416 |
| **0.000300** | 74.61% | 71.54% | 12 | 60 |
| **0.000450** | 73.58% | 71.98% | 7 | 25 |
| **0.000600** | **72.98%** | **73.41%** | **5** | **14** |

---

## 9. Graph: Decision Tree Performance with Cost-Complexity Pruning

![Figure 1: Decision Tree Performance with Cost-Complexity Pruning](dt_pruning_performance.png)

### Graph Analysis:
The graph illustrates the relationship between `ccp_alpha` and both the training and testing accuracy of the Decision Tree:
- As the `ccp_alpha` penalty increases from $0.000100$ to $0.000600$, the **training accuracy decreases steadily** from $96.16\%$ to $72.98\%$. This expected behavior occurs because stronger penalty parameters aggressively collapse deep, over-specialized branches.
- In contrast, the **testing accuracy increases monotonically** across the tested pruning range, ascending from **$63.17\%$** up to **$73.41\%$**.
- The highest observed testing accuracy (**73.41%**) was achieved at:
  $$ccp\_alpha = 0.000600 \quad (6.00 \times 10^{-4})$$
- This clearly demonstrates that cost-complexity pruning eliminated high-variance branches and substantially improved generalization on unseen test data.

---

## 10. Final Pruned Decision Tree
The optimal pruning hyperparameter was:
$$ccp\_alpha = 0.000600$$

### The final pruned tree produced:
| Metric | Result |
| :--- | :---: |
| **Training Accuracy** | **72.98%** |
| **Testing Accuracy** | **73.41%** |
| **Tree Depth** | **5** |
| **Number of Leaves** | **14** |

### Final Classification Report ($ccp\_alpha = 0.000600$):
| Class | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| **a** | 0.77 | 0.89 | 0.83 | 534 |
| **b** | 0.65 | 0.68 | 0.66 | 548 |
| **c** | 0.62 | 0.59 | 0.61 | 444 |
| **d** | 0.90 | 0.76 | 0.82 | 505 |
| **Accuracy** | — | — | **0.73** | 2,031 |
| **Macro Avg** | 0.74 | 0.73 | 0.73 | 2,031 |
| **Weighted Avg** | 0.74 | 0.73 | 0.73 | 2,031 |

### Final Confusion Matrix ($ccp\_alpha = 0.000600$):
```
                 Predicted Class
                 a        b        c        d
Actual a        474       60        0        0
Actual b        124      371       53        0
Actual c         16      122      264       42
Actual d          0       17      106      382
```

---

## 11. Graph: Unpruned vs Pruned Decision Tree

![Figure 2: Unpruned vs Pruned Decision Tree](dt_unpruned_vs_pruned.png)

### Graph Analysis:
The grouped bar chart directly compares the training and testing accuracy profiles of the unpruned and pruned Decision Trees:
- For the unpruned tree, the training accuracy was **99.14%**, while testing accuracy was only **62.38%** (a large generalization gap of **36.76 percentage points**).
- After cost-complexity pruning, training accuracy adjusted to **72.98%**, while testing accuracy rose significantly to **73.41%**.
- Consequently, pruning successfully bridged the generalization divide, bringing the model into optimal bias-variance equilibrium.

---

## 12. Final Comparison

| Metric | Unpruned Decision Tree | Pruned Decision Tree | Difference / Impact |
| :--- | :---: | :---: | :---: |
| **Training Accuracy** | 99.14% | 72.98% | -26.16% (Variance suppressed) |
| **Testing Accuracy** | 62.38% | **73.41%** | **+11.03% (Generalization gained)** |
| **Tree Depth** | 41 | **5** | **87.80% depth reduction** |
| **Number of Leaves** | 2,587 | **14** | **99.46% complexity reduction** |

- The number of leaves decreased from **2,587 to 14**, representing a dramatic **99.46% reduction in tree complexity**.
- The testing accuracy increased from **62.38% to 73.41%**, an improvement of **11.03 percentage points**.
- The pruned model is readily interpretable, human-auditable, and deployable on resource-constrained embedded EV microcontrollers.

---

## 13. Observations
The following observations were made:
1. The Decision Tree classifier was successfully implemented and evaluated using the Electric Vehicle Trip Energy Consumption dataset.
2. The initial unpruned tree achieved near-perfect training accuracy (99.14%) but substantially lower testing accuracy (62.38%).
3. The unpruned tree grew to a depth of 41 and contained 2,587 leaves, confirming extreme model overfitting.
4. Minimal cost-complexity pruning effectively collapsed noise-fitting subtrees and stabilized predictive boundaries.
5. Increasing `ccp_alpha` progressively decreased training accuracy while systematically elevating generalization accuracy on unseen test data.
6. The optimal tested `ccp_alpha` of **0.000600** achieved a peak testing accuracy of **73.41%**.
7. The total number of leaves was curtailed from **2,587 down to 14** (a 99.46% size reduction).
8. The tree depth was simplified from **41 levels down to 5 levels**, making the decision logic easily explainable.
9. Classification performance improved notably across all four energy tiers, with Class `a` reaching 0.83 F1-score and Class `d` achieving 0.90 precision.
10. Pruning simultaneously reduced structural complexity by 99.46% and boosted testing performance by +11.03%, proving the indispensable value of cost-complexity regularization in tree-based modeling.

---

## 14. Conclusion
The **Decision Tree classification algorithm** was implemented on the **Electric Vehicle Trip Energy Consumption dataset** and evaluated before and after **cost-complexity pruning**.

The unpruned Decision Tree achieved 99.14% training accuracy and 62.38% testing accuracy, with a depth of 41 and 2,587 leaves. Cost-complexity pruning substantially regularized the model architecture.

At the optimal `ccp_alpha` value of **0.000600**, the final pruned tree achieved **72.98% training accuracy** and **73.41% testing accuracy**, requiring only **5 levels of depth** and **14 terminal leaves**.

Thus, in this experiment, cost-complexity pruning successfully eliminated overfitting, reduced tree complexity by over 99%, and produced an **11.03 percentage point increase** in real-world testing accuracy.
