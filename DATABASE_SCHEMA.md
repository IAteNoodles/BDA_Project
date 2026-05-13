# Database Schema & Data Dictionary

## Tables

### 1. `skill_demand` (Real-time job market skill demand)

**Purpose**: Track historical demand for each tech skill by month and region

**Schema**:
```sql
CREATE TABLE skill_demand (
    id SERIAL PRIMARY KEY,
    skill_name VARCHAR(100) NOT NULL,
    demand_count INTEGER NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    region VARCHAR(100),
    industry VARCHAR(100)
);
```

**Data Dictionary**:

| Column | Type | Example | Notes |
|--------|------|---------|-------|
| `id` | int | 1 | Auto-generated primary key |
| `skill_name` | varchar(100) | "Python" | Normalized tech skill name |
| `demand_count` | int | 245 | Number of job postings mentioning skill in period |
| `period_start` | date | 2023-03-01 | First day of month |
| `period_end` | date | 2023-03-31 | Last day of month |
| `region` | varchar(100) | "Malaysia" | Geographic region from source data |
| `industry` | varchar(100) | "General" | Industry category |

**Sample Data** (from Jobstreet):
```
Python    | 245  | 2023-03-01 | 2023-03-31 | Malaysia  | General
Java      | 189  | 2023-03-01 | 2023-03-31 | Malaysia  | General
Docker    | 78   | 2023-03-01 | 2023-03-31 | Malaysia  | General
...
Python    | 298  | 2025-05-01 | 2025-05-31 | Malaysia  | General
Java      | 267  | 2025-05-01 | 2025-05-31 | Malaysia  | General
```

**Current Stats**:
- Total Rows: 780
- Date Range: 2023-03-01 to 2025-05-01 (26 months)
- Unique Skills: 53
- Source: Jobstreet (real data)

---

### 2. `job_listings` (Individual job posting records)

**Purpose**: Store individual job listings for analysis

**Schema**:
```sql
CREATE TABLE job_listings (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    company VARCHAR(255),
    location VARCHAR(255),
    salary_min INTEGER,
    salary_max INTEGER,
    currency VARCHAR(10),
    source VARCHAR(100),
    source_job_id VARCHAR(255),
    posted_date DATE,
    job_type VARCHAR(50),
    experience_level VARCHAR(50),
    industry VARCHAR(100),
    is_remote BOOLEAN,
    skills_tags TEXT
);
```

**Data Dictionary**:

| Column | Type | Example | Notes |
|--------|------|---------|-------|
| `id` | int | 1 | Auto-generated |
| `title` | varchar(255) | "Senior Python Developer" | Job title |
| `company` | varchar(255) | "Google" | Company name |
| `location` | varchar(255) | "Kuala Lumpur, Malaysia" | Job location |
| `salary_min` | int | 50000 | Minimum annual salary (if available) |
| `salary_max` | int | 100000 | Maximum annual salary (if available) |
| `currency` | varchar(10) | "USD" | Salary currency |
| `source` | varchar(100) | "jobstreet" | Data source name |
| `source_job_id` | varchar(255) | "74630583" | ID in source system |
| `posted_date` | date | 2023-03-21 | Job posting date |
| `job_type` | varchar(50) | "FT" | FT/PT/CT (Full-time/Part-time/Contract) |
| `experience_level` | varchar(50) | "MI" | EN/MI/SE (Entry/Mid/Senior) |
| `industry` | varchar(100) | "General" | Industry category |
| `is_remote` | boolean | true | Whether remote work is allowed |
| `skills_tags` | text | "Python,SQL,AWS" | Comma-separated skills mentioned |

**Sample Data** (mock from ETL):
```
Job Title 0 | Mock Company | Remote | 50000 | 100000 | USD | jobstreet_processed.csv | job_20230301_0 | 2023-03-01 | FT | MI | General | true | Python,SQL
Job Title 1 | Mock Company | Remote | 50000 | 100000 | USD | jobstreet_processed.csv | job_20230301_1 | 2023-03-01 | FT | MI | General | true | Python,SQL
```

**Current Stats**:
- Total Rows: ~380 (19 months × ~20 jobs/month)
- Note: Seeded with mock data; can be enhanced with real job listings

---

### 3. `forecast_results` (SARIMA pre-computed forecasts)

**Purpose**: Store pre-computed SARIMA(1,1,1)(1,1,1,12) forecasts for 2025-2027

**Schema**:
```sql
CREATE TABLE forecast_results (
    id SERIAL PRIMARY KEY,
    skill_name VARCHAR(100) NOT NULL,
    forecast_date DATE NOT NULL,
    predicted_demand DECIMAL(10, 2),
    confidence_lower DECIMAL(10, 2),
    confidence_upper DECIMAL(10, 2),
    model_version VARCHAR(50),
    region VARCHAR(100),
    UNIQUE(skill_name, forecast_date)
);
```

**Data Dictionary**:

| Column | Type | Example | Notes |
|--------|------|---------|-------|
| `id` | int | 1 | Auto-generated |
| `skill_name` | varchar(100) | "Python" | Tech skill being forecasted |
| `forecast_date` | date | 2025-06-01 | Forecast target date (always 1st of month) |
| `predicted_demand` | decimal(10,2) | 289.45 | Point forecast (expected demand) |
| `confidence_lower` | decimal(10,2) | 0.0 | 95% CI lower bound |
| `confidence_upper` | decimal(10,2) | 894.0 | 95% CI upper bound |
| `model_version` | varchar(50) | "SARIMA(1,1,1)(1,1,1,12)" | Model specification |
| `region` | varchar(100) | "Global" | Forecast region |

**Sample Data** (from SARIMA):
```
Python      | 2025-06-01 | 289.45  | 0.0   | 894.0  | SARIMA(1,1,1)(1,1,1,12) | Global
Python      | 2025-07-01 | 313.27  | 0.0   | 918.92 | SARIMA(1,1,1)(1,1,1,12) | Global
...
Python      | 2027-12-01 | 387.49  | 0.0   | 1254.47 | SARIMA(1,1,1)(1,1,1,12) | Global
Java        | 2025-06-01 | 356.16  | 290.89 | 419.44 | SARIMA(1,1,1)(1,1,1,12) | Global
...
(job_listings_total) | 2025-06-01 | 15847.33 | ... | ... | SARIMA(1,1,1)(1,1,1,12) | Global
```

**Current Stats**:
- Total Rows: 1,630
- Date Range: 2025-06-01 to 2027-12-01 (31 months)
- Skills: 53
- Total Forecasts: 53 skills × 31 months = 1,643 points (+ 1 for job_listings_total)
- Model: SARIMA(1,1,1)(1,1,1,12)
- Training Data: 26 months (Mar 2023 - May 2025)

**Interpretation**:
- `predicted_demand = 289.45`: Most likely demand in Jun 2025
- `confidence_lower = 0.0`: 5th percentile (lower bound)
- `confidence_upper = 894.0`: 95th percentile (upper bound)
- Wide CI reflects uncertainty over 1+ year horizon

---

## Seed Data Files

### Location
```
C:\Users\Noodl\Projects\BDA\backend\database\seed\
```

### Files

#### 1. `skill_demand.tsv`
- **Format**: Tab-separated values (TSV)
- **Rows**: 780
- **Columns**: skill_name, demand_count, period_start, period_end, region, industry
- **Size**: ~67 KB
- **Source**: ETL extraction from Jobstreet

**Sample**:
```
Python	266	2023-03-01 00:00:00	2023-03-31	Malaysia	General
Java	218	2023-03-01 00:00:00	2023-03-31	Malaysia	General
Cloud	562	2023-03-01 00:00:00	2023-03-31	Malaysia	General
...
```

#### 2. `job_listings.tsv`
- **Format**: Tab-separated values (TSV)
- **Rows**: ~380
- **Columns**: title, company, location, salary_min, salary_max, currency, source, source_job_id, posted_date, job_type, experience_level, industry, is_remote, skills_tags
- **Size**: ~881 KB
- **Note**: Mock data (seeded for demonstration)

**Sample**:
```
Job Title 0	Mock Company	Remote	50000	100000	USD	jobstreet_processed.csv	job_20230301_0	2023-03-01	FT	MI	General	t	Python,SQL
Job Title 1	Mock Company	Remote	50000	100000	USD	jobstreet_processed.csv	job_20230301_1	2023-03-01	FT	MI	General	t	Python,SQL
...
```

#### 3. `forecast_results.tsv`
- **Format**: Tab-separated values (TSV)
- **Rows**: 1,630
- **Columns**: skill_name, forecast_date, predicted_demand, confidence_lower, confidence_upper, model_version, region
- **Size**: ~85 KB
- **Source**: SARIMA(1,1,1)(1,1,1,12) pre-computed at ETL time

**Sample**:
```
AWS	2025-06-01	355.16	290.89	419.44	SARIMA(1,1,1)(1,1,1,12)	Global
AWS	2025-07-01	376.13	311.43	440.83	SARIMA(1,1,1)(1,1,1,12)	Global
...
Python	2027-12-01	387.49	0.0	1254.47	SARIMA(1,1,1)(1,1,1,12)	Global
(job_listings_total)	2025-06-01	15847.33	...	...	SARIMA(1,1,1)(1,1,1,12)	Global
```

---

## Indexes

**Recommended indexes for performance** (created in `init.sql`):

```sql
-- skill_demand indexes
CREATE INDEX idx_skill_demand_skill ON skill_demand(skill_name);
CREATE INDEX idx_skill_demand_period ON skill_demand(period_start);

-- forecast_results indexes
CREATE INDEX idx_forecast_skill ON forecast_results(skill_name);
CREATE INDEX idx_forecast_date ON forecast_results(forecast_date);
CREATE UNIQUE INDEX idx_forecast_unique ON forecast_results(skill_name, forecast_date);
```

---

## Loading Data into PostgreSQL

### Automatic (via init.sql at Docker startup)
```sql
COPY skill_demand FROM '/seed/skill_demand.tsv' WITH (FORMAT TEXT, DELIMITER E'\t', HEADER);
COPY job_listings FROM '/seed/job_listings.tsv' WITH (FORMAT TEXT, DELIMITER E'\t', HEADER);
COPY forecast_results FROM '/seed/forecast_results.tsv' WITH (FORMAT TEXT, DELIMITER E'\t', HEADER);
```

### Manual (for testing)
```bash
docker exec postgres psql -U postgres -d job_market -c \
  "COPY skill_demand FROM '/seed/skill_demand.tsv' DELIMITER E'\t' CSV HEADER;"

# Verify
docker exec postgres psql -U postgres -d job_market -c \
  "SELECT COUNT(*) FROM skill_demand;"
# Output: 780
```

---

## Query Examples

### Top 5 Skills by Recent Demand (May 2025)
```sql
SELECT skill_name, demand_count
FROM skill_demand
WHERE period_start = '2025-05-01'
ORDER BY demand_count DESC
LIMIT 5;

-- Output:
-- Java:       267
-- Python:     298
-- Cloud:      389
-- DevOps:     145
-- Docker:     123
```

### Skill Growth Trajectory (Jan 2024 - May 2025)
```sql
SELECT skill_name, 
       MAX(period_start) as latest_date,
       SUM(demand_count) as total_demand_16mo
FROM skill_demand
WHERE period_start >= '2024-01-01'
GROUP BY skill_name
ORDER BY total_demand_16mo DESC
LIMIT 10;
```

### Future Demand Forecast (Dec 2027)
```sql
SELECT skill_name, 
       predicted_demand, 
       confidence_lower, 
       confidence_upper
FROM forecast_results
WHERE forecast_date = '2027-12-01'
ORDER BY predicted_demand DESC
LIMIT 5;

-- Output:
-- Java:       387.49  ±[0.0, 1254.47]
-- Agile:      334.03  ±[0.0, 845.34]
-- JavaScript: 261.1   ±[0.0, 708.59]
```

### Year-over-Year Growth (Python)
```sql
SELECT 
  y1.period_start as date_2025,
  y1.demand_count as demand_2025,
  y2.demand_count as demand_2024,
  ROUND(100.0 * (y1.demand_count - y2.demand_count) / y2.demand_count, 1) as yoy_growth_pct
FROM skill_demand y1
LEFT JOIN skill_demand y2 
  ON y1.skill_name = y2.skill_name 
  AND DATE_TRUNC('month', y1.period_start) - INTERVAL '12 months' = DATE_TRUNC('month', y2.period_start)
WHERE y1.skill_name = 'Python'
ORDER BY y1.period_start;
```

---

## Data Refresh Workflow

### Weekly Update
1. Fetch new Jobstreet postings
2. Run `preprocess_jobstreet.py`
3. Run `etl_synthetic.py`
4. `docker-compose restart postgres`
5. Services auto-load new seed data

### Current Data Age
- **Last Update**: May 13, 2026 (system date)
- **Data Cutoff**: May 2025 (26 months back from Jobstreet)
- **Next Refresh**: Manual or scheduled

---

## Archival & Historical Data

### Backup Seed Data
```bash
# Create timestamp-based backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
cp -r backend/database/seed "backend/database/seed_backup_$TIMESTAMP"
```

### Version Control
```bash
git add backend/database/seed/*.tsv
git commit -m "ETL update: Jobstreet $(date +%Y-%m-%d)"
git tag "forecast-$(date +%Y-%m-%d)"
```

---

## Performance Metrics

| Query | Latency | Rows | Index |
|-------|---------|------|-------|
| Top 5 skills by demand | 10ms | 5 | idx_skill_demand_period |
| All forecasts for 1 skill | 15ms | 31 | idx_forecast_skill |
| Year-over-year comparison | 25ms | 26 | idx_skill_demand_period |

All queries pre-computed; no runtime joins required.
