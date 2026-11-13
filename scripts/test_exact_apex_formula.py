import pandas as pd
import numpy as np

print("Loading enriched_bbb.csv...")
df = pd.read_csv('d:/ipl-rating/enriched_bbb.csv', low_memory=False)

# Clean season column
df['season_str'] = df['season'].astype(str).str.slice(0, 4)

# 1. Deliveries setup matching build_v11_score.py:
# is_legal: ~(is_wide | is_noball)
df['is_legal'] = df['is_legal'].astype(bool)
# is_bowler_wicket: is_wicket & dismissal not in ['run out', 'retired hurt', 'obstructing the field']
non_bowler_dismissals = ['run out', 'retired hurt', 'obstructing the field', 'retired out']
df['is_bowler_wicket'] = df['is_wicket'] & (~df['dismissal_type'].str.lower().isin(non_bowler_dismissals))

# Phase definitions
# overid is 0-indexed or 1-indexed? Let's check min overid
print("Overid min/max:", df['overid'].min(), df['overid'].max())
if df['overid'].min() == 1:
    df['over_0'] = df['overid'] - 1
else:
    df['over_0'] = df['overid']

df['is_pp'] = df['over_0'] < 6
df['is_death'] = df['over_0'] >= 15
df['is_mid'] = ~df['is_pp'] & ~df['is_death']

# Global Season Phase Totals
global_phase = df.groupby('season_str').apply(lambda x: pd.Series({
    'g_pp_runs': x[x['is_pp']]['total_ball_runs'].sum(),
    'g_pp_balls': x[x['is_pp']]['is_legal'].sum(),
    'g_pp_wkts': x[x['is_pp']]['is_bowler_wicket'].sum(),
    'g_mid_runs': x[x['is_mid']]['total_ball_runs'].sum(),
    'g_mid_balls': x[x['is_mid']]['is_legal'].sum(),
    'g_mid_wkts': x[x['is_mid']]['is_bowler_wicket'].sum(),
    'g_death_runs': x[x['is_death']]['total_ball_runs'].sum(),
    'g_death_balls': x[x['is_death']]['is_legal'].sum(),
    'g_death_wkts': x[x['is_death']]['is_bowler_wicket'].sum(),
    'g_overall_runs': x['total_ball_runs'].sum(),
    'g_overall_balls': x['is_legal'].sum(),
    'g_overall_wkts': x['is_bowler_wicket'].sum()
}), include_groups=False).reset_index()

global_phase['season_rrr'] = (global_phase['g_overall_runs'] / global_phase['g_overall_balls'].replace(0, 1)) * 6.0
print("\nGlobal Phase Stats:")
print(global_phase[['season_str', 'season_rrr', 'g_overall_runs', 'g_overall_wkts']])

# Map season_rrr back
season_rrr_map = global_phase.set_index('season_str')['season_rrr']
df['season_rrr'] = df['season_str'].map(season_rrr_map)
df['pressure_multiplier'] = 1.0

# Innings 2 Chasing Pressure
chase_mask = df['innings'] == 2
df.loc[chase_mask, 'pressure_multiplier'] = (df.loc[chase_mask, 'RRR'] / df.loc[chase_mask, 'season_rrr']).clip(lower=1.0, upper=2.0)

# Garbage Time Stat-Padding Fix: RRR > 36.0 drops to 1.0
garbage_mask = chase_mask & (df['RRR'] > 36.0)
df.loc[garbage_mask, 'pressure_multiplier'] = 1.0

# Innings 1 Setting Pressure
set_mask = df['innings'] == 1
df.loc[set_mask, 'expected_wickets'] = (df.loc[set_mask, 'cum_legal_before'] / 120.0) * 8.0
df.loc[set_mask, 'wicket_pressure'] = (df.loc[set_mask, 'cum_wickets_before'] + 1.0) / (df.loc[set_mask, 'expected_wickets'] + 1.0)
df.loc[set_mask, 'current_rr'] = (df.loc[set_mask, 'cum_runs_before'] / df.loc[set_mask, 'cum_legal_before'].replace(0, 1)) * 6.0
df.loc[set_mask, 'rr_pressure'] = (df.loc[set_mask, 'season_rrr'] / df.loc[set_mask, 'current_rr'].replace(0, 0.1)).clip(upper=2.0)
df.loc[set_mask & (df['cum_legal_before'] <= 12), 'rr_pressure'] = 1.0
df.loc[set_mask, 'pressure_multiplier'] = df.loc[set_mask, ['wicket_pressure', 'rr_pressure']].max(axis=1).clip(lower=1.0, upper=2.0)

# Pressure Bonus Runs
df['pressure_bonus_runs'] = df['runs'] * (df['pressure_multiplier'] - 1.0)

# Aggregate Batting Pressure Impact (Unified Pressure)
bat_pressure = df.groupby('striker_name').agg(
    total_runs=('runs', 'sum'),
    balls_faced=('is_legal', 'sum'),
    chase_runs=('runs', lambda x: x[df.loc[x.index, 'innings'] == 2].sum()),
    chase_balls=('is_legal', lambda x: x[df.loc[x.index, 'innings'] == 2].sum()),
    pressure_bonus_runs=('pressure_bonus_runs', 'sum'),
    pressure_balls_faced=('is_legal', lambda x: x[df.loc[x.index, 'pressure_multiplier'] > 1.0].sum()),
    pressure_runs=('runs', lambda x: x[df.loc[x.index, 'pressure_multiplier'] > 1.0].sum()),
).reset_index().rename(columns={'striker_name': 'player_name'})

# Exactly like build_v11_score.py: unified_pressure_impact = pressure_bonus_runs * 0.15
bat_pressure['bat_chase_impact'] = bat_pressure['pressure_bonus_runs'] * 0.15

# Bowling calculations
# Bowling pressure impact from build_v11_score.py:
# lone_wolf_multiplier = max(0, team_economy - economy)
# low_total_multiplier = max(0, league_economy - avg_rrr_defended)
# bowl_pressure_impact = empirical_wickets * runs_per_wicket * (lone_wolf * 0.15 + low_total * 0.15)
# Also death bowling impact: bowl_death_impact = empirical_death_wickets * runs_per_wicket * max(0, z_death_econ * 0.2)

# Calculate match level team economies and bowler stats
match_bowler = df.groupby(['match_id', 'bowling_team_id', 'bowler_name']).agg(
    b_runs=('total_ball_runs', 'sum'),
    b_balls=('is_legal', 'sum'),
    b_wkts=('is_bowler_wicket', 'sum'),
    is_inn2=('innings', lambda x: (x == 2).iloc[0]),
    avg_rrr_faced=('RRR', lambda x: x[x > 0].mean() if (x > 0).any() else 0.0)
).reset_index()

match_team = df.groupby(['match_id', 'bowling_team_id']).agg(
    team_runs=('total_ball_runs', 'sum'),
    team_balls=('is_legal', 'sum')
).reset_index()
match_team['team_econ'] = (match_team['team_runs'] / match_team['team_balls'].replace(0, 1)) * 6.0

match_bowler = match_bowler.merge(match_team[['match_id', 'bowling_team_id', 'team_econ']], on=['match_id', 'bowling_team_id'], how='left')
match_bowler['bowler_econ'] = (match_bowler['b_runs'] / match_bowler['b_balls'].replace(0, 1)) * 6.0
match_bowler['lone_wolf_diff'] = np.maximum(0, match_bowler['team_econ'] - match_bowler['bowler_econ'])

league_econ = (df['total_ball_runs'].sum() / df['is_legal'].sum()) * 6.0
runs_per_wkt = df['total_ball_runs'].sum() / df['is_bowler_wicket'].sum()
print(f"League economy: {league_econ:.2f}, Runs per wicket: {runs_per_wkt:.2f}")

# Bowler overall aggregation
bowl_pressure = df.groupby('bowler_name').agg(
    total_balls=('is_legal', 'sum'),
    total_runs=('total_ball_runs', 'sum'),
    wickets=('is_bowler_wicket', 'sum'),
    death_balls=('is_legal', lambda x: x[df.loc[x.index, 'is_death']].sum()),
    death_runs=('total_ball_runs', lambda x: x[df.loc[x.index, 'is_death']].sum()),
    death_wkts=('is_bowler_wicket', lambda x: x[df.loc[x.index, 'is_death']].sum()),
    inn2_balls=('is_legal', lambda x: x[df.loc[x.index, 'innings'] == 2].sum()),
    inn2_runs=('total_ball_runs', lambda x: x[df.loc[x.index, 'innings'] == 2].sum()),
    inn2_wkts=('is_bowler_wicket', lambda x: x[df.loc[x.index, 'innings'] == 2].sum()),
    pressure_balls=('is_legal', lambda x: x[df.loc[x.index, 'pressure_multiplier'] > 1.0].sum()),
    pressure_runs=('total_ball_runs', lambda x: x[df.loc[x.index, 'pressure_multiplier'] > 1.0].sum()),
    pressure_wkts=('is_bowler_wicket', lambda x: x[df.loc[x.index, 'pressure_multiplier'] > 1.0].sum()),
).reset_index().rename(columns={'bowler_name': 'player_name'})

bowl_pressure['economy'] = (bowl_pressure['total_runs'] / bowl_pressure['total_balls'].replace(0, 1)) * 6.0
bowl_pressure['death_econ'] = (bowl_pressure['death_runs'] / bowl_pressure['death_balls'].replace(0, 1)) * 6.0
bowl_pressure['pressure_econ'] = (bowl_pressure['pressure_runs'] / bowl_pressure['pressure_balls'].replace(0, 1)) * 6.0
bowl_pressure['pressure_sr'] = bowl_pressure['pressure_balls'] / bowl_pressure['pressure_wkts'].replace(0, np.nan)

# Lone wolf average per bowler
bowler_lone_wolf = match_bowler.groupby('bowler_name')['lone_wolf_diff'].mean().reset_index().rename(columns={'bowler_name': 'player_name', 'lone_wolf_diff': 'lone_wolf_multiplier'})
bowl_pressure = bowl_pressure.merge(bowler_lone_wolf, on='player_name', how='left')

# Innings 2 defended RRR
inn2_defended = match_bowler[match_bowler['is_inn2']].groupby('bowler_name')['avg_rrr_faced'].mean().reset_index().rename(columns={'bowler_name': 'player_name', 'avg_rrr_faced': 'avg_rrr_defended'})
bowl_pressure = bowl_pressure.merge(inn2_defended, on='player_name', how='left')
bowl_pressure['avg_rrr_defended'] = bowl_pressure['avg_rrr_defended'].fillna(league_econ)
bowl_pressure['low_total_multiplier'] = np.maximum(0, league_econ - bowl_pressure['avg_rrr_defended'])

# V11 exact bowl pressure formula:
# bowl_pressure_impact = empirical_wickets * runs_per_wicket * (lone_wolf * 0.15 + low_total * 0.15)
bowl_pressure['bowl_pressure_impact'] = (bowl_pressure['wickets'] * runs_per_wkt * (bowl_pressure['lone_wolf_multiplier'] * 0.15 + bowl_pressure['low_total_multiplier'] * 0.15)).fillna(0)

# Print Top 20 Batters by bat_chase_impact (min 150 balls)
print("\n=== TOP 20 BATTERS BY EXACT V11/APEX CHASE & PRESSURE IMPACT (min 150 balls) ===")
top_bat = bat_pressure[bat_pressure['balls_faced'] >= 150].sort_values('bat_chase_impact', ascending=False)
print(top_bat[['player_name', 'bat_chase_impact', 'total_runs', 'balls_faced', 'pressure_runs', 'pressure_bonus_runs']].head(20).to_string(index=False))

# Print Top 20 Bowlers by bowl_pressure_impact (min 150 balls)
print("\n=== TOP 20 BOWLERS BY EXACT V11/APEX PRESSURE IMPACT (min 150 balls) ===")
top_bowl = bowl_pressure[bowl_pressure['total_balls'] >= 150].sort_values('bowl_pressure_impact', ascending=False)
print(top_bowl[['player_name', 'bowl_pressure_impact', 'wickets', 'total_balls', 'economy', 'lone_wolf_multiplier']].head(20).to_string(index=False))
