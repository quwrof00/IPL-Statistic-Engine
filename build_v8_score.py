import pandas as pd
import numpy as np
from pathlib import Path

data_dir = Path("d:/ipl-rating/ipl/data")

print("Loading raw Parquet dataset for V8 Era-Adjusted rebuild...")
df = pd.read_parquet(data_dir / "player_season_stats.parquet")

# 1. ERA NORMALIZATION (Z-SCORES)
print("Calculating Era Z-Scores...")
# Calculate league averages per season
season_stats = df.groupby("season").agg({
    "batting_average": ["mean", "std"],
    "strike_rate": ["mean", "std"],
    "bowling_average": ["mean", "std"],
    "economy": ["mean", "std"]
})
season_stats.columns = ['_'.join(col).strip() for col in season_stats.columns.values]
season_stats = season_stats.reset_index()

# Merge back
df = df.merge(season_stats, on="season", how="left")

# Calculate Z-Scores (safeguard against div by zero)
df["z_sr"] = (df["strike_rate"] - df["strike_rate_mean"]) / df["strike_rate_std"].replace(0, 1)
df["z_bat_avg"] = (df["batting_average"] - df["batting_average_mean"]) / df["batting_average_std"].replace(0, 1)

# Lower is better for bowling, so we invert the Z-score logic
df["z_econ"] = (df["economy_mean"] - df["economy"]) / df["economy_std"].replace(0, 1)
df["z_bowl_avg"] = (df["bowling_average_mean"] - df["bowling_average"]) / df["bowling_average_std"].replace(0, 1)

# Cap extreme Z-scores to prevent bizarre 1-ball anomalies from destroying the math
df["z_sr"] = df["z_sr"].clip(-3, 4)
df["z_bat_avg"] = df["z_bat_avg"].clip(-3, 4)
df["z_econ"] = df["z_econ"].clip(-3, 4)
df["z_bowl_avg"] = df["z_bowl_avg"].clip(-3, 4)

# 2. PLAYOFF CLUTCH MULTIPLIER
print("Applying Playoff Multipliers...")
# Runs in playoffs count as 1.5x regular runs. Same for wickets.
df["adjusted_runs"] = (df["runs"] - df["playoff_runs"].fillna(0)) + (df["playoff_runs"].fillna(0) * 1.5)
df["adjusted_wickets"] = (df["wickets"] - df["playoff_wickets"].fillna(0)) + (df["playoff_wickets"].fillna(0) * 1.5)

# 3. BASE VALUE CALCULATIONS
# A player's Batting Value is their Era-Adjusted efficiency scaled by their volume
# We add a base of 2 to Z-scores to ensure positive multipliers for decent players
df["batting_value"] = df["adjusted_runs"] * (np.maximum(0, df["z_sr"] + 1) + np.maximum(0, df["z_bat_avg"] + 1))
df["bowling_value"] = (df["adjusted_wickets"] * 15) * (np.maximum(0, df["z_econ"] + 1) + np.maximum(0, df["z_bowl_avg"] + 1))

# 4. BOUNDED CONSISTENCY PENALTY
print("Applying Consistency Penalty...")
# Penalize massive failure rates, max penalty 10%
df["batting_penalty"] = np.minimum(0.10, df["batting_failure_rate"].fillna(0))
df["bowling_penalty"] = np.minimum(0.10, df["bowling_failure_rate"].fillna(0))

df["batting_value"] = df["batting_value"] * (1 - df["batting_penalty"])
df["bowling_value"] = df["bowling_value"] * (1 - df["bowling_penalty"])

# Scale values to a 0-100 baseline before the Specialist Formula
max_bat = df["batting_value"].max()
max_bowl = df["bowling_value"].max()
df["batting_value_scaled"] = (df["batting_value"] / max_bat) * 100
df["bowling_value_scaled"] = (df["bowling_value"] / max_bowl) * 100

# 5. THE SPECIALIST DEFENSE FORMULA
print("Applying Bounded Utility Formula...")
df["max_skill"] = df[["batting_value_scaled", "bowling_value_scaled"]].max(axis=1)
df["min_skill"] = df[["batting_value_scaled", "bowling_value_scaled"]].min(axis=1)
df["v8_raw"] = df["max_skill"] + (0.35 * df["min_skill"])

# 6. ML OVERLAY: PARETO FRONT BONUS
print("Injecting Pareto Front ML Data...")
# Load Pareto data to get Fronts
df_v4 = pd.read_csv(data_dir / "quwrof_v4_scores.csv")[["player_name", "season", "pareto_front"]]
df = df.merge(df_v4, on=["player_name", "season"], how="left")

# If you are in Front 1 (Mathematically Invincible), you get a 5% Legendary Bonus
df["pareto_bonus"] = np.where(df["pareto_front"] == 1, 1.05, 1.0)
df["quwrof_v8_unscaled"] = df["v8_raw"] * df["pareto_bonus"]

# Final Scaling to 99.5
max_v8 = df["quwrof_v8_unscaled"].max()
df["quwrof_v8"] = (df["quwrof_v8_unscaled"] / max_v8) * 99.5
df["quwrof_v8"] = df["quwrof_v8"].round(2)

out_df = df.sort_values("quwrof_v8", ascending=False).reset_index(drop=True)

print("\n--- THE V8 LEADERBOARD (GROUND ZERO REBUILD) ---")
cols_to_show = ["player_name", "season", "adjusted_runs", "adjusted_wickets", "z_sr", "z_econ", "quwrof_v8"]
print(out_df[cols_to_show].head(20).round(2).to_string(index=False))

output_path = data_dir / "quwrof_v8_scores.csv"
out_df[["player_name", "season", "quwrof_v8", "z_sr", "z_econ"]].to_csv(output_path, index=False)
print(f"\nV8 scores saved to {output_path}")
