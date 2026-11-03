/**
 * AquaGuard IQ v2.5 - Enterprise Prognostics & IoT Telemetry Platform
 * AtomQUEST Track 2: Water Purifier Prognostics & IoT Telemetry
 * Design System: Creamy Sand & Liquid Glass Edition
 * 
 * Manages view switching between 3D Hero Landing & Active Dashboard,
 * real-time telemetry polling, multi-factor degradation updates,
 * Chart.js synchronization, and authenticated ESP32 REST communications.
 */

let currentView = 'landing'; // 'landing' | 'dashboard'
let currentTelemetryData = null;
let pollTimer = null;

document.addEventListener('DOMContentLoaded', () => {
  initCoreViewSwitchers();
  initNavigationTabs();
  initSimulationAndApiControls();
  fetchTelemetryMetrics();

  // Watchdog & Telemetry background poller (every 5 seconds)
  pollTimer = setInterval(fetchTelemetryMetrics, 5000);
});

/* =========================================================================
 * 1. View Switchers: 3D Hero Landing vs Active Dashboard
 * ========================================================================= */
function openDashboard() {
  currentView = 'dashboard';
  const heroLanding = document.getElementById('hero-landing') || document.getElementById('landing-hero-section');
  const dashboardView = document.getElementById('dashboard-view') || document.getElementById('dashboard-app-section');
  const returnBtn = document.getElementById('btnReturnToLanding');
  const floatingReturnBtn = document.getElementById('btnFloatingBackToLanding');

  if (heroLanding) {
    heroLanding.classList.add('hidden');
    heroLanding.classList.add('view-hidden');
  }
  if (dashboardView) {
    dashboardView.classList.remove('hidden');
    dashboardView.classList.add('view-active');
  }
  if (returnBtn) returnBtn.style.display = 'inline-flex';
  if (floatingReturnBtn) floatingReturnBtn.style.display = 'inline-flex';

  // Default to Dashboard tab
  switchToDashboardTab('tab-dashboard');

  // Smooth layout for Chart.js without size flickering
  setTimeout(() => {
    window.dispatchEvent(new Event('resize'));
    if (currentTelemetryData && typeof updateCharts === 'function') {
      updateCharts(currentTelemetryData);
      populateRulForecastTable(currentTelemetryData.prognostics);
    }
  }, 60);

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function openLanding() {
  currentView = 'landing';
  const heroLanding = document.getElementById('hero-landing') || document.getElementById('landing-hero-section');
  const dashboardView = document.getElementById('dashboard-view') || document.getElementById('dashboard-app-section');
  const returnBtn = document.getElementById('btnReturnToLanding');
  const floatingReturnBtn = document.getElementById('btnFloatingBackToLanding');

  if (dashboardView) {
    dashboardView.classList.add('hidden');
    dashboardView.classList.remove('view-active');
  }
  if (heroLanding) {
    heroLanding.classList.remove('hidden');
    heroLanding.classList.remove('view-hidden');
  }
  if (returnBtn) returnBtn.style.display = 'none';
  if (floatingReturnBtn) floatingReturnBtn.style.display = 'none';

  // Deactivate tab pill highlights
  document.querySelectorAll('.nav-tab, .nav-pill-btn').forEach(t => t.classList.remove('active'));

  // Trigger Three.js canvas size sync
  setTimeout(() => {
    window.dispatchEvent(new Event('resize'));
  }, 50);

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function initCoreViewSwitchers() {
  const launchBtn = document.getElementById('btn-launch-telemetry') || document.getElementById('btnHeroLaunchTelemetry');
  const mathsBtn = document.getElementById('btn-read-maths') || document.getElementById('btnHeroReadMaths');
  const mathsModal = document.getElementById('maths-modal') || document.getElementById('mathsModal');
  const closeModalBtn = document.getElementById('btn-close-modal') || document.getElementById('btnCloseMathsModal');
  const closeModalFooterBtn = document.getElementById('btnCloseMathsModalFooter');
  const brandLogo = document.getElementById('brandLogoHome');
  const returnBtn = document.getElementById('btnReturnToLanding');
  const floatingReturnBtn = document.getElementById('btnFloatingBackToLanding');

  // Launch Telemetry LiquidButton
  if (launchBtn) {
    launchBtn.addEventListener('click', () => {
      openDashboard();
      showToast("▷ Telemetry Dashboard Launched", "info");
    });
  }

  // Return to 3D Hero
  if (returnBtn) returnBtn.addEventListener('click', openLanding);
  if (floatingReturnBtn) floatingReturnBtn.addEventListener('click', openLanding);
  if (brandLogo) brandLogo.addEventListener('click', openLanding);

  // Read the Maths Modal Handlers
  const showMathsModal = () => {
    if (!mathsModal) return;
    mathsModal.classList.remove('hidden');
    // Force DOM reflow for CSS transition
    void mathsModal.offsetWidth;
    mathsModal.classList.add('active');
  };

  const hideMathsModal = () => {
    if (!mathsModal) return;
    mathsModal.classList.remove('active');
    setTimeout(() => {
      if (!mathsModal.classList.contains('active')) {
        mathsModal.classList.add('hidden');
      }
    }, 280);
  };

  if (mathsBtn) {
    mathsBtn.addEventListener('click', showMathsModal);
  }

  if (closeModalBtn) {
    closeModalBtn.addEventListener('click', hideMathsModal);
  }

  if (closeModalFooterBtn) {
    closeModalFooterBtn.addEventListener('click', hideMathsModal);
  }

  // Close modal on backdrop click
  if (mathsModal) {
    mathsModal.addEventListener('click', (e) => {
      if (e.target === mathsModal) {
        hideMathsModal();
      }
    });
  }

  // Close modal on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && mathsModal && mathsModal.classList.contains('active')) {
      hideMathsModal();
    }
  });
}

/* =========================================================================
 * 2. Navigation Tabs (Overview, Analytics, Simulation, ESP32 API, Export)
 * ========================================================================= */
function initNavigationTabs() {
  const navTabs = document.querySelectorAll('.nav-tab, .nav-pill-btn');

  navTabs.forEach(tab => {
    tab.addEventListener('click', (e) => {
      e.preventDefault();
      const targetTabId = tab.getAttribute('data-target') || 'tab-dashboard';
      switchToDashboardTab(targetTabId);
    });
  });
}

function switchToDashboardTab(targetTabId) {
  // Ensure dashboard view is visible
  const heroLanding = document.getElementById('hero-landing') || document.getElementById('landing-hero-section');
  const dashboardView = document.getElementById('dashboard-view') || document.getElementById('dashboard-app-section');
  const returnBtn = document.getElementById('btnReturnToLanding');

  if (heroLanding) {
    heroLanding.classList.add('hidden');
    heroLanding.classList.add('view-hidden');
  }
  if (dashboardView) {
    dashboardView.classList.remove('hidden');
    dashboardView.classList.add('view-active');
  }
  if (returnBtn) returnBtn.style.display = 'inline-flex';

  // Update tabs active state
  document.querySelectorAll('.nav-tab, .nav-pill-btn').forEach(t => {
    if (t.getAttribute('data-target') === targetTabId) {
      t.classList.add('active');
    } else {
      t.classList.remove('active');
    }
  });

  // Switch tab pane
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  const activePane = document.getElementById(targetTabId);
  if (activePane) activePane.classList.add('active');

  // Trigger charts resize/render
  if (currentTelemetryData && typeof updateCharts === 'function') {
    setTimeout(() => {
      updateCharts(currentTelemetryData);
      populateRulForecastTable(currentTelemetryData.prognostics);
    }, 50);
  }

  // Lazy-load export table if opening export tab
  if (targetTabId === 'tab-export') {
    loadFullTelemetryLogs();
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

/* =========================================================================
 * 3. Telemetry Simulation Actions & ESP32 Hardware Testing
 * ========================================================================= */
function initSimulationAndApiControls() {
  // Flow Simulation Triggers (+1L, +10L, +50L) via .btn-sim-add
  document.querySelectorAll('.btn-sim-add, .btn-sim-quick').forEach(btn => {
    btn.addEventListener('click', async () => {
      const litres = parseFloat(btn.dataset.litres || '10');
      let flowRate = 2.4;
      let tds = 360;
      let label = `Quick Ingest (+${litres}L)`;

      if (litres >= 50) {
        flowRate = 5.2; // triggers hydraulic turbulence penalty
        tds = 550;      // triggers accelerated mineral scaling
        label = `Heavy Stress Test (+${litres}L)`;
      }

      await executeTelemetrySimulation(litres, flowRate, tds, label, btn);
    });
  });

  // Dedicated Simulation Form Ingestion
  const btnCustomSim = document.getElementById('btnSubmitManualSim');
  if (btnCustomSim) {
    btnCustomSim.addEventListener('click', async (e) => {
      e.preventDefault();
      const litres = parseFloat(document.getElementById('simLitresInput')?.value || 5);
      const flowRate = parseFloat(document.getElementById('simFlowRateInput')?.value || 2.5);
      const tds = parseFloat(document.getElementById('simTdsInput')?.value || 350);
      const label = document.getElementById('simEventLabelInput')?.value || "Custom Flow Dispense";

      await executeTelemetrySimulation(litres, flowRate, tds, label, btnCustomSim);
    });
  }

  // ESP32 API Test Call Handlers
  const esp32TestBtn = document.getElementById('btn-test-esp32') || 
                       document.getElementById('btnTestEsp32Endpoint') || 
                       document.getElementById('btnRunMatrixEsp32Test');

  if (esp32TestBtn) {
    esp32TestBtn.addEventListener('click', async () => {
      await executeEsp32HardwareTest();
    });
  }

  document.querySelectorAll('.btn-test-esp32').forEach(btn => {
    btn.addEventListener('click', async () => {
      await executeEsp32HardwareTest();
    });
  });

  const btnSendEsp32TestForm = document.getElementById('btnSendEsp32Test');
  if (btnSendEsp32TestForm) {
    btnSendEsp32TestForm.addEventListener('click', async () => {
      const apiKey = document.getElementById('testApiKeyInput')?.value || 'AG-IQ-SECRET-KEY-2026';
      const deviceId = document.getElementById('testDeviceIdInput')?.value || 'ESP32_CUSTOM_NODE';
      const litres = parseFloat(document.getElementById('testLitresInput')?.value || 2.5);
      const flowRate = parseFloat(document.getElementById('testFlowRateInput')?.value || 3.2);
      const tds = parseFloat(document.getElementById('testTdsInput')?.value || 385);

      await executeCustomEsp32Payload(apiKey, deviceId, litres, flowRate, tds);
    });
  }

  // Copy Arduino Firmware Handler
  const btnCopyArduino = document.getElementById('btnCopyArduinoSketch');
  if (btnCopyArduino) {
    btnCopyArduino.addEventListener('click', async () => {
      const codeBlock = document.getElementById('arduinoCodeBlock');
      if (codeBlock) {
        const codeText = codeBlock.innerText.trim();
        try {
          if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(codeText);
          } else {
            const ta = document.createElement('textarea');
            ta.value = codeText;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
          }
          showToast("Arduino ESP32 firmware copied to clipboard!", "success");
          btnCopyArduino.textContent = "Copied ✓";
          setTimeout(() => {
            btnCopyArduino.textContent = "Copy Firmware";
          }, 2000);
        } catch (err) {
          showToast("Failed to copy code: " + err.message, "error");
        }
      }
    });
  }

  // Configuration Form: Update Rated Capacity
  const btnCapacity = document.getElementById('btnUpdateRatedCapacity');
  if (btnCapacity) {
    btnCapacity.addEventListener('click', async () => {
      const input = document.getElementById('inputRatedCapacity');
      const val = parseFloat(input?.value);
      if (!val || val <= 0) {
        showToast("Enter a valid membrane rated capacity (L)", "warning");
        return;
      }
      try {
        const res = await fetch('/api/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ rated_capacity_litres: val })
        });
        const data = await res.json();
        if (res.ok) {
          showToast(`Rated capacity updated to ${val.toLocaleString()} L`, "success");
          fetchTelemetryMetrics();
        } else {
          showToast(data.message || "Failed to update capacity", "error");
        }
      } catch (err) {
        showToast("Network error updating capacity", "error");
      }
    });
  }

  // Configuration Form: Daily Household Target
  const btnDaily = document.getElementById('btnUpdateDailyTarget');
  if (btnDaily) {
    btnDaily.addEventListener('click', async () => {
      const input = document.getElementById('inputDailyTarget');
      const val = parseFloat(input?.value);
      if (!val || val <= 0) {
        showToast("Enter a valid daily target (L)", "warning");
        return;
      }
      try {
        const res = await fetch('/api/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ daily_target_litres: val })
        });
        const data = await res.json();
        if (res.ok) {
          showToast(`Daily consumption target set to ${val} L/day`, "success");
          fetchTelemetryMetrics();
        } else {
          showToast(data.message || "Failed to update daily target", "error");
        }
      } catch (err) {
        showToast("Network error updating daily target", "error");
      }
    });
  }

  // CSV Export Buttons
  const csvPrimary = document.getElementById('btnExportCsvPrimary');
  const csvTrigger = document.getElementById('btnTriggerExportCsv');
  [csvPrimary, csvTrigger].forEach(btn => {
    if (btn) {
      btn.addEventListener('click', () => {
        showToast("Generating CSV Export...", "info");
        window.location.href = '/api/export-csv';
      });
    }
  });

  // Reset Modal Handlers
  initResetModalControls();

  // Diagnostic Modal
  initDiagnosticModalControls();

  // Header Refresh Sync Button
  const headerSync = document.getElementById('headerRefreshBtn');
  if (headerSync) {
    headerSync.addEventListener('click', async () => {
      await fetchTelemetryMetrics();
      showToast("Telemetry metrics refreshed", "success");
    });
  }
}

/* =========================================================================
 * 4. Telemetry Ingestion Core
 * ========================================================================= */
async function executeTelemetrySimulation(litres, flowRate, tds, label, buttonEl) {
  try {
    if (buttonEl) buttonEl.disabled = true;

    const response = await fetch('/api/add-usage', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        litres: litres,
        flow_rate_lpm: flowRate,
        tds_ppm: tds,
        event_label: label
      })
    });

    const data = await response.json();
    if (response.ok) {
      updateMetricsUI(data);
      if (data.prognostics) {
        updateHeroDegradationCard(data.prognostics);
        updateKpiCards(data.prognostics);
      }

      // Push real-time incremental point into Chart.js
      if (typeof pushDataPointToCharts === 'function' && data.added_record && data.prognostics) {
        pushDataPointToCharts(data.added_record, data.prognostics);
      }

      showToast(`+${litres}L Ingested • Effective Wear: ${data.added_record?.effective_litres?.toFixed(2)}L (${data.prognostics?.status_badge || 'OK'})`, "success");
      fetchTelemetryMetrics();
    } else {
      showToast("Simulation error: " + (data.message || "Rejected"), "error");
    }
  } catch (err) {
    console.error("Telemetry simulation error:", err);
    showToast("Network error simulating flow telemetry", "error");
  } finally {
    if (buttonEl) buttonEl.disabled = false;
  }
}

async function executeEsp32HardwareTest() {
  const terminal = document.getElementById('apiResponseTerminal');
  const badge = document.getElementById('apiResponseStatusBadge');
  const apiKey = document.getElementById('testApiKeyInput')?.value || 'AG-IQ-SECRET-KEY-2026';

  if (terminal) terminal.textContent = "[TRANSMITTING] POST /api/sensor-data (Simulated Hardware Handshake)...";

  try {
    const res = await fetch('/api/sensor-data', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Sensor-API-Key': apiKey
      },
      body: JSON.stringify({
        device_id: 'ESP32_TEST',
        litres_flowed: 2.5,
        flow_rate_lpm: 3.2,
        tds_ppm: 385.0,
        is_simulation: true
      })
    });
    const result = await res.json();
    if (terminal) {
      terminal.textContent = `HTTP ${res.status} ${res.ok ? 'OK (Simulated Handshake Verified)' : 'REJECTED'}\n` + JSON.stringify(result, null, 2);
    }
    if (badge) {
      badge.className = `badge-status ${res.ok ? 'normal' : 'danger'}`;
      badge.textContent = res.ok ? 'Verified 200' : `Error ${res.status}`;
    }
    if (res.ok) {
      showToast("ESP32 Test Endpoint Verified! (HTTP 200 OK — Simulated Handshake)", "success");
      fetchTelemetryMetrics();
    } else {
      showToast("API Error: " + (result.error || result.message || "Validation failed"), "error");
    }
  } catch (err) {
    if (terminal) terminal.textContent = `Network Error:\n${err.message}`;
    showToast("ESP32 Test Failed: " + err.message, "error");
  }
}

async function executeCustomEsp32Payload(apiKey, deviceId, litres, flowRate, tds) {
  const terminal = document.getElementById('apiResponseTerminal');
  const badge = document.getElementById('apiResponseStatusBadge');

  if (terminal) terminal.textContent = `[TRANSMITTING] POST /api/sensor-data\nDevice: ${deviceId}\nLitres: ${litres} L | Flow: ${flowRate} LPM | TDS: ${tds} PPM...`;

  try {
    const res = await fetch('/api/sensor-data', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Sensor-API-Key': apiKey
      },
      body: JSON.stringify({
        device_id: deviceId,
        litres_flowed: litres,
        flow_rate_lpm: flowRate,
        tds_ppm: tds
      })
    });

    const result = await res.json();
    if (terminal) {
      terminal.textContent = `HTTP ${res.status} ${res.ok ? 'OK' : 'ERROR'}\n` + JSON.stringify(result, null, 2);
    }

    if (badge) {
      badge.className = `badge-status ${res.ok ? 'normal' : 'danger'}`;
      badge.textContent = res.ok ? 'Success 200' : `Error ${res.status}`;
    }

    if (res.ok) {
      showToast(`Payload Ingested by ESP32 Gateway (${result.effective_wear_litres}L Wear)`, "success");
      fetchTelemetryMetrics();
    } else {
      showToast(`Rejected: ${result.message}`, "error");
    }
  } catch (err) {
    if (terminal) terminal.textContent = `Transmission Error:\n${err.message}`;
    showToast("Transmission Error: " + err.message, "error");
  }
}

/* =========================================================================
 * 5. Fetch & Synchronize Metrics UI
 * ========================================================================= */
async function fetchTelemetryMetrics() {
  try {
    const res = await fetch('/api/metrics');
    if (!res.ok) return;
    const data = await res.json();
    currentTelemetryData = data;

    updateMetricsUI(data);
    updateHardwareWatchdogBadge(data.system_state);
    updateHeroDegradationCard(data.prognostics);
    updateKpiCards(data.prognostics);
    updateRecentLogsTable(data.recent_logs);
    populateRulForecastTable(data.prognostics);

    // Keep charts synced
    if (typeof updateCharts === 'function') {
      updateCharts(data);
    }
  } catch (err) {
    console.warn("Metrics polling sync warning:", err);
  }
}

/**
 * Standard Telemetry State Updater (Prompt Specification)
 */
function updateMetricsUI(data) {
  if (!data) return;
  const prog = data.prognostics || data;

  const usageVal = document.getElementById('metric-total-usage');
  const remainingVal = document.getElementById('metric-remaining');
  const statusBadge = document.getElementById('metric-status');
  const consumedVal = document.getElementById('metric-capacity-consumed');
  const healthVal = document.getElementById('metric-health-score');

  const totalRaw = (prog.total_raw_litres !== undefined) ? prog.total_raw_litres : (data.total_usage || 0);
  const remaining = (prog.remaining_capacity_litres !== undefined) ? prog.remaining_capacity_litres : (data.remaining_capacity || 0);
  const status = prog.status_badge || prog.prognostic_status || data.prognostic_status || 'Operational';
  const consumed = (prog.capacity_consumed_pct !== undefined) ? prog.capacity_consumed_pct : (data.capacity_consumed_pct || 0);
  const health = (prog.health_score_pct !== undefined) ? prog.health_score_pct : 100.0;

  if (usageVal) usageVal.innerText = `${totalRaw.toLocaleString()} L`;
  if (remainingVal) remainingVal.innerText = `${remaining.toLocaleString()} L`;
  if (statusBadge) statusBadge.innerText = status;
  if (consumedVal) consumedVal.innerText = `${consumed.toFixed(1)}%`;
  if (healthVal) healthVal.innerText = `${health.toFixed(1)}%`;

  // Synchronize Live Hero Floating Telemetry Cards
  const heroMembrane = document.getElementById('heroMembranePct');
  const heroHardness = document.getElementById('heroHardnessState');
  const heroConn = document.getElementById('heroConnState');

  if (heroMembrane) {
    heroMembrane.textContent = `${Math.round(health)}%`;
  }
  if (heroHardness) {
    const isHardnessActive = (prog.penalty_factors && prog.penalty_factors.k_tds > 1.0) || true;
    heroHardness.textContent = isHardnessActive ? 'active' : 'nominal';
  }
  if (heroConn) {
    const isLive = data.system_state && data.system_state.sensor_status === 'ESP32_CONNECTED';
    heroConn.textContent = isLive ? 'live' : 'connected';
  }
}

function updateHardwareWatchdogBadge(systemState, customOverrideText = null) {
  const pill = document.getElementById('connectionStatusPill');
  const pillText = document.getElementById('connectionStatusText');
  const pillTitle = document.getElementById('connectionStatusTitle');
  const pillSubtitle = document.getElementById('connectionStatusSubtitle');
  const banner = document.getElementById('watchdogWarningBanner');
  const bannerSeconds = document.getElementById('watchdogElapsedSeconds');

  if (!pill) return;

  pill.className = 'connection-pill-capsule';

  if (customOverrideText) {
    pill.classList.add('esp32-live');
    if (pillTitle) pillTitle.textContent = customOverrideText;
    if (pillSubtitle) pillSubtitle.textContent = 'Hardware Handshake';
    if (pillText) pillText.textContent = customOverrideText;
    if (banner) banner.classList.remove('active');
    return;
  }

  const status = systemState ? (systemState.sensor_status || 'SIMULATION_MODE') : 'SIMULATION_MODE';
  const elapsed = systemState ? systemState.watchdog_elapsed_seconds : 0;

  if (status === 'ESP32_CONNECTED') {
    pill.classList.add('esp32-live');
    const dev = systemState.device_id || 'Active';
    if (pillTitle) pillTitle.textContent = 'ESP32 Live';
    if (pillSubtitle) pillSubtitle.textContent = `Node: ${dev}`;
    if (pillText) pillText.textContent = `ESP32 Live (${dev})`;
    if (banner) banner.classList.remove('active');
  } else if (status === 'SENSOR_OFFLINE_FALLBACK_ACTIVE') {
    pill.classList.add('sensor-offline');
    const elapsedMins = elapsed ? Math.floor(elapsed / 60) : 5;
    if (pillTitle) pillTitle.textContent = 'Sensor Offline';
    if (pillSubtitle) pillSubtitle.textContent = `${elapsedMins}m Fallback`;
    if (pillText) pillText.textContent = `Sensor Offline (${elapsedMins}m Fallback)`;
    if (banner) {
      banner.classList.add('active');
      if (bannerSeconds) bannerSeconds.textContent = Math.round(elapsed || 300);
    }
  } else {
    pill.classList.add('simulation');
    if (pillTitle) pillTitle.textContent = 'Simulation Mode';
    if (pillSubtitle) pillSubtitle.textContent = 'Live Connection';
    if (pillText) pillText.textContent = 'Simulation Mode (Live Connection)';
    if (banner) banner.classList.remove('active');
  }
}

function updateHeroDegradationCard(prog) {
  if (!prog) return;

  const rawEl = document.getElementById('heroRawLitres');
  const effEl = document.getElementById('heroEffectiveWear');
  const excessEl = document.getElementById('heroExcessWear');
  const multEl = document.getElementById('heroWearMultiplier');
  const statusEl = document.getElementById('heroStatusBadge');
  const descEl = document.getElementById('heroStatusDesc');

  if (rawEl) rawEl.textContent = `${prog.total_raw_litres.toLocaleString()} L`;
  if (effEl) effEl.textContent = `${prog.total_effective_litres.toLocaleString()} L`;
  if (excessEl) excessEl.textContent = `+${prog.excess_wear_pct}%`;
  if (multEl) multEl.textContent = `${prog.wear_multiplier}x`;

  if (statusEl) {
    statusEl.className = `badge-status ${prog.status_level}`;
    statusEl.textContent = prog.status_badge;
  }
  if (descEl) {
    descEl.textContent = prog.status_description;
  }
}

function updateKpiCards(prog) {
  if (!prog) return;

  const rawKpi = document.getElementById('kpiRawLitres');
  if (rawKpi) rawKpi.textContent = prog.total_raw_litres.toLocaleString();

  const effKpi = document.getElementById('kpiEffectiveWear');
  if (effKpi) effKpi.textContent = prog.total_effective_litres.toLocaleString();

  const remKpi = document.getElementById('kpiRemainingCapacity');
  if (remKpi) remKpi.textContent = prog.remaining_capacity_litres.toLocaleString();

  const healthKpi = document.getElementById('kpiHealthScore');
  const healthFill = document.getElementById('kpiHealthFill');
  if (healthKpi) healthKpi.textContent = `${prog.health_score_pct.toFixed(1)}%`;
  if (healthFill) {
    healthFill.style.width = `${prog.health_score_pct}%`;
    healthFill.className = `progress-bar-fill ${prog.status_level}`;
  }

  const consumedKpi = document.getElementById('kpiCapacityConsumed');
  const metricConsumed = document.getElementById('metric-capacity-consumed');
  const metricHealth = document.getElementById('metric-health-score');
  if (consumedKpi && prog.capacity_consumed_pct !== undefined) {
    consumedKpi.textContent = `${prog.capacity_consumed_pct.toFixed(1)}%`;
  }
  if (metricConsumed && prog.capacity_consumed_pct !== undefined) {
    metricConsumed.textContent = `${prog.capacity_consumed_pct.toFixed(1)}%`;
  }
  if (metricHealth && prog.health_score_pct !== undefined) {
    metricHealth.textContent = `${prog.health_score_pct.toFixed(1)}%`;
  }

  const rulKpi = document.getElementById('kpiRulDays');
  const rulSub = document.getElementById('kpiRulBurnRate');
  if (rulKpi) rulKpi.textContent = prog.rul_days > 900 ? '999+' : `${prog.rul_days} Days`;
  if (rulSub) rulSub.textContent = `Based on ~${prog.daily_usage_rate.toFixed(1)} L/day (7-Day Smoothed)`;
}

function updateRecentLogsTable(logs) {
  const tbody = document.getElementById('recentLogsTableBody');
  if (!tbody || !logs) return;

  if (logs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding: 2rem; color: #94a3b8;">No telemetry records logged yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = logs.map(row => {
    const isSensor = row.source === 'SENSOR';
    const sourceClass = isSensor ? 'badge-status normal' : 'badge-status warning';
    const sourceText = isSensor ? 'ESP32 SENSOR' : 'SIMULATION';

    return `
      <tr>
        <td><strong>${escapeHtml(row.record_id)}</strong></td>
        <td>${escapeHtml(row.timestamp)}</td>
        <td>${escapeHtml(row.device_id)}</td>
        <td><span class="${sourceClass}">${sourceText}</span></td>
        <td>${escapeHtml(row.event_type)}</td>
        <td style="color: #0284c7; font-weight:700;">${row.raw_litres.toFixed(2)} L</td>
        <td>${row.flow_rate.toFixed(2)} LPM</td>
        <td>${row.tds_ppm.toFixed(0)} PPM</td>
        <td style="color: #059669; font-weight:700;">${row.effective_litres.toFixed(2)} L</td>
      </tr>
    `;
  }).join('');
}

function populateRulForecastTable(prog) {
  if (!prog) return;

  const scoreEl = document.getElementById('tableHealthScore');
  const rateEl = document.getElementById('tableDailyRate');
  const rulEl = document.getElementById('tableRulDays');
  const dateEl = document.getElementById('tableProjectedDate');
  const actionEl = document.getElementById('tableRulAction');

  if (scoreEl) scoreEl.textContent = `${prog.health_score_pct.toFixed(1)}% (${prog.prognostic_status})`;
  if (rateEl) rateEl.textContent = `${prog.daily_usage_rate.toFixed(1)} L/day`;
  if (rulEl) rulEl.textContent = `${prog.rul_days} Days Remaining`;

  const projected = new Date();
  projected.setDate(projected.getDate() + (prog.rul_days > 900 ? 900 : prog.rul_days));
  const dateFormatted = projected.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  if (dateEl) dateEl.textContent = dateFormatted;

  if (actionEl) {
    if (prog.prognostic_status === 'CRITICAL_REPLACE') {
      actionEl.innerHTML = `<span style="color:var(--status-danger); font-weight:700;">⚠️ Urgent: Replace Cartridge Now</span>`;
    } else if (prog.prognostic_status === 'ATTENTION_REQUIRED') {
      actionEl.innerHTML = `<span style="color:var(--status-warning); font-weight:700;">Pre-order replacement filter</span>`;
    } else {
      actionEl.innerHTML = `<span style="color:var(--status-normal); font-weight:700;">Normal operation envelope</span>`;
    }
  }
}

/* =========================================================================
 * 6. Modals: Reset & Diagnostics
 * ========================================================================= */
function initResetModalControls() {
  const modal = document.getElementById('resetModal');
  const btnOpen1 = document.getElementById('btnResetSimulationData');
  const btnOpen2 = document.getElementById('btnOpenResetModalSim');
  const btnCancel1 = document.getElementById('btnCancelReset');
  const btnCancel2 = document.getElementById('btnCancelResetFooter');
  const btnEmpty = document.getElementById('btnConfirmResetEmpty');
  const btnSample = document.getElementById('btnConfirmResetSample');

  function openReset() {
    if (modal) {
      modal.classList.add('active');
      modal.classList.remove('hidden');
    }
  }
  function closeReset() {
    if (modal) {
      modal.classList.remove('active');
      modal.classList.add('hidden');
    }
  }

  if (btnOpen1) btnOpen1.addEventListener('click', openReset);
  if (btnOpen2) btnOpen2.addEventListener('click', openReset);
  if (btnCancel1) btnCancel1.addEventListener('click', closeReset);
  if (btnCancel2) btnCancel2.addEventListener('click', closeReset);

  if (btnEmpty) {
    btnEmpty.addEventListener('click', async () => {
      try {
        const res = await fetch('/api/reset', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mode: 'empty' })
        });
        if (res.ok) {
          showToast("Filter history wiped clean to 0 L", "success");
          closeReset();
          fetchTelemetryMetrics();
        }
      } catch (err) {
        showToast("Reset failed", "error");
      }
    });
  }

  if (btnSample) {
    btnSample.addEventListener('click', async () => {
      try {
        const res = await fetch('/api/reset', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mode: 'sample' })
        });
        if (res.ok) {
          showToast("AtomQUEST reference dataset restored & re-evaluated", "success");
          closeReset();
          fetchTelemetryMetrics();
        }
      } catch (err) {
        showToast("Reset failed", "error");
      }
    });
  }
}

function initDiagnosticModalControls() {
  const modal = document.getElementById('diagnosticModal');
  const btnOpen = document.getElementById('btnOpenDiagnosticModal');
  const btnClose = document.getElementById('btnCloseDiagnosticModal');
  const btnCloseFooter = document.getElementById('btnCloseDiagModalFooter');
  const btnApiTester = document.getElementById('btnOpenFullApiTesterFromModal');

  if (btnOpen && modal) {
    btnOpen.addEventListener('click', () => {
      modal.classList.add('active');
      modal.classList.remove('hidden');
    });
  }
  if (btnClose && modal) {
    btnClose.addEventListener('click', () => {
      modal.classList.remove('active');
      modal.classList.add('hidden');
    });
  }
  if (btnCloseFooter && modal) {
    btnCloseFooter.addEventListener('click', () => {
      modal.classList.remove('active');
      modal.classList.add('hidden');
    });
  }
  if (btnApiTester) {
    btnApiTester.addEventListener('click', () => {
      if (modal) {
        modal.classList.remove('active');
        modal.classList.add('hidden');
      }
      switchToDashboardTab('tab-esp32');
    });
  }
}

async function loadFullTelemetryLogs() {
  const tbody = document.getElementById('fullLogsTableBody');
  if (!tbody) return;

  try {
    const res = await fetch('/api/metrics');
    if (!res.ok) return;
    const data = await res.json();
    const logs = data.recent_logs || [];

    if (logs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 2rem; color: #94a3b8;">No records to preview.</td></tr>`;
      return;
    }

    tbody.innerHTML = logs.map(r => `
      <tr>
        <td><strong>${escapeHtml(r.record_id)}</strong></td>
        <td>${escapeHtml(r.timestamp)}</td>
        <td>${escapeHtml(r.source)}</td>
        <td>${r.raw_litres.toFixed(2)} L</td>
        <td>${r.flow_rate.toFixed(2)} LPM</td>
        <td>${r.tds_ppm.toFixed(0)} PPM</td>
        <td style="color:#059669; font-weight:700;">${r.effective_litres.toFixed(2)} L</td>
      </tr>
    `).join('');
  } catch (err) {
    console.error("Failed to load logs preview:", err);
  }
}

/* =========================================================================
 * 7. Helpers: Toast Notifications & HTML Escaping
 * ========================================================================= */
function showToast(message, type = 'info') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span>${escapeHtml(message)}</span>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
