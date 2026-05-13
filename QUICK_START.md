# Quick Start Guide

## System Status

**Current Setup**: ✅ RUNNING with REAL data (Jobstreet)

```
Data: Jobstreet (69K rows, 26 months, March 2023 - May 2025)
Skills: 53 tech skills extracted
Forecasts: 1,630 SARIMA points (to Dec 2027)
Model: SARIMA(1,1,1)(1,1,1,12)
Services: PostgreSQL, ML-Service, API-Server, Frontend
```

## 1. Quick Test

### Test ML Service (Direct)
```bash
curl -s http://localhost:5100/ml/health
# Response: {"status":"ok","model":"precomputed"}

curl -s http://localhost:5100/ml/predictions?topN=3 | python -m json.tool | head -50
```

### Test API Server (Proxy)
```bash
curl -s http://localhost:18080/api/forecasts/predictions?topN=3 | python -m json.tool | head -50
```

### View Frontend
```bash
# Open browser
http://localhost:5173
```

## 2. Restart Services

### Fresh Start (Clears Data)
```bash
cd C:\Users\Noodl\Projects\BDA
docker-compose down -v
docker-compose up -d postgres ml-service api-server frontend
# Wait 30s for postgres to initialize
```

### Soft Restart (Keeps Data)
```bash
docker-compose restart
```

### View Logs
```bash
docker logs postgres         # Database
docker logs ml-service       # Python ML service
docker logs api-server       # Java API
docker logs frontend         # React UI
```

## 3. Re-Run ETL (with Real Data)

### Automatic
```bash
# ETL auto-detects jobstreet_processed.csv in data/
python backend/database/etl_synthetic.py
```

### Output Files
```
backend/database/seed/
  ├── skill_demand.tsv        (780 rows, 53 skills, 26 months)
  ├── job_listings.tsv        (19 months)
  └── forecast_results.tsv    (1,630 forecast points to 2027-12)
```

## 4. Update Real Data

### Option A: Re-Download Jobstreet
```bash
kaggle datasets download -d azraimohamad/jobstreet-all-job-dataset \
  -p C:\Users\Noodl\Projects\BDA\data\jobstreet --unzip

python preprocess_jobstreet.py

python backend/database/etl_synthetic.py
```

### Option B: Use Different Dataset
1. Place CSV/XLSX in `C:\Users\Noodl\Projects\BDA\data/`
2. Ensure columns with names like: `date`, `skill`, `demand`
3. Run ETL (auto-detects)

### Option C: Use Synthetic Fallback
```bash
# Just delete jobstreet files
rm C:\Users\Noodl\Projects\BDA\data\jobstreet_processed.csv
python backend/database/etl_synthetic.py
# Will use synthetic data instead
```

## 5. View Forecasts

### Sample: Top Skill (Java) - Dec 2027
```
Forecast Date: 2027-12-01
Predicted Demand: 387.49
Confidence Lower: 0.0
Confidence Upper: 1254.47
Model: SARIMA(1,1,1)(1,1,1,12)
```

### Sample: All Forecasts for SQL
```bash
curl -s http://localhost:18080/api/forecasts/predictions?topN=50 | \
  python -c "
import sys, json
d = json.load(sys.stdin)
sql = [s for s in d if s['skillName'] == 'SQL'][0]
print('SQL Skill Forecast (2023-03 to 2027-12):')
for f in sql['forecasts'][-12:]:  # Last 12 months (2027)
    print(f'  {f[\"forecastDate\"]}: {f[\"predictedDemand\"]:.1f}')
"
```

## 6. Architecture

```
Real Job Data        ETL Pipeline         ML Service           API Server          Frontend
Jobstreet            Python Script        Python FastAPI       Java Spring         React Vite
69K rows ------>     Extract skills  -->  SARIMA model   -->   Proxy to ML  -->   Charts on
Mar 2023 - May 2025  aggreg by month      pre-compute         port 5100           port 5173
                     (26 months)          forecasts to 2027
```

## 7. Key Files

| File | Purpose |
|------|---------|
| `etl_synthetic.py` | ETL pipeline (auto-loads real data, fallback to synthetic) |
| `preprocess_jobstreet.py` | Extract tech skills from job descriptions |
| `backend/ml-service/main.py` | FastAPI endpoints for forecasts |
| `backend/api-server/.../ForecastService.java` | Proxy to ML service |
| `frontend/src/pages/Dashboard.tsx` | Forecast visualization |
| `docker-compose.yml` | Service orchestration |

## 8. Forecast Quality

### Model: SARIMA(1,1,1)(1,1,1,12)
- **Training Data**: 26 months Jobstreet (Mar 2023 - May 2025)
- **Forecast Horizon**: 31 months (May 2025 → Dec 2027)
- **Confidence**: 95% intervals
- **Seasonality**: 12-month job market cycles

### Expected Accuracy
- **2025**: High (6-month horizon)
- **2026**: Medium (12-18 month horizon)
- **2027**: Lower (24-31 month horizon)

## 9. Common Issues & Solutions

### Issue: "ML service not responding"
```bash
# Check service is running
docker ps | grep ml-service

# Check logs
docker logs ml-service

# Solution: Restart postgres first, then ml-service
docker-compose restart postgres ml-service
```

### Issue: "No forecasts appearing"
```bash
# Verify data was loaded
docker exec postgres psql -U postgres -d job_market \
  -c "SELECT COUNT(*) FROM forecast_results;"

# Should return: 1630 (or similar)
```

### Issue: "Real data not loading"
```bash
# Check ETL logs
python backend/database/etl_synthetic.py

# If it says "synthetic fallback" → real data not detected
# Verify jobstreet_processed.csv exists:
ls -la C:\Users\Noodl\Projects\BDA\data\jobstreet_processed.csv
```

## 10. Production Deployment

### Scale Up
1. Use RDS PostgreSQL (managed)
2. Deploy ml-service on Lambda / Cloud Run (serverless)
3. API-server on App Engine / ECS (auto-scaling)
4. Frontend on CDN (Cloudflare / CloudFront)

### Monitor
1. Set up alerts for forecast query latency
2. Track ETL execution time
3. Monitor ML model drift (if forecasts diverge from actuals)

### Update Frequency
- Recommended: Weekly ETL run (update with latest job postings)
- Quarterly: Re-train SARIMA (if new data patterns emerge)
- Annually: Evaluate model architecture (compare with newer methods)

---

## Summary

You now have:
- ✅ Real job market data (Jobstreet, 69K rows)
- ✅ 53 tech skills with demand trends
- ✅ SARIMA forecasts to Dec 2027
- ✅ Pre-computed forecasts (50ms queries)
- ✅ Full microservices stack (Postgres → ML → API → Frontend)
- ✅ Synthetic fallback (if real data fails)

**Ready for**: Testing, deployment, or enhancement!
