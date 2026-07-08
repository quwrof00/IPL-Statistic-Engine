import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

print("Loading data...")
df = pd.read_parquet("d:/ipl-rating/ipl/data/player_season_stats.parquet")

# Filter out extreme low-sample noise (similar to our quwrof qualifiers)
qualifiers = df[(df["balls_faced"] >= 50) | (df["balls_bowled"] >= 60)].copy()

print(f"Qualified seasons: {len(qualifiers)}")

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

# Fill NaNs with 0 (since non-bowlers will have NaN for bowling_average, relative stats, etc.)
X = qualifiers[feature_cols].fillna(0)

print("Standardizing features...")
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print("Fitting PCA...")
pca = PCA()
X_pca = pca.fit_transform(X_scaled)

explained = pd.DataFrame({
    "PC": [f"PC{i+1}" for i in range(len(pca.explained_variance_ratio_))],
    "Variance": pca.explained_variance_ratio_
})

print("\n--- Top 10 Principal Components ---")
print(explained.head(10).to_string(index=False))

# Let's also look at the feature loadings for PC1 and PC2 to see what they represent
loadings = pd.DataFrame(pca.components_.T, columns=[f"PC{i+1}" for i in range(len(pca.components_))], index=feature_cols)

print("\n--- What does PC1 represent? (Top 5 Positive & Negative Features) ---")
print("Positive drivers:")
print(loadings["PC1"].sort_values(ascending=False).head(5))
print("\nNegative drivers:")
print(loadings["PC1"].sort_values().head(5))

print("\n--- What does PC3 represent? (Top 5 Positive & Negative Features) ---")
print("Positive drivers:")
print(loadings["PC3"].sort_values(ascending=False).head(5))
print("\nNegative drivers:")
print(loadings["PC3"].sort_values().head(5))

# Project seasons onto PCs
pc_df = pd.DataFrame(X_pca[:, :4], columns=["PC1", "PC2", "PC3", "PC4"])
pc_df["player_name"] = qualifiers["player_name"].values
pc_df["season"] = qualifiers["season"].values

print("\n--- TOP 20: PC1 (Batting Dominance?) ---")
print(pc_df.sort_values("PC1", ascending=False).head(20)[["player_name", "season", "PC1"]].to_string(index=False))

print("\n--- TOP 20: PC2 (Bowling Dominance?) ---")
print(pc_df.sort_values("PC2", ascending=False).head(20)[["player_name", "season", "PC2"]].to_string(index=False))

print("\n--- TOP 20: PC3 (All-round Greatness?) ---")
print(pc_df.sort_values("PC3", ascending=False).head(20)[["player_name", "season", "PC3"]].to_string(index=False))
