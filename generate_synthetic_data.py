import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# Create synthetic job market dataset with proper time series data
# 36 months from 2022-01 to 2024-12

np.random.seed(42)

# Define tech skills with different trend patterns
TECH_SKILLS = [
    'Python', 'Java', 'JavaScript', 'SQL', 'AWS', 'Docker', 'Kubernetes',
    'React', 'Vue.js', 'Angular', 'Node.js', 'TypeScript', 'Go', 'Rust',
    'Machine Learning', 'Data Science', 'TensorFlow', 'PyTorch',
    'DevOps', 'CI/CD', 'Git', 'Linux', 'Windows', 'Cloud', 'Azure',
    'REST API', 'GraphQL', 'Microservices', 'Kafka', 'RabbitMQ',
    'MongoDB', 'PostgreSQL'
]

# Generate dates: 36 months (2022-01 to 2024-12)
dates = pd.date_range('2022-01-01', '2024-12-31', freq='MS')

# Create data with realistic patterns
rows = []

for skill in TECH_SKILLS:
    # Each skill has a base trend + seasonal component + noise
    base = np.random.uniform(100, 500)  # Starting demand
    trend_type = np.random.choice(['growing', 'stable', 'declining'])
    
    if trend_type == 'growing':
        trend = np.linspace(0, 150, len(dates))  # Growing trend
    elif trend_type == 'declining':
        trend = np.linspace(50, -100, len(dates))  # Declining trend
    else:
        trend = np.zeros(len(dates))  # Stable
    
    # Seasonal pattern (stronger in Q3/Q4, weaker in Q1/Q2)
    seasonal = np.array([np.sin(2 * np.pi * (m-1) / 12) * 80 for m in range(1, len(dates)+1)])
    
    # Noise
    noise = np.random.normal(0, 30, len(dates))
    
    # Combine
    demand = np.maximum(base + trend + seasonal + noise, 10)  # Min 10
    
    for i, date in enumerate(dates):
        rows.append({
            'period_start': date.strftime('%Y-%m-%d'),
            'period_end': (date + timedelta(days=30)).strftime('%Y-%m-%d'),
            'skill_name': skill,
            'demand_count': int(demand[i]),
            'region': 'USA',
            'industry': 'Technology'
        })

df_jobs = pd.DataFrame(rows)

# Save
output_path = r'C:\Users\Noodl\Projects\BDA\data\synthetic_job_skills.csv'
os.makedirs(os.path.dirname(output_path), exist_ok=True)
df_jobs.to_csv(output_path, index=False)

print(f"[OK] Created synthetic job data: {len(df_jobs)} rows")
print(f"  - {len(TECH_SKILLS)} skills, 36 months (2022-2024)")
print(f"  - Date range: {df_jobs['period_start'].min()} to {df_jobs['period_start'].max()}")
print(f"  - Saved to: {output_path}")
print()
print("Sample:")
print(df_jobs.head(10))
