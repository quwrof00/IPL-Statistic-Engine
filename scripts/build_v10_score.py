import pandas as pd
import numpy as np
from pathlib import Path

data_dir = Path("d:/ipl-rating/ipl/data")

print("Loading raw Parquet dataset for V10 Domain Normalization...")
df = pd.read_parquet(data_dir / "player_season_stats.parquet")

# 1. ERA NORMALIZATION (Z-SCORES)
print("Calculating Era Z-Scores...")
season_stats = df.groupby("season").agg({
    "batting_average": ["mean", "std"],
    "strike_rate": ["mean", "std"],
    "bowling_average": ["mean", "std"],
    "economy": ["mean", "std"]
})
season_stats.columns = ['_'.join(col).strip() for col in season_stats.columns.values]
season_stats = season_stats.reset_index()

df = df.merge(season_stats, on="season", how="left")

df["z_sr"] = (df["strike_rate"] - df["strike_rate_mean"]) / df["strike_rate_std"].replace(0, 1)
df["z_bat_avg"] = (df["batting_average"] - df["batting_average_mean"]) / df["batting_average_std"].replace(0, 1)
df["z_econ"] = (df["economy_mean"] - df["economy"]) / df["economy_std"].replace(0, 1)
df["z_bowl_avg"] = (df["bowling_average_mean"] - df["bowling_average"]) / df["bowling_average_std"].replace(0, 1)

# Cap extreme outliers to prevent 1-ball anomalies from destroying math
for col in ["z_sr", "z_bat_avg", "z_econ", "z_bowl_avg"]:
    df[col] = df[col].clip(-3, 4).fillna(0)

# 2. CONTEXT MULTIPLIERS (Playoffs = 1.5x)
print("Applying Context Multipliers...")
df["adjusted_runs"] = (df["runs"].fillna(0) - df["playoff_runs"].fillna(0)) + (df["playoff_runs"].fillna(0) * 1.5)
df["adjusted_wickets"] = (df["wickets"].fillna(0) - df["playoff_wickets"].fillna(0)) + (df["playoff_wickets"].fillna(0) * 1.5)

# 3. RAW VALUES
# Ensure positive multipliers by adding a +1 base to Z-scores
df["raw_batting_value"] = df["adjusted_runs"] * (np.maximum(0, df["z_sr"] + 1) + np.maximum(0, df["z_bat_avg"] + 1))
df["raw_bowling_value"] = (df["adjusted_wickets"] * 15) * (np.maximum(0, df["z_econ"] + 1) + np.maximum(0, df["z_bowl_avg"] + 1))

# Apply Bounded Consistency Penalty (Max 10% penalty for massive failure rates)
df["batting_penalty"] = np.minimum(0.10, df["batting_failure_rate"].fillna(0))
df["bowling_penalty"] = np.minimum(0.10, df["bowling_failure_rate"].fillna(0))

df["raw_batting_value"] = df["raw_batting_value"] * (1 - df["batting_penalty"])
df["raw_bowling_value"] = df["raw_bowling_value"] * (1 - df["bowling_penalty"])

# 4. INDEPENDENT DOMAIN NORMALIZATION (The Fix)
print("Normalizing Domains Independently...")
max_bat_value = df["raw_batting_value"].max()
max_bowl_value = df["raw_bowling_value"].max()

df["scaled_batting"] = (df["raw_batting_value"] / max_bat_value) * 100
df["scaled_bowling"] = (df["raw_bowling_value"] / max_bowl_value) * 100

# 5. SPECIALIST COMBINATION
df["max_skill"] = df[["scaled_batting", "scaled_bowling"]].max(axis=1)
df["min_skill"] = df[["scaled_batting", "scaled_bowling"]].min(axis=1)

df["v10_raw"] = df["max_skill"] + (0.35 * df["min_skill"])

# 6. ML OVERLAY: PARETO FRONT BONUS
print("Injecting Pareto Front ML Data...")
df_v4 = pd.read_csv(data_dir / "quwrof_v4_scores.csv")[["player_name", "season", "pareto_front"]]
df = df.merge(df_v4, on=["player_name", "season"], how="left")

# +5% Bonus for Mathematically Invincible Seasons
df["pareto_bonus"] = np.where(df["pareto_front"] == 1, 1.05, 1.0)
df["quwrof_v10_unscaled"] = df["v10_raw"] * df["pareto_bonus"]

# 7. FINAL SCALING
max_v10 = df["quwrof_v10_unscaled"].max()
df["quwrof_v10"] = (df["quwrof_v10_unscaled"] / max_v10) * 99.5
df["quwrof_v10"] = df["quwrof_v10"].round(2)

out_df = df.sort_values("quwrof_v10", ascending=False).reset_index(drop=True)

print("\n--- THE V10 LEADERBOARD (DOMAIN NORMALIZATION) ---")
cols_to_show = ["player_name", "season", "scaled_batting", "scaled_bowling", "quwrof_v10"]
print(out_df[cols_to_show].head(20).round(2).to_string(index=False))

output_path = data_dir / "quwrof_v10_scores.csv"
out_df[["player_name", "season", "quwrof_v10", "scaled_batting", "scaled_bowling"]].to_csv(output_path, index=False)
print(f"\nV10 scores saved to {output_path}")
