"""
AquaGuard IQ - Interactive Plotly Charts Module
Builds responsive, clean, high-contrast engineering visualizations for filter telemetry.
Every chart includes clear units, status color coding, and prominent SIMULATED DATA disclaimers.
"""

from typing import Optional
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Theme Colors
COLOR_PRIMARY = "#1E40AF"     # Royal Navy Blue
COLOR_ACCENT = "#0284C7"      # Deep Sky Blue
COLOR_SUCCESS = "#16A34A"     # Green (Normal)
COLOR_WARNING = "#F59E0B"     # Amber (Moderate)
COLOR_ORANGE = "#EA580C"      # Deep Orange (Service Soon)
COLOR_DANGER = "#DC2626"      # Crimson Red (Capacity Reached)
COLOR_BG_PLOT = "#F8FAFC"     # Light slate
COLOR_GRID = "#E2E8F0"        # Subtle slate gridline
COLOR_TEXT = "#1E293B"        # Charcoal readable text

DISCLAIMER_TEXT = "SIMULATED DATA — Illustrative Prototype Telemetry"


def _apply_standard_layout(fig: go.Figure, title: str, x_title: str, y_title: str) -> go.Figure:
    """Applies consistent styling, fonts, margins, and simulation watermarks."""
    fig.update_layout(
        title={
            "text": f"<b>{title}</b><br><span style='font-size:11px;color:#64748B;'>⚠️ {DISCLAIMER_TEXT}</span>",
            "x": 0.02,
            "xanchor": "left"
        },
        paper_bgcolor="#FFFFFF",
        plot_bgcolor=COLOR_BG_PLOT,
        font=dict(family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", color=COLOR_TEXT, size=12),
        margin=dict(l=55, r=30, t=65, b=50),
        xaxis=dict(
            title=x_title,
            showgrid=True,
            gridcolor=COLOR_GRID,
            zeroline=False,
            showline=True,
            linecolor="#CBD5E1"
        ),
        yaxis=dict(
            title=y_title,
            showgrid=True,
            gridcolor=COLOR_GRID,
            zeroline=False,
            showline=True,
            linecolor="#CBD5E1"
        ),
        hoverlabel=dict(
            bgcolor="#1E293B",
            font_size=12,
            font_color="#FFFFFF"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    return fig


def plot_cumulative_water_usage(df: pd.DataFrame, rated_capacity: float = 6000.0) -> go.Figure:
    """Cumulative water usage trajectory with rated capacity threshold."""
    fig = go.Figure()

    if df.empty:
        fig.add_annotation(text="No simulation records to display", showarrow=False, font=dict(size=14))
        return _apply_standard_layout(fig, "Cumulative Water Usage vs Rated Capacity", "Event / Timestamp", "Volume (Litres)")

    x_vals = pd.to_datetime(df["timestamp"]) if "timestamp" in df.columns else df.index

    # Cumulative volume area trace
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=df["cumulative_volume_litres"],
        mode="lines",
        name="Cumulative Volume (L)",
        line=dict(color=COLOR_ACCENT, width=3),
        fill="tozeroy",
        fillcolor="rgba(2, 132, 199, 0.08)",
        hovertemplate="<b>Date/Time:</b> %{x|%Y-%m-%d %H:%M}<br><b>Cumulative:</b> %{y:.1f} L<extra></extra>"
    ))

    # Rated Capacity reference line
    fig.add_hline(
        y=rated_capacity,
        line=dict(color=COLOR_DANGER, width=2, dash="dash"),
        annotation_text=f"Rated Capacity ({rated_capacity:,.0f} L)",
        annotation_position="top left",
        annotation_font=dict(color=COLOR_DANGER, size=11, family="monospace")
    )

    # 85% Service Soon line
    fig.add_hline(
        y=rated_capacity * 0.85,
        line=dict(color=COLOR_ORANGE, width=1.5, dash="dot"),
        annotation_text="85% Service Alert Threshold",
        annotation_position="bottom left",
        annotation_font=dict(color=COLOR_ORANGE, size=10)
    )

    return _apply_standard_layout(fig, "Cumulative Water Consumption vs Rated Capacity", "Timeline", "Cumulative Volume (Litres)")


def plot_daily_water_consumption(df: pd.DataFrame) -> go.Figure:
    """Daily consumption bar chart aggregated by calendar day."""
    fig = go.Figure()

    if df.empty:
        fig.add_annotation(text="No daily usage records available", showarrow=False, font=dict(size=14))
        return _apply_standard_layout(fig, "Daily Water Consumption", "Date", "Litres per Day")

    df_copy = df.copy()
    if "timestamp" in df_copy.columns:
        df_copy["date"] = pd.to_datetime(df_copy["timestamp"]).dt.date
    elif "day_number" in df_copy.columns:
        df_copy["date"] = df_copy["day_number"].apply(lambda d: f"Day {d}")
    else:
        df_copy["date"] = "Day 1"

    daily_sum = df_copy.groupby("date")["estimated_volume_litres"].sum().reset_index()
    avg_daily = daily_sum["estimated_volume_litres"].mean()

    # Bar chart
    fig.add_trace(go.Bar(
        x=daily_sum["date"].astype(str),
        y=daily_sum["estimated_volume_litres"],
        name="Daily Volume (L)",
        marker=dict(
            color=COLOR_PRIMARY,
            opacity=0.85,
            line=dict(color="#1E3A8A", width=1)
        ),
        hovertemplate="<b>Date:</b> %{x}<br><b>Usage:</b> %{y:.1f} Litres<extra></extra>"
    ))

    # Average reference line
    fig.add_hline(
        y=avg_daily,
        line=dict(color="#0D9488", width=2, dash="dash"),
        annotation_text=f"Average ({avg_daily:.1f} L/day)",
        annotation_position="top right",
        annotation_font=dict(color="#0D9488", size=11)
    )

    return _apply_standard_layout(fig, "Daily Water Consumption Profile", "Operational Date", "Water Volume (Litres)")


def plot_capacity_gauge(usage_percentage: float, status: str) -> go.Figure:
    """Sleek semi-circular gauge displaying filter capacity consumed with status colors."""
    pct = min(100.0, max(0.0, float(usage_percentage)))

    if pct < 70.0:
        bar_color = COLOR_SUCCESS
    elif pct < 85.0:
        bar_color = COLOR_WARNING
    elif pct < 100.0:
        bar_color = COLOR_ORANGE
    else:
        bar_color = COLOR_DANGER

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        number={"suffix": "%", "font": {"size": 36, "color": COLOR_TEXT, "family": "Inter, sans-serif"}},
        title={"text": f"<b>Filter Capacity Consumed</b><br><span style='font-size:12px;color:#64748B;'>Status: {status}</span>", "font": {"size": 15}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#94A3B8"},
            "bar": {"color": bar_color, "thickness": 0.28},
            "bgcolor": "#F1F5F9",
            "borderwidth": 1,
            "bordercolor": "#CBD5E1",
            "steps": [
                {"range": [0, 70], "color": "rgba(22, 163, 74, 0.12)"},
                {"range": [70, 85], "color": "rgba(245, 158, 11, 0.12)"},
                {"range": [85, 100], "color": "rgba(234, 88, 12, 0.15)"},
            ],
            "threshold": {
                "line": {"color": COLOR_DANGER, "width": 3},
                "thickness": 0.85,
                "value": 100
            }
        }
    ))

    fig.update_layout(
        paper_bgcolor="#FFFFFF",
        margin=dict(l=30, r=30, t=55, b=25),
        height=260,
        font=dict(family="Inter, sans-serif")
    )
    return fig


def plot_remaining_capacity_burndown(df: pd.DataFrame, rated_capacity: float = 6000.0) -> go.Figure:
    """Capacity burndown trajectory showing remaining usable litres."""
    fig = go.Figure()

    if df.empty:
        fig.add_annotation(text="No data for capacity burndown", showarrow=False)
        return _apply_standard_layout(fig, "Estimated Remaining Filter Capacity", "Timeline", "Remaining Volume (L)")

    x_vals = pd.to_datetime(df["timestamp"]) if "timestamp" in df.columns else df.index
    remaining = df["remaining_capacity_litres"] if "remaining_capacity_litres" in df.columns else (rated_capacity - df["cumulative_volume_litres"]).clip(lower=0)

    fig.add_trace(go.Scatter(
        x=x_vals,
        y=remaining,
        mode="lines",
        name="Remaining Capacity (L)",
        line=dict(color=COLOR_SUCCESS, width=2.5),
        fill="tozeroy",
        fillcolor="rgba(22, 163, 74, 0.08)",
        hovertemplate="<b>Date/Time:</b> %{x|%Y-%m-%d %H:%M}<br><b>Remaining:</b> %{y:.1f} Litres<extra></extra>"
    ))

    # Low capacity warning zone
    fig.add_hline(
        y=rated_capacity * 0.15,
        line=dict(color=COLOR_DANGER, width=1.5, dash="dash"),
        annotation_text="Critical Reserve Level (15%)",
        annotation_position="bottom right",
        annotation_font=dict(color=COLOR_DANGER, size=10)
    )

    return _apply_standard_layout(fig, "Filter Capacity Remaining (Burn-down)", "Timeline", "Remaining Capacity (Litres)")


def plot_flow_rate_trend(df: pd.DataFrame) -> go.Figure:
    """Dispensing flow-rate distribution across events."""
    fig = go.Figure()

    if df.empty:
        fig.add_annotation(text="No flow-rate events available", showarrow=False)
        return _apply_standard_layout(fig, "Simulated Flow-Rate Trend", "Event / Timestamp", "Flow Rate (L/min)")

    x_vals = pd.to_datetime(df["timestamp"]) if "timestamp" in df.columns else df.index

    # Scatter trace of individual dispensing events
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=df["simulated_flow_rate_lpm"],
        mode="markers+lines",
        name="Flow Rate (L/min)",
        line=dict(color="rgba(30, 64, 175, 0.35)", width=1),
        marker=dict(
            size=6,
            color=df["simulated_flow_rate_lpm"],
            colorscale="Viridis",
            colorbar=dict(title=dict(text="L/min", font=dict(size=10)), thickness=12, len=0.7),
            showscale=True
        ),
        hovertemplate="<b>Flow Rate:</b> %{y:.2f} L/min<br><b>Time:</b> %{x|%Y-%m-%d %H:%M}<extra></extra>"
    ))

    # Typical operating bounds
    fig.add_hrect(
        y0=1.8, y1=2.5,
        fillcolor="rgba(22, 163, 74, 0.08)",
        line_width=0,
        annotation_text="Nominal RO Output Band (1.8 - 2.5 L/min)",
        annotation_position="top left",
        annotation_font=dict(size=10, color=COLOR_SUCCESS)
    )

    return _apply_standard_layout(fig, "Simulated Flow-Rate Trend Across Events", "Timeline", "Flow Rate (L/min)")


def plot_simulated_tds_trend(df: pd.DataFrame) -> go.Figure:
    """Auxiliary simulated TDS trend representing filtration baseline."""
    fig = go.Figure()

    if df.empty or "simulated_tds_ppm" not in df.columns:
        fig.add_annotation(text="No TDS baseline records available", showarrow=False)
        return _apply_standard_layout(fig, "Simulated TDS Trend", "Timeline", "TDS (ppm)")

    x_vals = pd.to_datetime(df["timestamp"]) if "timestamp" in df.columns else df.index

    fig.add_trace(go.Scatter(
        x=x_vals,
        y=df["simulated_tds_ppm"],
        mode="lines",
        name="Simulated TDS (ppm)",
        line=dict(color="#7C3AED", width=2.5),
        hovertemplate="<b>Date/Time:</b> %{x|%Y-%m-%d %H:%M}<br><b>Simulated TDS:</b> %{y:.1f} ppm<extra></extra>"
    ))

    # Acceptable drinking water threshold indicator
    fig.add_hline(
        y=150.0,
        line=dict(color=COLOR_WARNING, width=1.5, dash="dash"),
        annotation_text="Suggested Palatability Threshold (150 ppm)",
        annotation_position="top left",
        annotation_font=dict(color=COLOR_WARNING, size=10)
    )

    return _apply_standard_layout(fig, "Simulated TDS Drift (Baseline Demonstration)", "Timeline", "Simulated TDS (ppm)")
