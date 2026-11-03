"""
AquaGuard IQ - SQLite Persistence Manager
Enterprise-Grade v2.0 Production Prototype
AtomQUEST Track 2: Water Purifier Prognostics & IoT Telemetry
"""

import os
import sqlite3
import csv
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import config


def get_db_connection() -> sqlite3.Connection:
    """Creates a thread-safe connection to the SQLite database."""
    os.makedirs(config.DATABASE_DIR, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db(seed_if_empty: bool = True):
    """Initializes the SQLite database with the schema."""
    os.makedirs(config.DATABASE_DIR, exist_ok=True)
    conn = get_db_connection()
    try:
        with open(config.SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema_script = f.read()
        conn.executescript(schema_script)
        conn.commit()

        # If telemetry table is empty and sample data exists, pre-seed
        if seed_if_empty:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM telemetry;")
            row = cursor.fetchone()
            if row and row['cnt'] == 0 and os.path.exists(config.SAMPLE_CSV_PATH):
                from modules.estimator import PrognosticEngine
                engine = PrognosticEngine()
                seed_benchmark_data(conn, config.SAMPLE_CSV_PATH, engine)
    finally:
        conn.close()


def get_system_state() -> Dict[str, Any]:
    """Retrieves the current singleton system state."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM system_state WHERE id = 1;")
        row = cursor.fetchone()
        if row:
            return dict(row)
        else:
            # Fallback re-insert
            conn.execute("""
                INSERT OR REPLACE INTO system_state (
                    id, total_raw_litres, total_effective_litres, rated_capacity, 
                    daily_avg_litres, sensor_status, device_id, last_updated
                ) VALUES (1, 0.0, 0.0, 3000.0, 15.0, 'SIMULATION_MODE', 'esp32_01', datetime('now', 'localtime'));
            """)
            conn.commit()
            cursor.execute("SELECT * FROM system_state WHERE id = 1;")
            return dict(cursor.fetchone())
    finally:
        conn.close()


def update_system_state(
    rated_capacity: Optional[float] = None,
    daily_avg_litres: Optional[float] = None,
    sensor_status: Optional[str] = None,
    last_sensor_ping: Optional[str] = None,
    device_id: Optional[str] = None
) -> Dict[str, Any]:
    """Updates operational parameters in the singleton system state table."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        fields = []
        values = []

        if rated_capacity is not None:
            fields.append("rated_capacity = ?")
            values.append(float(rated_capacity))
        if daily_avg_litres is not None:
            fields.append("daily_avg_litres = ?")
            values.append(float(daily_avg_litres))
        if sensor_status is not None:
            fields.append("sensor_status = ?")
            values.append(str(sensor_status))
        if last_sensor_ping is not None:
            fields.append("last_sensor_ping = ?")
            values.append(str(last_sensor_ping))
        if device_id is not None:
            fields.append("device_id = ?")
            values.append(str(device_id))

        fields.append("last_updated = datetime('now', 'localtime')")

        query = f"UPDATE system_state SET {', '.join(fields)} WHERE id = 1;"
        cursor.execute(query, values)
        conn.commit()

        cursor.execute("SELECT * FROM system_state WHERE id = 1;")
        return dict(cursor.fetchone())
    finally:
        conn.close()


def insert_telemetry(
    device_id: str,
    source: str,
    event_type: str,
    raw_litres: float,
    flow_rate: float,
    tds_ppm: float,
    k_tds: float,
    k_flow: float,
    effective_litres: float,
    timestamp: Optional[str] = None,
    record_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Inserts a validated telemetry event and updates cumulative totals atomically.
    """
    rec_id = record_id or f"telemetry_{uuid.uuid4().hex[:10]}"
    ts = timestamp or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # 1. Insert telemetry log
        cursor.execute("""
            INSERT INTO telemetry (
                record_id, timestamp, device_id, source, event_type, 
                raw_litres, flow_rate, tds_ppm, k_tds, k_flow, effective_litres
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            rec_id, ts, device_id, source, event_type, 
            round(raw_litres, 2), round(flow_rate, 2), round(tds_ppm, 1),
            round(k_tds, 4), round(k_flow, 2), round(effective_litres, 2)
        ))

        # 2. Atomically update system state cumulative counters
        cursor.execute("""
            UPDATE system_state 
            SET total_raw_litres = ROUND(total_raw_litres + ?, 2),
                total_effective_litres = ROUND(total_effective_litres + ?, 2),
                last_updated = datetime('now', 'localtime')
            WHERE id = 1;
        """, (round(raw_litres, 2), round(effective_litres, 2)))

        conn.commit()

        cursor.execute("SELECT * FROM telemetry WHERE record_id = ?;", (rec_id,))
        return dict(cursor.fetchone())
    finally:
        conn.close()


def get_telemetry_history(limit: Optional[int] = 50, offset: int = 0, source: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetches chronological telemetry logs."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM telemetry"
        params = []

        if source:
            query += " WHERE source = ?"
            params.append(source)

        query += " ORDER BY id DESC"

        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params.extend([int(limit), int(offset)])

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_daily_summary(days_limit: int = 30) -> List[Dict[str, Any]]:
    """
    Aggregates daily raw and effective water consumption for charts.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                SUBSTR(timestamp, 1, 10) as date_key,
                ROUND(SUM(raw_litres), 2) as daily_raw_litres,
                ROUND(SUM(effective_litres), 2) as daily_effective_litres,
                ROUND(AVG(flow_rate), 2) as avg_flow_rate,
                ROUND(AVG(tds_ppm), 1) as avg_tds_ppm,
                COUNT(*) as event_count
            FROM telemetry
            GROUP BY date_key
            ORDER BY date_key ASC;
        """)
        rows = [dict(r) for r in cursor.fetchall()]
        return rows[-days_limit:] if days_limit else rows
    finally:
        conn.close()


def get_all_daily_effective_series() -> List[float]:
    """Returns chronological list of daily effective litres for exponential smoothing."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ROUND(SUM(effective_litres), 2) as daily_effective
            FROM telemetry
            GROUP BY SUBSTR(timestamp, 1, 10)
            ORDER BY SUBSTR(timestamp, 1, 10) ASC;
        """)
        return [float(r['daily_effective']) for r in cursor.fetchall()]
    finally:
        conn.close()


def get_depletion_trajectory(limit: int = 40) -> List[Dict[str, Any]]:
    """
    Returns progressive cumulative raw & effective points for the Depletion Curve.
    Ensures a smooth, multi-point trajectory even when telemetry is recorded on a single day.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, timestamp, raw_litres, effective_litres
            FROM telemetry
            ORDER BY id ASC;
        """)
        rows = cursor.fetchall()

        trajectory = [{
            "label": "Start (0 L)",
            "cum_raw": 0.0,
            "cum_eff": 0.0
        }]

        if not rows:
            return trajectory

        total_rows = len(rows)
        if total_rows > limit:
            step = total_rows / float(limit)
            sampled_indices = set(int(round(i * step)) for i in range(limit))
            sampled_indices.add(total_rows - 1)
        else:
            sampled_indices = set(range(total_rows))

        cum_raw = 0.0
        cum_eff = 0.0
        for idx, row in enumerate(rows):
            cum_raw += float(row['raw_litres'] or 0.0)
            cum_eff += float(row['effective_litres'] or 0.0)
            if idx in sampled_indices:
                ts = row['timestamp'] or ''
                if len(ts) >= 16:
                    time_label = ts[11:16]
                elif ts:
                    time_label = ts
                else:
                    time_label = f"#{idx+1}"
                trajectory.append({
                    "label": time_label,
                    "cum_raw": round(cum_raw, 2),
                    "cum_eff": round(cum_eff, 2)
                })
        return trajectory
    finally:
        conn.close()


def seed_benchmark_data(conn: sqlite3.Connection, csv_path: str, engine):
    """Seeds the SQLite database from sample_water_usage.csv with computed multi-factor degradation."""
    if not os.path.exists(csv_path):
        return

    records_to_insert = []
    total_raw = 0.0
    total_effective = 0.0

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            vol = float(row.get('estimated_volume_litres') or row.get('litres_flowed') or 0.0)
            flow = float(row.get('simulated_flow_rate_lpm') or row.get('flow_rate_lpm') or 2.0)
            tds = float(row.get('simulated_tds_ppm') or config.DEFAULT_RAW_TDS_PPM)
            ts = row.get('timestamp') or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            event = row.get('event_type') or 'Sample Usage'

            k_tds, k_flow = engine.calculate_factors(flow, tds)
            effective = engine.calculate_degradation(vol, flow, tds)

            total_raw += vol
            total_effective += effective

            records_to_insert.append((
                f"rec_{i+1:04d}", ts, "esp32_sim_01", "SIMULATED", event,
                round(vol, 2), round(flow, 2), round(tds, 1),
                round(k_tds, 4), round(k_flow, 2), round(effective, 2)
            ))

    cursor = conn.cursor()
    cursor.executemany("""
        INSERT OR REPLACE INTO telemetry (
            record_id, timestamp, device_id, source, event_type,
            raw_litres, flow_rate, tds_ppm, k_tds, k_flow, effective_litres
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, records_to_insert)

    cursor.execute("""
        UPDATE system_state 
        SET total_raw_litres = ?,
            total_effective_litres = ?,
            last_updated = datetime('now', 'localtime')
        WHERE id = 1;
    """, (round(total_raw, 2), round(total_effective, 2)))
    conn.commit()


def reset_database(seed_sample: bool = False, engine = None) -> Dict[str, Any]:
    """Clears all telemetry and resets the cumulative counter to 0, or reseeds benchmark dataset."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM telemetry;")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'telemetry';")
        cursor.execute("""
            UPDATE system_state 
            SET total_raw_litres = 0.0,
                total_effective_litres = 0.0,
                sensor_status = 'SIMULATION_MODE',
                last_sensor_ping = NULL,
                last_updated = datetime('now', 'localtime')
            WHERE id = 1;
        """)
        conn.commit()

        if seed_sample and os.path.exists(config.SAMPLE_CSV_PATH) and engine:
            seed_benchmark_data(conn, config.SAMPLE_CSV_PATH, engine)

        cursor.execute("SELECT * FROM system_state WHERE id = 1;")
        return dict(cursor.fetchone())
    finally:
        conn.close()

