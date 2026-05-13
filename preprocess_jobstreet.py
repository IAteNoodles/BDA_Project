import pandas as pd
import re
from datetime import datetime

# Tech skills to extract
TECH_SKILLS = [
    'Python', 'Java', 'JavaScript', 'SQL', 'AWS', 'Docker', 'Kubernetes',
    'React', 'Vue.js', 'Angular', 'Node.js', 'TypeScript', 'Go', 'Rust',
    'Machine Learning', 'Data Science', 'TensorFlow', 'PyTorch',
    'DevOps', 'CI/CD', 'Git', 'Linux', 'Windows', 'Cloud', 'Azure',
    'REST API', 'GraphQL', 'Microservices', 'Kafka', 'RabbitMQ',
    'MongoDB', 'PostgreSQL', 'MySQL', 'Scala', 'C#', 'C++', 'PHP',
    'Ruby', 'Swift', 'Kotlin', 'Spark', 'Hadoop', 'Hive',
    'Excel', 'Tableau', 'Power BI', 'Looker',
    'Agile', 'Scrum', 'JIRA', 'Salesforce', 'SAP', 'Oracle',
]

# Create regex pattern
TECH_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(s) for s in TECH_SKILLS) + r')\b',
    re.IGNORECASE,
)

print("Loading Jobstreet dataset...")
df = pd.read_csv(r'C:\Users\Noodl\Projects\BDA\data\jobstreet\jobstreet_all_job_dataset.csv')
print(f"Loaded {len(df):,} rows")

# Parse dates
df['listingDate'] = pd.to_datetime(df['listingDate'], utc=True)
df['period_start'] = df['listingDate'].dt.to_period('M').dt.to_timestamp()

print(f"Date range: {df['period_start'].min()} to {df['period_start'].max()}")

# Extract skills from job_title and descriptions
print("\nExtracting tech skills...")
skill_mentions = []

for idx, row in df.iterrows():
    if idx % 10000 == 0:
        print(f"  Processing row {idx:,}...")
    
    text = ''
    if pd.notna(row['job_title']):
        text += str(row['job_title']) + ' '
    if pd.notna(row['descriptions']):
        text += str(row['descriptions'])
    
    # Find all skill mentions
    matches = set()
    for match in TECH_PATTERN.finditer(text):
        # Normalize skill name
        skill = match.group(1)
        # Find canonical name (case-insensitive match)
        for canonical in TECH_SKILLS:
            if skill.lower() == canonical.lower():
                matches.add(canonical)
                break
    
    for skill in matches:
        skill_mentions.append({
            'period_start': row['period_start'],
            'skill_name': skill,
        })

print(f"Found {len(skill_mentions):,} skill mentions")

# Aggregate by month and skill
df_skills = pd.DataFrame(skill_mentions)
df_skills = df_skills.groupby(['period_start', 'skill_name']).size().reset_index(name='demand_count')

print(f"Aggregated to {len(df_skills):,} (month, skill) pairs")
print(f"Unique skills: {df_skills['skill_name'].nunique()}")

# Add required columns
df_skills['period_end'] = df_skills['period_start'] + pd.offsets.MonthEnd(0)
df_skills['region'] = 'Malaysia'
df_skills['industry'] = 'General'

# Reorder columns to match synthetic data format
df_skills = df_skills[['period_start', 'period_end', 'skill_name', 'demand_count', 'region', 'industry']]

# Save
output_path = r'C:\Users\Noodl\Projects\BDA\data\jobstreet_processed.csv'
df_skills.to_csv(output_path, index=False)
print(f"\nSaved to {output_path}")
print(f"Final dataset: {len(df_skills)} rows, {df_skills['skill_name'].nunique()} skills")
print(f"Date range: {df_skills['period_start'].min()} to {df_skills['period_start'].max()}")
print(f"Sample skills: {df_skills['skill_name'].unique()[:10]}")
