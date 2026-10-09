"""Reusable visualizations for motor insurance analysis."""

import matplotlib.pyplot as plt
import pandas as pd


def _bar_plot(series, title, xlabel, ylabel, rotation=0, figsize=(8, 4)):
    """Create and return a labeled bar chart."""
    fig, ax = plt.subplots(figsize=figsize)
    series.plot(kind="bar", ax=ax, color="steelblue")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=rotation)
    fig.tight_layout()
    return fig


def plot_policy_status(data):
    """Plot policy counts by status."""
    counts = data["policies"]["policy_status"].value_counts()
    return _bar_plot(counts, "Policies by Status", "Policy Status", "Policies")


def plot_policy_type_distribution(data):
    """Plot policy counts by type."""
    counts = data["policies"]["policy_type"].value_counts()
    return _bar_plot(counts, "Policies by Type", "Policy Type", "Policies", 20)


def plot_premium_by_policy_type(data):
    """Plot total premium by policy type."""
    totals = data["policies"].groupby("policy_type")["premium_amount"].sum()
    return _bar_plot(
        totals, "Total Premium by Policy Type", "Policy Type", "Total Premium", 20
    )


def plot_monthly_claims(data):
    """Plot unique claims by claim month."""
    claims = data["claims"].copy()
    claims["claim_date"] = pd.to_datetime(claims["claim_date"], errors="coerce")
    monthly = (
        claims.dropna(subset=["claim_date"])
        .assign(month=lambda df: df["claim_date"].dt.to_period("M").astype(str))
        .groupby("month")["claim_id"]
        .nunique()
    )

    fig, ax = plt.subplots(figsize=(10, 4))
    monthly.plot(kind="line", marker="o", ax=ax)
    ax.set_title("Monthly Claim Volume")
    ax.set_xlabel("Claim Month")
    ax.set_ylabel("Number of Claims")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    return fig


def plot_claim_status(data):
    """Plot claim counts by status."""
    counts = data["claims"]["claim_status"].value_counts()
    return _bar_plot(counts, "Claims by Status", "Claim Status", "Claims", 15)


def plot_claim_type_distribution(data):
    """Plot claim counts by claim type."""
    counts = data["claims"]["claim_type"].value_counts()
    return _bar_plot(counts, "Claims by Type", "Claim Type", "Claims", 25)


def plot_claim_amount_distribution(data):
    """Plot the distribution of claim amounts."""
    fig, ax = plt.subplots(figsize=(8, 4))
    data["claims"]["claim_amount"].dropna().plot(
        kind="hist", bins=30, ax=ax, color="cornflowerblue", edgecolor="white"
    )
    ax.set_title("Distribution of Claim Amounts")
    ax.set_xlabel("Claim Amount")
    ax.set_ylabel("Number of Claims")
    fig.tight_layout()
    return fig


def _claims_with_vehicle(data):
    """Join claims to vehicle attributes using policy and vehicle IDs."""
    return (
        data["claims"].merge(
            data["policies"][["policy_id", "vehicle_id"]],
            on="policy_id",
            how="left",
            validate="many_to_one",
        ).merge(
            data["vehicles"][
                ["vehicle_id", "vehicle_type", "vehicle_make", "vehicle_year"]
            ],
            on="vehicle_id",
            how="left",
            validate="many_to_one",
        )
    )


def plot_claim_amount_by_vehicle_type(data):
    """Plot average claim amount by vehicle type."""
    joined = _claims_with_vehicle(data)
    average = joined.groupby("vehicle_type")["claim_amount"].mean()
    return _bar_plot(
        average,
        "Average Claim Amount by Vehicle Type",
        "Vehicle Type",
        "Average Claim Amount",
    )


def plot_claims_by_region(data):
    """Plot unique claim counts by customer state."""
    joined = data["claims"].merge(
        data["customers"][["customer_id", "state"]],
        on="customer_id",
        how="left",
        validate="many_to_one",
    )
    counts = joined.groupby("state")["claim_id"].nunique().sort_values(
        ascending=False
    )
    return _bar_plot(
        counts, "Claims by State", "State", "Number of Claims", 45, (10, 5)
    )


def plot_claim_severity_by_region(data):
    """Plot average claim amount by state and damage severity."""
    joined = data["claims"].merge(
        data["customers"][["customer_id", "state"]],
        on="customer_id",
        how="left",
        validate="many_to_one",
    )
    grouped = joined.pivot_table(
        index="state",
        columns="damage_severity",
        values="claim_amount",
        aggfunc="mean",
    )

    fig, ax = plt.subplots(figsize=(11, 5))
    grouped.plot(kind="bar", ax=ax)
    ax.set_title("Average Claim Amount by State and Damage Severity")
    ax.set_xlabel("State")
    ax.set_ylabel("Average Claim Amount")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    return fig


def plot_average_settlement_time(data):
    """Plot average settlement days by claim status."""
    claims = data["claims"].copy()

    if "claim_settlement_days" not in claims.columns:
        claims["claim_date"] = pd.to_datetime(
            claims["claim_date"], errors="coerce"
        )
        claims["settlement_date"] = pd.to_datetime(
            claims["settlement_date"], errors="coerce"
        )
        claims["claim_settlement_days"] = (
            claims["settlement_date"] - claims["claim_date"]
        ).dt.days

    averages = claims.groupby("claim_status")["claim_settlement_days"].mean()
    averages = averages.dropna()
    return _bar_plot(
        averages,
        "Average Settlement Time by Claim Status",
        "Claim Status",
        "Average Days",
    )


def plot_claim_to_premium_by_policy_type(data):
    """Plot total claim amount divided by total premium by policy type."""
    policies = data["policies"]
    claims_with_type = data["claims"].merge(
        policies[["policy_id", "policy_type"]],
        on="policy_id",
        how="left",
        validate="many_to_one",
    )

    claim_totals = claims_with_type.groupby("policy_type")[
        "claim_amount"
    ].sum()
    premium_totals = policies.groupby("policy_type")["premium_amount"].sum()
    ratio = (claim_totals / premium_totals).sort_values(ascending=False)

    return _bar_plot(
        ratio,
        "Claim Amount to Premium Ratio by Policy Type",
        "Policy Type",
        "Total Claims / Total Premium",
        20,
    )


def plot_vehicle_age_vs_claim_amount(data):
    """Plot average claim amount by vehicle age."""
    joined = _claims_with_vehicle(data)
    joined["vehicle_age"] = (
        pd.Timestamp.today().year - joined["vehicle_year"]
    )
    averages = joined.groupby("vehicle_age")["claim_amount"].mean().sort_index()

    fig, ax = plt.subplots(figsize=(8, 4))
    averages.plot(kind="line", marker="o", ax=ax)
    ax.set_title("Average Claim Amount by Vehicle Age")
    ax.set_xlabel("Vehicle Age (Years)")
    ax.set_ylabel("Average Claim Amount")
    fig.tight_layout()
    return fig


def plot_customer_age_vs_claim_amount(data):
    """Plot average claim amount by customer age group."""
    joined = data["claims"].merge(
        data["customers"][["customer_id", "customer_age"]],
        on="customer_id",
        how="left",
        validate="many_to_one",
    )
    joined["customer_age_group"] = pd.cut(
        joined["customer_age"],
        bins=[0, 25, 35, 45, 55, 100],
        labels=["18-25", "26-35", "36-45", "46-55", "56+"],
    )
    averages = joined.groupby(
        "customer_age_group", observed=False
    )["claim_amount"].mean()

    return _bar_plot(
        averages,
        "Average Claim Amount by Customer Age Group",
        "Customer Age Group",
        "Average Claim Amount",
    )


def plot_vehicle_type_claim_performance(data):
    """Plot claim count by vehicle type."""
    joined = _claims_with_vehicle(data)
    counts = joined.groupby("vehicle_type")["claim_id"].nunique()
    return _bar_plot(
        counts,
        "Claim Performance by Vehicle Type",
        "Vehicle Type",
        "Number of Claims",
    )


def plot_damage_severity_distribution(data):
    """Plot claims by damage severity."""
    counts = data["claims"]["damage_severity"].value_counts()
    return _bar_plot(
        counts, "Claims by Damage Severity", "Damage Severity", "Claims"
    )


def plot_payment_status(data):
    """Plot payment record counts by payment status."""
    counts = data["payments"]["payment_status"].value_counts()
    return _bar_plot(counts, "Payments by Status", "Payment Status", "Payments")


def plot_monthly_premium_trend(data):
    """Plot premium totals by policy start month."""
    policies = data["policies"].copy()
    policies["policy_start_date"] = pd.to_datetime(
        policies["policy_start_date"], errors="coerce"
    )

    monthly = (
        policies.dropna(subset=["policy_start_date"])
        .assign(
            month=lambda df: df["policy_start_date"]
            .dt.to_period("M")
            .astype(str)
        )
        .groupby("month")["premium_amount"]
        .sum()
    )

    fig, ax = plt.subplots(figsize=(10, 4))
    monthly.plot(kind="line", marker="o", ax=ax)
    ax.set_title("Monthly Premium Trend by Policy Start Date")
    ax.set_xlabel("Policy Start Month")
    ax.set_ylabel("Total Premium")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    return fig