# 🛕 Tirumala Tirupati Darshanam Daily Crowd Predictor

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests Passing](https://img.shields.io/badge/tests-15%20passed-success.svg)]()

An intelligent machine learning and domain-informed forecasting system to predict daily pilgrim footfall, waiting times (**Sarva Darshan & Special Entry ₹300**), and **Vaikuntam Queue Complex (VKC)** compartment occupancy for the Sri Venkateswara Temple at **Tirumala Tirupati Devasthanams (TTD)**.

---

## 🌟 Key Features

- **Panchangam & Hindu Lunar Calendar Engine**:
  - Computes lunar tithis (*Ekadashi, Pournami, Amavasya, Dwadasi*).
  - Automatically identifies **Purattasi Masam** and flags **Purattasi Saturdays** (which trigger massive footfall surges from Tamil Nadu).
  - Detects **Karthika Masam**, **Brahmotsavams** (*Salakatla* & *Navaratri* with Garuda Seva peaks), **Vaikunta Dwara Darshanam** (10-day peak), **Rathasapthami**, and **Eclipses** (*Grahanam* temple closures).
- **Multi-State Holiday & Academic Matrix**:
  - Models gazetted and bank holidays across primary pilgrim catchment states: **Andhra Pradesh, Telangana, Tamil Nadu, and Karnataka**.
  - Detects **3-day and 4-day extended long weekends**.
  - Accounts for academic calendars: **School Exam Season** (*Feb 15 - April 10: Leanest period of the year*) vs. **Summer Vacation** (*Mid-April to Early June: Maximum sustained crowd*).
- **Queue Dynamics & Throughput Physics**:
  - Accurately models the sanctum sanctorum (*Garbhagriha*) throughput constraint (~3,500 – 4,000 pilgrims/hour).
  - Calculates **VKC compartment occupancy** (0 to 31+ compartments inside Vaikuntam Queue Complex 1 & 2).
  - Predicts non-linear waiting times:
    - **Sarva Darshan (Free / SSD)**: 4 to 36+ hours.
    - **Special Entry Darshan (SED ₹300)**: 1.5 to 7.5 hours.
    - **Divya Darshan (Footpath Trekking)**: 3.5 to 16 hours.
  - Accounts for **multi-day queue spillover** (e.g. Saturday night overflow impacting Sunday & Monday).
- **Interactive Web Dashboard**:
  - **Monthly Heatmap Calendar**: Color-coded days (🟢 Low, 🟡 Moderate, 🟠 High, 🔴 Peak) with single-click day inspections.
  - **Single-Date Deep Dive**: Complete breakdown of why rush is high/low with tactical devotee advice.
  - **Trip Optimizer / Best Window Finder**: Ranks the top least-crowded days within any travel window and calculates waiting hours saved.
  - **Trends & Insights**: Visual day-of-week averages, 12-month seasonality curve, and feature importances.
  - **Pilgrim Survival Guide**: Rules on dress codes, SSD token counter locations, luggage lockers, and free Annaprasadam.
- **Interactive CLI (`predict_cli.py`)**:
  - Query single dates, print monthly calendars, or find best trip windows directly from your terminal.
- **Zero External Dependencies Required**:
  - Pure Python standard library implementation for all core features, regression math, API, and web serving. Optional support for `scikit-learn`, `pandas`, `numpy`.

---

## 🚀 Quick Start

### 1. Launch the Web Dashboard
```bash
python3 run_app.py
```
Open your browser and navigate to: **[http://localhost:8000](http://localhost:8000)**

### 2. Use the Command-Line Interface (CLI)

```bash
# Forecast a specific date (e.g. Brahmotsavam Garuda Seva)
python3 predict_cli.py --date 2026-10-06

# View full monthly calendar table for October 2026
python3 predict_cli.py --month 2026-10

# Find the best low-crowd days between Nov 1 and Nov 30, 2026
python3 predict_cli.py --recommend --start 2026-11-01 --end 2026-11-30

# Today's live queue status
python3 predict_cli.py --live

# Retrain regression models on calibrated historical data
python3 predict_cli.py --train
```

### 3. Run Automated Tests
```bash
python3 -m unittest discover -s tests
```

---

## 📊 Rush Tiers & Waiting Time Thresholds

| Rush Level | Daily Pilgrims | Sarva Darshan Wait | SED (₹300) Wait | Compartments Filled | Typical Scenario |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 🟢 **LOW** | < 60,000 | **4 – 8 hours** | **1.5 – 2.5 hours** | 0 – 10 compartments | Tuesday/Wednesday in School Exam Season (Feb–Mar) |
| 🟡 **MODERATE** | 60,000 – 72,000 | **8 – 14 hours** | **2.5 – 3.5 hours** | 10 – 20 compartments | Standard non-holiday Thursday or Monday |
| 🟠 **HIGH** | 72,000 – 84,000 | **14 – 22 hours** | **3.5 – 5.0 hours** | 20 – 30 compartments | Standard non-festival Saturday or Friday |
| 🔴 **PEAK** | > 84,000 | **22 – 36+ hours** | **5.0 – 7.5+ hours** | 31+ (Outside lines) | Brahmotsavam, Purattasi Saturdays, Vaikunta Ekadashi |

---

## 📡 REST API Endpoints

The embedded server exposes clean JSON endpoints:

| Endpoint | Method | Parameters | Description |
| :--- | :--- | :--- | :--- |
| `/api/predict` | `GET` | `date=YYYY-MM-DD` | Full deep-dive prediction, wait times, factors, and advice |
| `/api/calendar` | `GET` | `year=YYYY&month=MM` | 30/31-day rush forecast matrix for calendar heatmap |
| `/api/recommend` | `GET` | `start=YYYY-MM-DD&end=YYYY-MM-DD&ticket=all\|sed` | Optimal visit window finder ranking lowest crowd days |
| `/api/live-status` | `GET` | *none* | Today's estimated vs yesterday's reported bulletin snapshot |
| `/api/insights` | `GET` | *none* | Feature importance, DOW averages, and monthly seasonality |

---

## 🏗️ Project Structure

```
Tirumala Tirupati Rush Predictor/
├── data/
│   ├── historical_darshan_data.csv    # Calibrated multi-year dataset (2018-2026)
│   ├── festivals_calendar.json        # Hindu festival schedules & eclipse dates
│   ├── ttd_benchmarks.json            # Sanctum throughput & compartment limits
│   └── model_weights.json             # Serialized regression weights & feature importance
├── src/
│   ├── core/
│   │   ├── panchangam_engine.py       # Lunar tithi, Purattasi & festival engine
│   │   ├── holiday_matrix.py          # Multi-state holiday matrix & academic seasons
│   │   └── queue_dynamics.py          # VKC compartment math & wait-time transfer functions
│   ├── data_pipeline/
│   │   ├── dataset_generator.py       # Multi-year historical data synthesizer
│   │   └── bulletin_scraper.py        # TTD daily press release bulletin parser
│   ├── models/
│   │   ├── predictor.py               # Unified forecasting engine & trip optimizer
│   │   └── ml_trainer.py              # Regression training pipeline (MAE, RMSE, R²)
│   ├── api/
│   │   └── app.py                     # HTTP server & REST API handler
│   └── web/
│       ├── static/
│       │   ├── app.js                 # Frontend interactive logic
│       │   └── style.css              # Custom styling & animations
│       └── index.html                 # Temple-themed responsive dashboard
├── tests/
│   ├── test_panchangam.py             # Tests for lunar phases and Purattasi detection
│   ├── test_holiday_matrix.py         # Tests for public holidays and vacation cycles
│   ├── test_queue_dynamics.py         # Tests for compartment bounds & wait times
│   └── test_api.py                    # Tests for prediction & recommendation schemas
├── predict_cli.py                     # Command-line interface
├── run_app.py                         # Web application launcher
├── requirements.txt                   # Optional data science dependencies
└── README.md                          # Documentation
```

---

## 💡 Practical Devotee Tips Included in App

1. **Golden Days**: Tuesdays and Wednesdays during non-festival months consistently see the lowest waiting times (under 6 hours for Sarva Darshan).
2. **Purattasi Saturday Warning**: Avoid visiting without prior tickets on Purattasi Saturdays (mid-Sept to mid-Oct) as thousands trek the Alipiri footpath, causing waiting times to exceed 30+ hours.
3. **Food & Facilities**: Hot Annaprasadam, Sambhar rice, curd rice, infant milk, and drinking water are served continuously by TTD Srivari Sevaks inside all Vaikuntam compartments.
4. **SSD Token Hubs**: Free Slotted Sarva Darshan tokens are issued early morning in Tirupati at **Bhudevi Complex (Alipiri)**, **Srinivasam Complex (Bus Stand)**, and **Govindaraja Choultries (Railway Station)**. Aadhaar card is mandatory.

---

## 📜 License
MIT License. Dedicated to devotees of Lord Sri Venkateswara Swamy.
