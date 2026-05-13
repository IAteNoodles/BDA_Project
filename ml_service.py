#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ML Service - Flask API for forecasts
Serves job listings trends and skill demand predictions
Port: 5000
"""
import json
import os
from flask import Flask, jsonify
import pandas as pd
from datetime import datetime

app = Flask(__name__)

# Load job listings forecast
job_listings_forecast_file = 'job_listings_forecast.json'
job_listings_cache = None

def load_job_listings_forecast():
    """Load cached forecast data"""
    global job_listings_cache
    if job_listings_cache is not None:
        return job_listings_cache
    
    if os.path.exists(job_listings_forecast_file):
        with open(job_listings_forecast_file, 'r') as f:
            job_listings_cache = json.load(f)
        return job_listings_cache
    return None

@app.route('/ml/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok'}), 200

@app.route('/ml/job-listings-trend', methods=['GET'])
def get_job_listings_trend():
    """Get historical and predicted job listings trend"""
    forecast = load_job_listings_forecast()
    if not forecast:
        return jsonify({'historical': [], 'predicted': []}), 200
    return jsonify(forecast), 200

@app.route('/ml/predictions', methods=['GET'])
def get_predictions():
    """Get top N skill demand predictions (placeholder)"""
    # This endpoint is called by Java service but we already have forecasts in DB
    # Return empty for now since DB already has LSTM forecasts
    return jsonify([]), 200

if __name__ == '__main__':
    print("[INIT] ML Service starting on http://localhost:5000", flush=True)
    print("[LOAD] Loading job listings forecast...", flush=True)
    load_job_listings_forecast()
    print("[READY] ML Service ready", flush=True)
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
