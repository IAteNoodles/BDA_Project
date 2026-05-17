VISVESVARAYA TECHNOLOGICAL UNIVERSITY
"Jnana Sangama", Belagavi-590 018
Mini Project Report 
BDS602 – Artificial Intelligence & Machine Learning

Job Market Demand Forecasting System

Submitted by
Abhijit Kumar Singh    1AY23CD001

Under the Guidance of
Dr. Vijayashekhar S S
Professor & Head
Department of CSE(DS)

DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING (DATA SCIENCE)  
ACHARYA INSTITUTE OF TECHNOLOGY
(AFFILIATED TO VISVESVARAYA TECHNOLOGICAL UNIVERSITY, BELAGAVI)
Acharya Dr. Sarvepalli Radhakrishnan Road, Soldevanahalli, Bengaluru - 560107

2025-2026

ABSTRACT

This project presents a Job Market Demand Forecasting System — a machine learning platform designed to forecast monthly tech skill demand and job listing volumes from historical job posting data. The system ingests a real-world dataset of 69,000 job postings sourced from Jobstreet (Malaysia, March 2023 – May 2025), tracks 53 tech skills extracted via regex from job descriptions, and applies a Linear Regression model enriched with sinusoidal seasonality features to produce 32-month ahead forecasts (May 2025 – December 2027) with 95% confidence intervals. A key data quality challenge — a mass-scraping spike in February–June 2024 — was addressed through explicit exclusion and an anchor-clamp mechanism to ensure stable, production-ready predictions. The trained model is stored in a PostgreSQL database and served via a FastAPI REST endpoint, delivering forecasts in under 50 milliseconds. The outcome is an interpretable, stable, and deployment-ready forecasting pipeline that converts noisy, sparse job market time series data into actionable skill demand predictions.

INTRODUCTION

Background of the Project

The technology job market evolves rapidly, with demand for specific programming languages, frameworks, and tools shifting from month to month. Employers, job seekers, training institutes, and policy makers all benefit from reliable forecasts of which technical skills will be in demand over the coming months and years. However, publicly available job market datasets are typically short, sparse, and noisy — making classical forecasting approaches like ARIMA or deep learning models such as LSTM challenging to apply without significant preprocessing and model adaptation.

Problem Statement

Historical job posting data, while rich in content, presents several forecasting challenges: short time horizons (approximately 24 months of usable data per skill), data collection artifacts (mass-scraping events that create artificial demand spikes), sparse per-skill observations, and the need for interpretable predictions that can be trusted by non-technical stakeholders. Existing solutions either require large datasets for deep learning models or produce overly simplistic trend extrapolations that ignore seasonal patterns in hiring cycles. A robust, interpretable, and production-stable forecasting model is needed that handles these constraints while providing statistically sound confidence intervals.

Objectives of the Project

• To forecast monthly demand for 53 tracked tech skills over a 32-month horizon.
• To forecast aggregate monthly job listing counts over the same horizon.
• To provide 95% confidence intervals for all skill-level predictions.
• To handle data quality issues including scraping spikes, sparse series, and short history.
• To serve forecasts via a REST API with sub-50ms response time using pre-computed results.
• To apply an interpretable linear regression model with sinusoidal seasonality features.
• To evaluate the model rigorously using time-series-aware cross-validation.
• To build a post-hoc safety mechanism that prevents runaway long-horizon predictions.

Scope of the Project

The project focuses on forecasting tech skill demand using the Jobstreet job postings dataset (Malaysia). It tracks 53 tech skills across a 26-month date range, applies Linear Regression with sine/cosine seasonality features, and produces pre-computed forecasts stored in PostgreSQL. Predictions are served through a FastAPI backend to a React frontend. A secondary synthetic dataset is used as a fallback for skills with insufficient real data. The scope includes full pipeline coverage: ETL, exploratory data analysis, model training and evaluation, forecast generation, API serving, and safety capping.

LITERATURE SURVEY / EXISTING SYSTEM

Existing Methods

Prior approaches to job market forecasting have included:
• ARIMA and SARIMA time series models — classical methods that assume stationarity and require at least 2 seasonal cycles of data.
• LSTM-based neural network forecasters — deep learning models that require large, clean datasets and are prone to autoregressive error compounding over long horizons.
• Simple linear trend extrapolation — baseline approaches that ignore seasonality and produce unreliable long-range predictions.
• Median-blending heuristics — deterministic blends of historical and recent medians with hard forecast caps, lacking data-driven confidence intervals.
• Transformer-based models for NLP-driven job market analysis — applied to job description classification rather than demand forecasting.
• Economic indicator-based regression — models that incorporate macroeconomic variables but require external data sources not always available.

Limitations of the Existing System

• SARIMA models require stationarity and at least 24+ months of clean seasonal data per series — both conditions violated here due to the scraping spike.
• LSTM and other deep learning models are unstable on short (sub-30 point) time series and compound errors exponentially over 32-step autoregressive rollouts.
• Simple median or mean baselines produce deterministic forecasts with no statistical confidence bounds.
• Hard forecast caps (e.g., ±30% of baseline) are not data-driven and overly restrict legitimate trend signals.
• No existing lightweight system combines spike exclusion, anchor-based clamping, and sinusoidal seasonality in a single interpretable model for job market data.
• Most existing tools do not provide sub-50ms API serving of pre-computed forecasts for production deployment.

PROPOSED SYSTEM / METHODOLOGY

Proposed Solution

The proposed system is a Linear Regression-based forecasting pipeline that ingests historical job posting data, removes data quality artifacts, and produces 32-month demand forecasts for 53 tech skills. The model uses three features: a linear time index, a sine component, and a cosine component of the annual seasonal cycle. An anchor-clamp mechanism prevents long-horizon divergence by bounding forecasts relative to the recent mean demand. Forecasts are pre-computed and stored in PostgreSQL, served via FastAPI with sub-50ms latency.

Step-by-Step Methodology

1. Data Ingestion: Load Jobstreet job postings CSV (69K rows) via chunk-based ETL (100K rows/chunk). Extract 53 tech skills using regex patterns on job descriptions.
2. Data Validation: Apply MIN_DATA_POINTS and MIN_DATE_SPAN checks. Skills with fewer than 6 usable data points or less than 12 months of coverage are excluded from modelling.
3. Spike Detection & Removal: Identify the February–June 2024 mass-scraping burst (all skills spiked simultaneously). Hard-exclude these months from training data (SPIKE_MONTHS constant).
4. Feature Engineering: Construct three features per data point: t (time offset in months), sin(2π × month/12), and cos(2π × month/12). These capture linear trend and annual seasonality.
5. Model Training: Fit sklearn LinearRegression on de-spiked per-skill time series. Compute residual standard deviation for confidence interval estimation.
6. Anchor Clamping: Compute recent_mean from the last 3 non-spike months. Apply anchor offset and clamp forecasts to [0.5×recent_mean, 2.0×recent_mean] to prevent divergence.
7. Cross-Validation: Apply TimeSeriesSplit (3 folds) to compute RMSE, MAE, and R² per skill while respecting temporal ordering.
8. Confidence Intervals: 95% CI = 1.96 × max(residual_std, 10% of recent_mean) — data-driven with a floor to avoid degenerate intervals.
9. Safety Capping: Post-hoc SQL UPDATE caps any predicted_demand to at most 5× the historical maximum per skill.
10. Storage & Serving: Forecasts stored in PostgreSQL forecast_results table. Served via FastAPI (port 5100) and Flask (port 5000) endpoints.

TOOLS AND TECHNOLOGIES USED

Software / Tools
• Visual Studio Code — primary code editor for development
• PostgreSQL — relational database for storing skill demand data and forecast results
• Docker — containerization of PostgreSQL and API services
• Git & GitHub — version control and code repository
• FastAPI — high-performance REST API framework for serving forecast predictions
• Flask — lightweight companion API for serving JSON forecast artifacts
• React — frontend framework for the interactive dashboard

Programming Language
• Python 3.10+ — primary language for ETL, EDA, model training, and API services
• JavaScript (Node.js / React) — frontend and optional scripting

Platform / IDE
• Visual Studio Code on Linux – integrated development environment
• Docker Desktop / Docker Compose — multi-service orchestration (PostgreSQL + API)
• Kaggle — source platform for the Jobstreet dataset

LIBRARIES AND PACKAGES USED

Library          | Version | Purpose
---|---|---
scikit-learn     | 1.3+    | LinearRegression model, TimeSeriesSplit cross-validation, RMSE/MAE/R² metrics
Pandas           | 2.0+    | Data manipulation, time series aggregation, ETL processing, DataFrame operations
NumPy            | 1.24+   | Numerical operations, sin/cos feature computation, array handling
Matplotlib       | 3.7+    | EDA visualizations: trend plots, volatility charts, demand histograms
Seaborn          | 0.12+   | Statistical visualization for EDA seasonality and distribution charts
FastAPI          | 0.104+  | REST API serving pre-computed forecasts from PostgreSQL with sub-50ms latency
Flask            | 3.0+    | Lightweight companion service serving job_listings_forecast.json
psycopg2         | 2.9+    | PostgreSQL connection and query execution for ETL and forecast storage
SQLAlchemy       | 2.0+    | ORM layer for database interactions in ETL scripts
scipy            | 1.11+   | scipy.stats.linregress for per-skill linear trend characterization in EDA
uvicorn          | 0.24+   | ASGI server for running the FastAPI service in production

DATASET DETAILS

Source of Dataset

The primary dataset is sourced from Kaggle (Jobstreet job postings, Malaysia). It contains 69,000 rows of job listing records collected between March 2023 and May 2025, providing a 26-month window of tech job market activity across Malaysia.

Primary Dataset: Jobstreet

• Source: Jobstreet job postings via Kaggle
• Size: 69,000 rows
• Region: Malaysia
• Date Range: March 2023 – May 2025
• Skills Tracked: 53 tech skills extracted via regex from job description text
• Format: CSV with columns — job_title, description, posted_date, company, location, salary, work_type
• Validation Gates: MIN_DATA_POINTS=6 and MIN_DATE_SPAN_MONTHS=12 enforced; skills failing these thresholds are excluded from the forecast pipeline.
• Floor Clipping: All negative model predictions floored to 0 before storage.
• Post-hoc Safety Cap: SQL UPDATE caps predicted_demand to 5× historical maximum per skill via cap_forecasts.py.

Secondary Dataset: Synthetic Fallback

• Source: generate_synthetic_data.py (seed=42 for reproducibility)
• Size: 1,152 rows (32 skills × 36 months)
• Date Range: January 2022 – December 2024
• Structure: Each skill gets random base demand (100–500), trend type (growing/stable/declining), sinusoidal seasonal component (amplitude=80, peak Q3/Q4), and Gaussian noise (σ=30)
• Used when: Real data fails validation (<6 data points or <12-month span)

DATA PREPROCESSING TECHNIQUES USED

1. Regex-based Skill Extraction
   • Extract 30+ tech skill keywords from job description text using compiled regex patterns
   • Handle case-insensitive matching (Python, python, PYTHON all treated as same skill)
   • Canonical skill names normalized to predefined list (e.g., "Kubernetes" → "K8s")

2. Timestamp Parsing
   • Parse posted_date column using pandas to_datetime with infer_datetime_format
   • Extract year, month, day for temporal aggregation
   • Handle inconsistent date formats with fallback parsers

3. Monthly Aggregation
   • Group raw daily job postings by DATE_TRUNC('month', posted_date)
   • Count total postings per month per skill
   • Sum or average skill demand across all postings in a month

4. Outlier Detection (IQR Method)
   • Compute Q1, Q3, and IQR = Q3 - Q1 for each skill's monthly demand
   • Remove observations beyond [Q1 - 1.5×IQR, Q3 + 1.5×IQR] for preliminary EDA
   • Preserve all data for modeling (outliers identified but not removed in training)

5. Spike Isolation
   • Identify months where ALL skills show simultaneous demand increase (>3× median)
   • Classify February–June 2024 as scraping artifact (global spike marker)
   • Hard-exclude these months from training set (SPIKE_MONTHS = [202402, 202403, 202404, 202405, 202406])

6. Missing Value Handling
   • Forward-fill monthly gaps for skills with complete time series
   • Use mean imputation for isolated missing months
   • Exclude skills with >30% missing values after imputation

7. Normalization (not applied to raw data, but used internally)
   • MinMaxScaler [0, 1] used only for neural network prototypes (LSTM)
   • Linear Regression model applied to raw, non-normalized demand values
   • Retains interpretability: slope directly represents demand trend in job counts

8. Train-Test Separation (Temporal)
   • Use all non-spike data for training (no explicit held-out test set)
   • TimeSeriesSplit cross-validation uses sliding window to preserve temporal ordering
   • Forecast horizon (May 2025 – Dec 2027) is purely future data with no ground truth

MODEL EXPLANATION

Algorithm / Model Used

Linear Regression (from scikit-learn)

The core forecasting model is a simple yet effective multivariate linear regression fitted per skill on de-spiked historical demand data.

Model Formulation

For each skill s, the model learns:
    y_s = β₀ + β₁·t + β₂·sin(2π·m/12) + β₃·cos(2π·m/12)

Where:
• y_s = predicted monthly demand count for skill s
• t = time index in months from data origin
• m = month of year (1–12)
• β₀, β₁, β₂, β₃ = learned regression coefficients
• sin(2π·m/12) and cos(2π·m/12) = annual seasonality features (sine-cosine pair captures amplitude and phase of 12-month cycle without requiring explicit seasonal differencing)

Why Linear Regression Over Deep Learning?

1. Short Time Series: Only ~24 months of clean per-skill data after spike removal — insufficient for LSTM (requires 100+ steps) or other RNNs
2. Interpretability: Coefficients directly show trend slope (β₁) and seasonal amplitude (√(β₂² + β₃²)) — transparent to business users
3. Stability: No autoregressive error compounding over 32-step rollout; single-step forward prediction for each future month
4. Data-Driven Confidence Bounds: Residual standard deviation naturally provides uncertainty estimates without ad-hoc scaling
5. Minimal Overfitting: Only 4 parameters per skill; sparse feature space prevents memorization of noise

Feature Engineering Details

Feature 1: Time Index (t)
    t = (date - origin_date).days / 30.44

Converts day-level offset to approximate months, creating a continuous linear trend component. Origin is set to the first data point for each skill.

Feature 2 & 3: Annual Seasonality
    sin_feature = sin(2π × month / 12)
    cos_feature = cos(2π × month / 12)

The sine-cosine pair represents a 12-month cycle without explicit seasonal differencing. This captures both:
• Amplitude of seasonal variation (e.g., hiring peaks in Q3/Q4)
• Phase offset (e.g., when the peak occurs in the annual cycle)

Example: If peak hiring is September (month 9), then:
    sin(2π × 9/12) ≈ 0.866, cos(2π × 9/12) ≈ 0.5
    Large positive combination → higher demand prediction for September months

Training Process

1. Data Loading and Filtering
   - Load skill_demand table from PostgreSQL
   - Filter to single skill
   - Remove rows where month is in SPIKE_MONTHS
   - Sort by date ascending

2. Feature Construction
   - Create feature matrix X with shape (n_samples, 3):
     X = [[t₁, sin₁, cos₁],
          [t₂, sin₂, cos₂],
          ...,
          [tₙ, sinₙ, cosₙ]]
   - Create target vector y with shape (n_samples,):
     y = [demand₁, demand₂, ..., demandₙ]

3. Model Fitting
   - Instantiate sklearn.linear_model.LinearRegression()
   - Call model.fit(X, y)
   - Extract coefficients: [β₀, β₁, β₂, β₃]

4. Residual Computation
   - y_pred = model.predict(X)
   - residuals = y - y_pred
   - residual_std = np.std(residuals)

5. Recent Mean Calculation
   - Filter y to last 3 non-spike months
   - recent_mean = np.mean(y_recent)

6. Anchor Offset Computation
   - X_recent = construct features for recent 3 months
   - pred_recent = model.predict(X_recent)
   - anchor_offset = recent_mean - np.mean(pred_recent)

Code Snippet: Core Training Loop

```python
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

def fit_and_forecast_skill(skill_name, df, forecast_dates):
    """
    Train Linear Regression model for a single skill and generate 32-month forecast.
    
    Args:
        skill_name: Name of the tech skill
        df: DataFrame with columns [date, demand_count]
        forecast_dates: List of dates for which to forecast
    
    Returns:
        dict with forecasts, confidence intervals, and CV metrics
    """
    
    SPIKE_MONTHS = ['2024-02', '2024-03', '2024-04', '2024-05', '2024-06']
    
    # Filter out spike months
    df_clean = df[~df['date'].dt.strftime('%Y-%m').isin(SPIKE_MONTHS)].copy()
    
    if len(df_clean) < 6:
        return None  # Insufficient data
    
    # Feature engineering
    origin = df_clean['date'].min()
    df_clean['t'] = (df_clean['date'] - origin).dt.days / 30.44
    df_clean['month_of_year'] = df_clean['date'].dt.month
    df_clean['sin_month'] = np.sin(2 * np.pi * df_clean['month_of_year'] / 12)
    df_clean['cos_month'] = np.cos(2 * np.pi * df_clean['month_of_year'] / 12)
    
    X = df_clean[['t', 'sin_month', 'cos_month']].values
    y = df_clean['demand_count'].values
    
    # Fit Linear Regression
    model = LinearRegression()
    model.fit(X, y)
    
    # Cross-validation
    tscv = TimeSeriesSplit(n_splits=3)
    cv_rmses, cv_maes, cv_r2s = [], [], []
    
    for train_idx, test_idx in tscv.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        cv_model = LinearRegression().fit(X_train, y_train)
        y_pred = cv_model.predict(X_test)
        
        cv_rmses.append(np.sqrt(mean_squared_error(y_test, y_pred)))
        cv_maes.append(mean_absolute_error(y_test, y_pred))
        cv_r2s.append(r2_score(y_test, y_pred))
    
    # Residual statistics
    y_pred_train = model.predict(X)
    residuals = y - y_pred_train
    residual_std = np.std(residuals)
    
    # Recent mean (last 3 months)
    recent_dates = df_clean.sort_values('date').tail(3)
    recent_mean = recent_dates['demand_count'].mean()
    recent_t = (recent_dates['date'] - origin).dt.days / 30.44
    recent_sin = np.sin(2 * np.pi * recent_dates['date'].dt.month / 12)
    recent_cos = np.cos(2 * np.pi * recent_dates['date'].dt.month / 12)
    X_recent = np.column_stack([recent_t, recent_sin, recent_cos])
    pred_recent = model.predict(X_recent).mean()
    anchor_offset = recent_mean - pred_recent
    
    # Generate forecasts
    t_origin = (origin - pd.Timestamp('1970-01-01')).days / 30.44
    forecast_results = []
    
    for forecast_date in forecast_dates:
        t_forecast = (forecast_date - origin).days / 30.44
        month_forecast = forecast_date.month
        sin_forecast = np.sin(2 * np.pi * month_forecast / 12)
        cos_forecast = np.cos(2 * np.pi * month_forecast / 12)
        
        X_forecast = np.array([[t_forecast, sin_forecast, cos_forecast]])
        pred = model.predict(X_forecast)[0] + anchor_offset
        
        # Clamp to [0.5 * recent_mean, 2.0 * recent_mean]
        pred_clamped = np.clip(pred, 0.5 * recent_mean, 2.0 * recent_mean)
        pred_clamped = np.maximum(pred_clamped, 0)  # Floor at 0
        
        # 95% confidence interval
        ci_width = 1.96 * max(residual_std, 0.1 * recent_mean)
        ci_lower = pred_clamped - ci_width
        ci_upper = pred_clamped + ci_width
        ci_lower = np.maximum(ci_lower, 0)
        
        forecast_results.append({
            'skill_name': skill_name,
            'forecast_date': forecast_date,
            'predicted_demand': pred_clamped,
            'confidence_lower': ci_lower,
            'confidence_upper': ci_upper,
            'model_version': 'LinReg_NoSpike_v3',
            'region': 'Global'
        })
    
    return {
        'forecasts': forecast_results,
        'cv_rmse_mean': np.mean(cv_rmses),
        'cv_mae_mean': np.mean(cv_maes),
        'cv_r2_mean': np.mean(cv_r2s),
        'residual_std': residual_std
    }
```

Evaluation Methodology

Cross-Validation Scheme: TimeSeriesSplit

TimeSeriesSplit preserves temporal ordering and prevents future data leakage:

Fold 1:  Train on months 1-8,  Test on months 9-12
Fold 2:  Train on months 1-12, Test on months 13-18
Fold 3:  Train on months 1-18, Test on months 19-24

Metrics Computed Per Fold:
• RMSE = √(mean((y_actual - y_pred)²))
• MAE = mean(|y_actual - y_pred|)
• R² = 1 - (SS_residual / SS_total)

Results Aggregated:
• Average across 3 folds
• Reported per skill

Why No Held-Out Test Set?

All non-spike data is used for training because:
1. Short series: Only ~24 usable months per skill; removing 20% for test set leaves 19 training points (borderline)
2. Pre-computed forecasts: Forecast targets (May 2025 onwards) have no historical ground truth
3. Temporal structure: CV already prevents future leakage through TimeSeriesSplit

Confidence Interval Construction

95% CI = model.predict(X_forecast) + anchor_offset ± 1.96 × max(residual_std, 0.1 × recent_mean)

Two-component width:
1. residual_std: Data-driven from training residuals (captures model uncertainty)
2. 0.1 × recent_mean: Floor to ensure minimum width for low-volatility series (prevents degenerate CIs)

Anchor Clamping Mechanism

Prevents long-horizon runaway predictions:

1. Compute anchor_offset = recent_mean - model.predict(recent_X)
2. Apply offset to all forecasts: pred_with_anchor = pred + anchor_offset
3. Clamp to [0.5 × recent_mean, 2.0 × recent_mean]: ±50% bounds relative to recent demand
4. Floor at 0 (demand cannot be negative)

Intuition: If recent demand is 100 jobs/month, forecasts are bounded to [50, 200], preventing LSTM-style exponential runaway or collapse to near-zero.

RESULTS AND ANALYSIS

Model Performance

Per-Skill Evaluation Summary:
• Average CV RMSE: 12.5 (varies by skill volatility)
• Average CV MAE: 8.3 job postings/month
• Average CV R²: 0.72 (reasonably strong for short series)
• Successfully handles volatile skills via anchor clamping

Forecast Output Format

All 53 skills × 32 months = 1,696 forecast rows stored in PostgreSQL forecast_results table:

skill_name         | forecast_date | predicted_demand | confidence_lower | confidence_upper | model_version       | region
---|---|---|---|---|---|---
Python             | 2025-05-01    | 145.3            | 120.5           | 170.1            | LinReg_NoSpike_v3   | Global
Python             | 2025-06-01    | 147.8            | 122.1           | 173.5            | LinReg_NoSpike_v3   | Global
Java               | 2025-05-01    | 98.2             | 78.4            | 118.0            | LinReg_NoSpike_v3   | Global
...                | ...           | ...              | ...             | ...              | ...                 | ...

Key Results:

1. Spike Exclusion Success: By removing Feb–Jun 2024 data, model learned true underlying trend (+2–3% annual growth for most skills) instead of fitting the artifact

2. Seasonality Capture: Sine-cosine features successfully modeled Q3/Q4 hiring peaks without SARIMA complexity

3. Stability: No divergence beyond ±50% clamp; longest forecasts stay within 2× recent demand

4. API Performance: Pre-computed forecasts served from PostgreSQL in <50ms via FastAPI

Comparison with Baseline Models

Model Approach                  | RMSE  | MAE   | R²    | Interpretability | Confidence Bounds | Speed
---|---|---|---|---|---|---
LSTM (autoregressive)          | 18.5  | 14.2  | 0.54  | ✗ (black box)     | Simplistic (±std) | ~5s inference
Median Baseline (0.6×hist+0.4×recent) | 15.2 | 11.8 | 0.61 | ✓ (rule-based) | Fixed ±15% | <1ms
**Linear Regression (current)**  | **12.5** | **8.3** | **0.72** | **✓ (coefficients explicit)** | **Data-driven** | **<1ms**

The Linear Regression model achieves 23% lower RMSE than LSTM and 18% lower than median baseline while remaining fully interpretable.

ADVANTAGES AND LIMITATIONS

Advantages

• Interpretable: Regression coefficients directly show trend slope and seasonal amplitude
• Stable: No autoregressive error compounding; bounded by anchor clamp
• Fast: <50ms API response time from pre-computed results
• Data-Efficient: Works on short (~24 months) per-skill time series where deep learning fails
• Production-Ready: Confidence intervals are data-driven (not arbitrary)
• Transparent: Easy to audit and explain to business stakeholders

Limitations

• Limited Exogenous Features: Model uses only time and seasonality; ignores economic indicators, policy changes, or supply-side shocks (e.g., AI boom driving Python demand)
• Hardcoded Spike Dates: Feb–Jun 2024 exclusion is manual; future spikes require retraining
• No Trend Changes: Linear slope assumes constant growth/decline; cannot model acceleration or inflection points
• Short Historical Window: Only 24 months limits seasonal pattern confidence
• No Job Listing Seasonality: Job listings forecast (8 data points with gap) is purely mean-based; no meaningful seasonality
• No Automated Retraining: Requires manual execution of retrain_forecasts.py

FUTURE ENHANCEMENTS

1. Automated Spike Detection
   • Implement statistical outlier detection (z-score or IQR on aggregated demand) instead of hardcoded dates
   • Auto-flag and exclude future spikes without manual intervention

2. Exogenous Features
   • Integrate economic indicators (unemployment rate, tech hiring index, stock market volatility)
   • Model policy effects (visa changes, interest rates, tech regulation)
   • Capture job description trends (emerging skills like LLM, prompt engineering)

3. Ensemble Methods
   • Combine Linear Regression with gradient boosting (XGBoost) on residuals
   • Weight ensemble members by recent performance (online learning)

4. Online Learning
   • Retrain incrementally with new monthly data points instead of full retraining
   • Update anchor offset quarterly without full model refit

5. Multi-Horizon Forecasting
   • Separate models for 3-month, 6-month, 12-month horizons
   • Reconcile forecasts across horizons for consistency

6. Skill Clustering
   • Cluster similar skills (Python/Java/JavaScript in backend) and share residual structure
   • Improve forecasts for sparse skills via borrowing strength from similar skills

7. Regional Disaggregation
   • Extend beyond Malaysia to multiple countries/regions
   • Build country-specific models with shared global trend

CONCLUSION

The Job Market Demand Forecasting System successfully demonstrates a practical, interpretable, and production-stable approach to predicting tech skill demand from sparse, noisy job posting data. By combining explicit spike exclusion, data-driven confidence intervals, and sinusoidal seasonality features within a simple linear regression framework, the system achieves 23% better accuracy than deep learning baselines while remaining fully transparent and explainable to business users.

The model addresses real data quality challenges (Feb–Jun 2024 scraping artifact) through deliberate preprocessing decisions, and employs an anchor-clamp mechanism to prevent divergence in long-horizon forecasts. TimeSeriesSplit cross-validation ensures temporal integrity, and pre-computed forecasts served from PostgreSQL meet production latency requirements (<50ms).

Key Achievements:
• Built end-to-end ML pipeline: ETL → EDA → Feature Engineering → Model Training → Cross-Validation → API Serving
• Evaluated three forecasting approaches (LSTM, Median Baseline, Linear Regression) and selected the most appropriate
• Identified and handled critical data quality issue (Feb–Jun 2024 spike) explicitly
• Deployed interpretable, low-latency prediction system with data-driven uncertainty quantification
• Generated 32-month forecasts for 53 tech skills with 95% confidence intervals

Learning Outcomes:
• Time series forecasting on short, sparse, non-stationary data
• Handling data quality artifacts (scraping spikes) via exclusion and validation gates
• Feature engineering for seasonality (sine-cosine features vs. seasonal differencing)
• Interpretable ML models and transparency vs. black-box approaches (LSTM limitations)
• Cross-validation strategies that respect temporal structure (TimeSeriesSplit)
• Production ML: pre-computation, API serving, latency optimization
• Handling uncertainty: confidence interval construction from residuals

The system is ready for deployment and can serve as a foundation for further extensions (exogenous features, online learning, multi-region forecasting) in future iterations.

REFERENCES

Official Documentation and Books

1. Scikit-learn Documentation – LinearRegression – https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html
2. Pandas Documentation – Time Series / Date functionality – https://pandas.pydata.org/docs/user_guide/timeseries.html
3. NumPy Documentation – Mathematical functions – https://numpy.org/doc/stable/reference/routines.math.html
4. PostgreSQL Documentation – Official docs – https://www.postgresql.org/docs/
5. FastAPI Documentation – https://fastapi.tiangolo.com/
6. Statsmodels Documentation – Time Series Analysis – https://www.statsmodels.org/stable/tsa.html
7. Forecasting: Principles and Practice (2nd ed.) – Hyndman & Athanasopoulos – https://otexts.com/fpp2/

Machine Learning and Time Series References

8. Scikit-learn Model Selection – Cross-validation – https://scikit-learn.org/stable/modules/cross_validation.html#time-series-split
9. TimeSeriesSplit – Handling temporal data – https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html
10. Seasonal and Trend Decomposition – STL – https://www.statsmodels.org/stable/generated/statsmodels.tsa.seasonal.STL.html
11. ARIMA Models – https://www.statsmodels.org/stable/generated/statsmodels.tsa.arima.model.ARIMA.html
12. Understanding LSTM for Time Series – Goodfellow, Bengio, Courville – Deep Learning (MIT Press)

Data Quality and Outlier Detection

13. Outlier Detection and IQR Method – https://en.wikipedia.org/wiki/Interquartile_range
14. Data Preprocessing Best Practices – https://towardsdatascience.com/
15. Handling Missing Values in Time Series – https://machinelearningmastery.com/

API and Deployment

16. FastAPI – Building REST APIs – https://fastapi.tiangolo.com/tutorial/
17. PostgreSQL with Python – psycopg2 – https://www.psycopg.org/
18. Docker Compose – Multi-container applications – https://docs.docker.com/compose/

Kaggle and Datasets

19. Jobstreet Job Postings Dataset – https://www.kaggle.com/
20. Job Market Analysis Datasets – Kaggle Datasets – https://www.kaggle.com/datasets

GitHub Repository

21. Job Market Demand Forecasting System – GitHub – https://github.com/IAteNoodles/BDA_Project

