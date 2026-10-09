"""Generate data-driven insurance patterns and recommendations."""

import pandas as pd


def _make_insight(pattern, evidence, meaning, recommendation):
    """Create one insight using the required report format."""
    return {
        "pattern": pattern,
        "evidence": evidence,
        "business_meaning": meaning,
        "recommendation": recommendation,
    }


def generate_portfolio_insights(data):
    """Describe the largest policy-status group."""
    policies = data["policies"]
    counts = policies["policy_status"].value_counts()

    if counts.empty:
        return []

    status = counts.idxmax()
    count = int(counts.max())
    share = count / len(policies) * 100

    return [_make_insight(
        f"{status} is the most common policy status.",
        f"{count:,} of {len(policies):,} policies ({share:.1f}%) are {status}.",
        "The largest status group describes a substantial part of the policy portfolio.",
        "Review this segment alongside renewal and cancellation trends when planning portfolio actions.",
    )]


def generate_claim_insights(data):
    """Describe the most common claim type and the highest average claim type."""
    claims = data["claims"]
    if claims.empty:
        return []

    by_type = claims.groupby("claim_type").agg(
        claim_count=("claim_id", "nunique"),
        total_claim_amount=("claim_amount", "sum"),
        average_claim_amount=("claim_amount", "mean"),
    )

    most_common = by_type["claim_count"].idxmax()
    highest_average = by_type["average_claim_amount"].idxmax()

    findings = [
        _make_insight(
            f"{most_common} is the most common claim type.",
            f"It accounts for {int(by_type.loc[most_common, 'claim_count']):,} claims.",
            "This type contributes the largest claim volume in the dataset.",
            "Review this claim type by severity, vehicle age, and settlement time to identify operational patterns.",
        ),
        _make_insight(
            f"{highest_average} has the highest average claim amount.",
            f"Its average claim amount is {by_type.loc[highest_average, 'average_claim_amount']:,.2f} "
            f"across {int(by_type.loc[highest_average, 'claim_count']):,} claims.",
            "A high average claim amount may have a different cost impact from a high-volume claim type.",
            "Review a sample of these claims and compare their damage severity and settlement outcomes.",
        ),
    ]
    return findings


def generate_premium_insights(data):
    """Describe premium totals and average premiums by policy type."""
    policies = data["policies"]
    if policies.empty:
        return []

    by_type = policies.groupby("policy_type").agg(
        policy_count=("policy_id", "nunique"),
        total_premium=("premium_amount", "sum"),
        average_premium=("premium_amount", "mean"),
    )

    top_total = by_type["total_premium"].idxmax()
    top_average = by_type["average_premium"].idxmax()

    return [
        _make_insight(
            f"{top_total} policies generate the highest total premium.",
            f"They contribute {by_type.loc[top_total, 'total_premium']:,.2f} "
            f"from {int(by_type.loc[top_total, 'policy_count']):,} policies.",
            "This policy type is the largest source of premium income in the dataset.",
            "Track claim costs and renewal rates for this policy type alongside its premium contribution.",
        ),
        _make_insight(
            f"{top_average} has the highest average premium per policy.",
            f"The average premium is {by_type.loc[top_average, 'average_premium']:,.2f}.",
            "Average premium differs across policy types and should be considered alongside coverage and claims.",
            "Compare average premium with coverage and claim outcomes before making pricing decisions.",
        ),
    ]


def generate_customer_insights(data):
    """Describe claim patterns by customer age group."""
    claims = data["claims"].merge(
        data["customers"][["customer_id", "customer_age"]],
        on="customer_id",
        how="left",
        validate="many_to_one",
    )

    claims["customer_age_group"] = pd.cut(
        claims["customer_age"],
        bins=[0, 25, 35, 45, 55, 100],
        labels=["18-25", "26-35", "36-45", "46-55", "56+"],
    )

    by_age = claims.dropna(subset=["customer_age_group"]).groupby(
        "customer_age_group", observed=True
    ).agg(
        claim_count=("claim_id", "nunique"),
        average_claim_amount=("claim_amount", "mean"),
    )

    if by_age.empty:
        return []

    group = by_age["average_claim_amount"].idxmax()
    return [_make_insight(
        f"Customer age group {group} has the highest average claim amount.",
        f"The group averages {by_age.loc[group, 'average_claim_amount']:,.2f} "
        f"across {int(by_age.loc[group, 'claim_count']):,} claims.",
        "Claim amounts vary by customer age group in this dataset.",
        "Compare this group's policy mix, vehicle age, and claim severity before drawing conclusions about customer risk.",
    )]


def generate_vehicle_insights(data):
    """Describe claim patterns by vehicle make and type."""
    claim_vehicle = (
        data["claims"].merge(
            data["policies"][["policy_id", "vehicle_id"]],
            on="policy_id",
            how="left",
            validate="many_to_one",
        ).merge(
            data["vehicles"][["vehicle_id", "vehicle_type", "vehicle_make"]],
            on="vehicle_id",
            how="left",
            validate="many_to_one",
        )
    )

    findings = []
    types = claim_vehicle["vehicle_type"].dropna().nunique()

    if types <= 1:
        findings.append(_make_insight(
            "The dataset contains only one vehicle type.",
            f"All {len(data['vehicles']):,} vehicle records are listed as "
            f"{data['vehicles']['vehicle_type'].dropna().iloc[0] if not data['vehicles'].empty else 'one type'}.",
            "This dataset cannot compare claim outcomes across vehicle types.",
            "Use a broader vehicle-type dataset before making comparisons between vehicle categories.",
        ))

    by_make = claim_vehicle.groupby("vehicle_make").agg(
        claim_count=("claim_id", "nunique"),
        average_claim_amount=("claim_amount", "mean"),
    )

    if not by_make.empty:
        make = by_make["average_claim_amount"].idxmax()
        findings.append(_make_insight(
            f"{make} has the highest average claim amount among vehicle makes.",
            f"The average is {by_make.loc[make, 'average_claim_amount']:,.2f} "
            f"across {int(by_make.loc[make, 'claim_count']):,} claims.",
            "Claim amounts vary across vehicle makes in this dataset.",
            "Review vehicle age, claim severity, and sample size for this make before taking action.",
        ))

    return findings


def generate_risk_patterns(data):
    """Find policy types with the highest claim-to-premium ratio."""
    policies = data["policies"]
    claims_with_type = data["claims"].merge(
        policies[["policy_id", "policy_type"]],
        on="policy_id",
        how="left",
        validate="many_to_one",
    )

    claim_totals = claims_with_type.groupby("policy_type")["claim_amount"].sum()
    premium_totals = policies.groupby("policy_type")["premium_amount"].sum()
    ratios = (claim_totals / premium_totals.replace(0, pd.NA)).dropna()

    if ratios.empty:
        return []

    policy_type = ratios.idxmax()
    return [_make_insight(
        f"{policy_type} has the highest total-claims-to-total-premium ratio.",
        f"The ratio is {ratios.loc[policy_type]:.3f} "
        f"({claim_totals.loc[policy_type]:,.2f} in claims divided by "
        f"{premium_totals.loc[policy_type]:,.2f} in premium).",
        "This is a portfolio-level comparison and is not, by itself, proof of loss or profitability.",
        "Review coverage, claim development, and exposure counts for this policy type before changing pricing or underwriting.",
    )]


def generate_business_recommendations(data):
    """Collect recommendations generated from the active data."""
    generators = [
        generate_portfolio_insights,
        generate_claim_insights,
        generate_premium_insights,
        generate_customer_insights,
        generate_vehicle_insights,
        generate_risk_patterns,
    ]

    recommendations = []
    for generator in generators:
        for insight in generator(data):
            recommendation = insight["recommendation"]
            if recommendation not in recommendations:
                recommendations.append(recommendation)

    return recommendations