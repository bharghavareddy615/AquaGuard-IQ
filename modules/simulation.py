"""
AquaGuard IQ - Simulation Engine Module
Provides deterministic water-dispensing simulation, synthetic dataset generation,
and discrete event generators without background timers or blocking loops.
"""

from typing import Tuple, Dict, Any, Optional
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from modules.estimator import (
    calculate_filter_metrics,
    DEFAULT_RATED_CAPACITY_LITRES,
    DEFAULT_SERVICE_INTERVAL_DAYS,
    DEFAULT_DAILY_USAGE_LITRES,
    STATUS_NORMAL,
    STATUS_MODERATE,
    STATUS_SERVICE_SOON,
    STATUS_CAPACITY_REACHED
)

# Flow Profile Definitions (Litres per Minute)
PROFILE_LOW = "Low (0.8 – 1.2 L/min)"
PROFILE_NORMAL = "Normal (1.8 – 2.5 L/min)"
PROFILE_HIGH = "High (3.0 – 4.5 L/min)"
PROFILE_CUSTOM = "Custom"

FLOW_RANGES = {
    PROFILE_LOW: (0.8, 1.2),
    PROFILE_NORMAL: (1.8, 2.5),
    PROFILE_HIGH: (3.0, 4.5),
}


def sample_flow_rate(profile: str, custom_rate: float = 2.0, rng: Optional[np.random.RandomState] = None) -> float:
    """Returns a simulated flow rate in L/min based on profile selection."""
    if rng is None:
        rng = np.random.RandomState()

    if profile in FLOW_RANGES:
        low, high = FLOW_RANGES[profile]
        return round(float(rng.uniform(low, high)), 2)
    elif profile == PROFILE_CUSTOM:
        jitter = float(rng.uniform(-0.05, 0.05))
        return round(max(0.1, custom_rate + jitter), 2)
    else:
        return 2.0


def generate_synthetic_dataset(
    days: int = 90,
    daily_target_litres: float = 16.0,
    rated_capacity: float = DEFAULT_RATED_CAPACITY_LITRES,
    service_interval_days: float = DEFAULT_SERVICE_INTERVAL_DAYS,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates a reproducible, physically realistic synthetic dataset of domestic water usage.
    
    Simulation logic:
    - Multi-event daily pattern (morning breakfast/refill, midday cooking, evening family consumption)
    - Realistic pulse/flow variability
    - Auxiliary simulated TDS drift representing realistic membrane/carbon exhaustion baseline
    - Deterministic output controlled via seed
    """
    rng = np.random.RandomState(seed)
    start_date = datetime.now() - timedelta(days=days)

    records = []
    cumulative_volume = 0.0

    # Event templates: (name, avg_litres, flow_profile)
    event_templates = [
        ("Morning Drinking Water", 1.2, PROFILE_LOW),
        ("Breakfast & Cooking Refill", 4.5, PROFILE_NORMAL),
        ("Afternoon Water Refill", 2.0, PROFILE_NORMAL),
        ("Dinner Cooking & Prep", 5.0, PROFILE_NORMAL),
        ("Night Family Bottles Refill", 3.3, PROFILE_HIGH),
    ]

    for day_idx in range(days):
        current_day_date = start_date + timedelta(days=day_idx)
        elapsed_days = float(day_idx + 1)

        # Scale factor for daily variations (weekends vs weekdays)
        day_variation = rng.uniform(0.75, 1.35)
        # Target litres for today
        today_target = daily_target_litres * day_variation

        # Generate 4-7 discrete flow events throughout the day
        num_events = rng.randint(4, 7)
        hour_slots = np.sort(rng.choice(range(6, 23), size=num_events, replace=False))

        for ev_idx, hour in enumerate(hour_slots):
            template_name, base_vol, prof = event_templates[ev_idx % len(event_templates)]
            
            # Flow rate for this event
            flow_rate_lpm = sample_flow_rate(prof, rng=rng)
            
            # Volume for this event with variation
            event_vol = max(0.2, (base_vol * day_variation * rng.uniform(0.7, 1.3)))
            # Duration in seconds = (volume / flow_rate) * 60
            duration_sec = round((event_vol / flow_rate_lpm) * 60.0, 1)

            # Cumulative calculations
            cumulative_volume += event_vol

            # Evaluate filter metrics at this step
            metrics = calculate_filter_metrics(
                cumulative_volume_litres=cumulative_volume,
                rated_capacity_litres=rated_capacity,
                elapsed_days=elapsed_days,
                service_interval_days=service_interval_days,
                avg_daily_litres=daily_target_litres
            )

            # Simulated TDS drift: raw tap water ~350 ppm, fresh purified water ~75-90 ppm,
            # rises toward ~180-240 ppm as filter reaches capacity
            base_tds = 80.0
            exhaustion_factor = (cumulative_volume / rated_capacity) ** 1.4
            simulated_tds = round(base_tds + (140.0 * min(1.3, exhaustion_factor)) + rng.normal(0, 3.5), 1)

            # Event timestamp
            minute = rng.randint(0, 59)
            second = rng.randint(0, 59)
            event_time = current_day_date.replace(hour=int(hour), minute=int(minute), second=int(second))

            records.append({
                "timestamp": event_time.strftime("%Y-%m-%d %H:%M:%S"),
                "day_number": day_idx + 1,
                "elapsed_days": elapsed_days,
                "event_type": template_name,
                "simulated_flow_rate_lpm": round(flow_rate_lpm, 2),
                "duration_seconds": duration_sec,
                "estimated_volume_litres": round(event_vol, 2),
                "cumulative_volume_litres": round(cumulative_volume, 2),
                "rated_capacity_litres": round(rated_capacity, 2),
                "remaining_capacity_litres": metrics.remaining_capacity_litres,
                "usage_percentage": metrics.usage_percentage,
                "simulated_tds_ppm": max(40.0, simulated_tds),
                "maintenance_status": metrics.status,
                "is_simulated": True
            })

    df = pd.DataFrame(records)
    return df


def simulate_single_event(
    current_df: pd.DataFrame,
    flow_profile: str,
    custom_flow_rate: float,
    volume_litres: float,
    rated_capacity: float,
    service_interval_days: float,
    avg_daily_litres: float
) -> pd.DataFrame:
    """
    Appends a single simulated water dispensing event to the ongoing simulation dataset.
    Executes in a single deterministic step without UI lag.
    """
    rng = np.random.RandomState()
    flow_rate = sample_flow_rate(flow_profile, custom_rate=custom_flow_rate, rng=rng)
    event_vol = max(0.1, float(volume_litres))
    duration_sec = round((event_vol / flow_rate) * 60.0, 1)

    now = datetime.now()

    if current_df is not None and not current_df.empty:
        last_cum = float(current_df["cumulative_volume_litres"].iloc[-1])
        last_elapsed = float(current_df["elapsed_days"].iloc[-1])
        last_day = int(current_df["day_number"].iloc[-1])
        # Small elapsed increment for manual test button
        elapsed_days = last_elapsed + (event_vol / max(1.0, avg_daily_litres))
        day_number = last_day
    else:
        last_cum = 0.0
        elapsed_days = 1.0
        day_number = 1

    new_cum = last_cum + event_vol

    metrics = calculate_filter_metrics(
        cumulative_volume_litres=new_cum,
        rated_capacity_litres=rated_capacity,
        elapsed_days=elapsed_days,
        service_interval_days=service_interval_days,
        avg_daily_litres=avg_daily_litres
    )

    base_tds = 85.0
    exhaustion_factor = (new_cum / rated_capacity) ** 1.4
    simulated_tds = round(base_tds + (140.0 * min(1.3, exhaustion_factor)) + rng.normal(0, 2.0), 1)

    new_row = {
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "day_number": day_number,
        "elapsed_days": round(elapsed_days, 1),
        "event_type": "Interactive Dispensing Event",
        "simulated_flow_rate_lpm": round(flow_rate, 2),
        "duration_seconds": duration_sec,
        "estimated_volume_litres": round(event_vol, 2),
        "cumulative_volume_litres": round(new_cum, 2),
        "rated_capacity_litres": round(rated_capacity, 2),
        "remaining_capacity_litres": metrics.remaining_capacity_litres,
        "usage_percentage": metrics.usage_percentage,
        "simulated_tds_ppm": max(40.0, simulated_tds),
        "maintenance_status": metrics.status,
        "is_simulated": True
    }

    new_df = pd.concat([current_df, pd.DataFrame([new_row])], ignore_index=True)
    return new_df
