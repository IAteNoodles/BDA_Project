import pandas as pd

df = pd.read_csv(r'C:\Users\Noodl\Projects\BDA\data\jobstreet\jobstreet_all_job_dataset.csv', nrows=3)
print('Total columns:', len(df.columns))
print('Columns:', list(df.columns))
print()
print('Date columns:', [c for c in df.columns if any(x in c.lower() for x in ['date', 'time', 'period'])])
print()
print('Sample row 0:')
for col in df.columns[:15]:
    val = str(df[col].iloc[0])[:80]
    print(f'  {col}: {val}')
