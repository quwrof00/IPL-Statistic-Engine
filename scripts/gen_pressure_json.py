import pandas as pd, json, math

bat = pd.read_csv(r'd:\ipl-rating\final_batter_ratings.csv')
bowl = pd.read_csv(r'd:\ipl-rating\final_bowler_ratings.csv')
bbb = pd.read_csv(r'd:\ipl-rating\enriched_bbb.csv', low_memory=False)
ctpm = pd.read_csv(r'c:\Users\Shourya\Downloads\6af458274c1e8_data_pack\Data Pack\competition_team_player_mapping.csv')

# Pakistani players
pak_names = set(ctpm[ctpm.team_name.str.contains('Pakistan', case=False, na=False)].player_name.unique())

bat['is_pak'] = bat['striker_name'].isin(pak_names)
bowl['is_pak'] = bowl['bowler_name'].isin(pak_names)

def to_bool(s):
    return str(s).strip() in ('True', '1', 'true')

bbb['is_legal'] = bbb['is_legal'].apply(to_bool)
bbb['is_pressure'] = bbb['is_pressure'].apply(to_bool)
bbb['is_wicket'] = bbb['is_wicket'].apply(to_bool)
bbb['is_four'] = bbb['is_four'].apply(to_bool)
bbb['is_six'] = bbb['is_six'].apply(to_bool)
bbb['bowl_runs'] = bbb['runs'] + bbb['extras1_runs'].fillna(0)
bbb['is_dot'] = bbb['is_legal'] & (bbb['runs'] == 0) & (~bbb['is_wicket'])

ipl_match_ids = set(bbb[bbb['comp_name'].str.contains('IPL', case=False, na=False)]['match_id'].unique())
bbb['format_tag'] = bbb['match_id'].apply(lambda x: 'IPL' if x in ipl_match_ids else 'T20I')

# ---- BATTER enrichment ----
legal_bat = bbb[bbb.is_legal]
pres_bat = legal_bat[legal_bat.is_pressure].groupby('striker_name').agg(
    total_pressure_balls=('is_legal','sum'),
    pressure_matches=('match_id','nunique'),
    pres_runs=('runs','sum'),
    pres_wkts=('is_wicket','sum'),
    pres_fours=('is_four','sum'),
    pres_sixes=('is_six','sum'),
    pres_dots=('is_dot','sum'),
).reset_index()
pres_bat['pres_SR'] = (pres_bat['pres_runs'] / pres_bat['total_pressure_balls'] * 100).round(1)
pres_bat['pres_avg'] = (pres_bat['pres_runs'] / pres_bat['pres_wkts'].replace(0, 1)).round(1)
pres_bat['pres_dot_pct'] = (pres_bat['pres_dots'] / pres_bat['total_pressure_balls'] * 100).round(1)

all_bat = legal_bat.groupby('striker_name').agg(
    total_balls=('is_legal','sum'),
    total_runs=('runs','sum'),
    total_wkts=('is_wicket','sum'),
).reset_index()
all_bat['base_SR'] = (all_bat['total_runs'] / all_bat['total_balls'] * 100).round(1)
all_bat['base_avg'] = (all_bat['total_runs'] / all_bat['total_wkts'].replace(0, 1)).round(1)

bat = bat.merge(pres_bat, on='striker_name', how='left')
bat = bat.merge(all_bat, on='striker_name', how='left')
bat_full = bat.dropna(subset=['combined']).sort_values('combined', ascending=False).reset_index(drop=True)
bat_full['rank'] = bat_full.index + 1

# ---- BOWLER enrichment ----
legal_bowl = bbb[bbb.is_legal]
pres_bowl = legal_bowl[legal_bowl.is_pressure].groupby('bowler_name').agg(
    total_pressure_balls=('is_legal','sum'),
    pressure_matches=('match_id','nunique'),
    pres_runs=('bowl_runs','sum'),
    pres_wkts=('is_wicket','sum'),
    pres_dots=('is_dot','sum'),
).reset_index()
pres_bowl['pres_econ'] = (pres_bowl['pres_runs'] / pres_bowl['total_pressure_balls'] * 6).round(2)
pres_bowl['pres_wkt_rate'] = (pres_bowl['pres_wkts'] / pres_bowl['total_pressure_balls'] * 6).round(3)
pres_bowl['pres_dot_pct'] = (pres_bowl['pres_dots'] / pres_bowl['total_pressure_balls'] * 100).round(1)

all_bowl = legal_bowl.groupby('bowler_name').agg(
    total_balls_b=('is_legal','sum'),
    total_runs_c=('bowl_runs','sum'),
    total_wkts_b=('is_wicket','sum'),
).reset_index()
all_bowl['base_econ'] = (all_bowl['total_runs_c'] / all_bowl['total_balls_b'] * 6).round(2)

bowl = bowl.merge(pres_bowl, on='bowler_name', how='left')
bowl = bowl.merge(all_bowl, on='bowler_name', how='left')
bowl_full = bowl.dropna(subset=['combined']).sort_values('combined', ascending=False).reset_index(drop=True)
bowl_full['rank'] = bowl_full.index + 1

def safe(v, digits=3):
    if v is None: return None
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f): return None
        return round(f, digits)
    except: return None

def bat_row(r):
    return {
        'rank': int(r['rank']),
        'name': str(r['striker_name']),
        'is_pak': bool(r['is_pak']),
        'combined': safe(r.get('combined')),
        'BPR_ipl':  safe(r.get('BPR_ipl')),
        'BPR_t20i': safe(r.get('BPR_t20i')),
        'total_pressure_balls': int(r['total_pressure_balls']) if not pd.isna(r.get('total_pressure_balls', float('nan'))) else 0,
        'pressure_matches': int(r['pressure_matches']) if not pd.isna(r.get('pressure_matches', float('nan'))) else 0,
        'pres_SR':   safe(r.get('pres_SR'), 1),
        'base_SR':   safe(r.get('base_SR'), 1),
        'pres_avg':  safe(r.get('pres_avg'), 1),
        'base_avg':  safe(r.get('base_avg'), 1),
        'pres_dot_pct': safe(r.get('pres_dot_pct'), 1),
        'pres_runs': int(r['pres_runs']) if not pd.isna(r.get('pres_runs', float('nan'))) else 0,
        'pres_wkts': int(r['pres_wkts']) if not pd.isna(r.get('pres_wkts', float('nan'))) else 0,
    }

def bowl_row(r):
    return {
        'rank': int(r['rank']),
        'name': str(r['bowler_name']),
        'is_pak': bool(r['is_pak']),
        'combined': safe(r.get('combined')),
        'BowPR_ipl':  safe(r.get('BowPR_ipl')),
        'BowPR_t20i': safe(r.get('BowPR_t20i')),
        'total_pressure_balls': int(r['total_pressure_balls']) if not pd.isna(r.get('total_pressure_balls', float('nan'))) else 0,
        'pressure_matches': int(r['pressure_matches']) if not pd.isna(r.get('pressure_matches', float('nan'))) else 0,
        'pres_econ':    safe(r.get('pres_econ'), 2),
        'base_econ':    safe(r.get('base_econ'), 2),
        'pres_wkt_rate': safe(r.get('pres_wkt_rate'), 3),
        'pres_dot_pct': safe(r.get('pres_dot_pct'), 1),
        'pres_wkts': int(r['pres_wkts']) if not pd.isna(r.get('pres_wkts', float('nan'))) else 0,
    }

payload = {
    'batters': [bat_row(bat_full.iloc[i]) for i in range(min(150, len(bat_full)))],
    'bowlers': [bowl_row(bowl_full.iloc[i]) for i in range(min(150, len(bowl_full)))]
}

with open(r'd:\ipl-rating\ipl\public\pressure_data.json', 'w') as f:
    json.dump(payload, f, indent=2)

print("pressure_data.json written.")
print("Top 10 batters:")
for b in payload['batters'][:10]:
    print(f"  #{b['rank']} {b['name']} (PAK:{b['is_pak']}) combined={b['combined']} pres_SR={b['pres_SR']} base_SR={b['base_SR']} balls={b['total_pressure_balls']}")
print("\nTop 10 bowlers:")
for b in payload['bowlers'][:10]:
    print(f"  #{b['rank']} {b['name']} (PAK:{b['is_pak']}) combined={b['combined']} pres_econ={b['pres_econ']} base_econ={b['base_econ']} balls={b['total_pressure_balls']}")
