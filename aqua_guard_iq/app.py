"""
AquaGuard IQ - Flask Application & Telemetry Controller
Enterprise-Grade v2.0 Production Prototype
AtomQUEST Track 2: Water Purifier Prognostics & IoT Telemetry
"""

import os
import sys
import io
import csv
from datetime import datetime

# Ensure current application directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, Response

import config
from modules.db import (
    init_db,
    get_system_state,
    update_system_state,
    insert_telemetry,
    get_telemetry_history,
    get_daily_summary,
    get_all_daily_effective_series,
    get_depletion_trajectory,
    reset_database
)
from modules.estimator import PrognosticEngine
from modules.sensor_api import validate_sensor_payload, evaluate_hardware_watchdog

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Initialize the Multi-Factor Degradation Engine
engine = PrognosticEngine(rated_capacity_litres=config.DEFAULT_RATED_CAPACITY_LITRES)


def build_full_metrics_payload() -> dict:
    """Helper to assemble complete system state, multi-factor metrics, and trend series."""
    state = get_system_state()
    rated_capacity = float(state.get('rated_capacity', config.DEFAULT_RATED_CAPACITY_LITRES))
    engine.rated_capacity = rated_capacity

    # 1. Hardware Disconnection Watchdog evaluation
    sensor_status, seconds_elapsed = evaluate_hardware_watchdog(
        state.get('last_sensor_ping'),
        state.get('sensor_status', 'SIMULATION_MODE')
    )
    if sensor_status != state.get('sensor_status'):
        update_system_state(sensor_status=sensor_status)
        state['sensor_status'] = sensor_status

    # 2. 7-Day Rolling Exponential Smoothing Daily Usage
    daily_effective_series = get_all_daily_effective_series()
    smoothed_daily_usage = engine.compute_exponential_daily_usage(
        daily_effective_series,
        fallback_rate=float(state.get('daily_avg_litres', config.DEFAULT_DAILY_AVG_LITRES))
    )

    # 3. Multi-Factor Degradation Evaluation
    health = engine.evaluate_health(
        total_raw_litres=state.get('total_raw_litres', 0.0),
        total_effective_litres=state.get('total_effective_litres', 0.0),
        daily_usage_rate=smoothed_daily_usage
    )

    # 4. Daily aggregations and cumulative depletion trajectory for Chart.js
    daily_trends = get_daily_summary(days_limit=30)
    depletion_trajectory = get_depletion_trajectory(limit=40)

    # 5. Recent telemetry logs (latest 15)
    recent_logs = get_telemetry_history(limit=15)

    return {
        "status": "success",
        "system_state": {
            "device_id": state.get('device_id', 'esp32_01'),
            "sensor_status": sensor_status,
            "last_sensor_ping": state.get('last_sensor_ping'),
            "watchdog_elapsed_seconds": seconds_elapsed,
            "watchdog_timeout_seconds": config.WATCHDOG_TIMEOUT_SECONDS,
            "last_updated": state.get('last_updated')
        },
        "prognostics": health,
        "daily_trends": daily_trends,
        "depletion_trajectory": depletion_trajectory,
        "recent_logs": recent_logs,
        "constants": {
            "base_tds_ppm": config.BASE_TDS_PPM,
            "turbulence_flow_threshold_lpm": config.TURBULENCE_FLOW_THRESHOLD_LPM,
            "turbulence_stress_factor": config.TURBULENCE_STRESS_FACTOR,
            "sensor_api_key_configured": bool(config.SENSOR_API_KEY)
        }
    }


# ====================================================================
# Web Routes
# ====================================================================

@app.route('/')
def index():
    """Render main AquaGuard IQ telemetry dashboard."""
    return render_template('index.html')


@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Return real-time multi-factor filter metrics, status, and trend data."""
    payload = build_full_metrics_payload()
    return jsonify(payload), 200


@app.route('/api/sensor-data', methods=['POST'])
def receive_sensor_data():
    """
    ESP32 IoT Ingestion Endpoint with Authentication & Outlier Filtering.
    Headers:
        X-Sensor-API-Key: AG-IQ-SECRET-KEY-2026
    JSON Payload:
        {
            "device_id": "esp32_01",
            "litres_flowed": 1.25,
            "flow_rate_lpm": 2.4,
            "tds_ppm": 380.0
        }
    """
    if not request.is_json:
        return jsonify({"error": "Request body must be valid application/json"}), 400

    payload = request.get_json(silent=True) or {}

    # 1. IoT Security & Anomaly Validation
    is_valid, message, status_code = validate_sensor_payload(request.headers, payload)
    if not is_valid:
        return jsonify({
            "status": "rejected",
            "error": message,
            "status_code": status_code
        }), status_code

    device_id = str(payload.get('device_id', 'esp32_01')).strip() or 'esp32_01'
    litres_flowed = float(payload.get('litres_flowed', 0.0))
    flow_rate_lpm = float(payload.get('flow_rate_lpm', 2.0))
    tds_ppm = float(payload.get('tds_ppm', config.DEFAULT_RAW_TDS_PPM))

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Identify whether this is a simulated endpoint test or real physical hardware
    is_simulated = bool(payload.get('is_simulation', False)) or any(
        tag in device_id.upper() for tag in ('TEST', 'SIM')
    )

    # 2. Update Hardware Watchdog Heartbeat
    # Rule 6: Never label simulated hardware handshakes as real hardware connections.
    if not is_simulated:
        update_system_state(
            sensor_status='ESP32_CONNECTED',
            last_sensor_ping=now_str,
            device_id=device_id
        )

    # 3. If water flowed, calculate Multi-Factor Degradation and store record
    record = None
    if litres_flowed > 0:
        k_tds, k_flow = engine.calculate_factors(flow_rate_lpm, tds_ppm)
        effective_litres = engine.calculate_degradation(litres_flowed, flow_rate_lpm, tds_ppm)

        record = insert_telemetry(
            device_id=device_id,
            source='SIMULATED' if is_simulated else 'SENSOR',
            event_type='Simulated Endpoint Test' if is_simulated else 'Hardware Telemetry',
            raw_litres=litres_flowed,
            flow_rate=flow_rate_lpm,
            tds_ppm=tds_ppm,
            k_tds=k_tds,
            k_flow=k_flow,
            effective_litres=effective_litres,
            timestamp=now_str
        )

    response_data = build_full_metrics_payload()
    prognostics = response_data["prognostics"]
    return jsonify({
        "status": "accepted",
        "message": ("Simulated hardware handshake validated and logged (Physical hardware connection remains in simulation mode)"
                    if is_simulated
                    else ("Telemetry processed and degradation logged" if record else "Hardware ping acknowledged")),
        "device_id": device_id,
        "is_simulated": is_simulated,
        "recorded": bool(record),
        "ingested_record": record,
        "effective_wear_litres": effective_litres if record else 0.0,
        "metrics": prognostics,
        "prognostics": prognostics,
        "total_usage": prognostics.get("total_raw_litres", 0.0),
        "remaining_capacity": prognostics.get("remaining_capacity_litres", 0.0),
        "prognostic_status": prognostics.get("status_badge", "Operational"),
        "system_state": response_data["system_state"]
    }), 200


@app.route('/api/add-usage', methods=['POST'])
def add_simulated_usage():
    """
    Simulation Dispense Endpoint.
    JSON Payload:
        {
            "litres": 5.0,
            "flow_rate_lpm": 2.2,
            "tds_ppm": 350.0,
            "event_type": "Cooking Dispense"
        }
    """
    data = request.get_json(silent=True) or {}
    try:
        litres = float(data.get('litres', 0.0))
    except (ValueError, TypeError):
        return jsonify({"error": "Litres must be numeric"}), 400

    if litres <= 0:
        return jsonify({"error": "Litres must be greater than zero"}), 400

    flow_rate = float(data.get('flow_rate_lpm', 2.2))
    tds_ppm = float(data.get('tds_ppm', config.DEFAULT_RAW_TDS_PPM))
    event_type = data.get('event_type', 'Manual Simulation')

    state = get_system_state()
    device_id = state.get('device_id', 'esp32_sim_01')

    # Calculate degradation factors
    k_tds, k_flow = engine.calculate_factors(flow_rate, tds_ppm)
    effective_litres = engine.calculate_degradation(litres, flow_rate, tds_ppm)

    record = insert_telemetry(
        device_id=device_id,
        source='SIMULATED',
        event_type=event_type,
        raw_litres=litres,
        flow_rate=flow_rate,
        tds_ppm=tds_ppm,
        k_tds=k_tds,
        k_flow=k_flow,
        effective_litres=effective_litres
    )

    metrics_payload = build_full_metrics_payload()
    prognostics = metrics_payload["prognostics"]
    return jsonify({
        "status": "success",
        "message": f"Injected {litres:.2f} L (Effective Wear: {effective_litres:.2f} L)",
        "record": record,
        "added_record": record,
        "metrics": prognostics,
        "prognostics": prognostics,
        "total_usage": prognostics.get("total_raw_litres", 0.0),
        "remaining_capacity": prognostics.get("remaining_capacity_litres", 0.0),
        "prognostic_status": prognostics.get("status_badge", "Operational")
    }), 200


@app.route('/api/config', methods=['POST'])
@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update rated capacity and daily average baseline usage."""
    data = request.get_json(silent=True) or {}
    rated = None
    daily = None

    if 'rated_capacity_litres' in data or 'rated_capacity' in data:
        try:
            val = float(data.get('rated_capacity_litres', data.get('rated_capacity', 0.0)))
            if val > 0:
                rated = val
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid rated_capacity_litres"}), 400

    if 'daily_avg_litres' in data or 'daily_target_litres' in data or 'daily_avg' in data:
        try:
            val = float(data.get('daily_avg_litres', data.get('daily_target_litres', data.get('daily_avg', 0.0))))
            if val > 0:
                daily = val
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid daily_avg_litres"}), 400

    update_system_state(rated_capacity=rated, daily_avg_litres=daily)
    metrics_payload = build_full_metrics_payload()

    return jsonify({
        "status": "success",
        "message": "System configuration updated successfully",
        "metrics": metrics_payload["prognostics"]
    }), 200


@app.route('/api/reset', methods=['POST'])
def reset_usage():
    """Clear telemetry logs or reseed from sample benchmark dataset."""
    data = request.get_json(silent=True) or {}
    seed_sample = bool(data.get('seed_sample', False) or data.get('mode') == 'sample')

    reset_database(seed_sample=seed_sample, engine=engine)
    metrics_payload = build_full_metrics_payload()

    msg = "Usage logs cleared to 0 L." if not seed_sample else "Reset and reseeded 288 records from benchmark dataset."
    return jsonify({
        "status": "success",
        "message": msg,
        "metrics": metrics_payload["prognostics"]
    }), 200


@app.route('/api/history', methods=['GET'])
def get_history():
    """Return all telemetry records with pagination support."""
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    source = request.args.get('source', None)

    records = get_telemetry_history(limit=limit, offset=offset, source=source)
    return jsonify({
        "count": len(records),
        "limit": limit,
        "offset": offset,
        "records": records
    }), 200


@app.route('/api/export-csv', methods=['GET'])
def export_csv():
    """Export complete telemetry audit trail as a formatted CSV file."""
    records = get_telemetry_history(limit=None)
    # Reverse to chronological order for audit export
    records.reverse()

    state = get_system_state()
    rated = float(state.get('rated_capacity', config.DEFAULT_RATED_CAPACITY_LITRES))

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Record ID",
        "Timestamp",
        "Device ID",
        "Source",
        "Event Type",
        "Raw Volume (L)",
        "Flow Rate (L/min)",
        "TDS (PPM)",
        "TDS Factor (K_TDS)",
        "Flow Factor (K_Flow)",
        "Effective Wear (L)",
        "Cumulative Raw (L)",
        "Cumulative Effective (L)",
        "Remaining Capacity (L)",
        "Membrane Health (%)",
        "Prognostic Status"
    ])

    cum_raw = 0.0
    cum_eff = 0.0

    for r in records:
        raw_v = float(r.get('raw_litres', 0.0))
        eff_v = float(r.get('effective_litres', 0.0))
        cum_raw += raw_v
        cum_eff += eff_v

        rem = max(0.0, rated - cum_eff)
        health_pct = max(0.0, round(((rated - cum_eff) / rated) * 100.0, 1)) if rated > 0 else 0.0

        if health_pct < config.STATUS_ATTENTION_THRESHOLD_PCT or rem <= 0:
            status = "CRITICAL_REPLACE"
        elif health_pct <= config.STATUS_NORMAL_THRESHOLD_PCT:
            status = "ATTENTION_REQUIRED"
        else:
            status = "NORMAL"

        writer.writerow([
            r.get("record_id", ""),
            r.get("timestamp", ""),
            r.get("device_id", ""),
            r.get("source", ""),
            r.get("event_type", ""),
            f"{raw_v:.2f}",
            f"{float(r.get('flow_rate', 0.0)):.2f}",
            f"{float(r.get('tds_ppm', 0.0)):.1f}",
            f"{float(r.get('k_tds', 1.0)):.4f}",
            f"{float(r.get('k_flow', 1.0)):.2f}",
            f"{eff_v:.2f}",
            f"{cum_raw:.2f}",
            f"{cum_eff:.2f}",
            f"{rem:.2f}",
            f"{health_pct:.1f}%",
            status
        ])

    csv_data = output.getvalue()
    output.close()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=aqua_guard_iq_report.csv"
        }
    )


# ====================================================================
# Application Lifecycle & Boot
# ====================================================================

if __name__ == '__main__':
    print("=" * 65)
    print("  AquaGuard IQ Enterprise v2.0 - Water Purifier Telemetry Hub")
    print("  AtomQUEST Track 2: Filter Prognostics & IoT Ingestion")
    print(f"  Database Path: {config.DB_PATH}")
    print(f"  IoT Security Key: {config.SENSOR_API_KEY}")
    print("=" * 65)
    init_db(seed_if_empty=True)
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.FLASK_DEBUG)
