import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy.spatial.distance import mahalanobis
from scipy.stats import rankdata
from pathlib import Path

print("Loading data...")
stats_df = pd.read_parquet("d:/ipl-rating/ipl/data/player_season_stats.parquet")
v1_scores = pd.read_csv("d:/ipl-rating/ipl/data/quwrof_scores.csv")
v2_scores = pd.read_csv("d:/ipl-rating/ipl/data/quwrof_v2_scores.csv")

v1_scores["season"] = v1_scores["season"].astype(str)
stats_df["season"] = stats_df["season"].astype(str)
v2_scores["season"] = v2_scores["season"].astype(str)

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

print("Running PCA to get orthogonal embeddings...")
pca = PCA(n_components=3)
X_pca = pca.fit_transform(X_scaled)

pca_df = pd.DataFrame(X_pca, columns=["PC1", "PC2", "PC3"])
pca_df["player_name"] = qualifiers["player_name"].values
pca_df["season"] = qualifiers["season"].values

model_df = pd.merge(pca_df, v1_scores[["player_name", "season", "impact_score", "quwrof_score"]], on=["player_name", "season"], how="inner")
model_df = pd.merge(model_df, v2_scores[["player_name", "season", "quwrof_v2"]], on=["player_name", "season"], how="inner")

print("Constructing 4D Feature Space (PC1, PC2, PC3, Impact)...")
X_mahal = model_df[["PC1", "PC2", "PC3", "impact_score"]].values

print("Computing Covariance and Centroid...")
centroid = np.mean(X_mahal, axis=0)
covariance_matrix = np.cov(X_mahal, rowvar=False)
inv_covariance_matrix = np.linalg.inv(covariance_matrix)

print("Calculating Mahalanobis Greatness Distances...")
distances = []
for i in range(len(X_mahal)):
    dist = mahalanobis(X_mahal[i], centroid, inv_covariance_matrix)
    distances.append(dist)

model_df["mahalanobis_distance"] = distances

print("Converting Distances to Percentiles (QuwrofScore v3)...")
# Higher distance = Greater statistical rarity = Higher Percentile
model_df["mahalanobis_pct"] = (rankdata(model_df["mahalanobis_distance"]) / len(model_df)) * 100

# Scale to 99.5
model_df["quwrof_v3"] = (model_df["mahalanobis_pct"] / 100.0) * 99.5
model_df["quwrof_v3"] = model_df["quwrof_v3"].round(2)

print("\n--- FINAL QUWROFSCORE v3 (Mahalanobis Engine) ---")
final_rankings = model_df.sort_values("quwrof_v3", ascending=False).head(20)
print(final_rankings[["player_name", "season", "PC1", "PC2", "PC3", "impact_score", "mahalanobis_distance", "quwrof_v3"]].round(2).to_string(index=False))

# Save
output_path = Path("d:/ipl-rating/ipl/data/quwrof_v3_scores.csv")
model_df.sort_values("quwrof_v3", ascending=False).to_csv(output_path, index=False)
print(f"\nFinal Mahalanobis v3 scores saved to {output_path}")
