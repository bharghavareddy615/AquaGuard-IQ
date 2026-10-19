"""
AquaGuard IQ - Data Management Module
Handles CSV ingestion, data validation, serialization, template generation,
and persistent export for the simulation telemetry.
"""

from typing import Tuple, List, Optional
import io
import os
import pandas as pd
import numpy as np

REQUIRED_COLUMNS = [
    "timestamp",
    "simulated_flow_rate_lpm",
    "estimated_volume_litres",
    "cumulative_volume_litres",
    "rated_capacity_litres",
    "usage_percentage",
    "maintenance_status"
]

SAMPLE_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample_water_usage.csv")


def validate_telemetry_dataframe(df: pd.DataFrame) -> Tuple[bool, List[str], Optional[pd.DataFrame]]:
    """
    Validates uploaded or loaded DataFrame against expected schema,
    verifies non-empty contents, checks data types, and ensures numerical validity.
    """
    errors = []

    if df is None or df.empty:
        return False, ["Uploaded dataset is empty."], None

    # Check required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(missing_cols)}")
        return False, errors, None

    cleaned_df = df.copy()

    # Validate and parse timestamps
    try:
        cleaned_df["timestamp"] = pd.to_datetime(cleaned_df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        errors.append(f"Failed to parse 'timestamp' column as valid dates: {str(e)}")

    # Validate numerical fields
    numeric_cols = [
        "simulated_flow_rate_lpm",
        "estimated_volume_litres",
        "cumulative_volume_litres",
        "rated_capacity_litres",
        "usage_percentage"
    ]

    for col in numeric_cols:
        try:
            cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors="coerce")
            if cleaned_df[col].isnull().any():
                errors.append(f"Column '{col}' contains non-numeric or missing values.")
            elif (cleaned_df[col] < 0).any():
                errors.append(f"Column '{col}' contains negative values, which is physically invalid.")
        except Exception as e:
            errors.append(f"Error parsing numeric column '{col}': {str(e)}")

    if errors:
        return False, errors, None

    # Ensure optional auxiliary columns exist with fallbacks
    if "elapsed_days" not in cleaned_df.columns:
        cleaned_df["elapsed_days"] = np.linspace(1.0, 30.0, len(cleaned_df))
    if "simulated_tds_ppm" not in cleaned_df.columns:
        cleaned_df["simulated_tds_ppm"] = 85.0 + (cleaned_df["usage_percentage"] * 1.2)
    if "is_simulated" not in cleaned_df.columns:
        cleaned_df["is_simulated"] = True

    return True, [], cleaned_df


def load_csv_from_upload(uploaded_file) -> Tuple[bool, List[str], Optional[pd.DataFrame]]:
    """Reads and validates a CSV uploaded through st.file_uploader."""
    try:
        df = pd.read_csv(uploaded_file)
        return validate_telemetry_dataframe(df)
    except Exception as e:
        return False, [f"Failed to read CSV file: {str(e)}"], None


def export_dataframe_to_csv(df: pd.DataFrame) -> bytes:
    """Serializes DataFrame to UTF-8 encoded CSV bytes for download."""
    if df is None or df.empty:
        # Return empty template with headers
        empty_df = pd.DataFrame(columns=REQUIRED_COLUMNS)
        return empty_df.to_csv(index=False).encode("utf-8")
    return df.to_csv(index=False).encode("utf-8")


def ensure_sample_dataset_exists() -> str:
    """
    Verifies that data/sample_water_usage.csv exists on disk.
    If not, generates a 60-day reproducible synthetic dataset and saves it.
    """
    os.makedirs(os.path.dirname(SAMPLE_FILE_PATH), exist_ok=True)
    if not os.path.exists(SAMPLE_FILE_PATH):
        from modules.simulation import generate_synthetic_dataset
        sample_df = generate_synthetic_dataset(days=60, daily_target_litres=16.0, seed=101)
        sample_df.to_csv(SAMPLE_FILE_PATH, index=False)
    return SAMPLE_FILE_PATH


def load_bundled_sample_dataset() -> pd.DataFrame:
    """Loads the bundled sample dataset from data/sample_water_usage.csv."""
    path = ensure_sample_dataset_exists()
    return pd.read_csv(path)
