import pandas as pd
import numpy as np

print("Reading enriched_bbb.csv...")
df = pd.read_csv('d:/ipl-rating/enriched_bbb.csv')

print(f"Total rows: {len(df)}")
print("Seasons:", df['season'].unique())
print("Competitions:", df['comp_name'].value_counts())

# Check player names
print("\nSample striker names:", df['striker_name'].dropna().unique()[:10])
print("Sample bowler names:", df['bowler_name'].dropna().unique()[:10])
