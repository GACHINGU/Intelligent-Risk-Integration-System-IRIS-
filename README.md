# 🇰🇪 IRIS — Intelligent Risk Integration System

> **Kenya Monetary Policy Risk Intelligence Platform**
> Lead Scientist: Stephen Munene | Policy Analysis Unit
> Simulated educational system — not an official CBK publication

---

## What is IRIS?

IRIS is a live quantitative decision-support system that ingests Kenya's
inflation and interest rate data, runs a full structural model stack,
and produces an automated risk score, policy signals, and executive memoranda —
updated in real time.

It is built on 53 years of Kenya macroeconomic data (1971–2023) and the same
analytical frameworks used by the IMF, World Bank, and top central banks globally.

---

## System Architecture

Trading Economics API
↓
data/ingestion/       ← live data fetch + cache + validation
↓
data/pipeline/        ← clean + merge with historical + feature engineering
↓
models/               ← 8 structural models run in sequence
↓
risk/                 ← IRIS Risk Score (0-100) + classification + signals
↓
intelligence/         ← narrative engine + 3 memo types + wananchi brief
↓
dashboard/            ← Streamlit 8-page live dashboard
↓
scheduler/            ← auto-refresh + alert system

---

## Models

| Model | Purpose |
|-------|---------|
| ADF + KPSS | Stationarity testing |
| Johansen | Cointegration — are rates and inflation leashed together? |
| VECM | Short-run dynamics + long-run error correction |
| IRF | Impulse response — how long does a rate hike take to work? |
| FEVD | Variance decomposition — what % of inflation does CBK control? |
| GARCH(1,1) | Time-varying inflation volatility |
| Markov Regime-Switching | High vs low inflation era identification |
| Correlations | Pearson, Spearman, rolling, cross-correlation, lead-lag |

---

## IRIS Risk Score

A single composite number from 0 to 100:

| Score | Status | Meaning |
|-------|--------|---------|
| 0–25  | 🟢 STABLE   | Inflation within target, low volatility |
| 26–50 | 🟡 MODERATE | Above target or rising volatility |
| 51–75 | 🟠 DANGER   | High volatility, regime shift probable |
| 76–100| 🔴 CRITICAL | Crisis regime, immediate action required |

---

## Dashboard Pages

| Page | Content |
|------|---------|
| 🏠 Home | IRIS Score gauge, key metrics, component breakdown, signals |
| 📡 Live Data | Current readings, historical series, decade summary |
| 🎯 Risk Gauge | Full risk classification, conditions checklist, warnings |
| 🤖 Models | All 8 model outputs with charts and plain-English interpretation |
| 📊 Correlations | Static, rolling, cross-correlation, Fisher Effect |
| 📈 Statistics | Every number the system computes |
| 📋 Memorandum | Auto-generated memos for Governor, MPC, and Wananchi (PDF export) |
| 📚 History | Historical context, era analysis, similar historical years |

---

## Intelligence Layer

IRIS auto-generates three memo types on every run:

- **Governor Memo** — technical, formal, strategic
- **MPC Memo** — operational, recommendation-driven, rate signal
- **Wananchi Brief** — plain English, Swahili phrases, Kenyan examples

All memos are exportable as formatted PDFs.

---

## Getting Started

### 1. Clone and install

```bash
git clone https://github.com/yourusername/IRIS.git
cd IRIS
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Add your Trading Economics API key to .env
```

### 3. Add historical data

Place your CSV files in `data/historical/`:
- `kenya_interest_rates.csv` — columns: year, interest_rate
- `kenya_inflation_data.csv` — columns: year, inflation

### 4. Run

```bash
streamlit run app.py
```

### 5. Run tests

```bash
python -m pytest tests/ -v
```

---

## Tech Stack

Python 3.10+
├── streamlit       — dashboard
├── plotly          — interactive charts
├── pandas          — data manipulation
├── statsmodels     — VECM, GARCH, Johansen, Markov
├── arch            — GARCH(1,1) volatility
├── scipy           — correlations, statistics
├── reportlab       — PDF memo export
├── python-dotenv   — environment config
└── requests        — Trading Economics API

---

## Key Findings (from the historical analysis)

- Kenya's average inflation (1971–2023): **9.7%** vs average interest rate: **6.2%**
- Real interest rate was negative in the majority of years — **savers were losing value**
- Only **~14%** of Kenya's inflation is within the CBK's direct control (FEVD result)
- **~86%** is supply-driven: food, fuel, drought, exchange rate
- Rate hikes take **2–5 years** to reduce inflation (IRF result)
- Kenya has cycled through four distinct monetary regimes since independence

---

## Disclaimer

This is a simulated system built for educational and analytical purposes.
It is not an official publication of the Central Bank of Kenya,
the Monetary Policy Committee, the National Treasury,
or any affiliated institution.

All analysis is based on publicly available historical data.

---

*Asante kwa kusoma. Thank you for reading.*

**Stephen Munene** | Lead Scientist, Policy Analysis Unit
*IRIS v1.0 — November 2024*