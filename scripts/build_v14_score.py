import pandas as pd
import numpy as np
from pathlib import Path

data_dir = Path("d:/ipl-rating/ipl/data")

print("Loading V11 Submetrics for V14 (Uncapped Z-Score Engine)...")
# We load the V11 scores because V14 directly utilizes the exact V11 submetrics.
df = pd.read_csv(data_dir / "quwrof_v11_scores.csv")

# Masks for active players to find the true mean (excluding non-batters and non-bowlers)
bat_mask = df['raw_bat'] > 0
bowl_mask = df['raw_bowl'] > 0

bat_cols = ['bat_base', 'bat_chase_impact', 'bat_playoff_impact']
bowl_cols = ['bowl_base', 'bowl_pp_impact', 'bowl_death_impact', 'bowl_playoff_impact', 'bowl_pressure_impact']

print("Calculating Standard Deviations and Means...")
stats = {}
for col in bat_cols:
    stats[col] = {'mean': df.loc[bat_mask, col].mean(), 'std': df.loc[bat_mask, col].std()}
for col in bowl_cols:
    stats[col] = {'mean': df.loc[bowl_mask, col].mean(), 'std': df.loc[bowl_mask, col].std()}

# Hardcode the data-backed weights approved by the user
weights = {
    'bat_base': 375.0,
    'bat_chase_impact': 75.0,
    'bat_playoff_impact': 50.0,
    'bowl_base': 315.0,
    'bowl_pressure_impact': 75.0,
    'bowl_playoff_impact': 50.0,
    'bowl_pp_impact': 35.0,
    'bowl_death_impact': 25.0
}


print("\nApplying Uncapped Z-Scores...")
df['quwrof_v14'] = 0.0

for col in bat_cols:
    # Calculate Z-score. We floor negative Z-scores at 0 so bowlers aren't punished for bad batting.
    z_score = np.where(df['raw_bat'] > 0, (df[col] - stats[col]['mean']) / stats[col]['std'], 0)
    z_score = np.maximum(0, z_score)
    df[col + '_points'] = z_score * weights[col]
    df['quwrof_v14'] += df[col + '_points']

for col in bowl_cols:
    # Calculate Z-score. We floor negative Z-scores at 0 so batters aren't punished for bad bowling.
    z_score = np.where(df['raw_bowl'] > 0, (df[col] - stats[col]['mean']) / stats[col]['std'], 0)
    z_score = np.maximum(0, z_score)
    df[col + '_points'] = z_score * weights[col]
    df['quwrof_v14'] += df[col + '_points']

# We still retain percentiles for display/context if needed, but the primary ranking is V14 points
df = df.sort_values('quwrof_v14', ascending=False).reset_index(drop=True)

# Add Bat/Bowl specific totals for UI / Context
df['bat_points'] = df[[col + '_points' for col in bat_cols]].sum(axis=1)
df['bowl_points'] = df[[col + '_points' for col in bowl_cols]].sum(axis=1)

# Ensure the output format matches what the frontend expects
df['quwrof_v14'] = df['quwrof_v14'].round(2)

# Calculate percentiles for V14
# Overall percentile among all players
df['v14_percentile'] = df['quwrof_v14'].rank(pct=True) * 100
# Bat percentile among players who actually batted
df['v14_bat_percentile'] = 0.0
batters = df['bat_points'] > 0
if batters.any():
    df.loc[batters, 'v14_bat_percentile'] = df.loc[batters, 'bat_points'].rank(pct=True) * 100

# Bowl percentile among players who actually bowled
df['v14_bowl_percentile'] = 0.0
bowlers = df['bowl_points'] > 0
if bowlers.any():
    df.loc[bowlers, 'v14_bowl_percentile'] = df.loc[bowlers, 'bowl_points'].rank(pct=True) * 100

print("\n--- THE V14 LEADERBOARD (UNCAPPED Z-SCORE ENGINE) ---")
cols_to_show = ['player_name', 'season', 'quwrof_v14', 'bat_points', 'bowl_points']
print(df[cols_to_show].head(20).round(1).to_string(index=False))

output_path = data_dir / "quwrof_v14_scores.csv"

# Make sure we save all columns expected by frontend (submetrics, etc.)
out_cols = [
    "player_name", "season", "quwrof_v14", "bat_percentile", "bowl_percentile", 
    "bat_base", "bat_chase_impact", "bat_playoff_impact", "raw_bat", "rae", 
    "smart_wickets", "empirical_wickets", "bowl_base", "bowl_pp_impact", 
    "bowl_death_impact", "bowl_playoff_impact", "bowl_pressure_impact", "raw_bowl",
    "bat_points", "bowl_points", "v14_percentile", "v14_bat_percentile", "v14_bowl_percentile",
    "bat_playoff_impact_points", "bowl_playoff_impact_points",
    "bat_base_points", "bat_chase_impact_points", 
    "bowl_base_points", "bowl_pp_impact_points", "bowl_death_impact_points", "bowl_pressure_impact_points"
]
df[out_cols].to_csv(output_path, index=False)
print(f"\nV14 scores saved to {output_path}")
