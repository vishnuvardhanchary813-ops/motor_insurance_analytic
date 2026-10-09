"""Validation checks for the motor insurance tables."""

import warnings
import pandas as pd


REQUIRED_COLUMNS = {
    "customers": [
        "customer_id", "customer_name", "gender", "date_of_birth",
        "age", "city", "state", "occupation",
    ],
    "vehicles": [
        "vehicle_id", "customer_id", "vehicle_type", "vehicle_make",
        "vehicle_model", "vehicle_year", "fuel_type", "vehicle_value",
    ],
    "policies": [
        "policy_id", "customer_id", "vehicle_id", "policy_start_date",
        "policy_end_date", "policy_type", "premium_amount",
        "coverage_amount", "policy_status", "payment_frequency",
    ],
    "claims": [
        "claim_id", "policy_id", "customer_id", "claim_date",
        "accident_date", "claim_type", "accident_location",
        "claim_amount", "claim_status", "approval_date",
        "settlement_date", "damage_severity",
    ],
    "payments": [
        "payment_id", "claim_id", "policy_id", "payment_date",
        "payment_amount", "payment_status", "payment_method",
    ],
}

PRIMARY_KEYS = {
    "customers": "customer_id",
    "vehicles": "vehicle_id",
    "policies": "policy_id",
    "claims": "claim_id",
    "payments": "payment_id",
}

DATE_COLUMNS = {
    "customers": ["date_of_birth"],
    "vehicles": [],
    "policies": ["policy_start_date", "policy_end_date"],
    "claims": [
        "claim_date", "accident_date", "approval_date", "settlement_date"
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

ALLOWED_VALUES = {
    "customers": {
        "gender": {"Male", "Female"},
    },
    "vehicles": {
        "vehicle_type": {"Car"},
        "fuel_type": {"Petrol", "Diesel", "CNG", "Electric"},
    },
    "policies": {
        "policy_type": {"Comprehensive", "Third Party", "Zero Depreciation"},
        "policy_status": {"Active", "Expired", "Cancelled", "Renewed"},
        "payment_frequency": {"Annual", "Semi-Annual", "Quarterly"},
    },
    "claims": {
        "claim_type": {
            "Accident", "Third Party Damage", "Theft",
            "Natural Disaster", "Fire",
        },
        "claim_status": {"Pending", "Approved", "Rejected", "Settled"},
        "damage_severity": {"Low", "Medium", "High"},
    },
    "payments": {
        "payment_status": {"Completed"},
        "payment_method": {"Bank Transfer", "UPI", "Cheque", "NEFT"},
    },
}


def _validate_table(table_name, df):
    """Check required columns, primary key, types, and category values."""
    missing = set(REQUIRED_COLUMNS[table_name]) - set(df.columns)
    if missing:
        raise ValueError(
            f"{table_name} is missing columns: {sorted(missing)}"
        )

    errors = []
    key = PRIMARY_KEYS[table_name]

    if df[key].isna().any():
        errors.append(f"{table_name}.{key} contains missing IDs")
    if df[key].duplicated().any():
        errors.append(f"{table_name}.{key} contains duplicate IDs")

    for column in NUMERIC_COLUMNS[table_name]:
        numeric = pd.to_numeric(df[column], errors="coerce")
        invalid = df[column].notna() & numeric.isna()
        if invalid.any():
            errors.append(f"{table_name}.{column} contains non-numeric values")
        if (numeric < 0).any():
            errors.append(f"{table_name}.{column} contains negative values")

    for column in DATE_COLUMNS[table_name]:
        parsed = pd.to_datetime(df[column], errors="coerce")
        invalid = df[column].notna() & parsed.isna()
        if invalid.any():
            errors.append(f"{table_name}.{column} contains invalid dates")

    for column, allowed in ALLOWED_VALUES.get(table_name, {}).items():
        unexpected = set(df[column].dropna().unique()) - allowed
        if unexpected:
            errors.append(
                f"{table_name}.{column} contains unexpected values: "
                f"{sorted(unexpected)}"
            )

    if errors:
        raise ValueError("; ".join(errors))

    return True


def validate_customers(df):
    """Validate the customers table."""
    return _validate_table("customers", df)


def validate_vehicles(df):
    """Validate the vehicles table."""
    return _validate_table("vehicles", df)


def validate_policies(df):
    """Validate the policies table."""
    return _validate_table("policies", df)


def validate_claims(df):
    """Validate the claims table."""
    return _validate_table("claims", df)


def validate_payments(df):
    """Validate the payments table."""
    return _validate_table("payments", df)


def validate_relationships(data):
    """Check that related records point to existing IDs."""
    relationships = [
        ("vehicles", "customer_id", "customers", "customer_id"),
        ("policies", "customer_id", "customers", "customer_id"),
        ("policies", "vehicle_id", "vehicles", "vehicle_id"),
        ("claims", "policy_id", "policies", "policy_id"),
        ("claims", "customer_id", "customers", "customer_id"),
        ("payments", "claim_id", "claims", "claim_id"),
        ("payments", "policy_id", "policies", "policy_id"),
    ]

    errors = []

    for child, child_key, parent, parent_key in relationships:
        child_values = data[child][child_key]
        parent_values = data[parent][parent_key]

        if child_values.isna().any():
            errors.append(f"{child}.{child_key} contains missing IDs")

        unmatched = child_values.notna() & ~child_values.isin(parent_values)
        if unmatched.any():
            errors.append(
                f"{child}.{child_key} has {int(unmatched.sum())} IDs "
                f"not found in {parent}.{parent_key}"
            )

    claim_policy = data["claims"][["policy_id", "customer_id"]].merge(
        data["policies"][["policy_id", "customer_id"]],
        on="policy_id",
        suffixes=("_claim", "_policy"),
        how="left",
        validate="many_to_one",
    )

    mismatch = (
        claim_policy["customer_id_claim"]
        != claim_policy["customer_id_policy"]
    )
    if mismatch.any():
        errors.append(
            f"{int(mismatch.sum())} claims have a customer ID that "
            "does not match their policy"
        )

    if errors:
        raise ValueError("Relationship validation failed: " + "; ".join(errors))

    return True


def validate_all_tables(data):
    """Validate all tables and their relationships."""
    missing_tables = set(REQUIRED_COLUMNS) - set(data)
    if missing_tables:
        raise ValueError(f"Missing tables: {sorted(missing_tables)}")

    validators = {
        "customers": validate_customers,
        "vehicles": validate_vehicles,
        "policies": validate_policies,
        "claims": validate_claims,
        "payments": validate_payments,
    }

    for table_name, validator in validators.items():
        validator(data[table_name])

    validate_relationships(data)

    policies = data["policies"]
    start = pd.to_datetime(policies["policy_start_date"], errors="coerce")
    end = pd.to_datetime(policies["policy_end_date"], errors="coerce")
    reversed_dates = start.notna() & end.notna() & (end < start)

    if reversed_dates.any():
        warnings.warn(
            f"{int(reversed_dates.sum())} policies have an end date before "
            "their start date. The cleaning step will flag these records.",
            UserWarning,
        )

    return True