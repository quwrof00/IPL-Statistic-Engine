import pandas as pd
import numpy as np

df = pd.read_parquet('ipl/data/player_season_stats.parquet')
df_scores = pd.read_csv('ipl/data/quwrof_v11_scores.csv')
df = df.merge(df_scores[['player_name', 'season', 'rae', 'bat_chase_impact', 'bat_playoff_impact', 'raw_bowl']], on=['player_name', 'season'])

df['expected_runs'] = df['runs'].fillna(0) - df['rae']
df['E'] = df['runs'].fillna(0) / df['expected_runs'].replace(0, 1).clip(lower=1)
df['E'] = np.where(df['runs'].fillna(0) == 0, 0, df['E'])

# Test E^2
df['bat_base'] = df['runs'].fillna(0) * (df['E'] ** 2.0)
df['raw_bat'] = df['bat_base'] + df['bat_chase_impact'] + df['bat_playoff_impact']

bat_mask = df['raw_bat'] > 0
bowl_mask = df['raw_bowl'] > 0

bat_999 = df.loc[bat_mask, 'raw_bat'].quantile(0.999)
bowl_999 = df.loc[bowl_mask, 'raw_bowl'].quantile(0.999)

df['bat_value'] = (df['raw_bat'].fillna(0) / bat_999) * 100
df['bowl_value'] = (df['raw_bowl'].fillna(0) / bowl_999) * 100
df['bat_value'] = df['bat_value'].clip(upper=100)
df['bowl_value'] = df['bowl_value'].clip(upper=100)

df['bat_confidence'] = (df['balls_faced'].fillna(0) / 120).clip(upper=1.0) ** 2.0
df['bowl_confidence'] = (df['balls_bowled'].fillna(0) / 120).clip(upper=1.0) ** 2.0

df['total_value'] = (df['bat_value'] * df['bat_confidence']) + (df['bowl_value'] * df['bowl_confidence'])
df['final_v11'] = (df['total_value'].rank(pct=True) * 100).round(2)

print("--- NEW TOP 20 WITH E^2 ---")
print(df.sort_values('total_value', ascending=False)[['player_name', 'season', 'final_v11', 'total_value', 'runs', 'E']].head(20).to_string(index=False))

print("\n--- NOTABLE PLAYERS ---")
print(df[df['player_name'].isin(['V Kohli', 'AD Russell', 'YK Pathan', 'CH Gayle'])].sort_values('total_value', ascending=False)[['player_name', 'season', 'final_v11', 'total_value', 'runs', 'E']].head(6).to_string(index=False))
