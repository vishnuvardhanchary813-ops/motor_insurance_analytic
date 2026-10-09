"""KPI and business analysis functions for motor insurance."""

import pandas as pd


def _count_status(df, column, status):
    """Count rows matching a status."""
    return int(df[column].eq(status).sum())


def _safe_ratio(numerator, denominator):
    """Return a ratio, or zero when its denominator is zero."""
    return float(numerator / denominator) if denominator else 0.0


# Portfolio KPIs

def calculate_total_customers(data):
    """Return the number of unique customers."""
    return int(data["customers"]["customer_id"].nunique())


def calculate_total_policies(data):
    """Return the number of unique policies."""
    return int(data["policies"]["policy_id"].nunique())


def calculate_active_policies(data):
    """Return the number of active policies."""
    return _count_status(data["policies"], "policy_status", "Active")


def calculate_expired_policies(data):
    """Return the number of expired policies."""
    return _count_status(data["policies"], "policy_status", "Expired")


def calculate_cancelled_policies(data):
    """Return the number of cancelled policies."""
    return _count_status(data["policies"], "policy_status", "Cancelled")


def calculate_renewed_policies(data):
    """Return the number of renewed policies."""
    return _count_status(data["policies"], "policy_status", "Renewed")


# Premium KPIs

def calculate_total_premium(data):
    """Return total premium across policies, counting each policy once."""
    return float(data["policies"]["premium_amount"].sum())


def calculate_average_premium(data):
    """Return average premium per policy."""
    return float(data["policies"]["premium_amount"].mean())


def calculate_average_coverage(data):
    """Return average coverage amount per policy."""
    return float(data["policies"]["coverage_amount"].mean())


def calculate_premium_by_policy_type(data):
    """Return policy count and premium measures by policy type."""
    policies = data["policies"]
    return policies.groupby("policy_type").agg(
        policy_count=("policy_id", "nunique"),
        total_premium=("premium_amount", "sum"),
        average_premium=("premium_amount", "mean"),
    ).sort_values("total_premium", ascending=False)


# Claims KPIs

def calculate_total_claims(data):
    """Return the number of unique claims."""
    return int(data["claims"]["claim_id"].nunique())


def calculate_approved_claims(data):
    """Count claims whose status is Approved."""
    return _count_status(data["claims"], "claim_status", "Approved")


def calculate_rejected_claims(data):
    """Count claims whose status is Rejected."""
    return _count_status(data["claims"], "claim_status", "Rejected")


def calculate_pending_claims(data):
    """Count claims whose status is Pending."""
    return _count_status(data["claims"], "claim_status", "Pending")


def calculate_total_claim_amount(data):
    """Return total requested claim amount."""
    return float(data["claims"]["claim_amount"].sum())


def calculate_average_claim_amount(data):
    """Return average requested claim amount."""
    return float(data["claims"]["claim_amount"].mean())


def calculate_claim_approval_rate(data):
    """Return Approved claims as a percentage of all claims."""
    return _safe_ratio(
        calculate_approved_claims(data),
        calculate_total_claims(data),
    ) * 100


def calculate_claim_rejection_rate(data):
    """Return Rejected claims as a percentage of all claims."""
    return _safe_ratio(
        calculate_rejected_claims(data),
        calculate_total_claims(data),
    ) * 100


# Settlement and payment KPIs

def _average_days(data, column, start_column, end_column):
    """Calculate average elapsed days, using a derived column if available."""
    claims = data["claims"]

    if column in claims.columns:
        days = pd.to_numeric(claims[column], errors="coerce")
    else:
        start = pd.to_datetime(claims[start_column], errors="coerce")
        end = pd.to_datetime(claims[end_column], errors="coerce")
        days = (end - start).dt.days

    return float(days.dropna().mean()) if days.notna().any() else 0.0


def calculate_average_claim_processing_days(data):
    """Return average days from claim date to approval date."""
    return _average_days(
        data, "claim_processing_days", "claim_date", "approval_date"
    )


def calculate_average_claim_settlement_days(data):
    """Return average days from claim date to settlement date."""
    return _average_days(
        data, "claim_settlement_days", "claim_date", "settlement_date"
    )


def calculate_total_payment_amount(data):
    """Return total amount across payment records."""
    return float(data["payments"]["payment_amount"].sum())


def calculate_average_payment_amount(data):
    """Return average amount per payment record."""
    return float(data["payments"]["payment_amount"].mean())


# Risk ratios

def calculate_claim_to_premium_ratio(data):
    """Return total claim amount divided by total policy premium."""
    return _safe_ratio(
        calculate_total_claim_amount(data),
        calculate_total_premium(data),
    )


def calculate_claim_to_coverage_ratio(data):
    """Return total claim amount divided by total policy coverage."""
    total_coverage = float(data["policies"]["coverage_amount"].sum())
    return _safe_ratio(calculate_total_claim_amount(data), total_coverage)


def calculate_paid_claim_ratio(data):
    """Return total payment amount divided by total requested claim amount."""
    return _safe_ratio(
        calculate_total_payment_amount(data),
        calculate_total_claim_amount(data),
    )


# Customer analysis

def analyze_customer_claims(data):
    """Summarize claim counts and amounts by customer."""
    summary = data["claims"].groupby("customer_id").agg(
        claim_count=("claim_id", "nunique"),
        total_claim_amount=("claim_amount", "sum"),
        average_claim_amount=("claim_amount", "mean"),
    )

    result = data["customers"].merge(
        summary, on="customer_id", how="left", validate="one_to_one"
    )
    return result.fillna(
        {"claim_count": 0, "total_claim_amount": 0, "average_claim_amount": 0}
    )


def analyze_customer_premium(data):
    """Summarize policy counts and premium by customer."""
    summary = data["policies"].groupby("customer_id").agg(
        policy_count=("policy_id", "nunique"),
        total_premium=("premium_amount", "sum"),
        average_premium=("premium_amount", "mean"),
    )

    result = data["customers"].merge(
        summary, on="customer_id", how="left", validate="one_to_one"
    )
    return result.fillna(
        {"policy_count": 0, "total_premium": 0, "average_premium": 0}
    )


# Vehicle analysis

def _claims_with_vehicle_details(data):
    """Return claims joined to their policy and vehicle details."""
    vehicles = data["vehicles"].copy()

    if "vehicle_age" not in vehicles.columns:
        vehicles["vehicle_age"] = (
            pd.Timestamp.today().year - vehicles["vehicle_year"]
        )

    return (
        data["claims"].merge(
            data["policies"][["policy_id", "vehicle_id"]],
            on="policy_id",
            how="left",
            validate="many_to_one",
        ).merge(
            vehicles[
                [
                    "vehicle_id", "vehicle_type", "vehicle_make",
                    "vehicle_model", "vehicle_year", "vehicle_age", "fuel_type",
                ]
            ],
            on="vehicle_id",
            how="left",
            validate="many_to_one",
        )
    )


def analyze_vehicle_claims(data):
    """Summarize claim volume and amounts by vehicle type, make, and model."""
    claim_vehicle = _claims_with_vehicle_details(data)

    return claim_vehicle.groupby(
        ["vehicle_type", "vehicle_make", "vehicle_model"]
    ).agg(
        claim_count=("claim_id", "nunique"),
        total_claim_amount=("claim_amount", "sum"),
        average_claim_amount=("claim_amount", "mean"),
    ).sort_values("total_claim_amount", ascending=False)


def analyze_vehicle_risk_patterns(data):
    """Summarize claims by vehicle type, make, fuel, and vehicle age."""
    claim_vehicle = _claims_with_vehicle_details(data)

    return claim_vehicle.groupby(
        ["vehicle_type", "vehicle_make", "fuel_type", "vehicle_age"]
    ).agg(
        claim_count=("claim_id", "nunique"),
        total_claim_amount=("claim_amount", "sum"),
        average_claim_amount=("claim_amount", "mean"),
    ).sort_values("total_claim_amount", ascending=False)


def analyze_vehicle_type(data):
    """Summarize claim volume and amounts by vehicle type."""
    claim_vehicle = _claims_with_vehicle_details(data)

    return claim_vehicle.groupby("vehicle_type").agg(
        claim_count=("claim_id", "nunique"),
        total_claim_amount=("claim_amount", "sum"),
        average_claim_amount=("claim_amount", "mean"),
    ).sort_values("total_claim_amount", ascending=False)


# Business analysis

def analyze_claim_type(data):
    """Summarize claim counts and amounts by claim type."""
    return data["claims"].groupby("claim_type").agg(
        claim_count=("claim_id", "nunique"),
        total_claim_amount=("claim_amount", "sum"),
        average_claim_amount=("claim_amount", "mean"),
    ).sort_values("total_claim_amount", ascending=False)


def analyze_claim_status(data):
    """Summarize claim counts and amounts by claim status."""
    return data["claims"].groupby("claim_status").agg(
        claim_count=("claim_id", "nunique"),
        total_claim_amount=("claim_amount", "sum"),
        average_claim_amount=("claim_amount", "mean"),
    ).sort_values("claim_count", ascending=False)


def analyze_policy_type(data):
    """Summarize policy and claim measures by policy type."""
    policies = data["policies"]

    policy_summary = policies.groupby("policy_type").agg(
        policy_count=("policy_id", "nunique"),
        total_premium=("premium_amount", "sum"),
        average_premium=("premium_amount", "mean"),
    )

    claims_with_type = data["claims"].merge(
        policies[["policy_id", "policy_type"]],
        on="policy_id",
        how="left",
        validate="many_to_one",
    )

    claim_summary = claims_with_type.groupby("policy_type").agg(
        claim_count=("claim_id", "nunique"),
        total_claim_amount=("claim_amount", "sum"),
        average_claim_amount=("claim_amount", "mean"),
    )

    result = policy_summary.join(claim_summary, how="left")
    result["claim_to_premium_ratio"] = (
        result["total_claim_amount"] / result["total_premium"]
    )
    return result.fillna(0)


def analyze_region(data):
    """Summarize claim counts and amounts by customer state."""
    claims_by_state = data["claims"].merge(
        data["customers"][["customer_id", "state"]],
        on="customer_id",
        how="left",
        validate="many_to_one",
    )

    return claims_by_state.groupby("state").agg(
        claim_count=("claim_id", "nunique"),
        total_claim_amount=("claim_amount", "sum"),
        average_claim_amount=("claim_amount", "mean"),
    ).sort_values("total_claim_amount", ascending=False)


def analyze_damage_severity(data):
    """Summarize claim counts and amounts by damage severity."""
    return data["claims"].groupby("damage_severity").agg(
        claim_count=("claim_id", "nunique"),
        total_claim_amount=("claim_amount", "sum"),
        average_claim_amount=("claim_amount", "mean"),
    ).sort_values("total_claim_amount", ascending=False)