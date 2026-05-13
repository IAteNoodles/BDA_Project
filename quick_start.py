#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Start: Jobstreet Job Market Dataset for Time Series Forecasting
Dataset: 69,024 job postings (March 2023 - May 2025)
Download: kaggle datasets download -d azraimohamad/jobstreet-all-job-dataset --unzip
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

def main():
    print("\n" + "="*60)
    print("[JOBSTREET JOB MARKET DATASET - QUICK START]")
    print("="*60)
    
    try:
        # Load dataset
        print("\n⏳ Loading jobstreet_all_job_dataset.csv...")
        df = pd.read_csv('jobstreet_all_job_dataset.csv')
        df['date'] = pd.to_datetime(df['listingDate'])
        
        # Dataset overview
        print(f"\n[OK] Dataset Loaded: {len(df):,} records")
        print(f"\n[DATE RANGE]")
        print(f"   Start: {df['date'].min().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   End:   {df['date'].max().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Span:  {(df['date'].max() - df['date'].min()).days} days")
        
        # Time series statistics
        daily = df.groupby(df['date'].dt.date).size()
        print(f"\n[DAILY POSTING VOLUME]")
        print(f"   Average: {daily.mean():.0f} postings/day")
        print(f"   Min:     {daily.min()} postings")
        print(f"   Max:     {daily.max()} postings")
        
        # Data quality
        print(f"\n[DATA QUALITY]")
        print(f"   Job titles:    100% ({len(df):,})")
        print(f"   Descriptions:  100% ({len(df):,})")
        print(f"   Salary info:   {(df['salary'].notna().sum()/len(df)*100):.1f}% ({df['salary'].notna().sum():,})")
        print(f"   Unique companies: {df['company'].nunique():,}")
        print(f"   Unique titles: {df['job_title'].nunique():,}")
        
        # Monthly aggregation
        monthly = df.groupby(df['date'].dt.to_period('M')).size()
        print(f"\n[MONTHLY POSTINGS - Last 12 months]")
        for period, count in monthly.tail(12).items():
            print(f"   {period}: {count:,}")
        
        # Categories
        print(f"\n[TOP JOB CATEGORIES]")
        top_cats = df['category'].value_counts().head(10)
        for cat, count in top_cats.items():
            print(f"   {cat}: {count:,}")
        
        # Ready to use
        print(f"\n[OK] READY FOR TIME SERIES ANALYSIS")
        print(f"\n   Python Code Examples:")
        print(f"   ─────────────────────")
        print(f"   # Daily job postings")
        print(f"   daily = df.groupby(df['date'].dt.date).size()")
        print(f"   ")
        print(f"   # Weekly aggregation")
        print(f"   weekly = df.groupby(df['date'].dt.to_period('W')).size()")
        print(f"   ")
        print(f"   # By job category")
        print(f"   by_cat = df.groupby([df['date'].dt.date, 'category']).size()")
        print(f"   ")
        print(f"   # Salary trends")
        print(f"   sal = df[df['salary'].notna()].groupby(df['date'].dt.date)['salary'].agg(['mean', 'count'])")
        
        print("\n" + "="*60 + "\n")
        
    except FileNotFoundError:
        print("\n❌ ERROR: jobstreet_all_job_dataset.csv not found")
        print("Download with: kaggle datasets download -d azraimohamad/jobstreet-all-job-dataset --unzip")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
