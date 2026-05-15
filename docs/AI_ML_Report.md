# AI/ML Report: Job Market Demand Forecasting System

## 1. Introduction

This report documents the machine learning pipeline for the BDA Job Market Demand Forecasting System — a full-stack platform that forecasts tech skill demand and job listing volumes from historical job posting data. The system ingests real-world job market datasets (primarily Jobstreet, 69K rows, Malaysia, Mar 2023–May 2025, 53 tracked skills), applies time series forecasting, and serves predictions through a REST API to a React frontend.

The core ML challenge: forecasting monthly demand for 50+ tech skills over a 32-month horizon (May 2025 – Dec 2027) using short, sparse, noisy time series with collection artifacts (mass-scraping spikes).

## 2. Objective & Goal

**Objective:** Build an accurate, interpretable, and production-stable forecasting system that predicts monthly demand for individual tech skills and total job listing counts.

**Goals:**
- Forecast 53 tech skills' monthly demand for 32 months ahead
- Forecast aggregate monthly job listing counts for 32 months ahead
- Provide 95% confidence intervals for all predictions
- Serve forecasts via API in <50ms (pre-computed at ETL/training time)
- Handle data quality issues: sparse series, collection spikes, and short history

## 3. Data Selection

### Primary Dataset: Jobstreet
- **Source:** Jobstreet job postings (Kaggle)
- **Size:** 69,000 rows
- **Region:** Malaysia
- **Date Range:** March 2023 – May 2025
- **Skills Tracked:** 53 tech skills extracted via regex from job descriptions
- **Format:** CSV with columns including job_title, description, posted_date, company, location, salary, work_type

### Secondary Dataset: Synthetic Fallback
- **Source:** `generate_synthetic_data.py` (seed=42 for reproducibility)
- **Size:** 1,152 rows (32 skills × 36 months)
- **Date Range:** January 2022 – December 2024
- **Structure:** Each skill gets random base demand (100–500), trend type (growing/stable/declining), sinusoidal seasonal component (amplitude=80, peak Q3/Q4), and Gaussian noise (σ=30)
- **Used when:** Real data fails validation (<6 data points or <12-month span)

### Data Validation (ETL)
- `etl_kaggle.py`: Chunk-based processing (100K rows/chunk) of large CSV; regex extraction of 30 predefined tech skills; MIN_DATA_POINTS=3
- `etl_synthetic.py`: Flexible column detection by keyword matching; MIN_DATA_POINTS=6, MIN_DATE_SPAN_MONTHS=12; falls back to synthetic CSV if real data fails validation

## 4. Exploratory Data Analysis (EDA)

### Analyses Performed (eda_skill_demand.ipynb)
- **Data overview:** Shape, column types, date range, unique skill/period counts, missing value audit
- **Top-skill ranking:** Mean/max/min/std/count per skill, sorted by mean demand (top 15 for deeper analysis)
- **Time series characterization:** Per-skill linear trend (slope, R² via scipy.stats.linregress), volatility (std/mean CV), outlier count (>3σ), series length
- **Trend visualization:** Top-5 skills overlaid with polynomial degree-1 trend lines
- **Volatility analysis:** Horizontal bar chart, color-coded (green <0.3, orange 0.3–0.5, red >0.5); histogram of all demand counts with mean/median reference lines
- **Outlier detection:** IQR method (1.5×IQR fences) per top-15 skill
- **Data completeness:** Periods per skill; flagged skills with <10 months as sparse
- **Seasonality analysis:** Monthly mean/std/count; bar chart with error bars; seasonal strength = (max−min)/mean×100%; peak/trough month identification
- **Summary statistics:** Count of high/medium/low volatility skills, increasing/stable/decreasing trends, outlier totals, data completeness stats, seasonal variation percentage

### Visualizations Generated
| # | Chart | Saved As |
|---|-------|----------|
| 1 | 2×4 line plots: Top 8 skills' demand over time | `eda_top_8_skills.png` |
| 2 | Top 5 skills overlaid with linear trend lines | `eda_trends.png` |
| 3 | Volatility bar chart (color-coded by severity) | `eda_volatility.png` |
| 4 | Demand count histogram with mean/median lines | (same figure as volatility) |
| 5 | Average demand by month-of-year with error bars | `eda_seasonality.png` |

Also: `eda_summary.csv` — tabular summary of top-15 skill statistics

### Key EDA Findings
1. **Demand distribution:** Right-skewed (mean > median), long tail of high-demand observations
2. **Volatility tiers:** High (>0.5 CV), medium (0.3–0.5), low (<0.3) — highly volatile skills need special handling
3. **Outliers present:** IQR-based outlier counts per skill; significant outliers exist
4. **Sparse skills:** Some skills have <10 months of data — recommended for exclusion or special treatment
5. **Seasonality:** Monthly pattern present; seasonal strength varies by skill
6. **Critical spike artifact:** Feb–Jun 2024 — all skills spiked simultaneously due to a mass-scraping burst, not real market signal. This was the single most impactful data quality finding.

## 5. Model Evolution

The forecasting approach evolved through four iterations based on data quality findings and empirical results:

### v1: LSTM (Abandoned)
- **Files:** `forecast_lstm.py`, `forecast_job_listings.py`
- **Architecture:** Sequential Keras — LSTM(32, relu) → Dropout(0.1) → Dense(16, relu) → Dense(1, linear)
- **Job listings LSTM:** Smaller — LSTM(16, relu) → Dropout(0.1) → Dense(8, relu) → Dense(1, linear)
- **Preprocessing:** IQR outlier removal (1.5×IQR), MinMaxScaler to [0,1]
- **Training:** 30 epochs (skills) / 50 epochs (job listings), batch_size=4/2, 20% validation split, Adam(lr=0.001), MSE loss
- **Forecasting:** Autoregressive rollout of 32 steps; confidence intervals = ±1 std/mean ratio
- **Job listings special:** 70/30 blend of LSTM output with 1.5% monthly linear growth; ±15% sinusoidal seasonality factor
- **Why abandoned:**
  - Short, sparse per-skill series make LSTM unstable
  - Autoregressive rollout compounds errors over 32-month horizon
  - No formal evaluation metrics (MAE/RMSE/R²)
  - Confidence intervals too simplistic (±1 std)
  - GPU dependency for minimal gain
  - The hard-coded growth blend in job listings LSTM made the neural net decorative

### v2: Median/IQR Baseline (Transitional)
- **File:** `regenerate_forecasts_median.py`
- **Algorithm:** No model — 60% historical median + 40% recent median (last 3–5 months) blend
- **Trend:** Simple linear slope (first→last), damped by 0.1×
- **Seasonality:** Sinusoidal (±10% amplitude via 0.9 + 0.2·sin(2π·month/12))
- **Hard cap:** Forecasts clipped to [0.7× baseline, 1.3× baseline]
- **Confidence intervals:** Fixed ±15% of forecast value
- **Why transitional:**
  - Deterministic, no training instability
  - No GPU dependency, faster execution
  - But: 0.7–1.3× cap is too restrictive; fixed CI is not data-driven
  - No formal evaluation metrics

### v3: Linear Regression with Spike Exclusion (Current)
- **File:** `retrain_forecasts.py`
- **Model version:** `LinReg_NoSpike_v3`
- **This is the current production model — detailed in Section 6**

### Post-hoc: Forecast Capping
- **File:** `cap_forecasts.py`
- **Algorithm:** SQL UPDATE — caps `predicted_demand` to at most 5× historical max per skill
- **Purpose:** Safety net against runaway predictions from any model version

## 6. Current Model: Linear Regression v3 (LinReg_NoSpike_v3)

### Architecture
- **Model:** `sklearn.linear_model.LinearRegression`
- **Features (3):**
  1. `t` — time offset in months from origin: `(date - origin).days / 30.44`
  2. `sin(2π × month/12)` — annual sinusoidal seasonality (sine component)
  3. `cos(2π × month/12)` — annual sinusoidal seasonality (cosine component)
- **Interpretation:** Linear trend + annual sinusoidal seasonality — simple, interpretable, and appropriate for short series

### Preprocessing
1. Load `skill_demand` table from PostgreSQL via `docker exec postgres psql`
2. Remove spike months (Feb 2024 – Jun 2024) — `SPIKE_MONTHS` hardcoded
3. Train LR on de-spiked data only
4. Floor negative predictions to 0

### Training Pipeline (per skill)
1. Filter to single skill's data
2. Remove spike months (Feb–Jun 2024)
3. Build feature matrix: [t, sin(2π×month/12), cos(2π×month/12)]
4. Fit LinearRegression on cleaned data
5. TimeSeriesSplit cross-validation (3 folds) → compute RMSE, MAE, R²
6. Compute `recent_mean` from last 3 non-spike months
7. Compute anchor offset = `recent_mean - model.predict(recent_dates)`
8. Forecast = `model.predict(X_forecast) + anchor_offset`
9. Clamp to `[recent_mean × 0.5, recent_mean × 2.0]` (anchor clamp ±50%)
10. 95% CI = `1.96 × max(resid_std, recent_mean × 0.10)`

### Why Linear Regression Over LSTM/SARIMA
- **Data too limited for deep learning:** Only ~24 months of usable data per skill after spike removal — insufficient for LSTM
- **Spike contamination makes SARIMA unreliable:** The Feb–Jun 2024 artifact disrupts ARIMA stationarity assumptions
- **Interpretable:** Slope = trend direction, sin/cos = seasonal amplitude — directly explainable
- **Stable:** No training randomness, no autoregressive error compounding
- **Fast:** Instant training, pre-computed forecasts served in ~50ms from DB

### Job Listings Forecast (Special Case)
- Only 8 months of data with a 9-month gap → regression is misleading
- Uses: `recent_mean` of post-gap months as forecast level
- Gentle slope from post-gap period, capped at ±1/month
- CI with 20% minimum width
- CV is informational only (negative R² expected due to data sparsity)

### Forecast Horizon
- 2025-05-01 to 2027-12-01 (32 months)

### Output
- Skill forecasts → TSV file → `docker cp` into PostgreSQL `forecast_results` table (model_version="LinReg_NoSpike_v3")
- Job listings → `job_listings_forecast.json` (historical + predicted arrays with CIs)

## 7. Evaluation

### Cross-Validation Method
- **Method:** `TimeSeriesSplit` (3 folds) — respects temporal ordering, no future data leakage
- **Per-skill metrics:** RMSE, MAE, R²
- **Note:** No saved evaluation metrics files exist in the repository — metrics are printed to console during `retrain_forecasts.py` execution

### Evaluation Challenges
- **Short series:** ~24 usable months per skill after spike removal limits CV fold depth
- **Spike artifact:** Feb–Jun 2024 excluded from training; no ground truth for what "correct" values would be
- **Job listings:** Only 8 data points with 9-month gap → negative R² expected, CV is informational only
- **No held-out test set:** All non-spike data used for both training and CV evaluation

### Comparison Summary

| Model | Approach | Spike Handling | CI Quality | Evaluation | Status |
|-------|----------|---------------|------------|------------|--------|
| LSTM | Neural net, autoregressive | IQR outlier removal (1.5×) | ±1 std/mean (simplistic) | None formal | Abandoned |
| Median Baseline | Blend + damped trend | None | Fixed ±15% | None formal | Transitional |
| **LinReg v3** | **LR + sin/cos + anchor clamp** | **Hard exclusion (Feb–Jun 2024)** | **1.96 × max(resid_std, 10% floor)** | **TimeSeriesSplit CV** | **Current** |

## 8. Results

### Forecast Output Format
**Skill Forecasts** (in `forecast_results` table):
- Columns: skill_name, forecast_date, confidence_lower, confidence_upper, predicted_demand, model_version, region
- 53 skills × 32 months = 1,696 forecast rows
- Model version: "LinReg_NoSpike_v3"

**Job Listings Forecast** (in `job_listings_forecast.json`):
- `historical[]`: 8 data points (Jan 2024 – Apr 2025, with gap Jul 2024 – Feb 2025)
- `predicted[]`: 32 monthly forecasts (May 2025 – Dec 2027) with confidence intervals
- Pattern: Linear ramp from 9 to 40 (+1/month) — reflects the data sparsity forcing a simple trend

### Key Results
- **Anchor clamp mechanism** prevents long-horizon divergence: forecasts bounded to ±50% of recent_mean
- **Post-hoc safety cap** at 5× historical max per skill (via `cap_forecasts.py`)
- **Spike exclusion** removes the Feb–Jun 2024 artifact that would otherwise dominate the trend slope
- **Seasonality capture:** sin/cos features model annual hiring cycles without requiring 24+ months of clean data (unlike SARIMA which needs 2+ seasonal cycles)
- **Pre-computed forecasts:** All predictions stored in PostgreSQL at training time → API queries return in ~50ms

### Serving Architecture
- **FastAPI service** (`backend/ml-service/main.py`, port 5100): Queries `forecast_results` and `job_listings` tables from PostgreSQL
  - `GET /ml/predictions?topN=N&skill=X` — top N skills by avg predicted demand
  - `GET /ml/job-listings-trend` — historical + predicted job listing counts
  - `GET /ml/health` — status check
- **Flask service** (`ml_service.py`, port 5000): Lightweight companion serving `job_listings_forecast.json`
  - `GET /ml/job-listings-trend` — cached JSON
  - `GET /ml/predictions` — stub (returns []; skill forecasts served from DB via FastAPI)

### Limitations
1. **Short data history:** Only ~24 months of clean data limits model complexity
2. **Single region:** Jobstreet data is Malaysia-only; generalizability unknown
3. **No exogenous features:** Model uses only time and seasonality — no economic indicators, policy changes, or market events
4. **Fixed spike exclusion:** Feb–Jun 2024 dates hardcoded; future spikes need manual detection
5. **No automated retraining:** `retrain_forecasts.py` must be run manually
6. **Job listings forecast weak:** 8 data points with gap → simple mean-based forecast, no meaningful seasonality
7. **No held-out test:** All non-spike data used for training + CV; no temporal train/test split for final evaluation

### Future Improvements
- Automated spike detection (statistical instead of hardcoded dates)
- Exogenous features (economic indicators, job market indices)
- Online/incremental retraining pipeline
- More data sources for longer history and cross-regional validation
- Bayesian approaches for better uncertainty quantification
- Ensemble methods combining LR with lightweight models