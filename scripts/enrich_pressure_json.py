import pandas as pd
import numpy as np
import json

print("Building enriched official pressure dataset for UI...")
df = pd.read_csv('d:/ipl-rating/enriched_bbb.csv', low_memory=False)

# Load official player metadata mapping (nationality, teams, etc.)
mapping = pd.read_csv('C:/Users/Shourya/Downloads/6af458274c1e8_data_pack/Data Pack/competition_team_player_mapping.csv')
teams_df = pd.read_csv('C:/Users/Shourya/Downloads/6af458274c1e8_data_pack/Data Pack/teams.csv')
comps_df = pd.read_csv('C:/Users/Shourya/Downloads/6af458274c1e8_data_pack/Data Pack/competitions.csv')

# Determine nationality/team associations
mapping_with_team = mapping.merge(teams_df[['team_id', 'team_name']], on='team_id', how='left')

# Get national teams
nationalities = ['India', 'Australia', 'England', 'South Africa', 'New Zealand', 'West Indies', 'Pakistan', 'Sri Lanka', 'Afghanistan', 'Bangladesh', 'Zimbabwe', 'Ireland', 'Netherlands', 'Scotland', 'Namibia', 'UAE', 'Nepal', 'Oman', 'USA', 'Canada']
player_nat_map = {}
for p_name, group in mapping_with_team.groupby('player_name'):
    nats = [t for t in group['team_name_x'].unique() if t in nationalities]
    if nats:
        player_nat_map[p_name] = nats[0]
    else:
        # Check if they played in IPL
        ipl_teams = group[group['comp_name'].str.contains('IPL', case=False, na=False)]
        if len(ipl_teams) > 0:
            player_nat_map[p_name] = 'India' # fallback or check
        else:
            player_nat_map[p_name] = 'Overseas'

# Hardcode well known nationalities
known_nats = {
    'Wanindu Hasaranga': 'Sri Lanka',
    'Rashid Khan': 'Afghanistan',
    'Jasprit Bumrah': 'India',
    'Axar Patel': 'India',
    'Arshdeep Singh': 'India',
    'Varun Chakravarthy': 'India',
    'Blessing Muzarabani': 'Zimbabwe',
    'Kuldeep Yadav': 'India',
    'Sunil Narine': 'West Indies',
    'Bhuvneshwar Kumar': 'India',
    'Akeal Hosein': 'West Indies',
    'Yuzvendra Chahal': 'India',
    'Mitchell Santner': 'New Zealand',
    'Ravi Bishnoi': 'India',
    'Sikandar Raza': 'Zimbabwe',
    'Noor Ahmad': 'Afghanistan',
    'Shoriful Islam': 'Bangladesh',
    'Maheesh Theekshana': 'Sri Lanka',
    'Josh Hazlewood': 'Australia',
    'Mustafizur Rahman': 'Bangladesh',
    'Namboori Tilak Varma': 'India',
    'Suryakumar Yadav': 'India',
    'David Miller': 'South Africa',
    'Rovman Powell': 'West Indies',
    'Nicholas Pooran': 'West Indies',
    'Tristan Stubbs': 'South Africa',
    'Jos Buttler': 'England',
    'Aiden Markram': 'South Africa',
    'Tim David': 'Australia',
    'Rinku Singh': 'India',
    'Hardik Pandya': 'India',
    'Marcus Stoinis': 'Australia',
    'Heinrich Klaasen': 'South Africa',
    'Shivam Dube': 'India',
    'Ishan Kishan': 'India',
    'Lokesh Rahul': 'India',
    'Shimron Hetmyer': 'West Indies',
    'Abhishek Sharma': 'India',
    'Sanju Samson': 'India',
    'Shubman Gill': 'India',
    'Virat Kohli': 'India',
    'Rohit Sharma': 'India',
    'Rishabh Pant': 'India',
    'Yashasvi Jaiswal': 'India',
    'Ruturaj Gaikwad': 'India',
    'Glenn Maxwell': 'Australia',
    'Travis Head': 'Australia',
    'Andre Russell': 'West Indies',
    'Trent Boult': 'New Zealand',
    'Kagiso Rabada': 'South Africa',
    'Anrich Nortje': 'South Africa',
    'Mohammad Shami': 'India',
    'Mohammed Siraj': 'India',
    'Harshal Patel': 'India',
    'T Natarajan': 'India',
    'Sandeep Sharma': 'India',
    'Matheesha Pathirana': 'Sri Lanka',
    'Fazalhaq Farooqi': 'Afghanistan',
    'Naveen-ul-Haq': 'Afghanistan',
    'Sam Curran': 'England',
    'Liam Livingstone': 'England',
}

# Clean season column
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
season_rrr_map = global_phase.set_index('season_str')['season_rrr']
df['season_rrr'] = df['season_str'].map(season_rrr_map)
df['pressure_multiplier'] = 1.0

# Innings 2 Chasing Pressure
chase_mask = df['innings'] == 2
df.loc[chase_mask, 'pressure_multiplier'] = (df.loc[chase_mask, 'RRR'] / df.loc[chase_mask, 'season_rrr']).clip(lower=1.0, upper=2.0)
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

# ==================== BATTING ====================
bat_agg = df.groupby(['striker_id', 'striker_name']).agg(
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
    # Competition splits
    ipl_balls=('is_legal', lambda x: x[df.loc[x.index, 'comp_name'].str.contains('IPL', case=False, na=False)].sum()),
    t20i_balls=('is_legal', lambda x: x[~df.loc[x.index, 'comp_name'].str.contains('IPL', case=False, na=False)].sum()),
    ipl_pres_balls=('is_legal', lambda x: x[(df.loc[x.index, 'comp_name'].str.contains('IPL', case=False, na=False)) & (df.loc[x.index, 'pressure_multiplier'] > 1.0)].sum()),
    ipl_pres_runs=('runs', lambda x: x[(df.loc[x.index, 'comp_name'].str.contains('IPL', case=False, na=False)) & (df.loc[x.index, 'pressure_multiplier'] > 1.0)].sum()),
    t20i_pres_balls=('is_legal', lambda x: x[(~df.loc[x.index, 'comp_name'].str.contains('IPL', case=False, na=False)) & (df.loc[x.index, 'pressure_multiplier'] > 1.0)].sum()),
    t20i_pres_runs=('runs', lambda x: x[(~df.loc[x.index, 'comp_name'].str.contains('IPL', case=False, na=False)) & (df.loc[x.index, 'pressure_multiplier'] > 1.0)].sum()),
).reset_index().rename(columns={'striker_name': 'player_name', 'striker_id': 'player_id'})

bat_agg['bat_chase_impact'] = bat_agg['pressure_bonus_runs'] * 0.15
bat_agg['overall_sr'] = ((bat_agg['total_runs'] / bat_agg['balls_faced'].replace(0, 1)) * 100.0).round(2)
bat_agg['overall_avg'] = (bat_agg['total_runs'] / bat_agg['dismissals'].replace(0, 1)).round(2)
bat_agg['pressure_sr'] = ((bat_agg['pressure_runs'] / bat_agg['pressure_balls'].replace(0, 1)) * 100.0).round(2)
bat_agg['pressure_avg'] = (bat_agg['pressure_runs'] / bat_agg['pressure_dismissals'].replace(0, 1)).round(2)
bat_agg['sr_lift'] = (bat_agg['pressure_sr'] - bat_agg['overall_sr']).round(2)
bat_agg['ipl_sr'] = ((bat_agg['ipl_pres_runs'] / bat_agg['ipl_pres_balls'].replace(0, 1)) * 100.0).round(2)
bat_agg['t20i_sr'] = ((bat_agg['t20i_pres_runs'] / bat_agg['t20i_pres_balls'].replace(0, 1)) * 100.0).round(2)

# ==================== BOWLING ====================
match_bowler = df.groupby(['match_id', 'bowling_team_id', 'bowler_id', 'bowler_name']).agg(
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

bowl_agg = df.groupby(['bowler_id', 'bowler_name']).agg(
    total_balls=('is_legal', 'sum'),
    total_runs=('total_ball_runs', 'sum'),
    wickets=('is_bowler_wicket', 'sum'),
    dot_balls=('total_ball_runs', lambda x: (x == 0).sum()),
    # Phase stats
    death_balls=('is_legal', lambda x: x[df.loc[x.index, 'is_death']].sum()),
    death_runs=('total_ball_runs', lambda x: x[df.loc[x.index, 'is_death']].sum()),
    death_wkts=('is_bowler_wicket', lambda x: x[df.loc[x.index, 'is_death']].sum()),
    # Pressure stats
    pressure_balls=('is_legal', lambda x: x[df.loc[x.index, 'pressure_multiplier'] > 1.0].sum()),
    pressure_runs=('total_ball_runs', lambda x: x[df.loc[x.index, 'pressure_multiplier'] > 1.0].sum()),
    pressure_wkts=('is_bowler_wicket', lambda x: x[df.loc[x.index, 'pressure_multiplier'] > 1.0].sum()),
    # Competition splits
    ipl_balls=('is_legal', lambda x: x[df.loc[x.index, 'comp_name'].str.contains('IPL', case=False, na=False)].sum()),
    t20i_balls=('is_legal', lambda x: x[~df.loc[x.index, 'comp_name'].str.contains('IPL', case=False, na=False)].sum()),
    ipl_pres_balls=('is_legal', lambda x: x[(df.loc[x.index, 'comp_name'].str.contains('IPL', case=False, na=False)) & (df.loc[x.index, 'pressure_multiplier'] > 1.0)].sum()),
    ipl_pres_runs=('total_ball_runs', lambda x: x[(df.loc[x.index, 'comp_name'].str.contains('IPL', case=False, na=False)) & (df.loc[x.index, 'pressure_multiplier'] > 1.0)].sum()),
    t20i_pres_balls=('is_legal', lambda x: x[(~df.loc[x.index, 'comp_name'].str.contains('IPL', case=False, na=False)) & (df.loc[x.index, 'pressure_multiplier'] > 1.0)].sum()),
    t20i_pres_runs=('total_ball_runs', lambda x: x[(~df.loc[x.index, 'comp_name'].str.contains('IPL', case=False, na=False)) & (df.loc[x.index, 'pressure_multiplier'] > 1.0)].sum()),
).reset_index().rename(columns={'bowler_name': 'player_name', 'bowler_id': 'player_id'})

bowl_agg['economy'] = ((bowl_agg['total_runs'] / bowl_agg['total_balls'].replace(0, 1)) * 6.0).round(2)
bowl_agg['bowling_avg'] = (bowl_agg['total_runs'] / bowl_agg['wickets'].replace(0, 1)).round(2)
bowl_agg['bowling_sr'] = (bowl_agg['total_balls'] / bowl_agg['wickets'].replace(0, 1)).round(2)
bowl_agg['death_econ'] = ((bowl_agg['death_runs'] / bowl_agg['death_balls'].replace(0, 1)) * 6.0).round(2)
bowl_agg['pressure_econ'] = ((bowl_agg['pressure_runs'] / bowl_agg['pressure_balls'].replace(0, 1)) * 6.0).round(2)
bowl_agg['pressure_sr'] = (bowl_agg['pressure_balls'] / bowl_agg['pressure_wkts'].replace(0, 1)).round(2)
bowl_agg['econ_suppression'] = (bowl_agg['economy'] - bowl_agg['pressure_econ']).round(2)
bowl_agg['ipl_econ'] = ((bowl_agg['ipl_pres_runs'] / bowl_agg['ipl_pres_balls'].replace(0, 1)) * 6.0).round(2)
bowl_agg['t20i_econ'] = ((bowl_agg['t20i_pres_runs'] / bowl_agg['t20i_pres_balls'].replace(0, 1)) * 6.0).round(2)

bowler_lone_wolf = match_bowler.groupby(['bowler_id', 'bowler_name'])['lone_wolf_diff'].mean().reset_index().rename(columns={'bowler_name': 'player_name', 'bowler_id': 'player_id', 'lone_wolf_diff': 'lone_wolf_multiplier'})
bowl_agg = bowl_agg.merge(bowler_lone_wolf, on=['player_id', 'player_name'], how='left')

inn2_defended = match_bowler[match_bowler['is_inn2']].groupby(['bowler_id', 'bowler_name'])['avg_rrr_faced'].mean().reset_index().rename(columns={'bowler_name': 'player_name', 'bowler_id': 'player_id', 'avg_rrr_faced': 'avg_rrr_defended'})
bowl_agg = bowl_agg.merge(inn2_defended, on=['player_id', 'player_name'], how='left')
bowl_agg['avg_rrr_defended'] = bowl_agg['avg_rrr_defended'].fillna(league_econ)
bowl_agg['low_total_multiplier'] = np.maximum(0, league_econ - bowl_agg['avg_rrr_defended'])

bowl_agg['bowl_pressure_impact'] = (bowl_agg['wickets'] * runs_per_wkt * (bowl_agg['lone_wolf_multiplier'] * 0.15 + bowl_agg['low_total_multiplier'] * 0.15)).fillna(0).round(2)

# Assign nationality
bat_agg['nationality'] = bat_agg['player_name'].map(known_nats).fillna(bat_agg['player_name'].map(player_nat_map)).fillna('Overseas')
bowl_agg['nationality'] = bowl_agg['player_name'].map(known_nats).fillna(bowl_agg['player_name'].map(player_nat_map)).fillna('Overseas')

bat_agg['is_pakistani'] = bat_agg['nationality'] == 'Pakistan'
bowl_agg['is_pakistani'] = bowl_agg['nationality'] == 'Pakistan'

# Active / Retired check
active_retired = {'Ambati Rayudu', 'Dinesh Karthik', 'Shikhar Dhawan', 'Kieron Pollard', 'Robin Uthappa', 'Eoin Morgan', 'Dwayne Bravo', 'Suresh Raina', 'Murali Vijay', 'Amit Mishra'}
bat_agg['is_retired'] = bat_agg['player_name'].isin(active_retired)
bowl_agg['is_retired'] = bowl_agg['player_name'].isin(active_retired)

# Rank & Percentile computation across qualified players (>= 50 balls)
bat_qual = bat_agg[bat_agg['balls_faced'] >= 50].copy()
bowl_qual = bowl_agg[bowl_agg['total_balls'] >= 50].copy()

bat_agg['combined_score'] = bat_agg['bat_chase_impact'].round(2)
bowl_agg['combined_score'] = bowl_agg['bowl_pressure_impact'].round(2)

bat_agg['pres_metric'] = bat_agg['pressure_sr']
bat_agg['base_metric'] = bat_agg['overall_sr']
bat_agg['total_pressure_balls'] = bat_agg['pressure_balls']
bat_agg['ipl_balls'] = bat_agg['ipl_balls']
bat_agg['t20i_balls'] = bat_agg['t20i_balls']

bowl_agg['pres_metric'] = bowl_agg['pressure_econ']
bowl_agg['base_metric'] = bowl_agg['economy']
bowl_agg['total_pressure_balls'] = bowl_agg['pressure_balls']
bowl_agg['pres_wkts'] = bowl_agg['pressure_wkts']
bowl_agg['ipl_balls'] = bowl_agg['ipl_balls']
bowl_agg['t20i_balls'] = bowl_agg['t20i_balls']

# Replace NaN with None
bat_json = bat_agg.replace({np.nan: None}).to_dict(orient='records')
bowl_json = bowl_agg.replace({np.nan: None}).to_dict(orient='records')

final_payload = {
    'batters': bat_json,
    'bowlers': bowl_json,
    'metadata': {
        'total_deliveries': len(df),
        'league_economy': round(league_econ, 2),
        'runs_per_wicket': round(runs_per_wkt, 2),
        'formula': 'Exact Apex Engine QUWROF Unified Pressure (V11/V14)'
    }
}

with open('d:/ipl-rating/ipl/public/pressure_data.json', 'w') as f:
    json.dump(final_payload, f, indent=2)

print(f"Generated {len(bat_json)} batters and {len(bowl_json)} bowlers in pressure_data.json successfully!")
