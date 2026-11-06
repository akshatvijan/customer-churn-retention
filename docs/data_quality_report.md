# Data Quality Report
## Customer Churn & Retention Through Fulfilment Intelligence

**Phase:** Day 2 — Data Preparation and Fulfilment Analysis  
**Primary Dataset:** Olist Brazilian E-Commerce Dataset

## 1. Objective

The objective of this report is to evaluate the quality and consistency of the selected datasets before performing customer behaviour analysis and developing retention-risk features.

The analysis covers dataset structure, missing values, duplicate records, customer-level feature validation, and potential data leakage risks.

## 2. Dataset Overview

The following Olist datasets were used during the analysis.

| Dataset | Rows | Columns |
|---|---:|---:|
| Customers | 99,441 | 5 |
| Orders | 99,441 | 8 |
| Order Items | 112,650 | 7 |
| Payments | 103,886 | 5 |
| Reviews | 99,224 | 7 |

The datasets contain information about customers, orders, purchased products, payment transactions, and customer reviews.

## 3. Customer Feature Table

A customer-level feature table was generated using `customer_unique_id`.

The table contains the following features:

- `customer_unique_id`
- `total_orders`
- `delivered_orders`
- `cancelled_orders`
- `last_order_date`
- `average_order_value`
- `days_since_last_order`
- `retention_risk_proxy`

The generated table contains 96,096 customer records and 8 columns.

## 4. Data Quality Validation

The executed notebook identified the following issue:

| Validation | Result |
|---|---:|
| Customer records | 96,096 |
| Unique customer IDs | 96,096 |
| Duplicate customer IDs | 0 |
| Missing `total_orders` | 0 |
| Missing `delivered_orders` | 0 |
| Missing `cancelled_orders` | 0 |
| Missing `days_since_last_order` | 0 |
| Missing `average_order_value` | 1 |

One customer, identified by `830d5b7aaa3b6f1e9ad63703bec97d23`, had a missing `average_order_value`.

This issue requires checking the corresponding order, payment, and order-item records. The missing value should not automatically be replaced with zero because zero would represent a different business meaning.

The final duplicate-row count should be confirmed using the notebook's validation cell.

## 5. Data Quality Considerations

### 5.1 Missing Values

Missing values should be investigated before applying any imputation strategy. Financial features such as average order value require particular care because incorrect imputation can distort customer spending behaviour.

### 5.2 Duplicate Records

Customer-level features should contain one row per `customer_unique_id`.

Order-level tables should also be checked for duplicate order identifiers before performing merges.

### 5.3 Table Relationships

The following relationships were checked:

- Orders to customers through `customer_id`.
- Order items to orders through `order_id`.
- Payments to orders through `order_id`.
- Reviews to orders through `order_id`.

These relationships are important for combining operational and customer information correctly.

### 5.4 Aggregation Before Merging

Payment records should be aggregated at the order level before joining them to the orders table because an order may contain multiple payment records.

Similarly, reviews should be aggregated at the order level when a single review score per order is required.

## 6. Churn Label Considerations

The Olist dataset does not contain a direct, ground-truth customer churn label.

An inactivity-based retention-risk proxy can be created using the number of days since a customer's last purchase. However, this proxy represents an exploratory segmentation approach rather than a verified churn outcome.

Order cancellation must not be treated as equivalent to customer churn.

The IBM Telco Customer Churn dataset will be used separately for supervised churn modelling because it provides an explicit `Churn` target.

## 7. Data Leakage Risks

The following risks must be considered before modelling:

1. Delivery outcomes may not be available when a prediction is made before delivery.
2. Review scores may only become available after an order has been delivered.
3. The inactivity reference date is calculated retrospectively from the available dataset.
4. Features derived from future customer activity must not be used to predict an earlier outcome.
5. The Olist inactivity proxy must not be treated as the same target as the IBM Telco `Churn` column.

Features should be selected according to the intended prediction time.

## 8. Recommendations

- Investigate the customer record with the missing average order value.
- Confirm the final duplicate-row count.
- Verify that the processed feature table has been saved successfully.
- Keep Olist retention analysis separate from the IBM Telco supervised churn benchmark.
- Document all imputation and feature-selection decisions.

## 9. Conclusion

The customer-level feature table was generated with 96,096 records and 8 columns.

The available validation output identified one missing `average_order_value`. This issue and the final duplicate-row count should be resolved or explicitly documented before the table is considered fully validated.

The Olist feature table is intended for exploratory customer and fulfilment analysis. It is not, by itself, the final supervised machine-learning training dataset.