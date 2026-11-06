# Customer Churn & Retention Through Fulfilment Intelligence

## 1. Business Problem

Businesses need to identify customers who may be disengaging, understand relevant customer and fulfilment history, and select appropriate retention actions.

Customer retention decisions can become difficult when customer behaviour, order history, delivery performance, cancellations, and review information are spread across different datasets.

The proposed system will provide a structured workflow to analyse available customer information, investigate fulfilment evidence, estimate retention risk when a defensible target is available, and recommend feasible retention actions under explicit business rules.

## 2. Project Objective

The objective is to build a customer retention intelligence system that:

1. Analyses customer and fulfilment information.
2. Identifies useful customer-level behavioural and operational features.
3. Evaluates churn prediction using a separately labelled benchmark dataset.
4. Investigates whether Olist data supports a defensible future inactivity outcome.
5. Explains model predictions using suitable evidence and SHAP where applicable.
6. Proposes retention actions using deterministic eligibility and policy rules.
7. Records decision evidence, approval status, and relevant prediction metadata.
8. Exposes the functionality through a documented API and an agentic workflow.

## 3. Selected Data Sources

### Olist E-Commerce Dataset

Olist is the primary source for customer and fulfilment analysis. Its order, customer, delivery, and review information will be examined to determine which features and temporal outcomes are supported.

Olist does not provide a verified customer churn label. Any inactivity-based target must be defined explicitly and validated against the available observation period.

### IBM Telco Customer Churn Dataset

IBM Telco provides a labelled churn benchmark. It will be used as a separate dataset to evaluate a churn classification workflow.

Telco customer records must not be joined to Olist customer records. The datasets represent different customer populations and business contexts.

### Synthetic Campaign and Incentive Dataset

Synthetic campaign data will support development and testing of retention-action scenarios, eligibility rules, and budget constraints.

Synthetic records are hypothetical. They cannot establish that a real retention campaign causes better customer retention.

## 4. Intended Users

- Retention managers who review candidate customer follow-up actions.
- Customer experience managers who investigate fulfilment issues.
- Analysts who examine customer behaviour and operational evidence.
- ML engineers who evaluate predictions and monitor data quality.
- Business owners who review and approve consequential retention decisions.

## 5. Proposed System Workflow

1. Load and validate the selected datasets.
2. Analyse customer and fulfilment records.
3. Build customer-level features where supported by the data.
4. Define and validate the prediction target.
5. Train and evaluate an appropriate model when the target is defensible.
6. Explain predictions and distinguish observed facts from model inferences.
7. Generate candidate retention actions.
8. Apply eligibility, budget, contact-frequency, and approval rules.
9. Return a structured response and preserve relevant audit information.

## 6. Candidate Retention Actions

Candidate actions may include:

- Investigating a delivery or service issue.
- Following up with a customer.
- Requesting feedback when appropriate.
- Offering an eligible discount or free shipping.
- Proposing a loyalty incentive.
- Taking no action when evidence or eligibility is insufficient.

Incentives must not be issued automatically without the required human approval.

## 7. Scope and Boundaries

The seven-day MVP will focus on Olist, the separate IBM Telco churn benchmark, and synthetic campaign/incentive scenarios.

DataCo Smart Supply Chain and UCI Online Retail II are excluded from the current MVP.

The system is intended to support decisions, not to establish customer intent or prove causal relationships between fulfilment events and churn.

A risk score is not proof that a customer will leave. Recommendations must remain grounded in available evidence and deterministic policy checks.

## 8. Initial Technology Stack

- Python
- Pandas and NumPy
- Scikit-learn
- SHAP
- FastAPI and Pydantic
- PostgreSQL
- LangGraph
- Pytest
- MCP and Langfuse for the planned integration, subject to implementation and validation

## 9. Success Criteria

The project will be considered successful when:

1. The selected datasets and their limitations are documented.
2. Data quality and target feasibility are checked reproducibly.
3. Any trained model is evaluated on data not used to fit that model.
4. Predictions and explanations distinguish evidence from inference.
5. Retention actions pass deterministic policy validation.
6. Consequential actions require the specified approval.
7. API behaviour and important business rules have automated tests.
8. Setup, architecture, evaluation results, and limitations are documented.

## 10. Known Limitations

- Olist has no verified churn label.
- An inactivity-based outcome is a proxy and must not be described as verified churn.
- IBM Telco benchmark results may not generalise to Olist customers.
- Synthetic campaign data does not prove real-world campaign effectiveness.
- Model explanations do not establish causality.
- Final model selection depends on data validation and measured evaluation results.