"""Load the raw motor insurance CSV tables."""

from pathlib import Path

import pandas as pd


TABLE_NAMES = ("customers", "policies", "vehicles", "claims", "payments")


def check_file_exists(file_path):
    """Raise an error if the required file does not exist."""
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"Required CSV file not found: {path}")

    return True


def load_table(file_path):
    """Load one CSV file into a pandas DataFrame."""
    check_file_exists(file_path)
    return pd.read_csv(file_path)


def load_all_data(data_dir):
    """Load all five required CSV files from the raw data directory."""
    data_dir = Path(data_dir)

    data = {}
    for table_name in TABLE_NAMES:
        file_path = data_dir / f"{table_name}.csv"
        data[table_name] = load_table(file_path)

    return data