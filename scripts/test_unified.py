import pandas as pd

df = pd.read_csv('ipl/data/quwrof_v11_scores.csv')

max_bat = df['raw_bat'].max()
max_bowl = df['raw_bowl'].max()

df['bat_value'] = (df['raw_bat'].fillna(0) / max_bat) * 100
df['bowl_value'] = (df['raw_bowl'].fillna(0) / max_bowl) * 100

df['total_value'] = df['bat_value'] + df['bowl_value']
df['new_v11'] = df['total_value'].rank(pct=True) * 100

print("--- TOP 20 UNIFIED VALUE SCORE ---")
print(df.sort_values('total_value', ascending=False)[['player_name', 'season', 'new_v11', 'total_value', 'bat_value', 'bowl_value']].head(20).to_string(index=False))
