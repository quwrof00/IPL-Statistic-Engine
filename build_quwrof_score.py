import pandas as pd
import numpy as np
from pathlib import Path

df = pd.read_parquet("d:/ipl-rating/ipl/data/player_season_stats.parquet")

# 1. Qualifiers
# To avoid a guy who hit 1 ball for six having a 600 SR and ruining the percentiles
bat_qual = df["balls_faced"] >= 50
bowl_qual = df["balls_bowled"] >= 60

# 2. Helper to rank
def get_rank(series, ascending=True, qual_mask=None):
    if qual_mask is None:
        qual_mask = pd.Series(True, index=series.index)
    
    ranks = pd.Series(0.0, index=series.index)
    valid_data = series[qual_mask]
    
    if not valid_data.empty:
        # Pct rank returns 0.0 to 1.0, multiply by 100
        ranked = valid_data.rank(pct=True, ascending=ascending) * 100
        ranks.update(ranked)
        
    return ranks

# 3. Batting Component (0-100)
# Dominance (40%)
dom_runs = get_rank(df["league_relative_runs"], qual_mask=bat_qual)
dom_avg = get_rank(df["league_relative_avg"], qual_mask=bat_qual)
dom_sr = get_rank(df["league_relative_sr"], qual_mask=bat_qual)
bat_dominance = (dom_runs * 0.4) + (dom_avg * 0.3) + (dom_sr * 0.3)

# Volume (20%)
vol_runs = get_rank(df["runs"], qual_mask=bat_qual)
vol_bounds = get_rank(df["fours"] + df["sixes"], qual_mask=bat_qual)
bat_volume = (vol_runs * 0.6) + (vol_bounds * 0.4)

# Efficiency (20%)
eff_sr = get_rank(df["strike_rate"], qual_mask=bat_qual)
eff_avg = get_rank(df["batting_average"], qual_mask=bat_qual)
eff_bpct = get_rank(df["boundary_pct"], qual_mask=bat_qual)
bat_efficiency = (eff_sr * 0.4) + (eff_avg * 0.4) + (eff_bpct * 0.2)

# Context (20%)
ctx_wins = get_rank(df["runs_in_wins"], qual_mask=bat_qual)
ctx_chases = get_rank(df["runs_in_chases"], qual_mask=bat_qual)
ctx_playoff = get_rank(df["playoff_runs"], qual_mask=bat_qual)
ctx_death_sr = get_rank(df["death_SR"], qual_mask=bat_qual)
ctx_pressure = get_rank(df["avg_rrr_faced"], qual_mask=bat_qual) # Facing high RRR is hard
bat_context = (ctx_wins * 0.3) + (ctx_chases * 0.2) + (ctx_playoff * 0.2) + (ctx_death_sr * 0.2) + (ctx_pressure * 0.1)

df["batting_score"] = np.where(bat_qual, (bat_dominance * 0.4) + (bat_volume * 0.2) + (bat_efficiency * 0.2) + (bat_context * 0.2), 0)

# 4. Bowling Component (0-100)
# Dominance (40%)
dom_wickets = get_rank(df["league_relative_wickets"], qual_mask=bowl_qual)
dom_econ = get_rank(df["league_relative_economy"], qual_mask=bowl_qual) 
dom_bavg = get_rank(df["league_relative_bowling_avg"], qual_mask=bowl_qual)
bowl_dominance = (dom_wickets * 0.4) + (dom_econ * 0.3) + (dom_bavg * 0.3)

# Volume (20%)
vol_wickets = get_rank(df["wickets"], qual_mask=bowl_qual)
bowl_volume = vol_wickets

# Efficiency (20%)
eff_econ = get_rank(df["economy"], ascending=False, qual_mask=bowl_qual) # lower is better
eff_dot = get_rank(df["dot_ball_pct"], qual_mask=bowl_qual)
eff_bsr = get_rank(df["bowling_SR"], ascending=False, qual_mask=bowl_qual)
bowl_efficiency = (eff_econ * 0.4) + (eff_dot * 0.3) + (eff_bsr * 0.3)

# Context (20%)
ctx_bwins = get_rank(df["wickets_in_wins"], qual_mask=bowl_qual)
ctx_dwickets = get_rank(df["death_wickets"], qual_mask=bowl_qual)
ctx_pwickets = get_rank(df["powerplay_wickets"], qual_mask=bowl_qual)
ctx_bplayoff = get_rank(df["playoff_wickets"], qual_mask=bowl_qual)
ctx_deathecon = get_rank(df["death_economy"], ascending=False, qual_mask=bowl_qual)
ctx_ppecon = get_rank(df["powerplay_economy"], ascending=False, qual_mask=bowl_qual)
ctx_pressure = get_rank(df["avg_rrr_defended"], qual_mask=bowl_qual)

bowl_context = (ctx_bwins * 0.20) + (ctx_bplayoff * 0.15) + (ctx_pwickets * 0.15) + (ctx_deathecon * 0.20) + (ctx_dwickets * 0.10) + (ctx_pressure * 0.10) + (ctx_ppecon * 0.10)

df["bowling_score"] = np.where(bowl_qual, (bowl_dominance * 0.4) + (bowl_volume * 0.2) + (bowl_efficiency * 0.2) + (bowl_context * 0.2), 0)

# 5. Fielding Score (0-100)
fld_catches = get_rank(df["catches"])
fld_ro = get_rank(df["run_outs"])
fld_st = get_rank(df["stumpings"])
df["fielding_score"] = (fld_catches * 0.5) + (fld_ro * 0.3) + (fld_st * 0.2)

# 6. Impact Score (0-100)
imp_run_cont = get_rank(df["avg_match_run_contribution"], qual_mask=bat_qual)
imp_wic_cont = get_rank(df["avg_match_wicket_contribution"], qual_mask=bowl_qual)

# Consistency (Inverse of Failure Rate)
bat_cons = get_rank(df["batting_failure_rate"], ascending=False, qual_mask=bat_qual)
bowl_cons = get_rank(df["bowling_failure_rate"], ascending=False, qual_mask=bowl_qual)
# Blend consistency based on whether they are batter or bowler
consistency = np.where(df["batting_score"] > df["bowling_score"], bat_cons, bowl_cons)
# If they are genuine allrounders, average it
allrounder_mask = (df["batting_score"] > 40) & (df["bowling_score"] > 40)
consistency[allrounder_mask] = (bat_cons[allrounder_mask] + bowl_cons[allrounder_mask]) / 2

# Overall Match Contribution
match_cont = np.where(df["batting_score"] > df["bowling_score"], imp_run_cont, imp_wic_cont)
match_cont[allrounder_mask] = (imp_run_cont[allrounder_mask] + imp_wic_cont[allrounder_mask]) / 2

df["impact_score"] = (match_cont * 0.6) + (consistency * 0.4)

# 7. Role Expectations (Bonus contexts)
df["is_opener"] = (df["balls_faced_powerplay"] / df["balls_faced"].replace(0, 1)) > 0.40
df["is_finisher"] = (df["balls_faced_death"] / df["balls_faced"].replace(0, 1)) > 0.35
df["is_powerplay_bowler"] = (df["balls_bowled_powerplay"] / df["balls_bowled"].replace(0, 1)) > 0.40
df["is_death_bowler"] = (df["balls_bowled_death"] / df["balls_bowled"].replace(0, 1)) > 0.35

# Apply minor role bonuses directly to the component scores
df["batting_score"] = np.where(df["is_opener"], df["batting_score"] + (get_rank(df["powerplay_SR"], qual_mask=bat_qual) * 0.05), df["batting_score"])
df["batting_score"] = np.where(df["is_finisher"], df["batting_score"] + (ctx_death_sr * 0.05), df["batting_score"])
df["bowling_score"] = np.where(df["is_death_bowler"], df["bowling_score"] + (ctx_dwickets * 0.05), df["bowling_score"])
df["bowling_score"] = np.where(df["is_powerplay_bowler"], df["bowling_score"] + (ctx_pwickets * 0.05), df["bowling_score"])

# Ensure no component score exceeds 100
df["batting_score"] = np.minimum(100.0, df["batting_score"])
df["bowling_score"] = np.minimum(100.0, df["bowling_score"])
df["impact_score"] = np.minimum(100.0, df["impact_score"])
df["fielding_score"] = np.minimum(100.0, df["fielding_score"])

# 8. All-Round Bonus & Final Formula
df["all_round_bonus"] = 0.15 * np.minimum(df["batting_score"], df["bowling_score"])

df["raw_quwrof"] = (
    np.maximum(df["batting_score"], df["bowling_score"]) + 
    (0.25 * df["impact_score"]) + 
    (0.10 * df["fielding_score"]) + 
    df["all_round_bonus"]
)

# Cap at 99.5
# Wait, raw_quwrof can technically exceed 100 because 100 + 25 + 10 = 135.
# We must scale it perfectly. Let's scale raw_quwrof to 0-99.5
max_raw = df["raw_quwrof"].max()
df["quwrof_score"] = (df["raw_quwrof"] / max_raw) * 99.5
df["quwrof_score"] = df["quwrof_score"].round(2)

print("Sorting and saving final ratings...")
df = df.sort_values("quwrof_score", ascending=False)

output_path = Path("d:/ipl-rating/ipl/data/quwrof_scores.csv")
df.to_csv(output_path, index=False)
print(f"Scores saved to {output_path}")

print("\n--- TOP 20 GREATEST IPL SEASONS ---")
cols = ["player_name", "season", "runs", "wickets", "batting_score", "bowling_score", "impact_score", "quwrof_score"]
print(df[cols].head(20).to_string(index=False))
