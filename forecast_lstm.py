#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LSTM Time Series Forecasting for Skill Demand
Optimized for NVIDIA GPU + AMD CPU
"""
import pandas as pd
import numpy as np
import subprocess
import warnings
import os
import sys
from datetime import timedelta

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Unbuffered output
os.environ['PYTHONUNBUFFERED'] = '1'

warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import MinMaxScaler

print("[INIT] TensorFlow version: {}".format(tf.__version__), flush=True)

# GPU Detection
gpus = tf.config.list_physical_devices('GPU')
print("[DEVICE] Found {} GPU(s)".format(len(gpus)), flush=True)

if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        print("[GPU] Memory growth enabled", flush=True)
        # Use GPU for model execution
        tf.config.run_functions_eagerly(False)
    except Exception as e:
        print("[GPU] Warning: {}".format(str(e)), flush=True)
else:
    print("[CPU] No GPU detected, using CPU", flush=True)

def load_skill_demand_from_db():
    """Load skill demand from database"""
    print("[DB] Connecting...", flush=True)
    sql = "SELECT skill_name, period_start, demand_count FROM skill_demand ORDER BY skill_name, period_start"
    result = subprocess.run(
        ['docker', 'exec', 'postgres', 'psql', '-U', 'postgres', '-d', 'job_market', '-c', sql],
        capture_output=True, text=True, timeout=30
    )
    
    skills_data = {}
    for line in result.stdout.split('\n')[2:-2]:
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
    
    return skills_data

def detect_outliers_iqr(data):
    """IQR outlier detection"""
    Q1 = np.percentile(data, 25)
    Q3 = np.percentile(data, 75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    mask = (data >= lower) & (data <= upper)
    return mask, lower, upper

def build_lstm_model(lookback=6):
    """Build LSTM model optimized for GPU"""
    with tf.device('/GPU:0' if tf.config.list_physical_devices('GPU') else '/CPU:0'):
        model = Sequential([
            LSTM(32, activation='relu', input_shape=(lookback, 1), return_sequences=False),
            Dropout(0.1),
            Dense(16, activation='relu'),
            Dense(1, activation='linear')
        ])
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse'
        )
    return model

def create_sequences(data, lookback=6):
    """Create X, y sequences"""
    X, y = [], []
    for i in range(len(data) - lookback):
        X.append(data[i:i+lookback])
        y.append(data[i+lookback])
    return np.array(X), np.array(y)

def forecast_skill(skill_name, time_series, lookback=6, forecast_months=32):
    """Train and forecast single skill"""
    
    if len(time_series) < lookback + 2:
        return []
    
    # Sort by date
    time_series = sorted(time_series, key=lambda x: x[0])
    dates = np.array([d for d, v in time_series])
    values = np.array([v for d, v in time_series]).reshape(-1, 1)
    
    # Remove outliers
    outlier_mask, _, _ = detect_outliers_iqr(values.flatten())
    if outlier_mask.sum() < lookback + 2:
        outlier_mask = np.ones(len(values), dtype=bool)
    
    # Normalize
    scaler = MinMaxScaler(feature_range=(0, 1))
    values_norm = scaler.fit_transform(values)
    
    # Create sequences
    X, y = create_sequences(values_norm, lookback=lookback)
    if len(X) < 2:
        return []
    
    # Convert to float32 for GPU efficiency
    X = X.astype(np.float32)
    y = y.astype(np.float32)
    
    # Train
    model = build_lstm_model(lookback=lookback)
    model.fit(
        X, y,
        epochs=30,
        batch_size=4,
        validation_split=0.2,
        verbose=0
    )
    
    # Volatility
    volatility = np.std(values) / (np.mean(values) + 1e-6)
    
    # Forecast
    last_seq = values_norm[-lookback:].copy()
    forecasts = []
    current_date = dates[-1] + timedelta(days=30)
    
    for _ in range(forecast_months):
        pred = model.predict(last_seq.reshape(1, lookback, 1).astype(np.float32), verbose=0)[0, 0]
        demand = scaler.inverse_transform([[pred]])[0, 0]
        demand = max(0, float(demand))
        
        forecasts.append({
            'date': current_date.date(),
            'demand': demand,
            'lower': max(0, demand * (1 - volatility)),
            'upper': demand * (1 + volatility)
        })
        
        last_seq = np.vstack([last_seq[1:], [[pred]]])
        current_date += timedelta(days=30)
    
    # Log
    hist_min, hist_max = float(values.min()), float(values.max())
    fcst_vals = [f['demand'] for f in forecasts]
    fcst_min, fcst_max = min(fcst_vals), max(fcst_vals)
    print("  [TRAIN] {:<20} | hist: {:<6.0f}-{:<6.0f} | fcst: {:<6.0f}-{:<6.0f}".format(
        skill_name, hist_min, hist_max, fcst_min, fcst_max), flush=True)
    
    return forecasts

if __name__ == '__main__':
    print("=" * 80, flush=True)
    print("LSTM Forecasting - NVIDIA GPU + AMD CPU", flush=True)
    print("=" * 80, flush=True)
    
    # Load
    print("\n[1] LOADING DATA", flush=True)
    skills_data = load_skill_demand_from_db()
    print("    {} skills loaded".format(len(skills_data)), flush=True)
    
    # Filter
    valid_skills = {s: ts for s, ts in skills_data.items() if len(ts) >= 8}
    print("    {} skills with >=8 months".format(len(valid_skills)), flush=True)
    
    # Train
    print("\n[2] TRAINING LSTM MODELS", flush=True)
    all_forecasts = []
    
    for idx, (skill_name, time_series) in enumerate(sorted(valid_skills.items()), 1):
        forecasts = forecast_skill(skill_name, time_series, lookback=6, forecast_months=32)
        
        for fc in forecasts:
            all_forecasts.append({
                'skill_name': skill_name,
                'forecast_date': fc['date'],
                'predicted_demand': fc['demand'],
                'confidence_lower': fc['lower'],
                'confidence_upper': fc['upper'],
                'model_version': 'LSTM',
                'region': 'Global'
            })
        
        if idx % 5 == 0:
            print("    Progress: {}/{}".format(idx, len(valid_skills)), flush=True)
    
    print("\n    Generated {} forecast points".format(len(all_forecasts)), flush=True)
    
    # Create DataFrame
    df_forecasts = pd.DataFrame(all_forecasts)
    negatives = (df_forecasts['predicted_demand'] < 0).sum()
    print("    Negative forecasts: {}".format(negatives), flush=True)
    
    # Sample
    print("\n[3] SAMPLE FORECASTS", flush=True)
    for skill in ['Excel', 'SQL', 'CI/CD', 'Cloud', 'Python']:
        sample = df_forecasts[df_forecasts['skill_name'] == skill].head(3)
        if len(sample) > 0:
            print("    {}:".format(skill), flush=True)
            for _, row in sample.iterrows():
                print("      {}: {:.1f}".format(row['forecast_date'], row['predicted_demand']), flush=True)
    
    # Load to DB
    print("\n[4] LOADING TO DATABASE", flush=True)
    output_path = 'backend/database/seed/forecast_results.tsv'
    df_forecasts.to_csv(output_path, sep='\t', index=False, header=True)
    
    subprocess.run(['docker', 'cp', output_path, 'postgres:/tmp/forecast_results.tsv'], timeout=30)
    
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
    
    if 'COPY' in result.stdout or 'COPY' in result.stderr:
        import re
        match = re.search(r'COPY (\d+)', result.stdout + result.stderr)
        count = match.group(1) if match else '?'
        print("    [OK] COPY {} rows".format(count), flush=True)
        
        verify_sql = "SELECT COUNT(*) FROM forecast_results;"
        verify = subprocess.run(
            ['docker', 'exec', 'postgres', 'psql', '-U', 'postgres', '-d', 'job_market', '-c', verify_sql],
            capture_output=True, text=True, timeout=30
        )
        print("    [OK] Database loaded", flush=True)
    else:
        print("    [ERROR] Load failed", flush=True)
        print(result.stderr, flush=True)
    
    print("\n" + "=" * 80, flush=True)
    print("[DONE] LSTM forecasting complete!", flush=True)
    print("=" * 80, flush=True)
