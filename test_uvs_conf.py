import pandas as pd
import numpy as np

df = pd.read_parquet('ipl/data/player_season_stats.parquet')
df_scores = pd.read_csv('ipl/data/quwrof_v11_scores.csv')
df = df.merge(df_scores[['player_name', 'season', 'raw_bat', 'raw_bowl']], on=['player_name', 'season'])

# 1. Normalize based on the 99.9th percentile
bat_mask = df['raw_bat'] > 0
bowl_mask = df['raw_bowl'] > 0

bat_999 = df.loc[bat_mask, 'raw_bat'].quantile(0.999)
bowl_999 = df.loc[bowl_mask, 'raw_bowl'].quantile(0.999)

df['bat_value'] = (df['raw_bat'].fillna(0) / bat_999) * 100
df['bowl_value'] = (df['raw_bowl'].fillna(0) / bowl_999) * 100

df['bat_value'] = df['bat_value'].clip(upper=100)
df['bowl_value'] = df['bowl_value'].clip(upper=100)

# 2. Confidence Scaling (The Anti-Exploit)
df['bat_confidence'] = (df['balls_faced'].fillna(0) / 120).clip(upper=1.0) ** 2.0
df['bowl_confidence'] = (df['balls_bowled'].fillna(0) / 120).clip(upper=1.0) ** 2.0

df['bat_value_conf'] = df['bat_value'] * df['bat_confidence']
df['bowl_value_conf'] = df['bowl_value'] * df['bowl_confidence']

# 3. Total Value
df['total_value'] = df['bat_value_conf'] + df['bowl_value_conf']

# 4. Percentile Rank vs Linear Scale
df['new_v11_percentile'] = (df['total_value'].rank(pct=True) * 100).round(2)

max_val = df['total_value'].quantile(0.999)
df['new_v11_linear'] = ((df['total_value'] / max_val) * 100).clip(upper=100).round(2)

print("--- NEW TOP 20 ---")
print(df.sort_values('total_value', ascending=False)[['player_name', 'season', 'new_v11_percentile', 'new_v11_linear', 'total_value', 'bat_value_conf', 'bowl_value_conf']].head(20).to_string(index=False))

print("\n--- NOTABLE PLAYERS ---")
print(df[df['player_name'].isin(['V Kohli', 'JJ Bumrah', 'DA Warner', 'K Rabada', 'B Kumar'])].sort_values('total_value', ascending=False)[['player_name', 'season', 'new_v11', 'total_value', 'bat_value_conf', 'bowl_value_conf']].head(5).to_string(index=False))
