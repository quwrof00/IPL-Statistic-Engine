import pandas as pd
import numpy as np
from pathlib import Path

data_dir = Path("d:/ipl-rating/ipl/data")

print("Loading raw Parquet dataset for V11 Contextual Percentile rebuild...")
df = pd.read_parquet(data_dir / "player_season_stats.parquet")

# 1. Z-SCORE CONTEXT
print("Calculating Contextual Z-Scores...")

bat_season_stats = df[df["balls_faced"].fillna(0) > 0].groupby("season").agg({
    "strike_rate": ["mean", "std"],
    "batting_average": ["mean", "std"]
})
bat_season_stats.columns = ['_'.join(col).strip() for col in bat_season_stats.columns.values]

bat_death_stats = df[df["balls_faced_death"].fillna(0) > 0].groupby("season").agg({
    "death_SR": ["mean", "std"]
})
bat_death_stats.columns = ['_'.join(col).strip() for col in bat_death_stats.columns.values]

bat_pp_stats = df[df["balls_faced_powerplay"].fillna(0) > 0].groupby("season").agg({
    "powerplay_SR": ["mean", "std"]
})
bat_pp_stats.columns = ['_'.join(col).strip() for col in bat_pp_stats.columns.values]

bowl_season_stats = df[df["balls_bowled"].fillna(0) > 0].groupby("season").agg({
    "economy": ["mean", "std"],
    "bowling_average": ["mean", "std"]
})
bowl_season_stats.columns = ['_'.join(col).strip() for col in bowl_season_stats.columns.values]

bowl_death_stats = df[df["balls_bowled_death"].fillna(0) > 0].groupby("season").agg({
    "death_economy": ["mean", "std"]
})
bowl_death_stats.columns = ['_'.join(col).strip() for col in bowl_death_stats.columns.values]

bowl_pp_stats = df[df["balls_bowled_powerplay"].fillna(0) > 0].groupby("season").agg({
    "powerplay_economy": ["mean", "std"]
})
bowl_pp_stats.columns = ['_'.join(col).strip() for col in bowl_pp_stats.columns.values]

overall_season_stats = df.groupby("season").agg({
    "runs": ["sum"],
    "wickets": ["sum"]
})
overall_season_stats.columns = ['_'.join(col).strip() for col in overall_season_stats.columns.values]

season_stats = bat_season_stats.join(bat_death_stats).join(bat_pp_stats).join(bowl_season_stats).join(bowl_death_stats).join(bowl_pp_stats).join(overall_season_stats).reset_index()

season_stats["runs_per_wicket"] = (season_stats["runs_sum"] / season_stats["wickets_sum"].replace(0, 1)).clip(lower=15.0)

df = df.merge(season_stats, on="season", how="left")

# Batting Z-Scores
df["z_sr"] = (df["strike_rate"] - df["strike_rate_mean"]) / df["strike_rate_std"].replace(0, 1)
df["z_avg"] = (df["batting_average"] - df["batting_average_mean"]) / df["batting_average_std"].replace(0, 1)
df["z_death_sr"] = (df["death_SR"] - df["death_SR_mean"]) / df["death_SR_std"].replace(0, 1)

# Bowling Z-Scores (Inverted so Positive is better)
df["z_econ"] = (df["economy_mean"] - df["economy"]) / df["economy_std"].replace(0, 1)
df["z_bowl_avg"] = (df["bowling_average_mean"] - df["bowling_average"]) / df["bowling_average_std"].replace(0, 1)
df["z_death_econ"] = (df["death_economy_mean"] - df["death_economy"]) / df["death_economy_std"].replace(0, 1)
df["z_pp_econ"] = (df["powerplay_economy_mean"] - df["powerplay_economy"]) / df["powerplay_economy_std"].replace(0, 1)

context_cols = ["z_sr", "z_avg", "z_death_sr", "z_econ", "z_bowl_avg", "z_death_econ", "z_pp_econ"]
df[context_cols] = df[context_cols].fillna(0).clip(-3, 4)

df.loc[df["balls_faced"].fillna(0) < 30, ["z_sr", "z_avg"]] = 0
df.loc[df["balls_faced_death"].fillna(0) < 18, "z_death_sr"] = 0
df.loc[df["balls_bowled"].fillna(0) < 30, ["z_econ", "z_bowl_avg"]] = 0
df.loc[df["balls_bowled_death"].fillna(0) < 18, "z_death_econ"] = 0
df.loc[df["balls_bowled_powerplay"].fillna(0) < 18, "z_pp_econ"] = 0

# 1.5 EMPIRICAL LEAVE-ONE-OUT (LOO) PHASE EXPECTATIONS
print("Calculating Leave-One-Out (LOO) Empirical Expectations...")
deliveries = pd.read_parquet(data_dir / "deliveries.parquet")
deliveries['is_legal'] = ~(deliveries['is_wide'] | deliveries['is_noball'])
deliveries['is_bowler_wicket'] = deliveries['is_wicket'] & ~deliveries['dismissal_kind'].isin(['run out', 'retired hurt', 'obstructing the field'])
deliveries['is_pp'] = deliveries['over'] < 6
deliveries['is_death'] = deliveries['over'] >= 15
deliveries['is_mid'] = ~deliveries['is_pp'] & ~deliveries['is_death']

# Global Season Phase Totals
global_phase = deliveries.groupby('season').apply(lambda x: pd.Series({
    'g_pp_runs': x[x['is_pp']]['total_runs'].sum(),
    'g_pp_balls': x[x['is_pp']]['is_legal'].sum(),
    'g_pp_wkts': x[x['is_pp']]['is_bowler_wicket'].sum(),
    'g_mid_runs': x[x['is_mid']]['total_runs'].sum(),
    'g_mid_balls': x[x['is_mid']]['is_legal'].sum(),
    'g_mid_wkts': x[x['is_mid']]['is_bowler_wicket'].sum(),
    'g_death_runs': x[x['is_death']]['total_runs'].sum(),
    'g_death_balls': x[x['is_death']]['is_legal'].sum(),
    'g_death_wkts': x[x['is_death']]['is_bowler_wicket'].sum(),
    'g_overall_runs': x['total_runs'].sum(),
    'g_overall_balls': x['is_legal'].sum(),
    'g_overall_wkts': x['is_bowler_wicket'].sum()
}), include_groups=False).reset_index()

global_phase['season_rrr'] = (global_phase['g_overall_runs'] / global_phase['g_overall_balls'].replace(0, 1)) * 6.0

# Player Batting Phase Totals
player_bat = deliveries.groupby(['season', 'batter']).apply(lambda x: pd.Series({
    'p_pp_runs': x[x['is_pp']]['total_runs'].sum(),
    'p_pp_balls': x[x['is_pp']]['is_legal'].sum(),
    'p_mid_runs': x[x['is_mid']]['total_runs'].sum(),
    'p_mid_balls': x[x['is_mid']]['is_legal'].sum(),
    'p_death_runs': x[x['is_death']]['total_runs'].sum(),
    'p_death_balls': x[x['is_death']]['is_legal'].sum(),
}), include_groups=False).reset_index().rename(columns={'batter': 'player_name'})

# Join and calculate Batting LOO
bat_loo = pd.merge(player_bat, global_phase, on='season', how='left')
bat_loo['loo_pp_sr'] = ((bat_loo['g_pp_runs'] - bat_loo['p_pp_runs']) / (bat_loo['g_pp_balls'] - bat_loo['p_pp_balls']).replace(0, 1)) * 100
bat_loo['loo_mid_sr'] = ((bat_loo['g_mid_runs'] - bat_loo['p_mid_runs']) / (bat_loo['g_mid_balls'] - bat_loo['p_mid_balls']).replace(0, 1)) * 100
bat_loo['loo_death_sr'] = ((bat_loo['g_death_runs'] - bat_loo['p_death_runs']) / (bat_loo['g_death_balls'] - bat_loo['p_death_balls']).replace(0, 1)) * 100

# Merge Batting LOO into main df
df = pd.merge(df, bat_loo[['season', 'player_name', 'loo_pp_sr', 'loo_mid_sr', 'loo_death_sr']], on=['season', 'player_name'], how='left')
# For players who didn't bat, we fill with global average (which is close enough since they didn't bat)
global_phase_idx = global_phase.set_index('season')
df['loo_pp_sr'] = df['loo_pp_sr'].fillna(df['season'].map(global_phase_idx['g_pp_runs'] / global_phase_idx['g_pp_balls'] * 100)).fillna(120)
df['loo_mid_sr'] = df['loo_mid_sr'].fillna(df['season'].map(global_phase_idx['g_mid_runs'] / global_phase_idx['g_mid_balls'] * 100)).fillna(130)
df['loo_death_sr'] = df['loo_death_sr'].fillna(df['season'].map(global_phase_idx['g_death_runs'] / global_phase_idx['g_death_balls'] * 100)).fillna(150)

# Player Bowling Phase Totals
player_bowl = deliveries.groupby(['season', 'bowler']).apply(lambda x: pd.Series({
    'p_pp_wkts': x[x['is_pp']]['is_bowler_wicket'].sum(),
    'p_pp_balls_b': x[x['is_pp']]['is_legal'].sum(),
    'p_mid_wkts': x[x['is_mid']]['is_bowler_wicket'].sum(),
    'p_mid_balls_b': x[x['is_mid']]['is_legal'].sum(),
    'p_death_wkts': x[x['is_death']]['is_bowler_wicket'].sum(),
    'p_death_balls_b': x[x['is_death']]['is_legal'].sum(),
    'p_overall_wkts': x['is_bowler_wicket'].sum(),
    'p_overall_balls_b': x['is_legal'].sum()
}), include_groups=False).reset_index().rename(columns={'bowler': 'player_name'})

# Join and calculate Bowling LOO
bowl_loo = pd.merge(player_bowl, global_phase, on='season', how='left')
bowl_loo['loo_pp_wkt_rate'] = (bowl_loo['g_pp_wkts'] - bowl_loo['p_pp_wkts']) / (bowl_loo['g_pp_balls'] - bowl_loo['p_pp_balls_b']).replace(0, 1)
bowl_loo['loo_mid_wkt_rate'] = (bowl_loo['g_mid_wkts'] - bowl_loo['p_mid_wkts']) / (bowl_loo['g_mid_balls'] - bowl_loo['p_mid_balls_b']).replace(0, 1)
bowl_loo['loo_death_wkt_rate'] = (bowl_loo['g_death_wkts'] - bowl_loo['p_death_wkts']) / (bowl_loo['g_death_balls'] - bowl_loo['p_death_balls_b']).replace(0, 1)
bowl_loo['loo_overall_wkt_rate'] = (bowl_loo['g_overall_wkts'] - bowl_loo['p_overall_wkts']) / (bowl_loo['g_overall_balls'] - bowl_loo['p_overall_balls_b']).replace(0, 1)

df = pd.merge(df, bowl_loo[['season', 'player_name', 'loo_pp_wkt_rate', 'loo_mid_wkt_rate', 'loo_death_wkt_rate', 'loo_overall_wkt_rate']], on=['season', 'player_name'], how='left')
# Fill NaNs
df['loo_pp_wkt_rate'] = df['loo_pp_wkt_rate'].fillna(0.04)
df['loo_mid_wkt_rate'] = df['loo_mid_wkt_rate'].fillna(0.04)
df['loo_death_wkt_rate'] = df['loo_death_wkt_rate'].fillna(0.07)
df['loo_overall_wkt_rate'] = df['loo_overall_wkt_rate'].fillna(0.05)


# ==============================================================================
# 2. BATTING: LOO RAE ONLY (NO E^2)
# ==============================================================================
print("Applying Deep Context Math (LOO RAE)...")
print("Applying Deep Context Math (LOO RAE) with Phase Weights...")
# Phase Weights derived from Logistic Regression on Win Probability (First Innings)
W_PP = 1.00
W_MID = 1.21
W_DEATH = 1.24

df["runs_in_middle"] = df["runs"].fillna(0) - df["runs_in_powerplay"].fillna(0) - df["runs_in_death"].fillna(0)
df["balls_faced_middle"] = df["balls_faced"].fillna(0) - df["balls_faced_powerplay"].fillna(0) - df["balls_faced_death"].fillna(0)

df["weighted_runs"] = (
    df["runs_in_powerplay"].fillna(0) * W_PP +
    df["runs_in_middle"].fillna(0) * W_MID +
    df["runs_in_death"].fillna(0) * W_DEATH
)

df["weighted_expected_runs"] = (
    df["balls_faced_powerplay"].fillna(0) * (df["loo_pp_sr"] / 100) * W_PP +
    df["balls_faced_middle"].fillna(0) * (df["loo_mid_sr"] / 100) * W_MID +
    df["balls_faced_death"].fillna(0) * (df["loo_death_sr"] / 100) * W_DEATH
)

df["weighted_expected_runs"] = df["weighted_expected_runs"].fillna(df["weighted_runs"])
df["rae"] = df["weighted_runs"] - df["weighted_expected_runs"]

# EXPERIMENTAL CONTEXT IMPACT MATH
df["bat_base"] = df["weighted_runs"] + (df["rae"] * 3.0)

# Context Impact (Unified Pressure)
season_rrr_map = global_phase.set_index('season')['season_rrr']
deliveries['season_rrr'] = deliveries['season'].map(season_rrr_map)
deliveries['pressure_multiplier'] = 1.0

# Chasing Pressure (Innings 2)
chase_mask = deliveries['inning'] == 2
deliveries.loc[chase_mask, 'pressure_multiplier'] = (deliveries.loc[chase_mask, 'rrr'] / deliveries.loc[chase_mask, 'season_rrr']).clip(lower=1.0, upper=2.0)

# Garbage Time Stat-Padding Fix
# If RRR exceeds 36.0 (mathematically impossible without extras), the game is effectively dead.
# Pressure drops entirely, so we strip the multiplier back down to 1.0.
garbage_mask = chase_mask & (deliveries['rrr'] > 36.0)
deliveries.loc[garbage_mask, 'pressure_multiplier'] = 1.0
# Setting Pressure (Innings 1)
set_mask = deliveries['inning'] == 1
deliveries.loc[set_mask, 'expected_wickets'] = (deliveries.loc[set_mask, 'balls_elapsed'] / 120.0) * 8.0
deliveries.loc[set_mask, 'wicket_pressure'] = (deliveries.loc[set_mask, 'wickets_before'] + 1.0) / (deliveries.loc[set_mask, 'expected_wickets'] + 1.0)
deliveries.loc[set_mask, 'current_rr'] = (deliveries.loc[set_mask, 'score_before'] / deliveries.loc[set_mask, 'balls_elapsed'].replace(0, 1)) * 6.0
deliveries.loc[set_mask, 'rr_pressure'] = (deliveries.loc[set_mask, 'season_rrr'] / deliveries.loc[set_mask, 'current_rr'].replace(0, 0.1)).clip(upper=2.0)
deliveries.loc[set_mask & (deliveries['balls_elapsed'] <= 12), 'rr_pressure'] = 1.0
deliveries.loc[set_mask, 'pressure_multiplier'] = deliveries.loc[set_mask, ['wicket_pressure', 'rr_pressure']].max(axis=1).clip(lower=1.0, upper=2.0)

# Pressure Bonus
deliveries['pressure_bonus_runs'] = deliveries['batter_runs'] * (deliveries['pressure_multiplier'] - 1.0)
pressure_impact = deliveries.groupby(['season', 'batter']).agg(
    unified_pressure_impact=('pressure_bonus_runs', lambda x: x.sum() * 0.15)
).reset_index().rename(columns={'batter': 'player_name'})

df = pd.merge(df, pressure_impact, on=['season', 'player_name'], how='left')
df['bat_pressure_impact'] = df['unified_pressure_impact'].fillna(0)
df["bat_playoff_impact"] = df["playoff_runs"].fillna(0) * 0.5

df["raw_bat"] = df["bat_base"] + df["bat_pressure_impact"] + df["bat_playoff_impact"]

# 3. BAT PERCENTILE DISTRIBUTION
print("Mapping Batting Percentiles for Wicket Weighting...")
bat_mask = (df["balls_faced"] >= 30) | (df["innings_batted"] >= 8)
df.loc[bat_mask, "bat_percentile"] = df.loc[bat_mask, "raw_bat"].rank(pct=True) * 100
df["bat_percentile"] = df["bat_percentile"].fillna(0)

print("Calculating Contextual Wicket Weighting (Smart Wickets)...")
bowler_wkts = deliveries[deliveries["is_wicket"] & ~deliveries["dismissal_kind"].isin(["run out", "retired hurt", "obstructing the field"])].copy()

# Join bat_percentile of the dismissed batter
bat_pct_map = df[["player_name", "season", "bat_percentile"]].rename(columns={"player_name": "player_out"})
bowler_wkts = pd.merge(bowler_wkts, bat_pct_map, on=["player_out", "season"], how="left")
bowler_wkts["bat_percentile"] = bowler_wkts["bat_percentile"].fillna(0)

# Calculate dynamic wicket value
bowler_wkts["wv"] = 1.0 + (bowler_wkts["bat_percentile"] / 100.0)
bowler_wkts["pp_wv"] = np.where(bowler_wkts["over"] < 6, bowler_wkts["wv"], 0)
bowler_wkts["death_wv"] = np.where(bowler_wkts["over"] >= 15, bowler_wkts["wv"], 0)
bowler_wkts["playoff_wv"] = np.where(bowler_wkts["is_playoff"], bowler_wkts["wv"], 0)
bowler_wkts["mid_wv"] = np.where((bowler_wkts["over"] >= 6) & (bowler_wkts["over"] < 15), bowler_wkts["wv"], 0)

# Aggregate smart wickets per bowler per season# ==============================================================================
# 3. BOWLING: CONTEXTUAL WICKET WEIGHTING (SMART WICKETS + LOO SCARCITY)
# ==============================================================================
print("Calculating Contextual Wicket Weighting (Smart Wickets + LOO Scarcity)...")

# Smart Wickets (Batting percentile of dismissed batter)
smart_w = bowler_wkts.groupby(["bowler", "season"]).agg(
    smart_wickets=("wv", "sum"),
    smart_pp_wickets=("pp_wv", "sum"),
    smart_mid_wickets=("mid_wv", "sum"),
    smart_death_wickets=("death_wv", "sum"),
    smart_playoff_wickets=("playoff_wv", "sum")
).reset_index().rename(columns={"bowler": "player_name"})

df = pd.merge(df, smart_w, on=["player_name", "season"], how="left")
for col in ["smart_wickets", "smart_pp_wickets", "smart_mid_wickets", "smart_death_wickets", "smart_playoff_wickets"]:
    df[col] = df[col].fillna(0)

# Apply LOO Scarcity Multipliers (Empirical Wickets)
df["empirical_pp_wickets"] = df["smart_pp_wickets"] * (df["loo_overall_wkt_rate"] / df["loo_pp_wkt_rate"].replace(0, 1))
df["empirical_mid_wickets"] = df["smart_mid_wickets"] * (df["loo_overall_wkt_rate"] / df["loo_mid_wkt_rate"].replace(0, 1))
df["empirical_death_wickets"] = df["smart_death_wickets"] * (df["loo_overall_wkt_rate"] / df["loo_death_wkt_rate"].replace(0, 1))
df["empirical_wickets"] = df["empirical_pp_wickets"] + df["empirical_mid_wickets"] + df["empirical_death_wickets"]

# BOWLING: Base Efficiency + Death Wkts + PP Wkts + Playoff Wkts (USING EMPIRICAL WICKETS)
df["bowl_death_impact"] = df["empirical_death_wickets"] * df["runs_per_wicket"] * np.maximum(0, df["z_death_econ"] * 0.2)
df["bowl_pp_impact"] = df["empirical_pp_wickets"] * df["runs_per_wicket"] * np.maximum(0, df["z_pp_econ"] * 0.2)
df["bowl_playoff_impact"] = df["smart_playoff_wickets"] * (df["runs_per_wicket"] * 0.5)

# Pressure Impact (Lone Wolf & Defending Low Totals)
df["lone_wolf_multiplier"] = np.maximum(0, df["team_economy"].fillna(0) - df["economy"].fillna(0))
df["low_total_multiplier"] = np.maximum(0, df["league_economy"].fillna(0) - np.where(df["avg_rrr_defended"].fillna(0) == 0, df["league_economy"].fillna(0), df["avg_rrr_defended"].fillna(0)))
df["bowl_pressure_impact"] = (df["empirical_wickets"].fillna(0) * df["runs_per_wicket"].fillna(0) * (df["lone_wolf_multiplier"] * 0.15 + df["low_total_multiplier"] * 0.15)).fillna(0)

df["bowl_base"] = df["empirical_wickets"] * df["runs_per_wicket"] * (2.0 + np.tanh(df["z_econ"]) + np.tanh(df["z_bowl_avg"]))
df["raw_bowl"] = df["bowl_base"] + df["bowl_death_impact"] + df["bowl_pp_impact"] + df["bowl_playoff_impact"] + df["bowl_pressure_impact"]

# ==============================================================================
# 4. PERCENTILE MAPPING & ALL-ROUNDER SYNERGY BOOST
# ==============================================================================
print("Mapping Percentiles and Calculating Synergy Boost...")
bat_mask_pct = (df["balls_faced"] >= 30) | (df["innings_batted"] >= 8)
df.loc[bat_mask_pct, "bat_percentile"] = df.loc[bat_mask_pct, "raw_bat"].rank(pct=True) * 100
df["bat_percentile"] = df["bat_percentile"].fillna(0)

bowl_mask_pct = (df["balls_bowled"] >= 30) | (df["innings_bowled"] >= 8)
df.loc[bowl_mask_pct, "bowl_percentile"] = df.loc[bowl_mask_pct, "raw_bowl"].rank(pct=True) * 100
df["bowl_percentile"] = df["bowl_percentile"].fillna(0)

df["max_pct"] = df[["bat_percentile", "bowl_percentile"]].max(axis=1)
df["min_pct"] = df[["bat_percentile", "bowl_percentile"]].min(axis=1)

bat_confidence = (df["balls_faced"].fillna(0) / 120).clip(upper=1.0) ** 2.0
bowl_confidence = (df["balls_bowled"].fillna(0) / 120).clip(upper=1.0) ** 2.0
ar_confidence = np.minimum(bat_confidence, bowl_confidence)

raw_boost = ((df["min_pct"] / 100) ** 2) * 5.0
df["v11_raw"] = df["max_pct"] + (raw_boost * ar_confidence)

max_v11 = df["v11_raw"].max()
df["quwrof_v11"] = (df["v11_raw"] / max_v11) * 99.5

# Z-SCORE TIEBREAKER
bat_mean = df.loc[df["raw_bat"] > 0, "raw_bat"].mean()
bat_std = df.loc[df["raw_bat"] > 0, "raw_bat"].std()
bowl_mean = df.loc[df["raw_bowl"] > 0, "raw_bowl"].mean()
bowl_std = df.loc[df["raw_bowl"] > 0, "raw_bowl"].std()

df["bat_z"] = (df["raw_bat"] - bat_mean) / bat_std
df["bowl_z"] = (df["raw_bowl"] - bowl_mean) / bowl_std
df["max_z"] = df[["bat_z", "bowl_z"]].max(axis=1).fillna(0)

# Add microscopic tiebreaker
df["quwrof_v11"] = df["quwrof_v11"] + (df["max_z"] / 100)
df["quwrof_v11"] = df["quwrof_v11"].round(4)

out_df = df.sort_values("quwrof_v11", ascending=False).reset_index(drop=True)

print("\n--- THE V11 LEADERBOARD (CONTEXTUAL PERCENTILE) ---")
cols_to_show = ["player_name", "season", "bat_percentile", "bowl_percentile", "quwrof_v11"]
print(out_df[cols_to_show].head(20).round(2).to_string(index=False))

output_path = data_dir / "quwrof_v11_scores.csv"
out_df.rename(columns={"bat_pressure_impact": "bat_chase_impact"}, inplace=True)
out_df[["player_name", "season", "quwrof_v11", "bat_percentile", "bowl_percentile", "bat_base", "bat_chase_impact", "bat_playoff_impact", "raw_bat", "rae", "smart_wickets", "empirical_wickets", "bowl_base", "bowl_pp_impact", "bowl_death_impact", "bowl_playoff_impact", "bowl_pressure_impact", "raw_bowl"]].to_csv(output_path, index=False)
print(f"\nV11 scores saved to {output_path}")
