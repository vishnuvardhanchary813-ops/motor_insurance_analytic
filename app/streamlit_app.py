"""Streamlit dashboard for motor insurance analytics."""

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


# Make the project root importable when Streamlit starts this file.
PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from src import insights, visualization


st.set_page_config(
    page_title="Motor Insurance Analytics",
    page_icon="🚗",
    layout="wide",
)


@st.cache_data
def load_dashboard_data():
    """Load cleaned data tables and parse their date columns."""
    cleaned_dir = PROJECT_DIR / "data" / "cleaned"
    names = ["customers", "policies", "vehicles", "claims", "payments"]

    data = {}
    for name in names:
        file_path = cleaned_dir / f"{name}_cleaned.csv"
        if not file_path.exists():
            raise FileNotFoundError(f"Cleaned data file not found: {file_path}")
        data[name] = pd.read_csv(file_path)

    date_columns = {
        "customers": ["date_of_birth"],
        "policies": ["policy_start_date", "policy_end_date"],
        "claims": [
            "claim_date", "accident_date", "approval_date", "settlement_date"
        ],
        "payments": ["payment_date"],
    }

    for table, columns in date_columns.items():
        for column in columns:
            data[table][column] = pd.to_datetime(
                data[table][column], errors="coerce"
            )

    return data


def _all_selected(label, series):
    """Show a multiselect defaulting to all values."""
    options = sorted(series.dropna().unique().tolist())
    return st.sidebar.multiselect(label, options, default=options)


def show_sidebar_filters(data):
    """Collect filter choices and return related filtered tables."""
    st.sidebar.header("Filters")

    customers = data["customers"].copy()
    vehicles = data["vehicles"].copy()
    policies = data["policies"].copy()
    claims = data["claims"].copy()
    payments = data["payments"].copy()

    policy_types = _all_selected("Policy Type", policies["policy_type"])
    policy_statuses = _all_selected("Policy Status", policies["policy_status"])
    claim_statuses = _all_selected("Claim Status", claims["claim_status"])
    claim_types = _all_selected("Claim Type", claims["claim_type"])
    vehicle_types = _all_selected("Vehicle Type", vehicles["vehicle_type"])
    vehicle_makes = _all_selected("Vehicle Make", vehicles["vehicle_make"])
    states = _all_selected("State", customers["state"])
    cities = _all_selected("City", customers["city"])
    severities = _all_selected("Damage Severity", claims["damage_severity"])

    customers = customers[
        customers["state"].isin(states) & customers["city"].isin(cities)
    ]

    vehicles = vehicles[
        vehicles["vehicle_type"].isin(vehicle_types)
        & vehicles["vehicle_make"].isin(vehicle_makes)
    ]

    policies = policies[
        policies["policy_type"].isin(policy_types)
        & policies["policy_status"].isin(policy_statuses)
        & policies["vehicle_id"].isin(vehicles["vehicle_id"])
        & policies["customer_id"].isin(customers["customer_id"])
    ]

    claims["claim_date"] = pd.to_datetime(claims["claim_date"], errors="coerce")
    valid_dates = claims["claim_date"].dropna()

    if not valid_dates.empty:
        selected_dates = st.sidebar.date_input(
            "Claim Date Range",
            value=(valid_dates.min().date(), valid_dates.max().date()),
            min_value=valid_dates.min().date(),
            max_value=valid_dates.max().date(),
        )

        if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
            start_date, end_date = selected_dates
            claims = claims[
                claims["claim_date"].between(
                    pd.Timestamp(start_date),
                    pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1),
                )
            ]

    claims = claims[
        claims["policy_id"].isin(policies["policy_id"])
        & claims["claim_status"].isin(claim_statuses)
        & claims["claim_type"].isin(claim_types)
        & claims["damage_severity"].isin(severities)
    ]

    # Keep only related payment, vehicle, and customer rows.
    payments = payments[payments["claim_id"].isin(claims["claim_id"])]

    related_vehicle_ids = set(policies["vehicle_id"])
    vehicles = vehicles[vehicles["vehicle_id"].isin(related_vehicle_ids)]

    related_customer_ids = (
        set(policies["customer_id"]) | set(claims["customer_id"])
    )
    customers = customers[customers["customer_id"].isin(related_customer_ids)]

    return {
        "customers": customers,
        "policies": policies,
        "vehicles": vehicles,
        "claims": claims,
        "payments": payments,
    }


def show_kpis(data):
    """Show key portfolio and claim KPIs for the current filters."""
    policies = data["policies"]
    claims = data["claims"]

    total_claims = claims["claim_id"].nunique()
    approved_claims = claims["claim_status"].eq("Approved").sum()
    approval_rate = (
        approved_claims / total_claims * 100 if total_claims else 0
    )

    if "claim_settlement_days" in claims.columns:
        settlement_days = pd.to_numeric(
            claims["claim_settlement_days"], errors="coerce"
        ).dropna()
    else:
        settlement_days = pd.Series(dtype=float)

    average_settlement = (
        settlement_days.mean() if not settlement_days.empty else 0
    )

    columns = st.columns(6)
    columns[0].metric("Total Policies", f"{policies['policy_id'].nunique():,}")
    columns[1].metric(
        "Active Policies",
        f"{policies['policy_status'].eq('Active').sum():,}",
    )
    columns[2].metric(
        "Total Premium",
        f"{policies['premium_amount'].sum():,.2f}",
    )
    columns[3].metric("Total Claims", f"{total_claims:,}")
    columns[4].metric(
        "Total Claim Amount",
        f"{claims['claim_amount'].sum():,.2f}",
    )
    columns[5].metric("Approval Rate", f"{approval_rate:.2f}%")

    st.metric("Average Settlement Days", f"{average_settlement:.2f}")


def show_chart(data, chart_function):
    """Display a chart returned by a visualization function."""
    fig = chart_function(data)
    st.pyplot(fig, clear_figure=True)
    plt.close(fig)


def show_insights(data):
    """Display data-driven findings with evidence and recommendations."""
    generators = [
        insights.generate_portfolio_insights,
        insights.generate_claim_insights,
        insights.generate_premium_insights,
        insights.generate_customer_insights,
        insights.generate_vehicle_insights,
        insights.generate_risk_patterns,
    ]

    findings = []
    for generator in generators:
        findings.extend(generator(data))

    if not findings:
        st.info("No insights are available for the current filter selection.")
        return

    for finding in findings:
        with st.container(border=True):
            st.markdown(f"**Pattern:** {finding['pattern']}")
            st.markdown(f"**Evidence:** {finding['evidence']}")
            st.markdown(f"**Business Meaning:** {finding['business_meaning']}")
            st.markdown(f"**Recommendation:** {finding['recommendation']}")


def main():
    """Build and display the Streamlit dashboard."""
    st.title("Motor Insurance Analytics")
    st.caption(
        "Explore policies, premiums, claims, customers, vehicles, and risk."
    )

    try:
        full_data = load_dashboard_data()
    except (FileNotFoundError, pd.errors.EmptyDataError) as error:
        st.error(f"Could not load cleaned data: {error}")
        st.stop()

    data = show_sidebar_filters(full_data)

    page = st.sidebar.selectbox(
        "Dashboard Page",
        [
            "Executive Overview",
            "Policy Analysis",
            "Claims Analysis",
            "Customer Analysis",
            "Vehicle Analysis",
            "Premium & Risk",
            "Insights & Recommendations",
        ],
    )

    if page == "Executive Overview":
        show_kpis(data)
        st.subheader("Policy Status")
        show_chart(data, visualization.plot_policy_status)
        st.subheader("Monthly Claims")
        show_chart(data, visualization.plot_monthly_claims)

    elif page == "Policy Analysis":
        st.subheader("Policy Status")
        show_chart(data, visualization.plot_policy_status)
        st.subheader("Policy Type Distribution")
        show_chart(data, visualization.plot_policy_type_distribution)
        st.subheader("Premium by Policy Type")
        show_chart(data, visualization.plot_premium_by_policy_type)
        st.subheader("Monthly Premium Trend")
        show_chart(data, visualization.plot_monthly_premium_trend)

    elif page == "Claims Analysis":
        st.subheader("Monthly Claims")
        show_chart(data, visualization.plot_monthly_claims)
        st.subheader("Claim Status")
        show_chart(data, visualization.plot_claim_status)
        st.subheader("Claim Type")
        show_chart(data, visualization.plot_claim_type_distribution)
        st.subheader("Claim Amount Distribution")
        show_chart(data, visualization.plot_claim_amount_distribution)
        st.subheader("Claims by State")
        show_chart(data, visualization.plot_claims_by_region)
        st.subheader("Severity by State")
        show_chart(data, visualization.plot_claim_severity_by_region)
        st.subheader("Average Settlement Time")
        show_chart(data, visualization.plot_average_settlement_time)
        st.subheader("Damage Severity Distribution")
        show_chart(data, visualization.plot_damage_severity_distribution)

    elif page == "Customer Analysis":
        st.subheader("Claim Amount by Customer Age")
        show_chart(data, visualization.plot_customer_age_vs_claim_amount)

    elif page == "Vehicle Analysis":
        st.subheader("Claim Amount by Vehicle Type")
        show_chart(data, visualization.plot_claim_amount_by_vehicle_type)
        st.subheader("Claim Amount by Vehicle Age")
        show_chart(data, visualization.plot_vehicle_age_vs_claim_amount)
        st.subheader("Vehicle Type Claim Performance")
        show_chart(data, visualization.plot_vehicle_type_claim_performance)

    elif page == "Premium & Risk":
        st.subheader("Claim Amount to Premium by Policy Type")
        show_chart(data, visualization.plot_claim_to_premium_by_policy_type)

    elif page == "Insights & Recommendations":
        show_insights(data)

    st.sidebar.caption(
        "Vehicle type comparisons may be limited because this dataset "
        "contains only cars."
    )


if __name__ == "__main__":
    main()