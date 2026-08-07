import pandas as pd
import numpy as np
from pathlib import Path

data_dir = Path("d:/ipl-rating/ipl/data")

print("Loading raw Ball-by-Ball dataset for V12 Leverage Engine...")
deliv = pd.read_parquet(data_dir / "deliveries.parquet")

# 1. IDENTIFY TOP 4 BATSMEN PER INNING
print("Calculating Batting Orders...")
batter_entry = deliv.groupby(["match_id", "inning", "batter"])["balls_elapsed"].min().reset_index()
batter_entry["batting_position"] = batter_entry.groupby(["match_id", "inning"])["balls_elapsed"].rank(method="first")
batter_entry["is_top_4"] = batter_entry["batting_position"] <= 4

# Map is_top_4 to the player_out column in deliveries
deliv = deliv.merge(batter_entry[["match_id", "inning", "batter", "is_top_4"]], 
                    left_on=["match_id", "inning", "player_out"], 
                    right_on=["match_id", "inning", "batter"], 
                    how="left", suffixes=("", "_out_batter"))

deliv["is_top_4"] = deliv["is_top_4"].fillna(False)

# 2. CALCULATE LEVERAGE & PRESSURE INDEX BALL-BY-BALL
print("Calculating Leverage Indices...")
# Pressure based on wickets lost. Average = 3 wickets = 1.0
deliv["pressure_multiplier"] = (deliv["wickets_before"] + 1) / 4.0

# Leverage based on RRR in chases
deliv["leverage_index"] = np.where(deliv["inning"] == 2, 
                                   (deliv["rrr"].fillna(8.0) / 8.0) * deliv["pressure_multiplier"], 
                                   deliv["pressure_multiplier"])

# Cap extreme leverage to prevent wild distortions
deliv["leverage_index"] = deliv["leverage_index"].clip(0.5, 3.0)

# Valid wicket types for bowlers
valid_dismissals = ['bowled', 'caught', 'lbw', 'stumped', 'caught and bowled', 'hit wicket']
deliv["is_valid_wicket"] = (deliv["is_wicket"] == 1) & (deliv["dismissal_kind"].isin(valid_dismissals))

# 3. CALCULATE LEVERAGE EVENTS
deliv["leverage_runs"] = deliv["batter_runs"] * deliv["leverage_index"]
deliv["leverage_wickets"] = deliv["is_valid_wicket"].astype(int) * deliv["leverage_index"] * np.where(deliv["is_top_4"], 1.15, 1.0)

# 4. AGGREGATE TO PLAYER-SEASON LEVEL
print("Aggregating to Player-Season...")
# Batting Stats
bat_stats = deliv.groupby(["batter", "season"]).agg(
    total_runs=("batter_runs", "sum"),
    balls_faced=("is_wide", lambda x: (~x.astype(bool)).sum()), # balls faced excludes wides
    leverage_runs=("leverage_runs", "sum"),
    playoff_leverage_runs=("leverage_runs", lambda x: x[deliv.loc[x.index, "is_playoff"] == 1].sum())
).reset_index().rename(columns={"batter": "player_name"})

# Bowling Stats
bowl_stats = deliv.groupby(["bowler", "season"]).agg(
    total_wickets=("is_valid_wicket", "sum"),
    runs_conceded=("total_runs", lambda x: x[~deliv.loc[x.index, "is_legbye"].astype(bool) & ~deliv.loc[x.index, "is_bye"].astype(bool)].sum()),
    balls_bowled=("is_wide", lambda x: (~x.astype(bool)).sum() - deliv.loc[x.index, "is_noball"].astype(int).sum()), # legal deliveries
    leverage_wickets=("leverage_wickets", "sum"),
    playoff_leverage_wickets=("leverage_wickets", lambda x: x[deliv.loc[x.index, "is_playoff"] == 1].sum())
).reset_index().rename(columns={"bowler": "player_name"})

# Merge stats
df = pd.merge(bat_stats, bowl_stats, on=["player_name", "season"], how="outer").fillna(0)

# Calculate rates
df["strike_rate"] = np.where(df["balls_faced"] > 0, (df["total_runs"] / df["balls_faced"]) * 100, 0)
df["economy"] = np.where(df["balls_bowled"] > 0, (df["runs_conceded"] / (df["balls_bowled"] / 6)), 0)

# 5. ERA Z-SCORES
print("Calculating Era Z-Scores...")
season_stats = df.groupby("season").agg({
    "strike_rate": ["mean", "std"],
    "economy": ["mean", "std"]
})
season_stats.columns = ['_'.join(col).strip() for col in season_stats.columns.values]
season_stats = season_stats.reset_index()

df = df.merge(season_stats, on="season", how="left")

df["z_sr"] = (df["strike_rate"] - df["strike_rate_mean"]) / df["strike_rate_std"].replace(0, 1)
df["z_econ"] = (df["economy_mean"] - df["economy"]) / df["economy_std"].replace(0, 1)

# Cap Z-Scores to avoid 1-ball anomalies
df["z_sr"] = df["z_sr"].clip(-3, 4).fillna(0)
df["z_econ"] = df["z_econ"].clip(-3, 4).fillna(0)

# 6. RAW V12 SCORES WITH PLAYOFF MULTIPLIER (1.25x)
print("Applying Playoff Context (1.25x)...")
df["adjusted_lev_runs"] = df["leverage_runs"] + (df["playoff_leverage_runs"] * 0.25)
df["adjusted_lev_wickets"] = df["leverage_wickets"] + (df["playoff_leverage_wickets"] * 0.25)

df["raw_bat"] = df["adjusted_lev_runs"] * np.maximum(0, df["z_sr"] + 1)
df["raw_bowl"] = (df["adjusted_lev_wickets"] * 15) * np.maximum(0, df["z_econ"] + 1)

# 7. PERCENTILE DISTRIBUTION (WITH VOLUME THRESHOLDS)
print("Mapping to Percentile Distribution...")
# We enforce strict volume thresholds. You do not get a batting percentile if you scored less than 150 runs.
# This completely eliminates the "tail-ender illusion" where scoring 30 runs gave bowlers a 40th percentile bonus.
bat_mask = df["total_runs"] >= 150
df.loc[bat_mask, "bat_percentile"] = df.loc[bat_mask, "raw_bat"].rank(pct=True) * 100
df["bat_percentile"] = df["bat_percentile"].fillna(0)

# You do not get a bowling percentile if you took fewer than 5 wickets.
bowl_mask = df["total_wickets"] >= 5
df.loc[bowl_mask, "bowl_percentile"] = df.loc[bowl_mask, "raw_bowl"].rank(pct=True) * 100
df["bowl_percentile"] = df["bowl_percentile"].fillna(0)

# 8. SPECIALIST EQUILIBRIUM (User tweaked to 0.10)
df["max_pct"] = df[["bat_percentile", "bowl_percentile"]].max(axis=1)
df["min_pct"] = df[["bat_percentile", "bowl_percentile"]].min(axis=1)

df["v12_raw"] = df["max_pct"] + (0.10 * df["min_pct"])

# 9. FINAL SCALING
max_v12 = df["v12_raw"].max()
df["quwrof_v12"] = (df["v12_raw"] / max_v12) * 99.5
df["quwrof_v12"] = df["quwrof_v12"].round(2)

out_df = df.sort_values("quwrof_v12", ascending=False).reset_index(drop=True)

print("\n--- THE V12 LEADERBOARD (LEVERAGE ENGINE) ---")
cols_to_show = ["player_name", "season", "bat_percentile", "bowl_percentile", "quwrof_v12"]
print(out_df[cols_to_show].head(20).round(2).to_string(index=False))

output_path = data_dir / "quwrof_v12_scores.csv"
out_df[["player_name", "season", "quwrof_v12", "bat_percentile", "bowl_percentile"]].to_csv(output_path, index=False)
print(f"\nV12 scores saved to {output_path}")
