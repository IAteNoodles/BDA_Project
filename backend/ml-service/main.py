import os
import logging
from typing import Optional
from datetime import date, datetime

from fastapi import FastAPI, Query
from pydantic import BaseModel
import psycopg2

logger = logging.getLogger("ml-service")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="ML Forecasting Service", version="3.0.0")

DB_CONFIG = {
    "host": os.getenv("ML_DB_HOST", "localhost"),
    "port": int(os.getenv("ML_DB_PORT", "5432")),
    "dbname": os.getenv("ML_DB_NAME", "job_market"),
    "user": os.getenv("ML_DB_USER", "postgres"),
    "password": os.getenv("ML_DB_PASSWORD", "postgres123"),
}


class ForecastPoint(BaseModel):
    forecastDate: str
    predictedDemand: float
    confidenceLower: float
    confidenceUpper: float


class ForecastTrend(BaseModel):
    skillName: str
    averagePredictedDemand: float
    forecasts: list[ForecastPoint]


class TrendPoint(BaseModel):
    date: str
    count: float
    confidenceLower: Optional[float] = None
    confidenceUpper: Optional[float] = None


class JobListingsTrendResponse(BaseModel):
    historical: list[TrendPoint]
    predicted: list[TrendPoint]


class HealthResponse(BaseModel):
    status: str
    model: str


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def fetch_forecasts(skill: Optional[str] = None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if skill:
                cur.execute(
                    "SELECT skill_name, forecast_date, predicted_demand, "
                    "confidence_lower, confidence_upper "
                    "FROM forecast_results "
                    "WHERE skill_name != '(job_listings_total)' AND skill_name = %s "
                    "ORDER BY skill_name, forecast_date",
                    (skill,)
                )
            else:
                cur.execute(
                    "SELECT skill_name, forecast_date, predicted_demand, "
                    "confidence_lower, confidence_upper "
                    "FROM forecast_results "
                    "WHERE skill_name != '(job_listings_total)' "
                    "ORDER BY skill_name, forecast_date"
                )
            return cur.fetchall()
    finally:
        conn.close()


def fetch_job_listings_historical():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DATE_TRUNC('month', posted_date) AS month, COUNT(*) AS cnt "
                "FROM job_listings GROUP BY month ORDER BY month"
            )
            return cur.fetchall()
    finally:
        conn.close()


def fetch_job_listings_forecast():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT forecast_date, predicted_demand, confidence_lower, confidence_upper "
                "FROM forecast_results "
                "WHERE skill_name = '(job_listings_total)' "
                "ORDER BY forecast_date"
            )
            return cur.fetchall()
    finally:
        conn.close()


@app.get("/ml/predictions", response_model=list[ForecastTrend])
def get_predictions(topN: int = Query(10, ge=1, le=50), skill: Optional[str] = Query(None)):
    rows = fetch_forecasts(skill)
    skills = {}
    for skill_name, fdate, pred, clo, chi in rows:
        skills.setdefault(skill_name, []).append(
            ForecastPoint(
                forecastDate=fdate.isoformat() if hasattr(fdate, "isoformat") else str(fdate),
                predictedDemand=round(float(pred), 2),
                confidenceLower=round(float(clo), 2),
                confidenceUpper=round(float(chi), 2),
            )
        )
    trends = []
    for name, points in skills.items():
        avg = round(sum(p.predictedDemand for p in points) / len(points), 2)
        trends.append(ForecastTrend(skillName=name, averagePredictedDemand=avg, forecasts=points))
    trends.sort(key=lambda t: t.averagePredictedDemand, reverse=True)
    return trends[:topN]


@app.get("/ml/job-listings-trend", response_model=JobListingsTrendResponse)
def get_job_listings_trend():
    hist_rows = fetch_job_listings_historical()
    historical = [
        TrendPoint(
            date=row[0].strftime("%Y-%m-%d") if hasattr(row[0], "strftime") else str(row[0]),
            count=int(row[1]),
        )
        for row in hist_rows
    ]
    fc_rows = fetch_job_listings_forecast()
    predicted = [
        TrendPoint(
            date=row[0].isoformat() if hasattr(row[0], "isoformat") else str(row[0]),
            count=round(float(row[1]), 2),
            confidenceLower=round(float(row[2]), 2),
            confidenceUpper=round(float(row[3]), 2),
        )
        for row in fc_rows
    ]
    return JobListingsTrendResponse(historical=historical, predicted=predicted)


@app.get("/ml/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(status="ok", model="precomputed")