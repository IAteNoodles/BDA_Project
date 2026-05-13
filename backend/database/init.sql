-- Job Market Demand Forecasting System - Database Init
-- Connected to job_market database (created via POSTGRES_DB env var)

-- Job listings table
CREATE TABLE IF NOT EXISTS job_listings (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    company VARCHAR(255),
    location VARCHAR(255),
    salary_min DECIMAL(10,2),
    salary_max DECIMAL(10,2),
    salary_currency VARCHAR(3) DEFAULT 'USD',
    description TEXT,
    source VARCHAR(100),
    source_id VARCHAR(255),
    posted_date TIMESTAMP,
    scraped_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    job_type VARCHAR(50),
    experience_level VARCHAR(50),
    industry VARCHAR(100),
    is_remote BOOLEAN DEFAULT FALSE,
    skills TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Skill demand tracking
CREATE TABLE IF NOT EXISTS skill_demand (
    id BIGSERIAL PRIMARY KEY,
    skill_name VARCHAR(255) NOT NULL,
    demand_count INTEGER DEFAULT 0,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    region VARCHAR(100),
    industry VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Forecast results
CREATE TABLE IF NOT EXISTS forecast_results (
    id BIGSERIAL PRIMARY KEY,
    skill_name VARCHAR(255) NOT NULL,
    forecast_date DATE NOT NULL,
    predicted_demand DECIMAL(10,2),
    confidence_lower DECIMAL(10,2),
    confidence_upper DECIMAL(10,2),
    model_version VARCHAR(50),
    region VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_job_listings_title ON job_listings(title);
CREATE INDEX IF NOT EXISTS idx_job_listings_location ON job_listings(location);
CREATE INDEX IF NOT EXISTS idx_job_listings_posted_date ON job_listings(posted_date);
CREATE INDEX IF NOT EXISTS idx_job_listings_industry ON job_listings(industry);
CREATE INDEX IF NOT EXISTS idx_job_listings_experience ON job_listings(experience_level);
CREATE INDEX IF NOT EXISTS idx_skill_demand_skill ON skill_demand(skill_name);
CREATE INDEX IF NOT EXISTS idx_skill_demand_period ON skill_demand(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_forecast_skill ON forecast_results(skill_name);
CREATE INDEX IF NOT EXISTS idx_forecast_date ON forecast_results(forecast_date);

-- Seed data using COPY FROM STDIN
COPY job_listings (title, company, location, salary_min, salary_max, salary_currency, source, source_id, posted_date, job_type, experience_level, industry, is_remote, skills) FROM '/seed/job_listings.tsv';
COPY skill_demand (skill_name, demand_count, period_start, period_end, region, industry) FROM '/seed/skill_demand.tsv';
COPY forecast_results (skill_name, forecast_date, predicted_demand, confidence_lower, confidence_upper, model_version, region) FROM '/seed/forecast_results.tsv';