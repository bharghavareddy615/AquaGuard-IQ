# AquaGuard IQ

> **A Data-Driven Filter-Life Monitoring and Predictive Maintenance System for Water Purifiers**  
> **Competition:** atomQUEST 2026 | **Track 2:** Water Purifier | **Area:** Prognostics of filter failure using data analytics  
> **Team:** ProjectX | **Institution:** Amrita Vishwa Vidyapeetham | **Department:** Artificial Intelligence and Data Science (AI&DS)  

---

## ⚠️ Important Constraint & Simulation Disclaimer

**This repository contains a 100% software-only prototype.**  
- **No physical hardware** (ESP32, Arduino, Hall-effect flow sensors, TDS probes) is attached or required.
- All water flow measurements, cumulative usage figures, and sensor trends are **synthetically generated simulation data** designed to demonstrate telemetry handling and prognostic pipelines.
- **Safety Disclaimer:** AquaGuard IQ does **not** certify drinking-water safety or guarantee detection of all physical membrane ruptures or microbiological contamination.
- The proposed engineering targets (±10% volume estimation error, ≥95% flow-event detection) are **future physical test-bench targets**, not achieved experimental results.

---

## 🌟 Key Features

1. **Home / Overview Dashboard:**
   - Real-time simulated flow rate ($L/\text{min}$), cumulative volume ($L$), usage percentage ($\%$), and remaining capacity.
   - Dual-criteria maintenance status badges: `Normal`, `Moderate Usage`, `Service Soon`, `Capacity Reached`.
   - Next service forecast and capacity burn-down gauge.

2. **Interactive Simulation Engine:**
   - Button-driven, deterministic flow events (No freezing background loops).
   - Flow-rate profiles: Low ($0.8-1.2\text{ L/min}$), Normal ($1.8-2.5\text{ L/min}$), High ($3.0-4.5\text{ L/min}$), and Custom.
   - Reproducible synthetic dataset generator with adjustable duration and random seed.
   - Batch simulation shortcuts ($+100\text{L}, +500\text{L}, +1500\text{L}$) and full filter reset.

3. **Filter-Life Estimator:**
   - Transparent mathematical model calculating cumulative volume, remaining rated capacity, and remaining usable days.
   - User-configurable rated capacity ($500 - 20,000\text{ L}$) and service intervals ($30 - 730\text{ days}$).
   - Configurable moderate ($70\%$) and critical service ($85\%$) advisory thresholds.

4. **Interactive Plotly Visualizations:**
   - Cumulative consumption vs rated capacity limit.
   - Daily water consumption profile with mean consumption line.
   - Capacity burn-down trajectory.
   - Event-level flow rate distribution with nominal RO output zones.
   - Simulated auxiliary TDS drift demonstrating future sensor fusion.

5. **Data Analytics & Demonstration Machine Learning:**
   - Transparent rule-based baseline comparison against machine-learning prognostics.
   - Random Forest demonstration trained on synthetic feature spaces.
   - Feature importance rankings and live interactive inference tester.
   - Explicit disclaimer highlighting that synthetic accuracy does not establish real-world failure prediction.

6. **Data Management:**
   - Download current simulation telemetry as CSV.
   - Download bundled reference 60-day sample dataset (`data/sample_water_usage.csv`).
   - Upload and schema-validate external CSV datasets.

---

## 📁 Project Structure

```text
AtomQuest/
├── app.py                      # Main Streamlit web application
├── requirements.txt            # Python dependencies
├── README.md                   # Setup and methodology documentation
├── data/
│   └── sample_water_usage.csv  # Bundled 60-day reproducible synthetic telemetry
└── modules/
    ├── __init__.py             # Module package marker
    ├── simulation.py           # Flow generation and event simulation engine
    ├── estimator.py            # Mathematical estimation & prognostic modeling
    ├── charts.py               # Interactive Plotly engineering visualizations
    └── data_manager.py         # CSV parsing, schema validation, and persistence
```

---

## 🚀 Setup & Execution Instructions (Windows PowerShell)

Follow these exact steps in Windows PowerShell to set up and run AquaGuard IQ:

### Step 1: Verify Python Installation
Ensure Python 3.10 or newer is installed on your Windows system:
```powershell
py --version
```
*(Expected output: `Python 3.10.x` or higher, e.g., `Python 3.14.0`)*

### Step 2: Create a Virtual Environment
Navigate to the project root directory and create a localized virtual environment:
```powershell
cd C:\Users\bharg\Desktop\Projects\AtomQuest
py -m venv .venv
```

### Step 3: Activate the Virtual Environment
Activate the environment in Windows PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
```

> **Troubleshooting Execution Policy in PowerShell:**  
> If PowerShell displays a script execution policy error (`PSSecurityException` or `running scripts is disabled`), run:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> .\.venv\Scripts\Activate.ps1
> ```

### Step 4: Install Dependencies
Upgrade pip and install the required libraries:
```powershell
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

### Step 5: Launch AquaGuard IQ
Launch the Streamlit dashboard in your web browser:
```powershell
py -m streamlit run app.py
```
Streamlit will output local and network URLs (typically `http://localhost:8501`). Your default browser will open automatically.

---

## 🛠️ Common Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **Port 8501 already in use** | Another Streamlit app or background service is occupying the default port | Launch on a different port: `py -m streamlit run app.py --server.port 8502` |
| **ModuleNotFoundError** | Dependencies installed in global Python rather than active `.venv` | Ensure `(.venv)` is shown in your terminal prompt before running `py -m streamlit run app.py` |
| **Browser doesn't open automatically** | Headless or default browser configuration | Open any browser manually and navigate to `http://localhost:8501` |
| **CSV upload error** | Uploaded file lacks required telemetry columns | Download the bundled sample from the Data Management tab to inspect the required column format |

---

## 🔬 Hardware Sourcing & Future Plan (Round 2)

| Component | Target Specification | Indicative Cost (₹) |
| :--- | :--- | :--- |
| **ESP32 NodeMCU Board** | 30-pin dual-core Wi-Fi/BLE microcontroller | ₹350 – ₹500 |
| **Inline Water-Flow Sensor** | YF-S201 (1/2" Hall-effect turbine, $1-30\text{ L/min}$) | ₹200 – ₹350 |
| **Wiring, Tubing & Connectors** | Food-grade 1/4" to 1/2" quick-connect push fittings | ₹200 – ₹350 |
| **Calibration Rig** | Graduated cylinder, low-voltage 5V USB source | ₹200 – ₹400 |
| **Total Estimated Hardware Budget** | **₹1,050 – ₹2,000** |

---

## 📄 License & Attribution
Developed by **ProjectX** (Amrita Vishwa Vidyapeetham) for the **atomQUEST 2026 Innovation Competition (Track 2: Water Purifier)**.  
Software is provided for academic demonstration, peer review, and evaluation purposes.
