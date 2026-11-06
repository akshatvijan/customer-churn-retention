
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd

from frontend.shared.api_client import get_request, post_request


# ---------------- PAGE CONFIGURATION ----------------

st.set_page_config(
    page_title="Retention Intelligence | Admin",
    page_icon="📊",
    layout="wide"
)


# ---------------- CUSTOM CSS ----------------

st.markdown("""
<style>
    .main {
        background-color: #f8fafc;
    }

    .block-container {
        padding-top: 2rem;
    }

    .dashboard-subtitle {
        color: #64748b;
        font-size: 14px;
    }

    .approval-card {
        padding: 16px;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        margin-bottom: 12px;
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)


# ---------------- SESSION STATE ----------------

if "investigation_result" not in st.session_state:
    st.session_state.investigation_result = None

if "approval_result" not in st.session_state:
    st.session_state.approval_result = None

if "customer_data" not in st.session_state:
    st.session_state.customer_data = []

if "loaded_customer_source" not in st.session_state:
    st.session_state.loaded_customer_source = None

if "ai_search_result" not in st.session_state:
    st.session_state.ai_search_result = None


# ---------------- SIDEBAR ----------------

st.sidebar.title("🧠 Retention AI")

st.sidebar.caption("Admin Control Panel")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Customers",
        "Investigation",
        "Human Approval",
        "AI Search"
    ]
)

st.sidebar.divider()

st.sidebar.write("Backend Connection")

if st.sidebar.button("Check API Status"):

    health = get_request("/health")

    if not isinstance(health, dict) or health.get("error"):

        st.sidebar.error("Backend disconnected")

    else:

        st.sidebar.success("Backend connected")


# ---------------- HEADER ----------------

st.title("Customer Retention Intelligence")

st.markdown(
    '<p class="dashboard-subtitle">'
    'Monitor customers, investigate churn risk and manage retention decisions.'
    '</p>',
    unsafe_allow_html=True
)

st.divider()


# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":

    st.subheader("Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("AI Agents", "4")
    col2.metric("Data Sources", "2")
    col3.metric("Decision Engine", "Active")
    col4.metric("Approval System", "Active")

    st.divider()

    st.subheader("System Modules")

    col1, col2 = st.columns(2)

    with col1:

        st.info("**Customer Profile Agent**")

        st.write(
            "Fetches customer information from available data sources."
        )

        st.info("**Churn Prediction Agent**")

        st.write(
            "Generates churn predictions and inactivity risk signals."
        )

        st.info("**Fulfilment Investigation Agent**")

        st.write(
            "Investigates available fulfilment-related customer evidence."
        )

    with col2:

        st.info("**Retention Strategy Agent**")

        st.write(
            "Generates suitable retention action candidates."
        )

        st.info("**Decision Engine**")

        st.write(
            "Evaluates actions against deterministic business policies."
        )

        st.info("**Human Approval & Execution**")

        st.write(
            "Manages admin approval and prepares approved actions for execution."
        )


# ============================================================
# CUSTOMERS
# ============================================================

elif page == "Customers":

    st.subheader("Customer Management")

    source = st.selectbox(
        "Select Data Source",
        ["olist", "telco"],
        key="customer_data_source"
    )

    if st.button("Load Customers", type="primary"):

        st.session_state.customer_data = []
        st.session_state.loaded_customer_source = None

        with st.spinner(f"Loading {source.upper()} customers..."):

            customers = get_request(
                f"/api/v1/customers/{source}"
            )

        if not isinstance(customers, dict):

            st.error("Invalid response received from backend.")

        elif customers.get("error") or customers.get("detail"):

            st.error(
                customers.get("error")
                or customers.get("detail")
            )

        else:

            st.session_state.customer_data = customers.get(
                "data", []
            )

            st.session_state.loaded_customer_source = source

            st.success(
                f"Loaded {customers.get('total_records', 0)} "
                f"{source.upper()} customer records."
            )

    customer_data = st.session_state.customer_data

    loaded_source = st.session_state.loaded_customer_source

    if customer_data:

        if loaded_source:

            st.caption(
                f"Showing records from: {loaded_source.upper()}"
            )

        df = pd.DataFrame(customer_data)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No customer records loaded. "
            "Select a data source and click Load Customers."
        )


# ============================================================
# INVESTIGATION
# ============================================================

elif page == "Investigation":

    st.subheader("Customer Investigation")

    source = st.selectbox(
        "Customer Source",
        ["olist", "telco"],
        key="investigation_source"
    )

    default_id = (
        "high_risk_loyalty_customer_003"
        if source == "olist"
        else "7590-VHVEG"
    )

    customer_id = st.text_input(
        "Customer ID",
        value=default_id,
        key="investigation_customer_id"
    )

    if st.button("Run Investigation", type="primary"):

        if not customer_id.strip():

            st.warning("Enter a valid customer ID.")

        else:

            payload = {
                "customer_id": customer_id.strip(),
                "source": source
            }

            st.session_state.investigation_result = None
            st.session_state.approval_result = None

            with st.spinner("Running AI investigation..."):

                result = post_request(
                    "/api/v1/customers/investigate",
                    payload
                )

            if not isinstance(result, dict):

                st.error("Invalid response received from backend.")

            elif result.get("error") or result.get("detail"):

                st.error(
                    result.get("error")
                    or result.get("detail")
                )

            else:

                returned_customer_id = str(
                    result.get("customer_id", "")
                ).strip()

                requested_customer_id = customer_id.strip()

                returned_source = result.get("source")

                if returned_customer_id != requested_customer_id:

                    st.error(
                        "Customer ID mismatch! "
                        f"Requested: {requested_customer_id} | "
                        f"Returned: {returned_customer_id}. "
                        "Investigation result rejected."
                    )

                elif returned_source != source:

                    st.error(
                        f"Data source mismatch! "
                        f"Requested: {source} | "
                        f"Returned: {returned_source}."
                    )

                else:

                    st.session_state.investigation_result = result

                    st.success(
                        "Investigation successfully processed."
                    )

                    if result.get("status") == "awaiting_approval":

                        st.warning(
                            "Investigation is waiting for admin approval. "
                            "Open Human Approval from the sidebar."
                        )

                    else:

                        st.success(
                            f"Investigation status: "
                            f"{result.get('status', 'unknown')}"
                        )

    result = st.session_state.investigation_result

    if result:

        st.divider()

        st.subheader("Investigation Results")

        status = result.get("status", "unknown")

        if status == "awaiting_approval":

            st.warning("Waiting for human approval")

        elif status == "completed":

            st.success("Investigation completed")

        else:

            st.info(f"Investigation status: {status}")

        col1, col2 = st.columns(2)

        col1.metric(
            "Customer ID",
            result.get("customer_id", "N/A")
        )

        col2.metric(
            "Data Source",
            str(result.get("source", "N/A")).upper()
        )

        if result.get("churn_prediction"):

            with st.expander(
                "Churn Prediction",
                expanded=True
            ):

                st.json(result["churn_prediction"])

        if (
            result.get("source") == "olist"
            and result.get("fulfilment_analysis")
        ):

            with st.expander("Fulfilment Investigation"):

                st.json(result["fulfilment_analysis"])

        if result.get("retention_strategy"):

            with st.expander(
                "Retention Strategy",
                expanded=True
            ):

                st.json(result["retention_strategy"])

        if result.get("policy_result"):

            with st.expander("Decision Engine Results"):

                st.json(result["policy_result"])

        if result.get("human_approval"):

            with st.expander("Human Approval Results"):

                st.json(result["human_approval"])

        if result.get("execution_result"):

            with st.expander("Execution Results"):

                st.json(result["execution_result"])

        if result.get("audit_record"):

            with st.expander("Audit Information"):

                st.json(result["audit_record"])

        if result.get("errors"):

            with st.expander("Workflow Errors"):

                for error in result["errors"]:

                    st.warning(str(error))

        if status == "awaiting_approval":

            st.info(
                "Open Human Approval from the sidebar "
                "to review the candidate actions."
            )


# ============================================================
# HUMAN APPROVAL
# ============================================================

elif page == "Human Approval":

    st.subheader("Human Approval Center")

    result = st.session_state.investigation_result

    if not result:

        st.warning(
            "Run a customer investigation first."
        )

    elif result.get("status") != "awaiting_approval":

        st.info(
            "No pending approval request."
        )

        if st.session_state.approval_result:

            st.subheader("Previous Approval Result")

            st.json(
                st.session_state.approval_result
            )

    else:

        thread_id = result.get("thread_id")

        if not thread_id:

            st.error(
                "Thread ID is missing. Cannot resume workflow."
            )

        else:

            st.caption(f"Thread ID: {thread_id}")

            st.write(
                "**Customer ID:**",
                result.get("customer_id")
            )

            st.write(
                "**Source:**",
                str(result.get("source", "")).upper()
            )

            approval_requests = result.get(
                "approval_request",
                []
            )

            pending_actions = []

            if isinstance(approval_requests, list):

                for approval_request in approval_requests:

                    if not isinstance(approval_request, dict):
                        continue

                    pending_actions.extend(
                        approval_request.get(
                            "pending_actions", []
                        )
                    )

            if not pending_actions:

                st.warning(
                    "No pending actions were received from the backend."
                )

                st.json(approval_requests)

            else:

                st.write(
                    f"**Pending actions:** {len(pending_actions)}"
                )

                decisions = []

                with st.form("approval_form"):

                    reviewer = st.text_input(
                        "Reviewer Name",
                        value="admin"
                    )

                    st.divider()

                    for item in pending_actions:

                        action = item.get("action", {})

                        if not isinstance(action, dict):
                            continue

                        action_index = item.get("action_index")

                        st.markdown(
                            f"### Action #{action_index}"
                        )

                        st.markdown(
                            f"**Action Type:** "
                            f"`{action.get('action_type', 'N/A')}`"
                        )

                        st.write(
                            "**Description:**",
                            action.get("description", "N/A")
                        )

                        st.write(
                            "**Reason:**",
                            action.get("reason", "N/A")
                        )

                        st.write(
                            "**Priority:**",
                            action.get("priority", "N/A")
                        )

                        st.write(
                            "**Policy Reason:**",
                            item.get("policy_reason", "N/A")
                        )

                        decision = st.radio(
                            "Your Decision",
                            ["approved", "rejected"],
                            index=None,
                            horizontal=True,
                            key=(
                                f"approval_{thread_id}_"
                                f"{action_index}"
                            )
                        )

                        decisions.append({
                            "action_index": action_index,
                            "decision": decision
                        })

                        st.divider()

                    submitted = st.form_submit_button(
                        "Submit Approval Decisions",
                        type="primary",
                        use_container_width=True
                    )

                if submitted:

                    if not reviewer.strip():

                        st.error(
                            "Reviewer name is required."
                        )

                    elif any(
                        item["decision"] is None
                        for item in decisions
                    ):

                        st.error(
                            "Please select approve or reject "
                            "for every pending action."
                        )

                    elif not decisions:

                        st.error(
                            "No valid approval decisions available."
                        )

                    else:

                        payload = {
                            "thread_id": thread_id,
                            "decisions": [
                                {
                                    **decision,
                                    "approved_by": reviewer.strip()
                                }
                                for decision in decisions
                            ]
                        }

                        with st.spinner(
                            "Processing admin decisions..."
                        ):

                            approval = post_request(
                                "/api/v1/customers/approve",
                                payload
                            )

                        if not isinstance(approval, dict):

                            st.error(
                                "Invalid approval response received."
                            )

                        elif (
                            approval.get("error")
                            or approval.get("detail")
                        ):

                            st.error(
                                approval.get("error")
                                or approval.get("detail")
                            )

                        else:

                            st.session_state.approval_result = approval

                            approval_status = approval.get(
                                "status"
                            )

                            if approval_status == "completed":

                                st.session_state.investigation_result = {
                                    **result,
                                    **approval,
                                    "status": "completed"
                                }

                                st.success(
                                    "All approval decisions processed successfully!"
                                )

                            elif approval_status == "awaiting_approval":

                                updated_result = {
                                    **result,
                                    "approval_request": approval.get(
                                        "approval_request",
                                        result.get("approval_request", [])
                                    )
                                }

                                st.session_state.investigation_result = (
                                    updated_result
                                )

                                st.warning(
                                    "Some actions are still waiting for approval."
                                )

                            else:

                                st.info(
                                    approval.get(
                                        "message",
                                        "Approval response received."
                                    )
                                )

            # ---------------- APPROVAL RESULT ----------------

            approval = st.session_state.approval_result

            if approval:

                st.divider()

                st.subheader("Approval Results")

                if approval.get("human_approval"):

                    st.write("Human Approval")

                    st.json(
                        approval["human_approval"]
                    )

                if approval.get("execution_result"):

                    st.write("Execution Status")

                    execution = approval["execution_result"]

                    st.metric(
                        "Execution",
                        execution.get("status", "N/A")
                    )

                    st.json(
                        execution.get("executed_actions", [])
                    )

                if approval.get("audit_record"):

                    st.write("Audit Record")

                    st.json(
                        approval["audit_record"]
                    )

                if approval.get("errors"):

                    st.write("Workflow Errors")

                    for error in approval["errors"]:

                        st.warning(str(error))


# ============================================================
# AI SEARCH
# ============================================================

elif page == "AI Search":

    st.subheader("AI Search")

    st.caption(
        "Ask questions about customers, churn, fulfilment and retention "
        "using connected MCP tools and the knowledge base."
    )

    question = st.text_area(
        "Enter your question",
        placeholder=(
            "Example: Find Olist customers inactive for more than 90 days."
        ),
        height=120,
        key="ai_search_question"
    )

    if st.button("Search", type="primary"):

        if not question.strip():

            st.warning(
                "Please enter a search question."
            )

        else:

            with st.spinner(
                "Searching customer data and knowledge base..."
            ):

                result = post_request(
                    "/api/v1/customers/ai-search",
                    {
                        "question": question.strip()
                    }
                )

            if not isinstance(result, dict):

                st.error(
                    "Invalid response received from backend."
                )

            elif result.get("error") or result.get("detail"):

                st.error(
                    result.get("error")
                    or result.get("detail")
                )

            else:

                st.session_state.ai_search_result = result

                st.success(
                    "AI Search completed."
                )

    search_result = st.session_state.ai_search_result

    if search_result:

        st.divider()

        st.subheader("Search Results")

        answer = search_result.get("answer")

        if answer:

            st.markdown(answer)

        else:

            st.info(
                "No answer was returned."
            )

        sources = search_result.get("sources", [])

        if sources:

            with st.expander(
                "Sources and Evidence",
                expanded=True
            ):

                for index, source in enumerate(
                    sources,
                    start=1
                ):

                    st.markdown(
                        f"**Source {index}**"
                    )

                    if isinstance(source, dict):

                        st.json(source)

                    else:

                        st.write(source)

        errors = search_result.get("errors", [])

        if errors:

            with st.expander("Search Warnings"):

                for error in errors:

                    st.warning(str(error))

        if search_result.get("thread_id"):

            st.caption(
                f"Thread ID: {search_result['thread_id']}"
            )
