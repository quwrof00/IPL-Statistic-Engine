"""
Full RR IPL 2026 Gap Analysis
- Squad identification
- Phase-wise batting & bowling stats (PP / Middle / Death)
- Win vs Loss breakdown
- Pressure performance
- Gap identification for 2027 auction targeting
"""

import pandas as pd
import numpy as np
import json

pd.set_option('future.no_silent_downcasting', True)

RR_TEAM_ID = 3
CTPM_PATH = r'C:\Users\Shourya\Downloads\6af458274c1e8_data_pack\Data Pack\competition_team_player_mapping.csv'

print("=" * 60)
print("RR IPL 2026 GAP ANALYSIS")
print("=" * 60)

# ── Load Data ─────────────────────────────────────────────────────────────────
df = pd.read_csv('d:/ipl-rating/enriched_bbb.csv', low_memory=False)
ctpm = pd.read_csv(CTPM_PATH)

# ── 1. RR 2026 Squad ──────────────────────────────────────────────────────────
rr_squad_ctpm = ctpm[(ctpm['comp_id'] == 3298) & (ctpm['team_id'] == RR_TEAM_ID)]
print(f"\n[1] RR 2026 Squad ({len(rr_squad_ctpm)} players):")
print(rr_squad_ctpm[['player_id', 'player_name']].to_string(index=False))

rr_player_ids = set(rr_squad_ctpm['player_id'].tolist())
rr_player_names = dict(zip(rr_squad_ctpm['player_id'], rr_squad_ctpm['player_name']))

# ── 2. IPL 2026 Matches ───────────────────────────────────────────────────────
ipl26 = df[df['comp_id'] == 3298].copy()

# Classify deliveries as RR batting or RR bowling
ipl26['rr_batting'] = ipl26['batting_team_id'] == RR_TEAM_ID
ipl26['rr_bowling'] = ipl26['bowling_team_id'] == RR_TEAM_ID

# Match-level: find RR matches and outcomes
rr_matches_df = ipl26[(ipl26['batting_team_id'] == RR_TEAM_ID) | (ipl26['bowling_team_id'] == RR_TEAM_ID)]
rr_match_ids = rr_matches_df['match_id'].unique()
print(f"\n[2] RR played {len(rr_match_ids)} matches in IPL 2026")

# Win/Loss per match
match_outcomes = ipl26.groupby('match_id').agg(
    win_team_id=('win_team_id', 'first'),
    batting_teams=('batting_team_id', lambda x: x.unique().tolist()),
).reset_index()

rr_match_outcomes = match_outcomes[match_outcomes['match_id'].isin(rr_match_ids)].copy()
rr_match_outcomes['rr_won'] = rr_match_outcomes['win_team_id'] == RR_TEAM_ID
rr_match_outcomes['result'] = rr_match_outcomes['rr_won'].map({True: 'Win', False: 'Loss'})

wins = rr_match_outcomes['rr_won'].sum()
losses = len(rr_match_outcomes) - wins
print(f"   W{wins} L{losses}")

win_match_ids = set(rr_match_outcomes[rr_match_outcomes['rr_won']]['match_id'].tolist())
loss_match_ids = set(rr_match_outcomes[~rr_match_outcomes['rr_won']]['match_id'].tolist())

# ── Helper: Phase-wise stats ──────────────────────────────────────────────────
def phase_batting_stats(deliveries):
    """Given RR batting deliveries, return phase-wise stats."""
    d = deliveries.copy()
    d['phase_label'] = pd.cut(d['overid'], bins=[0, 6, 15, 20], labels=['Powerplay', 'Middle', 'Death'])
    d['is_dot'] = (d['runs'] == 0) & (d['is_wide'] == 0) & (d['is_noball'] == 0)
    d['is_boundary'] = (d['is_four'] == 1) | (d['is_six'] == 1)

    result = {}
    for phase, grp in d.groupby('phase_label', observed=True):
        legal = grp[grp['is_legal'] == 1]
        balls = len(legal)
        runs_scored = legal['runs'].sum()
        wickets = legal['is_wicket'].sum()
        dots = grp['is_dot'].sum()
        boundaries = legal['is_boundary'].sum()
        result[phase] = {
            'balls': int(balls),
            'runs': int(runs_scored),
            'wickets': int(wickets),
            'SR': round(runs_scored / balls * 100, 1) if balls > 0 else 0,
            'dot_pct': round(dots / max(len(grp[grp['is_legal'] == 1]), 1) * 100, 1),
            'boundary_pct': round(boundaries / balls * 100, 1) if balls > 0 else 0,
        }
    return result

def phase_bowling_stats(deliveries):
    """Given RR bowling deliveries, return phase-wise economy stats."""
    d = deliveries.copy()
    d['phase_label'] = pd.cut(d['overid'], bins=[0, 6, 15, 20], labels=['Powerplay', 'Middle', 'Death'])
    d['is_dot'] = (d['runs'] == 0) & (d['is_wide'] == 0) & (d['is_noball'] == 0)

    result = {}
    for phase, grp in d.groupby('phase_label', observed=True):
        legal = grp[grp['is_legal'] == 1]
        balls = len(legal)
        runs_conceded = legal['runs'].sum() + grp['extras1_runs'].sum() + grp['extras_2_runs'].sum()
        wickets = legal['is_wicket'].sum()
        dots = grp['is_dot'].sum()
        result[phase] = {
            'balls': int(balls),
            'runs_conceded': int(runs_conceded),
            'wickets': int(wickets),
            'econ': round(runs_conceded / balls * 6, 2) if balls > 0 else 0,
            'dot_pct': round(dots / max(len(grp[grp['is_legal'] == 1]), 1) * 100, 1),
            'wkt_per_6': round(wickets / balls * 6, 2) if balls > 0 else 0,
        }
    return result

# ── 3. Overall Phase Stats ────────────────────────────────────────────────────
rr_bat = ipl26[ipl26['rr_batting']]
rr_bowl = ipl26[ipl26['rr_bowling']]

print("\n[3] RR BATTING BY PHASE (all matches):")
bat_stats = phase_batting_stats(rr_bat)
for phase, s in bat_stats.items():
    print(f"   {phase:12s}: SR={s['SR']:5.1f} | Dot%={s['dot_pct']:4.1f}% | Bdry%={s['boundary_pct']:4.1f}% | Wkts={s['wickets']} in {s['balls']} balls")

print("\n[3] RR BOWLING BY PHASE (all matches):")
bowl_stats = phase_bowling_stats(rr_bowl)
for phase, s in bowl_stats.items():
    print(f"   {phase:12s}: Econ={s['econ']:4.2f} | Dot%={s['dot_pct']:4.1f}% | Wkts={s['wickets']} in {s['balls']} balls")

# ── 4. Win vs Loss Phase Breakdown ────────────────────────────────────────────
print("\n[4] WIN vs LOSS BREAKDOWN BY PHASE:")

for label, match_set in [("WIN", win_match_ids), ("LOSS", loss_match_ids)]:
    subset = ipl26[ipl26['match_id'].isin(match_set)]
    b = subset[subset['rr_batting']]
    bw = subset[subset['rr_bowling']]

    bat = phase_batting_stats(b)
    bowl = phase_bowling_stats(bw)

    print(f"\n  -- {label} ({len(match_set)} matches) --")
    print(f"  BATTING:   PP SR={bat.get('Powerplay',{}).get('SR',0):5.1f} | Mid SR={bat.get('Middle',{}).get('SR',0):5.1f} | Death SR={bat.get('Death',{}).get('SR',0):5.1f}")
    print(f"  BOWLING:   PP Econ={bowl.get('Powerplay',{}).get('econ',0):4.2f} | Mid Econ={bowl.get('Middle',{}).get('econ',0):4.2f} | Death Econ={bowl.get('Death',{}).get('econ',0):4.2f}")
    print(f"  BOWL WKTS: PP={bowl.get('Powerplay',{}).get('wickets',0)} | Mid={bowl.get('Middle',{}).get('wickets',0)} | Death={bowl.get('Death',{}).get('wickets',0)}")

# ── 5. Pressure Performance ───────────────────────────────────────────────────
print("\n[5] PRESSURE ANALYSIS (RR):")

rr_bat_pres = rr_bat[rr_bat['is_pressure']]
rr_bowl_pres = rr_bowl[rr_bowl['is_pressure']]

for label, d_all, d_pres, role in [
    ("BATTING", rr_bat, rr_bat_pres, "batting"),
    ("BOWLING", rr_bowl, rr_bowl_pres, "bowling"),
]:
    legal_all = d_all[d_all['is_legal'] == 1]
    legal_pres = d_pres[d_pres['is_legal'] == 1]
    if role == "batting":
        overall_sr = legal_all['runs'].sum() / max(len(legal_all), 1) * 100
        pres_sr = legal_pres['runs'].sum() / max(len(legal_pres), 1) * 100
        print(f"   {label}: Baseline SR={overall_sr:.1f} | Pressure SR={pres_sr:.1f} | Delta={pres_sr-overall_sr:+.1f}")
    else:
        overall_econ = (legal_all['runs'].sum() + d_all['extras1_runs'].sum() + d_all['extras_2_runs'].sum()) / max(len(legal_all), 1) * 6
        pres_econ = (legal_pres['runs'].sum() + d_pres['extras1_runs'].sum() + d_pres['extras_2_runs'].sum()) / max(len(legal_pres), 1) * 6
        print(f"   {label}: Baseline Econ={overall_econ:.2f} | Pressure Econ={pres_econ:.2f} | Delta={pres_econ-overall_econ:+.2f}")

# ── 6. Individual Player Stats ────────────────────────────────────────────────
print("\n[6] INDIVIDUAL RR PLAYER STATS (IPL 2026):")

# Batters (must have batted for RR)
rr_batters = rr_bat[rr_bat['striker_id'].isin(rr_player_ids)].copy()
rr_batters_legal = rr_batters[rr_batters['is_legal'] == 1]

batter_stats = rr_batters_legal.groupby(['striker_id', 'striker_name']).agg(
    balls=('runs', 'count'),
    runs=('runs', 'sum'),
    fours=('is_four', 'sum'),
    sixes=('is_six', 'sum'),
    dismissals=('is_wicket', 'sum'),
).reset_index()
batter_stats['SR'] = (batter_stats['runs'] / batter_stats['balls'] * 100).round(1)

# Pressure batting
rr_bat_pres_ind = rr_batters[rr_batters['is_pressure'] & (rr_batters['is_legal'] == 1)]
pres_bat = rr_bat_pres_ind.groupby('striker_id').agg(
    pres_balls=('runs', 'count'),
    pres_runs=('runs', 'sum'),
).reset_index()
pres_bat['pres_SR'] = (pres_bat['pres_runs'] / pres_bat['pres_balls'] * 100).round(1)

batter_stats = batter_stats.merge(pres_bat, on='striker_id', how='left')
batter_stats = batter_stats.sort_values('runs', ascending=False)

print("\n  BATTERS:")
print(f"  {'Player':<25} {'Balls':>5} {'Runs':>5} {'SR':>6} {'PresBalls':>9} {'PresRuns':>8} {'PresSR':>7}")
for _, r in batter_stats.iterrows():
    pb = int(r['pres_balls']) if pd.notna(r.get('pres_balls')) else 0
    pr = int(r['pres_runs']) if pd.notna(r.get('pres_runs')) else 0
    ps = float(r['pres_SR']) if pd.notna(r.get('pres_SR')) else 0.0
    print(f"  {r['striker_name']:<25} {int(r['balls']):>5} {int(r['runs']):>5} {r['SR']:>6.1f} {pb:>9} {pr:>8} {ps:>7.1f}")

# Bowlers
rr_bowlers = rr_bowl[rr_bowl['bowler_id'].isin(rr_player_ids)].copy()
rr_bowlers_legal = rr_bowlers[rr_bowlers['is_legal'] == 1]

bowler_stats = rr_bowlers_legal.groupby(['bowler_id', 'bowler_name']).agg(
    balls=('runs', 'count'),
    runs_c=('runs', 'sum'),
    wkts=('is_wicket', 'sum'),
).reset_index()
# add extras
ext = rr_bowlers.groupby('bowler_id').agg(
    ext_runs=('extras1_runs', 'sum'),
    ext2=('extras_2_runs', 'sum'),
).reset_index()
bowler_stats = bowler_stats.merge(ext, on='bowler_id', how='left').fillna(0)
bowler_stats['total_runs'] = bowler_stats['runs_c'] + bowler_stats['ext_runs'] + bowler_stats['ext2']
bowler_stats['econ'] = (bowler_stats['total_runs'] / bowler_stats['balls'] * 6).round(2)

# Pressure bowling
rr_bowl_pres_ind = rr_bowlers[rr_bowlers['is_pressure'] & (rr_bowlers['is_legal'] == 1)]
pres_bowl = rr_bowl_pres_ind.groupby('bowler_id').agg(
    pres_balls=('runs', 'count'),
    pres_runs=('runs', 'sum'),
    pres_wkts=('is_wicket', 'sum'),
).reset_index()
pres_bowl['pres_econ'] = (pres_bowl['pres_runs'] / pres_bowl['pres_balls'] * 6).round(2)

bowler_stats = bowler_stats.merge(pres_bowl, on='bowler_id', how='left')
bowler_stats = bowler_stats.sort_values('wkts', ascending=False)

print("\n  BOWLERS:")
print(f"  {'Player':<25} {'Balls':>5} {'Wkts':>5} {'Econ':>6} {'PresBalls':>9} {'PresWkts':>8} {'PresEcon':>8}")
for _, r in bowler_stats.iterrows():
    pb = int(r['pres_balls']) if pd.notna(r.get('pres_balls')) else 0
    pw = int(r['pres_wkts']) if pd.notna(r.get('pres_wkts')) else 0
    pe = float(r['pres_econ']) if pd.notna(r.get('pres_econ')) else 0.0
    print(f"  {r['bowler_name']:<25} {int(r['balls']):>5} {int(r['wkts']):>5} {r['econ']:>6.2f} {pb:>9} {pw:>8} {pe:>8.2f}")

# ── 7. Death Over Deep Dive ───────────────────────────────────────────────────
print("\n[7] DEATH OVER (16-20) DEEP DIVE:")

rr_bowl_death = rr_bowl[(rr_bowl['overid'] >= 16) & (rr_bowl['is_legal'] == 1)]
death_bowler = rr_bowl_death.groupby('bowler_name').agg(
    balls=('runs', 'count'),
    runs=('runs', 'sum'),
    wkts=('is_wicket', 'sum'),
).reset_index()
death_bowler['econ'] = (death_bowler['runs'] / death_bowler['balls'] * 6).round(2)
death_bowler = death_bowler[death_bowler['balls'] >= 6].sort_values('econ')
print("  Death bowlers (by econ):")
for _, r in death_bowler.iterrows():
    print(f"    {r['bowler_name']:<25} {int(r['balls']):>4} balls | Wkts={int(r['wkts'])} | Econ={r['econ']:.2f}")

# Death batting
rr_bat_death = rr_bat[(rr_bat['overid'] >= 16) & (rr_bat['is_legal'] == 1)]
death_batter = rr_bat_death.groupby('striker_name').agg(
    balls=('runs', 'count'),
    runs=('runs', 'sum'),
    sixes=('is_six', 'sum'),
).reset_index()
death_batter['SR'] = (death_batter['runs'] / death_batter['balls'] * 100).round(1)
death_batter = death_batter[death_batter['balls'] >= 10].sort_values('SR', ascending=False)
print("  Death batters (by SR, min 10 balls):")
for _, r in death_batter.iterrows():
    print(f"    {r['striker_name']:<25} {int(r['balls']):>4} balls | Runs={int(r['runs'])} | SR={r['SR']:.1f}")

# ── 8. Powerplay Bowling ──────────────────────────────────────────────────────
print("\n[8] POWERPLAY BOWLING (Overs 1-6):")
rr_bowl_pp = rr_bowl[(rr_bowl['overid'] <= 6) & (rr_bowl['is_legal'] == 1)]
pp_bowler = rr_bowl_pp.groupby('bowler_name').agg(
    balls=('runs', 'count'),
    runs=('runs', 'sum'),
    wkts=('is_wicket', 'sum'),
).reset_index()
pp_bowler['econ'] = (pp_bowler['runs'] / pp_bowler['balls'] * 6).round(2)
pp_bowler['sr_wkt'] = (pp_bowler['balls'] / pp_bowler['wkts'].replace(0, np.nan)).round(1)
pp_bowler = pp_bowler[pp_bowler['balls'] >= 6].sort_values('wkts', ascending=False)
print("  PP bowlers:")
for _, r in pp_bowler.iterrows():
    print(f"    {r['bowler_name']:<25} {int(r['balls']):>4} balls | Wkts={int(r['wkts'])} | Econ={r['econ']:.2f}")

# ── 9. Chase Performance ─────────────────────────────────────────────────────
print("\n[9] CHASE (2nd innings) vs DEFEND analysis:")
rr_bat_inn2 = rr_bat[rr_bat['innings'] == 2]
rr_bat_inn1 = rr_bat[rr_bat['innings'] == 1]

for label, sub in [("Chasing (Inn2)", rr_bat_inn2), ("Defending (Inn1)", rr_bat_inn1)]:
    legal = sub[sub['is_legal'] == 1]
    sr = legal['runs'].sum() / max(len(legal), 1) * 100
    pres = sub[sub['is_pressure'] & (sub['is_legal'] == 1)]
    pres_sr = pres['runs'].sum() / max(len(pres), 1) * 100
    print(f"  {label}: SR={sr:.1f} | Pressure SR={pres_sr:.1f}")

# Save a compact summary dict
summary = {
    'squad': rr_squad_ctpm[['player_id','player_name']].to_dict('records'),
    'record': {'matches': len(rr_match_ids), 'wins': int(wins), 'losses': int(losses)},
    'phase_batting': {k: v for k, v in bat_stats.items()},
    'phase_bowling': {k: v for k, v in bowl_stats.items()},
    'win_bat_phase': {phase: {'SR': 0} for phase in ['Powerplay','Middle','Death']},
    'loss_bat_phase': {phase: {'SR': 0} for phase in ['Powerplay','Middle','Death']},
}

with open('d:/ipl-rating/scripts/rr_gap_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print("\n[DONE] Summary saved to d:/ipl-rating/scripts/rr_gap_summary.json")
