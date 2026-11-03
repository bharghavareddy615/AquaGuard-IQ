"""
AquaGuard IQ v2.0 - Enterprise Water Purifier Telemetry & Prognostics Hub
AtomQUEST Track 2: Filter Degradation Forecasting & IoT Stream
Root Entry Point: Launches the AquaGuard IQ Flask application
"""

import os
import sys

# Ensure aqua_guard_iq package directory is on Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(CURRENT_DIR, 'aqua_guard_iq')
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from app import app, init_db, config

if __name__ == '__main__':
    print("=" * 65)
    print("  AquaGuard IQ Enterprise v2.0 - Water Purifier Telemetry Hub")
    print("  AtomQUEST Track 2: Filter Prognostics & IoT Ingestion")
    print(f"  Database Path: {config.DB_PATH}")
    print(f"  IoT Security Key: {config.SENSOR_API_KEY}")
    print("=" * 65)
    init_db(seed_if_empty=True)
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.FLASK_DEBUG)
