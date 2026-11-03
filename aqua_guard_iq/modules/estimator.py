"""
AquaGuard IQ - Advanced Multi-Factor Prognostic Engine & RUL Estimator
Enterprise-Grade v2.0 Production Prototype
AtomQUEST Track 2: Water Purifier Prognostics & IoT Telemetry
"""

import math
from typing import Dict, Any, List, Tuple
import config


class PrognosticEngine:
    """
    Advanced Multi-Factor Degradation Engine.
    Replaces basic linear volumetric subtraction with physics-informed membrane wear dynamics.
    """

    def __init__(self, rated_capacity_litres: float = config.DEFAULT_RATED_CAPACITY_LITRES):
        self.rated_capacity = float(rated_capacity_litres)

    def calculate_factors(self, flow_rate_lpm: float = 2.0, tds_ppm: float = 350.0) -> Tuple[float, float]:
        """
        Calculate independent stress factors:
        1. TDS Penalty Factor (Base 250 PPM = 1.0)
        2. Turbulence / Flow Rate Stress Factor (> 3.5 L/min = 1.15x wear)
        """
        # TDS Hardness Factor
        k_tds = 1.0 + max(0.0, (float(tds_ppm) - config.BASE_TDS_PPM) / 500.0)
        k_tds = round(k_tds, 4)

        # Flow Rate Turbulence Stress Factor
        k_flow = config.TURBULENCE_STRESS_FACTOR if float(flow_rate_lpm) > config.TURBULENCE_FLOW_THRESHOLD_LPM else 1.0

        return k_tds, k_flow

    def calculate_degradation(self, raw_litres: float, flow_rate_lpm: float = 2.0, tds_ppm: float = 350.0) -> float:
        """
        Multi-Factor Degradation Formula:
        Effective_Volume = Injected_Volume * K_TDS * K_FlowRate
        """
        k_tds, k_flow = self.calculate_factors(flow_rate_lpm, tds_ppm)
        effective_wear = float(raw_litres) * k_tds * k_flow
        return round(effective_wear, 2)

    def compute_rul(self, remaining_capacity: float, avg_daily_usage: float) -> int:
        """Calculates Remaining Useful Life (RUL) in days."""
        if avg_daily_usage <= 0:
            return 999
        days = math.floor(remaining_capacity / avg_daily_usage)
        return max(0, days)

    def compute_exponential_daily_usage(self, daily_usage_series: List[float], fallback_rate: float = 15.0) -> float:
        """
        7-Day Rolling Exponential Smoothing:
        S_t = alpha * Y_t + (1 - alpha) * S_{t-1}
        Weights recent daily usage patterns more heavily than past ones.
        """
        if not daily_usage_series:
            return float(fallback_rate)

        # Consider the last 7 daily observations
        window = daily_usage_series[-7:]
        alpha = config.EXPONENTIAL_SMOOTHING_ALPHA

        smoothed = window[0]
        for val in window[1:]:
            smoothed = alpha * val + (1.0 - alpha) * smoothed

        smoothed = round(smoothed, 2)
        return smoothed if smoothed > 0.5 else float(fallback_rate)

    def evaluate_health(self, total_raw_litres: float, total_effective_litres: float, 
                        daily_usage_rate: float) -> Dict[str, Any]:
        """
        Comprehensive multi-factor prognostic evaluation:
        - Total Raw Consumption (L)
        - Effective Weighted Degradation (L)
        - Remaining Effective Capacity (L)
        - Remaining Membrane Health Score (%)
        - Wear Multiplier / Penalty (%)
        - Remaining Useful Life (RUL in days)
        - Prognostic Status (NORMAL, ATTENTION_REQUIRED, CRITICAL_REPLACE)
        """
        total_raw = round(max(0.0, float(total_raw_litres)), 2)
        total_effective = round(max(0.0, float(total_effective_litres)), 2)
        rated = max(1.0, float(self.rated_capacity))

        # Remaining effective capacity
        remaining_capacity = max(0.0, round(rated - total_effective, 2))

        # Remaining health score % (100% brand new, 0% fully exhausted)
        health_score_pct = max(0.0, min(100.0, round(((rated - total_effective) / rated) * 100.0, 1)))
        capacity_consumed_pct = max(0.0, min(100.0, round((total_effective / rated) * 100.0, 1)))

        # Multi-factor penalty ratio (how much extra wear from hard water / turbulence)
        if total_raw > 0:
            excess_wear_pct = round(((total_effective - total_raw) / total_raw) * 100.0, 1)
            wear_multiplier = round(total_effective / total_raw, 2)
        else:
            excess_wear_pct = 0.0
            wear_multiplier = 1.0

        # RUL calculation in days
        effective_daily = max(0.1, float(daily_usage_rate))
        rul_days = self.compute_rul(remaining_capacity, effective_daily)

        # Tri-Tier Prognostic Classification:
        # NORMAL: Health Score > 30%
        # ATTENTION_REQUIRED: Health Score 15% - 30% (or RUL <= 21 days)
        # CRITICAL_REPLACE: Health Score < 15% (or RUL <= 7 days or remaining_capacity <= 0)
        if health_score_pct < config.STATUS_ATTENTION_THRESHOLD_PCT or remaining_capacity <= 0 or rul_days <= 7:
            prognostic_status = "CRITICAL_REPLACE"
            status_level = "danger"
            status_badge = "Critical: Replace Filter Immediately"
            status_description = (
                "Membrane exhaustion limit breached (<15% health). High mineral fouling and pore clogging "
                "risk microbial breakthrough. Immediate cartridge replacement required."
            )
        elif health_score_pct <= config.STATUS_NORMAL_THRESHOLD_PCT or rul_days <= 21:
            prognostic_status = "ATTENTION_REQUIRED"
            status_level = "warning"
            status_badge = "Attention Required"
            status_description = (
                "Membrane life in depletion buffer zone (15%-30% health). Pre-order replacement cartridge; "
                "schedule maintenance within the next 2-3 weeks."
            )
        else:
            prognostic_status = "NORMAL"
            status_level = "normal"
            status_badge = "Operational: Normal Health"
            status_description = (
                "Filter operating well within optimal performance envelope (>30% health). Flow hydraulics "
                "and membrane flux are stable."
            )

        return {
            "rated_capacity_litres": rated,
            "total_raw_litres": total_raw,
            "total_effective_litres": total_effective,
            "remaining_capacity_litres": remaining_capacity,
            "health_score_pct": health_score_pct,
            "capacity_consumed_pct": capacity_consumed_pct,
            "excess_wear_pct": excess_wear_pct,
            "wear_multiplier": wear_multiplier,
            "daily_usage_rate": effective_daily,
            "rul_days": rul_days,
            "prognostic_status": prognostic_status,
            "status_level": status_level,
            "status_badge": status_badge,
            "status_description": status_description
        }

