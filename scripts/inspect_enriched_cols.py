import pandas as pd

df = pd.read_csv('d:/ipl-rating/enriched_bbb.csv', nrows=5)
print("Columns count:", len(df.columns))
print("Columns:", df.columns.tolist())
