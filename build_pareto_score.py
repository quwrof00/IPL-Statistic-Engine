import pandas as pd
import numpy as np
from scipy.stats import rankdata
from pathlib import Path

print("Loading objective scores...")
scores_df = pd.read_csv("d:/ipl-rating/ipl/data/quwrof_scores.csv")

# The 4 axes representing our objectives
axes = ["batting_score", "bowling_score", "all_round_bonus", "impact_score"]
X = scores_df[axes].values

N = len(X)
print(f"Running Fast Non-Dominated Sort on {N} seasons...")

# Vectorized dominance check
# diff[i, j, :] = X[i, :] - X[j, :]
diff = X[:, None, :] - X[None, :, :]

# i dominates j if i >= j in all axes and i > j in at least one axis
dominates = np.logical_and(
    np.all(diff >= 0, axis=2),
    np.any(diff > 0, axis=2)
)

# Initialize fronts
domination_counts = np.sum(dominates, axis=0) # Number of players that dominate j
dominated_lists = [np.where(dominates[i])[0].tolist() for i in range(N)] # List of players that i dominates

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

print(f"Found {len(fronts)} Pareto Fronts. Calculating Crowding Distance...")

crowding_distance = np.zeros(N)

for front in fronts:
    l = len(front)
    if l <= 2:
        for idx in front:
            crowding_distance[idx] = np.inf
        continue
    
    # Initialize distances for this front
    distances = np.zeros(l)
    front_array = np.array(front)
    
    for m in range(4): # For each axis
        axis_vals = X[front_array, m]
        sorted_indices = np.argsort(axis_vals)
        
        # Max and min of the front for this axis
        m_min = axis_vals[sorted_indices[0]]
        m_max = axis_vals[sorted_indices[-1]]
        
        # Set boundaries to infinity
        distances[sorted_indices[0]] = np.inf
        distances[sorted_indices[-1]] = np.inf
        
        if m_max == m_min:
            continue
            
        # Add normalized distance
        for k in range(1, l - 1):
            distances[sorted_indices[k]] += (axis_vals[sorted_indices[k+1]] - axis_vals[sorted_indices[k-1]]) / (m_max - m_min)
            
    for idx_in_front, player_idx in enumerate(front_array):
        crowding_distance[player_idx] = distances[idx_in_front]

scores_df["pareto_front"] = rank
scores_df["crowding_distance"] = crowding_distance

print("Applying Unbiased Tie-Breaker and Scaling...")
# Tie-breaker for infinities: Euclidean norm of the 4 axes
# Completely unbiased, doesn't rely on human weights
scores_df["tie_breaker"] = np.linalg.norm(X, axis=1)

# Sort logic: Front (ascending), Crowding Distance (descending), Tie-breaker (descending)
scores_df = scores_df.sort_values(
    by=["pareto_front", "crowding_distance", "tie_breaker"], 
    ascending=[True, False, False]
).reset_index(drop=True)

N_total = len(scores_df)
scores_df["quwrof_v4"] = ((N_total - scores_df.index.values) / N_total) * 99.5
scores_df["quwrof_v4"] = scores_df["quwrof_v4"].round(2)

print("\n--- FINAL QUWROFSCORE v4 (Pareto Engine) ---")
final_rankings = scores_df.head(20)
print(final_rankings[["player_name", "season", "batting_score", "bowling_score", "all_round_bonus", "impact_score", "pareto_front", "crowding_distance", "quwrof_v4"]].to_string(index=False))

output_path = Path("d:/ipl-rating/ipl/data/quwrof_v4_scores.csv")
scores_df.to_csv(output_path, index=False)
print(f"\nFinal Pareto v4 scores saved to {output_path}")
