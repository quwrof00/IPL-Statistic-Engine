import pandas as pd
import numpy as np
from scipy.stats import rankdata
from pathlib import Path

print("Loading existing V5 metrics (HVC, PVS, Impact)...")
v5_scores = pd.read_csv("d:/ipl-rating/ipl/data/quwrof_v5_scores.csv")
N = len(v5_scores)

print("Layer 1: Dominance (PVS Percentile)")
v5_scores["dominance_percentile"] = (rankdata(v5_scores["pvs"]) / N) * 100

print("Layer 2: Context & Impact")
# Already loaded as `impact_score`

print("Layer 3: Gated Outlierness (Rarity)")
v5_scores["hvc_percentile"] = (rankdata(v5_scores["hvc"]) / N) * 100

# Square root compression to prevent 50x multipliers for extreme HVC
v5_scores["raw_rarity"] = np.sqrt(v5_scores["hvc_percentile"]) * 10

# The Gatekeeper: Rarity only amplifies already-elite dominance
v5_scores["rarity_score"] = np.where(
    v5_scores["dominance_percentile"] >= 85,
    v5_scores["raw_rarity"],
    0.0
)

print("Synthesizing Final QuwrofScore...")
# The Final Equation
v5_scores["quwrof_final_unscaled"] = (
    0.55 * v5_scores["dominance_percentile"] +
    0.30 * v5_scores["impact_score"] +
    0.15 * v5_scores["rarity_score"]
)

max_score = v5_scores["quwrof_final_unscaled"].max()
v5_scores["quwrof_final"] = (v5_scores["quwrof_final_unscaled"] / max_score) * 99.5
v5_scores["quwrof_final"] = v5_scores["quwrof_final"].round(2)

print("\n--- THE ULTIMATE GREATEST IPL SEASONS (FINAL SCORE) ---")
final_df = v5_scores.sort_values("quwrof_final", ascending=False).reset_index(drop=True)
print(final_df[["player_name", "season", "dominance_percentile", "impact_score", "rarity_score", "quwrof_final"]].head(20).round(1).to_string(index=False))

output_path = Path("d:/ipl-rating/ipl/data/quwrof_final_scores.csv")
final_df.to_csv(output_path, index=False)
print(f"\nThe definitive IPL ratings have been saved to {output_path}")
