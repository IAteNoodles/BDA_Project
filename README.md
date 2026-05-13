<p align="center">
  <img src="https://img.shields.io/badge/Platform-Big_Data-blueviolet" alt="Platform" />
  <img src="https://img.shields.io/badge/Hadoop-3.x-orange" alt="Hadoop" />
  <img src="https://img.shields.io/badge/Spark-3.0-orange" alt="Spark" />
  <img src="https://img.shields.io/badge/Kafka-7.0-green" alt="Kafka" />
  <img src="https://img.shields.io/badge/Spring_Boot-3.1-brightgreen" alt="Spring Boot" />
  <img src="https://img.shields.io/badge/FastAPI-0.100-teal" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-18-61DAFB" alt="React" />
  <img src="https://img.shields.io/badge/Python-3.10-3776AB" alt="Python" />
  <img src="https://img.shields.io/badge/Java-17-ED8B00" alt="Java" />
  <img src="https://img.shields.io/badge/TypeScript-5-3178C6" alt="TypeScript" />
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License" />
</p>

<h1 align="center">Job Market Demand Forecasting System</h1>

<p align="center"><strong>Predictive analytics platform for job market trends — Big Data processing, ML forecasting, real-time streaming, and interactive visualization.</strong></p>

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [System Status](#system-status)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Data Sources](#data-sources)
- [ETL Pipeline](#etl-pipeline)
- [ML Models](#ml-models)
- [API Reference](#api-reference)
- [Frontend](#frontend)
- [Big Data Ecosystem](#big-data-ecosystem)
- [Database Schema](#database-schema)
- [Port Map](#port-map)
- [Docker Images](#docker-images)
- [Environment Configuration](#environment-configuration)
- [ETL Refresh](#etl-refresh)
- [Performance Targets](#performance-targets)
- [Forecast Accuracy](#forecast-accuracy)
- [Key Design Decisions](#key-design-decisions)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA SOURCES                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Jobstreet    │  │   LinkedIn   │  │   Indeed     │  │   Glassdoor  │    │
│  │  (69K rows)   │  │   (avail)    │  │   (API)      │  │   (API)      │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                  │                  │                  │            │
│         └──────────────────┴──────────────────┴──────────────────┘            │
│                                     │                                        │
└─────────────────────────────────────┼────────────────────────────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INGESTION & STREAMING                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Apache Kafka (9092)                               │    │
│  │            "job-postings" topic · 4 partitions · Snappy              │    │
│  │            7-day retention · Real-time feed buffering                │    │
│  └──────────────┬──────────────────────────────────┬───────────────────┘    │
│                 │                                  │                        │
│     ┌───────────▼──────────┐            ┌─────────▼──────────┐             │
│     │  Kafka Consumer      │            │  Spark Streaming    │             │
│     │  (Spring Boot)       │            │  (Spark-Kafka)      │             │
│     │  → Postgres + HBase  │            │  → ETL + Analytics  │             │
│     └──────────┬───────────┘            └─────────┬──────────┘             │
└────────────────┼──────────────────────────────────┼────────────────────────┘
                 │                                  │
┌────────────────┼──────────────────────────────────┼────────────────────────┐
│                │        STORAGE LAYER              │                        │
│  ┌─────────────▼──────────┐  ┌────────────────────▼───────────────────┐    │
│  │  HDFS (NameNode:9870)  │  │  HBase (Master:16010)                  │    │
│  │  Raw data lake         │  │  NoSQL hot data · Real-time queries    │    │
│  └────────────────────────┘  └───────────────────────────────────────┘    │
│  ┌────────────────────────┐  ┌───────────────────────────────────────┐    │
│  │  Hive                  │  │  PostgreSQL 14 (5432)                  │    │
│  │  SQL-on-Hadoop         │  │  job_market DB · Forecasts · Metadata │    │
│  └────────────────────────┘  └───────────────────────────────────────┘    │
│  ┌────────────────────────┐                                              │    │
│  │  Redis (16379)         │  LRU · 2GB · TTL 3600s · API cache          │    │
│  └────────────────────────┘                                              │    │
└─────────────────────────────────────────────────────────────────────────────┘
                 │                                  │
┌────────────────┼──────────────────────────────────┼────────────────────────┐
│                │     PROCESSING & ML               │                        │
│  ┌─────────────▼──────────────────────────────────▼──────────────────┐    │
│  │  Apache Spark (Master:7077/8080/4040)                             │    │
│  │  Worker: 2 cores · 2G memory · ETL · MLlib · SQL · Streaming     │    │
│  └────────────────────────┬─────────────────────────────────────────┘    │
│                           │                                                │
│  ┌────────────────────────▼─────────────────────────────────────────┐    │
│  │  Python ML Service (FastAPI :5100→5000)                          │    │
│  │  SARIMA(1,1,1)(1,1,1,12) · LSTM · Linear Regression             │    │
│  │  Precomputed forecasts · 50ms query latency · 95% CI             │    │
│  └────────────────────────┬─────────────────────────────────────────┘    │
└───────────────────────────┼─────────────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────────────┐
│                    API & PRESENTATION                                   │
│  ┌────────────────────────▼─────────────────────────────────────────┐    │
│  │  Spring Boot API Server (:18080→8080)                            │    │
│  │  Java 17 · Spring Data JPA · Redis Cache · Kafka Producer       │    │
│  │  REST · Pagination · CORS · ML Proxy                             │    │
│  └────────────────────────┬─────────────────────────────────────────┘    │
│                           │                                              │
│  ┌────────────────────────▼─────────────────────────────────────────┐    │
│  │  React Frontend (:5173→3000)                                     │    │
│  │  Vite 4 · React 18 · TypeScript · Tailwind CSS · Chart.js 3     │    │
│  │  Dashboard · Jobs · Skills · Forecasts                           │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │  Apache Airflow (:8888) · Admin/Admin · LocalExecutor            │    │
│  │  DAG scheduling · Daily 02:00 · Workflow orchestration           │    │
│  └──────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## System Status

| Component | Status | Details |
|-----------|--------|---------|
| PostgreSQL 14 | ✅ Running | `job_market` DB, 3 tables, 2,790+ rows |
| Python ML Service | ✅ Running | FastAPI, SARIMA + LSTM + LinReg forecasts |
| Java API Server | ✅ Running | Spring Boot 3.1, full REST API with pagination |
| React Frontend | ✅ Running | 4 pages, Chart.js visualizations, responsive |
| Spark Cluster | 🟡 Infrastructure Ready | Master + Worker containers, Scala app skeleton |
| Hadoop HDFS | 🟡 Infrastructure Ready | NameNode + DataNode containers configured |
| Kafka + Zookeeper | 🟡 Infrastructure Ready | Broker with topic, Spring Boot consumer built |
| HBase | 🟡 Infrastructure Ready | Master container configured |
| Redis | 🟡 Infrastructure Ready | Alpine container, 2GB LRU cache |
| Airflow | 🟡 Infrastructure Ready | Webserver + Scheduler, DAGs configured |
| Kubernetes | 🔲 Planned | `k8s/` directory reserved |

---

## Tech Stack

### Big Data Layer

| Technology | Version | Role |
|-----------|---------|------|
| Apache Hadoop | 3.x (bde2020) | HDFS distributed storage, NameNode + DataNode |
| Apache Spark | 3.0.0 (bde2020) | ETL, analytics, MLlib, streaming-Kafka |
| Apache Kafka | 7.0.1 (Confluent) | Real-time streaming, 4-partition topics, Snappy compression |
| Apache HBase | bde2020 | NoSQL store for hot data queries |
| Apache Hive | — | SQL-on-Hadoop data warehouse |
| Apache Airflow | 2.5.0 | DAG scheduling, workflow orchestration |
| Redis | Alpine | API response caching, 2GB LRU, TTL 3600s |
| Flume/Sqoop | — | Batch and incremental data ingestion |

### Backend

| Technology | Version | Role |
|-----------|---------|------|
| Java | 17 | API server, Kafka consumer |
| Spring Boot | 3.1.0 | REST API, JPA, Redis, Kafka integration |
| Python | 3.10 | ML service, ETL scripts |
| FastAPI | 0.100+ | ML prediction serving |
| PostgreSQL | 14 | Primary database, forecasts, metadata |
| SARIMA | statsmodels | Primary forecast model |
| TensorFlow | — | LSTM models (GPU-accelerated) |
| scikit-learn | — | Linear Regression fallback model |

### Frontend

| Technology | Version | Role |
|-----------|---------|------|
| React | 18 | UI framework |
| TypeScript | 5 | Type safety |
| Vite | 4 | Build tool, dev server, proxy |
| Chart.js | 3 + react-chartjs-2 | Data visualizations |
| Tailwind CSS | — | Utility-first styling |
| Axios | — | HTTP client (configurable base URL) |
| react-router-dom | 6 | Client-side routing |
| D3.js | — | Advanced data visualizations (planned) |

### Infrastructure

| Technology | Role |
|-----------|------|
| Docker | Containerization (multi-stage builds) |
| Docker Compose | Full-stack local orchestration |
| Kubernetes | Production deployment (planned) |

---

## Project Structure

```
BDA/
├── backend/
│   ├── spark-jobs/                    # Scala Spark ETL (Spark Core/SQL/MLlib/Streaming-Kafka + HBase)
│   │   ├── src/
│   │   ├── pom.xml
│   │   └── Dockerfile
│   ├── kafka-consumer/                # Spring Boot Kafka consumer → Postgres + HBase
│   │   ├── src/
│   │   ├── pom.xml
│   │   └── Dockerfile
│   ├── api-server/                    # Spring Boot 3.1 REST API
│   │   ├── src/
│   │   ├── pom.xml
│   │   └── Dockerfile
│   ├── ml-service/                    # FastAPI Python ML service
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── forecast_sarima.py     # Primary: SARIMA(1,1,1)(1,1,1,12)
│   │   │   ├── forecast_lstm.py       # LSTM skill demand forecasting
│   │   │   ├── forecast_job_listings.py  # LSTM job listings forecasting
│   │   │   ├── retrain_forecasts.py   # Linear Regression v3 (LSTM replacement)
│   │   │   └── cap_forecasts.py       # Post-processing: clamp to 5× historical max
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── database/
│   │   ├── init.sql                   # PostgreSQL schema + COPY from seed files
│   │   ├── etl_synthetic.py           # Two-tier ETL loader (real → synthetic fallback)
│   │   ├── seed/                      # TSV seed files
│   │   │   ├── skill_demand.tsv       # 780 rows, 53 skills
│   │   │   ├── job_listings.tsv       # ~380 rows
│   │   │   └── forecast_results.tsv   # 1,630 forecast points
│   │   └── generate_synthetic_data.py # Fallback data generator (1,152 rows, 32 skills)
│   ├── airflow/
│   │   ├── dags/                      # Workflow DAGs
│   │   └── docker-compose.yml
│   └── config/                        # Hadoop, Hive, HBase configuration files
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard/             # Stat cards, charts, recent jobs
│   │   │   ├── JobTrends/             # Filterable job listings table
│   │   │   ├── Forecasts/             # Line charts with confidence intervals
│   │   │   └── Filters/               # Shared filter components
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx          # Overview: stats, top 10, forecasts, predictions
│   │   │   ├── Jobs.tsx               # Filterable job listings table
│   │   │   ├── Skills.tsx             # Bar chart + demand table
│   │   │   └── Forecasts.tsx          # Forecast charts + ML predictions table
│   │   ├── services/                  # Axios API clients
│   │   ├── hooks/                     # Custom React hooks
│   │   ├── App.tsx                    # React Router v6 routes
│   │   └── main.tsx
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts                 # Dev proxy: /api → VITE_API_URL
│   ├── Dockerfile                     # Multi-stage: node:18-alpine → static dist :3000
│   └── tailwind.config.js
├── data/
│   ├── raw/                           # Raw job posting datasets
│   │   └── jobstreet/                 # Kaggle dataset (69,024 rows)
│   ├── processed/                     # ETL output
│   │   └── jobstreet_processed.csv
│   ├── linkedin/                      # LinkedIn dataset
│   └── schemas/                       # Data schemas
├── docs/
│   ├── ARCHITECTURE.md
│   ├── SETUP.md
│   ├── API.md
│   ├── DATA_PIPELINE.md
│   └── SCALING.md
├── k8s/                               # Kubernetes manifests (planned)
├── docker-compose.yml                 # Full stack: 12+ services
├── .env.example                       # Environment template
├── preprocess_jobstreet.py            # Skill extraction from job titles/descriptions
└── README.md
```

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Git
- 8 GB RAM minimum (16 GB recommended for full Big Data stack)
- 50 GB disk space

### Launch Everything

```bash
git clone <repo>
cd BDA
cp .env.example .env
docker-compose up -d
```

Wait 2–3 minutes for all services to initialize, then access:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:5173 | React dashboard |
| **API Server** | http://localhost:18080 | Spring Boot REST API |
| **ML Service** | http://localhost:5100 | FastAPI predictions |
| **Spark Master** | http://localhost:8080 | Spark cluster UI |
| **Spark Apps** | http://localhost:4040 | Running app UI |
| **Hadoop NameNode** | http://localhost:9870 | HDFS overview |
| **Hadoop DataNode** | http://localhost:9864 | Data node status |
| **HBase Master** | http://localhost:16010 | NoSQL store UI |
| **Airflow** | http://localhost:8888 | DAG scheduler (admin/admin) |

### Quick Health Check

```bash
curl http://localhost:18080/api/health
curl http://localhost:5100/ml/health
```

---

## Data Sources

| Source | Records | Period | Region | Skills | Status |
|--------|---------|--------|--------|--------|--------|
| **Jobstreet** (Kaggle) | 69,024 | Mar 2023 – May 2025 | Malaysia | 53 tech | ✅ Primary |
| Synthetic fallback | 1,152 | 2022 – 2024 | — | 32 | ✅ Auto-fallback |
| LinkedIn | — | — | — | — | 📦 Available in `data/linkedin/` |
| Indian job market | — | — | India | — | 📦 Available |
| Dice | — | — | — | — | 📦 Available |
| Generic `job_descriptions.csv` | — | — | — | — | 📦 Available |

**Design**: ETL uses a two-tier loader — real data first, synthetic fallback if unavailable. This ensures the system always has data.

---

## ETL Pipeline

```
Jobstreet CSV (69K rows)
        │
        ▼
preprocess_jobstreet.py
  • Regex skill extraction from titles + descriptions
  • 53 tech skills identified
  • → data/jobstreet_processed.csv
        │
        ▼
backend/database/etl_synthetic.py
  • Two-tier loader: real data → synthetic fallback
  • Runs SARIMA forecast generation
  • Outputs TSV seed files:
      ├── backend/database/seed/skill_demand.tsv      (780 rows)
      ├── backend/database/seed/job_listings.tsv       (~380 rows)
      └── backend/database/seed/forecast_results.tsv   (1,630 points)
        │
        ▼
backend/database/init.sql
  • PostgreSQL schema creation (3 tables)
  • COPY commands load TSV seed files
        │
        ▼
PostgreSQL job_market database ready
```

### Airflow Orchestration

- **Schedule**: Daily at 02:00
- **Executor**: LocalExecutor with Postgres backend
- **ETL timeout**: 30 minutes
- **Batch size**: 10,000 records
- **DAGs**: Configured in `backend/airflow/dags/`

---

## ML Models

### Model Inventory

| Model | File | Purpose | Forecast Horizon | Speed |
|-------|------|---------|-----------------|-------|
| **SARIMA(1,1,1)(1,1,1,12)** | `forecast_sarima.py` | Primary: skill demand forecasting | 31 months (to Dec 2027) | 50ms query (precomputed) |
| **LSTM** | `forecast_lstm.py` | Per-skill demand | 32 months | GPU-accelerated, 30 epochs |
| **LSTM (Job Listings)** | `forecast_job_listings.py` | Monthly job posting count | 32 months | 50 epochs, blended |
| **Linear Regression v3** | `retrain_forecasts.py` | LSTM replacement | Ongoing | Fast, CV-validated |

### SARIMA — Primary Model

- **Order**: (1,1,1)(1,1,1,12) — captures trend + annual seasonality
- **Training data**: 26 months Jobstreet (Mar 2023 – May 2025)
- **Forecast horizon**: 31 months to December 2027
- **Confidence**: 95% intervals
- **Why SARIMA over Exponential Smoothing**: captures both trend and seasonality
- **Why precomputed**: auto_arima takes ~60s per skill; precomputed queries return in ~50ms
- **Model version**: `SARIMA(1,1,1)(1,1,1,12)`

### LSTM — Skill Demand

- **Architecture**: LSTM(32) → Dropout → Dense(16) → Dense(1)
- **Training**: 30 epochs, lookback window = 6
- **Forecast**: 32 months per skill
- **Runtime**: GPU-accelerated via TensorFlow

### LSTM — Job Listings

- **Architecture**: LSTM(16) → Dropout → Dense(8) → Dense(1)
- **Training**: 50 epochs, lookback window = 3
- **Forecast**: 32 months
- **Blending**: 70% LSTM + 30% growth trend (1.5%/month) + sinusoidal seasonality

### Linear Regression v3 — LSTM Replacement

- **Features**: Trend + sin/cos seasonality
- **Validation**: TimeSeriesSplit cross-validation
- **Spike handling**: Excludes "scrape spike" months (Feb – Jun 2024)
- **Clamping**: Anchor ±50%
- **Model version**: `LinReg_NoSpike_v3`

### Post-Processing

- **`cap_forecasts.py`**: Clamps all forecast values to 5× historical maximum per skill, preventing unrealistic projections

---

## API Reference

### Java API Server — Spring Boot (`:18080`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Service health check |
| `GET` | `/api/jobs` | List jobs (filterable, paginated) |
| `GET` | `/api/jobs/{id}` | Get job by ID |
| `GET` | `/api/jobs/stats` | Job listing statistics |
| `GET` | `/api/skills` | List skills (filterable, paginated) |
| `GET` | `/api/skills/top` | Top skills by demand |
| `GET` | `/api/forecasts` | List forecasts (filterable, paginated) |
| `GET` | `/api/forecasts/trends` | Forecast trend data |
| `GET` | `/api/forecasts/predictions` | ML predictions (proxied to ML service) |
| `GET` | `/api/forecasts/job-listings-trend` | Job listings trend (proxied to ML service) |

**Details**: Spring Data JPA, pagination on all list endpoints, Spring Data Redis caching, CORS enabled on `/api/**`, `ddl-auto: none` (schema managed by `init.sql`), model version hardcoded as `SARIMA(1,1,1)(1,1,1,12)`, region `Global`.

### Python ML Service — FastAPI (`:5100`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/ml/health` | ML service health check |
| `GET` | `/ml/predictions?topN=5` | Top N skill predictions |
| `GET` | `/ml/job-listings-trend` | Job listings forecast trend |

**Details**: Serves precomputed SARIMA forecasts from PostgreSQL. Port 5100 chosen because Windows blocks ports 4937–5036.

### Planned API Extensions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/trends` | Job demand trends (time-series aggregation) |
| `GET` | `/api/forecasts/{region}` | Region-specific forecasts |
| `GET` | `/api/skills/{skill}` | Skill-specific historical + forecast data |
| `GET` | `/api/companies/{company}` | Company hiring trends |
| `GET` | `/api/analytics/summary` | Dashboard summary statistics |
| `POST` | `/api/search` | Advanced search with filters |

---

## Frontend

**4 pages** built with React 18 + TypeScript + Tailwind CSS + Chart.js 3:

| Page | Route | Contents |
|------|-------|----------|
| **Dashboard** | `/` | Stat cards, top 10 skills bar chart, forecast line charts, job listings prediction, recent jobs |
| **Jobs** | `/jobs` | Filterable job listings table |
| **Skills** | `/skills` | Skill demand bar chart + demand table |
| **Forecasts** | `/forecasts` | Line charts with 95% confidence intervals, ML predictions table |

**Build**: Docker multi-stage — `node:18-alpine` build → static `dist` served on port 3000.

**Dev proxy**: Vite proxies `/api` requests to `VITE_API_URL` (default `http://localhost:8080`).

**Planned deps** (declared but unused): zustand, @reduxjs/toolkit, react-redux, d3, mapbox-gl.

### State Management

- **Redux Toolkit** (`@reduxjs/toolkit` + `react-redux`): Declared, planned for global state
- **Zustand**: Declared, lightweight alternative for local component state
- Currently using local React state; migration to Redux/Zustand planned

---

## Big Data Ecosystem

All services defined in `docker-compose.yml`:

### Hadoop HDFS

| Service | Image | Ports | Role |
|---------|-------|-------|------|
| NameNode | bde2020/hadoop-namenode | 9870 (UI), 9000 (HDFS) | HDFS master, metadata |
| DataNode | bde2020/hadoop-datanode | 9864 (UI) | HDFS worker, data blocks |

### Apache Spark

| Service | Image | Ports | Resources | Role |
|---------|-------|-------|-----------|------|
| Spark Master | bde2020/spark-master:3.0.0 | 7077 (submit), 8080 (UI), 4040 (apps) | — | Cluster manager |
| Spark Worker | bde2020/spark-worker:3.0.0 | 18081 (UI) | 2 cores, 2G memory | Executor node |

**Spark Jobs** (`backend/spark-jobs/`): Scala app with Spark Core, Spark SQL, MLlib, Streaming-Kafka, and HBase client dependencies.

### Apache Kafka

| Service | Image | Ports | Config |
|---------|-------|-------|--------|
| Zookeeper | confluentinc/cp-kafka:7.0.1 | 2181 | Kafka coordination |
| Kafka Broker | confluentinc/cp-kafka:7.0.1 | 9092 | 4 partitions, Snappy, 7-day retention |

**Topic**: `job-postings` — consumed by Spring Boot Kafka Consumer, persisted to PostgreSQL + HBase.

### Apache HBase

| Service | Image | Port | Role |
|---------|-------|------|------|
| HBase Master | bde2020/hbase-master | 16010 | NoSQL hot data store |

### Redis

| Service | Image | Port | Config |
|---------|-------|------|--------|
| Redis | redis:alpine | 16379 | 2GB max memory, LRU eviction, TTL 3600s |

### Apache Airflow

| Service | Image | Port | Config |
|---------|-------|------|--------|
| Webserver | apache/airflow:2.5.0 | 8888 | admin/admin |
| Scheduler | apache/airflow:2.5.0 | — | LocalExecutor, Postgres backend |

### Monitoring & Logging

| Component | Status | Details |
|-----------|--------|---------|
| Spark UI | ✅ Available | Yarn UI + Spark History Server at :4040 |
| Hadoop UI | ✅ Available | NameNode UI at :9870, DataNode at :9864 |
| ELK Stack | 🔲 Planned | Centralized logging (Elasticsearch, Logstash, Kibana) |
| Prometheus + Grafana | 🔲 Planned | Metrics collection and dashboards |
| Alerting | 🔲 Planned | Job failures, data quality issues, SLA breaches |

---

## Database Schema

### PostgreSQL 14 — `job_market` Database

**3 tables, 2,790+ total rows:**

```sql
skill_demand (
    id              SERIAL PRIMARY KEY,
    skill_name      VARCHAR,
    demand_count    INTEGER,
    period_start    DATE,
    period_end      DATE,
    region          VARCHAR,
    industry        VARCHAR,
    created_at      TIMESTAMP
)

job_listings (
    id              SERIAL PRIMARY KEY,
    title           VARCHAR,
    company         VARCHAR,
    location        VARCHAR,
    salary_min      NUMERIC,
    salary_max      NUMERIC,
    salary_currency VARCHAR,
    description     TEXT,
    source          VARCHAR,
    source_id       VARCHAR,
    posted_date     DATE,
    scraped_date    DATE,
    job_type        VARCHAR,
    experience_level VARCHAR,
    industry        VARCHAR,
    is_remote       BOOLEAN,
    skills          TEXT,
    created_at      TIMESTAMP,
    updated_at      TIMESTAMP
)

forecast_results (
    id               SERIAL PRIMARY KEY,
    skill_name       VARCHAR,
    forecast_date    DATE,
    predicted_demand NUMERIC,
    confidence_lower NUMERIC,
    confidence_upper NUMERIC,
    model_version    VARCHAR,
    region           VARCHAR,
    created_at       TIMESTAMP
)
```

**Row counts**: skill_demand (780), job_listings (~380), forecast_results (1,630)

---

## Port Map

| Service | Host Port | Container Port |
|---------|-----------|----------------|
| Frontend | 5173 | 3000 |
| API Server | 18080 | 8080 |
| ML Service | 5100 | 5000 |
| PostgreSQL | 5432 | 5432 |
| Redis | 16379 | 6379 |
| Spark Master | 7077, 8080, 4040 | 7077, 8080, 4040 |
| Spark Worker | 18081 | 8081 |
| Hadoop NameNode | 9870, 9000 | 9870, 9000 |
| Hadoop DataNode | 9864 | 9864 |
| HBase Master | 16010 | 16010 |
| Kafka Broker | 9092 | 9092 |
| Zookeeper | 2181 | 2181 |
| Airflow Webserver | 8888 | 8080 |

> **Note**: ML service uses port 5100 because Windows blocks ports 4937–5036.

---

## Docker Images

| Image | Source |
|-------|--------|
| `iatenoodles/bda-postgres:latest` | Docker Hub |
| `iatenoodles/bda-api-server:latest` | Docker Hub |
| `iatenoodles/bda-frontend:latest` | Docker Hub |
| `iatenoodles/bda-kafka-consumer:latest` | Docker Hub |
| `iatenoodles/bda-spark-jobs:latest` | Docker Hub |
| `bda-ml-service:latest` | Built locally |

---

## Environment Configuration

All configuration via `.env` (copy from `.env.example`):

### Big Data

```
HADOOP_NAMENODE_URI=hdfs://namenode:9000
HADOOP_REPLICATION=3
HADOOP_YARN_RESOURCEMANAGER=yarn-rm:8032
SPARK_MASTER=spark://spark-master:7077
SPARK_DRIVER_MEMORY=2g
SPARK_EXECUTOR_MEMORY=2g
SPARK_DEFAULT_PARALLELISM=200
KAFKA_BROKERS=kafka:9092
KAFKA_ZOOKEEPER=zookeeper:2181
KAFKA_PARTITIONS=4
KAFKA_COMPRESSION=snappy
KAFKA_RETENTION_HOURS=168
HBASE_HOST=hbase-master
HBASE_ZOOKEEPER=zk
HBASE_MASTER_PORT=16010
HBASE_REGION_PORT=16020
```

### Database & Cache

```
POSTGRES_HOST=postgres
POSTGRES_DB=job_market
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
REDIS_HOST=redis
REDIS_PASSWORD=redis123
REDIS_TTL=3600
REDIS_EVICTION=allkeys-lru
REDIS_MAXMEMORY=2gb
```

### API & Frontend

```
API_PORT=8080
API_WORKERS=4
JWT_SECRET=your-secret
JWT_EXPIRY=24h
VITE_API_URL=http://localhost:8080
```

### Airflow

```
AIRFLOW_EXECUTOR=LocalExecutor
AIRFLOW_DB=airflow
AIRFLOW_USER=admin
AIRFLOW_PASSWORD=admin
```

### Pipeline

```
PIPELINE_SCHEDULE=0 2 * * *
PIPELINE_BATCH_SIZE=10000
PIPELINE_ETL_TIMEOUT=1800
```

### Feature Flags

```
FEATURE_STREAMING=false
FEATURE_ML_FORECASTING=true
FEATURE_REALTIME_DASHBOARDS=false
FEATURE_DATA_EXPORT=true
FEATURE_ADVANCED_ANALYTICS=false
```

### Security

```
SSL_ENABLED=false
CORS_ORIGIN=localhost:3000
RATE_LIMIT=1000/min
```

### External APIs

```
INDEED_API_KEY=
LINKEDIN_API_KEY=
GLASSDOOR_API_KEY=
```

### AWS

```
AWS_S3_BUCKET=
AWS_ACCESS_KEY=
AWS_SECRET_KEY=
```

### Email

```
SMTP_HOST=
SMTP_PORT=
SMTP_USER=
SMTP_PASSWORD=
```

---

## ETL Refresh

Re-run the full pipeline when data updates:

```bash
python preprocess_jobstreet.py
python backend/database/etl_synthetic.py
docker-compose down -v && docker-compose up -d postgres ml-service api-server frontend
```

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Data ingestion | 100K+ records/min |
| Query latency (p95) | < 500ms |
| Forecast generation | < 5 min (full dataset) |
| Forecast query | ~50ms (precomputed SARIMA) |
| Dashboard load | < 2s |
| Data freshness | 1 hour (batch) + real-time (streaming) |

---

## Forecast Accuracy

| Period | Confidence | Notes |
|--------|-----------|-------|
| 2025 | High | Within training data range |
| 2026 | Medium | 1 year extrapolation |
| 2027 | Lower | 31-month horizon, intervals widen significantly |

Confidence intervals are at 95%. The `cap_forecasts.py` post-processor clamps values to 5× historical maximum per skill to prevent unrealistic projections.

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Real data + synthetic fallback** | System always has data; graceful degradation if Jobstreet unavailable |
| **Precomputed SARIMA forecasts** | 50ms queries vs 60s auto_arima runtime per skill |
| **SARIMA over Exponential Smoothing** | Captures both trend and annual seasonality |
| **Python ML + Java API + React frontend** | Separation of concerns; each layer independently scalable |
| **Port 5100 for ML service** | Windows blocks ports 4937–5036 |
| **Spike exclusion in Linear Regression** | Feb–Jun 2024 scrape spike distorts trend; model excludes these months |
| **Forecast capping** | Prevents unrealistic exponential growth projections |
| **CORS all origins on /api/** | Development convenience; restrict in production |

---

## Development

### Backend — API Server

```bash
cd backend/api-server
mvn spring-boot:run
```

### Backend — ML Service

```bash
cd backend/ml-service
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 5000
```

### Backend — Spark Jobs

```bash
cd backend/spark-jobs
mvn clean package
spark-submit target/job-*.jar
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Testing

```bash
# Backend unit tests
cd backend/api-server && mvn test

# Backend integration tests
cd backend/api-server && mvn verify

# Frontend tests
cd frontend && npm test

# End-to-end tests
cd frontend && npm run test:e2e
```

## Deployment

See [SETUP.md](docs/SETUP.md) for:
- **Kubernetes**: Manifests in `k8s/` directory (planned)
- **Cloud**: AWS S3 backups, GCP/Azure compatible
- **Production configuration**: SSL, rate limiting, CORS hardening
- **Scaling guidelines**: See [SCALING.md](docs/SCALING.md)

---

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, data flow, component interactions |
| [SETUP.md](docs/SETUP.md) | Installation, configuration, troubleshooting |
| [API.md](docs/API.md) | Full REST API reference |
| [DATA_PIPELINE.md](docs/DATA_PIPELINE.md) | ETL workflows, Spark jobs, data lineage |
| [SCALING.md](docs/SCALING.md) | Performance tuning, cluster setup, capacity planning |

---

## Contributing

1. Create a feature branch
2. Make changes with tests
3. Submit a pull request

---

## License

MIT

## Support

- **Issues**: GitHub Issues
- **Docs**: See `/docs` folder
- **Questions**: See Discussions tab