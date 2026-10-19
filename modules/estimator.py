"""
AquaGuard IQ - Filter-Life Estimator Module
Contains deterministic baseline estimation logic, rule-based thresholding,
and synthetic predictive modeling helpers.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

# Standard default constants based on typical residential RO / Carbon filtration systems
DEFAULT_RATED_CAPACITY_LITRES = 6000.0  # Common sediment/carbon pre-filter rating
DEFAULT_SERVICE_INTERVAL_DAYS = 365     # Recommended maximum service interval (12 months)
DEFAULT_DAILY_USAGE_LITRES = 16.0       # Average 4-person household drinking/cooking water

# Status definitions and corresponding theme colors
STATUS_NORMAL = "Normal"
STATUS_MODERATE = "Moderate Usage"
STATUS_SERVICE_SOON = "Service Soon"
STATUS_CAPACITY_REACHED = "Capacity Reached"

STATUS_COLORS = {
    STATUS_NORMAL: {"bg": "#E8F5E9", "text": "#1B5E20", "border": "#81C784", "hex": "#2E7D32"},
    STATUS_MODERATE: {"bg": "#FFF8E1", "text": "#F57F17", "border": "#FFD54F", "hex": "#F9A825"},
    STATUS_SERVICE_SOON: {"bg": "#FFF3E0", "text": "#E65100", "border": "#FFB74D", "hex": "#EF6C00"},
    STATUS_CAPACITY_REACHED: {"bg": "#FFEBEE", "text": "#B71C1C", "border": "#E57373", "hex": "#C62828"},
}


@dataclass
class FilterMetrics:
    cumulative_volume_litres: float
    rated_capacity_litres: float
    remaining_capacity_litres: float
    usage_percentage: float
    elapsed_days: float
    service_interval_days: float
    time_elapsed_percentage: float
    status: str
    status_reason: str
    estimated_days_remaining: Optional[float]
    projected_replacement_date: Optional[str]


def evaluate_filter_status(
    usage_pct: float,
    time_pct: float,
    mod_thresh: float = 70.0,
    soon_thresh: float = 85.0
) -> Tuple[str, str]:
    """
    Evaluates combined filter maintenance status based on dual volume and time criteria.
    Status is governed by whichever constraint (cumulative throughput or elapsed time)
    is closer to exhaustion.
    """
    reasons = []

    # Volume-based status evaluation
    if usage_pct >= 100.0:
        vol_status = STATUS_CAPACITY_REACHED
        reasons.append(f"Cumulative water volume reached 100% of rated capacity ({usage_pct:.1f}%).")
    elif usage_pct >= soon_thresh:
        vol_status = STATUS_SERVICE_SOON
        reasons.append(f"Water volume is near rated limit ({usage_pct:.1f}%).")
    elif usage_pct >= mod_thresh:
        vol_status = STATUS_MODERATE
        reasons.append(f"Water volume is in moderate consumption range ({usage_pct:.1f}%).")
    else:
        vol_status = STATUS_NORMAL

    # Time-based status evaluation
    if time_pct >= 100.0:
        time_status = STATUS_CAPACITY_REACHED
        reasons.append(f"Elapsed calendar time has exceeded the recommended service interval ({time_pct:.1f}%).")
    elif time_pct >= soon_thresh:
        time_status = STATUS_SERVICE_SOON
        reasons.append(f"Calendar service interval is drawing close ({time_pct:.1f}% elapsed).")
    elif time_pct >= mod_thresh:
        time_status = STATUS_MODERATE
        reasons.append(f"Filter has completed over {mod_thresh:.0f}% of recommended calendar interval.")
    else:
        time_status = STATUS_NORMAL

    # Rank severity: Normal < Moderate < Service Soon < Capacity Reached
    severity_order = [STATUS_NORMAL, STATUS_MODERATE, STATUS_SERVICE_SOON, STATUS_CAPACITY_REACHED]
    highest_idx = max(severity_order.index(vol_status), severity_order.index(time_status))
    combined_status = severity_order[highest_idx]

    if not reasons:
        reasons.append("Usage volume and operational duration are within safe rated limits.")

    return combined_status, " ".join(reasons)


def calculate_filter_metrics(
    cumulative_volume_litres: float,
    rated_capacity_litres: float = DEFAULT_RATED_CAPACITY_LITRES,
    elapsed_days: float = 0.0,
    service_interval_days: float = DEFAULT_SERVICE_INTERVAL_DAYS,
    avg_daily_litres: float = DEFAULT_DAILY_USAGE_LITRES,
    mod_thresh: float = 70.0,
    soon_thresh: float = 85.0
) -> FilterMetrics:
    """
    Computes all standard filter metrics from volume and time parameters.
    Guarantees no negative remaining capacities or NaN percentages.
    """
    safe_rated = max(1.0, float(rated_capacity_litres))
    safe_interval = max(1.0, float(service_interval_days))
    cum_vol = max(0.0, float(cumulative_volume_litres))
    days = max(0.0, float(elapsed_days))

    # Calculate remaining capacity (clamped at 0)
    remaining_litres = max(0.0, safe_rated - cum_vol)

    # Usage percentage clamped at 100% for display meters (actual throughput can exceed 100%)
    usage_percentage = min(100.0, (cum_vol / safe_rated) * 100.0)

    # Time percentage
    time_percentage = min(100.0, (days / safe_interval) * 100.0)

    # Determine status
    status, reason = evaluate_filter_status(
        usage_pct=usage_percentage,
        time_pct=time_percentage,
        mod_thresh=mod_thresh,
        soon_thresh=soon_thresh
    )

    # Estimated remaining days calculation based on daily consumption
    estimated_days_rem: Optional[float] = None
    projected_date_str: Optional[str] = None

    if avg_daily_litres > 0.0:
        vol_days_left = remaining_litres / avg_daily_litres
        calendar_days_left = max(0.0, safe_interval - days)
        # Conservative estimate takes the minimum of volume vs calendar expiry
        estimated_days_rem = max(0.0, min(vol_days_left, calendar_days_left))
        
        target_date = pd.Timestamp.now() + pd.Timedelta(days=estimated_days_rem)
        projected_date_str = target_date.strftime("%Y-%m-%d")

    return FilterMetrics(
        cumulative_volume_litres=round(cum_vol, 2),
        rated_capacity_litres=round(safe_rated, 2),
        remaining_capacity_litres=round(remaining_litres, 2),
        usage_percentage=round(usage_percentage, 1),
        elapsed_days=round(days, 1),
        service_interval_days=round(safe_interval, 1),
        time_elapsed_percentage=round(time_percentage, 1),
        status=status,
        status_reason=reason,
        estimated_days_remaining=round(estimated_days_rem, 1) if estimated_days_rem is not None else None,
        projected_replacement_date=projected_date_str
    )


def get_status_badge_html(status: str) -> str:
    """Returns styled inline HTML badge for a given maintenance status."""
    cfg = STATUS_COLORS.get(status, STATUS_COLORS[STATUS_NORMAL])
    return (
        f"<span style='background-color: {cfg['bg']}; color: {cfg['text']}; "
        f"border: 1px solid {cfg['border']}; border-radius: 9999px; padding: 4px 14px; "
        f"font-weight: 600; font-size: 0.85rem; letter-spacing: 0.02em; display: inline-block;'>"
        f"{status}</span>"
    )


def train_synthetic_prognostic_model(df: pd.DataFrame) -> Tuple[Optional[Any], Dict[str, Any]]:
    """
    Trains a demonstrative classification model on synthetic simulation features.
    
    IMPORTANT NOTICE:
    This model operates on generated simulation data to show how multi-parameter
    prognostics will integrate once real bench test data is collected.
    It DOES NOT prove real-world filter failure accuracy.
    """
    required_cols = [
        "cumulative_volume_litres",
        "simulated_flow_rate_lpm",
        "elapsed_days",
        "maintenance_status"
    ]
    for col in required_cols:
        if col not in df.columns:
            return None, {"error": f"Missing column for training: {col}"}

    # Features and target
    feature_cols = ["cumulative_volume_litres", "simulated_flow_rate_lpm", "elapsed_days"]
    
    # If simulated TDS is present, include it as an auxiliary feature
    if "simulated_tds_ppm" in df.columns:
        feature_cols.append("simulated_tds_ppm")

    X = df[feature_cols].copy()
    y = df["maintenance_status"].astype(str)

    if len(df) < 15:
        return None, {"error": "Insufficient dataset size (minimum 15 rows required for demonstration)."}

    # Train a transparent Random Forest Classifier
    rf = RandomForestClassifier(n_estimators=30, max_depth=4, random_state=42)
    rf.fit(X, y)
    y_pred = rf.predict(X)

    acc = float(accuracy_score(y, y_pred))
    importances = dict(zip(feature_cols, [round(float(imp), 4) for imp in rf.feature_importances_]))

    report = {
        "accuracy": acc,
        "feature_importances": importances,
        "classes": list(rf.classes_),
        "sample_size": len(df),
        "features_used": feature_cols,
        "disclaimer": (
            "Demonstration model trained on synthetic simulation records. "
            "Evaluates algorithmic feasibility; does NOT validate physical membrane failure."
        )
    }

    return rf, report
