-- ====================================================================
-- AquaGuard IQ - Enterprise v2.0 Database Schema (SQLite)
-- AtomQUEST Track 2: Water Purifier Prognostics & IoT Telemetry
-- ====================================================================

-- 1. Telemetry Ingestion Log
CREATE TABLE IF NOT EXISTS telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id TEXT UNIQUE NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT (datetime('now', 'localtime')),
    device_id TEXT NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('SIMULATED', 'SENSOR')),
    event_type TEXT NOT NULL DEFAULT 'Water Dispense',
    raw_litres REAL NOT NULL,
    flow_rate REAL NOT NULL,
    tds_ppm REAL NOT NULL DEFAULT 350.0,
    k_tds REAL NOT NULL DEFAULT 1.2,
    k_flow REAL NOT NULL DEFAULT 1.0,
    effective_litres REAL NOT NULL
);

-- Indexing for rapid chronological reporting and aggregation
CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry(timestamp);
CREATE INDEX IF NOT EXISTS idx_telemetry_source ON telemetry(source);
CREATE INDEX IF NOT EXISTS idx_telemetry_device ON telemetry(device_id);

-- 2. System State & Prognostic Parameters Singleton Table
CREATE TABLE IF NOT EXISTS system_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    total_raw_litres REAL NOT NULL DEFAULT 0.0,
    total_effective_litres REAL NOT NULL DEFAULT 0.0,
    rated_capacity REAL NOT NULL DEFAULT 3000.0,
    daily_avg_litres REAL NOT NULL DEFAULT 15.0,
    sensor_status TEXT NOT NULL DEFAULT 'SIMULATION_MODE' 
        CHECK (sensor_status IN ('ESP32_CONNECTED', 'SIMULATION_MODE', 'SENSOR_OFFLINE_FALLBACK_ACTIVE')),
    last_sensor_ping DATETIME,
    device_id TEXT NOT NULL DEFAULT 'esp32_01',
    last_updated DATETIME NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- Initialize default singleton state if not present
INSERT OR IGNORE INTO system_state (
    id, total_raw_litres, total_effective_litres, rated_capacity, 
    daily_avg_litres, sensor_status, device_id, last_updated
) VALUES (
    1, 0.0, 0.0, 3000.0, 
    15.0, 'SIMULATION_MODE', 'esp32_01', datetime('now', 'localtime')
);

