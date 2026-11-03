# AquaGuard IQ v2.0 💧
**Enterprise-Grade Production Prototype | AtomQUEST Track 2: Water Purifier**
*Prognostics of Filter Failure, Multi-Factor Degradation & IoT Telemetry Hub*

---

## 🌟 Executive Summary

**AquaGuard IQ v2.0** upgrades basic water volume counters into an enterprise-grade, physics-informed prognostic maintenance system. Instead of relying on naive linear volume subtraction, AquaGuard IQ computes an **Effective Degradation Volume** based on raw water hardness (TDS), fluid turbulence stress factors, and 7-day rolling exponential smoothing usage patterns.

It features hardware-enforced authentication, real-time outlier rejection, an automated 300-second hardware disconnection watchdog, SQLite WAL persistence, and an interactive cyan-navy telemetry dashboard.

---

## 📐 Directory Structure

```
aqua_guard_iq/
│── app.py                   # Main Flask application & route controllers
│── config.py                # Environment parameters & threshold constants
│── requirements.txt         # Dependencies (flask, requests)
│── README.md                # Technical documentation & API Specs
│── database/
│   └── schema.sql           # SQLite DB creation script
│── modules/
│   ├── __init__.py
│   ├── db.py                # SQLite persistence manager (Telemetry & Logs)
│   ├── estimator.py         # Advanced Multi-Factor Prognostic Engine & RUL
│   └── sensor_api.py        # ESP32 authentication, validation & outlier filtering
│── static/
│   ├── css/
│   │   └── style.css        # Professional cyan-navy telemetry dashboard UI
│   └── js/
│       ├── app.js           # Real-time state manager & API fetcher
│       └── charts.js        # Chart.js multi-axis depletion trend analytics
└── templates/
    └── index.html           # Full telemetry UI with live diagnostic modal
```

---

## 🔬 Multi-Factor Degradation Formulation (`modules/estimator.py`)

### 1. The Core Degradation Formula
$$\text{Effective\_Wear} = \text{Raw\_Volume} \times K_{\text{TDS}} \times K_{\text{Flow}}$$

### 2. Mineral Hardness Penalty ($K_{\text{TDS}}$)
Baseline pure water is set to $250\text{ PPM} \implies K_{\text{TDS}} = 1.0$. Mineral accumulation accelerates pore clogging on semi-permeable RO membranes:
$$K_{\text{TDS}} = 1.0 + \max\left(0, \frac{\text{TDS} - 250}{500}\right)$$
- At $375\text{ PPM}$ (hard domestic tap water): $K_{\text{TDS}} = 1.25$ ($25\%$ wear acceleration).
- At $500\text{ PPM}$ (severe scale accumulation): $K_{\text{TDS}} = 1.50$ ($50\%$ wear acceleration).

### 3. Turbulence Stress Factor ($K_{\text{Flow}}$)
High dispense velocity generates trans-membrane pressure spikes:
$$K_{\text{Flow}} = \begin{cases} 1.15 & \text{if } \text{Flow Rate} > 3.5\text{ L/min} \\ 1.00 & \text{otherwise} \end{cases}$$

### 4. Remaining Membrane Health Score & RUL
- **Health Score (%)**:
  $$\text{Health Score} = \max\left(0, \frac{\text{Rated Capacity} - \text{Total Effective Wear}}{\text{Rated Capacity}} \times 100\right)$$
- **7-Day Rolling Exponential Smoothing Daily Rate**:
  $$S_t = \alpha \cdot Y_t + (1 - \alpha) \cdot S_{t-1} \quad (\alpha = 0.3)$$
- **Remaining Useful Life (RUL in Days)**:
  $$\text{RUL} = \left\lfloor \frac{\text{Remaining Capacity}}{S_t} \right\rfloor$$

### 5. Tri-Tier Prognostic Classification
| Status | Health Score Threshold | RUL Threshold | System Action |
| :--- | :--- | :--- | :--- |
| **`NORMAL`** | $> 30\%$ | $> 21$ Days | Normal operation; optimal flow dynamics |
| **`ATTENTION_REQUIRED`** | $15\% - 30\%$ | $8 - 21$ Days | Pre-order replacement cartridge buffer |
| **`CRITICAL_REPLACE`** | $< 15\%$ | $\le 7$ Days | Immediate replacement; risk of microbial breakthrough |

---

## 🔒 IoT Security & Hardware Watchdog (`modules/sensor_api.py`)

### 1. API Key Authentication
All physical ESP32 payloads must supply the HTTP header:
```http
X-Sensor-API-Key: AG-IQ-SECRET-KEY-2026
```
Invalid or missing headers return `HTTP 401 Unauthorized`.

### 2. Anomaly & Outlier Filtering
- Flow rate ceiling: `flow_rate_lpm > 15.0 L/min` triggers `HTTP 422 Unprocessable Entity` (sensor glitch rejection).
- Negative flow guard: Any negative volume or flow returns `HTTP 400 Bad Request`.

### 3. Hardware Disconnection Watchdog (300 Seconds)
If an active ESP32 sensor does not send a telemetry heartbeat for over **300 seconds**, the system automatically switches to:
```
SENSOR_OFFLINE_FALLBACK_ACTIVE
```
Visual indicators flash across the UI, alerting operators while the system continues logging simulated events safely.

---

## 🗄️ Database Architecture (`modules/db.py`)

Persistent storage uses SQLite with Write-Ahead Logging (`WAL` mode) at `aqua_guard_iq/database/aquaguard.db`:
- **`telemetry`**: Full chronological ingestion log with `record_id`, `timestamp`, `device_id`, `source` (`SENSOR` vs `SIMULATED`), `raw_litres`, `flow_rate`, `tds_ppm`, `k_tds`, `k_flow`, and `effective_litres`.
- **`system_state`**: Singleton state maintaining cumulative raw & effective litres, rated capacity, daily average, sensor status, and last heartbeat.

---

## 📡 REST API Specifications

### 1. Ingest Hardware Telemetry
- **Endpoint**: `POST /api/sensor-data`
- **Headers**:
  ```
  Content-Type: application/json
  X-Sensor-API-Key: AG-IQ-SECRET-KEY-2026
  ```
- **Payload**:
  ```json
  {
    "device_id": "esp32_01",
    "litres_flowed": 1.25,
    "flow_rate_lpm": 2.4,
    "tds_ppm": 380.0
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "status": "accepted",
    "message": "Telemetry processed and degradation logged",
    "device_id": "esp32_01",
    "recorded": true,
    "metrics": {
      "health_score_pct": 98.4,
      "rul_days": 182,
      "prognostic_status": "NORMAL"
    }
  }
  ```

### 2. Fetch Full Telemetry & Prognostics
- **Endpoint**: `GET /api/metrics`
- **Response**: Complete snapshot containing system state, watchdog counters, multi-factor metrics, daily trend series, and recent logs.

### 3. Simulate Dispense Event
- **Endpoint**: `POST /api/add-usage`
- **Payload**:
  ```json
  {
    "litres": 5.0,
    "flow_rate_lpm": 2.2,
    "tds_ppm": 350.0,
    "event_type": "Cooking & Food Prep"
  }
  ```

### 4. Download Formatted CSV Audit Trail
- **Endpoint**: `GET /api/export-csv`
- Returns an attachment `aquaguard_iq_v2_telemetry.csv` containing raw volumes, stress factors, effective wear, and health statuses.

---

## 🚀 Running on Windows

From the project root using PowerShell:

```powershell
# 1. Activate environment and install dependencies
.\.venv\Scripts\pip.exe install -r aqua_guard_iq\requirements.txt

# 2. Launch AquaGuard IQ v2.0
.\.venv\Scripts\python.exe aqua_guard_iq\app.py
```

Open your browser at: **`http://127.0.0.1:5000`**
