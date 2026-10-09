from pathlib import Path

from src.data_loader import load_all_data
from src.validation import validate_all_tables
from src.data_cleaner import clean_data, save_cleaned_data


def run_pipeline():
    """Load, validate, clean, and save the motor insurance data."""
    project_dir = Path(__file__).resolve().parent
    raw_dir = project_dir / "data" / "raw"
    cleaned_dir = project_dir / "data" / "cleaned"

    print("Loading raw CSV files...")
    data = load_all_data(raw_dir)

    print("Validating columns, IDs, and relationships...")
    validate_all_tables(data)

    print("Cleaning data and creating derived columns...")
    cleaned_data = clean_data(data)

    print("Saving cleaned CSV files...")
    save_cleaned_data(cleaned_data, cleaned_dir)

    print(f"Pipeline complete. Cleaned files saved in: {cleaned_dir}")


if __name__ == "__main__":
    run_pipeline()