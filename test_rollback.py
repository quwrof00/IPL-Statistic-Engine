import pandas as pd
import numpy as np

df = pd.read_parquet('ipl/data/player_season_stats.parquet')
df_scores = pd.read_csv('ipl/data/quwrof_v11_scores.csv')

# Load the base stats needed for the original formula
df = df.merge(df_scores[['player_name', 'season', 'rae', 'expected_runs', 'z_econ', 'z_bowl_avg', 'smart_wickets', 'smart_pp_wickets', 'smart_death_wickets', 'smart_playoff_wickets', 'z_death_econ', 'z_pp_econ', 'runs_per_wicket']], on=['player_name', 'season'])

# 1. BATTING: RAE only
df['bat_base'] = df['runs'].fillna(0) + df['rae']

# Need batting impacts (recreate them)
df["bat_chase_impact"] = df["runs_in_chases"].fillna(0) * (df["avg_rrr_faced"].fillna(8.0) / 8.0)
df["bat_playoff_impact"] = df["playoff_runs"].fillna(0) * 2.0
df["raw_bat"] = df["bat_base"] + df["bat_chase_impact"] + df["bat_playoff_impact"]

bat_mask = (df["balls_faced"] >= 30) | (df["innings_batted"] >= 8)
df.loc[bat_mask, "bat_percentile"] = df.loc[bat_mask, "raw_bat"].rank(pct=True) * 100
df["bat_percentile"] = df["bat_percentile"].fillna(0)

# 2. BOWLING: Revert to Z-Scores (No Empirical Wickets)
df["bowl_death_impact"] = df["smart_death_wickets"].fillna(0) * df["runs_per_wicket"] * np.maximum(0, df["z_death_econ"] + 1)
df["bowl_pp_impact"] = df["smart_pp_wickets"].fillna(0) * df["runs_per_wicket"] * np.maximum(0, df["z_pp_econ"] + 1)
df["bowl_playoff_impact"] = df["smart_playoff_wickets"].fillna(0) * (df["runs_per_wicket"] * 2.0)

df["bowl_base"] = df["smart_wickets"].fillna(0) * df["runs_per_wicket"] * (np.maximum(0, df["z_econ"] + 1) + np.maximum(0, df["z_bowl_avg"] + 1))
df["raw_bowl"] = df["bowl_base"] + df["bowl_death_impact"] + df["bowl_pp_impact"] + df["bowl_playoff_impact"]

bowl_mask = (df["balls_bowled"] >= 30) | (df["innings_bowled"] >= 8)
df.loc[bowl_mask, "bowl_percentile"] = df.loc[bowl_mask, "raw_bowl"].rank(pct=True) * 100
df["bowl_percentile"] = df["bowl_percentile"].fillna(0)

# 3. OLD ALL-ROUNDER FORMULA
df["max_pct"] = df[["bat_percentile", "bowl_percentile"]].max(axis=1)
df["min_pct"] = df[["bat_percentile", "bowl_percentile"]].min(axis=1)

bat_confidence = (df["balls_faced"].fillna(0) / 120).clip(upper=1.0) ** 2.0
bowl_confidence = (df["balls_bowled"].fillna(0) / 120).clip(upper=1.0) ** 2.0
ar_confidence = np.minimum(bat_confidence, bowl_confidence)

raw_boost = ((df["min_pct"] / 100) ** 2) * 5
df["v11_raw"] = df["max_pct"] + (raw_boost * ar_confidence)

max_v11 = df["v11_raw"].max()
df["quwrof_v11"] = (df["v11_raw"] / max_v11) * 99.5

print("--- REVERTED TOP 20 ---")
print(df.sort_values("quwrof_v11", ascending=False)[["player_name", "season", "quwrof_v11", "bat_percentile", "bowl_percentile"]].head(20).to_string(index=False))
