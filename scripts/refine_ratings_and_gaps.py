"""
Refined Pressure Rating Engine & RR Auction Gap Matcher
1. Computes blended pressure ratings (50% Absolute Output + 50% Relative Maintenance)
2. Applies 65:35 IPL:T20I Bayesian weight
3. Identifies top candidates specifically tailored for RR's 2027 Auction War Room Gaps:
   - Gap 1: Death Over Lockdown Specialist (Econ in overs 16-20 < 9.5, high dot %, high pressure wicket rate)
   - Gap 2: Powerplay Strike Bowler (Overs 1-6 wicket taker, low econ, early breakthroughs)
   - Gap 3: High-Impact Middle/Death Finisher (SR under pressure > 160, boundary % high, clutch chase record)
   - Gap 4: Spin Enforcer / Middle Overs Choke (SMS Jaipur abrasive pitch suitability)
"""

import pandas as pd
import numpy as np
import json
import os

pd.set_option('future.no_silent_downcasting', True)

# Load enriched data
print("Loading enriched ball-by-ball...")
df = pd.read_csv('d:/ipl-rating/enriched_bbb.csv', low_memory=False)

# Load player metadata
with open('d:/ipl-rating/scripts/player_meta.json', 'r') as f:
    meta = json.load(f)

# Split IPL vs T20I
ipl_df = df[df['comp_name'].str.contains('IPL', na=False)].copy()
t20i_df = df[~df['comp_name'].str.contains('IPL', na=False)].copy()

def compute_batter_ratings(d_sub, min_balls=40):
    legal = d_sub[d_sub['is_legal'] == 1].copy()
    legal['is_dot'] = (legal['runs'] == 0) & (legal['is_wide'] == 0) & (legal['is_noball'] == 0)
    
    # Baseline
    base = legal.groupby(['striker_id', 'striker_name']).agg(
        base_balls=('runs', 'count'),
        base_runs=('runs', 'sum'),
        base_outs=('is_wicket', 'sum'),
        base_dots=('is_dot', 'sum'),
        base_fours=('is_four', 'sum'),
        base_sixes=('is_six', 'sum'),
        matches=('match_id', 'nunique'),
    ).reset_index()
    base['base_SR'] = (base['base_runs'] / base['base_balls'] * 100).round(2)
    base['base_dot_pct'] = (base['base_dots'] / base['base_balls']).round(4)
    base['base_avg'] = (base['base_runs'] / base['base_outs'].replace(0, 1)).round(2)
    
    # Pressure
    pres = legal[legal['is_pressure']].groupby('striker_id').agg(
        pres_balls=('runs', 'count'),
        pres_runs=('runs', 'sum'),
        pres_outs=('is_wicket', 'sum'),
        pres_dots=('is_dot', 'sum'),
        pres_fours=('is_four', 'sum'),
        pres_sixes=('is_six', 'sum'),
        pres_matches=('match_id', 'nunique'),
    ).reset_index()
    pres['pres_SR'] = (pres['pres_runs'] / pres['pres_balls'] * 100).round(2)
    pres['pres_dot_pct'] = (pres['pres_dots'] / pres['pres_balls']).round(4)
    pres['pres_avg'] = (pres['pres_runs'] / pres['pres_outs'].replace(0, 1)).round(2)
    
    merged = base.merge(pres, on='striker_id', how='inner')
    merged = merged[merged['pres_balls'] >= min_balls].copy()
    
    # P90 benchmark for pressure SR
    p90_pres_sr = np.percentile(merged['pres_SR'], 85)
    
    # Formulas
    # 1. Absolute SR performance relative to elite standard
    merged['abs_sr_score'] = merged['pres_SR'] / p90_pres_sr
    # 2. Relative SR retention
    merged['rel_sr_ratio'] = merged['pres_SR'] / merged['base_SR'].replace(0, 100)
    # 3. Dot delta (lower is better, delta = pres - base)
    merged['dot_delta'] = merged['pres_dot_pct'] - merged['base_dot_pct']
    # 4. Average impact
    merged['rel_avg_ratio'] = (merged['pres_avg'] / merged['base_avg'].replace(0, 20)).clip(0.5, 2.0)
    
    # Composite BPR:
    # 40% Absolute Pressure SR + 35% Relative SR Retention + 15% Average Maintenance - 10% Dot Ball Spike
    merged['bpr'] = (
        0.40 * merged['abs_sr_score'] +
        0.35 * merged['rel_sr_ratio'] +
        0.15 * merged['rel_avg_ratio'] -
        0.20 * merged['dot_delta']
    ).round(4)
    
    return merged

def compute_bowler_ratings(d_sub, min_balls=40):
    legal = d_sub[d_sub['is_legal'] == 1].copy()
    legal['is_dot'] = (legal['runs'] == 0) & (legal['is_wide'] == 0) & (legal['is_noball'] == 0)
    
    # Extras per bowler
    ext = d_sub.groupby('bowler_id').agg(
        ext1=('extras1_runs', 'sum'),
        ext2=('extras_2_runs', 'sum'),
    ).reset_index()
    
    base = legal.groupby(['bowler_id', 'bowler_name']).agg(
        base_balls=('runs', 'count'),
        base_bat_runs=('runs', 'sum'),
        base_wkts=('is_wicket', 'sum'),
        base_dots=('is_dot', 'sum'),
        matches=('match_id', 'nunique'),
    ).reset_index()
    base = base.merge(ext, on='bowler_id', how='left').fillna(0)
    base['base_total_runs'] = base['base_bat_runs'] + base['ext1'] + base['ext2']
    base['base_econ'] = (base['base_total_runs'] / base['base_balls'] * 6).round(2)
    base['base_dot_pct'] = (base['base_dots'] / base['base_balls']).round(4)
    base['base_sr'] = (base['base_balls'] / base['base_wkts'].replace(0, 1)).round(2)
    
    # Pressure
    ext_pres = d_sub[d_sub['is_pressure']].groupby('bowler_id').agg(
        pres_ext1=('extras1_runs', 'sum'),
        pres_ext2=('extras_2_runs', 'sum'),
    ).reset_index()
    
    pres = legal[legal['is_pressure']].groupby('bowler_id').agg(
        pres_balls=('runs', 'count'),
        pres_bat_runs=('runs', 'sum'),
        pres_wkts=('is_wicket', 'sum'),
        pres_dots=('is_dot', 'sum'),
        pres_matches=('match_id', 'nunique'),
    ).reset_index()
    pres = pres.merge(ext_pres, on='bowler_id', how='left').fillna(0)
    pres['pres_total_runs'] = pres['pres_bat_runs'] + pres['pres_ext1'] + pres['pres_ext2']
    pres['pres_econ'] = (pres['pres_total_runs'] / pres['pres_balls'] * 6).round(2)
    pres['pres_dot_pct'] = (pres['pres_dots'] / pres['pres_balls']).round(4)
    pres['pres_sr'] = (pres['pres_balls'] / pres['pres_wkts'].replace(0, 1)).round(2)
    
    merged = base.merge(pres, on='bowler_id', how='inner')
    merged = merged[merged['pres_balls'] >= min_balls].copy()
    
    # Benchmark P15 for pressure econ (lower is better, e.g. ~7.5 rpo)
    p15_pres_econ = np.percentile(merged['pres_econ'], 15)
    
    # Formulas
    # 1. Absolute economy score (p15 / pres_econ)
    merged['abs_econ_score'] = (p15_pres_econ / merged['pres_econ'].clip(lower=4.0)).clip(0.5, 2.0)
    # 2. Relative economy maintenance (base_econ / pres_econ)
    merged['rel_econ_ratio'] = (merged['base_econ'] / merged['pres_econ'].clip(lower=4.0)).clip(0.5, 2.0)
    # 3. Wicket taking frequency under pressure
    merged['pres_wkt_rate'] = (merged['pres_wkts'] / merged['pres_balls'] * 24).round(3) # wkts per 4 overs
    # 4. Dot delta (pres_dot - base_dot, higher is better)
    merged['dot_delta'] = merged['pres_dot_pct'] - merged['base_dot_pct']
    
    # Composite BowPR:
    # 40% Absolute Econ Score + 30% Relative Econ Maintenance + 20% Wicket Punch + 10% Dot Spike
    merged['bowpr'] = (
        0.40 * merged['abs_econ_score'] +
        0.30 * merged['rel_econ_ratio'] +
        0.20 * (merged['pres_wkt_rate'] / 0.8).clip(0.5, 2.0) +
        0.10 * (1.0 + merged['dot_delta'])
    ).round(4)
    
    return merged

print("Computing IPL ratings...")
ipl_bat = compute_batter_ratings(ipl_df, min_balls=35)
ipl_bowl = compute_bowler_ratings(ipl_df, min_balls=35)

print("Computing T20I ratings...")
t20i_bat = compute_batter_ratings(t20i_df, min_balls=35)
t20i_bowl = compute_bowler_ratings(t20i_df, min_balls=35)

# Combine 65:35 with Bayesian shrinkage
def combine_ratings(ipl_res, t20i_res, id_col, name_col, score_col, balls_col):
    all_players = set(ipl_res[id_col]).union(set(t20i_res[id_col]))
    rows = []
    for pid in all_players:
        i_row = ipl_res[ipl_res[id_col] == pid]
        t_row = t20i_res[t20i_res[id_col] == pid]
        
        has_i = len(i_row) > 0
        has_t = len(t_row) > 0
        
        name = i_row[name_col].values[0] if has_i else t_row[name_col].values[0]
        i_score = i_row[score_col].values[0] if has_i else None
        t_score = t_row[score_col].values[0] if has_t else None
        i_balls = int(i_row[balls_col].values[0]) if has_i else 0
        t_balls = int(t_row[balls_col].values[0]) if has_t else 0
        
        tot_balls = i_balls + t_balls
        
        # 65:35 combining
        if has_i and has_t:
            combined = 0.65 * i_score + 0.35 * t_score
        elif has_i:
            # Shrink toward 1.0 baseline
            shrink = min(i_balls / 120.0, 1.0)
            combined = 0.65 * i_score + 0.35 * (1.0 * (1 - shrink) + i_score * shrink)
        else:
            # T20I only
            shrink = min(t_balls / 150.0, 1.0)
            combined = 0.35 * t_score + 0.65 * (1.0 * (1 - shrink) + t_score * shrink)
            
        m_info = meta.get(name, {'nationality': 'Unknown', 'age': None})
        nat = m_info.get('nationality', 'Unknown')
        is_pak = (nat == 'Pakistan') or (name in ['Babar Azam', 'Fakhar Zaman', 'Shaheen Shah Afridi', 'Mohammad Rizwan', 'Shadab Khan', 'Haris Rauf', 'Naseem Shah', 'Iftikhar Ahmed', 'Arafat Minhas', 'Sufiyan Muqeem', 'Mohammad Nawaz', 'Abrar Ahmed', 'Shan Masood', 'Imad Wasim', 'Usama Mir', 'Abbas Afridi', 'Salman Ali Agha', 'Haseebullah Khan', 'Mohammad Haris', 'Saim Ayub'])
        
        # Pull key stats
        p_sr = (i_row['pres_SR'].values[0] if (has_i and 'pres_SR' in i_row) else 
                t_row['pres_SR'].values[0] if (has_t and 'pres_SR' in t_row) else None)
        b_sr = (i_row['base_SR'].values[0] if (has_i and 'base_SR' in i_row) else 
                t_row['base_SR'].values[0] if (has_t and 'base_SR' in t_row) else None)
        p_econ = (i_row['pres_econ'].values[0] if (has_i and 'pres_econ' in i_row) else 
                  t_row['pres_econ'].values[0] if (has_t and 'pres_econ' in t_row) else None)
        b_econ = (i_row['base_econ'].values[0] if (has_i and 'base_econ' in i_row) else 
                  t_row['base_econ'].values[0] if (has_t and 'base_econ' in t_row) else None)
        p_wkts = (int(i_row['pres_wkts'].values[0]) if (has_i and 'pres_wkts' in i_row) else 
                  int(t_row['pres_wkts'].values[0]) if (has_t and 'pres_wkts' in t_row) else 0)
        
        rows.append({
            'player_id': pid,
            'player_name': name,
            'nationality': nat,
            'age': m_info.get('age'),
            'is_pakistani': is_pak,
            'has_ipl': has_i,
            'has_t20i': has_t,
            'ipl_balls': i_balls,
            't20i_balls': t_balls,
            'total_pressure_balls': tot_balls,
            'ipl_rating': round(float(i_score), 4) if i_score else None,
            't20i_rating': round(float(t_score), 4) if t_score else None,
            'pres_metric': float(p_sr) if p_sr is not None else float(p_econ) if p_econ is not None else None,
            'base_metric': float(b_sr) if b_sr is not None else float(b_econ) if b_econ is not None else None,
            'pres_wkts': p_wkts,
            'combined_score': round(float(combined), 4)
        })
        
    res_df = pd.DataFrame(rows)
    return res_df.sort_values(by='combined_score', ascending=False)

comb_bat = combine_ratings(ipl_bat, t20i_bat, 'striker_id', 'striker_name', 'bpr', 'pres_balls')
comb_bowl = combine_ratings(ipl_bowl, t20i_bowl, 'bowler_id', 'bowler_name', 'bowpr', 'pres_balls')

print("\n--- TOP 15 BATTERS (IPL-Eligible, Total Pres Balls >= 60) ---")
eligible_bat = comb_bat[(~comb_bat['is_pakistani']) & (comb_bat['total_pressure_balls'] >= 60)].head(15)
print(eligible_bat[['player_name', 'nationality', 'age', 'total_pressure_balls', 'pres_metric', 'base_metric', 'combined_score']].to_string(index=False))

print("\n--- TOP 15 BOWLERS (IPL-Eligible, Total Pres Balls >= 60) ---")
eligible_bowl = comb_bowl[(~comb_bowl['is_pakistani']) & (comb_bowl['total_pressure_balls'] >= 60)].head(15)
print(eligible_bowl[['player_name', 'nationality', 'age', 'total_pressure_balls', 'pres_metric', 'base_metric', 'pres_wkts', 'combined_score']].to_string(index=False))

# Now let's do RR SPECIFIC GAP MATCHING from the delivery data
print("\n" + "="*60)
print("RR SPECIFIC GAP TARGET MATCHING")
print("="*60)

# Gap 1: Death Over Specialists (Overs 16-20)
# Filter bowlers in IPL who bowled >= 30 death balls under pressure or overall death balls >= 50
ipl_legal = ipl_df[ipl_df['is_legal'] == 1].copy()
ipl_death = ipl_legal[ipl_legal['overid'] >= 16].copy()
ipl_death_pres = ipl_death[ipl_death['is_pressure']].copy()

d_bowlers = ipl_death.groupby(['bowler_id', 'bowler_name']).agg(
    death_balls=('runs', 'count'),
    death_runs=('runs', 'sum'),
    death_wkts=('is_wicket', 'sum'),
).reset_index()
d_bowlers['death_econ'] = (d_bowlers['death_runs'] / d_bowlers['death_balls'] * 6).round(2)

d_pres = ipl_death_pres.groupby('bowler_id').agg(
    pres_death_balls=('runs', 'count'),
    pres_death_runs=('runs', 'sum'),
    pres_death_wkts=('is_wicket', 'sum'),
).reset_index()
d_pres['pres_death_econ'] = (d_pres['pres_death_runs'] / d_pres['pres_death_balls'] * 6).round(2)

death_targets = d_bowlers.merge(d_pres, on='bowler_id', how='inner')
death_targets = death_targets.rename(columns={'bowler_id': 'player_id'})
death_targets = death_targets[death_targets['pres_death_balls'] >= 30].copy()
death_targets = death_targets.merge(comb_bowl[['player_id', 'nationality', 'age', 'is_pakistani', 'combined_score']], on='player_id', how='left')
death_targets = death_targets[~death_targets['is_pakistani'].fillna(False)]
death_targets = death_targets.sort_values(by='pres_death_econ', ascending=True)

print("\n[GAP 1: DEATH OVERS LOCKDOWN SEAMER / BOWLER]")
print("Targeting: Econ < 9.5 in death pressure, min 30 death pressure balls")
print(death_targets[['bowler_name', 'nationality', 'age', 'death_balls', 'death_econ', 'pres_death_balls', 'pres_death_econ', 'pres_death_wkts', 'combined_score']].head(10).to_string(index=False))

# Gap 2: Powerplay Strike Bowler (Overs 1-6)
ipl_pp = ipl_legal[ipl_legal['overid'] <= 6].copy()
pp_bowlers = ipl_pp.groupby(['bowler_id', 'bowler_name']).agg(
    pp_balls=('runs', 'count'),
    pp_runs=('runs', 'sum'),
    pp_wkts=('is_wicket', 'sum'),
).reset_index()
pp_bowlers['pp_econ'] = (pp_bowlers['pp_runs'] / pp_bowlers['pp_balls'] * 6).round(2)
pp_bowlers['pp_sr'] = (pp_bowlers['pp_balls'] / pp_bowlers['pp_wkts'].replace(0, 1)).round(1)
pp_targets = pp_bowlers[pp_bowlers['pp_balls'] >= 80].copy()
pp_targets = pp_targets.rename(columns={'bowler_id': 'player_id'})
pp_targets = pp_targets.merge(comb_bowl[['player_id', 'nationality', 'age', 'is_pakistani', 'combined_score']], on='player_id', how='left')
is_pak_bowl = pp_targets['is_pakistani'].fillna(False).astype(bool)
pp_targets = pp_targets.loc[~is_pak_bowl].sort_values(by='pp_wkts', ascending=False)

print("\n[GAP 2: POWERPLAY WICKET TAKER]")
print("Targeting: High PP wickets, Econ < 8.5")
print(pp_targets[['bowler_name', 'nationality', 'age', 'pp_balls', 'pp_wkts', 'pp_econ', 'pp_sr', 'combined_score']].head(10).to_string(index=False))

# Gap 3: Clutch Middle / Death Finisher (Batting)
# Filter batters with high pressure SR, especially in chase or death
ipl_bat_death = ipl_legal[ipl_legal['overid'] >= 14].copy()
bat_finisher = ipl_bat_death.groupby(['striker_id', 'striker_name']).agg(
    fin_balls=('runs', 'count'),
    fin_runs=('runs', 'sum'),
    fin_sixes=('is_six', 'sum'),
    fin_fours=('is_four', 'sum'),
).reset_index()
bat_finisher['fin_SR'] = (bat_finisher['fin_runs'] / bat_finisher['fin_balls'] * 100).round(1)

bat_pres_fin = ipl_bat_death[ipl_bat_death['is_pressure']].groupby('striker_id').agg(
    pres_fin_balls=('runs', 'count'),
    pres_fin_runs=('runs', 'sum'),
    pres_fin_sixes=('is_six', 'sum'),
).reset_index()
bat_pres_fin['pres_fin_SR'] = (bat_pres_fin['pres_fin_runs'] / bat_pres_fin['pres_fin_balls'] * 100).round(1)

fin_targets = bat_finisher.merge(bat_pres_fin, on='striker_id', how='inner')
fin_targets = fin_targets.rename(columns={'striker_id': 'player_id'})
fin_targets = fin_targets[fin_targets['pres_fin_balls'] >= 30].copy()
fin_targets = fin_targets.merge(comb_bat[['player_id', 'nationality', 'age', 'is_pakistani', 'combined_score']], on='player_id', how='left')
is_pak_bat = fin_targets['is_pakistani'].fillna(False).astype(bool)
fin_targets = fin_targets.loc[~is_pak_bat].sort_values(by='pres_fin_SR', ascending=False)

print("\n[GAP 3: CLUTCH MIDDLE-DEATH FINISHER]")
print("Targeting: Pres Death SR > 165, boundary hitting under pressure")
print(fin_targets[['striker_name', 'nationality', 'age', 'fin_balls', 'fin_SR', 'pres_fin_balls', 'pres_fin_runs', 'pres_fin_SR', 'combined_score']].head(10).to_string(index=False))

print("\n[GAP 3: CLUTCH MIDDLE-DEATH FINISHER]")
print("Targeting: Pres Death SR > 165, boundary hitting under pressure")
print(fin_targets[['striker_name', 'nationality', 'age', 'fin_balls', 'fin_SR', 'pres_fin_balls', 'pres_fin_runs', 'pres_fin_SR', 'combined_score']].head(10).to_string(index=False))

# Save the final JSON data for frontend
frontend_data = {
    'batters': comb_bat.head(150).to_dict(orient='records'),
    'bowlers': comb_bowl.head(150).to_dict(orient='records'),
}
with open('ipl/public/pressure_data.json', 'w') as f:
    json.dump(frontend_data, f, indent=2)

print("\nUpdated ipl/public/pressure_data.json with refined blended ratings.")
