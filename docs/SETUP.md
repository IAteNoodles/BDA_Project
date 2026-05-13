# Setup & Installation Guide

## Prerequisites

### System Requirements

**Minimum (Local Development)**
- CPU: 4 cores
- RAM: 8 GB
- Disk: 50 GB SSD
- OS: Linux, macOS, or Windows (WSL2)

**Recommended (Production)**
- CPU: 16+ cores
- RAM: 64+ GB
- Disk: 500+ GB SSD
- OS: Linux (Ubuntu 20.04 LTS or CentOS 7+)

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- Git 2.30+
- Java 17 JDK
- Python 3.9+
- Node.js 18+ (frontend only)

### Install Docker & Docker Compose

**Linux (Ubuntu)**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

sudo usermod -aG docker $USER
newgrp docker

# Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify
docker --version
docker-compose --version
```

**macOS**
```bash
# Using Homebrew
brew install docker docker-compose
# Or download Docker Desktop from docker.com
```

**Windows**
- Install WSL2: https://docs.microsoft.com/windows/wsl/install
- Install Docker Desktop: https://www.docker.com/products/docker-desktop

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/job-market-forecasting.git
cd job-market-forecasting
```

### 2. Configure Environment

```bash
cp .env.example .env

# Edit .env for local development
nano .env
```

**Key environment variables:**

```env
# Hadoop
HADOOP_NAMENODE_URI=hdfs://namenode:9000
HADOOP_NAMENODE_HTTP_PORT=9870
HADOOP_DATANODE_PORT=50075

# Spark
SPARK_MASTER=spark://spark-master:7077
SPARK_EXECUTOR_MEMORY=2g
SPARK_EXECUTOR_CORES=2

# Kafka
KAFKA_BROKERS=kafka:9092
KAFKA_PARTITIONS=4
KAFKA_REPLICATION_FACTOR=1

# HBase
HBASE_HOST=hbase
HBASE_ZOOKEEPER_PORT=2181

# PostgreSQL
DB_HOST=postgres
DB_PORT=5432
DB_NAME=job_market
DB_USER=postgres
DB_PASSWORD=postgres123
DB_POOL_SIZE=10

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_TTL=3600

# API Server
API_PORT=8080
API_WORKERS=4
JWT_SECRET=your-secret-key-here

# Frontend
REACT_APP_API_URL=http://localhost:8080
REACT_APP_ENV=development

# Airflow
AIRFLOW_HOME=/airflow
AIRFLOW__CORE__DAGS_FOLDER=/airflow/dags
AIRFLOW__CORE__LOAD_EXAMPLES=false
```

### 3. Start Services

```bash
# Build images (first time)
docker-compose build

# Start all services in background
docker-compose up -d

# View logs
docker-compose logs -f

# Wait for services to be healthy (2-3 minutes)
docker-compose ps
```

**Expected services:**

```
NAME                    STATUS                 PORTS
namenode                Up                     0.0.0.0:9870->9870/tcp
datanode                Up                     0.0.0.0:50075->50075/tcp
spark-master            Up                     0.0.0.0:7077->7077/tcp
spark-worker-1          Up                     0.0.0.0:8081->8081/tcp
kafka                   Up                     0.0.0.0:9092->9092/tcp
zookeeper               Up                     0.0.0.0:2181->2181/tcp
hbase                   Up                     0.0.0.0:16010->16010/tcp
postgres                Up (healthy)           0.0.0.0:5432->5432/tcp
redis                   Up (healthy)           0.0.0.0:6379->6379/tcp
api-server              Up                     0.0.0.0:8080->8080/tcp
frontend                Up                     0.0.0.0:3000->3000/tcp
airflow-webserver       Up                     0.0.0.0:8888->8080/tcp
airflow-scheduler       Up                     -
```

### 4. Initialize Databases

```bash
# PostgreSQL schema
docker-compose exec postgres psql -U postgres -f /init.sql

# HBase tables
docker-compose exec hbase hbase shell
# Inside HBase shell:
# create 'job_postings_live', 'posting', 'metadata', 'enriched'
# create 'demand_index', 'metrics', 'forecast'
# create 'skill_index', 'stats'
# exit
```

### 5. Verify Services

```bash
# Hadoop HDFS
http://localhost:9870

# Spark UI
http://localhost:4040

# Kafka UI (optional)
docker-compose exec kafka kafka-console-producer --broker-list localhost:9092 --topic test

# HBase UI
http://localhost:16010

# API Server
curl http://localhost:8080/api/health

# Frontend
http://localhost:3000

# Airflow
http://localhost:8888 (admin/admin)
```

### 6. Load Sample Data

```bash
# Generate sample dataset
docker-compose exec spark-master spark-submit \
  /opt/spark/jobs/generate_sample_data.py \
  --records=100000 \
  --output=/data/raw/sample_job_postings.csv

# Load into HDFS
docker-compose exec namenode hadoop fs -put \
  /data/raw/sample_job_postings.csv \
  hdfs://namenode:9000/data/raw/

# Run initial ETL
docker-compose exec spark-master spark-submit \
  /opt/spark/jobs/etl_batch.py \
  --input hdfs://namenode:9000/data/raw/ \
  --output hdfs://namenode:9000/data/processed/
```

## Backend Development

### Build & Run API Server

```bash
cd backend/api-server

# Build
mvn clean package

# Run locally (no Docker)
mvn spring-boot:run

# Build Docker image
docker build -t job-market-api:latest .
docker run -p 8080:8080 --env-file ../../.env job-market-api:latest
```

### Develop Spark Jobs

```bash
cd backend/spark-jobs

# Add dependencies to pom.xml
# Build
mvn clean package

# Run locally
spark-submit \
  --master local[4] \
  --driver-memory 2g \
  target/spark-jobs-1.0.jar

# Or in Docker
docker-compose exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  /opt/spark/jobs/etl_batch.py \
  --input hdfs://namenode:9000/data/raw/ \
  --output hdfs://namenode:9000/data/processed/
```

### Run Airflow DAGs

```bash
# Access Airflow UI
http://localhost:8888

# Enable DAGs:
# 1. Go to DAGs page
# 2. Toggle each DAG to "on"

# Manually trigger DAG
docker-compose exec airflow-webserver \
  airflow dags trigger -e 2024-01-01 daily_etl_pipeline

# View logs
docker-compose exec airflow-webserver \
  airflow dags list-runs --dag-id daily_etl_pipeline
```

## Frontend Development

### Build & Run UI

```bash
cd frontend

# Install dependencies
npm install

# Development server (hot reload)
npm run dev
# Runs on http://localhost:3000

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests
npm test

# Lint & format
npm run lint
npm run format
```

### Connect to Backend

Frontend automatically connects to `REACT_APP_API_URL` from `.env`:

```javascript
// src/services/api.ts
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8080';

export const fetchTrends = async (region, skill) => {
  const response = await fetch(`${API_BASE}/api/trends?region=${region}&skill=${skill}`);
  return response.json();
};
```

## Database Setup

### PostgreSQL

```bash
# Access PostgreSQL
docker-compose exec postgres psql -U postgres -d job_market

# Create schema
psql -U postgres -d job_market -f backend/database/schema.sql

# Seed data
psql -U postgres -d job_market -f backend/database/seeds.sql

# View tables
\dt

# Sample query
SELECT COUNT(*) FROM job_postings_fact;
```

### HBase

```bash
# Access HBase shell
docker-compose exec hbase hbase shell

# Create tables
create 'job_postings_live', {NAME => 'posting', VERSIONS => 1}, {NAME => 'metadata'}, {NAME => 'enriched'}
create 'demand_index', {NAME => 'metrics'}, {NAME => 'forecast'}
create 'skill_index', {NAME => 'stats'}

# Disable/drop tables
disable 'job_postings_live'
drop 'job_postings_live'

# Exit
exit
```

### Hive

```bash
# Access Hive
docker-compose exec hbase hive

# Create external tables
CREATE EXTERNAL TABLE IF NOT EXISTS job_postings (
  id STRING,
  title STRING,
  company STRING,
  location STRING,
  salary DOUBLE,
  skills ARRAY<STRING>,
  posted_date STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/data/processed/job_postings_enriched/';

# Query
SELECT COUNT(*) FROM job_postings;
SELECT title, salary FROM job_postings LIMIT 10;
```

## Monitoring & Troubleshooting

### View Container Logs

```bash
# Specific service
docker-compose logs -f api-server

# All services
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100 postgres
```

### Health Checks

```bash
# Hadoop namenode
curl http://localhost:9870

# Spark master
curl http://localhost:7077

# Kafka topic list
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# PostgreSQL connection
docker-compose exec postgres psql -U postgres -c "SELECT 1"

# Redis ping
docker-compose exec redis redis-cli ping
```

### Common Issues

**1. Port Already in Use**
```bash
# Find process using port
lsof -i :8080

# Kill process
kill -9 <PID>

# Or change ports in docker-compose.yml
```

**2. Out of Disk Space**
```bash
# Check disk usage
docker system df

# Clean up Docker
docker system prune
docker volume prune
```

**3. Container Crashes on Startup**
```bash
# Increase Docker memory limits
# Docker Desktop → Preferences → Resources → Memory (8-16GB)

# Check logs
docker-compose logs <service>

# Rebuild image
docker-compose build --no-cache
```

**4. Kafka Consumer Lag**
```bash
# Check consumer groups
docker-compose exec kafka kafka-consumer-groups --list --bootstrap-server localhost:9092

# Monitor specific group
docker-compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group job-posting-consumer
```

**5. HBase Connection Refused**
```bash
# Verify HBase is running
docker-compose ps hbase

# Check HBase logs
docker-compose logs hbase | grep ERROR

# Restart HBase
docker-compose restart hbase
```

## Performance Tuning

### Spark Configuration

Edit `backend/spark-jobs/conf/spark-defaults.conf`:

```properties
spark.executor.memory          4g
spark.executor.cores           4
spark.driver.memory            2g
spark.default.parallelism      200
spark.sql.shuffle.partitions   200
spark.sql.adaptive.enabled     true
spark.rdd.compress             true
spark.shuffle.compress         true
```

### Hadoop Configuration

Edit `backend/hadoop/conf/core-site.xml`:

```xml
<property>
  <name>hadoop.tmp.dir</name>
  <value>/data/hadoop</value>
</property>
<property>
  <name>fs.replication</name>
  <value>1</value>  <!-- Set to 3 for production -->
</property>
```

### PostgreSQL Tuning

Edit `.env`:

```env
DB_POOL_SIZE=20
DB_CONNECTION_TIMEOUT=30000
```

### Redis Caching

```bash
# Monitor Redis memory
docker-compose exec redis redis-cli INFO memory

# Set max memory policy
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
docker-compose exec redis redis-cli CONFIG SET maxmemory 2gb
```

## Production Deployment

### Pre-deployment Checklist

- [ ] All tests passing (`mvn test && npm test`)
- [ ] Build succeeds without errors
- [ ] Environment variables configured for production
- [ ] Database backups configured
- [ ] SSL certificates obtained
- [ ] Load balancer configured
- [ ] Monitoring & alerting set up
- [ ] Disaster recovery plan tested

### Deploy to Kubernetes

```bash
# Build images for registry
docker build -t myregistry/job-market-api:v1.0 backend/api-server/
docker build -t myregistry/job-market-ui:v1.0 frontend/
docker push myregistry/job-market-api:v1.0
docker push myregistry/job-market-ui:v1.0

# Deploy Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmaps.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/api-server.yaml
kubectl apply -f k8s/frontend.yaml

# Verify deployment
kubectl get pods -n job-market
kubectl describe pod <pod-name> -n job-market
```

### Scaling & Load Testing

```bash
# API load test
ab -n 10000 -c 100 http://localhost:8080/api/trends

# Kafka throughput test
docker-compose exec kafka kafka-producer-perf-test \
  --topic job-postings-raw \
  --num-records 100000 \
  --record-size 500 \
  --throughput 10000 \
  --producer-props bootstrap.servers=localhost:9092

# Database performance
pgbench -c 10 -j 2 -T 60 -U postgres job_market
```

## Backup & Recovery

### Backup Strategy

```bash
# Daily PostgreSQL backup
docker-compose exec postgres pg_dump -U postgres job_market > backup_$(date +%Y%m%d).sql

# HDFS snapshot
docker-compose exec namenode hadoop dfsadmin -allowSnapshot /data
docker-compose exec namenode hadoop dfs -createSnapshot /data my_snapshot_$(date +%Y%m%d)

# HBase backup
docker-compose exec hbase hbase shell << EOF
create_table 'job_postings_live', 'posting', 'metadata'
snapshot create -t job_postings_live snap_$(date +%Y%m%d)
EOF
```

### Recovery

```bash
# Restore PostgreSQL
psql -U postgres job_market < backup_20240101.sql

# Restore HDFS from snapshot
docker-compose exec namenode hadoop dfs -cp hdfs://namenode:9000/.snapshot/my_snapshot_20240101/data /data

# Restore HBase
docker-compose exec hbase hbase shell << EOF
restore_snapshot 'snap_20240101'
EOF
```

## Next Steps

- [ ] Set up CI/CD pipeline (GitHub Actions/GitLab CI)
- [ ] Configure log aggregation (ELK stack)
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Configure alerting (PagerDuty)
- [ ] Create runbooks for common operations
- [ ] Schedule regular disaster recovery drills
