import pandas as pd
from pathlib import Path

data_dir = Path("d:/ipl-rating/ipl/data")

print("Loading datasets...")
# Base dataset from Final (V6), which already has V1 (quwrof_score), V5 (quwrof_v5), and primary_team
df_final = pd.read_csv(data_dir / "quwrof_final_scores.csv")

# Rename V1 to be consistent
df_final = df_final.rename(columns={"quwrof_score": "quwrof_v1"})

# Load other versions to merge their final scores
df_v2 = pd.read_csv(data_dir / "quwrof_v2_scores.csv")[["player_name", "season", "quwrof_v2"]]
df_v3 = pd.read_csv(data_dir / "quwrof_v3_scores.csv")[["player_name", "season", "quwrof_v3"]]
df_v4 = pd.read_csv(data_dir / "quwrof_v4_scores.csv")[["player_name", "season", "quwrof_v4"]]
df_v7 = pd.read_csv(data_dir / "quwrof_v7_scores.csv")[["player_name", "season", "quwrof_v7"]]
df_v8 = pd.read_csv(data_dir / "quwrof_v8_scores.csv")[["player_name", "season", "quwrof_v8", "z_sr", "z_econ"]]
df_v9 = pd.read_csv(data_dir / "quwrof_v9_scores.csv")[["player_name", "season", "quwrof_v9", "pca_efficiency", "volume_multiplier"]]
df_v10 = pd.read_csv(data_dir / "quwrof_v10_scores.csv")[["player_name", "season", "quwrof_v10", "scaled_batting", "scaled_bowling"]]
df_v11 = pd.read_csv(data_dir / "quwrof_v11_scores.csv")[["player_name", "season", "quwrof_v11", "bat_percentile", "bowl_percentile", "bat_base", "bat_chase_impact", "bat_playoff_impact", "raw_bat", "rae", "smart_wickets", "empirical_wickets", "bowl_base", "bowl_pp_impact", "bowl_death_impact", "bowl_playoff_impact", "bowl_pressure_impact", "raw_bowl"]]
df_v12 = pd.read_csv(data_dir / "quwrof_v12_scores.csv")[["player_name", "season", "quwrof_v12"]]
df_v13 = pd.read_csv(data_dir / "quwrof_v13_scores.csv")[["player_name", "season", "quwrof_v13", "bat_z", "bowl_z"]]
df_v14 = pd.read_csv(data_dir / "quwrof_v14_scores.csv")[["player_name", "season", "quwrof_v14", "bat_points", "bowl_points", "v14_percentile", "v14_bat_percentile", "v14_bowl_percentile", "bat_playoff_impact_points", "bowl_playoff_impact_points", "bat_base_points", "bat_chase_impact_points", "bowl_base_points", "bowl_pp_impact_points", "bowl_death_impact_points", "bowl_pressure_impact_points"]]
print("Merging...")
merged = df_final.merge(df_v2, on=["player_name", "season"], how="left")
merged = merged.merge(df_v3, on=["player_name", "season"], how="left")
merged = merged.merge(df_v4, on=["player_name", "season"], how="left")
merged = merged.merge(df_v7, on=["player_name", "season"], how="left")
merged = merged.merge(df_v8, on=["player_name", "season"], how="left")
merged = merged.merge(df_v9, on=["player_name", "season"], how="left")
merged = merged.merge(df_v10, on=["player_name", "season"], how="left")
merged = merged.merge(df_v11, on=["player_name", "season"], how="left")
merged = merged.merge(df_v12, on=["player_name", "season"], how="left")
merged = merged.merge(df_v13, on=["player_name", "season"], how="left")
merged = merged.merge(df_v14, on=["player_name", "season"], how="left")
# Replace NaN with 0 for versions that might have filtered out players (though they shouldn't have)
merged.fillna({
    "quwrof_v1": 0, "quwrof_v2": 0, "quwrof_v3": 0, "quwrof_v4": 0, "quwrof_v5": 0, "quwrof_v7": 0, "quwrof_v8": 0, "quwrof_v9": 0, "quwrof_v10": 0, "quwrof_v11": 0, "quwrof_v12": 0, "quwrof_v13": 0, "quwrof_v14": 0, "quwrof_final": 0,
    "bat_base": 0, "bat_chase_impact": 0, "bat_playoff_impact": 0, "raw_bat": 0, "bowl_base": 0, "bowl_pp_impact": 0, "bowl_death_impact": 0, "bowl_playoff_impact": 0, "bowl_pressure_impact": 0, "raw_bowl": 0,
    "bat_points": 0, "bowl_points": 0, "v14_percentile": 0, "v14_bat_percentile": 0, "v14_bowl_percentile": 0, "bat_playoff_impact_points": 0, "bowl_playoff_impact_points": 0,
    "bat_base_points": 0, "bat_chase_impact_points": 0, "bowl_base_points": 0, "bowl_pp_impact_points": 0, "bowl_death_impact_points": 0, "bowl_pressure_impact_points": 0
}, inplace=True)

# Select relevant columns for frontend to keep JSON size small
columns_to_keep = [
    "player_name", "season", "primary_team",
    "dominance_percentile", "impact_score", "rarity_score",
    "runs", "batting_average", "strike_rate", "wickets", "bowling_average", "economy",
    "z_sr", "z_econ", "pca_efficiency", "volume_multiplier",
    "scaled_batting", "scaled_bowling", "bat_percentile", "bowl_percentile", "bat_z", "bowl_z", "bat_points", "bowl_points", "v14_percentile", "v14_bat_percentile", "v14_bowl_percentile", "bat_playoff_impact_points", "bowl_playoff_impact_points", "bat_base_points", "bat_chase_impact_points", "bowl_base_points", "bowl_pp_impact_points", "bowl_death_impact_points", "bowl_pressure_impact_points",
    "bat_base", "bat_chase_impact", "bat_playoff_impact", "raw_bat", "rae", 
    "smart_wickets", "empirical_wickets", "bowl_base", "bowl_pp_impact", "bowl_death_impact", "bowl_playoff_impact", "bowl_pressure_impact", "raw_bowl",
    "quwrof_v1", "quwrof_v2", "quwrof_v3", "quwrof_v4", "quwrof_v5", "quwrof_v7", "quwrof_v8", "quwrof_v9", "quwrof_v10", "quwrof_v11", "quwrof_v12", "quwrof_v13", "quwrof_v14", "quwrof_final"
]

merged = merged[columns_to_keep]

team_mapping = {
    'Rising Pune Supergiant': 'Rising Pune Supergiants',
    'Royal Challengers Bangalore': 'Royal Challengers Bengaluru',
    'Delhi Daredevils': 'Delhi Capitals',
    'Kings XI Punjab': 'Punjab Kings'
}
merged['primary_team'] = merged['primary_team'].replace(team_mapping)

out_path = Path("d:/ipl-rating/ipl/public/data_v2.json")
merged.to_json(out_path, orient="records")
print(f"Data prepared and saved to {out_path}")
