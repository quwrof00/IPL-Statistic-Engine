import pandas as pd
df = pd.read_parquet('ipl/data/player_season_stats.parquet')
df_scores = pd.read_csv('ipl/data/quwrof_v11_scores.csv')
df = df.merge(df_scores[['player_name', 'season', 'rae', 'bat_percentile', 'bat_chase_impact', 'bat_playoff_impact']], on=['player_name', 'season'])

# Expected runs = runs - RAE (since RAE = runs - expected)
df['expected'] = df['runs'] - df['rae']

# Avoid division by zero
df['E'] = df['runs'] / df['expected'].replace(0, 1).clip(lower=1)

for exponent in [1, 2, 2.5, 3]:
    df[f'bat_base_E{exponent}'] = df['runs'] * (df['E'] ** exponent)
    df[f'raw_bat_E{exponent}'] = df[f'bat_base_E{exponent}'] + df['bat_chase_impact'] + df['bat_playoff_impact']
    
    bat_mask = (df["balls_faced"] >= 30) | (df["innings_batted"] >= 8)
    df.loc[bat_mask, f'pct_E{exponent}'] = df.loc[bat_mask, f'raw_bat_E{exponent}'].rank(pct=True) * 100

print("--- TOP 10 WITH E^2 ---")
print(df.sort_values('pct_E2', ascending=False)[['player_name', 'season', 'pct_E2', 'runs', 'expected', 'E']].head(10).to_string(index=False))

print("\n--- TOP 10 WITH E^2.5 ---")
print(df.sort_values('pct_E2.5', ascending=False)[['player_name', 'season', 'pct_E2.5', 'runs', 'expected', 'E']].head(10).to_string(index=False))

print("\n--- ANDRE RUSSELL 2019 ---")
print(df[(df['player_name'] == 'AD Russell') & (df['season'] == '2019')][['player_name', 'season', 'bat_percentile', 'pct_E1', 'pct_E2', 'pct_E2.5', 'pct_E3', 'E', 'runs']].to_string(index=False))
