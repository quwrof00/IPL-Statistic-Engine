import pandas as pd
import numpy as np
from scipy.stats import rankdata
from pathlib import Path
import gc

print("Loading objective scores...")
scores_df = pd.read_csv("d:/ipl-rating/ipl/data/quwrof_scores.csv")

# The 4 axes representing our objectives
axes = ["batting_score", "bowling_score", "all_round_bonus", "impact_score"]
X = scores_df[axes].values

N = len(X)
print(f"Running Fast Non-Dominated Sort on {N} seasons...")

# Vectorized dominance check
diff = X[:, None, :] - X[None, :, :]

# i dominates j if i >= j in all axes and i > j in at least one axis
dominates = np.logical_and(
    np.all(diff >= 0, axis=2),
    np.any(diff > 0, axis=2)
)

domination_counts = np.sum(dominates, axis=0)
dominated_lists = [np.where(dominates[i])[0].tolist() for i in range(N)]

current_front = np.where(domination_counts == 0)[0].tolist()
rank = np.zeros(N, dtype=int)

fronts = []
front_idx = 1
while current_front:
    fronts.append(current_front)
    next_front = []
    for i in current_front:
        rank[i] = front_idx
        for j in dominated_lists[i]:
            domination_counts[j] -= 1
            if domination_counts[j] == 0:
                next_front.append(j)
    current_front = next_front
    front_idx += 1

print(f"Found {len(fronts)} Pareto Fronts.")

print("Calculating Monte Carlo Hypervolume Contribution (HVC) per front...")
hvc = np.zeros(N)
N_MC_POINTS = 1_000_000
CHUNK_SIZE = 100_000

# To prevent calculating HVC for heavily dominated low-tier fronts that cover almost no volume, 
# we'll compute HVC for all fronts. It takes just a few seconds.
for f_idx, front in enumerate(fronts):
    if len(front) <= 1:
        # If only 1 player in the front, their HVC is 100% of the volume they cover.
        # But HVC is used to rank WITHIN a front, so if size is 1, HVC doesn't matter.
        continue
    
    front_array = np.array(front)
    front_scores = X[front_array] # Shape: (k, 4)
    
    front_hvc = np.zeros(len(front))
    
    for _ in range(N_MC_POINTS // CHUNK_SIZE):
        # Generate random imaginary seasons
        # Since all axes are roughly bounded 0-100 (some maxes might be slightly higher or lower)
        # we'll sample up to the absolute max in the dataset + 1
        max_bounds = np.max(X, axis=0) + 1
        mc_points = np.random.uniform(0, max_bounds, size=(CHUNK_SIZE, 4))
        
        # is_dominated shape: (CHUNK_SIZE, k)
        is_dominated = np.all(mc_points[:, None, :] <= front_scores[None, :, :], axis=2)
        
        sum_dom = is_dominated.sum(axis=1)
        exclusive_mask = (sum_dom == 1)
        
        if np.any(exclusive_mask):
            exclusive_dominations = is_dominated[exclusive_mask]
            # Count how many points each player exclusively dominated
            front_hvc += exclusive_dominations.sum(axis=0)
            
    # Store normalized HVC
    for idx_in_front, player_idx in enumerate(front_array):
        hvc[player_idx] = front_hvc[idx_in_front] / N_MC_POINTS
        
    # Free memory
    gc.collect()

scores_df["pareto_front"] = rank
scores_df["hvc"] = hvc

print("Calculating Pareto Value Score (L2 Norm)...")
scores_df["pvs"] = np.linalg.norm(X, axis=1)

print("Scaling and saving...")
scores_df = scores_df.sort_values(
    by=["pareto_front", "hvc", "pvs"], 
    ascending=[True, False, False]
).reset_index(drop=True)

N_total = len(scores_df)
scores_df["quwrof_v5"] = ((N_total - scores_df.index.values) / N_total) * 99.5
scores_df["quwrof_v5"] = scores_df["quwrof_v5"].round(2)

print("\n--- FINAL QUWROFSCORE v5 (Hypervolume Engine) ---")
final_rankings = scores_df.head(20)
print(final_rankings[["player_name", "season", "batting_score", "bowling_score", "all_round_bonus", "impact_score", "pareto_front", "hvc", "pvs", "quwrof_v5"]].to_string(index=False))

output_path = Path("d:/ipl-rating/ipl/data/quwrof_v5_scores.csv")
scores_df.to_csv(output_path, index=False)
print(f"\nFinal Hypervolume v5 scores saved to {output_path}")
