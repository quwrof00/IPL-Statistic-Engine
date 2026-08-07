import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from pathlib import Path

data_dir = Path("d:/ipl-rating/ipl/data")

print("Loading raw Parquet dataset for V9 PCA Efficiency rebuild...")
df = pd.read_parquet(data_dir / "player_season_stats.parquet")

# 1. ERA NORMALIZATION (Z-SCORES OF RATE STATS)
print("Calculating Era Z-Scores for Rate Metrics...")
season_stats = df.groupby("season").agg({
    "batting_average": ["mean", "std"],
    "strike_rate": ["mean", "std"],
    "bowling_average": ["mean", "std"],
    "economy": ["mean", "std"],
    "boundary_pct": ["mean", "std"],
    "dot_ball_pct": ["mean", "std"]
})
season_stats.columns = ['_'.join(col).strip() for col in season_stats.columns.values]
season_stats = season_stats.reset_index()

df = df.merge(season_stats, on="season", how="left")

# Calculate Z-Scores
df["z_sr"] = (df["strike_rate"] - df["strike_rate_mean"]) / df["strike_rate_std"].replace(0, 1)
df["z_bat_avg"] = (df["batting_average"] - df["batting_average_mean"]) / df["batting_average_std"].replace(0, 1)
df["z_boundary"] = (df["boundary_pct"] - df["boundary_pct_mean"]) / df["boundary_pct_std"].replace(0, 1)

# Lower is better for bowling average and economy
df["z_econ"] = (df["economy_mean"] - df["economy"]) / df["economy_std"].replace(0, 1)
df["z_bowl_avg"] = (df["bowling_average_mean"] - df["bowling_average"]) / df["bowling_average_std"].replace(0, 1)
df["z_dot"] = (df["dot_ball_pct"] - df["dot_ball_pct_mean"]) / df["dot_ball_pct_std"].replace(0, 1)

# Fill NaNs with 0 (average) for players who didn't bat or didn't bowl
rate_features = ["z_sr", "z_bat_avg", "z_boundary", "z_econ", "z_bowl_avg", "z_dot"]
df[rate_features] = df[rate_features].fillna(0)

# Clip extreme outliers (the 1-ball anomalies)
for f in rate_features:
    df[f] = df[f].clip(-3, 3)

# 2. PCA ON EFFICIENCY MATRIX
print("Training PCA on Efficiency latent space...")
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df[rate_features])

# Train PCA to discover 4 latent dimensions of efficiency
pca = PCA(n_components=4)
pca_features = pca.fit_transform(X_scaled)

# Weight the PCA components by their explained variance
weights = pca.explained_variance_ratio_
raw_pca_score = np.dot(pca_features, weights)

# Normalize the raw PCA score so the worst season is 0
df["pca_efficiency"] = raw_pca_score - raw_pca_score.min()

# 3. THE VOLUME RECTIFIER (Bounded Volume)
print("Applying Square Root Bounded Volume Rectifier...")
# Total balls involved in the game (faced + bowled)
df["total_balls_involved"] = df["balls_faced"].fillna(0) + df["balls_bowled"].fillna(0)

# The square root severely diminishes the gap between 600 balls and 300 balls,
# preventing openers from running away with the leaderboards simply by existing.
df["volume_multiplier"] = np.sqrt(df["total_balls_involved"])

df["v9_unscaled"] = df["pca_efficiency"] * df["volume_multiplier"]

# 4. SCALING TO 99.5
max_v9 = df["v9_unscaled"].max()
df["quwrof_v9"] = (df["v9_unscaled"] / max_v9) * 99.5
df["quwrof_v9"] = df["quwrof_v9"].round(2)

out_df = df.sort_values("quwrof_v9", ascending=False).reset_index(drop=True)

print("\n--- THE V9 LEADERBOARD (PCA EFFICIENCY) ---")
cols_to_show = ["player_name", "season", "total_balls_involved", "pca_efficiency", "volume_multiplier", "quwrof_v9"]
print(out_df[cols_to_show].head(20).round(2).to_string(index=False))

output_path = data_dir / "quwrof_v9_scores.csv"
out_df[["player_name", "season", "quwrof_v9", "pca_efficiency", "volume_multiplier"]].to_csv(output_path, index=False)
print(f"\nV9 scores saved to {output_path}")
