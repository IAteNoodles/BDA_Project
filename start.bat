@echo off
setlocal enabledelayedexpansion

:: BDA Job Market Demand Forecasting System - Startup Script
:: ============================================================

echo.
echo ============================================
echo  BDA Job Market Demand Forecasting System
echo ============================================
echo.

docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running or not installed.
    echo         Please start Docker Desktop and try again.
    exit /b 1
)
echo [OK] Docker is running

cd /d "%~dp0"

if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul 2>&1
        echo [WARN] .env not found - copied from .env.example
        echo        Review .env and update values before proceeding.
    ) else (
        echo [WARN] No .env or .env.example found. Services may fail.
    )
) else (
    echo [OK] .env file found
)

set MISSING_BUILT=0
set MISSING_PULLED=0

echo.
echo [CHECK] Verifying images...

docker image inspect iatenoodles/bda-api-server:latest >nul 2>&1
if errorlevel 1 (
    echo [MISSING] iatenoodles/bda-api-server:latest
    set MISSING_BUILT=1
) else (
    echo [OK] iatenoodles/bda-api-server:latest
)

docker image inspect iatenoodles/bda-frontend:latest >nul 2>&1
if errorlevel 1 (
    echo [MISSING] iatenoodles/bda-frontend:latest
    set MISSING_BUILT=1
) else (
    echo [OK] iatenoodles/bda-frontend:latest
)

docker image inspect iatenoodles/bda-kafka-consumer:latest >nul 2>&1
if errorlevel 1 (
    echo [MISSING] iatenoodles/bda-kafka-consumer:latest
    set MISSING_BUILT=1
) else (
    echo [OK] iatenoodles/bda-kafka-consumer:latest
)

docker image inspect iatenoodles/bda-spark-jobs:latest >nul 2>&1
if errorlevel 1 (
    echo [MISSING] iatenoodles/bda-spark-jobs:latest
    set MISSING_BUILT=1
) else (
    echo [OK] iatenoodles/bda-spark-jobs:latest
)

docker image inspect bda-postgres:latest >nul 2>&1
if errorlevel 1 (
    echo [MISSING] bda-postgres (local build)
    set MISSING_BUILT=1
) else (
    echo [OK] bda-postgres (local build)
)

docker image inspect bda-ml-service:latest >nul 2>&1
if errorlevel 1 (
    echo [MISSING] bda-ml-service (local build)
    set MISSING_BUILT=1
) else (
    echo [OK] bda-ml-service (local build)
)

docker image inspect bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8 >nul 2>&1
if errorlevel 1 (
    echo [MISSING] bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8
    set MISSING_PULLED=1
) else (
    echo [OK] bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8
)

docker image inspect bde2020/hadoop-datanode:2.0.0-hadoop3.2.1-java8 >nul 2>&1
if errorlevel 1 (
    echo [MISSING] bde2020/hadoop-datanode:2.0.0-hadoop3.2.1-java8
    set MISSING_PULLED=1
) else (
    echo [OK] bde2020/hadoop-datanode:2.0.0-hadoop3.2.1-java8
)

docker image inspect bde2020/spark-master:3.0.0-hadoop3.2 >nul 2>&1
if errorlevel 1 (
    echo [MISSING] bde2020/spark-master:3.0.0-hadoop3.2
    set MISSING_PULLED=1
) else (
    echo [OK] bde2020/spark-master:3.0.0-hadoop3.2
)

docker image inspect bde2020/spark-worker:3.0.0-hadoop3.2 >nul 2>&1
if errorlevel 1 (
    echo [MISSING] bde2020/spark-worker:3.0.0-hadoop3.2
    set MISSING_PULLED=1
) else (
    echo [OK] bde2020/spark-worker:3.0.0-hadoop3.2
)

docker image inspect bde2020/hbase-master:1.0.0-hbase1.2.6 >nul 2>&1
if errorlevel 1 (
    echo [MISSING] bde2020/hbase-master:1.0.0-hbase1.2.6
    set MISSING_PULLED=1
) else (
    echo [OK] bde2020/hbase-master:1.0.0-hbase1.2.6
)

docker image inspect confluentinc/cp-zookeeper:7.0.1 >nul 2>&1
if errorlevel 1 (
    echo [MISSING] confluentinc/cp-zookeeper:7.0.1
    set MISSING_PULLED=1
) else (
    echo [OK] confluentinc/cp-zookeeper:7.0.1
)

docker image inspect confluentinc/cp-kafka:7.0.1 >nul 2>&1
if errorlevel 1 (
    echo [MISSING] confluentinc/cp-kafka:7.0.1
    set MISSING_PULLED=1
) else (
    echo [OK] confluentinc/cp-kafka:7.0.1
)

docker image inspect redis:7-alpine >nul 2>&1
if errorlevel 1 (
    echo [MISSING] redis:7-alpine
    set MISSING_PULLED=1
) else (
    echo [OK] redis:7-alpine
)

docker image inspect apache/airflow:2.5.0-python3.9 >nul 2>&1
if errorlevel 1 (
    echo [MISSING] apache/airflow:2.5.0-python3.9
    set MISSING_PULLED=1
) else (
    echo [OK] apache/airflow:2.5.0-python3.9
)

if "!MISSING_PULLED!"=="1" (
    echo.
    echo [PULL] Pulling missing external images...
    docker compose pull
    if errorlevel 1 (
        echo [ERROR] docker compose pull failed.
        exit /b 1
    )
    echo [OK] Pull complete
)

if "!MISSING_BUILT!"=="1" (
    echo.
    echo [BUILD] Building missing local images...
    docker compose build
    if errorlevel 1 (
        echo [ERROR] docker compose build failed.
        exit /b 1
    )
    echo [OK] Build complete
)

echo.
echo [START] Starting all services...
docker compose up -d
if errorlevel 1 (
    echo [ERROR] docker compose up failed.
    exit /b 1
)
echo [OK] Services started

echo.
echo [WAIT] Waiting for services to become healthy...
echo.

set PG_READY=0
set PG_ELAPSED=0
:wait_postgres
if !PG_ELAPSED! geq 60 (
    echo [ERROR] postgres did not become ready within 60s
    goto :done_postgres
)
docker exec postgres pg_isready -U postgres >nul 2>&1
if not errorlevel 1 (
    echo [OK] postgres is ready
    set PG_READY=1
    goto :done_postgres
)
set /a PG_ELAPSED+=2
echo [WAIT] postgres - waiting... (!PG_ELAPSED!s)
timeout /t 2 /nobreak >nul
goto :wait_postgres
:done_postgres

set ML_READY=0
set ML_ELAPSED=0
:wait_ml
if !ML_ELAPSED! geq 60 (
    echo [ERROR] ml-service did not become ready within 60s
    goto :done_ml
)
curl -s http://localhost:5100/ml/health >nul 2>&1
if not errorlevel 1 (
    echo [OK] ml-service is ready
    set ML_READY=1
    goto :done_ml
)
set /a ML_ELAPSED+=2
echo [WAIT] ml-service - waiting... (!ML_ELAPSED!s)
timeout /t 2 /nobreak >nul
goto :wait_ml
:done_ml

set API_READY=0
set API_ELAPSED=0
:wait_api
if !API_ELAPSED! geq 90 (
    echo [ERROR] api-server did not become ready within 90s
    goto :done_api
)
curl -s http://localhost:18080/actuator/health >nul 2>&1
if not errorlevel 1 (
    echo [OK] api-server is ready
    set API_READY=1
    goto :done_api
)
set /a API_ELAPSED+=2
echo [WAIT] api-server - waiting... (!API_ELAPSED!s)
timeout /t 2 /nobreak >nul
goto :wait_api
:done_api

set FE_READY=0
set FE_ELAPSED=0
:wait_frontend
if !FE_ELAPSED! geq 60 (
    echo [ERROR] frontend did not become ready within 60s
    goto :done_frontend
)
curl -s http://localhost:5173 >nul 2>&1
if not errorlevel 1 (
    echo [OK] frontend is ready
    set FE_READY=1
    goto :done_frontend
)
set /a FE_ELAPSED+=2
echo [WAIT] frontend - waiting... (!FE_ELAPSED!s)
timeout /t 2 /nobreak >nul
goto :wait_frontend
:done_frontend

echo.
set FAILED=0
for /f "tokens=*" %%a in ('docker compose ps -a --format "{{.Name}}\t{{.Status}}" 2^>nul') do (
    echo %%a | findstr /i "exited error" >nul 2>&1
    if not errorlevel 1 (
        echo [ERROR] %%a
        set FAILED=1
    )
)

echo.
echo ============================================
echo  Access URLs
echo ============================================
echo.
echo   Frontend:          http://localhost:5173
echo   API Server:        http://localhost:18080
echo   ML Service:        http://localhost:5100
echo   PostgreSQL:        localhost:5432
echo   Redis:             localhost:16379
echo   Hadoop NameNode:   http://localhost:9870
echo   Hadoop DataNode:   http://localhost:9864
echo   Spark Master UI:   http://localhost:8080
echo   Spark Worker UI:   http://localhost:18081
echo   HBase UI:          http://localhost:16010
echo   Airflow UI:        http://localhost:8888  (admin/admin)
echo   Kafka:             localhost:9092
echo   Zookeeper:         localhost:2181
echo.
echo ============================================
echo.

if "!FAILED!"=="1" (
    echo [ERROR] Some services failed to start. Check logs with:
    echo         docker compose logs
    echo.
)

echo View live logs:  docker compose logs -f
echo Stop services:    docker compose down
echo.