# Target and Evaluation Plan

## 1. Purpose

This document defines the initial target strategy, validation approach, evaluation metrics, and leakage-prevention rules for the Customer Churn & Retention Through Fulfilment Intelligence MVP.

Final modelling decisions will be made only after the selected datasets have been inspected.

## 2. IBM Telco Customer Churn — Primary Classification Benchmark

### Target definition

The expected target column is `Churn`, with values commonly represented as `Yes` and `No`. The actual file and target values must be verified before modelling.

- `Yes`: customer is labelled as churned in the dataset.
- `No`: customer is labelled as not churned in the dataset.

The dataset's documentation must be checked to understand the meaning and timing of this label.

### Initial modelling plan

1. Inspect the target column and its class distribution.
2. Identify identifier columns and remove unsuitable predictive features.
3. Separate numerical and categorical features.
4. Build preprocessing and modelling pipelines.
5. Establish a simple baseline classifier.
6. Evaluate using a held-out test set or an appropriate cross-validation strategy.
7. Compare candidate models using the same evaluation approach.

A stratified split may be used when appropriate to preserve the target-class proportions. The final split strategy will be recorded in the experiment results.

### Evaluation metrics

- **Precision:** Of customers predicted as churned, how many were labelled as churned?
- **Recall:** Of customers labelled as churned, how many did the model identify?
- **F1-score:** Harmonic mean of precision and recall.
- **ROC-AUC:** Measures ranking performance across classification thresholds when suitable for the target and evaluation setup.
- **Confusion matrix:** Summarises correct and incorrect predictions by class.

Accuracy may also be reported, but it must not be used alone if the target classes are imbalanced.

## 3. Olist — Target Feasibility Investigation

### Current position

Olist does not provide a verified churn label. The project must not label customers as confirmed churners merely because they have not placed another order in the observed data.

### Feasibility checks

Before creating an inactivity-based target, inspect:

1. The earliest and latest relevant order dates.
2. The number of unique customers and repeat purchasers.
3. The distribution of time between consecutive purchases.
4. The amount of customer history available before each possible prediction date.
5. Whether enough future data exists to observe the proposed outcome window.
6. Whether cancellations, incomplete records, or data coverage limitations could distort the outcome.

### Possible proxy-target design

If the available data supports it, an inactivity-based proxy may be investigated using:

- **Observation window:** Historical information available before a defined prediction date.
- **Prediction date:** The date on which the customer risk assessment is made.
- **Outcome window:** A future period used to check whether the customer places another qualifying order.
- **Proxy label:** A documented rule based on activity or inactivity during that future period.

The length of these windows is **not finalised**. It must be selected after examining dataset date coverage and purchase behaviour.

If the data cannot support a defensible future outcome window, the project will report the limitation rather than inventing a churn label.

## 4. Leakage Prevention

The following rules apply to both feature engineering and model evaluation:

1. Features must use information available at or before the prediction date.
2. Future orders, future reviews, and future delivery outcomes must not be included in historical prediction features.
3. Columns that directly reveal the target must not be used as input features.
4. Preprocessing steps, including imputation, encoding, and scaling where required, must be fitted using