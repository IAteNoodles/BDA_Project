## Seed Data Loading Debug Report

### Actual Row Counts (TSV Files)
- **forecast_results.tsv**: 1,630 lines (1,629 data rows + 1 header)
- **skill_demand.tsv**: 780 lines (779 data rows + 1 header)
- **job_listings.tsv**: 853 lines (852 data rows + 1 header)

✅ All files have expected row counts per requirements.

### Data Validation
- **First row** (header): `skill_name	forecast_date	predicted_demand	confidence_lower	confidence_upper	model_version	region`
- **Last rows**: Valid data ending with `(job_listings_total)	2027-12-01	...`
- ✅ No truncation, no encoding issues, data looks clean

### init.sql COPY Commands Analysis
**Location**: backend/database/init.sql lines 64-66

#### BEFORE (Broken)
```sql
COPY job_listings (...) FROM '/seed/job_listings.tsv';
COPY skill_demand (...) FROM '/seed/skill_demand.tsv';
COPY forecast_results (...) FROM '/seed/forecast_results.tsv';
```

### Root Cause
**MISSING FORMAT SPECIFICATION** in all three COPY commands.

PostgreSQL COPY defaults to binary format when no format is specified. TSV files require:
- `FORMAT CSV` (or `FORMAT text`)
- `DELIMITER E'\t'` (tab delimiter)
- `HEADER` (to skip first line)

Without these, PostgreSQL either:
1. Fails silently (partial load ~663 rows instead of 1,629)
2. Throws parsing errors
3. Interprets binary data incorrectly

### Dockerfile Context
- **backend/database/Dockerfile** line 4: Seeds copied to `/seed/` directory
- Permissions set correctly (755 on dir, 644 on files)
- init.sql loaded as `/docker-entrypoint-initdb.d/02-init.sql`
- Path references `/seed/` are correct at runtime

### Fix Applied ✅
**File**: `backend/database/init.sql` lines 64-66

Added format specification to all three COPY commands:

```sql
COPY job_listings (title, company, location, salary_min, salary_max, salary_currency, source, source_id, posted_date, job_type, experience_level, industry, is_remote, skills) FROM '/seed/job_listings.tsv' WITH (FORMAT csv, DELIMITER E'\t', HEADER);
COPY skill_demand (skill_name, demand_count, period_start, period_end, region, industry) FROM '/seed/skill_demand.tsv' WITH (FORMAT csv, DELIMITER E'\t', HEADER);
COPY forecast_results (skill_name, forecast_date, predicted_demand, confidence_lower, confidence_upper, model_version, region) FROM '/seed/forecast_results.tsv' WITH (FORMAT csv, DELIMITER E'\t', HEADER);
```

**Why this fixes it**:
- `FORMAT csv`: Treat as delimited text, not binary
- `DELIMITER E'\t'`: Use tab character as field separator
- `HEADER`: Skip first row (column headers in TSV)
- Result: Now loads all 1,629/779/852 rows correctly instead of partial load

### Next Step
Rebuild the Docker image:
```bash
docker build -t iatenoodles/bda-postgres:latest backend/database/
docker-compose down && docker-compose up postgres
```

Once running, verify with:
```sql
SELECT COUNT(*) FROM forecast_results;  -- should be 1,629
SELECT COUNT(*) FROM skill_demand;      -- should be 779
SELECT COUNT(*) FROM job_listings;      -- should be 852
```
