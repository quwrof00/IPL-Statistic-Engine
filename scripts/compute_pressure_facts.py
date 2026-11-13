"""
Calculate empirical pressure metrics from enriched_bbb.csv
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv('d:/ipl-rating/enriched_bbb.csv', low_memory=False)

total_del = len(df)
pres_del = int(df['is_pressure'].sum())
pres_pct = round(pres_del / total_del * 100, 1)

# Legal balls
p_bat = df[df['is_pressure'] & (df['is_legal'] == 1)]
np_bat = df[(~df['is_pressure']) & (df['is_legal'] == 1)]

p_sr = round(float(p_bat['runs'].sum() / len(p_bat) * 100), 2)
np_sr = round(float(np_bat['runs'].sum() / len(np_bat) * 100), 2)
p_dot = round(float((p_bat['runs'] == 0).mean() * 100), 2)
np_dot = round(float((np_bat['runs'] == 0).mean() * 100), 2)
p_wkt = round(float(p_bat['is_wicket'].mean() * 100), 2)
np_wkt = round(float(np_bat['is_wicket'].mean() * 100), 2)
wkt_multiplier = round(p_wkt / np_wkt, 2)

# Chases
m_inn2 = df[df['innings'] == 2].groupby('match_id').agg(
    target=('target', 'first'),
    max_rrr=('RRR', 'max'),
    win_team_id=('win_team_id', 'first'),
    bat_team_id=('batting_team_id', 'first')
).reset_index()

m_inn2['chase_won'] = m_inn2['win_team_id'] == m_inn2['bat_team_id']
total_chases = len(m_inn2)
won_chases = int(m_inn2['chase_won'].sum())
chase_win_pct = round(won_chases / total_chases * 100, 1)

rrr_10_matches = set(df[(df['innings'] == 2) & (df['RRR'] > 10)]['match_id'].unique())
rrr_12_matches = set(df[(df['innings'] == 2) & (df['RRR'] > 12)]['match_id'].unique())

c_10 = m_inn2[m_inn2['match_id'].isin(rrr_10_matches)]
c_12 = m_inn2[m_inn2['match_id'].isin(rrr_12_matches)]

win_10_pct = round(float(c_10['chase_won'].mean() * 100), 1)
win_12_pct = round(float(c_12['chase_won'].mean() * 100), 1)

# Death overs (16-20)
death = df[df['overid'] >= 16]
death_total = len(death)
death_pres = int(death['is_pressure'].sum())
death_pres_pct = round(death_pres / death_total * 100, 1)

# Breakdown by phase of pressure deliveries
phase_counts = df[df['is_pressure']]['phase'].value_counts().to_dict()

pressure_facts = {
    'total_deliveries': total_del,
    'pressure_deliveries': pres_del,
    'pressure_pct': pres_pct,
    'pressure_sr': p_sr,
    'baseline_sr': np_sr,
    'pressure_dot_pct': p_dot,
    'baseline_dot_pct': np_dot,
    'pressure_wicket_rate': p_wkt,
    'baseline_wicket_rate': np_wkt,
    'wkt_risk_multiplier': wkt_multiplier,
    'total_chases': total_chases,
    'chase_baseline_win_pct': chase_win_pct,
    'rrr_10_win_pct': win_10_pct,
    'rrr_12_win_pct': win_12_pct,
    'death_total_deliveries': death_total,
    'death_pressure_deliveries': death_pres,
    'death_pressure_pct': death_pres_pct,
    'phase_distribution': phase_counts
}

print(json.dumps(pressure_facts, indent=2))

with open('d:/ipl-rating/scripts/pressure_facts.json', 'w') as f:
    json.dump(pressure_facts, f, indent=2)
