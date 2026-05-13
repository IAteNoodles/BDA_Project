# Job Market Demand Forecasting System

Predictive analytics platform for job market trends using Big Data processing, machine learning, and real-time visualization.

## Overview

Processes massive job posting datasets (millions of records) to forecast demand trends across industries, regions, and skill categories. Uses Hadoop ecosystem for distributed processing and modern web UI for insights visualization.

## Key Features

- **Big Data Processing**: Hadoop MapReduce + Apache Spark for ETL pipelines
- **Real-time Analytics**: Apache Kafka streaming job posting feeds
- **Data Warehouse**: HBase for structured NoSQL storage, Hive for SQL queries
- **ML Forecasting**: Spark MLlib for predictive models (time series, demand clustering)
- **Interactive Dashboard**: React/D3.js frontend with responsive visualizations
- **REST API**: Spring Boot microservices for data queries
- **Data Ingestion**: Flume/Sqoop for batch and incremental data loads
- **Orchestration**: Apache Airflow for workflow scheduling

## Tech Stack

### Big Data Layer
- **Hadoop 3.x** - HDFS, MapReduce
- **Apache Spark 3.x** - ETL, Analytics, MLlib
- **Apache Kafka** - Real-time streaming
- **HBase** - NoSQL data store
- **Hive** - SQL on Hadoop
- **Flume/Sqoop** - Data ingestion
- **Apache Airflow** - Workflow orchestration

### Backend
- **Java 17** - Core processing
- **Spring Boot 3.x** - REST APIs
- **PostgreSQL** - Metadata, forecasts
- **Redis** - Caching

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **D3.js/Chart.js** - Data visualizations
- **Tailwind CSS** - Styling
- **Vite** - Build tool

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Local orchestration
- **Kubernetes** - Production deployment

## Project Structure

```
job-market-forecasting/
├── docs/                          # Documentation
│   ├── ARCHITECTURE.md           # System design
│   ├── SETUP.md                  # Installation guide
│   ├── API.md                    # API documentation
│   └── DATA_PIPELINE.md          # ETL workflows
├── backend/
│   ├── spark-jobs/               # Spark ETL jobs
│   │   ├── src/
│   │   ├── pom.xml
│   │   └── Dockerfile
│   ├── kafka-consumer/           # Real-time ingestion
│   ├── api-server/               # Spring Boot REST API
│   │   ├── src/
│   │   ├── pom.xml
│   │   └── Dockerfile
│   ├── airflow/                  # DAGs & workflows
│   │   ├── dags/
│   │   └── docker-compose.yml
│   └── config/                   # Hadoop, Hive, HBase configs
├── frontend/
│   ├── src/
│   │   ├── components/           # React components
│   │   │   ├── Dashboard/
│   │   │   ├── JobTrends/
│   │   │   ├── Forecasts/
│   │   │   └── Filters/
│   │   ├── pages/
│   │   ├── services/            # API clients
│   │   ├── hooks/               # Custom hooks
│   │   ├── store/               # State management (Redux)
│   │   └── App.tsx
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── data/                         # Sample datasets
│   ├── raw/                      # Raw job postings
│   ├── processed/                # Processed data
│   └── schemas/
├── docker-compose.yml            # Full stack orchestration
├── .env.example                  # Environment template
└── README.md

```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Git
- 8GB RAM, 50GB disk space

### Local Development

```bash
# Clone repo
git clone <repo>
cd job-market-forecasting

# Configure environment
cp .env.example .env

# Start full stack
docker-compose up -d

# Wait for services to be healthy (2-3 min)
docker-compose ps

# Access services
Frontend:   http://localhost:3000
API:        http://localhost:8080
Spark UI:   http://localhost:4040
Hadoop UI:  http://localhost:9870
HBase UI:   http://localhost:16010
```

## Data Pipeline

1. **Ingestion**: Job postings collected from APIs/scraping
2. **Kafka Stream**: Real-time feed buffering
3. **HDFS Storage**: Raw data persisted
4. **Spark ETL**: Clean, transform, enrich
5. **Hive Tables**: Structured data warehouse
6. **HBase**: Hot data for real-time queries
7. **Analytics**: Spark MLlib forecasts
8. **PostgreSQL**: Results & aggregations
9. **API Layer**: Expose via REST endpoints
10. **Frontend**: Interactive visualizations

## Core Workflows

### Batch Processing (Daily)
- Job posting ingestion from sources
- Cleaning & deduplication
- Feature extraction & enrichment
- Demand classification
- Forecast generation
- Results persisting

### Real-time Streaming
- Incoming job postings via Kafka
- Immediate classification
- Hot data cache update
- Dashboard refresh

### Analytics
- Trend analysis (3/6/12 months)
- Skill demand ranking
- Geographic heat mapping
- Salary correlation
- Growth predictions

## API Endpoints

```
GET  /api/trends               # Job demand trends
GET  /api/forecasts/:region    # Regional forecasts
GET  /api/skills/:skill        # Skill-specific data
GET  /api/companies/:company   # Company hiring trends
GET  /api/analytics/summary    # Dashboard summary
POST /api/search               # Advanced search
```

See [API.md](docs/API.md) for full specification.

## Monitoring & Logging

- **Spark**: Yarn UI + Spark History Server
- **Hadoop**: Namenode UI, Resource Manager
- **Logs**: Centralized (ELK Stack ready)
- **Metrics**: Prometheus + Grafana
- **Alerts**: Job failures, data quality issues

## Configuration

Key env vars in `.env`:

```
# Hadoop
HADOOP_NAMENODE_URI=hdfs://namenode:9000
HADOOP_YARN_RESOURCEMANAGER=yarn-rm:8032

# Spark
SPARK_MASTER=spark://spark-master:7077
SPARK_EXECUTOR_MEMORY=2g

# Kafka
KAFKA_BROKERS=kafka:9092

# Backend
DB_HOST=postgres
REDIS_HOST=redis

# Frontend
REACT_APP_API_URL=http://localhost:8080
```

## Development

### Backend Development
```bash
cd backend/api-server
mvn spring-boot:run
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Spark Job Development
```bash
cd backend/spark-jobs
mvn clean package
spark-submit target/job-*.jar
```

## Testing

```bash
# Unit tests
mvn test

# Integration tests
mvn verify

# Frontend tests
npm test

# End-to-end
npm run test:e2e
```

## Deployment

See [SETUP.md](docs/SETUP.md) for:
- Kubernetes deployment
- Cloud setup (AWS/GCP/Azure)
- Production configuration
- Scaling guidelines

## Documentation

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System design, data flow, components
- **[SETUP.md](docs/SETUP.md)** - Installation, configuration, troubleshooting
- **[API.md](docs/API.md)** - REST API reference
- **[DATA_PIPELINE.md](docs/DATA_PIPELINE.md)** - ETL workflows, Spark jobs
- **[SCALING.md](docs/SCALING.md)** - Performance tuning, cluster setup

## Performance Targets

- **Data ingestion**: 100K+ records/min
- **Query latency**: <500ms (p95)
- **Forecast generation**: <5min for full dataset
- **Dashboard load**: <2s
- **Data freshness**: 1 hour (batch) + real-time (streaming)

## Contributing

1. Create feature branch
2. Make changes
3. Add tests
4. Submit PR

## License

MIT

## Support

- Issues: GitHub Issues
- Docs: See `/docs` folder
- Questions: See Discussions tab
