import os
import sys
from datetime import date, timedelta
from collections import defaultdict

import pandas as pd
import numpy as np

# Paths
DATA_DIR = r"C:\Users\Noodl\Projects\BDA\data"
SYNTHETIC_DATA_PATH = r"C:\Users\Noodl\Projects\BDA\data\synthetic_job_skills.csv"
SEED_DIR = r"C:\Users\Noodl\Projects\BDA\backend\database\seed"

FORECAST_END = date(2027, 12, 1)
MIN_DATA_POINTS = 6
MIN_DATE_SPAN_MONTHS = 12


def load_real_data():
    """
    Try to load real dataset from data/ directory.
    Detects available CSV/XLSX files and parses flexibly.
    Returns (df, source_name) or (None, None) if failed.
    """
    try:
        candidates = []
        for fname in os.listdir(DATA_DIR):
            fpath = os.path.join(DATA_DIR, fname)
            if os.path.isfile(fpath) and fname.endswith(('.csv', '.xlsx')):
                candidates.append((fname, fpath))
        
        if not candidates:
            return None, None
        
        print(f"  Found {len(candidates)} potential data files")
        
        # Try each candidate
        for fname, fpath in sorted(candidates):
            try:
                print(f"  Trying {fname}...", end=" ")
                
                # Read file
                if fname.endswith('.xlsx'):
                    df = pd.read_excel(fpath)
                else:
                    df = pd.read_csv(fpath)
                
                if len(df) == 0:
                    print("empty, skipped")
                    continue
                
                # Try to identify date column (flexible parsing)
                date_col = None
                for col in df.columns:
                    if any(x in col.lower() for x in ['date', 'period', 'time', 'month', 'year']):
                        try:
                            pd.to_datetime(df[col], errors='coerce')
                            date_col = col
                            break
                        except:
                            pass
                
                if date_col is None:
                    print("no date column found, skipped")
                    continue
                
                # Parse dates and check span
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                df = df.dropna(subset=[date_col])
                
                if len(df) < MIN_DATA_POINTS:
                    print(f"insufficient rows ({len(df)}), skipped")
                    continue
                
                date_min = df[date_col].min()
                date_max = df[date_col].max()
                month_span = (date_max.year - date_min.year) * 12 + (date_max.month - date_min.month)
                
                if month_span < MIN_DATE_SPAN_MONTHS:
                    print(f"date span too short ({month_span} months), skipped")
                    continue
                
                # Find skill/demand columns (flexible)
                skill_col = None
                demand_col = None
                
                for col in df.columns:
                    col_lower = col.lower()
                    if any(x in col_lower for x in ['skill', 'technology', 'tool', 'requirement', 'description', 'title']):
                        skill_col = col
                    if any(x in col_lower for x in ['demand', 'count', 'frequency', 'occurrences', 'total']):
                        demand_col = col
                
                if skill_col is None or demand_col is None:
                    print(f"missing skill/demand columns, skipped")
                    continue
                
                # Validate and prepare
                df_clean = df[[date_col, skill_col, demand_col]].copy()
                df_clean.columns = ['period_start', 'skill_name', 'demand_count']
                df_clean['skill_name'] = df_clean['skill_name'].astype(str).str.strip()
                df_clean['demand_count'] = pd.to_numeric(df_clean['demand_count'], errors='coerce')
                df_clean = df_clean.dropna()
                
                if len(df_clean) < MIN_DATA_POINTS:
                    print(f"insufficient valid rows, skipped")
                    continue
                
                # Resample to monthly if needed
                df_clean['period_start'] = pd.to_datetime(df_clean['period_start'])
                df_clean = df_clean.sort_values('period_start')
                df_clean = df_clean.groupby([pd.Grouper(key='period_start', freq='MS'), 'skill_name'])['demand_count'].sum().reset_index()
                
                # Add missing columns for compatibility
                df_clean['period_end'] = df_clean['period_start'] + pd.offsets.MonthEnd(0)
                df_clean['region'] = 'Global'
                df_clean['industry'] = 'General'
                
                print(f"loaded {len(df_clean)} rows, {df_clean['skill_name'].nunique()} skills, span {month_span} months")
                return df_clean, fname
            
            except Exception as e:
                print(f"error: {e}")
                continue
        
        return None, None
    
    except Exception as e:
        print(f"  Real data load error: {e}")
        return None, None


def load_synthetic_fallback():
    """Load synthetic fallback data from synthetic_job_skills.csv"""
    try:
        df = pd.read_csv(SYNTHETIC_DATA_PATH)
        df['period_start'] = pd.to_datetime(df['period_start'])
        df['period_end'] = pd.to_datetime(df['period_end'])
        return df, "synthetic_job_skills.csv (fallback)"
    except Exception as e:
        print(f"ERROR: Failed to load synthetic fallback: {e}")
        return None, None


def forecast_skill_sarima(dates, counts, skill_name):
    """Forecast using SARIMA(1,1,1)(1,1,1,12) with 12-month seasonality"""
    if len(counts) < MIN_DATA_POINTS:
        return None
    
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX
        from warnings import filterwarnings
        filterwarnings('ignore')
        
        series = pd.Series(counts, index=pd.to_datetime(dates))
        series = series.sort_index()
        series = series.resample('MS').sum().fillna(0)
        
        last_date = series.index[-1].date()
        if last_date >= FORECAST_END:
            return None
        
        # Calculate forecast steps
        n_steps = 0
        d = last_date
        while d < FORECAST_END:
            n_steps += 1
            if d.month == 12:
                d = date(d.year + 1, 1, 1)
            else:
                d = date(d.year, d.month + 1, 1)
        
        if n_steps <= 0:
            return None
        
        # SARIMA(1,1,1)(1,1,1,12) - captures trend and yearly seasonality
        try:
            model = SARIMAX(
                series,
                order=(1, 1, 1),
                seasonal_order=(1, 1, 1, 12),
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            result = model.fit(disp=False, maxiter=200)
            
            # Forecast with confidence intervals
            forecast_obj = result.get_forecast(steps=n_steps)
            fc = forecast_obj.predicted_mean
            ci = forecast_obj.conf_int(alpha=0.05)
            
            rows = []
            for i, dt in enumerate(fc.index):
                val = max(0.0, float(fc.iloc[i]))
                lower = max(0.0, float(ci.iloc[i, 0]))
                upper = max(val, float(ci.iloc[i, 1]))
                rows.append(
                    f"{skill_name}\t{dt.strftime('%Y-%m-%d')}\t{val:.2f}\t"
                    f"{lower:.2f}\t{upper:.2f}\tSARIMA(1,1,1)(1,1,1,12)\tGlobal"
                )
            return rows
        except Exception as e:
            # Fallback to simpler model if SARIMA fails
            print(f"    SARIMA failed for {skill_name}: {e}, trying ARIMA...")
            from statsmodels.tsa.arima.model import ARIMA
            model = ARIMA(series, order=(1, 1, 1))
            result = model.fit()
            forecast_obj = result.get_forecast(steps=n_steps)
            fc = forecast_obj.predicted_mean
            ci = forecast_obj.conf_int(alpha=0.05)
            
            rows = []
            for i, dt in enumerate(fc.index):
                val = max(0.0, float(fc.iloc[i]))
                lower = max(0.0, float(ci.iloc[i, 0]))
                upper = max(val, float(ci.iloc[i, 1]))
                rows.append(
                    f"{skill_name}\t{dt.strftime('%Y-%m-%d')}\t{val:.2f}\t"
                    f"{lower:.2f}\t{upper:.2f}\tARIMA(1,1,1)\tGlobal"
                )
            return rows
    except Exception as e:
        print(f"    Forecast failed for {skill_name}: {e}")
        return None


def forecast_job_listings_sarima(dates, counts):
    """Forecast total job listings using SARIMA"""
    if len(counts) < MIN_DATA_POINTS:
        return None
    
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX
        from warnings import filterwarnings
        filterwarnings('ignore')
        
        series = pd.Series(counts, index=pd.to_datetime(dates))
        series = series.sort_index()
        series = series.resample('MS').sum().fillna(0)
        
        last_date = series.index[-1].date()
        if last_date >= FORECAST_END:
            return None
        
        n_steps = 0
        d = last_date
        while d < FORECAST_END:
            n_steps += 1
            if d.month == 12:
                d = date(d.year + 1, 1, 1)
            else:
                d = date(d.year, d.month + 1, 1)
        
        if n_steps <= 0:
            return None
        
        try:
            model = SARIMAX(
                series,
                order=(1, 1, 1),
                seasonal_order=(1, 1, 1, 12),
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            result = model.fit(disp=False, maxiter=200)
            forecast_obj = result.get_forecast(steps=n_steps)
            fc = forecast_obj.predicted_mean
            ci = forecast_obj.conf_int(alpha=0.05)

            rows = []
            for i, dt in enumerate(fc.index):
                val = max(0.0, float(fc.iloc[i]))
                lower = max(0.0, float(ci.iloc[i, 0]))
                upper = max(val, float(ci.iloc[i, 1]))
                rows.append(
                    f"(job_listings_total)\t{dt.strftime('%Y-%m-%d')}\t{val:.2f}\t"
                    f"{lower:.2f}\t{upper:.2f}\tSARIMA(1,1,1)(1,1,1,12)\tGlobal"
                )
            return rows
        except Exception as e:
            print(f"    SARIMA failed for job_listings: {e}, trying ARIMA...")
            from statsmodels.tsa.arima.model import ARIMA
            model = ARIMA(series, order=(1, 1, 1))
            result = model.fit()
            forecast_obj = result.get_forecast(steps=n_steps)
            fc = forecast_obj.predicted_mean
            ci = forecast_obj.conf_int(alpha=0.05)

            rows = []
            for i, dt in enumerate(fc.index):
                val = max(0.0, float(fc.iloc[i]))
                lower = max(0.0, float(ci.iloc[i, 0]))
                upper = max(val, float(ci.iloc[i, 1]))
                rows.append(
                    f"(job_listings_total)\t{dt.strftime('%Y-%m-%d')}\t{val:.2f}\t"
                    f"{lower:.2f}\t{upper:.2f}\tARIMA(1,1,1)\tGlobal"
                )
            return rows
    except Exception as e:
        print(f"    Forecast failed for job_listings: {e}")
        return None


def main():
    os.makedirs(SEED_DIR, exist_ok=True)
    
    print("=" * 70)
    print("Starting ETL Pipeline")
    print("=" * 70)
    
    # Try real data first, fallback to synthetic
    print("\n[STEP 1] Loading data...")
    print("Trying real data sources...")
    df, data_source = load_real_data()
    
    if df is None or len(df) == 0:
        print("Real data unavailable or invalid, using synthetic fallback...")
        df, data_source = load_synthetic_fallback()
        
        if df is None or len(df) == 0:
            print("ERROR: Both real and synthetic data sources failed!")
            sys.exit(1)
    
    print(f"\n[DATA SOURCE] {data_source}")
    print(f"[ROWS] {len(df):,}")
    print(f"[SKILLS] {df['skill_name'].nunique()}")
    print(f"[DATE RANGE] {df['period_start'].min().strftime('%Y-%m-%d')} to {df['period_start'].max().strftime('%Y-%m-%d')}")
    
    # Group by skill and month for skill_demand.tsv
    skill_data = df.copy()
    skill_data['period_start'] = pd.to_datetime(skill_data['period_start'])
    skill_data = skill_data.sort_values('period_start')
    
    # Write skill_demand.tsv
    print("\n[STEP 2] Writing skill_demand.tsv...")
    skill_demand_path = os.path.join(SEED_DIR, "skill_demand.tsv")
    with open(skill_demand_path, "w", encoding="utf-8") as f:
        for _, row in skill_data.iterrows():
            f.write(
                f"{row['skill_name']}\t{row['demand_count']}\t{row['period_start']}\t"
                f"{row['period_end']}\t{row['region']}\t{row['industry']}\n"
            )
    print(f"[OK] skill_demand.tsv ({len(skill_data):,} rows)")
    
    # Calculate total job listings per month for job_listings.tsv
    print("\n[STEP 3] Writing job_listings.tsv...")
    job_listings_data = []
    for _, row in skill_data.iterrows():
        job_listings_data.append({
            'period_start': row['period_start'],
            'period_end': row['period_end'],
            'demand_count': row['demand_count']
        })
    
    df_jobs = pd.DataFrame(job_listings_data)
    df_jobs = df_jobs.groupby('period_start').agg({
        'demand_count': 'sum',
        'period_end': 'first'
    }).reset_index()
    df_jobs = df_jobs.rename(columns={'demand_count': 'count'})
    
    job_listings_path = os.path.join(SEED_DIR, "job_listings.tsv")
    with open(job_listings_path, "w", encoding="utf-8") as f:
        for _, row in df_jobs.iterrows():
            for i in range(max(1, int(row['count'] / 50))):
                f.write(
                    f"Job Title {i}\tMock Company\tRemote\t50000\t100000\t"
                    f"USD\t{data_source}\tjob_{row['period_start'].strftime('%Y%m%d')}_{i}\t"
                    f"{row['period_start'].strftime('%Y-%m-%d')}\tFT\tMI\t"
                    f"General\tt\tPython,SQL\n"
                )
    print(f"[OK] job_listings.tsv ({len(df_jobs)} months)")
    
    # Pre-compute forecasts with SARIMA
    print("\n[STEP 4] Pre-computing SARIMA forecasts...")
    forecast_rows = []
    
    # Skill forecasts
    for skill in sorted(df['skill_name'].unique()):
        skill_df = df[df['skill_name'] == skill].copy()
        skill_df['period_start'] = pd.to_datetime(skill_df['period_start'])
        skill_df = skill_df.sort_values('period_start')
        dates = skill_df['period_start'].dt.strftime('%Y-%m-%d').tolist()
        counts = skill_df['demand_count'].tolist()
        result = forecast_skill_sarima(dates, counts, skill)
        if result:
            forecast_rows.extend(result)
            print(f"  [OK] {skill}: {len(result)} months")
        else:
            print(f"  [SKIP] {skill}")
    
    # Job listings total forecast
    jl_dates = df_jobs['period_start'].dt.strftime('%Y-%m-%d').tolist()
    jl_counts = df_jobs['count'].tolist()
    jl_result = forecast_job_listings_sarima(jl_dates, jl_counts)
    if jl_result:
        forecast_rows.extend(jl_result)
        print(f"  [OK] job_listings_total: {len(jl_result)} months")
    
    forecast_path = os.path.join(SEED_DIR, "forecast_results.tsv")
    with open(forecast_path, "w", encoding="utf-8") as f:
        for row in forecast_rows:
            f.write(row + "\n")
    print(f"[OK] forecast_results.tsv ({len(forecast_rows):,} points)")
    
    print("\n" + "=" * 70)
    print("ETL Pipeline Complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
