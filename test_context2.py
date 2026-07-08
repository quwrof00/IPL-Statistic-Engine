import pandas as pd
import numpy as np
from pathlib import Path

data_dir = Path("d:/ipl-rating/ipl/data")
deliveries = pd.read_parquet(data_dir / "deliveries.parquet")
df = pd.read_parquet(data_dir / "player_season_stats.parquet")

print("Calculating Contextual Z-Scores...")
for metric in ["strike_rate", "batting_average", "runs", "powerplay_SR", "death_SR", "economy", "bowling_average", "wickets", "powerplay_economy", "death_economy"]:
    df[f"z_{metric}"] = df.groupby("season")[metric].transform(lambda x: (x - x.mean()) / x.std())

df = df.rename(columns={"z_strike_rate": "z_sr", "z_batting_average": "z_avg", "z_powerplay_SR": "z_pp_sr", "z_death_SR": "z_death_sr", "z_powerplay_economy": "z_pp_econ", "z_death_economy": "z_death_econ"})

df['z_econ'] = -df['z_economy']
df['z_bowl_avg'] = -df['z_bowling_average']
df['z_pp_econ'] = -df['z_pp_econ']
df['z_death_econ'] = -df['z_death_econ']

print("Calculating Leave-One-Out (LOO) Empirical Expectations...")

# Get total season runs and balls
season_totals = df.groupby("season")[["runs", "balls_faced", "runs_in_powerplay", "balls_faced_powerplay", "runs_in_death", "balls_faced_death", "wickets", "balls_bowled"]].sum().reset_index()
season_totals.columns = ["season", "total_runs", "total_balls", "total_pp_runs", "total_pp_balls", "total_death_runs", "total_death_balls", "total_wickets", "total_balls_bowled"]
df = df.merge(season_totals, on="season")

df["loo_runs_scored"] = df["total_runs"] - df["runs"].fillna(0)
df["loo_balls_faced"] = df["total_balls"] - df["balls_faced"].fillna(0)
df["loo_wickets_lost"] = df["total_wickets"] - df["dismissals"].fillna(0)

df["loo_pp_runs"] = df["total_pp_runs"] - df["runs_in_powerplay"].fillna(0)
df["loo_pp_balls"] = df["total_pp_balls"] - df["balls_faced_powerplay"].fillna(0)
df["loo_death_runs"] = df["total_death_runs"] - df["runs_in_death"].fillna(0)
df["loo_death_balls"] = df["total_death_balls"] - df["balls_faced_death"].fillna(0)

df["runs_in_middle"] = df["runs"].fillna(0) - df["runs_in_powerplay"].fillna(0) - df["runs_in_death"].fillna(0)
df["balls_faced_middle"] = df["balls_faced"].fillna(0) - df["balls_faced_powerplay"].fillna(0) - df["balls_faced_death"].fillna(0)
df["loo_mid_runs"] = (df["total_runs"] - df["total_pp_runs"] - df["total_death_runs"]) - df["runs_in_middle"].fillna(0)
df["loo_mid_balls"] = (df["total_balls"] - df["total_pp_balls"] - df["total_death_balls"]) - df["balls_faced_middle"].fillna(0)

df["loo_pp_sr"] = (df["loo_pp_runs"] / df["loo_pp_balls"].replace(0, 1)) * 100
df["loo_mid_sr"] = (df["loo_mid_runs"] / df["loo_mid_balls"].replace(0, 1)) * 100
df["loo_death_sr"] = (df["loo_death_runs"] / df["loo_death_balls"].replace(0, 1)) * 100

# Phase Weights from Logistic Regression
W_PP = 1.00
W_MID = 1.21
W_DEATH = 1.24

# Calculate Weighted Runs and Expected Runs
df["weighted_runs"] = (
    df["runs_in_powerplay"].fillna(0) * W_PP +
    df["runs_in_middle"].fillna(0) * W_MID +
    df["runs_in_death"].fillna(0) * W_DEATH
)

df["weighted_expected_runs"] = (
    df["balls_faced_powerplay"].fillna(0) * (df["loo_pp_sr"] / 100) * W_PP +
    df["balls_faced_middle"].fillna(0) * (df["loo_mid_sr"] / 100) * W_MID +
    df["balls_faced_death"].fillna(0) * (df["loo_death_sr"] / 100) * W_DEATH
)

df["weighted_expected_runs"] = df["weighted_expected_runs"].fillna(df["weighted_runs"])
df["rae"] = df["weighted_runs"] - df["weighted_expected_runs"]

# EXPERIMENTAL CONTEXT IMPACT MATH
df["bat_base"] = df["weighted_runs"] + df["rae"]

# Old chase impact was runs * (avg_rrr_faced / 8.0). Rinku Singh got 2.3x on 280 runs.
# Let's cap RRR multiplier, and use death z_score but much smaller.
df["capped_rrr_ratio"] = (df["avg_rrr_faced"].fillna(8.0) / 8.0).clip(upper=1.5)
df["bat_chase_impact"] = df["runs_in_chases"].fillna(0) * (df["capped_rrr_ratio"] - 1.0).clip(lower=0)
df["bat_playoff_impact"] = df["playoff_runs"].fillna(0) * 0.5

df["raw_bat"] = df["bat_base"] + df["bat_chase_impact"] + df["bat_playoff_impact"]

bat_mask_pct = (df["balls_faced"] >= 30) | (df["innings_batted"] >= 8)
df.loc[bat_mask_pct, "bat_percentile"] = df.loc[bat_mask_pct, "raw_bat"].rank(pct=True) * 100
df["bat_percentile"] = df["bat_percentile"].fillna(0)


print("--- NEW TOP 20 BATTING ---")
print(df.sort_values("bat_percentile", ascending=False)[["player_name", "season", "bat_percentile", "raw_bat", "rae", "bat_chase_impact", "bat_base"]].head(20).to_string(index=False))

print("\n--- RINKU SINGH 2023 ---")
print(df[(df.player_name == 'RK Singh') & (df.season == '2023')][["player_name", "season", "bat_percentile", "raw_bat", "bat_chase_impact", "rae"]].to_string(index=False))

print("\n--- ANDRE RUSSELL 2019 ---")
print(df[(df.player_name == 'AD Russell') & (df.season == '2019')][["player_name", "season", "bat_percentile", "raw_bat", "bat_chase_impact", "rae"]].to_string(index=False))
