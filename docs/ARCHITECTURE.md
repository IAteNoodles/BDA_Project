# System Architecture

## Overview

Multi-layered distributed system processing job market data at scale using Hadoop ecosystem, streaming, ML, and modern frontend.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       FRONTEND LAYER                             │
│  React SPA + D3.js Visualizations + Redux State Management       │
└─────────────────┬───────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────────┐
│                      API GATEWAY LAYER                           │
│  Spring Boot REST API + JWT Auth + Rate Limiting + Caching       │
└─────────────────┬───────────────────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
┌───────▼────────┐  ┌───────▼────────┐
│  PostgreSQL    │  │     Redis      │
│  (Results, DB) │  │   (Cache)      │
└────────────────┘  └────────────────┘
        │
┌───────▼──────────────────────────────────────────────────────────┐
│                   PROCESSING LAYER                               │
│  Spark SQL + MLlib + Hive + HBase                                │
└───────┬──────────────────────────────────────────────────────────┘
        │
        ├─────────────────────────┬──────────────────────────┐
        │                         │                          │
┌───────▼──────────┐  ┌──────────▼──────┐  ┌──────────────▼──┐
│ Batch Processing │  │  Real-time      │  │  Machine       │
│ (Daily ETL)      │  │  Streaming      │  │  Learning      │
│                  │  │  (Kafka)        │  │  (Forecasts)   │
└───────┬──────────┘  └──────────┬──────┘  └──────────┬──────┘
        │                        │                     │
┌───────▼────────────────────────▼─────────────────────▼────────┐
│               STORAGE LAYER (Hadoop Ecosystem)                 │
│  HDFS + HBase + Hive Metastore                                 │
└──────────────────────────────────────────────────────────────┘
        │
┌───────▼──────────────────────────────────────────────────────┐
│               DATA INGESTION LAYER                             │
│  Flume + Sqoop + Kafka Producers                               │
└──────────────────────────────────────────────────────────────┘
        │
        └─────────────────────────┬────────────────────────┐
                                  │                        │
                        ┌─────────▼──────┐  ┌──────────────▼──┐
                        │  External APIs │  │   Web Scraping  │
                        │  (Job Boards)  │  │   Services      │
                        └────────────────┘  └─────────────────┘
```

## Components Deep Dive

### 1. Data Ingestion Layer

#### Kafka Producers
- Connect to job posting APIs (LinkedIn, Indeed, Glassdoor)
- Publish ~10K+ messages/min to Kafka topics
- Topics:
  - `job-postings-raw`: Unfiltered feed
  - `job-postings-dedupe`: De-duplicated
  - `job-postings-events`: Hiring events

```
Topic Partitioning:
└── job-postings-raw
    ├── Partition 0 → [Region: NA]
    ├── Partition 1 → [Region: EU]
    ├── Partition 2 → [Region: APAC]
    └── Partition 3 → [Region: Other]
```

#### Flume
- Batch ingest from file sources
- One agent per data center
- Sinks to HDFS `/data/raw/job_postings/`

#### Sqoop
- Import historical job data from relational databases
- Incremental imports (delta loads)
- Schedule: Daily 02:00 UTC

### 2. Storage Layer (Hadoop)

#### HDFS Directory Structure
```
/data/
├── raw/
│   ├── job_postings/YYYY/MM/DD/
│   ├── company_data/YYYY/MM/
│   └── historical_archive/
├── processed/
│   ├── job_postings_cleaned/
│   ├── job_postings_enriched/
│   └── skill_matrix/
├── models/
│   ├── demand_forecast_model_v2/
│   └── skill_classifier_model_v3/
└── warehouse/
    ├── hive_tables/
    └── aggregations/
```

#### HBase Tables
```
Table: job_postings_live
├── RowKey: [company_id]_[posting_id]_[ts]
├── CF: posting (title, description, salary)
├── CF: metadata (created, updated, status)
└── CF: enriched (skills, classification, sentiment)

Table: demand_index
├── RowKey: [date]_[region]_[skill]
├── CF: metrics (count, avg_salary, growth_rate)
└── CF: forecast (30d, 90d, 180d)

Table: skill_index
├── RowKey: [skill_name]_[timestamp]
└── CF: stats (frequency, trend, salary_percentile)
```

#### Hive Tables (SQL Layer)
```sql
-- Managed tables in Hive warehouse
job_postings_stg        -- Staging (raw data)
job_postings_fact       -- Fact table (cleaned, dedupe)
job_details_dim         -- Job dimensions
company_dim             -- Company information
location_dim            -- Geographic data
skill_dim               -- Skill categories
industry_dim            -- Industry classification
demand_forecast         -- Model outputs
```

### 3. Processing Layer

#### Batch ETL Pipeline (Spark)

Daily schedule (02:00 UTC, ~30 min execution):

```
Step 1: Data Ingestion (5 min)
  ├── Read from Kafka last 24h
  ├── Read Sqoop delta from HDFS
  └── Merge data sources

Step 2: Data Cleaning (8 min)
  ├── Remove nulls & duplicates
  ├── Standardize text (lowercase, trim)
  ├── Validate salary ranges
  └── Filter spam/bot postings
  Result → HDFS /processed/clean/

Step 3: Data Enrichment (10 min)
  ├── Extract skills (regex + NLP)
  ├── Map companies to MNC database
  ├── Geocode locations
  ├── Classify industries
  └── Sentiment analysis on descriptions
  Result → HDFS /processed/enriched/

Step 4: Aggregation (4 min)
  ├── Group by (date, region, skill, industry)
  ├── Calculate: count, avg_salary, growth
  └── Update HBase tables
  
Step 5: Feature Engineering (2 min)
  ├── Create time-series features
  ├── Lag features (t-1, t-7, t-30 days)
  └── Exponential moving averages

Step 6: Model Training (1 min)
  ├── ARIMA for time series
  ├── LightGBM for classification
  └── Save models to HDFS
```

#### Real-time Streaming (Kafka → Spark Streaming)

```
Kafka Consumer
  ├── Buffer window: 30 seconds
  ├── Process 1K records/batch
  └── Actions:
      ├── Update HBase live tables
      ├── Cache in Redis (5 min TTL)
      ├── WebSocket push to dashboards
      └── Trigger ML inference
```

#### Machine Learning (Spark MLlib)

Models trained daily:

**1. Demand Forecasting (ARIMA)**
- Input: Historical demand (12 months)
- Output: 30/90/180 day forecasts
- Features: Trend, seasonality, external regressors
- Accuracy target: RMSE < 5%

**2. Skill Classification (LightGBM)**
- Input: Job posting text
- Output: Skill categories + proficiency
- Classes: 500+ skills
- Accuracy target: F1 > 0.92

**3. Anomaly Detection (Isolation Forest)**
- Input: Job posting features
- Output: Spam/bot probability
- Threshold: 0.85
- Precision target: > 0.98

**4. Trend Clustering (K-means)**
- Input: Skill demand vectors
- Output: Emerging skill clusters
- K: 20 clusters
- Update: Monthly

### 4. API Layer

#### Spring Boot Microservices

```
api-server/
├── controllers/
│   ├── TrendsController
│   ├── ForecastController
│   ├── SkillsController
│   ├── LocationsController
│   └── AnalyticsController
├── services/
│   ├── TrendService
│   ├── ForecastService
│   ├── SkillService
│   └── CacheService
├── repositories/
│   ├── PostgreSQLRepo (forecasts)
│   ├── HBaseRepo (live data)
│   └── RedisRepo (cache)
└── config/
    ├── SecurityConfig (JWT)
    └── CacheConfig
```

#### Key Endpoints

```
GET  /api/trends
     ├── Query params: region, skill, industry, start_date, end_date
     ├── Cache: 1 hour
     └── Response: {date, count, avg_salary, growth_rate}

GET  /api/forecasts/{region}
     ├── Path param: region
     ├── Query params: days_ahead (30/90/180)
     └── Response: {date, predicted_demand, confidence_interval}

GET  /api/skills/{skill}
     ├── Path param: skill
     ├── Query params: region, time_period
     └── Response: {frequency, salary, trend_vector, related_skills}

GET  /api/locations
     ├── Query params: skill
     ├── Response: {city, state, count, salary_median}

POST /api/search
     ├── Body: {filters: {skills, regions, salary_range, industries}}
     └── Response: Paginated job postings + stats
```

#### Caching Strategy

```
Redis Cache Layers:
├── L1: Result cache (1 hour TTL)
│   └── Key: "trend:{region}:{skill}:{date_range}"
├── L2: Model cache (24 hour TTL)
│   └── Key: "forecast:{region}:{days}"
└── L3: Dimension cache (7 day TTL)
    └── Key: "skill_list", "location_list"

Cache Invalidation:
├── TTL-based (automatic)
├── Event-based (on new data load)
└── Manual (admin API)
```

### 5. Frontend Layer

#### React Component Architecture

```
App.tsx
├── Layout
│   ├── Header (navigation, user profile)
│   ├── Sidebar (filters, menu)
│   └── MainContent
│
├── Pages
│   ├── Dashboard/
│   │   ├── DemandMetrics (KPI cards)
│   │   ├── TrendChart (line chart)
│   │   ├── SkillHeatmap (matrix)
│   │   └── RegionalMap (geo visualization)
│   │
│   ├── Trends/
│   │   ├── TrendFilters
│   │   ├── HistoricalChart
│   │   └── TrendComparison
│   │
│   ├── Forecasts/
│   │   ├── ForecastSelector
│   │   ├── PredictionChart
│   │   └── ConfidenceInterval
│   │
│   ├── Skills/
│   │   ├── SkillSearch
│   │   ├── SkillRanking
│   │   └── SkillCorrelation
│   │
│   └── Analytics/
│       ├── AdvancedFilters
│       ├── DataExport
│       └── Reports
│
├── Hooks
│   ├── useFetchTrends
│   ├── useFetchForecasts
│   ├── useDebounce
│   └── useLocalStorage
│
└── Redux Store
    ├── trendsSlice
    ├── forecastsSlice
    ├── filtersSlice
    └── uiSlice
```

#### Visualizations

- **Line Charts** (D3.js): Demand trends over time
- **Heatmaps**: Skill × Region demand matrix
- **Geo Maps** (Mapbox): Regional heat mapping
- **Bar Charts** (Chart.js): Top skills, companies
- **Sankey Diagram**: Skill flow/transitions
- **Scatter Plot**: Salary vs demand correlation

#### Performance Optimizations

```
Frontend Optimization:
├── Code splitting (route-based)
├── Lazy loading (charts on scroll)
├── Virtual scrolling (large lists)
├── Memoization (React.memo, useMemo)
├── WebSocket (real-time updates)
├── Service Worker (offline support)
└── Image optimization (WebP format)

Load Time Targets:
├── Initial: < 2s
├── Interactive: < 3s
├── Chart render: < 500ms
└── API response: < 500ms (p95)
```

## Data Flow Example: Job Posting

```
1. Source System (Job Board API)
   └─→ JSON: {title, company, location, skills, salary, description}

2. Kafka Topic: job-postings-raw
   └─→ 10,000 msgs/min partitioned by region

3. Kafka Consumer (Spark Streaming)
   ├─→ Deserialize JSON
   ├─→ Basic validation
   └─→ Write to HBase (live table)

4. Daily Batch ETL
   ├─→ Read from Kafka + HDFS raw
   ├─→ Deduplicate (posting_id + company)
   ├─→ Clean text, standardize formats
   ├─→ Extract skills via NLP
   ├─→ Classify industry
   ├─→ Write to HDFS /processed/
   └─→ Write to Hive tables

5. ML Inference
   ├─→ Load pre-trained skill classifier
   ├─→ Predict skill categories
   ├─→ Score anomaly (spam detection)
   └─→ Update HBase enriched columns

6. Aggregation
   ├─→ Group by (date, region, skill)
   ├─→ Calculate demand metrics
   └─→ Update HBase demand_index table

7. API Query
   ├─→ GET /api/trends?region=CA&skill=Python
   ├─→ Spring Boot service hits HBase
   ├─→ Redis check (cache hit/miss)
   ├─→ Return JSON to frontend
   └─→ Cache result for 1 hour

8. Frontend Display
   ├─→ Fetch from /api/trends
   ├─→ Redux dispatch action
   ├─→ Render D3 chart
   └─→ User sees trend over time
```

## Scalability & Performance

### Horizontal Scaling

```
Kafka Partitions: 4 (region-based)
  ├─→ Scale up: Add partitions (resharding needed)
  └─→ Consumers: Match partition count

Spark Executors:
  ├─→ Dev: 2 executors × 2GB
  ├─→ Prod: 16 executors × 4GB
  └─→ Scaling: YARN auto-scales based on queue

HDFS Replication:
  ├─→ Dev: 1 replica
  ├─→ Prod: 3 replicas
  └─→ Block size: 256MB (default)

API Servers:
  ├─→ Dev: 1 instance
  ├─→ Prod: 3+ instances (load balanced)
  └─→ Scaling: Kubernetes auto-scaling (HPA)

Frontend:
  ├─→ CDN: CloudFront/Cloudflare
  ├─→ Caching: Aggressive for static assets
  └─→ Instances: Stateless (horizontal scale)
```

### Performance Optimization

```
Query Optimization:
├── Partitioning: By date, region
├── Indexing: HBase Bloom filters
├── Caching: Redis L1/L2
└── Sampling: For large date ranges

Processing Optimization:
├── Spark: Broadcast joins, partition pruning
├── Hive: Bucketing, compression (Snappy)
├── Parallelism: 200-400 partitions
└── Memory: Tuned GC, off-heap cache

Network Optimization:
├── Compression: Gzip API responses
├── Pagination: Default 100 records
├── Filtering: Server-side only
└── Delta sync: Only changed data
```

## Disaster Recovery

```
Backup Strategy:
├── HDFS: Snapshots daily
├── HBase: Incremental backups (2h frequency)
├── PostgreSQL: WAL + daily dumps
└── Config: Git versioned

Recovery SLA:
├── RTO (Recovery Time Objective): 1 hour
├── RPO (Recovery Point Objective): 15 minutes
└── Test recovery: Monthly drill

Replication:
├── Active-Passive: Standby cluster
├── Cross-region: S3/GCS mirroring
└── Failover: Automated DNS switch
```

## Monitoring & Observability

```
Metrics Collected:
├── Spark: Task success rate, execution time
├── Hadoop: Namenode memory, HDFS usage
├── Kafka: Consumer lag, throughput
├── HBase: Read/write latency, GC time
├── API: Response time, error rate, QPS
└── Frontend: Page load time, error rate

Alerting Thresholds:
├── Kafka lag > 5 min → critical
├── API error rate > 1% → warning
├── Forecast job duration > 45 min → alert
└── Disk usage > 80% → alert

Dashboards:
├── Operations: Cluster health, resource usage
├── Data Pipeline: ETL status, volumes
├── API Performance: Latency, throughput
└── Business: Data quality, forecast accuracy
```

## Security

```
Authentication:
├── API: JWT tokens (RS256)
├── Services: HTTPS + mTLS
└── Hadoop: Kerberos (production)

Authorization:
├── Role-based (Admin, Analyst, Viewer)
├── Data-level: Region/skill filters
└── API rate limiting: 1000 req/min per token

Data Security:
├── Encryption at rest: AES-256
├── Encryption in transit: TLS 1.2+
├── PII masking: Salary hashing
└── Audit logs: All API access
```
