#!/usr/bin/env python3
"""
Replace SARIMA with simple trend-following forecasts.
For each skill, calculate slope from last 6 months and extrapolate.
"""
import pandas as pd
import subprocess
from datetime import datetime, timedelta
import numpy as np

def run_sql(sql):
    result = subprocess.run(
        ['docker', 'exec', 'postgres', 'psql', '-U', 'postgres', '-d', 'job_market', '-c', sql],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout

# Get all historical data
print("Loading historical skill demand...")
sql = """
SELECT skill_name, period_start, demand_count 
FROM skill_demand 
ORDER BY skill_name, period_start
"""
output = run_sql(sql)

# Parse into dict
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

print(f"Loaded {len(skills_data)} skills")

# Generate forecasts
forecasts = []
base_date = pd.to_datetime('2025-05-01')  # Start from actual data end

for skill, data in skills_data.items():
    if len(data) < 2:
        continue
    
    data.sort()
    
    # Get last 6 months of data
    recent_cutoff = data[-1][0] - timedelta(days=180)
    recent_data = [(d, v) for d, v in data if d >= recent_cutoff]
    
    if len(recent_data) < 2:
        recent_data = data[-3:] if len(data) >= 3 else data
    
    # Calculate trend (slope) using linear regression
    x = np.array([(d - recent_data[0][0]).days for d, v in recent_data])
    y = np.array([v for d, v in recent_data])
    
    slope = (y[-1] - y[0]) / (x[-1] - x[0]) if x[-1] != x[0] else 0
    intercept = y[-1] - slope * x[-1]
    
    # Last known value
    last_date, last_value = data[-1]
    
    print(f"{skill:20} | hist_range: {y.min():.0f}-{y.max():.0f} | recent_slope: {slope:.2f}/day | last: {last_value:.0f}")
    
    # Forecast for next 32 months (May 2025 - Dec 2027)
    current_date = base_date
    for month_offset in range(32):
        forecast_date = base_date + timedelta(days=30*month_offset)
        days_ahead = (forecast_date - last_date).days
        
        # Linear extrapolation
        forecast_value = last_value + slope * days_ahead
        
        # Never go negative
        forecast_value = max(0, forecast_value)
        
        # Bound to recent range + 20% growth max
        recent_max = y.max()
        forecast_value = min(forecast_value, recent_max * 1.2)
        
        # Add confidence bounds (±30%)
        conf_lower = max(0, forecast_value * 0.7)
        conf_upper = forecast_value * 1.3
        
        forecasts.append({
            'skill_name': skill,
            'forecast_date': forecast_date.date(),
            'predicted_demand': forecast_value,
            'confidence_lower': conf_lower,
            'confidence_upper': conf_upper,
            'model': 'TrendFollowing',
            'region': 'Global'
        })

# Create DataFrame and load into DB
df_forecasts = pd.DataFrame(forecasts)

print(f"\nGenerated {len(df_forecasts)} forecasts")
print(f"Sample:")
print(df_forecasts[df_forecasts['skill_name']=='Excel'].head(10))

# Write to TSV
df_forecasts.to_csv('backend/database/seed/forecast_results.tsv', 
                     sep='\t', index=False, header=True)

# Load into DB
print("\nLoading into database...")
subprocess.run([
    'docker', 'cp', 
    'backend/database/seed/forecast_results.tsv',
    'postgres:/tmp/forecast_results.tsv'
], timeout=30)

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
print(result.stdout)
print("Done!")
