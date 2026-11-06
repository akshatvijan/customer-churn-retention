# User Stories — Customer Churn & Retention Through Fulfilment Intelligence

## 1. Purpose

These user stories describe how different users will interact with the Customer Churn & Retention Through Fulfilment Intelligence system. They define expected behaviour and acceptance criteria for the MVP.

## 2. Retention Manager

### US-01: Identify Customers Requiring Attention
**As a** retention manager,  
**I want** to identify customers who may be at risk of disengaging,  
**so that** I can prioritise appropriate retention activities.

**Acceptance criteria:**
- The system must show a risk score only when a suitable model and target definition are available.
- The score must be accompanied by an explanation of its intended meaning.
- The system must not describe an unverified inactivity proxy as confirmed churn.
- Missing or unreliable information must be clearly identified.

### US-02: Understand Fulfilment Issues
**As a** retention manager,  
**I want** to review relevant order and fulfilment evidence,  
**so that** I can investigate possible service-related problems.

**Acceptance criteria:**
- The system should use available order, delivery, and review information from Olist.
- It must distinguish observed facts from assumptions or inferred explanations.
- It must not claim that a fulfilment issue caused a customer to leave without supporting evidence.

### US-03: Receive Retention Action Recommendations
**As a** retention manager,  
**I want** to receive suitable retention-action suggestions,  
**so that** I can decide how to follow up with a customer.

**Acceptance criteria:**
- Candidate actions may include service investigation, customer follow-up, feedback request, eligible discount or free shipping, loyalty incentive, or no action.
- Recommendations must follow deterministic eligibility and policy rules.
- Incentives must require human approval before they are issued.
- The system must explain the evidence and rules supporting a recommendation.

## 3. Data Analyst

### US-04: Validate Dataset Quality
**As a** data analyst,  
**I want** to inspect dataset schemas, missing values, duplicates, and date coverage,  
**so that** I can assess whether the data is suitable for analysis.

**Acceptance criteria:**
- Dataset columns and data types must be inspected before feature engineering.
- Missing values and duplicate records must be measured and documented.
- Date coverage and customer identifiers must be checked where available.
- Unverified dataset assumptions must be recorded as pending validation.

### US-05: Evaluate Churn Prediction
**As a** data analyst,  
**I want** to evaluate churn prediction using a labelled benchmark dataset,  
**so that** I can measure model performance on data not used for training.

**Acceptance criteria:**
- IBM Telco Customer Churn must be evaluated separately from Olist.
- The target label and class distribution must be documented.
- Evaluation must use a suitable held-out test set or cross-validation strategy.
- Suitable metrics must be reported, including precision, recall, F1-score, and ROC-AUC when appropriate.
- Results from IBM Telco must not automatically be treated as proof of performance on Olist customers.

## 4. Machine Learning Engineer

### US-06: Explain Predictions
**As a** machine learning engineer,  
**I want** to explain model predictions using relevant features and suitable explanation methods,  
**so that** users can understand the evidence associated with a prediction.

**Acceptance criteria:**
- Explanations must refer to available model features.
- SHAP may be used when compatible with the selected model and explanation method.
- Explanations must not be presented as proof of causation.
- The system must identify limitations or missing evidence.

## 5. System Administrator

### US-07: Access a Health Endpoint
**As a** system administrator,  
**I want** a health endpoint for the API,  
**so that** I can check whether the application is responding.

**Acceptance criteria:**
- `GET /health` must return a successful response when the API is running.
- The response must contain a clear status field.
- The health endpoint must not expose credentials or sensitive customer information.

### US-08: Audit Retention Decisions
**As a** system administrator or authorised reviewer,  
**I want** important recommendation details to be recorded,  
**so that** decisions can be reviewed later.

**Acceptance criteria:**
- Records should identify the recommendation, supporting evidence, applicable policy checks, and approval status.
- Sensitive information must not be unnecessarily included in logs.
- The system must distinguish a proposed action from an approved or executed action.

## 6. Scope Boundaries

- Olist is the primary source for customer and fulfilment analysis.
- IBM Telco Customer Churn is a separate labelled benchmark.
- Synthetic campaign and incentive data is for hypothetical scenarios and testing.
- DataCo and UCI Online Retail II are excluded from the current MVP.
- The system must not claim that synthetic scenarios prove real-world campaign effectiveness.
- A model score alone must not trigger an incentive or other consequential action.

## 7. Day 1 Status

These user stories define the intended MVP behaviour. Their acceptance criteria will be verified progressively during implementation and testing. They are not evidence that all features have already been implemented.