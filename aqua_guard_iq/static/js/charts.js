/**
 * AquaGuard IQ - Multi-Axis Prognostic Analytics & Charts (Chart.js)
 * Enterprise-Grade v2.0 Production Prototype
 * AtomQUEST Track 2: Water Purifier Prognostics & IoT Telemetry
 */

let depletionCurveChartInstance = null;
let dailyForecastChartInstance = null;
let healthGaugeChartInstance = null;

/**
 * Helper to check if an element is visible in the active DOM tree
 */
function isElementVisible(el) {
  if (!el) return false;
  return el.offsetParent !== null || el.getClientRects().length > 0;
}

/**
 * Main entry point to refresh all charts with updated telemetry metrics
 */
function updateCharts(data) {
  if (!data || !data.prognostics) return;

  const dashboardView = document.getElementById('dashboard-view');
  // If dashboard view is hidden, don't instantiate charts yet to avoid 0-dimension canvas issues
  if (dashboardView && (dashboardView.classList.contains('hidden') || dashboardView.style.display === 'none')) {
    return;
  }

  // Active tab check: render dashboard overview charts
  const gaugeCanvas = document.getElementById('healthGaugeChart');
  const depletionCanvas = document.getElementById('depletionCurveChart');
  if (isElementVisible(gaugeCanvas)) {
    renderHealthGauge(data.prognostics);
  }
  if (isElementVisible(depletionCanvas)) {
    renderDepletionCurve(data);
  }

  // Render analytics forecast chart if its canvas is visible
  const forecastCanvas = document.getElementById('dailyForecastChart');
  if (isElementVisible(forecastCanvas)) {
    renderDailyConsumptionForecast(data);
  }
}

/**
 * Smoothly pushes an incremental telemetry point into active Chart.js instances in real-time
 */
function pushDataPointToCharts(record, prognostics) {
  if (!record || !prognostics) return;

  // 1. Update Gauge immediately
  renderHealthGauge(prognostics);

  // 2. Incremental update on Depletion Curve
  if (depletionCurveChartInstance) {
    const timeLabel = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const rated = Number(prognostics.rated_capacity_litres || 3000.0);
    const effVal = Number(prognostics.total_effective_litres || 0.0);
    const rawVal = Number(prognostics.total_raw_litres || 0.0);

    depletionCurveChartInstance.data.labels.push(timeLabel);
    depletionCurveChartInstance.data.datasets[0].data.push(effVal);
    depletionCurveChartInstance.data.datasets[1].data.push(rawVal);
    depletionCurveChartInstance.data.datasets[2].data.push(rated);

    // Keep max 50 points on live curve to avoid memory bloat
    if (depletionCurveChartInstance.data.labels.length > 50) {
      depletionCurveChartInstance.data.labels.shift();
      depletionCurveChartInstance.data.datasets[0].data.shift();
      depletionCurveChartInstance.data.datasets[1].data.shift();
      depletionCurveChartInstance.data.datasets[2].data.shift();
    }
    depletionCurveChartInstance.update();
  }

  // 3. Update Daily Forecast if active
  if (dailyForecastChartInstance && dailyForecastChartInstance.data.datasets[0]) {
    const rawData = dailyForecastChartInstance.data.datasets[0].data;
    const effData = dailyForecastChartInstance.data.datasets[1].data;
    if (rawData.length > 0) {
      rawData[rawData.length - 1] = Math.round(((rawData[rawData.length - 1] || 0) + (record.raw_litres || 0)) * 10) / 10;
      effData[effData.length - 1] = Math.round(((effData[effData.length - 1] || 0) + (record.effective_litres || 0)) * 10) / 10;
      dailyForecastChartInstance.update('none');
    }
  }
}

/**
 * 1. Membrane Health Gauge (Doughnut with Center Text Readout & Custom HTML Legend)
 */
function renderHealthGauge(prognostics) {
  const canvas = document.getElementById('healthGaugeChart');
  if (!canvas || !isElementVisible(canvas)) return;

  const healthScore = Math.max(0, Math.min(100, parseFloat(prognostics.health_score_pct !== undefined ? prognostics.health_score_pct : 100)));
  const consumedPct = Math.max(0, Math.min(100, parseFloat(prognostics.capacity_consumed_pct !== undefined ? prognostics.capacity_consumed_pct : (100 - healthScore))));
  const statusLevel = prognostics.status_level || 'normal';
  const remainingL = (prognostics.remaining_capacity_litres !== undefined)
    ? Number(prognostics.remaining_capacity_litres).toLocaleString('en-US', { maximumFractionDigits: 1 })
    : '0';

  // Dynamic status color
  let activeColor = '#10b981'; // emerald (normal)
  if (statusLevel === 'warning') activeColor = '#f59e0b'; // amber (attention required)
  if (statusLevel === 'danger') activeColor = '#ef4444';  // red (critical replacement)

  // Update center gauge display text
  const scoreEl = document.getElementById('gaugeScore');
  const subEl = document.getElementById('gaugeRemainingSub');
  if (scoreEl) {
    scoreEl.textContent = `${healthScore.toFixed(1)}%`;
    scoreEl.style.color = activeColor;
  }
  if (subEl) {
    subEl.textContent = `${remainingL} L Left`;
  }

  // Update custom HTML legend
  const dotEl = document.getElementById('gaugeLegendHealthDot');
  const legendPct = document.getElementById('gaugeLegendHealthPct');
  const legendConsumed = document.getElementById('gaugeLegendConsumedPct');
  if (dotEl) dotEl.style.background = activeColor;
  if (legendPct) legendPct.textContent = `${healthScore.toFixed(1)}%`;
  if (legendConsumed) legendConsumed.textContent = `${consumedPct.toFixed(1)}%`;

  // If instance already exists, update data smoothly in-place without tearing down canvas context
  if (healthGaugeChartInstance) {
    healthGaugeChartInstance.data.datasets[0].data = [healthScore, consumedPct];
    healthGaugeChartInstance.data.datasets[0].backgroundColor = [activeColor, 'rgba(226, 232, 240, 0.75)'];
    healthGaugeChartInstance.update();
    return;
  }

  const ctx = canvas.getContext('2d');
  healthGaugeChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Remaining Membrane Life', 'Effective Wear Consumed'],
      datasets: [{
        data: [healthScore, consumedPct],
        backgroundColor: [activeColor, 'rgba(226, 232, 240, 0.75)'],
        borderColor: ['transparent', 'transparent'],
        borderWidth: 0,
        hoverOffset: 3,
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '74%',
      circumference: 360,
      rotation: -90, // Start clockwise sweep from 12 o'clock
      animation: {
        duration: 400
      },
      plugins: {
        legend: {
          display: false // Driven by crisp HTML legend below canvas
        },
        tooltip: {
          backgroundColor: '#0f172a',
          titleFont: { family: 'Plus Jakarta Sans', size: 12 },
          bodyFont: { family: 'JetBrains Mono', size: 12, weight: '600' },
          padding: 10,
          cornerRadius: 8,
          callbacks: {
            label: function(context) {
              const label = context.label || '';
              const value = context.parsed || 0;
              return ` ${label}: ${value.toFixed(1)}%`;
            }
          }
        }
      }
    }
  });
}

/**
 * 2. Live Chart 1: Depletion Curve (Cumulative Raw vs Effective Wear vs Rated Limit)
 */
function renderDepletionCurve(data) {
  const canvas = document.getElementById('depletionCurveChart');
  if (!canvas || !isElementVisible(canvas)) return;

  const prognostics = data.prognostics || {};
  const ratedCapacity = Number(prognostics.rated_capacity_litres || 3000.0);
  const totalRaw = Number(prognostics.total_raw_litres || 0.0);
  const totalEff = Number(prognostics.total_effective_litres || 0.0);

  const labels = [];
  const rawPoints = [];
  const effPoints = [];
  const limitLine = [];

  const trajectory = data.depletion_trajectory || [];
  const trends = data.daily_trends || [];

  if (trajectory && trajectory.length > 1) {
    // 1. High-resolution cumulative trajectory across telemetry records
    trajectory.forEach(pt => {
      labels.push(pt.label || '');
      rawPoints.push(pt.cum_raw);
      effPoints.push(pt.cum_eff);
      limitLine.push(ratedCapacity);
    });
  } else if (trends && trends.length > 1) {
    // 2. Multi-day aggregation
    labels.push('Start (0 L)');
    rawPoints.push(0);
    effPoints.push(0);
    limitLine.push(ratedCapacity);

    let cumRaw = 0;
    let cumEff = 0;
    trends.forEach(day => {
      cumRaw += day.daily_raw_litres || 0;
      cumEff += day.daily_effective_litres || 0;
      labels.push(day.date_key || '');
      rawPoints.push(Math.round(cumRaw * 10) / 10);
      effPoints.push(Math.round(cumEff * 10) / 10);
      limitLine.push(ratedCapacity);
    });
  } else {
    // 3. Fallback: Always guarantee at least 2 points (Start Baseline -> Current State)
    labels.push('Start (0 L)', 'Current State');
    rawPoints.push(0, Math.round(totalRaw * 10) / 10);
    effPoints.push(0, Math.round(totalEff * 10) / 10);
    limitLine.push(ratedCapacity, ratedCapacity);
  }

  // Ensure limit line matches full label count
  while (limitLine.length < labels.length) {
    limitLine.push(ratedCapacity);
  }

  // If instance already exists, update smoothly in-place
  if (depletionCurveChartInstance) {
    depletionCurveChartInstance.data.labels = labels;
    depletionCurveChartInstance.data.datasets[0].data = effPoints;
    depletionCurveChartInstance.data.datasets[1].data = rawPoints;
    depletionCurveChartInstance.data.datasets[2].data = limitLine;
    depletionCurveChartInstance.data.datasets[2].label = `Membrane Rated Limit (${ratedCapacity.toLocaleString()} L)`;
    depletionCurveChartInstance.options.scales.y.suggestedMax = Math.max(ratedCapacity * 1.08, (totalEff || 0) * 1.2, 100);
    depletionCurveChartInstance.update();
    return;
  }

  const ctx = canvas.getContext('2d');
  depletionCurveChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Effective Membrane Wear (L)',
          data: effPoints,
          borderColor: '#6366f1',
          backgroundColor: 'rgba(99, 102, 241, 0.12)',
          fill: true,
          tension: 0.35,
          borderWidth: 2.5,
          pointRadius: labels.length > 25 ? 1.5 : 3.5,
          pointHoverRadius: 6,
          pointBackgroundColor: '#6366f1'
        },
        {
          label: 'Raw Volume Ingested (L)',
          data: rawPoints,
          borderColor: '#06b6d4',
          backgroundColor: 'rgba(6, 182, 212, 0.05)',
          fill: false,
          tension: 0.35,
          borderWidth: 2,
          pointRadius: labels.length > 25 ? 1.5 : 3.5,
          pointHoverRadius: 6,
          pointBackgroundColor: '#06b6d4'
        },
        {
          label: `Membrane Rated Limit (${ratedCapacity.toLocaleString()} L)`,
          data: limitLine,
          borderColor: '#ef4444',
          borderDash: [6, 6],
          borderWidth: 2,
          pointRadius: 0,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 400
      },
      interaction: {
        mode: 'index',
        intersect: false
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            font: { family: 'Plus Jakarta Sans', size: 10 },
            color: '#94a3b8',
            maxTicksLimit: 12
          }
        },
        y: {
          beginAtZero: true,
          suggestedMax: Math.max(ratedCapacity * 1.08, (totalEff || 0) * 1.2, 100),
          grid: { color: 'rgba(15, 23, 42, 0.04)' },
          ticks: {
            font: { family: 'JetBrains Mono', size: 10 },
            color: '#94a3b8',
            callback: value => `${value} L`
          }
        }
      },
      plugins: {
        legend: {
          position: 'top',
          align: 'end',
          labels: {
            boxWidth: 10,
            usePointStyle: true,
            font: { family: 'Plus Jakarta Sans', size: 11, weight: '600' },
            color: '#475569'
          }
        },
        tooltip: {
          backgroundColor: '#0f172a',
          titleFont: { family: 'Plus Jakarta Sans', size: 12 },
          bodyFont: { family: 'JetBrains Mono', size: 12 },
          padding: 10,
          cornerRadius: 8,
          callbacks: {
            label: function(context) {
              const label = context.dataset.label || '';
              const value = context.parsed.y !== null ? context.parsed.y : '';
              return ` ${label}: ${value} L`;
            }
          }
        }
      }
    }
  });
}

/**
 * 3. Live Chart 3: Daily Consumption & RUL Forecast Trend
 */
function renderDailyConsumptionForecast(data) {
  const canvas = document.getElementById('dailyForecastChart');
  if (!canvas || !isElementVisible(canvas)) return;

  const trends = data.daily_trends || [];
  const prognostics = data.prognostics || {};
  const smoothedRate = Number(prognostics.daily_usage_rate || 15.0);

  const labels = trends.map(t => t.date_key || '');
  const dailyRaw = trends.map(t => t.daily_raw_litres || 0);
  const dailyEff = trends.map(t => t.daily_effective_litres || 0);
  const baselineRate = trends.map(() => smoothedRate);

  if (labels.length === 0) {
    labels.push('Today');
    dailyRaw.push(Number(prognostics.total_raw_litres || 0));
    dailyEff.push(Number(prognostics.total_effective_litres || 0));
    baselineRate.push(smoothedRate);
  }

  if (dailyForecastChartInstance) {
    dailyForecastChartInstance.data.labels = labels;
    dailyForecastChartInstance.data.datasets[0].data = dailyRaw;
    dailyForecastChartInstance.data.datasets[1].data = dailyEff;
    dailyForecastChartInstance.data.datasets[2].data = baselineRate;
    dailyForecastChartInstance.data.datasets[2].label = `Smoothed Burn Rate (${smoothedRate.toFixed(1)} L/day)`;
    dailyForecastChartInstance.update();
    return;
  }

  const ctx = canvas.getContext('2d');
  dailyForecastChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          type: 'bar',
          label: 'Raw Daily Litres (L)',
          data: dailyRaw,
          backgroundColor: '#38bdf8',
          borderRadius: 4,
          barPercentage: 0.6
        },
        {
          type: 'bar',
          label: 'Effective Wear (L)',
          data: dailyEff,
          backgroundColor: '#818cf8',
          borderRadius: 4,
          barPercentage: 0.6
        },
        {
          type: 'line',
          label: `Smoothed Burn Rate (${smoothedRate.toFixed(1)} L/day)`,
          data: baselineRate,
          borderColor: '#f59e0b',
          borderWidth: 2,
          borderDash: [4, 4],
          pointRadius: 0,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            font: { family: 'Plus Jakarta Sans', size: 10 },
            color: '#94a3b8',
            maxTicksLimit: 12
          }
        },
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(15, 23, 42, 0.04)' },
          ticks: {
            font: { family: 'JetBrains Mono', size: 10 },
            color: '#94a3b8',
            callback: value => `${value} L`
          }
        }
      },
      plugins: {
        legend: {
          position: 'top',
          align: 'end',
          labels: {
            boxWidth: 10,
            usePointStyle: true,
            font: { family: 'Plus Jakarta Sans', size: 11, weight: '600' },
            color: '#475569'
          }
        },
        tooltip: {
          backgroundColor: '#0f172a',
          titleFont: { family: 'Plus Jakarta Sans', size: 12 },
          bodyFont: { family: 'JetBrains Mono', size: 12 },
          padding: 10,
          cornerRadius: 8
        }
      }
    }
  });
}
