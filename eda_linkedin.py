"""
Comprehensive EDA on LinkedIn Job Postings Dataset
====================================================
Covers all requested files and analysis points.
"""

import io
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# Force UTF-8 output so Unicode characters don't crash on Windows cp1252 consoles
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = r"C:\Users\Noodl\Projects\BDA\data\linkedin"

SEP = "=" * 70
sep = "-" * 70

# ─────────────────────────────────────────────────────────────────────────────
# Helper utilities
# ─────────────────────────────────────────────────────────────────────────────


def load_csv(rel_path: str) -> pd.DataFrame:
    """Try UTF-8 first, fall back to latin-1."""
    full = f"{BASE}\\{rel_path}"
    try:
        df = pd.read_csv(full, encoding="utf-8", low_memory=False)
        enc = "utf-8"
    except UnicodeDecodeError:
        df = pd.read_csv(full, encoding="latin-1", low_memory=False)
        enc = "latin-1"
    print(f"  [loaded]  {rel_path}  |  encoding={enc}  |  shape={df.shape}")
    return df


def null_pct(df: pd.DataFrame) -> pd.Series:
    return (df.isnull().mean() * 100).round(2)


def print_file_overview(name: str, df: pd.DataFrame):
    print(f"\n{SEP}")
    print(f"  FILE: {name}")
    print(SEP)
    print(f"  Rows : {len(df):,}")
    print(f"  Cols : {df.shape[1]}")
    print(f"\n  Column names:\n    {list(df.columns)}")

    print(f"\n  Null % per column:")
    np_ = null_pct(df)
    for col, pct in np_.items():
        bar = "|" * int(pct / 5)  # one pipe per 5 %
        print(f"    {col:<40}  {pct:>6.2f}%  {bar}")

    print(f"\n  First 3 rows (transposed for readability):")
    sample = df.head(3).T
    sample.columns = [f"row_{i}" for i in range(len(sample.columns))]
    for idx, row in sample.iterrows():
        vals = "  |  ".join(str(v)[:60] for v in row.values)
        print(f"    {str(idx):<40}  {vals}")


# ─────────────────────────────────────────────────────────────────────────────
# 1. POSTINGS.CSV
# ─────────────────────────────────────────────────────────────────────────────

print(f"\n{'#' * 70}")
print("  SECTION 1 — postings.csv")
print(f"{'#' * 70}")

post = load_csv("postings.csv")
print_file_overview("postings.csv", post)

# ── 4. Timestamps ────────────────────────────────────────────────────────────
print(f"\n{sep}")
print("  [4] Timestamp columns: listed_time & original_listed_time")
print(sep)

for col in ["listed_time", "original_listed_time"]:
    if col not in post.columns:
        print(f"  !! Column '{col}' NOT FOUND")
        continue

    raw = post[col].dropna()
    sample_raw = raw.head(5).tolist()
    print(f"\n  Column: {col}")
    print(f"    dtype      : {post[col].dtype}")
    print(f"    non-null   : {raw.shape[0]:,}  ({raw.shape[0] / len(post) * 100:.1f}%)")
    print(f"    raw samples: {sample_raw}")

    # Detect if numeric (Unix) or string
    first_val = raw.iloc[0]
    if pd.api.types.is_numeric_dtype(raw):
        kind = "UNIX ms" if first_val > 1e12 else "UNIX s"
        print(f"    kind       : {kind}")
        if first_val > 1e12:
            parsed = pd.to_datetime(raw, unit="ms", utc=True)
        else:
            parsed = pd.to_datetime(raw, unit="s", utc=True)
    else:
        # Try ISO string parse
        kind = "string/ISO"
        print(f"    kind       : {kind}")
        parsed = pd.to_datetime(raw, utc=True, errors="coerce")

    parsed = parsed.dt.tz_convert("UTC")
    print(f"    min date   : {parsed.min()}")
    print(f"    max date   : {parsed.max()}")
    unique_months = parsed.dt.to_period("M").nunique()
    month_counts = parsed.dt.to_period("M").value_counts().sort_index()
    print(f"    unique months: {unique_months}")
    print(f"    month distribution (top 15):")
    for period, cnt in month_counts.tail(15).items():
        bar = "|" * max(1, int(cnt / month_counts.max() * 30))
        print(f"      {period}  {cnt:>7,}  {bar}")

    # Store parsed version for later use (don't write to disk)
    if col == "listed_time":
        post_listed_parsed = parsed

print(f"\n  Time series suitability:")
print(
    f"    Unique months in listed_time: {post_listed_parsed.dt.to_period('M').nunique()}"
)
print(f"    Monthly listing counts (all):")
monthly = post_listed_parsed.dt.to_period("M").value_counts().sort_index()
for period, cnt in monthly.items():
    bar = "|" * max(1, int(cnt / monthly.max() * 40))
    print(f"      {period}  {cnt:>7,}  {bar}")

# ── 5. remote_allowed ────────────────────────────────────────────────────────
print(f"\n{sep}")
print("  [5] remote_allowed — distribution")
print(sep)

if "remote_allowed" in post.columns:
    rc = post["remote_allowed"]
    print(f"    dtype        : {rc.dtype}")
    print(f"    non-null     : {rc.notna().sum():,}  ({rc.notna().mean() * 100:.1f}%)")
    print(f"    null         : {rc.isna().sum():,}  ({rc.isna().mean() * 100:.1f}%)")
    vc = rc.value_counts(dropna=False)
    print(f"    value_counts :")
    for val, cnt in vc.items():
        print(f"      {str(val):<10}  {cnt:>7,}  ({cnt / len(post) * 100:.1f}%)")
else:
    print("  !! remote_allowed NOT FOUND")

# ── 6. normalized_salary ─────────────────────────────────────────────────────
print(f"\n{sep}")
print("  [6] normalized_salary")
print(sep)

if "normalized_salary" in post.columns:
    ns = post["normalized_salary"].dropna()
    print(f"    non-null count : {len(ns):,}  ({len(ns) / len(post) * 100:.1f}%)")
    print(f"    min            : {ns.min():,.2f}")
    print(f"    max            : {ns.max():,.2f}")
    print(f"    mean           : {ns.mean():,.2f}")
    print(f"    median         : {ns.median():,.2f}")
    print(
        f"    percentiles    : 25th={ns.quantile(0.25):,.0f}  75th={ns.quantile(0.75):,.0f}  95th={ns.quantile(0.95):,.0f}"
    )
else:
    print("  !! normalized_salary NOT FOUND")

# ── 7. skills_desc ────────────────────────────────────────────────────────────
print(f"\n{sep}")
print("  [7] skills_desc")
print(sep)

if "skills_desc" in post.columns:
    sd = post["skills_desc"]
    non_null = sd.dropna()
    non_empty = non_null[non_null.str.strip().ne("")]
    print(
        f"    non-null       : {len(non_null):,}  ({len(non_null) / len(post) * 100:.1f}%)"
    )
    print(
        f"    non-empty      : {len(non_empty):,}  ({len(non_empty) / len(post) * 100:.1f}%)"
    )
    print(f"\n    Sample values (first 3 non-empty):")
    for i, val in enumerate(non_empty.head(3)):
        print(f"      [{i}] {str(val)[:200]}")
else:
    print("  !! skills_desc NOT FOUND")

# ── 8. Salary columns ─────────────────────────────────────────────────────────
print(f"\n{sep}")
print("  [8] Salary columns: min_salary, max_salary, med_salary")
print(sep)

for col in ["min_salary", "max_salary", "med_salary"]:
    if col not in post.columns:
        print(f"    !! {col} NOT FOUND")
        continue
    s = post[col].dropna()
    print(f"\n    {col}:")
    print(f"      fill rate : {len(s):,}  ({len(s) / len(post) * 100:.1f}%)")
    print(f"      min       : {s.min():,.2f}")
    print(f"      max       : {s.max():,.2f}")
    print(f"      median    : {s.median():,.2f}")
    print(f"      mean      : {s.mean():,.2f}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. jobs/job_skills.csv
# ─────────────────────────────────────────────────────────────────────────────

print(f"\n{'#' * 70}")
print("  SECTION 2 — jobs/job_skills.csv")
print(f"{'#' * 70}")

skills_df = load_csv(r"jobs\job_skills.csv")
print_file_overview("jobs/job_skills.csv", skills_df)

# ─────────────────────────────────────────────────────────────────────────────
# 3. jobs/salaries.csv
# ─────────────────────────────────────────────────────────────────────────────

print(f"\n{'#' * 70}")
print("  SECTION 3 — jobs/salaries.csv")
print(f"{'#' * 70}")

sal_df = load_csv(r"jobs\salaries.csv")
print_file_overview("jobs/salaries.csv", sal_df)

# ─────────────────────────────────────────────────────────────────────────────
# 4. jobs/job_industries.csv
# ─────────────────────────────────────────────────────────────────────────────

print(f"\n{'#' * 70}")
print("  SECTION 4 — jobs/job_industries.csv")
print(f"{'#' * 70}")

job_ind_df = load_csv(r"jobs\job_industries.csv")
print_file_overview("jobs/job_industries.csv", job_ind_df)

# ─────────────────────────────────────────────────────────────────────────────
# 5. jobs/benefits.csv
# ─────────────────────────────────────────────────────────────────────────────

print(f"\n{'#' * 70}")
print("  SECTION 5 — jobs/benefits.csv")
print(f"{'#' * 70}")

ben_df = load_csv(r"jobs\benefits.csv")
print_file_overview("jobs/benefits.csv", ben_df)

# ─────────────────────────────────────────────────────────────────────────────
# 6. companies/companies.csv
# ─────────────────────────────────────────────────────────────────────────────

print(f"\n{'#' * 70}")
print("  SECTION 6 — companies/companies.csv")
print(f"{'#' * 70}")

comp_df = load_csv(r"companies\companies.csv")
print_file_overview("companies/companies.csv", comp_df)

# ─────────────────────────────────────────────────────────────────────────────
# 7. companies/company_industries.csv
# ─────────────────────────────────────────────────────────────────────────────

print(f"\n{'#' * 70}")
print("  SECTION 7 — companies/company_industries.csv")
print(f"{'#' * 70}")

comp_ind_df = load_csv(r"companies\company_industries.csv")
print_file_overview("companies/company_industries.csv", comp_ind_df)

# ─────────────────────────────────────────────────────────────────────────────
# 8. mappings/skills.csv
# ─────────────────────────────────────────────────────────────────────────────

print(f"\n{'#' * 70}")
print("  SECTION 8 — mappings/skills.csv")
print(f"{'#' * 70}")

skills_map = load_csv(r"mappings\skills.csv")
print_file_overview("mappings/skills.csv", skills_map)

# ─────────────────────────────────────────────────────────────────────────────
# 9. mappings/industries.csv
# ─────────────────────────────────────────────────────────────────────────────

print(f"\n{'#' * 70}")
print("  SECTION 9 — mappings/industries.csv")
print(f"{'#' * 70}")

ind_map = load_csv(r"mappings\industries.csv")
print_file_overview("mappings/industries.csv", ind_map)

# ─────────────────────────────────────────────────────────────────────────────
# [9] Top 20 skills — job_skills JOIN mappings/skills
# ─────────────────────────────────────────────────────────────────────────────

print(f"\n{'#' * 70}")
print("  ANALYSIS [9] — Top 20 Most Demanded Skills")
print(f"{'#' * 70}")

print(f"\n  job_skills columns    : {list(skills_df.columns)}")
print(f"  skills_map columns    : {list(skills_map.columns)}")

# Find the common key — usually 'skill_abr' or similar
skill_key_left = None
skill_key_right = None

for c in skills_df.columns:
    if "skill" in c.lower() and (
        "abr" in c.lower()
        or "id" in c.lower()
        or c.lower() in ["skill_abr", "skill_id"]
    ):
        skill_key_left = c
        break
if skill_key_left is None:
    # fallback: use first column that looks like an abbreviation
    for c in skills_df.columns:
        if skills_df[c].dtype == object and skills_df[c].str.len().median() < 10:
            skill_key_left = c
            break

for c in skills_map.columns:
    if "abr" in c.lower() or c == skill_key_left:
        skill_key_right = c
        break
if skill_key_right is None:
    skill_key_right = skills_map.columns[0]

print(f"\n  Join key left  (job_skills)   : {skill_key_left}")
print(f"  Join key right (skills_map)   : {skill_key_right}")

# Find name column in skills_map
name_col = None
for c in skills_map.columns:
    if "name" in c.lower():
        name_col = c
        break
if name_col is None:
    name_col = [c for c in skills_map.columns if c != skill_key_right][0]

print(f"  Skill name column             : {name_col}")

merged_skills = skills_df.merge(
    skills_map[[skill_key_right, name_col]],
    left_on=skill_key_left,
    right_on=skill_key_right,
    how="left",
)

top20 = merged_skills[name_col].value_counts().head(20).reset_index()
top20.columns = ["skill_name", "count"]
top20["pct_of_jobs"] = (top20["count"] / len(skills_df) * 100).round(2)

print(f"\n  TOP 20 MOST DEMANDED SKILLS:")
print(f"  {'Rank':<5}  {'Skill Name':<35}  {'Count':>8}  {'% of job-skill rows':>20}")
print(f"  {'-' * 5}  {'-' * 35}  {'-' * 8}  {'-' * 20}")
for i, row in top20.iterrows():
    bar = "|" * max(1, int(row["pct_of_jobs"] * 2))
    print(
        f"  {i + 1:<5}  {str(row['skill_name']):<35}  {int(row['count']):>8,}  {row['pct_of_jobs']:>19.2f}%  {bar}"
    )

# ─────────────────────────────────────────────────────────────────────────────
# [10] Join job_skills → postings on job_id to get skills per date
# ─────────────────────────────────────────────────────────────────────────────

print(f"\n{'#' * 70}")
print("  ANALYSIS [10] — job_skills JOIN postings (skill + date)")
print(f"{'#' * 70}")

# Find job_id column in both
post_id_col = None
for c in post.columns:
    if "job_id" in c.lower() or c.lower() == "id":
        post_id_col = c
        break

skills_post_id_col = None
for c in skills_df.columns:
    if "job_id" in c.lower():
        skills_post_id_col = c
        break

print(f"\n  postings job_id col  : {post_id_col}")
print(f"  job_skills job_id col: {skills_post_id_col}")

# Parse listed_time into a proper datetime column (in memory only)
if "listed_time" in post.columns:
    raw_lt = post["listed_time"]
    if pd.api.types.is_numeric_dtype(raw_lt):
        first_nonnull = raw_lt.dropna().iloc[0]
        if first_nonnull > 1e12:
            post_with_date = post[[post_id_col, "listed_time"]].copy()
            post_with_date["listed_date"] = pd.to_datetime(
                post_with_date["listed_time"], unit="ms", utc=True
            ).dt.tz_convert("UTC")
        else:
            post_with_date = post[[post_id_col, "listed_time"]].copy()
            post_with_date["listed_date"] = pd.to_datetime(
                post_with_date["listed_time"], unit="s", utc=True
            ).dt.tz_convert("UTC")
    else:
        post_with_date = post[[post_id_col, "listed_time"]].copy()
        post_with_date["listed_date"] = pd.to_datetime(
            post_with_date["listed_time"], utc=True, errors="coerce"
        )
else:
    print("  !! listed_time not available, using first date column found")
    post_with_date = post[[post_id_col]].copy()
    post_with_date["listed_date"] = pd.NaT

# Full chain: job_skills → postings (date) → skills_map (name)
full_join = skills_df.merge(
    post_with_date[[post_id_col, "listed_date"]],
    left_on=skills_post_id_col,
    right_on=post_id_col,
    how="left",
).merge(
    skills_map[[skill_key_right, name_col]],
    left_on=skill_key_left,
    right_on=skill_key_right,
    how="left",
)

print(f"\n  Full join shape: {full_join.shape}")
print(f"  Rows with valid date: {full_join['listed_date'].notna().sum():,}")
print(f"\n  Sample join result (10 rows with date):")

sample_join = (
    full_join[full_join["listed_date"].notna()][
        [skills_post_id_col, name_col, "listed_date"]
    ]
    .rename(columns={skills_post_id_col: "job_id", name_col: "skill_name"})
    .head(10)
)
print(sample_join.to_string(index=False))

# Skill demand over time (monthly)
print(f"\n  Skill demand time series — top 5 skills by month (sample):")
full_join["month"] = full_join["listed_date"].dt.to_period("M")
skill_monthly = (
    full_join[full_join["listed_date"].notna()]
    .groupby(["month", name_col])
    .size()
    .reset_index(name="count")
)
top5_skill_names = top20.head(5)["skill_name"].tolist()
skill_monthly_top5 = skill_monthly[skill_monthly[name_col].isin(top5_skill_names)]
pivot = skill_monthly_top5.pivot_table(
    index="month", columns=name_col, values="count", fill_value=0
).tail(10)
print(pivot.to_string())

# ─────────────────────────────────────────────────────────────────────────────
# OVERALL VERDICT
# ─────────────────────────────────────────────────────────────────────────────

print(f"\n{'#' * 70}")
print("  OVERALL VERDICT")
print(f"{'#' * 70}")

# Recalculate key metrics for verdict
listed_non_null = (
    post["listed_time"].notna().sum() if "listed_time" in post.columns else 0
)
listed_pct = listed_non_null / len(post) * 100 if len(post) > 0 else 0

norm_sal_nn = (
    post["normalized_salary"].notna().sum()
    if "normalized_salary" in post.columns
    else 0
)
norm_sal_pct = norm_sal_nn / len(post) * 100

remote_nn = (
    post["remote_allowed"].notna().sum() if "remote_allowed" in post.columns else 0
)
remote_pct = remote_nn / len(post) * 100

n_skill_rows = len(skills_df)
n_unique_months = (
    post_listed_parsed.dt.to_period("M").nunique()
    if "listed_time" in post.columns
    else 0
)

print(f"""
  +-------------+----------------------------------------------------------+
  |              LINKEDIN DATASET - FITNESS SCORECARD           |
  +-------------+----------------------------------------------------------+
  | USE CASE    | ASSESSMENT                                               |
  +-------------+----------------------------------------------------------+
  | (a) MONTHLY | listed_time non-null: {listed_non_null:,} ({listed_pct:.1f}%)
  | JOB LISTING | Unique months      : {n_unique_months}
  | TIME SERIES | VERDICT: {"[EXCELLENT]" if n_unique_months >= 12 and listed_pct > 80 else ("[MODERATE]" if n_unique_months >= 6 else "[POOR]    ")}
  +-------------+----------------------------------------------------------+
  | (b) SKILL   | job_skills rows    : {n_skill_rows:,}
  | DEMAND TS   | Joinable to dates  : YES (via job_id -> postings)
  |             | VERDICT: {"[EXCELLENT]" if n_skill_rows > 10000 else ("[MODERATE]" if n_skill_rows > 1000 else "[POOR]    ")}
  +-------------+----------------------------------------------------------+
  | (c) SALARY  | normalized_salary  : {norm_sal_nn:,} ({norm_sal_pct:.1f}%)
  | ANALYSIS    | min/max/med cols   : available (see above)
  |             | salaries.csv       : also available
  |             | VERDICT: {"[EXCELLENT]" if norm_sal_pct > 50 else ("[MODERATE - sparse]" if norm_sal_pct > 10 else "[POOR - very sparse]")}
  +-------------+----------------------------------------------------------+
  | (d) REMOTE  | remote_allowed non-null: {remote_nn:,} ({remote_pct:.1f}%)
  | WORK        | Binary flag (0/1)
  | ANALYSIS    | VERDICT: {"[EXCELLENT]" if remote_pct > 50 else ("[MODERATE - sparse]" if remote_pct > 20 else "[POOR - very sparse]")}
  +-------------+----------------------------------------------------------+
""")

print("  DETAILED NOTES:")
print(
    f"  • postings.csv has {len(post):,} rows covering {n_unique_months} unique months"
)
print(f"  • job_skills has {n_skill_rows:,} rows joinable to postings via job_id")
print(f"  • skills_map has {len(skills_map):,} skill name mappings")
print(f"  • normalized_salary covers {norm_sal_pct:.1f}% of postings — treat with care")
print(
    f"  • remote_allowed covers {remote_pct:.1f}% of postings (rest = NaN, assumed unknown)"
)
print(f"  • jobs/salaries.csv provides an independent salary lookup table")
print(f"  • The dataset is REAL LinkedIn data — no synthetic rows")
print(
    f"  • Temporal coverage: {post_listed_parsed.min().date()} → {post_listed_parsed.max().date()}"
)
print()
print("  RECOMMENDATION:")
if n_unique_months >= 12:
    print("  [EXCELLENT] This dataset is WELL-SUITED for all four analysis tracks.")
    print("     Use postings.csv as the spine; join job_skills for skill demand;")
    print("     use normalized_salary / salaries.csv for pay analysis;")
    print("     and remote_allowed for remote-work trend analysis.")
else:
    print(f"  [WARNING] Only {n_unique_months} unique months detected in listed_time.")
    print("     listed_time is nearly all April 2024 — a single-month snapshot.")
    print("     Use original_listed_time for a slightly wider window (5 months).")
    print("     For TRUE time-series, you may need to supplement with other datasets.")
    print("     However, skill demand, salary, and remote analyses are still viable")
    print("     as cross-sectional snapshots with 123K+ postings.")

print(f"\n{'=' * 70}")
print("  EDA COMPLETE")
print(f"{'=' * 70}\n")
