"""
AquaGuard IQ - IoT Security & Sensor Telemetry Ingestion Layer
Enterprise-Grade v2.0 Production Prototype
AtomQUEST Track 2: Water Purifier Prognostics & IoT Telemetry
"""

from datetime import datetime, timezone
from typing import Tuple, Dict, Any, Optional
import config


def validate_sensor_payload(request_headers: Dict[str, Any], payload: Dict[str, Any]) -> Tuple[bool, str, int]:
    """
    Validates incoming sensor payload:
    1. Authenticates X-Sensor-API-Key against configured secret key.
    2. Outlier filtering: Rejects negative telemetry values and anomalous flow spikes (> 15 L/min).
    3. Type checks incoming fields.
    """
    # 1. API Key Authentication
    api_key = request_headers.get("X-Sensor-API-Key") or request_headers.get(config.API_KEY_HEADER)
    if not api_key or api_key != config.SENSOR_API_KEY:
        return False, "Unauthorized: Invalid or missing X-Sensor-API-Key header", 401

    if not isinstance(payload, dict):
        return False, "Malformed payload: Expected JSON object", 400

    # 2. Extract telemetry fields with defaults
    try:
        litres = float(payload.get("litres_flowed", 0.0))
        flow_rate = float(payload.get("flow_rate_lpm", 0.0))
    except (ValueError, TypeError):
        return False, "Type error: litres_flowed and flow_rate_lpm must be numeric", 400

    # Optional TDS field
    try:
        tds_ppm = float(payload.get("tds_ppm", config.DEFAULT_RAW_TDS_PPM))
    except (ValueError, TypeError):
        return False, "Type error: tds_ppm must be numeric", 400

    # 3. Anomaly & Outlier Filtering
    if litres < config.MIN_LITRES_FLOWED or flow_rate < config.MIN_FLOW_RATE_LPM or tds_ppm < 0:
        return False, "Invalid negative telemetry values rejected", 400

    if flow_rate > config.MAX_FLOW_RATE_LPM:
        return False, f"Anomalous flow spike detected (Spike {flow_rate:.1f} L/min exceeds safety ceiling of {config.MAX_FLOW_RATE_LPM} L/min)", 422

    return True, "Payload Validated Successfully", 200


def evaluate_hardware_watchdog(last_sensor_ping: Optional[str], current_sensor_status: str = 'SIMULATION_MODE') -> Tuple[str, Optional[float]]:
    """
    Hardware Disconnection Watchdog:
    If no sensor payload is received within 300 seconds from a physical sensor,
    flag the system status to 'SENSOR_OFFLINE_FALLBACK_ACTIVE'.

    Returns:
        (sensor_status, seconds_elapsed_since_last_ping)
    """
    if not last_sensor_ping:
        return 'SIMULATION_MODE', None

    try:
        # Support both ISO formats and standard datetime strings
        cleaned_str = str(last_sensor_ping).replace('T', ' ')
        if '.' in cleaned_str:
            ping_dt = datetime.strptime(cleaned_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
        else:
            ping_dt = datetime.strptime(cleaned_str, '%Y-%m-%d %H:%M:%S')

        now = datetime.now()
        seconds_elapsed = max(0.0, (now - ping_dt).total_seconds())

        if seconds_elapsed <= config.WATCHDOG_TIMEOUT_SECONDS:
            return 'ESP32_CONNECTED', seconds_elapsed
        else:
            # Watchdog timeout exceeded (300s window lapsed)
            return 'SENSOR_OFFLINE_FALLBACK_ACTIVE', seconds_elapsed

    except Exception:
        return current_sensor_status or 'SIMULATION_MODE', None

