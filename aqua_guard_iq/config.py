"""
AquaGuard IQ - Configuration & Threshold Parameters
Enterprise-Grade v2.0 Production Prototype
AtomQUEST Track 2: Water Purifier Prognostics & IoT Telemetry
"""

import os

# Base directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, 'database')
DB_PATH = os.path.join(DATABASE_DIR, 'aquaguard.db')
SCHEMA_PATH = os.path.join(DATABASE_DIR, 'schema.sql')
DATA_DIR = os.path.join(BASE_DIR, 'data')
SAMPLE_CSV_PATH = os.path.join(DATA_DIR, 'sample_water_usage.csv')

# IoT Security & Authentication
SENSOR_API_KEY = os.getenv('SENSOR_API_KEY', 'AG-IQ-SECRET-KEY-2026')
API_KEY_HEADER = 'X-Sensor-API-Key'

# Hardware Watchdog Parameters
WATCHDOG_TIMEOUT_SECONDS = int(os.getenv('WATCHDOG_TIMEOUT_SECONDS', 300))

# Outlier & Sensor Anomaly Thresholds
MAX_FLOW_RATE_LPM = float(os.getenv('MAX_FLOW_RATE_LPM', 15.0))
MIN_FLOW_RATE_LPM = 0.0
MIN_LITRES_FLOWED = 0.0

# Multi-Factor Degradation Engine Constants
BASE_TDS_PPM = 250.0
TURBULENCE_FLOW_THRESHOLD_LPM = 3.5  # High-wear threshold (>3.5 L/min)
TURBULENCE_STRESS_FACTOR = 1.15      # 15% accelerated membrane wear
DEFAULT_RAW_TDS_PPM = 350.0          # Typical household raw tap water TDS

# Prognostic Filter Life Thresholds
DEFAULT_RATED_CAPACITY_LITRES = 3000.0
DEFAULT_DAILY_AVG_LITRES = 15.0

# Health Score & RUL Status Thresholds
STATUS_NORMAL_THRESHOLD_PCT = 30.0       # > 30% remaining is Normal
STATUS_ATTENTION_THRESHOLD_PCT = 15.0    # 15% - 30% is Attention Required, < 15% is Critical Replace

# Exponential Smoothing Alpha for Daily Usage Forecasting
EXPONENTIAL_SMOOTHING_ALPHA = 0.3

# Server Settings
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'true').lower() in ('true', '1', 'yes')

