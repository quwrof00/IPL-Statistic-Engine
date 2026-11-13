import pandas as pd
import numpy as np
import json

print("Running full Apex Engine pipeline on 2022+ Data Pack...")
df = pd.read_csv('d:/ipl-rating/enriched_bbb.csv', low_memory=False)

df['season_str'] = df['season'].astype(str).str.slice(0, 4)
df['is_legal'] = df['is_legal'].astype(bool)
non_bowler_dismissals = ['run out', 'retired hurt', 'obstructing the field', 'retired out']
df['is_bowler_wicket'] = df['is_wicket'] & (~df['dismissal_type'].str.lower().isin(non_bowler_dismissals))

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

# ==================== BATTING AGGREGATION ====================
bat_agg = df.groupby('striker_name').agg(
    total_runs=('runs', 'sum'),
    balls_faced=('is_legal', 'sum'),
    dismissals=('is_wicket', lambda x: x[df.loc[x.index, 'dismissed_player_id'] == df.loc[x.index, 'striker_id']].sum()),
    fours=('is_four', 'sum'),
    sixes=('is_six', 'sum'),
    dot_balls=('runs', lambda x: (x == 0).sum()),
    # Pressure stats
    pressure_balls=('is_legal', lambda x: x[df.loc[x.index, 'pressure_multiplier'] > 1.0].sum()),
    pressure_runs=('runs', lambda x: x[df.loc[x.index, 'pressure_multiplier'] > 1.0].sum()),
    pressure_bonus_runs=('pressure_bonus_runs', 'sum'),
    pressure_dismissals=('is_wicket', lambda x: x[(df.loc[x.index, 'pressure_multiplier'] > 1.0) & (df.loc[x.index, 'dismissed_player_id'] == df.loc[x.index, 'striker_id'])].sum()),
    # Chase stats
    chase_balls=('is_legal', lambda x: x[df.loc[x.index, 'innings'] == 2].sum()),
    chase_runs=('runs', lambda x: x[df.loc[x.index, 'innings'] == 2].sum()),
    chase_dismissals=('is_wicket', lambda x: x[(df.loc[x.index, 'innings'] == 2) & (df.loc[x.index, 'dismissed_player_id'] == df.loc[x.index, 'striker_id'])].sum()),
    # Death stats
    death_balls=('is_legal', lambda x: x[df.loc[x.index, 'is_death']].sum()),
    death_runs=('runs', lambda x: x[df.loc[x.index, 'is_death']].sum()),
).reset_index().rename(columns={'striker_name': 'player_name'})

bat_agg['bat_chase_impact'] = bat_agg['pressure_bonus_runs'] * 0.15
bat_agg['overall_sr'] = (bat_agg['total_runs'] / bat_agg['balls_faced'].replace(0, 1)) * 100.0
bat_agg['overall_avg'] = bat_agg['total_runs'] / bat_agg['dismissals'].replace(0, 1)
bat_agg['pressure_sr'] = (bat_agg['pressure_runs'] / bat_agg['pressure_balls'].replace(0, 1)) * 100.0
bat_agg['pressure_avg'] = bat_agg['pressure_runs'] / bat_agg['pressure_dismissals'].replace(0, 1)
bat_agg['chase_sr'] = (bat_agg['chase_runs'] / bat_agg['chase_balls'].replace(0, 1)) * 100.0
bat_agg['chase_avg'] = bat_agg['chase_runs'] / bat_agg['chase_dismissals'].replace(0, 1)
bat_agg['sr_lift'] = bat_agg['pressure_sr'] - bat_agg['overall_sr']

# ==================== BOWLING AGGREGATION ====================
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

bowl_agg = df.groupby('bowler_name').agg(
    total_balls=('is_legal', 'sum'),
    total_runs=('total_ball_runs', 'sum'),
    wickets=('is_bowler_wicket', 'sum'),
    dot_balls=('total_ball_runs', lambda x: (x == 0).sum()),
    # Phase stats
    pp_balls=('is_legal', lambda x: x[df.loc[x.index, 'is_pp']].sum()),
    pp_runs=('total_ball_runs', lambda x: x[df.loc[x.index, 'is_pp']].sum()),
    pp_wkts=('is_bowler_wicket', lambda x: x[df.loc[x.index, 'is_pp']].sum()),
    death_balls=('is_legal', lambda x: x[df.loc[x.index, 'is_death']].sum()),
    death_runs=('total_ball_runs', lambda x: x[df.loc[x.index, 'is_death']].sum()),
    death_wkts=('is_bowler_wicket', lambda x: x[df.loc[x.index, 'is_death']].sum()),
    # Pressure stats
    pressure_balls=('is_legal', lambda x: x[df.loc[x.index, 'pressure_multiplier'] > 1.0].sum()),
    pressure_runs=('total_ball_runs', lambda x: x[df.loc[x.index, 'pressure_multiplier'] > 1.0].sum()),
    pressure_wkts=('is_bowler_wicket', lambda x: x[df.loc[x.index, 'pressure_multiplier'] > 1.0].sum()),
).reset_index().rename(columns={'bowler_name': 'player_name'})

bowl_agg['economy'] = (bowl_agg['total_runs'] / bowl_agg['total_balls'].replace(0, 1)) * 6.0
bowl_agg['bowling_avg'] = bowl_agg['total_runs'] / bowl_agg['wickets'].replace(0, 1)
bowl_agg['bowling_sr'] = bowl_agg['total_balls'] / bowl_agg['wickets'].replace(0, 1)
bowl_agg['death_econ'] = (bowl_agg['death_runs'] / bowl_agg['death_balls'].replace(0, 1)) * 6.0
bowl_agg['pressure_econ'] = (bowl_agg['pressure_runs'] / bowl_agg['pressure_balls'].replace(0, 1)) * 6.0
bowl_agg['pressure_sr'] = bowl_agg['pressure_balls'] / bowl_agg['pressure_wkts'].replace(0, 1)
bowl_agg['econ_suppression'] = bowl_agg['economy'] - bowl_agg['pressure_econ']

# Lone wolf average per bowler
bowler_lone_wolf = match_bowler.groupby('bowler_name')['lone_wolf_diff'].mean().reset_index().rename(columns={'bowler_name': 'player_name', 'lone_wolf_diff': 'lone_wolf_multiplier'})
bowl_agg = bowl_agg.merge(bowler_lone_wolf, on='player_name', how='left')

# Innings 2 defended RRR
inn2_defended = match_bowler[match_bowler['is_inn2']].groupby('bowler_name')['avg_rrr_faced'].mean().reset_index().rename(columns={'bowler_name': 'player_name', 'avg_rrr_faced': 'avg_rrr_defended'})
bowl_agg = bowl_agg.merge(inn2_defended, on='player_name', how='left')
bowl_agg['avg_rrr_defended'] = bowl_agg['avg_rrr_defended'].fillna(league_econ)
bowl_agg['low_total_multiplier'] = np.maximum(0, league_econ - bowl_agg['avg_rrr_defended'])

# V11 exact formula
bowl_agg['bowl_pressure_impact'] = (bowl_agg['wickets'] * runs_per_wkt * (bowl_agg['lone_wolf_multiplier'] * 0.15 + bowl_agg['low_total_multiplier'] * 0.15)).fillna(0)

# Filter for active qualified players (min 150 balls)
active_retired = ['Ambati Rayudu', 'Dinesh Karthik', 'Shikhar Dhawan', 'Kieron Pollard', 'Robin Uthappa', 'Eoin Morgan', 'Dwayne Bravo']
bat_qual = bat_agg[(bat_agg['balls_faced'] >= 150) & (~bat_agg['player_name'].isin(active_retired))].copy()
bowl_qual = bowl_agg[(bowl_agg['total_balls'] >= 150) & (~bowl_agg['player_name'].isin(active_retired))].copy()

# Calculate Percentiles
bat_qual['bat_pressure_percentile'] = bat_qual['bat_chase_impact'].rank(pct=True) * 100.0
bowl_qual['bowl_pressure_percentile'] = bowl_qual['bowl_pressure_impact'].rank(pct=True) * 100.0

top10_batters = bat_qual.sort_values('bat_chase_impact', ascending=False).head(10).reset_index(drop=True)
top10_bowlers = bowl_qual.sort_values('bowl_pressure_impact', ascending=False).head(10).reset_index(drop=True)

top10_batters['rank'] = range(1, 11)
top10_bowlers['rank'] = range(1, 11)

print("\n=== FINAL OFFICIAL TOP 10 BATTERS UNDER PRESSURE (EXACT APEX FORMULA) ===")
print(top10_batters[['rank', 'player_name', 'bat_chase_impact', 'bat_pressure_percentile', 'total_runs', 'overall_sr', 'pressure_sr', 'sr_lift']].to_string(index=False))

print("\n=== FINAL OFFICIAL TOP 10 BOWLERS UNDER PRESSURE (EXACT APEX FORMULA) ===")
print(top10_bowlers[['rank', 'player_name', 'bowl_pressure_impact', 'bowl_pressure_percentile', 'wickets', 'economy', 'pressure_econ', 'lone_wolf_multiplier']].to_string(index=False))

# Export to JSON
top_batters_list = top10_batters.round(2).to_dict(orient='records')
top_bowlers_list = top10_bowlers.round(2).to_dict(orient='records')

all_batters_list = bat_qual.sort_values('bat_chase_impact', ascending=False).head(50).round(2).to_dict(orient='records')
all_bowlers_list = bowl_qual.sort_values('bowl_pressure_impact', ascending=False).head(50).round(2).to_dict(orient='records')

output = {
    'top10_batters': top_batters_list,
    'top10_bowlers': top_bowlers_list,
    'all_batters': all_batters_list,
    'all_bowlers': all_bowlers_list,
    'benchmarks': {
        'league_economy': round(league_econ, 2),
        'runs_per_wicket': round(runs_per_wkt, 2),
        'total_deliveries': len(df),
        'pressure_deliveries': int((df['pressure_multiplier'] > 1.0).sum()),
        'pressure_pct': round((df['pressure_multiplier'] > 1.0).mean() * 100.0, 1),
    }
}

with open('d:/ipl-rating/ipl/public/official_rankings.json', 'w') as f:
    json.dump(output, f, indent=2)

print("\nSuccessfully exported to d:/ipl-rating/ipl/public/official_rankings.json")
