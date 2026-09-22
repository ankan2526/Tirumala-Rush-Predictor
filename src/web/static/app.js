// Tirumala Tirupati Rush Predictor Frontend Logic

let currentCalYear = 2026;
let currentCalMonth = 9;
let calendarDataCache = {};

document.addEventListener("DOMContentLoaded", () => {
  // Initialize Lucide icons
  if (window.lucide) {
    lucide.createIcons();
  }

  // Set default dates
  const today = new Date();
  // Sync to 2026 if year is around 2026
  currentCalYear = today.getFullYear();
  currentCalMonth = today.getMonth() + 1;

  const todayStr = formatDate(today);
  const next30 = new Date(today.getTime() + 30 * 86400000);

  const predictInput = document.getElementById("predict-input-date");
  if (predictInput) predictInput.value = todayStr;

  const optStart = document.getElementById("opt-start-date");
  const optEnd = document.getElementById("opt-end-date");
  if (optStart) optStart.value = todayStr;
  if (optEnd) optEnd.value = formatDate(next30);

  // Load initial views
  fetchLiveStatus();
  loadCalendar(currentCalYear, currentCalMonth);
  fetchDatePrediction(todayStr);
  loadInsights();
});

// -------------------------------------------------------------
// NAVIGATION TABS
// -------------------------------------------------------------
function switchTab(tabId) {
  document.querySelectorAll(".tab-content").forEach((el) => el.classList.add("hidden"));
  document.querySelectorAll(".nav-tab").forEach((btn) => btn.classList.remove("active"));

  const targetSection = document.getElementById(`tab-${tabId}`);
  const targetBtn = document.getElementById(`tab-btn-${tabId}`);

  if (targetSection) targetSection.classList.remove("hidden");
  if (targetBtn) targetBtn.classList.add("active");

  if (window.lucide) {
    lucide.createIcons();
  }
}

// -------------------------------------------------------------
// TOP LIVE STATUS GLANCE
// -------------------------------------------------------------
async function fetchLiveStatus() {
  try {
    const res = await fetch("/api/live-status");
    const data = await res.json();

    if (data && data.today) {
      const today = data.today;
      const dateEl = document.getElementById("header-today-date");
      const badgeEl = document.getElementById("header-today-badge");
      const waitEl = document.getElementById("header-today-wait");
      const pillEl = document.getElementById("top-live-pill");

      if (dateEl) dateEl.textContent = today.date;
      if (badgeEl) {
        badgeEl.textContent = today.rush_level;
        badgeEl.className = `text-xs px-2 py-0.5 rounded font-bold uppercase ${today.badge_class}`;
      }
      if (waitEl) waitEl.textContent = `Sarva: ${today.sarva_darshan_wait_hours}h`;
      if (pillEl) pillEl.classList.remove("hidden");
    }
  } catch (err) {
    console.warn("Could not fetch live status:", err);
  }
}

// -------------------------------------------------------------
// RUSH CALENDAR
// -------------------------------------------------------------
async function loadCalendar(year, month) {
  const titleEl = document.getElementById("cal-month-title");
  const seasonEl = document.getElementById("cal-season-subtitle");
  const gridEl = document.getElementById("calendar-days-grid");

  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];
  if (titleEl) titleEl.textContent = `${monthNames[month - 1]} ${year}`;

  // Season descriptions
  const seasons = {
    1: "Vaikunta Dwara Darshanam & Sankranti Festival Rush",
    2: "Annual Rathasapthami & School Exam Lean Season Starts",
    3: "Board Exam Season (Leanest Pilgrimage Window of the Year)",
    4: "Ugadi Asthanam & Summer Vacation Buildup Begins",
    5: "Peak Summer Vacation Rush (Continuous High Crowds)",
    6: "Summer Rush Wind-down & Jyestabhishekam",
    7: "Dakshinayana Punya Kalam & Monsoon Term",
    8: "Shravana Masam (Auspicious Fridays & Varalakshmi Vratam)",
    9: "Purattasi Masam Influx & Srivari Salakatla Brahmotsavam",
    10: "Navaratri Brahmotsavam & Dussehra School Holidays",
    11: "Auspicious Karthika Masam & Deepotsavam Surge",
    12: "Year-End Surge & Vaikuntha Ekadashi Opening"
  };
  if (seasonEl) seasonEl.textContent = seasons[month] || "Regular Pilgrimage Season";

  gridEl.innerHTML = `
    <div class="col-span-7 py-16 text-center text-slate-500">
      <i data-lucide="loader-2" class="w-8 h-8 animate-spin mx-auto text-amber-400 mb-2"></i>
      <p>Loading monthly crowd heatmap...</p>
    </div>
  `;
  if (window.lucide) lucide.createIcons();

  try {
    const res = await fetch(`/api/calendar?year=${year}&month=${month}`);
    const data = await res.json();
    calendarDataCache[`${year}-${month}`] = data.days;
    renderCalendarGrid(data.days, year, month);
  } catch (err) {
    gridEl.innerHTML = `<div class="col-span-7 text-center text-rose-400 py-10">Failed to load calendar data.</div>`;
  }
}

function renderCalendarGrid(days, year, month) {
  const gridEl = document.getElementById("calendar-days-grid");
  gridEl.innerHTML = "";

  if (!days || days.length === 0) return;

  // First day offset (0=Mon, 6=Sun)
  const firstWeekday = days[0].weekday_num; // Monday is 0
  for (let i = 0; i < firstWeekday; i++) {
    const emptyCell = document.createElement("div");
    emptyCell.className = "bg-slate-900/30 rounded-xl border border-dashed border-slate-800/50 p-2 hidden sm:block opacity-30";
    gridEl.appendChild(emptyCell);
  }

  days.forEach((dayData) => {
    const cell = document.createElement("div");
    const isPeak = dayData.rush_level === "PEAK";
    const isLow = dayData.rush_level === "LOW";
    const glowClass = isPeak ? "border-peak-glow" : (isLow ? "border-low-glow" : "");

    cell.className = `cal-cell bg-slate-900 border border-slate-800 rounded-xl p-2 sm:p-2.5 flex flex-col justify-between min-h-[90px] sm:min-h-[105px] ${glowClass}`;
    cell.onclick = () => openDayModal(dayData);

    const eventTag = dayData.highlight_event
      ? `<span class="truncate text-[10px] font-medium text-amber-300 bg-amber-500/15 border border-amber-500/30 px-1.5 py-0.5 rounded block mt-1" title="${dayData.highlight_event}">${dayData.highlight_event}</span>`
      : "";

    cell.innerHTML = `
      <div>
        <div class="flex items-center justify-between">
          <span class="font-bold text-sm text-slate-200">${dayData.day}</span>
          <span class="text-[10px] px-1.5 py-0.5 rounded font-bold uppercase ${dayData.badge_class}">${dayData.rush_level}</span>
        </div>
        ${eventTag}
      </div>

      <div class="pt-2 border-t border-slate-800/80 space-y-0.5 text-[11px]">
        <div class="flex justify-between text-slate-400">
          <span>Devotees:</span>
          <span class="font-semibold text-slate-200">${formatK(dayData.estimated_pilgrims)}</span>
        </div>
        <div class="flex justify-between text-slate-400">
          <span>Sarva:</span>
          <span class="font-bold" style="color: ${dayData.rush_color}">${dayData.sarva_darshan_wait_hours}h</span>
        </div>
      </div>
    `;

    gridEl.appendChild(cell);
  });

  if (window.lucide) lucide.createIcons();
}

function changeMonth(delta) {
  currentCalMonth += delta;
  if (currentCalMonth > 12) {
    currentCalMonth = 1;
    currentCalYear += 1;
  } else if (currentCalMonth < 1) {
    currentCalMonth = 12;
    currentCalYear -= 1;
  }
  loadCalendar(currentCalYear, currentCalMonth);
}

function jumpToToday() {
  const today = new Date();
  currentCalYear = today.getFullYear();
  currentCalMonth = today.getMonth() + 1;
  loadCalendar(currentCalYear, currentCalMonth);
}

// -------------------------------------------------------------
// DAY CLICK MODAL
// -------------------------------------------------------------
function openDayModal(day) {
  const modal = document.getElementById("day-modal");
  const content = document.getElementById("modal-day-content");

  content.innerHTML = `
    <div class="space-y-4">
      <div>
        <div class="flex items-center space-x-2">
          <span class="text-xs px-2.5 py-0.5 rounded-full font-bold uppercase ${day.badge_class}">${day.rush_level} RUSH</span>
          <span class="text-xs text-slate-400">${day.tithi}</span>
        </div>
        <h3 class="text-xl font-bold font-cinzel text-amber-300 mt-1">${day.date} (${day.day_name})</h3>
        ${day.highlight_event ? `<p class="text-xs text-amber-400 font-semibold mt-0.5">★ ${day.highlight_event}</p>` : ''}
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div class="bg-slate-900 p-3 rounded-xl border border-slate-800">
          <span class="text-xs text-slate-400">Pilgrim Count</span>
          <div class="text-lg font-bold text-white">${day.estimated_pilgrims.toLocaleString()}</div>
        </div>
        <div class="bg-slate-900 p-3 rounded-xl border border-slate-800">
          <span class="text-xs text-slate-400">Vaikuntam Compartments</span>
          <div class="text-lg font-bold text-amber-400">${day.compartments_filled} / 31 filled</div>
        </div>
      </div>

      <div class="bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 space-y-2 text-xs">
        <div class="flex justify-between items-center pb-2 border-b border-slate-800">
          <span class="text-slate-300 font-semibold">Sarva Darshan (Free / SSD):</span>
          <span class="font-bold text-sm" style="color: ${day.rush_color}">${day.sarva_darshan_wait_hours} Hours</span>
        </div>
        <div class="flex justify-between items-center">
          <span class="text-slate-300 font-semibold">Special Entry Darshan (₹300):</span>
          <span class="font-bold text-sm text-emerald-400">${day.sed_wait_hours} Hours</span>
        </div>
      </div>

      <div class="flex justify-end space-x-3 pt-2">
        <button onclick="inspectDateInDeepDive('${day.date}')" class="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs transition flex items-center space-x-1.5">
          <i data-lucide="external-link" class="w-3.5 h-3.5"></i>
          <span>Full Deep-Dive Breakdown</span>
        </button>
      </div>
    </div>
  `;

  modal.classList.remove("hidden");
  if (window.lucide) lucide.createIcons();
}

function closeDayModal() {
  document.getElementById("day-modal").classList.add("hidden");
}

function inspectDateInDeepDive(dateStr) {
  closeDayModal();
  switchTab("predict");
  document.getElementById("predict-input-date").value = dateStr;
  fetchDatePrediction(dateStr);
}

// -------------------------------------------------------------
// DATE PREDICTOR (DEEP DIVE)
// -------------------------------------------------------------
async function fetchDatePrediction(dateStr) {
  if (!dateStr) {
    const input = document.getElementById("predict-input-date");
    dateStr = input ? input.value : formatDate(new Date());
  }

  const container = document.getElementById("prediction-result-container");
  container.innerHTML = `
    <div class="text-center py-16 text-slate-500">
      <i data-lucide="loader-2" class="w-8 h-8 animate-spin mx-auto text-amber-400 mb-2"></i>
      <p>Simulating temple queue dynamics and panchangam for ${dateStr}...</p>
    </div>
  `;
  if (window.lucide) lucide.createIcons();

  try {
    const res = await fetch(`/api/predict?date=${dateStr}`);
    const data = await res.json();
    renderPredictionResult(data);
  } catch (err) {
    container.innerHTML = `<div class="text-rose-400 text-center py-8">Error loading prediction: ${err.message}</div>`;
  }
}

function setAndPredictDate(target) {
  let dStr;
  const today = new Date();

  if (target === "today") {
    dStr = formatDate(today);
  } else if (target === "next-sat") {
    const day = today.getDay();
    const diff = (6 - day + 7) % 7 || 7;
    const nextSat = new Date(today.getTime() + diff * 86400000);
    dStr = formatDate(nextSat);
  } else {
    dStr = target;
  }

  document.getElementById("predict-input-date").value = dStr;
  fetchDatePrediction(dStr);
}

function renderPredictionResult(p) {
  const container = document.getElementById("prediction-result-container");

  // Factors HTML
  const factorsHtml = p.factors.map(f => `
    <div class="bg-slate-900 border border-slate-800 rounded-xl p-3.5 flex items-start justify-between gap-3">
      <div>
        <div class="text-[10px] font-semibold uppercase tracking-wider text-slate-400">${f.category}</div>
        <div class="font-bold text-sm text-slate-200 mt-0.5">${f.name}</div>
        <div class="text-xs text-slate-400 mt-1">${f.detail}</div>
      </div>
      <div class="flex-shrink-0">
        <span class="text-xs font-bold px-2 py-1 rounded ${f.favorable ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'}">
          ${f.impact}
        </span>
      </div>
    </div>
  `).join("");

  // Tips HTML
  const tipsHtml = p.recommendations.travel_tips.map(t => `
    <li class="flex items-start space-x-2 text-xs text-slate-300">
      <i data-lucide="check-circle-2" class="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5"></i>
      <span>${t}</span>
    </li>
  `).join("");

  container.innerHTML = `
    <!-- Top Hero Card -->
    <div class="bg-gradient-to-r from-slate-900 via-[#111827] to-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-6">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div class="flex items-center space-x-2.5">
            <span class="text-xs px-2.5 py-1 rounded-full font-bold uppercase ${p.badge_class}">
              ${p.rush_level} RUSH
            </span>
            <span class="text-xs text-amber-400/90 font-medium">Tithi: ${p.tithi} (${p.paksha})</span>
            <span class="text-xs text-slate-400">• Moon: ${p.moon_illumination}</span>
          </div>
          <h2 class="text-2xl font-bold font-cinzel text-white mt-1.5">${p.date} (${p.day_name})</h2>
          <p class="text-sm font-medium mt-0.5" style="color: ${p.rush_color}">
            ${p.rush_label} — ${p.advice}
          </p>
        </div>

        <div class="flex items-center space-x-4 bg-slate-950/80 px-5 py-3 rounded-xl border border-slate-800">
          <div>
            <div class="text-xs text-slate-400 font-medium">Estimated Daily Devotees</div>
            <div class="text-2xl font-black text-amber-300 tracking-tight font-cinzel">
              ${p.estimated_pilgrims.toLocaleString()}
            </div>
          </div>
          <div class="h-8 w-px bg-slate-800"></div>
          <div>
            <div class="text-xs text-slate-400 font-medium">VKC Compartments</div>
            <div class="text-lg font-bold text-white">${p.compartments_filled} / 31</div>
          </div>
        </div>
      </div>

      <!-- Darshan Wait Times Grid -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        
        <!-- Sarva Darshan -->
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2 relative overflow-hidden">
          <div class="absolute top-0 right-0 w-24 h-24 bg-amber-500/5 rounded-full blur-2xl"></div>
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Sarva Darshan (Free/SSD)</span>
            <span class="text-[10px] bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded">Vaikuntam Complex</span>
          </div>
          <div class="text-2xl font-black" style="color: ${p.rush_color}">
            ${p.sarva_darshan_wait_range}
          </div>
          <p class="text-xs text-slate-400">Expected waiting time inside compartments before reaching Srivari sanctum.</p>
        </div>

        <!-- Special Entry Darshan (₹300) -->
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2 relative overflow-hidden">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Special Entry (₹300)</span>
            <span class="text-[10px] bg-emerald-500/20 text-emerald-300 px-1.5 py-0.5 rounded">Online Quota</span>
          </div>
          <div class="text-2xl font-black text-emerald-400">
            ${p.sed_wait_range}
          </div>
          <p class="text-xs text-slate-400">Direct entry corridor via Krishna Teja Rest House bypassing general compartments.</p>
        </div>

        <!-- Divya Darshan -->
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2 relative overflow-hidden">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Divya Darshan (Pedestrians)</span>
            <span class="text-[10px] bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded">Alipiri / Srivari Mettu</span>
          </div>
          <div class="text-2xl font-black text-amber-300">
            ~${p.divya_darshan_wait_hours} Hours
          </div>
          <p class="text-xs text-slate-400">Pedestrian devotees trekking steps with issued biometric footpath tokens.</p>
        </div>

      </div>

      <!-- Secondary Metrics -->
      <div class="grid grid-cols-3 gap-3 text-center bg-slate-950/60 p-3 rounded-xl border border-slate-800/80 text-xs">
        <div>
          <span class="text-slate-400 block">Est. Srivari Hundi</span>
          <strong class="text-white text-sm">₹ ${p.est_hundi_crores} Crores</strong>
        </div>
        <div class="border-x border-slate-800">
          <span class="text-slate-400 block">Kalyanakatta Tonsures</span>
          <strong class="text-white text-sm">~${p.est_tonsures.toLocaleString()}</strong>
        </div>
        <div>
          <span class="text-slate-400 block">Laddus Distributed</span>
          <strong class="text-white text-sm">~${p.est_laddus.toLocaleString()}</strong>
        </div>
      </div>
    </div>

    <!-- Contributing Factors & Tactical Advice -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      
      <!-- Factors -->
      <div class="lg:col-span-2 bg-[#111827] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
        <div>
          <h3 class="font-cinzel font-bold text-amber-300 text-base">Key Demand Factors for this Date</h3>
          <p class="text-xs text-slate-400">Why the model predicts this specific crowd volume</p>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          ${factorsHtml}
        </div>
      </div>

      <!-- Tactical Advice -->
      <div class="bg-[#111827] border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
        <div>
          <h3 class="font-cinzel font-bold text-amber-300 text-base">Devotee Action Plan</h3>
          <p class="text-xs text-slate-400">Tactical queuing guidelines</p>
        </div>

        <div class="space-y-3 text-xs">
          <div class="bg-slate-900 p-3 rounded-xl border border-slate-800 space-y-1">
            <span class="text-slate-400 font-medium block">Recommended Sarva Darshan Queue Entry:</span>
            <strong class="text-amber-300">${p.recommendations.best_sarva_entry}</strong>
          </div>

          <div class="bg-slate-900 p-3 rounded-xl border border-slate-800 space-y-1">
            <span class="text-slate-400 font-medium block">Recommended SED (₹300) Entry Slot:</span>
            <strong class="text-emerald-400">${p.recommendations.best_sed_entry}</strong>
          </div>

          <ul class="space-y-2 pt-1">
            ${tipsHtml}
          </ul>
        </div>
      </div>

    </div>
  `;

  if (window.lucide) lucide.createIcons();
}

// -------------------------------------------------------------
// TRIP PLANNER (BEST VISIT WINDOW)
// -------------------------------------------------------------
async function runTripOptimizer() {
  const start = document.getElementById("opt-start-date").value;
  const end = document.getElementById("opt-end-date").value;
  const ticket = document.getElementById("opt-darshan-type").value;
  const container = document.getElementById("optimizer-results-container");

  container.innerHTML = `
    <div class="text-center py-12 text-slate-500">
      <i data-lucide="loader-2" class="w-8 h-8 animate-spin mx-auto text-amber-400 mb-2"></i>
      <p>Ranking best low-crowd days between ${start} and ${end}...</p>
    </div>
  `;
  if (window.lucide) lucide.createIcons();

  try {
    const res = await fetch(`/api/recommend?start=${start}&end=${end}&ticket=${ticket}`);
    const data = await res.json();
    renderOptimizerResults(data);
  } catch (err) {
    container.innerHTML = `<div class="text-rose-400 text-center py-6">Failed to compute recommendations: ${err.message}</div>`;
  }
}

function renderOptimizerResults(data) {
  const container = document.getElementById("optimizer-results-container");
  const list = data.recommendations;

  if (!list || list.length === 0) {
    container.innerHTML = `<div class="text-slate-400 text-center py-8">No dates found in the specified range.</div>`;
    return;
  }

  const cardsHtml = list.map((item, idx) => {
    const isTop = idx === 0;
    const topBadge = isTop ? `<span class="bg-amber-500 text-slate-950 text-[10px] font-black px-2 py-0.5 rounded-full uppercase">#1 Best Choice</span>` : `<span class="text-xs text-slate-400 font-bold">Rank #${idx + 1}</span>`;

    return `
      <div class="bg-[#111827] border ${isTop ? 'border-amber-500/60 shadow-amber-500/10' : 'border-slate-800'} rounded-2xl p-5 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4 transition hover:border-slate-700">
        
        <div class="space-y-1.5">
          <div class="flex items-center space-x-2.5">
            ${topBadge}
            <span class="text-xs px-2 py-0.5 rounded font-bold uppercase ${item.rush_level === 'LOW' ? 'badge-low' : 'badge-moderate'}">${item.rush_level} RUSH</span>
            <span class="text-xs text-slate-400">${item.tithi}</span>
          </div>
          <h4 class="text-lg font-bold font-cinzel text-white">${item.date} (${item.day_name})</h4>
          <p class="text-xs text-slate-400">${item.advice}</p>
        </div>

        <div class="flex items-center space-x-4 bg-slate-900 px-4 py-2.5 rounded-xl border border-slate-800">
          <div>
            <span class="text-[10px] text-slate-400 block uppercase">Sarva Wait</span>
            <strong class="text-base font-bold text-emerald-400">${item.sarva_darshan_wait_hours} hrs</strong>
          </div>
          <div class="h-6 w-px bg-slate-800"></div>
          <div>
            <span class="text-[10px] text-slate-400 block uppercase">SED ₹300 Wait</span>
            <strong class="text-base font-bold text-amber-300">${item.sed_wait_hours} hrs</strong>
          </div>
          ${item.hours_saved_vs_peak > 0 ? `
            <div class="h-6 w-px bg-slate-800"></div>
            <div>
              <span class="text-[10px] text-emerald-400 font-semibold block uppercase">Time Saved</span>
              <strong class="text-xs font-bold text-emerald-300 bg-emerald-500/20 px-2 py-0.5 rounded border border-emerald-500/30">
                -${item.hours_saved_vs_peak} hrs
              </strong>
            </div>
          ` : ''}
        </div>

        <button onclick="inspectDateInDeepDive('${item.date}')" class="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition flex-shrink-0">
          View Date Details
        </button>

      </div>
    `;
  }).join("");

  container.innerHTML = `
    <div class="space-y-3">
      <div class="flex items-center justify-between text-xs text-slate-400 px-1">
        <span>Found ${list.length} low-crowd days between ${data.start_date} and ${data.end_date}</span>
        <span>Ranked by minimum queue delay</span>
      </div>
      ${cardsHtml}
    </div>
  `;

  if (window.lucide) lucide.createIcons();
}

// -------------------------------------------------------------
// TRENDS & INSIGHTS
// -------------------------------------------------------------
async function loadInsights() {
  try {
    const res = await fetch("/api/insights");
    const data = await res.json();

    // 1. Day of Week Chart
    const dowContainer = document.getElementById("dow-chart-container");
    if (dowContainer && data.dow_distribution) {
      dowContainer.innerHTML = data.dow_distribution.map(d => {
        const pct = (d.avg_pilgrims / 90000) * 100;
        const barColor = d.avg_pilgrims > 80000 ? 'bg-rose-500' : (d.avg_pilgrims > 65000 ? 'bg-amber-500' : 'bg-emerald-500');
        return `
          <div class="text-xs space-y-1">
            <div class="flex justify-between text-slate-300">
              <span class="font-medium">${d.day} <span class="text-slate-500">(${d.rush_tier})</span></span>
              <span class="font-bold">${formatK(d.avg_pilgrims)} devotees • ~${d.wait_hours}h wait</span>
            </div>
            <div class="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
              <div class="h-full ${barColor} rounded-full" style="width: ${pct}%"></div>
            </div>
          </div>
        `;
      }).join("");
    }

    // 2. Monthly Seasonality
    const monthContainer = document.getElementById("monthly-chart-container");
    if (monthContainer && data.monthly_seasonality) {
      monthContainer.innerHTML = data.monthly_seasonality.map(m => {
        const isHigh = m.index >= 1.25;
        const isLow = m.index <= 0.90;
        const badgeBg = isHigh ? 'bg-rose-950/40 border-rose-800/40 text-rose-300' : (isLow ? 'bg-emerald-950/40 border-emerald-800/40 text-emerald-300' : 'bg-slate-900 border-slate-800 text-slate-300');

        return `
          <div class="p-2.5 rounded-xl border ${badgeBg} space-y-1">
            <div class="flex justify-between items-center">
              <span class="font-bold text-slate-200">${m.name}</span>
              <span class="font-mono font-bold">${m.index}x</span>
            </div>
            <p class="text-[10px] text-slate-400 truncate" title="${m.surge_event}">${m.surge_event}</p>
          </div>
        `;
      }).join("");
    }

    // 3. Feature Importance & Model Metrics
    const featContainer = document.getElementById("feature-importance-container");
    const metricsPill = document.getElementById("model-metrics-pill");

    if (data.model_weights && data.model_weights.feature_importance_pct) {
      const imp = data.model_weights.feature_importance_pct;
      featContainer.innerHTML = Object.entries(imp).map(([key, val]) => `
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-3 space-y-1.5">
          <div class="flex justify-between items-center">
            <span class="font-semibold text-slate-300 capitalize">${formatFeatureName(key)}</span>
            <span class="font-bold text-amber-400">${val}%</span>
          </div>
          <div class="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
            <div class="h-full bg-amber-500 rounded-full" style="width: ${Math.min(100, val * 4)}%"></div>
          </div>
        </div>
      `).join("");

      if (metricsPill && data.model_weights.pilgrims_model) {
        const pm = data.model_weights.pilgrims_model;
        metricsPill.innerHTML = `Model Accuracy: <span class="text-amber-400 font-bold">MAE ±${formatK(pm.mae)}</span> | <span class="text-slate-300">R² = ${pm.r2}</span>`;
      }
    }
  } catch (err) {
    console.warn("Could not load insights:", err);
  }
}

// -------------------------------------------------------------
// HELPER UTILITIES
// -------------------------------------------------------------
function formatDate(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function formatK(num) {
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + "k";
  }
  return String(num);
}

function formatFeatureName(name) {
  return name.replace(/^is_/, "").replace(/_/g, " ");
}
