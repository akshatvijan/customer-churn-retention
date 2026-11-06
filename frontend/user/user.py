import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd

from frontend.shared.api_client import get_request

# ---------------- PAGE CONFIGURATION ----------------

st.set_page_config(
    page_title="My Customer Portal",
    page_icon="🛍️",
    layout="wide"
)


# ---------------- SESSION STATE ----------------

if "customer_profile" not in st.session_state:
    st.session_state.customer_profile = None

if "customer_id" not in st.session_state:
    st.session_state.customer_id = ""


# ---------------- CUSTOM CSS ----------------

st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
    }

    .welcome-card {
        background: linear-gradient(120deg, #1e3a8a, #2563eb);
        padding: 30px;
        border-radius: 15px;
        color: white;
        margin-bottom: 20px;
    }

    .welcome-card h2 {
        color: white;
    }

    .welcome-card p {
        color: #dbeafe;
    }

    .reward-card {
        background: linear-gradient(120deg, #14532d, #16a34a);
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
        color: #dcfce7;
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

st.sidebar.title("🛍️ My Account")

page = st.sidebar.radio(
    "Navigation",
    [
        "Home",
        "My Profile",
        "My Orders",
        "Offers & Rewards",
        "Recommendations"
    ]
)

st.sidebar.divider()
st.sidebar.caption("Customer Portal")


# ---------------- HEADER ----------------

st.title("My Customer Portal")

st.caption(
    "Your shopping experience, orders and customer services in one place."
)

st.divider()


# ---------------- CUSTOMER LOOKUP ----------------

if st.session_state.customer_profile is None:

    st.subheader("Find Your Customer Profile")

    st.info(
        "Enter your Olist customer ID to view your customer information."
    )

    customer_id = st.text_input(
        "Customer ID",
        placeholder="Enter your customer ID"
    )

    if st.button("Load My Profile", type="primary"):

        if not customer_id.strip():

            st.warning("Please enter your customer ID.")

        else:

            with st.spinner("Loading customer profile..."):

                response = get_request(
                    f"/api/v1/customers/olist/profile/{customer_id.strip()}"
                )

            if (
                isinstance(response, dict)
                and response.get("success")
                and isinstance(response.get("customer_data"), dict)
            ):

                st.session_state.customer_profile = response["customer_data"]
                st.session_state.customer_id = customer_id.strip()

                st.rerun()

            else:

                error_message = (
                    response.get("detail")
                    or response.get("error")
                    or "Customer not found."
                    if isinstance(response, dict)
                    else "Unable to load customer profile."
                )

                st.error(error_message)


# ---------------- CUSTOMER DASHBOARD ----------------

else:

    customer = st.session_state.customer_profile
    customer_id = st.session_state.customer_id

    # ---------------- CHANGE CUSTOMER ----------------

    if st.sidebar.button("Change Customer"):

        st.session_state.customer_profile = None
        st.session_state.customer_id = ""

        st.rerun()


    # ---------------- FETCH APPROVED ACTIONS ----------------

    retention_response = get_request(
        f"/api/v1/customers/{customer_id}/retention-actions?source=olist"
    )

    if (
        not isinstance(retention_response, dict)
        or retention_response.get("error")
        or retention_response.get("detail")
    ):

        approved_actions = []

        retention_error = (
            retention_response.get("error")
            or retention_response.get("detail")
            or "Unable to load approved actions."
            if isinstance(retention_response, dict)
            else "Unable to load approved actions."
        )

    else:

        approved_actions = retention_response.get("data", [])
        retention_error = None


    # ---------------- APPROVED LOYALTY REWARDS ----------------

    approved_rewards = [
        item for item in approved_actions
        if item.get("action_type") == "loyalty_reward"
    ]


    # ---------------- HOME ----------------

    if page == "Home":

        st.markdown("""
        <div class="welcome-card">
            <h2>Welcome Back!</h2>
            <p>Your customer account overview</p>
        </div>
        """, unsafe_allow_html=True)

        st.subheader("Your Account Overview")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total Orders",
            customer.get("total_orders", "N/A")
        )

        col2.metric(
            "Delivered Orders",
            customer.get("delivered_orders", "N/A")
        )

        col3.metric(
            "Cancelled Orders",
            customer.get("cancelled_orders", "N/A")
        )

        st.divider()

        st.subheader("Account Information")

        st.write("Customer ID:", customer_id)

        st.write(
            "Last Order Date:",
            customer.get("last_order_date", "N/A")
        )

        st.write(
            "Average Order Value:",
            customer.get("average_order_value", "N/A")
        )

        st.write(
            "Days Since Last Order:",
            customer.get("days_since_last_order", "N/A")
        )

        st.info(
            "This overview displays information available in your "
            "customer account dataset."
        )


    # ---------------- MY PROFILE ----------------

    elif page == "My Profile":

        st.subheader("My Profile")

        st.write("Customer ID:", customer_id)

        st.write(
            "Total Orders:",
            customer.get("total_orders", "N/A")
        )

        st.write(
            "Last Order Date:",
            customer.get("last_order_date", "N/A")
        )

        st.write(
            "Average Order Value:",
            customer.get("average_order_value", "N/A")
        )

        st.write(
            "Delivered Orders:",
            customer.get("delivered_orders", "N/A")
        )

        st.write(
            "Cancelled Orders:",
            customer.get("cancelled_orders", "N/A")
        )

        st.write(
            "Days Since Last Order:",
            customer.get("days_since_last_order", "N/A")
        )

        st.write(
            "Retention Risk:",
            customer.get("retention_risk_proxy", "N/A")
        )


    # ---------------- MY ORDERS ----------------

    elif page == "My Orders":

        st.subheader("My Orders")

        st.write(
            "Available order summary from the customer dataset."
        )

        order_data = {
            "Order Metric": [
                "Total Orders",
                "Delivered Orders",
                "Cancelled Orders"
            ],
            "Value": [
                customer.get("total_orders", 0),
                customer.get("delivered_orders", 0),
                customer.get("cancelled_orders", 0)
            ]
        }

        st.dataframe(
            pd.DataFrame(order_data),
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "Individual order IDs and item-level history are not "
            "currently exposed by the customer API."
        )


    # ---------------- OFFERS AND REWARDS ----------------

    elif page == "Offers & Rewards":

        st.subheader("🎁 My Offers & Rewards")

        st.caption(
            "View loyalty rewards approved for your customer account."
        )

        if st.button("Refresh Offers"):

            st.rerun()

        if retention_error:

            st.error(retention_error)

        elif approved_rewards:

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


    # ---------------- RECOMMENDATIONS ----------------

    elif page == "Recommendations":

        st.subheader("Personalised Recommendations")

        st.caption(
            "View product recommendations approved for your account."
        )

        recommendation_actions = [
            item for item in approved_actions
            if item.get("action_type") == "product_recommendation"
        ]

        if retention_error:

            st.error(retention_error)

        elif recommendation_actions:

            for item in recommendation_actions:

                with st.container(border=True):

                    st.markdown("### Recommended for You")

                    st.write(
                        item.get(
                            "description",
                            "Recommendation details are not available."
                        )
                    )

        else:

            st.info(
                "No approved product recommendations are currently "
                "available for your account."
            )


# ---------------- FOOTER ----------------

st.divider()

st.caption(
    "Customer Retention Intelligence | Customer Portal"
)
