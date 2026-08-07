import pandas as pd

df = pd.read_csv('ipl/data/quwrof_v11_scores.csv')

# 1. Normalize based on the 99.9th percentile to drop freak outliers
bat_mask = df['raw_bat'] > 0
bowl_mask = df['raw_bowl'] > 0

bat_999 = df.loc[bat_mask, 'raw_bat'].quantile(0.999)
bowl_999 = df.loc[bowl_mask, 'raw_bowl'].quantile(0.999)

df['bat_value'] = (df['raw_bat'].fillna(0) / bat_999) * 100
df['bowl_value'] = (df['raw_bowl'].fillna(0) / bowl_999) * 100

# Cap at 100 just in case
df['bat_value'] = df['bat_value'].clip(upper=100)
df['bowl_value'] = df['bowl_value'].clip(upper=100)

# 2. Add them natively
df['total_value'] = df['bat_value'] + df['bowl_value']

# 3. Percentile Rank
df['new_v11'] = (df['total_value'].rank(pct=True) * 100).round(2)

print("--- NEW TOP 20 ---")
print(df.sort_values('total_value', ascending=False)[['player_name', 'season', 'new_v11', 'total_value', 'bat_value', 'bowl_value']].head(20).to_string(index=False))

print("\n--- NOTABLE SPECIALISTS ---")
print(df[df['player_name'].isin(['V Kohli', 'JJ Bumrah', 'DA Warner'])].sort_values('total_value', ascending=False)[['player_name', 'season', 'new_v11', 'total_value', 'bat_value', 'bowl_value']].head(5).to_string(index=False))
