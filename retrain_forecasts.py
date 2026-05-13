#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BDA Forecast Retrainer v3 — EDA + Linear Regression + Cross-Validation
=======================================================================

Root-cause fixes applied
------------------------
1. SKILL DEMAND — Feb-Mar 2024 was a data-collection spike (all skills spiked
   simultaneously). We EXCLUDE those spike months entirely and train ONLY on
   the post-spike "normal" window (2024-07 onward + pre-spike baseline).
   This gives a clean slope on real, comparable data.
   CV is run with TimeSeriesSplit on the cleaned window.

2. JOB LISTINGS — Only 8 months of data with a 9-month gap in the middle.
   A linear regression slope of -1.35/mo would flatline to 1 immediately.
   Fix: use the mean of the last 3 real months as a stable anchor, apply a
   very gentle ±0 trend, and widen CIs to reflect genuine uncertainty.

3. ANCHOR CLAMP — forecast values are clamped to ±50% of recent_mean so
   long-horizon extrapolation can never wildly diverge from what we actually
   see today.

Run with stable-env:
    stable-env\\Scripts\\python retrain_forecasts.py
"""

import io
import json
import subprocess
import sys
import warnings

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit

warnings.filterwarnings("ignore")

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

FORECAST_START = pd.Timestamp("2025-05-01")
FORECAST_END = pd.Timestamp("2027-12-01")
FORECAST_MONTHS = (
    (FORECAST_END.year - FORECAST_START.year) * 12
    + (FORECAST_END.month - FORECAST_START.month)
    + 1
)
N_CV_SPLITS = 3

# The Feb-Jun 2024 period was a mass-import/scraping burst — all skills spiked
# together. We treat any month where the *global* job count is abnormally high
# as a "scrape spike" and exclude it from regression training.
SPIKE_MONTHS = pd.to_datetime(
    [
        "2024-02-01",
        "2024-03-01",
        "2024-04-01",
        "2024-05-01",
        "2024-06-01",
    ]
)

# ─────────────────────────────────────────────────────────────────────────────
# DB helpers
# ─────────────────────────────────────────────────────────────────────────────


def run_psql(sql: str) -> str:
    """
    Run a SQL statement inside the postgres docker container.
    Uses shell=True on Windows so docker is found via PATH.
    Prints stderr if the command fails so we can diagnose quickly.
    """
    # Build a single shell command string — safer on Windows
    # Escape any single quotes inside the SQL
    sql_escaped = sql.replace('"', '\\"')
    cmd = f'docker exec postgres psql -U postgres -d job_market -c "{sql_escaped}"'

    r = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60,
        shell=True,
    )
    if r.returncode != 0 and r.stderr.strip():
        print(f"  [psql stderr] {r.stderr.strip()[:300]}", flush=True)
    return r.stdout + r.stderr


def load_skill_demand() -> pd.DataFrame:
    sql = "SELECT skill_name, period_start, demand_count FROM skill_demand ORDER BY skill_name, period_start;"
    raw = run_psql(sql)
    if not raw.strip():
        print("  [WARN] load_skill_demand: empty response from DB", flush=True)
    rows = []
    for line in raw.split("\n")[2:]:
        if "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 3 and parts[0] and parts[1]:
            try:
                rows.append(
                    {
                        "skill_name": parts[0],
                        "period_start": pd.to_datetime(parts[1]),
                        "demand_count": float(parts[2]),
                    }
                )
            except Exception:
                continue
    return pd.DataFrame(rows)


def load_job_listings() -> pd.DataFrame:
    sql = "SELECT DATE_TRUNC('month', posted_date)::date AS month, COUNT(*) AS cnt FROM job_listings WHERE posted_date IS NOT NULL GROUP BY 1 ORDER BY 1;"
    raw = run_psql(sql)
    if not raw.strip():
        print("  [WARN] load_job_listings: empty response from DB", flush=True)
    rows = []
    for line in raw.split("\n")[2:]:
        if "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 2 and parts[0] and parts[1]:
            try:
                rows.append(
                    {
                        "date": pd.to_datetime(parts[0]),
                        "count": float(parts[1]),
                    }
                )
            except Exception:
                continue
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# EDA
# ─────────────────────────────────────────────────────────────────────────────


def eda_skill_demand(df: pd.DataFrame):
    print("\n" + "=" * 70)
    print("  EDA — SKILL DEMAND")
    print("=" * 70)
    print(f"  Total rows          : {len(df):,}")
    print(f"  Unique skills       : {df['skill_name'].nunique()}")
    print(
        f"  Date range          : {df['period_start'].min().date()} → "
        f"{df['period_start'].max().date()}"
    )
    print(
        f"  Demand global range : {df['demand_count'].min():.0f} – "
        f"{df['demand_count'].max():.0f}"
    )
    print(
        f"  Demand mean / median: {df['demand_count'].mean():.1f} / "
        f"{df['demand_count'].median():.1f}"
    )

    # IQR spike detection
    q1, q3 = df["demand_count"].quantile([0.25, 0.75])
    fence = q3 + 3 * (q3 - q1)
    spikes = df[df["demand_count"] > fence]
    print(f"\n  IQR upper fence (Q3+3×IQR): {fence:.0f}")
    print(f"  Spike rows detected        : {len(spikes)}")
    if len(spikes):
        print("\n  Top 8 spike rows:")
        print(
            spikes.nlargest(8, "demand_count")[
                ["skill_name", "period_start", "demand_count"]
            ].to_string(index=False)
        )

    # Detect the spike months via mean across all skills per month
    month_mean = (
        df.groupby("period_start")["demand_count"].mean().reset_index(name="avg_demand")
    )
    global_median = month_mean["avg_demand"].median()
    spike_detected = month_mean[month_mean["avg_demand"] > global_median * 3]
    print(f"\n  Global-mean spike months (>3× median {global_median:.1f}):")
    print(spike_detected.to_string(index=False))

    # Per-skill table (top 5 by peak)
    top5 = df.groupby("skill_name")["demand_count"].max().nlargest(5).index.tolist()
    print(f"\n  Per-skill stats — top 5 by peak:")
    print(
        f"  {'Skill':<22} {'n':>4} {'min':>6} {'max':>7} "
        f"{'mean':>7} {'post-spike avg':>15} {'spike_months':>10}"
    )
    print("  " + "-" * 80)
    for sk in top5:
        s = df[df["skill_name"] == sk].sort_values("period_start")
        ps = s[~s["period_start"].isin(SPIKE_MONTHS)]
        recent = s[s["period_start"] >= "2024-07-01"]
        sm = (
            s[s["period_start"].isin(SPIKE_MONTHS)]["period_start"]
            .dt.strftime("%Y-%m")
            .tolist()
        )
        print(
            f"  {sk:<22} {len(s):>4} {s['demand_count'].min():>6.0f} "
            f"{s['demand_count'].max():>7.0f} {s['demand_count'].mean():>7.1f} "
            f"{recent['demand_count'].mean():>15.1f} "
            f"{','.join(sm) if sm else 'none':>10}"
        )
    print()


def eda_job_listings(df: pd.DataFrame):
    print("\n" + "=" * 70)
    print("  EDA — JOB LISTINGS (monthly)")
    print("=" * 70)
    print(f"  Total months : {len(df)}")
    print(f"  Date range   : {df['date'].min().date()} → {df['date'].max().date()}")
    print(f"  Count range  : {df['count'].min():.0f} – {df['count'].max():.0f}")
    print(f"  Mean / Median: {df['count'].mean():.1f} / {df['count'].median():.1f}")
    print(f"  Std dev      : {df['count'].std():.1f}")

    # Detect data gap
    df_s = df.sort_values("date")
    for i in range(1, len(df_s)):
        gap_months = (
            df_s.iloc[i]["date"].year - df_s.iloc[i - 1]["date"].year
        ) * 12 + (df_s.iloc[i]["date"].month - df_s.iloc[i - 1]["date"].month)
        if gap_months > 2:
            print(
                f"\n  [!] Data gap detected: {gap_months} months between "
                f"{df_s.iloc[i - 1]['date'].strftime('%Y-%m')} and "
                f"{df_s.iloc[i]['date'].strftime('%Y-%m')}"
            )

    print("\n  Monthly data (bar = share of peak):")
    peak = df["count"].max()
    for _, r in df.sort_values("date").iterrows():
        bar = "█" * max(1, int(r["count"] / peak * 30))
        print(f"    {r['date'].strftime('%Y-%m')}  {r['count']:>4.0f}  {bar}")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# Feature builder
# ─────────────────────────────────────────────────────────────────────────────


def build_features(dates: pd.Series, origin: pd.Timestamp) -> np.ndarray:
    """trend + annual sin/cos seasonality"""
    t = np.array([(d - origin).days / 30.44 for d in dates])
    month = np.array([d.month for d in dates])
    sin_m = np.sin(2 * np.pi * month / 12)
    cos_m = np.cos(2 * np.pi * month / 12)
    return np.column_stack([t, sin_m, cos_m])


# ─────────────────────────────────────────────────────────────────────────────
# Cross-validation
# ─────────────────────────────────────────────────────────────────────────────


def cross_val_evaluate(
    X: np.ndarray, y: np.ndarray, n_splits: int = N_CV_SPLITS
) -> dict:
    """TimeSeriesSplit CV — returns mean RMSE / MAE / R²"""
    tscv = TimeSeriesSplit(n_splits=n_splits)
    rmses, maes, r2s = [], [], []

    for tr, te in tscv.split(X):
        if len(tr) < 2 or len(te) < 1:
            continue
        m = LinearRegression().fit(X[tr], y[tr])
        p = m.predict(X[te])
        rmses.append(float(np.sqrt(mean_squared_error(y[te], p))))
        maes.append(float(mean_absolute_error(y[te], p)))
        r2s.append(float(r2_score(y[te], p)) if len(te) > 1 else float("nan"))

    return {
        "rmse": float(np.nanmean(rmses)),
        "mae": float(np.nanmean(maes)),
        "r2": float(np.nanmean(r2s)),
        "n_folds": len(rmses),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Skill demand: fit + forecast
# ─────────────────────────────────────────────────────────────────────────────


def fit_and_forecast_skill(
    skill: str,
    sub: pd.DataFrame,
    forecast_dates: pd.DatetimeIndex,
    origin: pd.Timestamp,
) -> dict:
    """
    Strategy
    --------
    1. Remove the known scrape-spike months (Feb-Jun 2024) — they don't
       represent real hiring demand and blow up any regression.
    2. Train LinearRegression on the de-spiked series (trend + seasonality).
    3. Evaluate with TimeSeriesSplit CV.
    4. Compute recent_mean from the last 3 non-spike months.
    5. Apply an anchor offset so the forecast STARTS at recent_mean.
    6. Clamp all predictions to [recent_mean * 0.5, recent_mean * 2.0] so
       long-horizon extrapolation stays within a credible range.
    """
    sub = sub.sort_values("period_start").reset_index(drop=True)

    # ── Remove spike months ──────────────────────────────────────────────
    clean = sub[~sub["period_start"].isin(SPIKE_MONTHS)].reset_index(drop=True)
    if len(clean) < 3:
        # Fall back to full data if too little remains
        clean = sub.copy()

    y_clean = clean["demand_count"].values.astype(float)
    X_clean = build_features(clean["period_start"], origin)

    # ── CV on cleaned data ───────────────────────────────────────────────
    cv = {"rmse": np.nan, "mae": np.nan, "r2": np.nan, "n_folds": 0}
    if len(X_clean) >= N_CV_SPLITS + 1:
        cv = cross_val_evaluate(X_clean, y_clean)

    # ── Train final model on all cleaned history ─────────────────────────
    model = LinearRegression().fit(X_clean, y_clean)

    # ── Recent mean: last 3 NON-spike months ────────────────────────────
    recent_clean = clean.tail(3)
    recent_mean = recent_clean["demand_count"].mean()

    # ── Anchor offset ────────────────────────────────────────────────────
    X_recent = build_features(recent_clean["period_start"], origin)
    reg_at_last = model.predict(X_recent).mean()
    anchor_off = recent_mean - reg_at_last

    # ── Forecast ─────────────────────────────────────────────────────────
    X_fc = build_features(pd.Series(forecast_dates), origin)
    preds = model.predict(X_fc) + anchor_off

    # Clamp: predictions cannot stray beyond ±100% of recent_mean
    lo_clamp = recent_mean * 0.50
    hi_clamp = recent_mean * 2.00
    preds = np.clip(preds, lo_clamp, hi_clamp)
    preds = np.maximum(preds, 0)

    # ── 95% CI from training residual std ───────────────────────────────
    resid_std = float(np.std(y_clean - model.predict(X_clean)))
    ci = 1.96 * max(resid_std, recent_mean * 0.10)  # at least 10% width
    lower = np.maximum(preds - ci, 0)
    upper = preds + ci

    return {
        "preds": preds,
        "lower": lower,
        "upper": upper,
        "cv": cv,
        "recent_mean": recent_mean,
        "slope": float(model.coef_[0]),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Job listings: stable-mean forecast
# ─────────────────────────────────────────────────────────────────────────────


def forecast_job_listings(df: pd.DataFrame) -> dict:
    """
    With only 8 months of data and a 9-month gap, linear regression produces
    a misleading negative slope. Instead we:
      1. Run CV anyway (for reporting / learning purposes).
      2. Use recent_mean (last 3 months) as the stable forecast level.
      3. Apply a tiny gentle slope derived ONLY from the post-gap period
         (Mar-Apr 2025) so the line doesn't completely flatline.
      4. CI = 1.96 × residual std of the recent window.
    """
    df = df.sort_values("date").reset_index(drop=True)
    origin = df["date"].min()
    y = df["count"].values.astype(float)
    X_hist = build_features(df["date"], origin)

    # ── CV (informational) ───────────────────────────────────────────────
    cv = {"rmse": np.nan, "mae": np.nan, "r2": np.nan, "n_folds": 0}
    if len(X_hist) >= N_CV_SPLITS + 1:
        cv = cross_val_evaluate(X_hist, y)

    print(f"\n  Cross-validation (TimeSeriesSplit, {N_CV_SPLITS} folds):")
    print(f"    RMSE : {cv['rmse']:.2f}")
    print(f"    MAE  : {cv['mae']:.2f}")
    print(
        f"    R²   : {cv['r2']:.4f}  "
        f"(negative R² is expected with a data gap — CV is informational)"
    )

    # ── Use post-gap data only for trend estimate ────────────────────────
    post_gap = df[df["date"] >= "2025-01-01"].reset_index(drop=True)
    if len(post_gap) < 2:
        post_gap = df.tail(3)

    recent_mean = post_gap["count"].mean()
    resid_std = post_gap["count"].std() if len(post_gap) > 1 else recent_mean * 0.3

    # Gentle slope from post-gap window (per month)
    if len(post_gap) >= 2:
        x_pg = np.arange(len(post_gap), dtype=float)
        y_pg = post_gap["count"].values.astype(float)
        slope = float(np.polyfit(x_pg, y_pg, 1)[0])  # counts/month
        # Dampen extreme slopes — cap at ±1 per month
        slope = float(np.clip(slope, -1.0, 1.0))
    else:
        slope = 0.0

    print(f"\n  Recent {len(post_gap)}-month mean : {recent_mean:.1f}")
    print(f"  Post-gap slope (capped) : {slope:+.3f} per month")
    print(f"  Residual std            : {resid_std:.1f}")

    ci = 1.96 * max(resid_std, recent_mean * 0.20)  # at least 20% width

    # ── Forecast ─────────────────────────────────────────────────────────
    forecast_dates = pd.date_range(FORECAST_START, FORECAST_END, freq="MS")
    preds = np.array(
        [max(1.0, recent_mean + slope * i) for i in range(len(forecast_dates))]
    )
    lower = np.maximum(preds - ci, 0)
    upper = preds + ci

    print(f"\n  Forecast sample (first 6 months):")
    for i in range(min(6, len(forecast_dates))):
        print(
            f"    {forecast_dates[i].strftime('%Y-%m')}  "
            f"pred={preds[i]:.1f}  CI=[{lower[i]:.1f}, {upper[i]:.1f}]"
        )

    # ── Build JSON ────────────────────────────────────────────────────────
    historical_out = [
        {
            "date": r["date"].strftime("%Y-%m-%d"),
            "count": float(r["count"]),
            "confidenceLower": None,
            "confidenceUpper": None,
        }
        for _, r in df.iterrows()
    ]
    predicted_out = [
        {
            "date": fd.strftime("%Y-%m-%d"),
            "count": round(float(preds[i]), 2),
            "confidenceLower": round(float(lower[i]), 2),
            "confidenceUpper": round(float(upper[i]), 2),
        }
        for i, fd in enumerate(forecast_dates)
    ]
    return {"historical": historical_out, "predicted": predicted_out}


# ─────────────────────────────────────────────────────────────────────────────
# Skill demand — batch processor
# ─────────────────────────────────────────────────────────────────────────────


def process_skill_demand(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "=" * 70)
    print("  TRAINING — SKILL DEMAND (LinReg, spike-excluded, CV)")
    print("=" * 70)

    forecast_dates = pd.date_range(FORECAST_START, FORECAST_END, freq="MS")
    origin = df["period_start"].min()
    skills = sorted(df["skill_name"].unique())
    all_rows = []

    print(
        f"\n  {'Skill':<22} {'n_clean':>8} {'recent_avg':>11} "
        f"{'slope/mo':>9} {'RMSE':>7} {'MAE':>7} {'R²':>7}"
    )
    print("  " + "-" * 78)

    for skill in skills:
        sub = df[df["skill_name"] == skill].copy()
        if len(sub) < 3:
            continue

        r = fit_and_forecast_skill(skill, sub, forecast_dates, origin)
        cv = r["cv"]
        # n_clean = rows used for training (spike months excluded)
        n_clean = len(sub[~sub["period_start"].isin(SPIKE_MONTHS)])
        if n_clean < 3:
            n_clean = len(sub)

        print(
            f"  {skill:<22} {n_clean:>8} {r['recent_mean']:>11.1f} "
            f"{r['slope']:>9.2f} {cv['rmse']:>7.1f} "
            f"{cv['mae']:>7.1f} {cv['r2']:>7.2f}"
        )

        for i, fd in enumerate(forecast_dates):
            all_rows.append(
                {
                    "skill_name": skill,
                    "forecast_date": fd.date(),
                    "predicted_demand": round(float(r["preds"][i]), 4),
                    "confidence_lower": round(float(r["lower"][i]), 4),
                    "confidence_upper": round(float(r["upper"][i]), 4),
                    "model_version": "LinReg_NoSpike_v3",
                    "region": "Global",
                }
            )

    df_fc = pd.DataFrame(all_rows)

    # Sanity check
    avg_by_skill = (
        df_fc.groupby("skill_name")["predicted_demand"]
        .mean()
        .nlargest(10)
        .reset_index()
    )
    print(
        f"\n  Generated {len(df_fc):,} rows across {df_fc['skill_name'].nunique()} skills"
    )
    print("\n  Sanity check — top 10 by avg predicted demand:")
    print(avg_by_skill.to_string(index=False))

    return df_fc


# ─────────────────────────────────────────────────────────────────────────────
# Push to Postgres
# ─────────────────────────────────────────────────────────────────────────────


def run_docker_cp(src: str, dst: str) -> bool:
    """docker cp using shell=True so PATH is resolved on Windows."""
    r = subprocess.run(
        f'docker cp "{src}" "{dst}"',
        capture_output=True,
        text=True,
        timeout=30,
        shell=True,
    )
    if r.returncode != 0:
        print(f"  [docker cp error] {r.stderr.strip()[:200]}", flush=True)
        return False
    return True


def push_to_db(df_fc: pd.DataFrame):
    print("\n" + "=" * 70)
    print("  PUSHING TO POSTGRES")
    print("=" * 70)

    tsv = "backend/database/seed/forecast_results.tsv"
    df_fc.to_csv(tsv, sep="\t", index=False)
    print(f"  Wrote {len(df_fc):,} rows → {tsv}")

    ok = run_docker_cp(tsv, "postgres:/tmp/forecast_results.tsv")
    if not ok:
        print("  [ERROR] docker cp failed — aborting DB push")
        return
    print("  Copied TSV into container ✓")

    # Split into two calls: TRUNCATE first, then COPY
    # Avoids quoting the tab character inside a shell string
    r1 = run_psql("TRUNCATE forecast_results CASCADE;")
    print(f"  TRUNCATE: {r1.strip()}")

    copy_sql = (
        "COPY forecast_results "
        "(skill_name, forecast_date, predicted_demand, confidence_lower, "
        "confidence_upper, model_version, region) "
        "FROM '/tmp/forecast_results.tsv' "
        "WITH (FORMAT csv, DELIMITER E'\\t', HEADER);"
    )
    result = run_psql(copy_sql)
    if "COPY" in result:
        nums = [x for x in result.split() if x.isdigit()]
        print(f"  Loaded {nums[0] if nums else '?'} rows into forecast_results ✓")
    else:
        print("  [WARN] Unexpected COPY response:")
        print("  " + result[:500])


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────


def main():
    print("=" * 70)
    print("  BDA FORECAST RETRAINER v3")
    print(
        f"  Window : {FORECAST_START.date()} → {FORECAST_END.date()} "
        f"({FORECAST_MONTHS} months)"
    )
    print(
        f"  Spike months excluded from training: "
        + ", ".join(d.strftime("%Y-%m") for d in SPIKE_MONTHS)
    )
    print("=" * 70)

    # 1. Load
    print("\n[1] Loading data from Postgres...")
    df_skill = load_skill_demand()
    df_jobs = load_job_listings()
    print(f"    Skill demand rows : {len(df_skill):,}")
    print(f"    Job listing months: {len(df_jobs)}")

    if df_skill.empty:
        print("[ERROR] No skill demand data — is Postgres running?")
        sys.exit(1)

    # 2. EDA
    print("\n[2] Running EDA...")
    eda_skill_demand(df_skill)
    eda_job_listings(df_jobs)

    # 3. Skill demand forecasts
    print("\n[3] Training skill demand models...")
    df_skill_fc = process_skill_demand(df_skill)

    # 4. Job listings forecast
    print("\n[4] Training job listings model...")
    print("\n" + "=" * 70)
    print("  TRAINING — JOB LISTINGS")
    print("=" * 70)
    jl_fc = forecast_job_listings(df_jobs)

    # 5. Push skill forecasts to DB
    print("\n[5] Pushing skill forecasts to Postgres...")
    push_to_db(df_skill_fc)

    # 6. Save job listings JSON
    jl_path = "job_listings_forecast.json"
    with open(jl_path, "w", encoding="utf-8") as f:
        json.dump(jl_fc, f, indent=2)
    print(
        f"\n[6] Saved {jl_path} "
        f"({len(jl_fc['historical'])} historical, "
        f"{len(jl_fc['predicted'])} predicted points)"
    )

    print("\n" + "=" * 70)
    print("  DONE — restart the ML service to pick up new forecasts")
    print("=" * 70)


if __name__ == "__main__":
    main()
