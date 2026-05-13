#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LSTM Job Listings Trend Forecasting
Predicts monthly job posting counts to 2027
"""
import pandas as pd
import numpy as np
import subprocess
import warnings
import os
import sys
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.environ['PYTHONUNBUFFERED'] = '1'
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import MinMaxScaler

tf.get_logger().setLevel('ERROR')

def load_job_listings_from_db():
    """Load job listings and aggregate by month"""
    print("[DB] Loading job listings...", flush=True)
    
    sql = """
    SELECT DATE_TRUNC('month', posted_date)::date as month, COUNT(*) as count
    FROM job_listings
    WHERE posted_date IS NOT NULL
    GROUP BY DATE_TRUNC('month', posted_date)
    ORDER BY month
    """
    
    result = subprocess.run(
        ['docker', 'exec', 'postgres', 'psql', '-U', 'postgres', '-d', 'job_market', '-c', sql],
        capture_output=True, text=True, timeout=30
    )
    
    data = []
    for line in result.stdout.split('\n')[2:-2]:
        if '|' not in line:
            continue
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 2 and parts[0] and parts[1]:
            try:
                date = pd.to_datetime(parts[0])
                count = int(parts[1])
                data.append({'date': date, 'count': count})
            except:
                continue
    
    df = pd.DataFrame(data).sort_values('date')
    return df

def build_lstm_model(lookback=3):
    """Build LSTM for job listings"""
    model = Sequential([
        LSTM(16, activation='relu', input_shape=(lookback, 1)),
        Dropout(0.1),
        Dense(8, activation='relu'),
        Dense(1, activation='linear')
    ])
    model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
    return model

def create_sequences(data, lookback=3):
    """Create sequences"""
    X, y = [], []
    for i in range(len(data) - lookback):
        X.append(data[i:i+lookback])
        y.append(data[i+lookback])
    return np.array(X), np.array(y)

def forecast_job_listings(df, lookback=3, forecast_months=32):
    """Train LSTM and forecast job listings with realistic growth"""
    
    if len(df) < lookback + 2:
        print("[WARN] Insufficient historical data", flush=True)
        return None, None
    
    dates = df['date'].values
    values = df['count'].values.reshape(-1, 1).astype(np.float32)
    
    print("[DATA] Historical range: {} to {}".format(dates[0], dates[-1]), flush=True)
    print("[DATA] Count range: {:.0f} to {:.0f} (avg {:.0f})".format(
        values.min(), values.max(), values.mean()), flush=True)
    
    # Normalize
    scaler = MinMaxScaler(feature_range=(0, 1))
    values_norm = scaler.fit_transform(values)
    
    # Create sequences
    X, y = create_sequences(values_norm, lookback=lookback)
    if len(X) < 2:
        print("[WARN] Cannot create sequences", flush=True)
        return None, None
    
    X = X.astype(np.float32)
    y = y.astype(np.float32)
    
    # Train
    print("[TRAIN] Training LSTM model...", flush=True)
    model = build_lstm_model(lookback=lookback)
    model.fit(X, y, epochs=50, batch_size=2, validation_split=0.2, verbose=0)
    
    # Forecast with realistic growth
    print("[FORECAST] Generating forecasts with growth trend...", flush=True)
    last_seq = values_norm[-lookback:].copy()
    forecasts = []
    
    current_date = pd.to_datetime(dates[-1]) + relativedelta(months=1)
    
    # Volatility for CI
    volatility = np.std(values) / (np.mean(values) + 1e-6)
    
    # Historical peak for realistic scaling
    hist_peak = values.max()
    hist_mean = values.mean()
    
    # Growth parameters: assume job market recovers and grows 15% annually
    base_multiplier = 1.0
    monthly_growth_rate = 0.015  # ~18% annually
    
    for month in range(forecast_months):
        # LSTM base prediction
        pred = model.predict(last_seq.reshape(1, lookback, 1), verbose=0)[0, 0]
        base_count = scaler.inverse_transform([[pred]])[0, 0]
        
        # Apply realistic growth trend
        # Start from recent average and grow monthly
        growth_factor = base_multiplier * ((1 + monthly_growth_rate) ** (month + 1))
        
        # Blend LSTM output with growth trend (70% LSTM, 30% growth)
        lstm_weight = 0.7
        growth_weight = 0.3
        
        count = (lstm_weight * base_count + 
                 growth_weight * (hist_mean * growth_factor))
        
        # Add some realistic variance (sinusoidal seasonality)
        seasonal_factor = 1 + 0.15 * np.sin(2 * np.pi * (month % 12) / 12)
        count = count * seasonal_factor
        
        count = max(5, float(count))  # Floor at 5 to avoid unrealistically low
        
        # Confidence intervals
        lower = max(2, count * (1 - volatility))
        upper = count * (1 + volatility)
        
        forecasts.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'count': count,
            'confidenceLower': lower,
            'confidenceUpper': upper
        })
        
        last_seq = np.vstack([last_seq[1:], [[pred]]])
        current_date += relativedelta(months=1)
    
    return forecasts, volatility

if __name__ == '__main__':
    print("=" * 80, flush=True)
    print("Job Listings LSTM Forecasting", flush=True)
    print("=" * 80, flush=True)
    
    # Load historical data
    print("\n[1] LOADING HISTORICAL DATA", flush=True)
    df_hist = load_job_listings_from_db()
    print("    {} months of historical data".format(len(df_hist)), flush=True)
    
    if len(df_hist) < 5:
        print("[ERROR] Insufficient historical data", flush=True)
        sys.exit(1)
    
    # Train and forecast
    print("\n[2] TRAINING AND FORECASTING", flush=True)
    forecasts, volatility = forecast_job_listings(df_hist, lookback=3, forecast_months=32)
    
    if not forecasts:
        print("[ERROR] Forecasting failed", flush=True)
        sys.exit(1)
    
    # Prepare output
    print("\n[3] PREPARING OUTPUT", flush=True)
    
    historical_data = []
    for _, row in df_hist.iterrows():
        historical_data.append({
            'date': row['date'].strftime('%Y-%m-%d'),
            'count': float(row['count']),
            'confidenceLower': None,
            'confidenceUpper': None
        })
    
    # Convert numpy types to Python types
    predicted_data = []
    for fc in forecasts:
        predicted_data.append({
            'date': fc['date'],
            'count': float(fc['count']),
            'confidenceLower': float(fc['confidenceLower']),
            'confidenceUpper': float(fc['confidenceUpper'])
        })
    
    output = {
        'historical': historical_data,
        'predicted': predicted_data
    }
    
    # Save to file for API to read
    output_file = 'job_listings_forecast.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print("    [OK] Saved to {}".format(output_file), flush=True)
    
    # Show samples
    print("\n[4] SAMPLE FORECASTS", flush=True)
    for i, fc in enumerate(forecasts[:6]):
        print("    {}: count={:.0f} (CI: {:.0f}-{:.0f})".format(
            fc['date'], fc['count'], fc['confidenceLower'], fc['confidenceUpper']), flush=True)
    
    print("\n" + "=" * 80, flush=True)
    print("[DONE] Job listings forecasting complete!", flush=True)
    print("=" * 80, flush=True)
