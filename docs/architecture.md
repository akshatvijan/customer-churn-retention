# System Architecture — Customer Churn & Retention Through Fulfilment Intelligence

## 1. Purpose

This document describes the planned architecture of the Customer Churn & Retention Through Fulfilment Intelligence MVP.

The architecture will combine customer and fulfilment data analysis, churn-risk evaluation, evidence-based investigation, policy-controlled retention recommendations, and an API.

The implementation will be developed incrementally. Components shown in the approved architecture diagrams represent the intended design and do not imply that every component has already been implemented.

## 2. Approved Architecture Diagrams

The project has two approved architecture diagrams:

1. **Agentic AI Workflow Flowchart** — describes the intended workflow and coordination of investigation, analysis, decision-making, and review.
2. **Application Architecture Flowchart** — describes the intended application components and their relationships.

The original approved diagrams must be preserved. This document supplements them with written descriptions rather than replacing them.

The diagrams will be maintained in `docs/diagrams/`.

## 3. High-Level Architecture

The planned application is organised into the following layers.

### 3.1 Data Layer

**Purpose:** Store and prepare the data used by the application.

Selected sources:
- Olist Brazilian E-Commerce Dataset.
- IBM Telco Customer Churn dataset.
- Synthetic campaign and incentive scenarios.

Responsibilities:
- Validate input files and schemas.
- Inspect missing values, duplicate records, and data types.
- Prepare customer and fulfilment features.
- Keep the selected datasets separate where their populations and meanings differ.
- Record data provenance and known limitations.

### 3.2 Machine Learning Layer

**Purpose:** Evaluate customer churn risk where the target and data support meaningful prediction.

Planned responsibilities:
- Feature preprocessing.
- Baseline model training and evaluation.
- Model comparison.
- Prediction generation.
- Model performance reporting.
- Explainability using SHAP where appropriate.

IBM Telco will initially serve as a separate labelled benchmark. Olist modelling depends on whether a defensible future inactivity target can be established.

### 3.3 Fulfilment Investigation Layer

**Purpose:** Gather and organise available evidence that may be relevant to a customer's experience.

Potential evidence includes:
- Order status.
- Delivery timing.
- Cancellation information.
- Review information.
- Purchase history.

The layer must distinguish observed evidence from assumptions. It must not claim that an operational issue caused churn without supporting evidence.

### 3.4 Agent Orchestration Layer

**Purpose:** Coordinate the planned investigation and decision workflow.

LangGraph is the planned orchestration framework.

Potential responsibilities include:
- Receiving a customer-analysis request.
- Coordinating relevant investigation steps.
- Passing structured evidence between components.
- Requesting