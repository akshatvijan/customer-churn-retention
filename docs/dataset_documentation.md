# Dataset Documentation — Customer Churn & Retention Through Fulfilment Intelligence

## 1. Purpose

This document records the selected data sources, their intended use, expected validation checks, and known limitations for the MVP.

Dataset schemas, actual files, date coverage, and data quality must be verified before implementation decisions are finalised.

## 2. Dataset Overview

| Dataset | Intended use | Churn label available? | Current status |
|---|---|---|---|
| Olist Brazilian E-Commerce Dataset | Customer behaviour and fulfilment analysis | No verified churn label | Schema and files pending local validation |
| IBM Telco Customer Churn | Separate supervised churn-classification benchmark | Yes, a churn label is provided | Exact file and schema pending validation |
| Synthetic Campaign and Incentive Dataset | Test retention recommendations, eligibility rules, and hypothetical campaign scenarios | Synthetic labels, if generated, are not real observed outcomes | To be designed and generated |

DataCo and UCI Online Retail II are excluded from the current MVP.

## 3. Olist Brazilian E-Commerce Dataset

### Intended purpose
Olist is the primary dataset for analysing customer purchasing behaviour and fulfilment-related evidence.

### Expected areas of analysis
The available tables may support analysis of:
- Customer and customer-location records.
- Orders and order status.
- Order items and product information.
- Payments.
- Seller information.
- Delivery timestamps and estimated delivery dates.
- Customer reviews.

The exact tables, column names, relationships, and date ranges must be confirmed against the actual files before use.

### Planned validation
1. List the available CSV files.
2. Inspect column names and data types.
3. Check missing values and duplicate records.
4. Validate primary identifiers and relationships between tables.
5. Inspect order and delivery date coverage.
6. Determine whether repeat purchases and future inactivity can be evaluated reliably.
7. Document exclusions and any data-cleaning decisions.

### Churn limitation
Olist does not provide a verified churn label. An inactivity-based target may be investigated only after establishing a defensible observation period, prediction date, and future outcome window.

Inactivity must be described as a proxy outcome, not confirmed customer churn.

## 4. IBM Telco Customer Churn Dataset

### Intended purpose
This dataset will provide a separate labelled benchmark for developing and evaluating a churn-classification workflow.

### Target
The expected target column is `Churn`, commonly represented by values such as `Yes` and `No`. Its actual name, values, missing records, and class distribution must be checked in the selected file.

### Planned validation
1. Confirm the source and exact file version.
2. Inspect all column names and data types.
3. Check missing values, duplicates, and identifier columns.
4. Inspect the target distribution.
5. Identify categorical and numerical features.
6. Check for identifiers or other fields that should not be used as predictive features.
7. Create a leakage-aware training and evaluation process.

### Limitation
IBM Telco represents a different business context from Olist. Its model performance cannot be assumed to generalise to Olist customers.

The two datasets must remain separate; records must not be joined across them.

## 5. Synthetic Campaign and Incentive Dataset

### Intended purpose
Synthetic data will support development and testing of retention-action rules before real campaign outcome data is available.

### Potential fields
The proposed schema may include:
- Scenario identifier.
- Customer reference identifier.
- Candidate action.
- Eligibility status.
- Incentive cost.
- Available budget.
- Contact-frequency status.
- Approval status.
- Hypothetical scenario outcome, if required for testing.

The final schema will be documented when the generator is implemented.

### Limitations
Synthetic records are hypothetical. They can test software behaviour and policy rules, but cannot establish that an incentive causes real customers to remain active.

Synthetic outcomes must not be reported as measured business results.

## 6. Data Storage and Handling

The project will use the following local directories:

- `data/raw/` — original dataset files, kept unchanged where licensing and distribution terms permit.
- `data/processed/` — validated and transformed datasets.
- `data/synthetic/` — generated campaign and incentive scenarios.

Dataset files should not be committed to Git until their licence, redistribution terms, size, and privacy implications have been reviewed.

Credentials and other secrets must not be stored in datasets, source code, or Git history.

## 7. Cross-Dataset Rules

1. Olist is used for customer and fulfilment analysis.
2. IBM Telco is used as a separate churn benchmark.
3. Synthetic data is used for hypothetical scenarios and policy testing.
4. No direct join is permitted between Olist and IBM Telco customer records.
5. Features must be derived only from information available at the intended prediction time.
6. Future information must not leak into model training features.
7. Data quality issues and exclusions must be documented.

## 8. Current Validation Status

At the start of Day 1, the project structure and development environment have been created, but the actual dataset files and their schemas have not yet been confirmed in the local project.

Therefore, the following remain pending:
- Dataset acquisition and source verification.
- File and schema inspection.
- Data quality checks.
- Date coverage assessment.
- Olist target feasibility assessment.
- Final feature and preprocessing decisions.

This document describes the data plan; it does not claim that dataset validation has already been completed.