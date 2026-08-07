import pandas as pd
df = pd.read_csv('ipl/data/quwrof_v11_scores.csv')

# Look at the max values for raw_bat and raw_bowl to see if they are on the same scale
print("Max raw_bat:", df['raw_bat'].max())
print("Max raw_bowl:", df['raw_bowl'].max())

# Add them together
df['total_value'] = df['raw_bat'].fillna(0) + df['raw_bowl'].fillna(0)

# Rank by total value
df['total_percentile'] = df['total_value'].rank(pct=True) * 100

print("\n--- TOP 20 BY TOTAL VALUE (RAW_BAT + RAW_BOWL) ---")
print(df.sort_values('total_value', ascending=False)[['player_name', 'season', 'total_value', 'raw_bat', 'raw_bowl']].head(20).to_string(index=False))
