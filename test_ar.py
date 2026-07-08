import pandas as pd
import numpy as np

df = pd.read_csv('ipl/data/quwrof_v11_scores.csv')

df["max_pct"] = df[["bat_percentile", "bowl_percentile"]].max(axis=1)
df["min_pct"] = df[["bat_percentile", "bowl_percentile"]].min(axis=1)

raw_boost = (df["min_pct"] / 100) ** 2
# Assume full confidence for test
df["v11_new"] = df["max_pct"] + ((99.99 - df["max_pct"]) * raw_boost)

print("--- NEW TOP 20 ---")
print(df.sort_values("v11_new", ascending=False)[["player_name", "season", "bat_percentile", "bowl_percentile", "v11_new"]].head(20).to_string(index=False))
