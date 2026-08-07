import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy.stats import rankdata
from pathlib import Path

print("Loading data...")
stats_df = pd.read_parquet("d:/ipl-rating/ipl/data/player_season_stats.parquet")
scores_df = pd.read_csv("d:/ipl-rating/ipl/data/quwrof_scores.csv")

scores_df["season"] = scores_df["season"].astype(str)
stats_df["season"] = stats_df["season"].astype(str)

qualifiers = stats_df[(stats_df["balls_faced"] >= 50) | (stats_df["balls_bowled"] >= 60)].copy()

feature_cols = [
    # Batting
    "runs", "strike_rate", "batting_average", "boundary_pct",
    "league_relative_runs", "league_relative_sr", "league_relative_avg",
    "runs_in_wins", "runs_in_chases", "playoff_runs", "death_SR", "powerplay_SR",
    "avg_rrr_faced", "batting_failure_rate",
    # Bowling
    "wickets", "economy", "bowling_average", "bowling_SR", "dot_ball_pct",
    "league_relative_wickets", "league_relative_economy", "league_relative_bowling_avg",
    "wickets_in_wins", "death_wickets", "powerplay_wickets", "playoff_wickets",
    "death_economy", "powerplay_economy", "avg_rrr_defended", "bowling_failure_rate",
    # Fielding & Impact
    "catches", "run_outs", "stumpings",
    "avg_match_run_contribution", "avg_match_wicket_contribution"
]

X_raw = qualifiers[feature_cols].fillna(0)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_raw)

print("Running PCA...")
pca = PCA(n_components=3)
X_pca = pca.fit_transform(X_scaled)

pca_df = pd.DataFrame(X_pca, columns=["PC1", "PC2", "PC3"])
pca_df["player_name"] = qualifiers["player_name"].values
pca_df["season"] = qualifiers["season"].values

model_df = pd.merge(pca_df, scores_df[["player_name", "season", "impact_score"]], on=["player_name", "season"], how="inner")

print("Calculating Factor Scores & Percentiles...")
# 1. Transform to Factors
model_df["specialist_factor"] = np.abs(model_df["PC1"])
model_df["strike_bowling_factor"] = model_df["PC2"]
model_df["utility_factor"] = model_df["PC3"]

# 2. Convert to Percentiles (0-100)
model_df["specialist_pct"] = (rankdata(model_df["specialist_factor"]) / len(model_df)) * 100
model_df["strike_bowling_pct"] = (rankdata(model_df["strike_bowling_factor"]) / len(model_df)) * 100
model_df["utility_pct"] = (rankdata(model_df["utility_factor"]) / len(model_df)) * 100

print("Applying Explained Variance Weights...")
# 3. Variance-Driven PCA Score (64% / 19% / 17%)
model_df["pca_component_score"] = (
    0.64 * model_df["specialist_pct"] +
    0.19 * model_df["strike_bowling_pct"] +
    0.17 * model_df["utility_pct"]
)

print("Injecting Contextual Impact...")
# 4. Final QuwrofScore v2 (70% PCA / 30% Impact)
model_df["quwrof_v2"] = (
    0.70 * model_df["pca_component_score"] +
    0.30 * model_df["impact_score"]
)

# If we want the absolute max to hit 99.5 for aesthetic consistency, we can scale it.
# However, this score will naturally max out around 95-98. Let's see what the max is.
max_raw = model_df["quwrof_v2"].max()
# Scaling linearly to 99.5:
model_df["quwrof_v2"] = (model_df["quwrof_v2"] / max_raw) * 99.5
model_df["quwrof_v2"] = model_df["quwrof_v2"].round(2)

print("\n--- FINAL QUWROFSCORE v2 (Mathematical Engine) ---")
final_rankings = model_df.sort_values("quwrof_v2", ascending=False).head(20)
print(final_rankings[["player_name", "season", "specialist_pct", "strike_bowling_pct", "utility_pct", "impact_score", "quwrof_v2"]].round(1).to_string(index=False))

# Save
output_path = Path("d:/ipl-rating/ipl/data/quwrof_v2_scores.csv")
model_df.sort_values("quwrof_v2", ascending=False).to_csv(output_path, index=False)
print(f"\nFinal Mathematical V2 scores saved to {output_path}")
