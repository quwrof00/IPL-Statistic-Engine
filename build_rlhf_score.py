import pandas as pd
import numpy as np
from pathlib import Path

data_dir = Path("d:/ipl-rating/ipl/data")

print("Loading base scores for RLHF Weighting...")
scores_df = pd.read_csv(data_dir / "quwrof_scores.csv")

# RLHF Weights learned from Human Calibration:
# A1: Preferred SR over Volume -> High Batting Weight
# A3: Preferred Economy/Powerplay over Death -> High Bowling Weight
# A4: Preferred Individual Output over Context -> Low Impact Weight
# A5: Preferred Wicket Volume over Rarity -> Zero/Low Rarity Weight

W_BATTING = 0.45
W_BOWLING = 0.45
W_IMPACT = 0.05
W_ALL_ROUND = 0.05

print("Calculating QuwrofScore V7 (RLHF Engine)...")
scores_df["quwrof_v7_unscaled"] = (
    W_BATTING * scores_df["batting_score"] +
    W_BOWLING * scores_df["bowling_score"] +
    W_IMPACT * scores_df["impact_score"] +
    W_ALL_ROUND * scores_df["all_round_bonus"]
)

# Scale to 99.5
max_val = scores_df["quwrof_v7_unscaled"].max()
scores_df["quwrof_v7"] = (scores_df["quwrof_v7_unscaled"] / max_val) * 99.5
scores_df["quwrof_v7"] = scores_df["quwrof_v7"].round(2)

out_df = scores_df.sort_values("quwrof_v7", ascending=False).reset_index(drop=True)

print("\n--- THE RLHF LEADERBOARD (V7) ---")
print(out_df[["player_name", "season", "batting_score", "bowling_score", "impact_score", "quwrof_v7"]].head(20).to_string(index=False))

output_path = data_dir / "quwrof_v7_scores.csv"
out_df.to_csv(output_path, index=False)
print(f"\nRLHF V7 scores saved to {output_path}")
