#!/usr/bin/env python3
"""Generate realistic job_listings.tsv with correct schema"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

print("Loading Jobstreet skill demand...")
df_demand = pd.read_csv('data/jobstreet_processed.csv')
df_demand['period_start'] = pd.to_datetime(df_demand['period_start'])
min_date = df_demand['period_start'].min()
max_date = df_demand['period_start'].max()

np.random.seed(42)
jobs = []
job_id = 0

companies = [
    'Google', 'Microsoft', 'Amazon', 'Meta', 'Apple', 'Tesla', 'Netflix', 
    'LinkedIn', 'Uber', 'Airbnb', 'Stripe', 'Shopify', 'Slack', 'Figma',
    'Notion', 'GitLab', 'Datadog', 'Twilio', 'Grafana', 'Hashicorp'
]

titles_template = [
    'Senior {} Engineer', '{} Developer', '{} Specialist', 
    '{} Architect', 'Lead {} Expert', '{} Technical Lead'
]

# Generate jobs for each month
current_date = min_date
while current_date <= max_date:
    month_data = df_demand[df_demand['period_start'].dt.to_period('M') == current_date.to_period('M')]
    
    for _, row in month_data.iterrows():
        skill = row['skill_name']
        demand = int(row['demand_count'])
        num_jobs = max(0, min(2, int(demand / 100)))
        
        for _ in range(num_jobs):
            company = np.random.choice(companies)
            title_template = np.random.choice(titles_template)
            title = title_template.format(skill)
            
            jobs.append({
                'title': title,
                'company': company,
                'location': np.random.choice(['Remote', 'Singapore', 'Kuala Lumpur', 'Bangkok', 'Manila']),
                'salary_min': max(30000, 50000 + np.random.randint(-10000, 30000)),
                'salary_max': min(500000, 100000 + np.random.randint(-20000, 50000)),
                'salary_currency': 'USD',
                'source': 'jobstreet_processed.csv',
                'source_id': f'job_{job_id:06d}',
                'posted_date': current_date,
                'job_type': np.random.choice(['FT', 'PT', 'Contractor']),
                'experience_level': np.random.choice(['Entry', 'Mid', 'Senior']),
                'industry': row.get('industry', 'General'),
                'is_remote': True if np.random.random() > 0.3 else False,
                'skills': skill
            })
            job_id += 1
    
    current_date += timedelta(days=30)

output = pd.DataFrame(jobs).head(850)
output.to_csv('backend/database/seed/job_listings.tsv', sep='\t', index=False, header=True)
print(f"Generated {len(output)} jobs")
