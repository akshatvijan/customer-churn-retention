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
    page_title="Telco Customer Portal",
    page_icon="📱",
    layout="wide"
)


# ---------------- SESSION STATE ----------------

if "telco_customer_profile" not in st.session_state:
    st.session_state.telco_customer_profile = None

if "telco_customer_id" not in st.session_state:
    st.session_state.telco_customer_id = ""


# ---------------- CUSTOM CSS ----------------

st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
    }

    .welcome-card {
        background: linear-gradient(120deg, #164e63, #0891b2);
        padding: 25px;
        border-radius: 15px;
        color: white;
        margin-bottom: 20px;
    }

    .welcome-card h2 {
        color: white;
    }

    .welcome-card p {
        color: #cffafe;
    }

    .reward-card {
        background: linear-gradient(120deg, #164e63, #0891b2);
        padding: 25px;
        border-radius: 15px;
        color: white;
        margin-bottom: 18px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }

    .reward-card h2 {
        color: white;
        margin-bottom: 12px;
    }

    .reward-card p {
        color: #cffafe;
        font-size: 16px;
    }

    .reward-status {
        display: inline-block;
        background: rgba(255,255,255,0.2);
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


# ---------------- SIDEBAR ----------------

st.sidebar.title("📱 My Telco Account")

page = st.sidebar.radio(
    "Navigation",
    [
        "My Profile",
        "My Services",
        "Offers & Rewards"
    ]
)

st.sidebar.divider()
st.sidebar.caption("Telco Customer Portal")


# ---------------- HEADER ----------------

st.title("My Telco Customer Portal")

st.caption(
    "View your personal information, active services and approved rewards."
)

st.divider()


# ---------------- CUSTOMER LOOKUP ----------------

if st.session_state.telco_customer_profile is None:

    st.subheader("Find Your Telco Account")

    st.info(
        "Enter your Telco Customer ID to access your account."
    )

    customer_id = st.text_input(
        "Telco Customer ID",
        placeholder="Example: 7590-VHVEG"
    )

    if st.button("Load My Account", type="primary"):

        if not customer_id.strip():

            st.warning("Please enter your Customer ID.")

        else:

            with st.spinner("Loading your account..."):

                response = get_request(
                    f"/api/v1/customers/telco/profile/{customer_id.strip()}"
                )

            if (
                isinstance(response, dict)
                and response.get("success")
                and isinstance(response.get("customer_data"), dict)
            ):

                customer = response["customer_data"]

                returned_id = (
                    customer.get("customer_id")
                    or customer.get("customerID")
                )

                if returned_id != customer_id.strip():

                    st.error("Customer ID verification failed.")

                else:

                    st.session_state.telco_customer_profile = customer
                    st.session_state.telco_customer_id = customer_id.strip()

                    st.rerun()

            else:

                error_message = (
                    response.get("detail")
                    or response.get("error")
                    or response.get("message")
                    or "Customer not found."
                    if isinstance(response, dict)
                    else "Unable to load customer profile."
                )

                st.error(error_message)


# ---------------- CUSTOMER DASHBOARD ----------------

else:

    customer = st.session_state.telco_customer_profile
    customer_id = st.session_state.telco_customer_id

    if st.sidebar.button("Change Customer"):

        st.session_state.telco_customer_profile = None
        st.session_state.telco_customer_id = ""

        st.rerun()


    # ---------------- MY PROFILE ----------------

    if page == "My Profile":

        st.markdown("""
        <div class="welcome-card">
            <h2>My Profile</h2>
            <p>Your personal Telco account information</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:

            st.write("**Customer ID:**", customer_id)
            st.write("**Gender:**", customer.get("gender", "N/A"))
            st.write("**Senior Citizen:**", customer.get("SeniorCitizen", "N/A"))

        with col2:

            st.write("**Partner:**", customer.get("Partner", "N/A"))
            st.write("**Dependents:**", customer.get("Dependents", "N/A"))
            st.write("**Tenure:**", customer.get("tenure", "N/A"), "months")


    # ---------------- MY SERVICES ----------------

    elif page == "My Services":

        st.markdown("""
        <div class="welcome-card">
            <h2>My Services</h2>
            <p>Services associated with your Telco account</p>
        </div>
        """, unsafe_allow_html=True)

        service_fields = {
            "Phone Service": "PhoneService",
            "Multiple Lines": "MultipleLines",
            "Internet Service": "InternetService",
            "Online Security": "OnlineSecurity",
            "Online Backup": "OnlineBackup",
            "Device Protection": "DeviceProtection",
            "Tech Support": "TechSupport",
            "Streaming TV": "StreamingTV",
            "Streaming Movies": "StreamingMovies"
        }

        service_data = []

        for service_name, field_name in service_fields.items():

            value = customer.get(field_name)

            service_data.append({
                "Service": service_name,
                "Status": value if value not in (None, "") else "N/A"
            })

        st.dataframe(
            pd.DataFrame(service_data),
            use_container_width=True,
            hide_index=True
        )


    # ---------------- OFFERS & REWARDS ----------------

    elif page == "Offers & Rewards":

        st.markdown("""
        <div class="welcome-card">
            <h2>🎁 Offers & Rewards</h2>
            <p>Your approved loyalty rewards</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Refresh Offers"):

            st.rerun()

        retention_response = get_request(
            f"/api/v1/customers/{customer_id}/retention-actions?source=telco"
        )

        if (
            not isinstance(retention_response, dict)
            or retention_response.get("error")
            or retention_response.get("detail")
        ):

            st.error(
                retention_response.get("error")
                or retention_response.get("detail")
                or "Unable to load offers."
                if isinstance(retention_response, dict)
                else "Unable to load offers."
            )

        else:

            approved_actions = retention_response.get("data", [])

            approved_rewards = [
                item for item in approved_actions
                if item.get("action_type") == "loyalty_reward"
            ]

            if approved_rewards:

                st.success(
                    f"{len(approved_rewards)} approved reward(s) available."
                )

                for item in approved_rewards:

                    description = item.get(
                        "description",
                        "Reward details are not available."
                    )

                    st.markdown(
                        f"""
                        <div class="reward-card">
                            <h2>🎁 Special Loyalty Reward</h2>
                            <p>{description}</p>
                            <span class="reward-status">
                                ✓ Approved by Admin
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            else:

                st.info(
                    "No approved offers or rewards are currently available "
                    "for your account."
                )


# ---------------- FOOTER ----------------

st.divider()

st.caption(
    "Customer Retention Intelligence | Telco Customer Portal"
)
