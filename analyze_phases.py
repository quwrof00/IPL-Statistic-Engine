import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from pathlib import Path

data_dir = Path("d:/ipl-rating/ipl/data")
deliveries = pd.read_parquet(data_dir / "deliveries.parquet")

# Filter for first innings only (batting first) to avoid chase-completed-early bias
deliveries_1st = deliveries[deliveries["inning"] == 1]

# Calculate runs scored by each team in each phase per match
# Phase definitions: PP (0-5), Mid (6-14), Death (15-19)
phase_runs = deliveries_1st.groupby(["match_id", "batting_team"]).agg(
    pp_runs=("total_runs", lambda x: x[deliveries_1st.loc[x.index, "over"] < 6].sum()),
    mid_runs=("total_runs", lambda x: x[(deliveries_1st.loc[x.index, "over"] >= 6) & (deliveries_1st.loc[x.index, "over"] < 15)].sum()),
    death_runs=("total_runs", lambda x: x[deliveries_1st.loc[x.index, "over"] >= 15].sum()),
    winner=("winner", "first")
).reset_index()

# Create boolean target: Did this batting_team win the match?
phase_runs["is_win"] = (phase_runs["batting_team"] == phase_runs["winner"]).astype(int)

# 1. Correlation with Winning
print("--- CORRELATION WITH WINNING ---")
print(phase_runs[["pp_runs", "mid_runs", "death_runs", "is_win"]].corr()["is_win"])

# 2. Logistic Regression (Impact of 1 extra run in each phase on Win Probability)
X = phase_runs[["pp_runs", "mid_runs", "death_runs"]]
y = phase_runs["is_win"]

model = LogisticRegression().fit(X, y)
weights = pd.Series(model.coef_[0], index=["pp_runs", "mid_runs", "death_runs"])
print("\n--- LOGISTIC REGRESSION COEFFICIENTS ---")
print(weights)

# Normalize so the minimum weight is 1.0 (baseline)
normalized_weights = weights / weights.min()
print("\n--- NORMALIZED PHASE WEIGHTS (Base = 1.0) ---")
print(normalized_weights)
