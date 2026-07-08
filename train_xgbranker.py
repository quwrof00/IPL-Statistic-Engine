import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from xgboost import XGBRanker
from pathlib import Path

print("Loading data...")
stats_df = pd.read_parquet("d:/ipl-rating/ipl/data/player_season_stats.parquet")
scores_df = pd.read_csv("d:/ipl-rating/ipl/data/quwrof_scores.csv")

# Ensure player_name and season are matching types
scores_df["season"] = scores_df["season"].astype(str)
stats_df["season"] = stats_df["season"].astype(str)

# Filter qualifiers for PCA
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

print("Running PCA to generate latent features...")
pca = PCA(n_components=3)
X_pca = pca.fit_transform(X_scaled)

pca_df = pd.DataFrame(X_pca, columns=["PC1", "PC2", "PC3"])
pca_df["player_name"] = qualifiers["player_name"].values
pca_df["season"] = qualifiers["season"].values

# Merge with existing QuwrofScores to get Impact and Target (y)
model_df = pd.merge(pca_df, scores_df[["player_name", "season", "impact_score", "quwrof_score"]], on=["player_name", "season"], how="inner")

print("Preparing Learning to Rank dataset...")
# Sort by season because rankers require grouped data
model_df = model_df.sort_values(by="season").reset_index(drop=True)

X_train = model_df[["PC1", "PC2", "PC3", "impact_score"]]
y_train = model_df["quwrof_score"].astype(int)

# To perform Learning to Rank, we provide group sizes (how many players per season)
# However, XGBRanker in its modern API can take `qid` directly. Must be integer.
model_df["qid"] = pd.factorize(model_df["season"])[0]
qids = model_df["qid"]

print("Training XGBRanker...")
ranker = XGBRanker(
    objective="rank:pairwise",
    n_estimators=100,
    learning_rate=0.1,
    max_depth=4,
    random_state=42
)

ranker.fit(X_train, y_train, qid=qids)

print("Predicting optimal rankings...")
# Generate raw ranking scores
model_df["xgb_raw_score"] = ranker.predict(X_train)

# The raw output from a pairwise ranker is an arbitrary log-odds margin. 
# We need to scale it to our clean 0-99.5 scale.
# Let's map it to percentiles first to stabilize the arbitrary log-odds scale, then scale to 99.5
from scipy.stats import rankdata

model_df["pca_score_pct"] = (rankdata(model_df["xgb_raw_score"]) / len(model_df)) * 100

# Optional: To make the top player 99.5, we scale the max raw percentile up.
# Actually, the percentile will perfectly scale from 0 to 100.
model_df["final_pca_quwrof"] = (model_df["pca_score_pct"] / 100.0) * 99.5
model_df["final_pca_quwrof"] = model_df["final_pca_quwrof"].round(2)

print("\n--- NEW TOP 20 GREATEST IPL SEASONS (LEARNED VIA XGBRANKER) ---")
final_rankings = model_df.sort_values("final_pca_quwrof", ascending=False).head(20)
print(final_rankings[["player_name", "season", "PC1", "PC2", "PC3", "impact_score", "final_pca_quwrof"]].to_string(index=False))

# Feature importances
print("\n--- What did the Model Learn? (Feature Importances) ---")
importances = pd.DataFrame({
    "Feature": X_train.columns,
    "Importance": ranker.feature_importances_
}).sort_values("Importance", ascending=False)
print(importances.to_string(index=False))

# Save
output_path = Path("d:/ipl-rating/ipl/data/quwrof_pca_scores.csv")
model_df.sort_values("final_pca_quwrof", ascending=False).to_csv(output_path, index=False)
print(f"\nFinal PCA-driven scores saved to {output_path}")
