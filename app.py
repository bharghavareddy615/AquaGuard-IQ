"""
AquaGuard IQ - Main Streamlit Application
A Data-Driven Filter-Life Monitoring and Predictive Maintenance System for Water Purifiers.
Competition: atomQUEST 2026 | Track 2: Water Purifier | Area: Prognostics of Filter Failure
Team: ProjectX | Institute: Amrita Vishwa Vidyapeetham

IMPORTANT CONSTRAINT:
Software-only prototype. All telemetry is simulated. No physical sensors connected.
"""

import os
import streamlit as st
import pandas as pd
import numpy as np

from modules.estimator import (
    calculate_filter_metrics,
    get_status_badge_html,
    train_synthetic_prognostic_model,
    DEFAULT_RATED_CAPACITY_LITRES,
    DEFAULT_SERVICE_INTERVAL_DAYS,
    DEFAULT_DAILY_USAGE_LITRES,
    STATUS_NORMAL,
    STATUS_MODERATE,
    STATUS_SERVICE_SOON,
    STATUS_CAPACITY_REACHED,
    STATUS_COLORS
)
from modules.simulation import (
    generate_synthetic_dataset,
    simulate_single_event,
    PROFILE_LOW,
    PROFILE_NORMAL,
    PROFILE_HIGH,
    PROFILE_CUSTOM,
    FLOW_RANGES
)
from modules.charts import (
    plot_cumulative_water_usage,
    plot_daily_water_consumption,
    plot_capacity_gauge,
    plot_remaining_capacity_burndown,
    plot_flow_rate_trend,
    plot_simulated_tds_trend
)
from modules.data_manager import (
    load_bundled_sample_dataset,
    export_dataframe_to_csv,
    load_csv_from_upload,
    REQUIRED_COLUMNS
)

# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="AquaGuard IQ | Filter-Life Telemetry",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean, professional engineering CSS styling (light theme, high contrast)
st.markdown("""
<style>
    /* Font and base reset */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Top simulation banner */
    .sim-banner {
        background-color: #FEF3C7;
        border-left: 5px solid #D97706;
        color: #92400E;
        padding: 10px 16px;
        border-radius: 4px;
        font-size: 0.9rem;
        font-weight: 500;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    /* Engineering Metric Cards */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .metric-card:hover {
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.08);
    }
    .metric-title {
        color: #64748B;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .metric-value {
        color: #0F172A;
        font-size: 1.85rem;
        font-weight: 700;
        line-height: 1.2;
    }
    .metric-sub {
        color: #64748B;
        font-size: 0.82rem;
        margin-top: 4px;
    }
    
    /* Status Badge styling in cards */
    .badge-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    /* Section Headers */
    .section-header {
        color: #1E3A8A;
        font-size: 1.35rem;
        font-weight: 700;
        margin-top: 15px;
        margin-bottom: 12px;
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 6px;
    }

    /* Code & monospace accents */
    code, pre {
        font-family: 'JetBrains Mono', monospace;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# State Initialization
# ---------------------------------------------------------
if "telemetry_df" not in st.session_state:
    try:
        st.session_state.telemetry_df = load_bundled_sample_dataset()
    except Exception:
        st.session_state.telemetry_df = generate_synthetic_dataset(days=60, seed=42)

if "rated_capacity" not in st.session_state:
    st.session_state.rated_capacity = DEFAULT_RATED_CAPACITY_LITRES

if "service_interval_days" not in st.session_state:
    st.session_state.service_interval_days = float(DEFAULT_SERVICE_INTERVAL_DAYS)

if "daily_target_litres" not in st.session_state:
    st.session_state.daily_target_litres = DEFAULT_DAILY_USAGE_LITRES

if "mod_threshold" not in st.session_state:
    st.session_state.mod_threshold = 70.0

if "soon_threshold" not in st.session_state:
    st.session_state.soon_threshold = 85.0

if "simulation_paused" not in st.session_state:
    st.session_state.simulation_paused = False


# ---------------------------------------------------------
# Top Universal Simulation Banner
# ---------------------------------------------------------
def render_sim_banner():
    st.markdown("""
    <div class="sim-banner">
        <span>⚠️</span>
        <div>
            <strong>SIMULATION MODE — NO PHYSICAL SENSORS CONNECTED</strong> &nbsp;|&nbsp;
            <em>AquaGuard IQ (atomQUEST 2026, Track 2: Water Purifier).</em>
            All telemetry, flow rates, and sensor trends are synthetically generated for demonstration.
        </div>
    </div>
    """, unsafe_allow_html=True)


# Compute current telemetry metrics helper
def get_current_metrics():
    df = st.session_state.telemetry_df
    if df is not None and not df.empty:
        cum_vol = float(df["cumulative_volume_litres"].iloc[-1])
        elapsed_days = float(df["elapsed_days"].iloc[-1]) if "elapsed_days" in df.columns else len(df) / 5.0
        last_flow = float(df["simulated_flow_rate_lpm"].iloc[-1])
        last_timestamp = str(df["timestamp"].iloc[-1])
    else:
        cum_vol = 0.0
        elapsed_days = 0.0
        last_flow = 0.0
        last_timestamp = "N/A"

    metrics = calculate_filter_metrics(
        cumulative_volume_litres=cum_vol,
        rated_capacity_litres=st.session_state.rated_capacity,
        elapsed_days=elapsed_days,
        service_interval_days=st.session_state.service_interval_days,
        avg_daily_litres=st.session_state.daily_target_litres,
        mod_thresh=st.session_state.mod_threshold,
        soon_thresh=st.session_state.soon_threshold
    )
    return metrics, last_flow, last_timestamp


# ---------------------------------------------------------
# Sidebar Navigation & Settings
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/water.png", width=64)
    st.title("AquaGuard IQ")
    st.caption("Filter-Life Telemetry & Prognostics\natomQUEST 2026 — Track 2")

    st.markdown("---")
    
    page = st.radio(
        "Navigation",
        [
            "🏠 1. Home / Overview",
            "⚡ 2. Interactive Simulation",
            "⏱️ 3. Filter-Life Estimator",
            "📊 4. Interactive Charts",
            "🔬 5. Data Analytics & ML",
            "💾 6. Data Management",
            "📖 7. Methodology & About"
        ],
        index=0
    )

    st.markdown("---")
    st.markdown("### ⚙️ Quick System Parameters")
    
    # Adjustable Rated Capacity
    new_rated = st.number_input(
        "Rated Filter Capacity (L)",
        min_value=500.0,
        max_value=20000.0,
        value=float(st.session_state.rated_capacity),
        step=500.0,
        help="Hypothetical manufacturer rated volumetric limit for sediment/carbon filter media."
    )
    if new_rated != st.session_state.rated_capacity:
        st.session_state.rated_capacity = new_rated
        st.rerun()

    # Adjustable Service Interval
    new_interval = st.number_input(
        "Max Service Interval (Days)",
        min_value=30.0,
        max_value=730.0,
        value=float(st.session_state.service_interval_days),
        step=30.0,
        help="Recommended calendar replacement limit (typically 365 days / 12 months)."
    )
    if new_interval != st.session_state.service_interval_days:
        st.session_state.service_interval_days = new_interval
        st.rerun()

    # Average Daily Consumption
    new_daily = st.slider(
        "Estimated Daily Usage (L/day)",
        min_value=2.0,
        max_value=60.0,
        value=float(st.session_state.daily_target_litres),
        step=1.0,
        help="Expected daily drinking and cooking water consumption for the household."
    )
    if new_daily != st.session_state.daily_target_litres:
        st.session_state.daily_target_litres = new_daily
        st.rerun()

    st.markdown("---")
    
    # Live status badge preview in sidebar
    m, _, _ = get_current_metrics()
    st.markdown(f"**Current Status:** {get_status_badge_html(m.status)}", unsafe_allow_html=True)
    st.caption(f"Used: {m.cumulative_volume_litres:,.1f} L / {m.rated_capacity_litres:,.0f} L ({m.usage_percentage:.1f}%)")
    st.caption("🔒 *Simulated Data Only*")


# ---------------------------------------------------------
# PAGE 1: HOME / OVERVIEW
# ---------------------------------------------------------
if page == "🏠 1. Home / Overview":
    render_sim_banner()

    st.title("Water Purifier Telemetry Overview")
    st.markdown(
        "Real-time operational dashboard estimating cumulative water throughput, "
        "filter capacity consumption, and dual-criteria maintenance requirements."
    )

    metrics, last_flow, last_time = get_current_metrics()

    # Metric Cards in Row
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Simulated Flow Rate</div>
            <div class="metric-value">{last_flow:.2f} <span style="font-size:1rem;font-weight:400;">L/min</span></div>
            <div class="metric-sub">Last Event: {last_time[-8:] if last_time != 'N/A' else 'N/A'}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Cumulative Water Used</div>
            <div class="metric-value">{metrics.cumulative_volume_litres:,.1f} <span style="font-size:1rem;font-weight:400;">L</span></div>
            <div class="metric-sub">Elapsed: {metrics.elapsed_days:.0f} days</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Filter Capacity Used</div>
            <div class="metric-value">{metrics.usage_percentage:.1f}%</div>
            <div class="metric-sub">Rated: {metrics.rated_capacity_litres:,.0f} L</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Remaining Capacity</div>
            <div class="metric-value">{metrics.remaining_capacity_litres:,.1f} <span style="font-size:1rem;font-weight:400;">L</span></div>
            <div class="metric-sub">Days Left: ~{metrics.estimated_days_remaining if metrics.estimated_days_remaining is not None else 'N/A'} d</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        cfg = STATUS_COLORS.get(metrics.status, STATUS_COLORS[STATUS_NORMAL])
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid {cfg['hex']};">
            <div class="metric-title">Maintenance Status</div>
            <div style="margin-top: 6px;">{get_status_badge_html(metrics.status)}</div>
            <div class="metric-sub" style="margin-top: 8px;">Target: {metrics.projected_replacement_date if metrics.projected_replacement_date else 'Immediate'}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Status Recommendation & Prognostic Guidance Box
    rec_col, gauge_col = st.columns([3, 2])

    with rec_col:
        st.subheader("📋 Maintenance Advisory & Prognostic Status")
        
        if metrics.status == STATUS_NORMAL:
            st.success(
                f"**System Healthy (Normal Operation):** Cumulative water volume ({metrics.cumulative_volume_litres:.1f} L) "
                f"and operational duration ({metrics.elapsed_days:.0f} days) are comfortably within recommended limits. "
                "No filter replacement required at this time."
            )
        elif metrics.status == STATUS_MODERATE:
            st.warning(
                f"**Moderate Usage Detected:** Filter has consumed {metrics.usage_percentage:.1f}% of rated volumetric capacity "
                f"or {metrics.time_elapsed_percentage:.1f}% of recommended calendar life. Begin planning for spare replacement cartridges."
            )
        elif metrics.status == STATUS_SERVICE_SOON:
            st.warning(
                f"**Service Required Soon:** Filter has passed the 85% advisory threshold. "
                f"Remaining usable volume is approximately {metrics.remaining_capacity_litres:.1f} L "
                f"(~{metrics.estimated_days_remaining:.0f} days at {st.session_state.daily_target_litres:.0f} L/day). Schedule servicing."
            )
        else:
            st.error(
                f"**Rated Capacity Reached:** Volumetric capacity or calendar service interval limit reached! "
                "Filter media exhaustion imminent. Replacement recommended to prevent water flow restriction or particulate breakthrough."
            )

        st.info(
            f"**Evaluation Logic:** {metrics.status_reason}\n\n"
            f"*Note: Calculations assume an average household usage of {st.session_state.daily_target_litres:.1f} L/day. "
            "Estimates are derived from manufacturer ratings, not direct chemical contamination measurements.*"
        )

    with gauge_col:
        gauge_fig = plot_capacity_gauge(metrics.usage_percentage, metrics.status)
        st.plotly_chart(gauge_fig, use_container_width=True)

    # Mini Chart preview
    st.markdown("### 📈 Recent Telemetry Trajectory")
    chart_tab1, chart_tab2 = st.tabs(["Cumulative Volume", "Remaining Capacity Burn-down"])
    with chart_tab1:
        st.plotly_chart(
            plot_cumulative_water_usage(st.session_state.telemetry_df, rated_capacity=st.session_state.rated_capacity),
            use_container_width=True
        )
    with chart_tab2:
        st.plotly_chart(
            plot_remaining_capacity_burndown(st.session_state.telemetry_df, rated_capacity=st.session_state.rated_capacity),
            use_container_width=True
        )


# ---------------------------------------------------------
# PAGE 2: INTERACTIVE SIMULATION
# ---------------------------------------------------------
elif page == "⚡ 2. Interactive Simulation":
    render_sim_banner()

    st.title("Interactive Water-Flow Simulation")
    st.markdown(
        "Demonstrates deterministic, button-driven water dispensing events without background loops or Streamlit UI freezing. "
        "Allows testing how different dispensing profiles, flow rates, and volumes affect cumulative telemetry."
    )

    ctrl_col1, ctrl_col2 = st.columns([1, 1])

    with ctrl_col1:
        st.markdown("#### 🚰 Simulate Dispensing Event")
        profile = st.selectbox(
            "Select Flow-Rate Profile",
            [PROFILE_NORMAL, PROFILE_LOW, PROFILE_HIGH, PROFILE_CUSTOM],
            index=0,
            help="Simulates typical flow rates of different usage scenarios (drinking water, cooking pot refill, bottle filling)."
        )

        custom_rate = 2.0
        if profile == PROFILE_CUSTOM:
            custom_rate = st.slider("Custom Flow Rate (L/min)", min_value=0.2, max_value=6.0, value=2.0, step=0.1)

        dispense_vol = st.slider(
            "Dispensing Event Volume (Litres)",
            min_value=0.2,
            max_value=25.0,
            value=3.5,
            step=0.1,
            help="Simulated volume drawn during this water dispensing session."
        )

        # Dispense Action Button
        if st.button("💧 Simulate Water Dispense Event", use_container_width=True, type="primary"):
            st.session_state.telemetry_df = simulate_single_event(
                current_df=st.session_state.telemetry_df,
                flow_profile=profile,
                custom_flow_rate=custom_rate,
                volume_litres=dispense_vol,
                rated_capacity=st.session_state.rated_capacity,
                service_interval_days=st.session_state.service_interval_days,
                avg_daily_litres=st.session_state.daily_target_litres
            )
            st.success(f"Simulated {dispense_vol:.1f} L dispense event logged successfully!")
            st.rerun()

        # Batch Simulation Button
        st.markdown("---")
        st.markdown("#### ⚡ Batch Consumption Shortcut")
        add_col1, add_col2, add_col3 = st.columns(3)
        with add_col1:
            if st.button("+100 L Bulk Run"):
                st.session_state.telemetry_df = simulate_single_event(
                    current_df=st.session_state.telemetry_df,
                    flow_profile=PROFILE_HIGH,
                    custom_flow_rate=3.5,
                    volume_litres=100.0,
                    rated_capacity=st.session_state.rated_capacity,
                    service_interval_days=st.session_state.service_interval_days,
                    avg_daily_litres=st.session_state.daily_target_litres
                )
                st.rerun()
        with add_col2:
            if st.button("+500 L Accelerated"):
                st.session_state.telemetry_df = simulate_single_event(
                    current_df=st.session_state.telemetry_df,
                    flow_profile=PROFILE_HIGH,
                    custom_flow_rate=4.0,
                    volume_litres=500.0,
                    rated_capacity=st.session_state.rated_capacity,
                    service_interval_days=st.session_state.service_interval_days,
                    avg_daily_litres=st.session_state.daily_target_litres
                )
                st.rerun()
        with add_col3:
            if st.button("+1500 L Near End"):
                st.session_state.telemetry_df = simulate_single_event(
                    current_df=st.session_state.telemetry_df,
                    flow_profile=PROFILE_HIGH,
                    custom_flow_rate=4.0,
                    volume_litres=1500.0,
                    rated_capacity=st.session_state.rated_capacity,
                    service_interval_days=st.session_state.service_interval_days,
                    avg_daily_litres=st.session_state.daily_target_litres
                )
                st.rerun()

    with ctrl_col2:
        st.markdown("#### 🎲 Reproducible Synthetic Dataset Generator")
        st.caption("Generate a multi-month synthetic dataset with realistic daily variance and morning/evening demand peaks.")

        gen_days = st.slider("Dataset Duration (Days)", min_value=15, max_value=180, value=60, step=15)
        gen_seed = st.number_input("Random Seed (Reproducibility)", min_value=1, max_value=9999, value=42, step=1)

        if st.button("🔄 Generate Synthetic Dataset", use_container_width=True):
            with st.spinner("Generating reproducible simulation records..."):
                new_df = generate_synthetic_dataset(
                    days=gen_days,
                    daily_target_litres=st.session_state.daily_target_litres,
                    rated_capacity=st.session_state.rated_capacity,
                    service_interval_days=st.session_state.service_interval_days,
                    seed=int(gen_seed)
                )
                st.session_state.telemetry_df = new_df
            st.success(f"Generated {len(new_df)} synthetic dispensing records across {gen_days} operational days!")
            st.rerun()

        st.markdown("---")
        st.markdown("#### 🔁 Reset Filter State")
        if st.button("🧹 Reset to Brand New Filter (0 L Used)", use_container_width=True):
            # Create fresh dataset with 0 usage
            st.session_state.telemetry_df = generate_synthetic_dataset(days=1, daily_target_litres=0.1, seed=1)
            st.session_state.telemetry_df = st.session_state.telemetry_df.iloc[0:1].copy()
            st.session_state.telemetry_df["cumulative_volume_litres"] = 0.0
            st.session_state.telemetry_df["estimated_volume_litres"] = 0.0
            st.session_state.telemetry_df["usage_percentage"] = 0.0
            st.session_state.telemetry_df["elapsed_days"] = 0.0
            st.session_state.telemetry_df["remaining_capacity_litres"] = float(st.session_state.rated_capacity)
            st.session_state.telemetry_df["maintenance_status"] = STATUS_NORMAL
            st.success("Simulation reset: Fresh filter initialized at 0.0 L cumulative usage.")
            st.rerun()

    # Recent Log Table
    st.markdown("---")
    st.markdown("### 📋 Recent Simulated Telemetry Records")
    if st.session_state.telemetry_df is not None and not st.session_state.telemetry_df.empty:
        display_df = st.session_state.telemetry_df.tail(10).copy()
        display_cols = [
            "timestamp", "event_type", "simulated_flow_rate_lpm", "estimated_volume_litres",
            "cumulative_volume_litres", "remaining_capacity_litres", "usage_percentage", "maintenance_status"
        ]
        available_cols = [c for c in display_cols if c in display_df.columns]
        st.dataframe(display_df[available_cols], use_container_width=True)
    else:
        st.info("No simulation records currently loaded.")


# ---------------------------------------------------------
# PAGE 3: FILTER-LIFE ESTIMATOR
# ---------------------------------------------------------
elif page == "⏱️ 3. Filter-Life Estimator":
    render_sim_banner()

    st.title("Filter-Life Estimator & Prognostic Rules")
    st.markdown(
        "Transparent engineering calculations computing remaining rated capacity, "
        "percentage exhaustion, and remaining useful life projection."
    )

    metrics, _, _ = get_current_metrics()

    # Mathematical formulation explanation
    with st.expander("📐 View Mathematical Formulations & Derivations", expanded=True):
        st.markdown(r"""
        AquaGuard IQ utilizes a **dual-criteria deterministic baseline model** accounting for both volumetric throughput and calendar duration:
        
        1. **Cumulative Water Volume ($V_{cum}$):**
           $$V_{cum} = \sum_{i=1}^{N} V_i = \sum_{i=1}^{N} \left( Q_i \times \frac{\Delta t_i}{60} \right)$$
           Where $Q_i$ is flow rate in L/min and $\Delta t_i$ is pulse event duration in seconds.
        
        2. **Remaining Volumetric Capacity ($C_{rem}$):**
           $$C_{rem} = \max\left(0, \; C_{rated} - V_{cum}\right)$$
        
        3. **Filter Capacity Exhaustion ($U_{\%}$):**
           $$U_{\%} = \min\left(100\%, \; \frac{V_{cum}}{C_{rated}} \times 100\%\right)$$
        
        4. **Projected Usable Days Remaining ($D_{rem}$):**
           $$D_{rem} = \min\left( \frac{C_{rem}}{\overline{V}_{daily}}, \; \max\left(0, T_{interval} - T_{elapsed}\right) \right)$$
           Where $\overline{V}_{daily}$ is the average daily consumption, $T_{interval}$ is manufacturer service interval (e.g. 365 days), and $T_{elapsed}$ is elapsed days.
        """)

    # Threshold Adjusters
    st.markdown("### 🎛️ Configurable Maintenance Thresholds")
    st.caption("Adjust the advisory and critical warning triggers according to filter manufacturer recommendations.")

    tcol1, tcol2 = st.columns(2)
    with tcol1:
        new_mod = st.slider("Moderate Usage Advisory (%)", min_value=50.0, max_value=80.0, value=float(st.session_state.mod_threshold), step=5.0)
        if new_mod != st.session_state.mod_threshold:
            st.session_state.mod_threshold = new_mod
            st.rerun()

    with tcol2:
        new_soon = st.slider("Service Soon Critical Alert (%)", min_value=75.0, max_value=95.0, value=float(st.session_state.soon_threshold), step=5.0)
        if new_soon != st.session_state.soon_threshold:
            st.session_state.soon_threshold = new_soon
            st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Live Parameter Breakdown")

    m_col1, m_col2 = st.columns(2)

    with m_col1:
        st.markdown(f"""
        | Metric Name | Current Value | Unit |
        | :--- | :--- | :--- |
        | **Rated Capacity ($C_{{rated}}$)** | `{metrics.rated_capacity_litres:,.1f}` | Litres |
        | **Cumulative Throughput ($V_{{cum}}$)** | `{metrics.cumulative_volume_litres:,.1f}` | Litres |
        | **Remaining Usable Capacity ($C_{{rem}}$)** | `{metrics.remaining_capacity_litres:,.1f}` | Litres |
        | **Volumetric Exhaustion ($U_{{%}}$)** | `{metrics.usage_percentage:.1f}%` | % |
        | **Operational Elapsed Time** | `{metrics.elapsed_days:.1f}` | Days |
        | **Service Interval Limit** | `{metrics.service_interval_days:.1f}` | Days |
        """)

    with m_col2:
        st.markdown(f"""
        | Prognostic Parameter | Estimated Value | Evaluation |
        | :--- | :--- | :--- |
        | **Combined Maintenance Status** | {get_status_badge_html(metrics.status)} | Dual Constraint |
        | **Assumed Daily Consumption** | `{st.session_state.daily_target_litres:.1f}` | L/day |
        | **Estimated Usable Days Remaining** | `~{metrics.estimated_days_remaining if metrics.estimated_days_remaining is not None else 0.0:.0f}` | Days |
        | **Projected Service Date** | `{metrics.projected_replacement_date if metrics.projected_replacement_date else 'Immediate'}` | Calendar |
        | **Primary Limiting Factor** | `{'Volumetric Throughput' if metrics.usage_percentage >= metrics.time_elapsed_percentage else 'Calendar Elapsed Duration'}` | Threshold |
        """, unsafe_allow_html=True)

    st.warning(
        "⚠️ **Engineering Integrity Disclaimer:** These figures are rule-based estimates derived from user-configured "
        "manufacturer ratings and simulated volumetric throughput. They are not direct physical measurements of filter media pore clogging, "
        "biofouling, microbial contamination, or chemical breakthrough."
    )


# ---------------------------------------------------------
# PAGE 4: INTERACTIVE CHARTS
# ---------------------------------------------------------
elif page == "📊 4. Interactive Charts":
    render_sim_banner()

    st.title("Interactive Telemetry & Prognostic Visualizations")
    st.markdown(
        "Plotly interactive charts showing water consumption patterns, cumulative throughput, "
        "burn-down trajectories, and flow dynamics. All charts include pan, zoom, hover tooltips, and export capabilities."
    )

    df = st.session_state.telemetry_df

    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Cumulative & Daily Throughput",
        "📉 Capacity Burn-Down & Exhaustion",
        "🌊 Flow-Rate Dynamics",
        "🧪 Auxiliary Simulated TDS Drift"
    ])

    with tab1:
        st.plotly_chart(
            plot_cumulative_water_usage(df, rated_capacity=st.session_state.rated_capacity),
            use_container_width=True
        )
        st.markdown("---")
        st.plotly_chart(
            plot_daily_water_consumption(df),
            use_container_width=True
        )

    with tab2:
        c1, c2 = st.columns([1, 2])
        metrics, _, _ = get_current_metrics()
        with c1:
            st.plotly_chart(plot_capacity_gauge(metrics.usage_percentage, metrics.status), use_container_width=True)
            st.info(
                f"**Current Status:** {metrics.status}\n\n"
                f"Remaining volume: **{metrics.remaining_capacity_litres:,.1f} Litres** "
                f"({100.0 - metrics.usage_percentage:.1f}% remaining of {metrics.rated_capacity_litres:,.0f} L)."
            )
        with c2:
            st.plotly_chart(
                plot_remaining_capacity_burndown(df, rated_capacity=st.session_state.rated_capacity),
                use_container_width=True
            )

    with tab3:
        st.plotly_chart(plot_flow_rate_trend(df), use_container_width=True)
        st.caption(
            "Visualizes individual water dispensing events. The shaded green band denotes nominal residential reverse-osmosis "
            "delivery rates (1.8 – 2.5 L/min). Flow deviations can indicate dispensing vessel differences or line pressure shifts."
        )

    with tab4:
        st.plotly_chart(plot_simulated_tds_trend(df), use_container_width=True)
        st.warning(
            "⚠️ **SIMULATED TDS DATA:** This trend is a simulated baseline demonstrating how auxiliary water-quality telemetry "
            "will be integrated in future phases. TDS drift can reflect membrane exhaustion, but is not alone definitive proof of filter failure."
        )


# ---------------------------------------------------------
# PAGE 5: DATA ANALYTICS & MACHINE LEARNING
# ---------------------------------------------------------
elif page == "🔬 5. Data Analytics & ML":
    render_sim_banner()

    st.title("Data Analytics & Prognostic Machine Learning")
    st.markdown(
        "Comparing the transparent rule-based baseline estimator against a demonstration "
        "machine-learning prognostic pipeline built on synthetic telemetry features."
    )

    st.error("""
    ### ⚠️ CRITICAL NOTICE ON SYNTHETIC-DATA MACHINE LEARNING
    - The machine learning model demonstrated below is trained **exclusively on computer-generated simulation data**.
    - High synthetic accuracy **does NOT establish or reflect real-world filter failure accuracy**.
    - In physical purifiers, filter failure involves complex membrane compaction, biological fouling, particulate cake formation, and pressure drop curves.
    - This software architecture establishes the **data pipeline foundation** so that verified empirical sensor datasets can be seamlessly plugged in during physical test bench phases.
    """)

    st.markdown("### ⚖️ Baseline vs Prognostic Machine Learning Distinction")
    dist_col1, dist_col2 = st.columns(2)

    with dist_col1:
        st.markdown("""
        #### 1. Rule-Based Baseline Estimator (Current)
        - **Mechanism:** Integrates flow pulse counts to determine cumulative liters ($V_{cum}$). Compares against manufacturer rated volume ($C_{rated}$) and elapsed days ($T_{elapsed}$).
        - **Transparency:** 100% deterministic and explainable. No hidden black-box decisions.
        - **Limitation:** Does not adapt if feed water turbidity is unusually high or if biological fouling occurs ahead of rated gallon capacity.
        """)

    with dist_col2:
        st.markdown("""
        #### 2. Advanced Prognostic Model (Future Goal)
        - **Mechanism:** Ingests multi-sensor streams (flow rate variance, differential pressure, total dissolved solids, temperature).
        - **Objective:** Predict Remaining Useful Life (RUL) and detect premature physical filter degradation before sudden failure.
        - **Prerequisite:** Requires extensive physical laboratory run-to-failure benchmarks with certified reference equipment.
        """)

    st.markdown("---")
    st.markdown("### 🤖 Synthetic Prognostic Model Demonstration")
    
    df = st.session_state.telemetry_df

    if df is not None and len(df) >= 15:
        rf_model, report = train_synthetic_prognostic_model(df)

        if rf_model is not None:
            col_res1, col_res2 = st.columns([1, 1])

            with col_res1:
                st.markdown("#### Model Architecture & Synthetic Fit")
                st.write(f"- **Algorithm:** Random Forest Classifier (30 estimators, max depth 4)")
                st.write(f"- **Training Records:** {report['sample_size']} synthetic events")
                st.write(f"- **Input Features:** `{', '.join(report['features_used'])}`")
                st.write(f"- **Synthetic Accuracy:** `{report['accuracy'] * 100.0:.1f}%` *(On synthetic simulation)*")
                st.caption(f"Note: {report['disclaimer']}")

            with col_res2:
                st.markdown("#### Feature Importance Analysis")
                feat_df = pd.DataFrame(list(report["feature_importances"].items()), columns=["Feature", "Importance"])
                feat_df = feat_df.sort_values(by="Importance", ascending=True)
                st.bar_chart(data=feat_df.set_index("Feature"))

            st.markdown("---")
            st.markdown("#### 🧪 Interactive Synthetic Inference Demonstration")
            st.caption("Input hypothetical sensor observations to evaluate the synthetic model's prognostic classification:")

            i_col1, i_col2, i_col3, i_col4 = st.columns(4)
            with i_col1:
                test_vol = st.number_input("Hypothetical Volume (L)", min_value=0.0, max_value=15000.0, value=float(df["cumulative_volume_litres"].iloc[-1]))
            with i_col2:
                test_flow = st.number_input("Flow Rate (L/min)", min_value=0.1, max_value=8.0, value=2.2)
            with i_col3:
                test_days = st.number_input("Elapsed Days", min_value=1.0, max_value=730.0, value=float(df["elapsed_days"].iloc[-1]) if "elapsed_days" in df.columns else 30.0)
            with i_col4:
                test_tds = st.number_input("Simulated TDS (ppm)", min_value=10.0, max_value=600.0, value=110.0)

            test_data = {"cumulative_volume_litres": [test_vol], "simulated_flow_rate_lpm": [test_flow], "elapsed_days": [test_days]}
            if "simulated_tds_ppm" in report["features_used"]:
                test_data["simulated_tds_ppm"] = [test_tds]
            test_features = pd.DataFrame(test_data)

            pred_class = rf_model.predict(test_features)[0]
            pred_probs = rf_model.predict_proba(test_features)[0]
            class_probs = dict(zip(rf_model.classes_, [round(p * 100.0, 1) for p in pred_probs]))

            st.markdown(f"**Predicted Synthetic Maintenance State:** {get_status_badge_html(pred_class)}", unsafe_allow_html=True)
            st.write(f"Class Probabilities: `{class_probs}`")
        else:
            st.warning(f"Could not initialize demonstration model: {report.get('error')}")
    else:
        st.info("Please load or generate at least 15 simulation records in the Simulation tab to run the demonstration model.")


# ---------------------------------------------------------
# PAGE 6: DATA MANAGEMENT
# ---------------------------------------------------------
elif page == "💾 6. Data Management":
    render_sim_banner()

    st.title("Data Management & Telemetry Persistence")
    st.markdown(
        "Export telemetry logs to CSV for external analysis, import compatible datasets, "
        "and inspect simulation schema integrity."
    )

    exp_col, imp_col = st.columns(2)

    with exp_col:
        st.markdown("### 📥 Export Simulation Data")
        st.markdown("Download the active simulation history or the reference sample dataset in standard CSV format.")

        df = st.session_state.telemetry_df
        csv_bytes = export_dataframe_to_csv(df)

        st.download_button(
            label="💾 Download Current Simulation History (CSV)",
            data=csv_bytes,
            file_name="aquaguard_simulation_telemetry.csv",
            mime="text/csv",
            use_container_width=True
        )

        try:
            bundled_sample = load_bundled_sample_dataset()
            sample_bytes = export_dataframe_to_csv(bundled_sample)
            st.download_button(
                label="📄 Download Bundled Reference Sample (CSV)",
                data=sample_bytes,
                file_name="sample_water_usage.csv",
                mime="text/csv",
                use_container_width=True
            )
        except Exception as e:
            st.caption(f"Sample file access note: {e}")

    with imp_col:
        st.markdown("### 📤 Upload Compatible Dataset")
        st.caption("Upload a pre-recorded or exported CSV dataset. Must contain standard telemetry schema columns.")

        uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
        if uploaded_file is not None:
            is_valid, errors, cleaned_df = load_csv_from_upload(uploaded_file)
            if is_valid and cleaned_df is not None:
                st.session_state.telemetry_df = cleaned_df
                st.success(f"Successfully loaded and validated {len(cleaned_df)} records from '{uploaded_file.name}'!")
                st.rerun()
            else:
                st.error("Uploaded CSV failed schema validation:")
                for err in errors:
                    st.write(f"- ❌ {err}")

    st.markdown("---")
    st.markdown("### 🔍 Telemetry Dataset Inspector")
    if st.session_state.telemetry_df is not None and not st.session_state.telemetry_df.empty:
        df = st.session_state.telemetry_df
        st.markdown(f"**Total Records:** `{len(df)}` &nbsp;|&nbsp; **Date Range:** `{df['timestamp'].iloc[0]}` to `{df['timestamp'].iloc[-1]}`")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No records loaded.")


# ---------------------------------------------------------
# PAGE 7: METHODOLOGY & ABOUT (atomQUEST 2026)
# ---------------------------------------------------------
elif page == "📖 7. Methodology & About":
    render_sim_banner()

    st.title("Project Methodology & System Architecture")
    st.markdown("### AquaGuard IQ: A Data-Driven Filter-Life Monitoring System")
    st.caption("**Competition:** atomQUEST 2026 | **Track 2:** Water Purifier | **Area:** Prognostics of filter failure using data analytics")
    st.caption("**Team:** ProjectX | **Institution:** Amrita Vishwa Vidyapeetham | **Department:** Artificial Intelligence and Data Science (AI&DS)")

    st.markdown("---")

    # Architecture Overview
    st.markdown("#### 1. Problem Statement")
    st.write(
        "Conventional domestic water purifiers rely heavily on arbitrary calendar timers (e.g. 6 or 12 months) "
        "or unmonitored user memory for servicing. This causes two major failure modes: (1) filters servicing too early "
        "waste usable media and increase household expenses, and (2) filters in high-consumption households exceed rated throughput, "
        "causing membrane pore clogging, bacterial breakthrough, and compromised water quality. "
        "There is no transparent indication of cumulative liters consumed."
    )

    st.markdown("#### 2. Proposed Solution")
    st.write(
        "AquaGuard IQ bridges this gap by introducing inline flow-rate telemetry coupled with edge microcontroller processing "
        "and a Python data analytics dashboard. The prototype computes cumulative water volume, monitors actual drinking-water usage "
        "against OEM rated limits, and provides prognostic maintenance warnings before filter exhaustion."
    )

    st.markdown("#### 3. System Workflow Architecture")
    st.markdown("""
    ```
    +----------------------------------------------------------------------------------------------------+
    |                                AQUAGUARD IQ SYSTEM WORKFLOW                                        |
    +----------------------------------------------------------------------------------------------------+
    |  [Physical Tap / Tank]                                                                             |
    |          |                                                                                         |
    |          v                                                                                         |
    |  [Inline Flow Sensor] --------> Pulsed Output (Hall Effect / Turbine)                              |
    |                                          |                                                         |
    |                                          v                                                         |
    |                              [ESP32 Microcontroller]                                               |
    |                              - Pulse Accumulation Interrupt                                        |
    |                              - Calibration Factor (Q = Pulses / K)                                 |
    |                              - USB Serial / Wireless Telemetry Stream                              |
    |                                          |                                                         |
    |                                          v                                                         |
    |                              [AquaGuard IQ Python Engine]                                          |
    |                              - Time-Series Timestamping & Logging                                  |
    |                              - Cumulative Volume Tracking: V_cum = sum(V_i)                        |
    |                              - Dual-Constraint Evaluation (Volume vs Calendar)                     |
    |                                          |                                                         |
    |                   +----------------------+----------------------+                              |
    |                   v                                             v                              |
    |     [Baseline Rule Engine]                         [Prognostics & Visuals]                     |
    |     - Normal (<70%)                                - Interactive Streamlit UI                  |
    |     - Moderate (70-85%)                            - Plotly Telemetry Analytics                |
    |     - Service Soon (85-100%)                       - Future ML Labeled Integration             |
    |     - Capacity Reached (>=100%)                    - CSV Telemetry Persistence                 |
    +----------------------------------------------------------------------------------------------------+
    ```
    """)

    st.markdown("#### 4. Baseline vs Target Engineering Performance")
    st.write(
        "The following engineering specifications are defined as **future physical test-bench targets**, "
        "not achieved experimental results in this software prototype:"
    )
    
    st.markdown("""
    | Performance Metric | Proposed Engineering Target | Current Prototype Status | Verification Method |
    | :--- | :--- | :--- | :--- |
    | **Water Volume Estimation Error** | **Within ±10%** of reference volume | *Software Simulation Only* | Repeated graduated cylinder & volumetric flask trials |
    | **Flow-Event Detection Rate** | **At least 95%** under test conditions | *Software Simulation Only* | Automated multi-pulse trigger logging on ESP32 |
    | **Failure Prognostics Accuracy** | Pending empirical benchmark | *Synthetic Demo Only* | Run-to-failure membrane pressure & TDS logging |
    """)

    st.markdown("#### 5. Technical & Safety Limitations")
    st.warning("""
    **MANDATORY SAFETY & TECHNICAL DISCLOSURES:**
    1. **Software-Only Prototype:** This release is purely a software and algorithmic demonstration. No physical sensors, ESP32 boards, or plumbing connections are attached.
    2. **Drinking Water Safety Disclaimer:** AquaGuard IQ does NOT certify drinking water safety. It monitors volumetric throughput and manufacturer specifications; it does NOT directly detect bacteria, viruses, heavy metals, or hazardous chemicals.
    3. **Filter Failure Scope:** A filter may physically rupture or develop channeling due to pressure surges before reaching rated volumetric limits. Volumetric estimation is an advisory maintenance indicator, not a guarantee against mechanical failure.
    """)

    st.markdown("#### 6. Future Physical Hardware Integration (Round 2 Plan)")
    st.write("When moving to physical prototyping, the system will be assembled with off-the-shelf, budget-friendly components:")

    st.markdown("""
    | Component / Item | Specification | Estimated Cost (₹) |
    | :--- | :--- | :--- |
    | **ESP32 Development Board** | 30-pin dual-core Wi-Fi/BLE NodeMCU | ₹350 – ₹500 |
    | **Inline Flow Sensor** | YF-S201 (1/2\" Hall effect pulse sensor) | ₹200 – ₹350 |
    | **Wiring, Connectors & Breadboard** | Jumper wires, food-grade quick-connect fittings | ₹200 – ₹350 |
    | **Bench Testing Materials** | Graduated measuring jug, low-voltage 5V USB supply | ₹200 – ₹400 |
    | **Indicative Subtotal** | Hardware test rig components | **₹950 – ₹1,600** |
    | **Buffer / Contingency** | Spares & miscellaneous fittings | ₹100 – ₹400 |
    | **Target Total Budget** | Affordable student innovation prototype | **₹1,050 – ₹2,000** |
    """)

    st.markdown("---")
    st.caption("AquaGuard IQ © 2026 ProjectX | Amrita Vishwa Vidyapeetham | atomQUEST 2026 Track 2")
