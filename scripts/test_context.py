import pandas as pd
import numpy as np

df = pd.read_parquet('ipl/data/player_season_stats.parquet')
df_scores = pd.read_csv('ipl/data/quwrof_v11_scores.csv')

df = df.merge(df_scores[['player_name', 'season', 'rae', 'expected_runs', 'z_econ', 'z_bowl_avg', 'smart_wickets', 'smart_pp_wickets', 'smart_death_wickets', 'smart_playoff_wickets', 'z_death_econ', 'z_pp_econ', 'runs_per_wicket', 'loo_overall_wkt_rate', 'loo_pp_wkt_rate', 'loo_mid_wkt_rate', 'loo_death_wkt_rate', 'z_death_sr']], on=['player_name', 'season'])

df['bat_base'] = df['runs'].fillna(0) + df['rae']

# Tune Context Weights!
df["capped_rrr_ratio"] = (df["avg_rrr_faced"].fillna(8.0) / 8.0).clip(upper=1.5)
df["bat_chase_impact"] = df["runs_in_chases"].fillna(0) * (df["capped_rrr_ratio"] - 1.0).clip(lower=0) # Only bonus for >8 RRR
df["bat_playoff_impact"] = df["playoff_runs"].fillna(0) * 0.5

# Death impact: scale by z_death_sr gently
df["bat_death_impact"] = df["runs_in_death"].fillna(0) * np.maximum(0, df["z_death_sr"] * 0.5)

df["raw_bat"] = df["bat_base"] + df["bat_chase_impact"] + df["bat_playoff_impact"] + df["bat_death_impact"]

bat_mask = (df["balls_faced"] >= 30) | (df["innings_batted"] >= 8)
df.loc[bat_mask, "bat_percentile"] = df.loc[bat_mask, "raw_bat"].rank(pct=True) * 100
df["bat_percentile"] = df["bat_percentile"].fillna(0)

# BOWLING
df["empirical_pp_wickets"] = df["smart_pp_wickets"] * (df["loo_overall_wkt_rate"] / df["loo_pp_wkt_rate"].replace(0, 1))
df["empirical_mid_wickets"] = df["smart_mid_wickets"] * (df["loo_overall_wkt_rate"] / df["loo_mid_wkt_rate"].replace(0, 1))
df["empirical_death_wickets"] = df["smart_death_wickets"] * (df["loo_overall_wkt_rate"] / df["loo_death_wkt_rate"].replace(0, 1))
df["empirical_wickets"] = df["empirical_pp_wickets"] + df["empirical_mid_wickets"] + df["empirical_death_wickets"]

df["bowl_death_impact"] = df["empirical_death_wickets"] * df["runs_per_wicket"] * np.maximum(0, df["z_death_econ"] * 0.5)
df["bowl_pp_impact"] = df["empirical_pp_wickets"] * df["runs_per_wicket"] * np.maximum(0, df["z_pp_econ"] * 0.5)
df["bowl_playoff_impact"] = df["smart_playoff_wickets"] * (df["runs_per_wicket"] * 0.5)

df["bowl_base"] = df["empirical_wickets"] * df["runs_per_wicket"] * (np.maximum(0, df["z_econ"] + 1) + np.maximum(0, df["z_bowl_avg"] + 1))
df["raw_bowl"] = df["bowl_base"] + df["bowl_death_impact"] + df["bowl_pp_impact"] + df["bowl_playoff_impact"]

bowl_mask = (df["balls_bowled"] >= 30) | (df["innings_bowled"] >= 8)
df.loc[bowl_mask, "bowl_percentile"] = df.loc[bowl_mask, "raw_bowl"].rank(pct=True) * 100
df["bowl_percentile"] = df["bowl_percentile"].fillna(0)

df["max_pct"] = df[["bat_percentile", "bowl_percentile"]].max(axis=1)
df["min_pct"] = df[["bat_percentile", "bowl_percentile"]].min(axis=1)

bat_confidence = (df["balls_faced"].fillna(0) / 120).clip(upper=1.0) ** 2.0
bowl_confidence = (df["balls_bowled"].fillna(0) / 120).clip(upper=1.0) ** 2.0
ar_confidence = np.minimum(bat_confidence, bowl_confidence)

raw_boost = ((df["min_pct"] / 100) ** 2) * 5
df["v11_raw"] = df["max_pct"] + (raw_boost * ar_confidence)

max_v11 = df["v11_raw"].max()
df["quwrof_v11"] = (df["v11_raw"] / max_v11) * 99.5

print("--- NEW TOP 20 ---")
print(df.sort_values("quwrof_v11", ascending=False)[["player_name", "season", "quwrof_v11", "bat_percentile", "bowl_percentile"]].head(20).to_string(index=False))

print("\n--- RINKU SINGH ---")
print(df[(df.player_name == 'RK Singh') & (df.season == '2023')][["player_name", "season", "quwrof_v11", "bat_percentile", "raw_bat", "bat_chase_impact", "bat_playoff_impact", "bat_death_impact", "rae"]].to_string(index=False))

print("\n--- ANDRE RUSSELL 2019 ---")
print(df[(df.player_name == 'AD Russell') & (df.season == '2019')][["player_name", "season", "quwrof_v11", "bat_percentile", "raw_bat", "bat_chase_impact", "bat_playoff_impact", "bat_death_impact", "rae"]].to_string(index=False))
