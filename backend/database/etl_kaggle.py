import re
import os
import sys
from collections import defaultdict
from datetime import date, timedelta

import pandas as pd
import numpy as np

DATA_PATH = r"C:\Users\Noodl\Projects\BDA\data\job_descriptions.csv"
SEED_DIR = r"C:\Users\Noodl\Projects\BDA\backend\database\seed"
CHUNK_SIZE = 100000
MAX_JOB_ROWS = 50000

TECH_SKILLS = [
    "Python", "Java", "JavaScript", "SQL", "AWS", "Docker", "Kubernetes",
    "React", "Angular", "TensorFlow", "PyTorch", "Machine Learning",
    "Deep Learning", "NLP", "Data Analysis", "Tableau", "Power BI",
    "Spark", "Hadoop", "Linux", "Git", "Azure", "GCP", "DevOps",
    "CI/CD", "REST API", "Agile", "Scrum", "Cloud Computing", "Cybersecurity",
]

TECH_SKILL_LOWER = {s.lower(): s for s in TECH_SKILLS}

WORK_TYPE_MAP = {
    "Full-Time": "FT",
    "Part-Time": "PT",
    "Contract": "CT",
    "Intern": "IN",
    "Temporary": "TP",
}

TECH_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(s) for s in TECH_SKILLS) + r')\b',
    re.IGNORECASE,
)

FORECAST_END = date(2027, 12, 1)
MIN_DATA_POINTS = 3


def parse_salary(salary_str):
    if pd.isna(salary_str) or not isinstance(salary_str, str):
        return None, None
    m = re.match(r'\$(\d+)K-\$(\d+)K', salary_str)
    if m:
        return int(m.group(1)) * 1000, int(m.group(2)) * 1000
    return None, None


def parse_experience_level(exp_str):
    if pd.isna(exp_str) or not isinstance(exp_str, str):
        return "MI"
    m = re.match(r'(\d+)', exp_str)
    if m:
        years = int(m.group(1))
        if years >= 5:
            return "SE"
        elif years >= 2:
            return "MI"
        else:
            return "EN"
    return "MI"


def extract_tech_from_description(desc):
    if pd.isna(desc) or not isinstance(desc, str):
        return set()
    return {TECH_SKILL_LOWER[m.group(1).lower()] for m in TECH_PATTERN.finditer(desc)}


def month_period(mkey):
    parts = mkey.split("-")
    year, month = int(parts[0]), int(parts[1])
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)
    return start.isoformat(), end.isoformat()


def forecast_skill(dates, counts, skill_name):
    if len(counts) < MIN_DATA_POINTS:
        return None
    series = pd.Series(counts, index=pd.DatetimeIndex(dates))
    series = series.sort_index()
    series = series.resample('MS').sum().fillna(0)
    last_date = series.index[-1].date()
    if last_date >= FORECAST_END:
        return None
    n_steps = 0
    d = last_date
    while d < FORECAST_END:
        n_steps += 1
        if d.month == 12:
            d = date(d.year + 1, 1, 1)
        else:
            d = date(d.year, d.month + 1, 1)
    if n_steps <= 0:
        return None
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        sp = 4 if len(series) >= 8 else None
        if sp and len(series) >= 2 * sp:
            fit = ExponentialSmoothing(
                series, trend='add', seasonal='add', seasonal_periods=sp
            ).fit(optimized=True)
        else:
            fit = ExponentialSmoothing(series, trend='add', seasonal=None).fit(optimized=True)
        fc = fit.forecast(n_steps)
        resid_std = np.std(fit.resid)
        rows = []
        for i, (dt, val) in enumerate(fc.items()):
            step = i + 1
            ci = 1.96 * resid_std * np.sqrt(step)
            rows.append(
                f"{skill_name}\t{dt.strftime('%Y-%m-%d')}\t{val:.2f}\t"
                f"{max(0, val - ci):.2f}\t{val + ci:.2f}\t"
                f"Holt-Winters\tGlobal"
            )
        return rows
    except Exception as e:
        print(f"    Forecast failed for {skill_name}: {e}")
        return None


def forecast_job_listings(monthly_counts):
    dates = [d for d, _ in monthly_counts]
    counts = [c for _, c in monthly_counts]
    if len(counts) < MIN_DATA_POINTS:
        return None
    series = pd.Series(counts, index=pd.DatetimeIndex(dates))
    series = series.sort_index()
    series = series.resample('MS').sum().fillna(0)
    last_date = series.index[-1].date()
    if last_date >= FORECAST_END:
        return None
    n_steps = 0
    d = last_date
    while d < FORECAST_END:
        n_steps += 1
        if d.month == 12:
            d = date(d.year + 1, 1, 1)
        else:
            d = date(d.year, d.month + 1, 1)
    if n_steps <= 0:
        return None
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        sp = 4 if len(series) >= 8 else None
        if sp and len(series) >= 2 * sp:
            fit = ExponentialSmoothing(
                series, trend='add', seasonal='add', seasonal_periods=sp
            ).fit(optimized=True)
        else:
            fit = ExponentialSmoothing(series, trend='add', seasonal=None).fit(optimized=True)
        fc = fit.forecast(n_steps)
        resid_std = np.std(fit.resid)
        rows = []
        for i, (dt, val) in enumerate(fc.items()):
            step = i + 1
            ci = 1.96 * resid_std * np.sqrt(step)
            rows.append(
                f"(job_listings_total)\t{dt.strftime('%Y-%m-%d')}\t{val:.2f}\t"
                f"{max(0, val - ci):.2f}\t{val + ci:.2f}\tHolt-Winters\tGlobal"
            )
        return rows
    except Exception as e:
        print(f"    Forecast failed for job_listings: {e}")
        return None


def main():
    os.makedirs(SEED_DIR, exist_ok=True)

    skill_counts = defaultdict(lambda: defaultdict(int))
    monthly_job_counts = defaultdict(int)
    sample_frames = []
    total_read = 0

    usecols = [
        "Job Id", "Job Title", "Role", "Company", "location", "Country",
        "Salary Range", "Work Type", "Job Posting Date", "skills",
        "Job Description", "Experience",
    ]

    print("Starting ETL processing...")
    reader = pd.read_csv(DATA_PATH, chunksize=CHUNK_SIZE, dtype=str, usecols=usecols)

    for chunk_idx, chunk in enumerate(reader):
        total_read += len(chunk)
        print(f"  Chunk {chunk_idx}: read {len(chunk)} rows (total {total_read})")

        chunk["_mkey"] = chunk["Job Posting Date"].str[:7]
        chunk = chunk[chunk["_mkey"].notna()]

        chunk["tech_skills"] = chunk["Job Description"].apply(extract_tech_from_description)

        for _, row in chunk.iterrows():
            mkey = row["_mkey"]
            for skill_name in row["tech_skills"]:
                skill_counts[skill_name][mkey] += 1
            monthly_job_counts[mkey] += 1

        sampled_n = min(2000, len(chunk))
        sample_frames.append(chunk.sample(n=sampled_n, random_state=42))

    print(f"Finished reading {total_read} rows")
    print(f"Found {len(skill_counts)} tech skills across {len(monthly_job_counts)} months")

    # --- Write skill_demand.tsv ---
    skill_demand_path = os.path.join(SEED_DIR, "skill_demand.tsv")
    with open(skill_demand_path, "w", encoding="utf-8") as f:
        sorted_skills = sorted(skill_counts.keys())
        for skill_name in sorted_skills:
            months = skill_counts[skill_name]
            for mkey in sorted(months.keys()):
                count = months[mkey]
                period_start, period_end = month_period(mkey)
                f.write(f"{skill_name}\t{count}\t{period_start}\t{period_end}\tGlobal\tGeneral\n")
    print(f"Wrote skill_demand.tsv ({len(skill_counts)} skills)")

    # --- Write job_listings.tsv ---
    job_listings_path = os.path.join(SEED_DIR, "job_listings.tsv")
    combined = pd.concat(sample_frames, ignore_index=True)

    all_mkeys = sorted(combined["_mkey"].unique())
    if not all_mkeys:
        print("No data found, exiting.")
        sys.exit(1)

    rows_per_month = MAX_JOB_ROWS // len(all_mkeys)
    remaining = MAX_JOB_ROWS - rows_per_month * len(all_mkeys)

    sampled_dfs = []
    for i, mkey in enumerate(all_mkeys):
        month_df = combined[combined["_mkey"] == mkey]
        take = rows_per_month + (1 if i < remaining else 0)
        if len(month_df) <= take:
            sampled_dfs.append(month_df)
        else:
            sampled_dfs.append(month_df.sample(n=take, random_state=42))

    sampled = pd.concat(sampled_dfs, ignore_index=True)
    print(f"Sampled {len(sampled)} job listings across {len(all_mkeys)} months")

    with open(job_listings_path, "w", encoding="utf-8") as f:
        for _, row in sampled.iterrows():
            job_id = str(row.get("Job Id", ""))
            title = str(row.get("Job Title", "")) if not pd.isna(row.get("Job Title")) else ""
            company = str(row.get("Company", "")) if not pd.isna(row.get("Company")) else ""
            location = str(row.get("location", "")) if not pd.isna(row.get("location")) else ""
            salary_str = row.get("Salary Range", "")
            salary_min, salary_max = parse_salary(salary_str)
            salary_min_str = str(salary_min) if salary_min is not None else ""
            salary_max_str = str(salary_max) if salary_max is not None else ""
            posted_date = str(row.get("Job Posting Date", "")) if not pd.isna(row.get("Job Posting Date")) else ""
            work_type = str(row.get("Work Type", "")) if not pd.isna(row.get("Work Type")) else ""
            job_type = WORK_TYPE_MAP.get(work_type, "")
            exp_level = parse_experience_level(row.get("Experience", ""))
            is_remote = "t" if "Remote" in location else "f"

            tech_skills = extract_tech_from_description(row.get("Job Description", ""))
            skills_str = ",".join(sorted(tech_skills))

            f.write(
                f"{title}\t{company}\t{location}\t{salary_min_str}\t{salary_max_str}"
                f"\tUSD\tkaggle-jobs\t{job_id}\t{posted_date}\t{job_type}"
                f"\t{exp_level}\tGeneral\t{is_remote}\t{skills_str}\n"
            )
    print(f"Wrote job_listings.tsv ({len(sampled)} rows)")

    # --- Pre-compute forecasts ---
    print("\nPre-computing forecasts...")
    forecast_rows = []

    # Skill demand forecasts
    for skill_name in sorted(skill_counts.keys()):
        months = skill_counts[skill_name]
        dates = []
        counts = []
        for mkey in sorted(months.keys()):
            parts = mkey.split("-")
            dates.append(f"{parts[0]}-{parts[1]}-01")
            counts.append(months[mkey])
        result = forecast_skill(dates, counts, skill_name)
        if result:
            forecast_rows.extend(result)

    # Job listings total forecast
    monthly_sorted = sorted(monthly_job_counts.items())
    jl_dates = [f"{mkey.split('-')[0]}-{mkey.split('-')[1]}-01" for mkey, _ in monthly_sorted]
    jl_counts = [c for _, c in monthly_sorted]
    jl_result = forecast_job_listings(list(zip(
        [f"{mkey.split('-')[0]}-{mkey.split('-')[1]}-01" for mkey, _ in monthly_sorted],
        [c for _, c in monthly_sorted]
    )))
    if jl_result:
        forecast_rows.extend(jl_result)

    forecast_path = os.path.join(SEED_DIR, "forecast_results.tsv")
    with open(forecast_path, "w", encoding="utf-8") as f:
        for row in forecast_rows:
            f.write(row + "\n")
    print(f"Wrote forecast_results.tsv ({len(forecast_rows)} forecast points)")

    print("ETL complete.")


if __name__ == "__main__":
    main()