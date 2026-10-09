"""Clean motor insurance data and save cleaned tables."""

from pathlib import Path

import pandas as pd


DATE_COLUMNS = {
    "customers": ["date_of_birth"],
    "vehicles": [],
    "policies": ["policy_start_date", "policy_end_date"],
    "claims": [
        "claim_date",
        "accident_date",
        "approval_date",
        "settlement_date",
    ],
    "payments": ["payment_date"],
}

NUMERIC_COLUMNS = {
    "customers": ["age"],
    "vehicles": ["vehicle_year", "vehicle_value"],
    "policies": ["premium_amount", "coverage_amount"],
    "claims": ["claim_amount"],
    "payments": ["payment_amount"],
}


def clean_text_columns(df):
    """Trim whitespace in text columns and mark blank cells as missing."""
    df = df.copy()

    for column in df.select_dtypes(include=["object", "string"]).columns:
        values = df[column].astype("string").str.strip()
        df[column] = values.mask(values.eq(""), pd.NA)

    return df


def remove_duplicates(df):
    """Remove exact duplicate rows."""
    return df.drop_duplicates().reset_index(drop=True)


def clean_date_columns(table_name, df):
    """Convert known date columns to datetime."""
    df = df.copy()

    for column in DATE_COLUMNS[table_name]:
        df[column] = pd.to_datetime(df[column], errors="coerce")

    return df


def validate_numeric_columns(table_name, df):
    """Convert known numeric columns to numeric values."""
    df = df.copy()

    for column in NUMERIC_COLUMNS[table_name]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    return df


def handle_missing_values(data):
    """Preserve missing values rather than inventing replacements."""
    return {name: df.copy() for name, df in data.items()}


def validate_business_rules(data):
    """Flag reversed policy dates and reject negative monetary values."""
    money_columns = {
        "vehicles": ["vehicle_value"],
        "policies": ["premium_amount", "coverage_amount"],
        "claims": ["claim_amount"],
        "payments": ["payment_amount"],
    }

    errors = []

    for table_name, columns in money_columns.items():
        for column in columns:
            negative = data[table_name][column] < 0
            if negative.any():
                errors.append(
                    f"{table_name}.{column} has "
                    f"{int(negative.sum())} negative values"
                )

    policies = data["policies"]
    invalid_dates = (
        policies["policy_start_date"].notna()
        & policies["policy_end_date"].notna()
        & (policies["policy_end_date"] < policies["policy_start_date"])
    )

    # Keep the policy rows, flag them, and blank their invalid end dates.
    policies["policy_date_issue"] = invalid_dates

    if invalid_dates.any():
        print(
            f"Warning: {int(invalid_dates.sum())} policies have reversed dates. "
            "Their end dates were blanked and the rows flagged."
        )
        policies.loc[invalid_dates, "policy_end_date"] = pd.NaT

    if errors:
        raise ValueError("Business rule check failed: " + "; ".join(errors))

    return True


def create_derived_columns(data):
    """Add customer and vehicle ages, durations, and claim ratios."""
    cleaned = {name: df.copy() for name, df in data.items()}
    today = pd.Timestamp.today().normalize()

    # Calculate customer age by row; use the supplied age if birth date is missing.
    customers = cleaned["customers"]
    dob = pd.to_datetime(customers["date_of_birth"], errors="coerce")

    birthday_not_reached = (
        (dob.dt.month > today.month)
        | (
            (dob.dt.month == today.month)
            & (dob.dt.day > today.day)
        )
    ).fillna(False).astype(int)

    customers["customer_age"] = (
        today.year - dob.dt.year - birthday_not_reached
    )
    customers["customer_age"] = customers["customer_age"].fillna(
        customers["age"]
    )

    # Calculate vehicle age using the current year.
    vehicles = cleaned["vehicles"]
    vehicles["vehicle_age"] = today.year - vehicles["vehicle_year"]

    # Calculate policy duration and active flag.
    policies = cleaned["policies"]
    policies["policy_duration_days"] = (
        policies["policy_end_date"] - policies["policy_start_date"]
    ).dt.days
    policies["policy_active_flag"] = (
        policies["policy_status"].eq("Active").astype("int8")
    )

    # Calculate claim processing and settlement durations.
    claims = cleaned["claims"]
    claims["claim_processing_days"] = (
        claims["approval_date"] - claims["claim_date"]
    ).dt.days
    claims["claim_settlement_days"] = (
        claims["settlement_date"] - claims["claim_date"]
    ).dt.days

    # Join policy premium and coverage to each claim.
    claim_policy = claims.merge(
        policies[["policy_id", "premium_amount", "coverage_amount"]],
        on="policy_id",
        how="left",
        validate="many_to_one",
    )

    premium = claim_policy["premium_amount"].where(
        claim_policy["premium_amount"] != 0
    )
    coverage = claim_policy["coverage_amount"].where(
        claim_policy["coverage_amount"] != 0
    )

    claims["claim_to_premium_ratio"] = (
        claim_policy["claim_amount"] / premium
    ).to_numpy()
    claims["claim_to_coverage_ratio"] = (
        claim_policy["claim_amount"] / coverage
    ).to_numpy()

    # Sum multiple payment records per claim before calculating the ratio.
    payment_totals = cleaned["payments"].groupby("claim_id")[
        "payment_amount"
    ].sum()

    claims["total_payment_amount"] = claims["claim_id"].map(payment_totals)

    claim_amount = claims["claim_amount"].where(
        claims["claim_amount"] != 0
    )
    claims["paid_claim_ratio"] = (
        claims["total_payment_amount"] / claim_amount
    )

    return cleaned


def clean_data(data):
    """Clean all tables and add derived columns."""
    cleaned = {}

    for table_name, df in data.items():
        df = clean_text_columns(df)
        df = remove_duplicates(df)
        df = clean_date_columns(table_name, df)
        df = validate_numeric_columns(table_name, df)
        cleaned[table_name] = df

    cleaned = handle_missing_values(cleaned)
    validate_business_rules(cleaned)

    return create_derived_columns(cleaned)


def save_cleaned_data(data, output_dir):
    """Save cleaned tables using the required filenames."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for table_name, df in data.items():
        output_file = output_dir / f"{table_name}_cleaned.csv"
        df.to_csv(
            output_file,
            index=False,
            date_format="%Y-%m-%d",
            encoding="utf-8",
        )