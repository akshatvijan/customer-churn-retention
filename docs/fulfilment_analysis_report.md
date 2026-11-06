# Fulfilment Analysis Report
## Customer Churn & Retention Through Fulfilment Intelligence

**Phase:** Day 2 — Data Preparation and Fulfilment Analysis  
**Primary Dataset:** Olist Brazilian E-Commerce Dataset

## 1. Objective

The objective of this analysis is to investigate order fulfilment performance, cancellations, customer review patterns, and purchase inactivity.

The findings can help identify operational patterns that may be associated with customer experience and retention risk.

## 2. Order Status Analysis

The notebook produced the following order-status distribution.

| Order Status | Orders | Share |
|---|---:|---:|
| Delivered | 96,478 | 97.02% |
| Shipped | 1,107 | 1.11% |
| Canceled | 625 | 0.63% |
| Unavailable | 609 | 0.61% |
| Invoiced | 314 | 0.32% |
| Processing | 301 | 0.30% |

Delivered orders represent the large majority of recorded orders.

Canceled and unavailable orders represent operational issues that can be investigated further.

However, a canceled order does not necessarily mean that the customer has churned.

## 3. Delivery Performance Analysis

Delivery performance was calculated using delivered orders with usable delivery timestamps.

| Metric | Result |
|---|---:|
| Delivered orders analysed | 96,470 |
| Average delivery duration | 12.56 days |
| Average delivery delay | -11.18 days |
| Late deliveries | 7,820 |
| Late-delivery percentage | 8.11% |

Delivery delay was calculated by comparing the actual delivery timestamp with the estimated delivery timestamp.

A negative average delay of -11.18 days indicates that deliveries occurred earlier than the estimated delivery date on average.

Approximately 8.11% of the analysed delivery records were classified as late.

These statistics describe the records used by the notebook and should not automatically be generalized to orders with missing or invalid timestamps.

## 4. Customer Review Analysis

The overall average review score reported by the notebook was 4.09.

The review-score distribution was:

| Review Score | Reviews | Share |
|---|---:|---:|
| 1 | 11,424 | 11.51% |
| 2 | 3,151 | 3.18% |
| 3 | 8,179 | 8.24% |
| 4 | 19,142 | 19.29% |
| 5 | 57,328 | 57.78% |

Five-star reviews represented the largest category, accounting for 57.78% of the recorded reviews.

However, 11.51% of reviews received one star, indicating that a portion of customers reported a poor experience.

## 5. Delivery Timeliness and Review Scores

The notebook compared average review scores for late deliveries and deliveries classified as on-time or early.

| Delivery Category | Reviews | Average Review Score |
|---|---:|---:|
| Late Delivery | 7,655 | 2.57 |
| On-Time or Early | 88,169 | 4.29 |

The average review score for late deliveries was 2.57, compared with 4.29 for on-time or early deliveries.

This indicates an association between late delivery and lower customer review scores in the analysed records.

However, this is an observational relationship and does not prove that delivery delays directly caused lower ratings. Other factors, such as product quality, seller performance, and customer-service experience, may also influence review scores.

## 6. Inactivity-Based Retention-Risk Proxy

An exploratory retention-risk proxy was created using the number of days since each customer's last recorded order.

The notebook used `2018-10-17 17:30:18` as the reference timestamp, corresponding to the latest purchase timestamp in the loaded data.

The resulting categories were:

| Retention-Risk Category | Customers |
|---|---:|
| `high_inactivity` | 86,432 |
| `at_risk` | 7,990 |
| `monitor` | 1,665 |
| `recent` | 9 |

The distribution shows that most customers fall into the high-inactivity category under the thresholds used in the notebook.

This result must be interpreted in the context of the historical dataset and the selected inactivity thresholds. It does not represent a verified churn rate.

## 7. Key Findings

### Finding 1: Most Recorded Orders Were Delivered

Delivered orders represented 97.02% of the order-status records reported by the notebook.

### Finding 2: Most Analysed Deliveries Were Not Late

The late-delivery percentage was 8.11% among the delivery records used in the analysis.

### Finding 3: Late Delivery Was Associated With Lower Review Scores

Late deliveries had an average review score of 2.57, while on-time or early deliveries had an average score of 4.29.

This difference suggests that delivery performance deserves further investigation as a potential contributor to customer experience.

### Finding 4: Most Reviews Were Positive

Five-star reviews represented 57.78% of the recorded reviews, although 11.51% were one-star reviews.

### Finding 5: The Inactivity Proxy Flagged Most Customers

Most customers were classified as highly inactive under the exploratory thresholds. The result should not be interpreted as evidence that these customers have permanently churned.

## 8. Limitations and Leakage Risks

- Olist does not provide a direct customer churn label.
- The inactivity proxy depends on a retrospective reference timestamp.
- Review scores may not be available at the intended prediction time.
- Actual delivery outcomes may occur after a retention prediction would need to be made.
- The association between delivery delays and review scores does not establish causation.
- Olist-derived features must remain separate from the IBM Telco churn target in the planned benchmark approach.

## 9. Conclusion

The analysis identified an association between delivery timeliness and customer review experience. Late deliveries had substantially lower average review scores than deliveries classified as on-time or early.

The inactivity-based proxy can support exploratory customer segmentation, but it should not be treated as a validated churn label.

These findings provide a foundation for further investigation of customer behaviour, fulfilment performance, and retention risk, subject to data validation and careful control of prediction-time leakage.