# Decision Layer Selection — Customer Churn & Retention Through Fulfilment Intelligence

## 1. Purpose

This document records the initial approach for selecting retention actions in the MVP.

The decision layer must convert available customer evidence and risk information into recommendations that follow explicit business rules. A model prediction or agent-generated suggestion must not independently authorise a consequential action.

## 2. Decision-Layer Requirements

The decision layer should:

1. Accept structured customer evidence and relevant risk information when available.
2. Evaluate candidate retention actions.
3. Check eligibility and applicable business policies.
4. Consider incentive cost and budget limits.
5. Enforce contact-frequency restrictions when the required information is available.
6. Require human approval before an incentive is issued.
7. Explain why an action was recommended or rejected.
8. Support a no-action outcome when no candidate action is appropriate.
9. Record decision evidence and approval status for later review.
10. Handle missing or unreliable information safely.

## 3. Candidate Approaches

### Option A: Deterministic Rules and Baseline Ranker

This approach uses explicit business rules and a simple ranking mechanism to evaluate candidate actions.

**Advantages:**
- Decisions are predictable and reproducible.
- Eligibility and budget constraints can be tested directly.
- Individual rules are easier to inspect and explain.
- It does not require a trained language model to enforce core policies.
- It provides a practical baseline for the MVP.

**Limitations:**
- Rules require maintenance as business requirements change.
- The ranking mechanism may not capture complex customer behaviour.
- Rule quality depends on the quality of available evidence and requirements.

### Option B: Agent-Based Recommendation

An agentic workflow can gather evidence, coordinate investigations, and propose candidate actions.

**Advantages:**
- Can coordinate multiple investigation steps.
- Can organise evidence from different application components.
- Can provide contextual explanations for recommendations.
- Can support more complex workflows.

**Limitations:**
- Outputs may be inconsistent if not constrained.
- Additional orchestration and testing are required.
- An agent-generated suggestion is not, by itself, proof that an action is eligible or beneficial.
- Policy enforcement must not depend solely on natural-language instructions.

### Option C: Hybrid Decision Layer

A hybrid approach combines agent-based investigation with deterministic decision and policy checks.

The agentic workflow gathers and organises evidence. The deterministic layer validates candidate actions against explicit rules before the application returns a recommendation.

**Advantages:**
- Supports contextual investigation and predictable policy enforcement.
- Separates evidence gathering from action eligibility.
- Makes approval requirements and decision outcomes easier to audit.

**Limitations:**
- Requires clear interfaces between the workflow and decision components.
- Needs testing for missing evidence, conflicting recommendations, and policy failures.
- Adds integration complexity compared with a rules-only implementation.

## 4. Provisional Selection

**Selected for the initial MVP: a deterministic baseline ranker combined with a policy engine.**

The broader application may use a hybrid workflow in which LangGraph coordinates investigation and recommendation steps, while deterministic code remains responsible for validating eligibility and enforcing mandatory constraints.

This is a provisional architectural decision. The final implementation may be refined after requirements and technical compatibility are evaluated.

## 5. Candidate Retention Actions

The initial candidate action set is:

| Candidate action | Intended use | Required checks |
|---|---|---|
| Service investigation | Investigate a possible fulfilment or service issue | Supporting evidence and investigation eligibility |
| Customer follow-up | Contact a customer where appropriate | Consent or applicable contact rules, contact-frequency limits |
| Feedback request | Request feedback about an experience | Relevant interaction and contact eligibility |
| Discount or free shipping | Consider an eligible incentive | Eligibility, cost, budget, applicable terms, human approval |
| Loyalty incentive | Consider an eligible loyalty-related action | Eligibility, cost, applicable terms, human approval |
| No action | Avoid an unnecessary or unsupported intervention | Record why no action was selected where appropriate |

The exact rules and thresholds must be defined and tested before these actions can be treated as operational.

## 6. Decision Sequence

The planned decision sequence is:

1. Receive structured evidence and available risk information.
2. Validate the request and required fields.
3. Identify candidate actions relevant to the case.
4. Check action-specific eligibility.
5. Apply contact-frequency, budget, and other applicable constraints.
6. Exclude actions that violate mandatory policies.
7. Rank the remaining eligible actions using a documented baseline method.
8. Select the highest-ranked eligible action or choose no action.
9. Mark incentives as pending human approval.
10. Record the decision, supporting evidence, policy results, and approval status.

If essential information is missing, the system should request further investigation or return a safe no-action result instead of inventing facts.

## 7. Safety and Governance Rules

- A churn-risk score does not prove that a customer will leave.
- A recommendation does not prove that an action will retain the customer.
- Synthetic campaign scenarios do not demonstrate real-world campaign effectiveness.
- An agent must not bypass deterministic policy checks.
- Incentives must not be issued without the required human approval.
- The application must distinguish proposed, approved, rejected, and executed actions.
- Decisions should be traceable without unnecessarily exposing sensitive customer information.
- The decision layer must not fabricate eligibility, consent, budget, or customer-history information.

## 8. OpenJEV and Laya Evaluation

OpenJEV and Laya are candidates for further technical investigation, not confirmed selections.

Before selecting either, the project must:
1. Identify the exact intended product, library, or repository.
2. Review its official technical documentation.
3. Verify compatibility with the project's Python environment and workflow.
4. Assess its integration requirements and maintenance status.
5. Compare its capabilities against the actual MVP requirements.
6. Document the evidence supporting the final choice.

No compatibility or performance claim is made before this review.

## 9. Day 1 Status

The provisional decision-layer approach has been documented.

Pending work:
- Define the exact action-ranking inputs and scoring method.
- Specify policy rules and test cases.
- Evaluate OpenJEV and Laya against the project requirements.
- Implement the decision layer.
- Validate policy enforcement through automated tests.

The decision layer has not yet been implemented merely by documenting this plan.