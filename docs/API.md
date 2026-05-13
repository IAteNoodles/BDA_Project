# API Documentation

## Base URL

```
Development:  http://localhost:8080
Production:   https://api.job-market.com
```

## Authentication

All endpoints require JWT bearer token in header:

```
Authorization: Bearer <token>
```

### Get Token

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}

Response 200:
{
  "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600,
  "user": {
    "id": "user-123",
    "email": "user@example.com",
    "roles": ["analyst"]
  }
}
```

## Common Response Format

```json
{
  "success": true,
  "data": {},
  "error": null,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

Error response:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INVALID_REGION",
    "message": "Region 'XX' not found",
    "details": {}
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Endpoints

### Trends API

#### Get Job Demand Trends

Retrieve historical job demand data for a skill/region combination.

```http
GET /api/trends
```

**Query Parameters:**

| Param | Type | Required | Default | Example |
|-------|------|----------|---------|---------|
| skill | string | yes | - | python |
| region | string | no | global | us-ca |
| industry | string | no | - | technology |
| start_date | ISO8601 | no | -90d | 2024-01-01 |
| end_date | ISO8601 | no | today | 2024-01-15 |
| granularity | string | no | daily | daily/weekly/monthly |

**Response:**

```json
{
  "success": true,
  "data": {
    "skill": "python",
    "region": "us-ca",
    "trend": [
      {
        "date": "2024-01-01",
        "count": 4523,
        "avg_salary": 145000,
        "growth_rate": 2.5,
        "source_count": 15
      },
      {
        "date": "2024-01-02",
        "count": 4601,
        "avg_salary": 145230,
        "growth_rate": 1.7,
        "source_count": 16
      }
    ],
    "summary": {
      "total_postings": 102345,
      "avg_salary": 145230,
      "90_day_growth": 8.5,
      "trend_direction": "up"
    }
  }
}
```

**Status Codes:**
- 200: Success
- 400: Invalid parameters
- 401: Unauthorized
- 404: Skill/region not found
- 500: Server error

**Example:**

```bash
curl -H "Authorization: Bearer $TOKEN" \
  'http://localhost:8080/api/trends?skill=python&region=us-ca&start_date=2024-01-01'
```

#### Get Skill Rankings

Get top skills by job posting frequency.

```http
GET /api/trends/skills/ranking
```

**Query Parameters:**

| Param | Type | Default | Example |
|-------|------|---------|---------|
| region | string | global | us-ca |
| industry | string | - | technology |
| limit | int | 20 | 50 |
| offset | int | 0 | 100 |

**Response:**

```json
{
  "success": true,
  "data": {
    "skills": [
      {
        "rank": 1,
        "skill": "python",
        "postings_count": 102345,
        "postings_pct": 25.3,
        "avg_salary": 145230,
        "growth_30d": 5.2,
        "growth_90d": 12.8
      },
      {
        "rank": 2,
        "skill": "java",
        "postings_count": 98765,
        "postings_pct": 24.1,
        "avg_salary": 148900,
        "growth_30d": 3.1,
        "growth_90d": 8.5
      }
    ],
    "total": 500,
    "timestamp": "2024-01-15T10:00:00Z"
  }
}
```

### Forecasts API

#### Get Demand Forecast

Retrieve predicted job demand for future periods.

```http
GET /api/forecasts/{skill}
```

**Path Parameters:**

| Param | Type | Example |
|-------|------|---------|
| skill | string | python |

**Query Parameters:**

| Param | Type | Default | Example |
|-------|------|---------|---------|
| region | string | global | us-ca |
| horizon | int | 30 | 90 |
| confidence | float | 0.95 | 0.90 |

**Response:**

```json
{
  "success": true,
  "data": {
    "skill": "python",
    "region": "global",
    "forecast_horizon_days": 30,
    "confidence_level": 0.95,
    "forecast": [
      {
        "date": "2024-02-15",
        "predicted_demand": 107200,
        "lower_bound": 104500,
        "upper_bound": 109900,
        "change_pct": 4.5
      }
    ],
    "model_info": {
      "model_name": "ARIMA(1,1,1)",
      "accuracy_rmse": 0.045,
      "last_trained": "2024-01-15T02:00:00Z"
    }
  }
}
```

#### Get Multiple Skill Forecasts

Batch forecast for comparison.

```http
POST /api/forecasts/batch
Content-Type: application/json

{
  "skills": ["python", "java", "javascript"],
  "region": "us-ca",
  "horizon": 30
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "forecasts": [
      {
        "skill": "python",
        "region": "us-ca",
        "predicted_demand": 5234,
        "trend": "up",
        "confidence": 0.92
      }
    ]
  }
}
```

### Skills API

#### Get Skill Details

Detailed information about a specific skill.

```http
GET /api/skills/{skill}
```

**Path Parameters:**

| Param | Type | Example |
|-------|------|---------|
| skill | string | python |

**Query Parameters:**

| Param | Type | Example |
|-------|------|---------|
| region | string | us-ca |

**Response:**

```json
{
  "success": true,
  "data": {
    "skill": "python",
    "skill_id": "skill-python",
    "category": "programming_language",
    "demand": {
      "current": 102345,
      "30_day_avg": 98760,
      "90_day_avg": 95230,
      "trend": "up"
    },
    "salary": {
      "average": 145230,
      "median": 142000,
      "p25": 120000,
      "p75": 170000
    },
    "regions": [
      {
        "region": "us-ca",
        "postings": 25340,
        "avg_salary": 155000
      }
    ],
    "related_skills": [
      {
        "skill": "django",
        "correlation": 0.89,
        "co_occurrence": 0.72
      }
    ],
    "industries": [
      {
        "industry": "technology",
        "postings_pct": 65.2,
        "salary_premium": 1.15
      }
    ]
  }
}
```

#### Search Skills

Full-text search for skills.

```http
GET /api/skills/search
```

**Query Parameters:**

| Param | Type | Example |
|-------|------|---------|
| q | string | python |
| category | string | programming_language |
| limit | int | 10 |

**Response:**

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "skill": "python",
        "category": "programming_language",
        "matches": "90%",
        "demand": 102345
      }
    ],
    "total": 45
  }
}
```

### Locations API

#### Get Location Data

Job posting data by geographic region.

```http
GET /api/locations
```

**Query Parameters:**

| Param | Type | Example |
|-------|------|---------|
| skill | string | python |
| industry | string | technology |
| limit | int | 50 |

**Response:**

```json
{
  "success": true,
  "data": {
    "locations": [
      {
        "location_id": "us-ca",
        "region": "California",
        "country": "United States",
        "postings_count": 25340,
        "postings_pct": 24.8,
        "avg_salary": 155000,
        "growth_90d": 8.5,
        "top_industries": [
          {
            "industry": "technology",
            "count": 18000
          }
        ],
        "top_skills": [
          "python",
          "java",
          "react"
        ]
      }
    ],
    "total": 15
  }
}
```

### Companies API

#### Get Company Data

Hiring trends by company.

```http
GET /api/companies/{company}
```

**Path Parameters:**

| Param | Type | Example |
|-------|------|---------|
| company | string | google |

**Query Parameters:**

| Param | Type | Example |
|-------|------|---------|
| timeframe | string | 90d |

**Response:**

```json
{
  "success": true,
  "data": {
    "company": "Google",
    "company_id": "company-google",
    "hiring_volume": {
      "current_month": 1245,
      "3_month_avg": 1120,
      "12_month_avg": 1050,
      "trend": "up"
    },
    "top_skills": [
      {
        "skill": "python",
        "frequency": 890,
        "salary": 180000
      }
    ],
    "locations": [
      "us-ca",
      "us-wa",
      "us-ny"
    ],
    "avg_salary": 175000,
    "job_categories": [
      {
        "title": "Senior Software Engineer",
        "count": 234
      }
    ]
  }
}
```

#### Top Hiring Companies

Get companies hiring the most.

```http
GET /api/companies/ranking
```

**Query Parameters:**

| Param | Type | Default | Example |
|-------|------|---------|---------|
| skill | string | - | python |
| region | string | global | us-ca |
| limit | int | 20 | 50 |

**Response:**

```json
{
  "success": true,
  "data": {
    "companies": [
      {
        "rank": 1,
        "company": "Google",
        "postings": 1245,
        "avg_salary": 175000,
        "hiring_growth": 5.2
      }
    ],
    "total": 500
  }
}
```

### Analytics API

#### Dashboard Summary

High-level metrics for dashboard.

```http
GET /api/analytics/summary
```

**Query Parameters:**

| Param | Type | Example |
|-------|------|---------|
| timeframe | string | 30d |

**Response:**

```json
{
  "success": true,
  "data": {
    "total_postings": 406234,
    "new_postings_today": 12340,
    "postings_growth_30d": 8.5,
    "unique_skills": 523,
    "unique_companies": 4521,
    "avg_salary": 125340,
    "top_trending_skills": [
      {
        "skill": "genai",
        "growth_30d": 125.3
      }
    ],
    "most_active_regions": [
      {
        "region": "us-ca",
        "postings": 52340
      }
    ]
  }
}
```

#### Advanced Search

Complex queries with multiple filters.

```http
POST /api/analytics/search
Content-Type: application/json

{
  "filters": {
    "skills": ["python", "django"],
    "regions": ["us-ca", "us-wa"],
    "industries": ["technology"],
    "salary_min": 100000,
    "salary_max": 200000,
    "companies": ["google", "amazon"],
    "posted_after": "2024-01-01"
  },
  "aggregations": [
    "skills",
    "regions",
    "industries"
  ],
  "limit": 100,
  "offset": 0
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "posting-123",
        "title": "Senior Python Engineer",
        "company": "Google",
        "location": "us-ca",
        "salary": 180000,
        "skills": ["python", "django", "kubernetes"],
        "posted_date": "2024-01-15"
      }
    ],
    "aggregations": {
      "skills": [
        {
          "skill": "python",
          "count": 234
        }
      ],
      "regions": [
        {
          "region": "us-ca",
          "count": 156
        }
      ]
    },
    "total": 456,
    "returned": 100
  }
}
```

### Export API

#### Export Data

Export results in various formats.

```http
GET /api/export
```

**Query Parameters:**

| Param | Type | Example |
|-------|------|---------|
| format | string | csv |
| query_id | string | search-456 |

**Supported Formats:**
- csv
- json
- parquet
- excel

**Response:**

```
HTTP/1.1 200 OK
Content-Type: text/csv
Content-Disposition: attachment; filename="trends_2024-01-15.csv"

date,count,avg_salary,growth_rate
2024-01-15,4523,145000,2.5
2024-01-14,4412,144800,1.8
...
```

### Health & Status

#### API Health Check

```http
GET /api/health
```

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "checks": {
    "database": "ok",
    "cache": "ok",
    "hdfs": "ok",
    "hbase": "ok"
  }
}
```

#### Data Freshness

```http
GET /api/status/freshness
```

**Response:**

```json
{
  "success": true,
  "data": {
    "last_update": "2024-01-15T02:30:00Z",
    "update_frequency": "daily",
    "records_processed": 125340,
    "coverage": {
      "regions": 50,
      "skills": 523,
      "companies": 4521
    }
  }
}
```

## Rate Limiting

All endpoints are rate-limited:

```
- Free tier: 100 requests/hour
- Pro tier: 10,000 requests/hour
- Enterprise: Unlimited
```

Rate limit headers:

```
X-RateLimit-Limit: 10000
X-RateLimit-Remaining: 9234
X-RateLimit-Reset: 1705329600
```

## Webhooks

Subscribe to data updates:

```http
POST /api/webhooks
Content-Type: application/json

{
  "url": "https://yourapp.com/webhook",
  "events": ["daily_forecast_ready", "skill_trending", "data_update"],
  "filters": {
    "skills": ["python"],
    "regions": ["us-ca"]
  }
}
```

Webhook payload:

```json
{
  "event": "daily_forecast_ready",
  "timestamp": "2024-01-15T02:30:00Z",
  "data": {
    "skill": "python",
    "forecast": {...}
  }
}
```

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| INVALID_SKILL | 400 | Skill not found |
| INVALID_REGION | 400 | Region not found |
| INVALID_DATE_RANGE | 400 | Invalid date parameters |
| UNAUTHORIZED | 401 | Missing or invalid token |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| RATE_LIMITED | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Server error |

## Versioning

API version in URL or header:

```
GET /api/v1/trends        # URL versioning
GET /api/trends           # Current version
Accept: application/vnd.api+json; version=1  # Header versioning
```

## SDKs

Official SDKs available:

- [Python](https://github.com/yourusername/job-market-sdk-python)
- [JavaScript/TypeScript](https://github.com/yourusername/job-market-sdk-js)
- [Java](https://github.com/yourusername/job-market-sdk-java)

## Support

- API Docs: https://api.job-market.com/docs
- Status Page: https://status.job-market.com
- Email: api-support@job-market.com
