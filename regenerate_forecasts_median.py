#!/usr/bin/env python3
"""
Generate forecasts using median baseline approach.
More robust than percentile-based, handles outliers better.
"""
import pandas as pd
import subprocess
import numpy as np
from datetime import timedelta

def run_sql(sql):
    result = subprocess.run(
        ['docker', 'exec', 'postgres', 'psql', '-U', 'postgres', '-d', 'job_market', '-c', sql],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout

# Load historical data
print("Loading historical skill demand...")
sql = """SELECT skill_name, period_start, demand_count FROM skill_demand ORDER BY skill_name, period_start"""
output = run_sql(sql)

skills_data = {}
for line in output.split('\n')[2:-2]:
    if '|' not in line:
        continue
    parts = [p.strip() for p in line.split('|')]
    if len(parts) >= 3 and parts[0] and parts[1]:
        try:
            skill = parts[0]
            date = pd.to_datetime(parts[1])
            demand = float(parts[2])
            
            if skill not in skills_data:
                skills_data[skill] = []
            skills_data[skill].append((date, demand))
        except:
            continue

print(f"Loaded {len(skills_data)} skills\n")

forecasts = []
base_date = pd.to_datetime('2025-05-01')
np.random.seed(42)

for skill, data in skills_data.items():
    if len(data) < 2:
        continue
    
    data.sort()
    values = np.array([v for d, v in data])
    
    # Use IQR (Interquartile Range) method to identify outliers
    q1 = np.percentile(values, 25)
    q3 = np.percentile(values, 75)
    iqr = q3 - q1
    
    # Remove extreme outliers (beyond 3x IQR)
    lower_bound = q1 - 3 * iqr
    upper_bound = q3 + 3 * iqr
    
    stable_vals = [v for v in values if lower_bound <= v <= upper_bound]
    
    if not stable_vals:
        stable_vals = values
    
    # Use median of stable values as baseline
    baseline = np.median(stable_vals)
    
    # Use mean of last 3-5 months to weight recent data
    recent_vals = values[-min(5, len(values)):]
    recent_median = np.median(recent_vals)
    
    # Blend them: 60% historical baseline + 40% recent
    forecast_baseline = baseline * 0.6 + recent_median * 0.4
    
    # Calculate trend across full history
    dates = [d for d, v in data]
    x = np.array([(d - dates[0]).days for d in dates])
    y = values
    slope = (y[-1] - y[0]) / (x[-1] - x[0]) if x[-1] > 0 else 0
    
    print(f"{skill:20} | hist: {min(values):7.0f}-{max(values):7.0f} | baseline: {baseline:7.0f} | recent: {recent_median:7.0f} | blend: {forecast_baseline:7.0f}")
    
    # Generate 32 months of forecasts
    for month_offset in range(32):
        forecast_date = base_date + timedelta(days=30 * month_offset)
        
        # Add seasonal variation + small trend
        seasonal = forecast_baseline * (0.9 + 0.2 * np.sin(2 * np.pi * month_offset / 12))
        trend_component = slope * (month_offset * 30) * 0.1  # Damped trend
        
        forecast_value = seasonal + trend_component
        forecast_value = max(0, forecast_value)
        
        # Cap to reasonable range (baseline ±30% to allow growth/decline)
        forecast_value = np.clip(forecast_value, forecast_baseline * 0.7, forecast_baseline * 1.3)
        
        conf_lower = max(0, forecast_value * 0.85)
        conf_upper = forecast_value * 1.15
        
        forecasts.append({
            'skill_name': skill,
            'forecast_date': forecast_date.date(),
            'predicted_demand': forecast_value,
            'confidence_lower': conf_lower,
            'confidence_upper': conf_upper,
            'model': 'MedianBaseline',
            'region': 'Global'
        })

df_forecasts = pd.DataFrame(forecasts)

print(f"\nGenerated {len(df_forecasts)} forecasts\n")
print("Sample forecasts:")
for skill in ['Excel', 'SQL', 'CI/CD']:
    sample = df_forecasts[df_forecasts['skill_name']==skill].head(3)
    if len(sample) > 0:
        print(f"{skill}:")
        for _, row in sample.iterrows():
            print(f"  {row['forecast_date']}: {row['predicted_demand']:.0f}")

# Load into database
df_forecasts.to_csv('backend/database/seed/forecast_results.tsv', sep='\t', index=False, header=True)

print("\nLoading into database...")
subprocess.run(['docker', 'cp', 'backend/database/seed/forecast_results.tsv', 'postgres:/tmp/forecast_results.tsv'], timeout=30)

load_sql = """
TRUNCATE forecast_results CASCADE;
COPY forecast_results (skill_name, forecast_date, confidence_lower, confidence_upper, predicted_demand, model_version, region)
FROM '/tmp/forecast_results.tsv'
WITH (FORMAT csv, DELIMITER E'\\t', HEADER);
"""
result = subprocess.run(
    ['docker', 'exec', 'postgres', 'psql', '-U', 'postgres', '-d', 'job_market', '-c', load_sql],
    capture_output=True, text=True, timeout=30
)

if 'COPY' in result.stdout:
    print(result.stdout.strip())
    
    # Verify
    verify = run_sql("SELECT COUNT(*) FROM forecast_results WHERE predicted_demand < 0;")
    print(f"Negative forecasts: {verify.split()[2]}")
else:
    print("Error loading forecasts")
    print(result.stderr)
