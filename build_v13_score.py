import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.cluster import KMeans
from scipy.stats import norm
from pathlib import Path

data_dir = Path("d:/ipl-rating/ipl/data")

print("Loading raw Ball-by-Ball dataset for V13 ML Probit Engine...")
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

# 7. ML CLUSTERING FOR VOLUME THRESHOLDS (Replaces Manual)
print("Training Unsupervised ML Clustering for Volume Thresholds...")
# Batting Clusters
bat_features = df[["total_runs"]].fillna(0).values.reshape(-1, 1)
kmeans_bat = KMeans(n_clusters=2, random_state=42, n_init=10)
df["bat_cluster"] = kmeans_bat.fit_predict(bat_features)

# Identify which cluster is the "Tail-Ender" cluster (the one with lower average runs)
bat_cluster_centers = kmeans_bat.cluster_centers_.flatten()
tail_ender_cluster = 0 if bat_cluster_centers[0] < bat_cluster_centers[1] else 1

# Bowling Clusters
bowl_features = df[["total_wickets"]].fillna(0).values.reshape(-1, 1)
kmeans_bowl = KMeans(n_clusters=2, random_state=42, n_init=10)
df["bowl_cluster"] = kmeans_bowl.fit_predict(bowl_features)

bowl_cluster_centers = kmeans_bowl.cluster_centers_.flatten()
part_timer_cluster = 0 if bowl_cluster_centers[0] < bowl_cluster_centers[1] else 1

# 8. PERCENTILE DISTRIBUTION WITH ML MASKS
print("Mapping to Percentile Distribution...")
bat_mask = df["bat_cluster"] != tail_ender_cluster
df.loc[bat_mask, "bat_percentile"] = df.loc[bat_mask, "raw_bat"].rank(pct=True) * 100
df["bat_percentile"] = df["bat_percentile"].fillna(0)

bowl_mask = df["bowl_cluster"] != part_timer_cluster
df.loc[bowl_mask, "bowl_percentile"] = df.loc[bowl_mask, "raw_bowl"].rank(pct=True) * 100
df["bowl_percentile"] = df["bowl_percentile"].fillna(0)

# 9. PROBIT TRANSFORMATION (Inverse CDF)
print("Applying Probit Transformation (Inverse CDF)...")
# Convert percentiles (0-100) to probabilities (0-1).
# Cap at 0.9999 and 0.0001 to avoid infinite Z-Scores.
df["bat_prob"] = (df["bat_percentile"] / 100).clip(0.0001, 0.9999)
df["bowl_prob"] = (df["bowl_percentile"] / 100).clip(0.0001, 0.9999)

# Transform into infinite Gaussian Z-Scores
df["bat_z"] = np.where(df["bat_percentile"] > 0, norm.ppf(df["bat_prob"]), 0)
df["bowl_z"] = np.where(df["bowl_percentile"] > 0, norm.ppf(df["bowl_prob"]), 0)

# 10. NON-LINEAR EQUILIBRIUM (Specialist Formula)
df["max_z"] = df[["bat_z", "bowl_z"]].max(axis=1)
df["min_z"] = df[["bat_z", "bowl_z"]].min(axis=1)

df["v13_raw"] = df["max_z"] + (0.10 * df["min_z"])

# 11. FINAL SCALING
max_v13 = df["v13_raw"].max()
df["quwrof_v13"] = (df["v13_raw"] / max_v13) * 99.5
df["quwrof_v13"] = df["quwrof_v13"].round(2)

out_df = df.sort_values("quwrof_v13", ascending=False).reset_index(drop=True)

print("\n--- THE V13 LEADERBOARD (PROBIT ML ENGINE) ---")
cols_to_show = ["player_name", "season", "bat_percentile", "bowl_percentile", "quwrof_v13"]
print(out_df[cols_to_show].head(20).round(2).to_string(index=False))

output_path = data_dir / "quwrof_v13_scores.csv"
out_df[["player_name", "season", "quwrof_v13", "bat_percentile", "bowl_percentile", "bat_z", "bowl_z"]].to_csv(output_path, index=False)
print(f"\nV13 scores saved to {output_path}")
