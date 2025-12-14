# Formulas & Calculations Reference

This document provides detailed formulas and calculations used throughout the AI Research Impact Observatory pipeline. For a high-level overview, see [README.md](README.md).

## Table of Contents

1. [Paper-Level Metrics](#paper-level-metrics)
2. [Normalization Formulas](#normalization-formulas)
3. [Aggregation Formulas](#aggregation-formulas)
4. [Feature Engineering Formulas](#feature-engineering-formulas)
5. [Model Confidence Calculations](#model-confidence-calculations)
6. [Year-over-Year Calculations](#year-over-year-calculations)

---

## Paper-Level Metrics

### ML Impact Score

**Formula**:
```
ML_Impact_Score = ML_Probability × (W_ADOPT × Adoption_Normalized + W_IMPACT × Impact_Normalized + W_REPRO × Reproducibility_Normalized)
```

**Where**:
- `ML_Probability` (0.0 to 1.0): Probability that paper uses ML
- `Adoption_Normalized` (0.0 to 1.0): Normalized adoption level
- `Impact_Normalized` (0.0 to 1.0): Normalized impact scope
- `Reproducibility_Normalized` (0.0 to 1.0): Normalized reproducibility level
- `W_ADOPT = 0.45` (45% weight)
- `W_IMPACT = 0.35` (35% weight)
- `W_REPRO = 0.20` (20% weight)

**Calculation Steps**:
1. Calculate `ML_Probability` from binary ML classifier (see [Model Confidence Calculations](#model-confidence-calculations))
2. Normalize adoption level (0-4) → (0.0-1.0)
3. Normalize impact scope (0-3) → (0.0-1.0)
4. Normalize reproducibility (0-3) → (0.0-1.0)
5. Weighted sum: `0.45 × Adoption + 0.35 × Impact + 0.20 × Reproducibility`
6. Multiply by `ML_Probability`

**Example**:
- ML_Probability = 0.90 (90% chance uses ML)
- Adoption_Normalized = 0.75 (adoption level 3 out of 4)
- Impact_Normalized = 0.67 (impact level 2 out of 3)
- Reproducibility_Normalized = 0.67 (reproducibility level 2 out of 3)

```
Weighted_Sum = 0.45 × 0.75 + 0.35 × 0.67 + 0.20 × 0.67
             = 0.3375 + 0.2345 + 0.134
             = 0.706

ML_Impact_Score = 0.90 × 0.706 = 0.6354
```

**Range**: 0.0 to 1.0
- **0.0**: No ML usage or very low impact
- **1.0**: High ML usage with maximum impact and reproducibility

---

### Reproducibility Risk Score

**Formula**:
```
Reproducibility_Risk = ML_Probability × (1.0 - Reproducibility_Normalized)
```

**Where**:
- `ML_Probability` (0.0 to 1.0): Probability that paper uses ML
- `Reproducibility_Normalized` (0.0 to 1.0): Normalized reproducibility level

**Calculation Steps**:
1. Calculate `ML_Probability` from binary ML classifier
2. Normalize reproducibility level (0-3) → (0.0-1.0)
3. Calculate risk: `1.0 - Reproducibility_Normalized`
4. Multiply by `ML_Probability`

**Example**:
- ML_Probability = 0.95 (95% chance uses ML)
- Reproducibility_Normalized = 0.33 (reproducibility level 1 out of 3, difficult to reproduce)

```
Risk = 1.0 - 0.33 = 0.67
Reproducibility_Risk = 0.95 × 0.67 = 0.6365
```

**Range**: 0.0 to 1.0
- **0.0**: No ML usage or fully reproducible
- **1.0**: High ML usage with very low reproducibility (high risk)

**Interpretation**:
- **Low risk (0.0-0.3)**: ML papers that are easy to reproduce
- **Medium risk (0.3-0.7)**: Some reproducibility concerns
- **High risk (0.7-1.0)**: ML papers that are very difficult to reproduce

---

## Normalization Formulas

### Class Level Normalization

**Formula**:
```
Normalized_Value = Class_Level / Max_Class_Level
```

**Where**:
- `Class_Level`: The predicted class level (integer)
- `Max_Class_Level`: Maximum possible class level

**For Adoption Level**:
```
Adoption_Normalized = Adoption_Level / 4.0
```
- Adoption_Level: 0 (none), 1 (minimal), 2 (moderate), 3 (substantial), 4 (core)
- Max_Class_Level: 4
- Range: 0.0 to 1.0

**For Impact Scope**:
```
Impact_Normalized = Impact_Level / 3.0
```
- Impact_Level: 0 (narrow), 1 (moderate), 2 (broad), 3 (transformative)
- Max_Class_Level: 3
- Range: 0.0 to 1.0

**For Reproducibility**:
```
Reproducibility_Normalized = Reproducibility_Level / 3.0
```
- Reproducibility_Level: 0 (not_feasible), 1 (difficult), 2 (moderate), 3 (straightforward)
- Max_Class_Level: 3
- Range: 0.0 to 1.0

**Implementation**:
```python
def normalize_class(x: np.ndarray, max_class: int) -> np.ndarray:
    x = x.astype(float)
    return (x / float(max_class)).clip(0.0, 1.0)
```

---

### ML Probability Approximation

**Formula**:
```
ML_Probability = {
    Confidence_Score,  if Prediction == 1 (uses ML)
    1.0 - Confidence_Score,  if Prediction == 0 (no ML)
}
```

**Where**:
- `Prediction`: Binary prediction (0 = no ML, 1 = uses ML)
- `Confidence_Score`: Maximum class probability from calibrated classifier (0.0 to 1.0)

**Calculation Steps**:
1. Get binary prediction from ML classifier
2. Get confidence score (maximum probability from calibrated classifier)
3. If prediction = 1: `ML_Probability = Confidence_Score`
4. If prediction = 0: `ML_Probability = 1.0 - Confidence_Score`
5. Clip to [0.0, 1.0]

**Example**:
- Prediction = 1 (uses ML)
- Confidence_Score = 0.92

```
ML_Probability = 0.92
```

**Example**:
- Prediction = 0 (no ML)
- Confidence_Score = 0.85

```
ML_Probability = 1.0 - 0.85 = 0.15
```

**Implementation**:
```python
def approx_pos_prob(pred: np.ndarray, conf: np.ndarray) -> np.ndarray:
    pred = pred.astype(int)
    conf = conf.astype(float)
    return np.where(pred == 1, conf, 1.0 - conf).clip(0.0, 1.0)
```

---

## Aggregation Formulas

### Field-Year Aggregations

**Grouping**: Papers grouped by `field` and `publication_year`

**Metrics Calculated**:

1. **Number of Papers**:
   ```
   n_papers = COUNT(paper_id)
   ```

2. **ML Share**:
   ```
   ml_share = MEAN(is_ml_prob)
   ```
   - Average probability that papers in this field-year use ML
   - Range: 0.0 to 1.0

3. **Average Adoption**:
   ```
   avg_adoption = MEAN(adoption_pred)
   ```
   - Average adoption level (0-4)

4. **Average Impact**:
   ```
   avg_impact = MEAN(impact_pred)
   ```
   - Average impact level (0-3)

5. **Average Reproducibility**:
   ```
   avg_repro = MEAN(repro_pred)
   ```
   - Average reproducibility level (0-3)

6. **Average ML Impact Score**:
   ```
   avg_ml_impact = MEAN(ml_impact_score)
   ```
   - Average ML impact score across all papers in field-year

7. **Average Reproducibility Risk**:
   ```
   avg_repro_risk = MEAN(repro_risk)
   ```
   - Average reproducibility risk across all papers in field-year

8. **90th Percentile ML Impact**:
   ```
   p90_ml_impact = QUANTILE(ml_impact_score, 0.90)
   ```
   - Top 10% impact score in this field-year

9. **99th Percentile ML Impact**:
   ```
   p99_ml_impact = QUANTILE(ml_impact_score, 0.99)
   ```
   - Top 1% impact score in this field-year

10. **Year-over-Year ML Share Change**:
    ```
    ml_share_yoy = ml_share[year] - ml_share[year-1]
    ```
    - Change in ML adoption from previous year
    - Can be positive (increasing) or negative (decreasing)

11. **Year-over-Year Impact Change**:
    ```
    avg_ml_impact_yoy = avg_ml_impact[year] - avg_ml_impact[year-1]
    ```
    - Change in average impact from previous year

**Implementation**:
```python
field_year = (
    paper_scores
    .groupby(["field", "publication_year"], dropna=False)
    .agg(
        n_papers=("paper_id", "size"),
        ml_share=("is_ml_prob", "mean"),
        avg_adoption=("adoption_pred", "mean"),
        avg_impact=("impact_pred", "mean"),
        avg_repro=("repro_pred", "mean"),
        avg_ml_impact=("ml_impact_score", "mean"),
        avg_repro_risk=("repro_risk", "mean"),
        p90_ml_impact=("ml_impact_score", lambda x: float(np.quantile(x, 0.90))),
        p99_ml_impact=("ml_impact_score", lambda x: float(np.quantile(x, 0.99))),
    )
    .reset_index()
)
```

---

### Field-Level Aggregations

**Grouping**: Papers grouped by `field` (across all years)

**Metrics Calculated**:

1. **Total Papers**:
   ```
   n_papers = COUNT(paper_id)
   ```

2. **Overall ML Share**:
   ```
   ml_share = MEAN(is_ml_prob)
   ```
   - Average ML adoption rate across all years

3. **Average ML Impact**:
   ```
   avg_ml_impact = MEAN(ml_impact_score)
   ```
   - Average impact score across all papers in field

4. **95th Percentile ML Impact**:
   ```
   p95_ml_impact = QUANTILE(ml_impact_score, 0.95)
   ```
   - Top 5% impact score in field

5. **Average Reproducibility Risk**:
   ```
   avg_repro_risk = MEAN(repro_risk)
   ```
   - Average risk across all papers in field

**Implementation**:
```python
field_sum = (
    paper_scores
    .groupby("field", dropna=False)
    .agg(
        n_papers=("paper_id", "size"),
        ml_share=("is_ml_prob", "mean"),
        avg_ml_impact=("ml_impact_score", "mean"),
        p95_ml_impact=("ml_impact_score", lambda x: float(np.quantile(x, 0.95))),
        avg_repro_risk=("repro_risk", "mean"),
    )
    .reset_index()
    .sort_values(["avg_ml_impact", "ml_share", "n_papers"], ascending=False)
)
```

---

## Feature Engineering Formulas

### HashingVectorizer

**Purpose**: Convert text to numerical features using hash functions

**Formula**:
```
Feature_Index = hash(word) mod N_FEATURES
Feature_Value = count(word)  # or binary presence
```

**Where**:
- `hash(word)`: Hash function applied to word/ngram
- `N_FEATURES = 2^18 = 262,144`: Fixed number of features
- `count(word)`: Number of times word appears in document

**Configuration**:
- `n_features = 262,144` (2^18)
- `ngram_range = (1, 2)`: Single words and word pairs
- `binary = False`: Use counts (not just presence)
- `lowercase = True`: Convert to lowercase

**Example**:
- Word: "machine learning"
- Hash("machine") mod 262144 → Feature index 12345
- Hash("learning") mod 262144 → Feature index 67890
- Hash("machine learning") mod 262144 → Feature index 23456

**Output**: Sparse matrix of shape `(n_documents, 262144)`

---

### TF-IDF Transformation

**Term Frequency (TF)**:
```
TF(t, d) = count(t, d) / total_words(d)
```

**Where**:
- `t`: Term (word/ngram)
- `d`: Document (paper)
- `count(t, d)`: Number of times term appears in document
- `total_words(d)`: Total words in document

**Inverse Document Frequency (IDF)**:
```
IDF(t, D) = log(total_documents / documents_with_term(t))
```

**Where**:
- `D`: Collection of all documents
- `total_documents`: Total number of documents
- `documents_with_term(t)`: Number of documents containing term `t`

**TF-IDF Score**:
```
TF_IDF(t, d, D) = TF(t, d) × IDF(t, D)
```

**Normalization** (L2 norm):
```
TF_IDF_normalized = TF_IDF / sqrt(sum(TF_IDF^2))
```

**Example**:
- Term: "neural network"
- Appears 5 times in paper (out of 1000 words)
- Appears in 50 out of 36,821 papers

```
TF = 5 / 1000 = 0.005
IDF = log(36821 / 50) = log(736.42) = 6.60
TF_IDF = 0.005 × 6.60 = 0.033
```

**Output**: Sparse matrix of shape `(n_documents, 262144)` with TF-IDF scores

---

### TruncatedSVD (Dimensionality Reduction)

**Purpose**: Reduce 262,144 features to 256 features while preserving information

**Formula**:
```
X_reduced = X_tfidf × V[:, :256]
```

**Where**:
- `X_tfidf`: TF-IDF matrix (n_documents × 262144)
- `V`: Right singular vectors from SVD (262144 × 256)
- `X_reduced`: Reduced feature matrix (n_documents × 256)

**SVD Decomposition**:
```
X_tfidf = U × Σ × V^T
```

**Where**:
- `U`: Left singular vectors (n_documents × n_components)
- `Σ`: Singular values (diagonal matrix)
- `V`: Right singular vectors (262144 × n_components)

**Truncated SVD**:
- Keep only top 256 components (largest singular values)
- `V[:, :256]`: First 256 columns of V

**Variance Preserved**:
```
Variance_Preserved = sum(σ_i^2 for i=1..256) / sum(σ_i^2 for all i)
```
- Typically preserves 80-90% of variance

**Configuration**:
- `n_components = 256`
- `random_state = 42` (for reproducibility)

**Output**: Dense matrix of shape `(n_documents, 256)` with float32 values

---

## Model Confidence Calculations

### Calibrated Classifier Confidence

**Base Classifier**: Logistic Regression
- Outputs raw probabilities (may be overconfident)

**Calibration Method**: Sigmoid Calibration with 3-fold Cross-Validation

**Formula**:
```
Calibrated_Probability = sigmoid(a × logit(raw_probability) + b)
```

**Where**:
- `logit(p) = log(p / (1 - p))`: Logit transformation
- `sigmoid(x) = 1 / (1 + exp(-x))`: Sigmoid function
- `a, b`: Calibration parameters learned from cross-validation

**Confidence Score**:
```
Confidence = max(Calibrated_Probabilities)
```

**Where**:
- `Calibrated_Probabilities`: Array of probabilities for each class
- `max()`: Maximum probability (confidence in predicted class)

**Example** (Binary Classification):
- Raw probabilities: [0.3, 0.7]
- Calibrated probabilities: [0.25, 0.75]
- Prediction: 1 (second class)
- Confidence: 0.75

**Example** (Multi-class Classification):
- Raw probabilities: [0.1, 0.2, 0.5, 0.2]
- Calibrated probabilities: [0.08, 0.18, 0.65, 0.09]
- Prediction: 2 (third class, highest probability)
- Confidence: 0.65

**Implementation**:
```python
from sklearn.calibration import CalibratedClassifierCV

base = LogisticRegression(max_iter=4000, class_weight="balanced", solver="lbfgs")
clf = CalibratedClassifierCV(base, method="sigmoid", cv=3)
clf.fit(X_train, y_train)

proba = clf.predict_proba(X_test)
confidence = proba.max(axis=1)  # Maximum probability
```

---

### Overall Confidence Score (Bucketing)

**Formula**:
```
Overall_Confidence = (is_ml_conf + adoption_conf + impact_conf + repro_conf) / 4.0
```

**Bucketing**:
```
Confidence_Label = {
    "high",    if Overall_Confidence >= 0.80
    "medium",  if 0.60 <= Overall_Confidence < 0.80
    "low",     if Overall_Confidence < 0.60
}
```

**Where**:
- `is_ml_conf`: Confidence from binary ML classifier
- `adoption_conf`: Confidence from adoption level classifier
- `impact_conf`: Confidence from impact scope classifier
- `repro_conf`: Confidence from reproducibility classifier

**Example**:
- is_ml_conf = 0.95
- adoption_conf = 0.85
- impact_conf = 0.75
- repro_conf = 0.80

```
Overall_Confidence = (0.95 + 0.85 + 0.75 + 0.80) / 4.0 = 0.8375
Confidence_Label = "high"  (0.8375 >= 0.80)
```

**Implementation**:
```python
def bucket_conf(x: np.ndarray):
    out = np.full(len(x), "low", dtype=object)
    out[x >= 0.80] = "high"
    out[(x >= 0.60) & (x < 0.80)] = "medium"
    return out
```

---

## Year-over-Year Calculations

### ML Share Year-over-Year Change

**Formula**:
```
ml_share_yoy[field, year] = ml_share[field, year] - ml_share[field, year-1]
```

**Where**:
- `ml_share[field, year]`: ML adoption share in current year
- `ml_share[field, year-1]`: ML adoption share in previous year

**Example**:
- Physics, 2020: ml_share = 0.35
- Physics, 2021: ml_share = 0.42

```
ml_share_yoy[Physics, 2021] = 0.42 - 0.35 = 0.07
```
- Positive value: ML adoption increased by 7 percentage points

**Implementation**:
```python
field_year["ml_share_yoy"] = field_year.groupby("field")["ml_share"].diff()
```

---

### ML Impact Year-over-Year Change

**Formula**:
```
avg_ml_impact_yoy[field, year] = avg_ml_impact[field, year] - avg_ml_impact[field, year-1]
```

**Where**:
- `avg_ml_impact[field, year]`: Average ML impact in current year
- `avg_ml_impact[field, year-1]`: Average ML impact in previous year

**Example**:
- Chemistry, 2019: avg_ml_impact = 0.15
- Chemistry, 2020: avg_ml_impact = 0.18

```
avg_ml_impact_yoy[Chemistry, 2020] = 0.18 - 0.15 = 0.03
```
- Positive value: Average impact increased by 0.03

**Implementation**:
```python
field_year["avg_ml_impact_yoy"] = field_year.groupby("field")["avg_ml_impact"].diff()
```

---

## Score Driver Identification

**Purpose**: Identify which component drives the ML Impact Score

**Formula**:
```
Score_Driver = argmax([Adoption_Normalized, Impact_Normalized, Reproducibility_Normalized])
```

**Where**:
- `argmax()`: Returns index of maximum value
- Values: [0 = adoption, 1 = impact, 2 = repro]

**Example**:
- Adoption_Normalized = 0.75
- Impact_Normalized = 0.90
- Reproducibility_Normalized = 0.50

```
Score_Driver = argmax([0.75, 0.90, 0.50]) = 1 = "impact"
```
- Impact is the dominant driver (highest normalized value)

**Implementation**:
```python
drivers = np.vstack([adopt_norm, impact_norm, repro_norm]).T
driver_names = np.array(["adoption", "impact", "repro"])
score_driver = driver_names[np.argmax(drivers, axis=1)]
```

---

## Summary

### Key Formula Summary

| Metric | Formula | Range |
|--------|---------|-------|
| **ML Impact Score** | `ML_Prob × (0.45×Adopt + 0.35×Impact + 0.20×Repro)` | 0.0-1.0 |
| **Reproducibility Risk** | `ML_Prob × (1.0 - Repro)` | 0.0-1.0 |
| **Adoption Normalized** | `Adoption_Level / 4.0` | 0.0-1.0 |
| **Impact Normalized** | `Impact_Level / 3.0` | 0.0-1.0 |
| **Repro Normalized** | `Repro_Level / 3.0` | 0.0-1.0 |
| **ML Probability** | `Confidence if pred=1, else 1-Confidence` | 0.0-1.0 |
| **ML Share** | `MEAN(is_ml_prob)` | 0.0-1.0 |
| **Year-over-Year Change** | `Value[year] - Value[year-1]` | Any |

### Weight Distribution

The ML Impact Score uses the following weights:
- **Adoption**: 45% (most important)
- **Impact**: 35% (very important)
- **Reproducibility**: 20% (important but less than others)

This weighting reflects that adoption depth is the primary indicator of ML integration, followed by impact, with reproducibility as a quality factor.

---

For implementation details, see the code in `main.ipynb` Block 5 (Gold Layer).
