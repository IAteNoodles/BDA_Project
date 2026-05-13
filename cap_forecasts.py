#!/usr/bin/env python3
"""Cap forecasts to 5x historical maximum per skill"""
import subprocess
import re

def run_psql(sql):
    """Run psql command"""
    result = subprocess.run(
        ['docker', 'exec', 'postgres', 'psql', '-U', 'postgres', '-d', 'job_market', '-c', sql],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout + result.stderr

# Get historical max per skill
print("Getting historical max per skill...")
sql_hist = "SELECT skill_name, MAX(demand_count) as hist_max FROM skill_demand GROUP BY skill_name ORDER BY hist_max DESC;"
output = run_psql(sql_hist)

skill_maxes = {}
for line in output.split('\n')[2:]:  # Skip header
    if '|' not in line or not line.strip():
        continue
    parts = [p.strip() for p in line.split('|')]
    if len(parts) >= 2 and parts[0] and parts[1]:
        try:
            skill = parts[0]
            hist_max = float(parts[1])
            skill_maxes[skill] = hist_max
            print(f"  {skill}: hist_max={hist_max:.0f} -> cap={hist_max*5:.0f}")
        except ValueError:
            continue

# Cap forecasts
print("\nCapping forecasts...")
total_capped = 0
for skill, hist_max in skill_maxes.items():
    cap_value = hist_max * 5
    # Escape single quotes in skill names
    skill_escaped = skill.replace("'", "''")
    sql_cap = f"UPDATE forecast_results SET predicted_demand = LEAST(predicted_demand, {cap_value}) WHERE skill_name = '{skill_escaped}' AND predicted_demand > {cap_value};"
    result = run_psql(sql_cap)
    if 'UPDATE' in result:
        count = re.search(r'UPDATE (\d+)', result)
        if count:
            rows = int(count.group(1))
            total_capped += rows
            if rows > 0:
                print(f"  {skill}: capped {rows} rows to {cap_value:.0f}")

print(f"\nTotal rows capped: {total_capped}")

# Verify
print("\nVerifying caps...")
sql_verify = "SELECT skill_name, MIN(predicted_demand), MAX(predicted_demand) FROM forecast_results GROUP BY skill_name ORDER BY MAX(predicted_demand) DESC LIMIT 10;"
output = run_psql(sql_verify)
print(output)
