import pandas as pd
from pathlib import Path
import numpy as np

print("Loading match stats...")
df = pd.read_parquet("d:/ipl-rating/ipl/data/player_match_stats.parquet")

print("Aggregating season stats...")
season_grp = df.groupby(["player_name", "season"])

def get_primary_team(x):
    return x.value_counts().index[0]

# Fast Dummy Columns for Context
df["runs_in_wins_dummy"] = np.where(df["is_win"], df["runs_scored"], 0)
df["runs_in_chases_dummy"] = np.where(df["is_chase"], df["runs_scored"], 0)
df["playoff_runs_dummy"] = np.where(df["is_playoff"], df["runs_scored"], 0)
df["is_batting_failure"] = (df["runs_scored"] < 15) & (df["balls_faced"] > 0)

df["wickets_in_wins_dummy"] = np.where(df["is_win"], df["wickets_taken"], 0)
df["playoff_wickets_dummy"] = np.where(df["is_playoff"], df["wickets_taken"], 0)
df["is_bowling_failure"] = (df["wickets_taken"] == 0) & (df["balls_bowled"] > 0)

season_stats = season_grp.agg(
    primary_team=("team", get_primary_team),
    matches=("match_id", "nunique"),
    innings_batted=("balls_faced", lambda x: (x > 0).sum()),
    runs=("runs_scored", "sum"),
    balls_faced=("balls_faced", "sum"),
    fours=("fours", "sum"),
    sixes=("sixes", "sum"),
    fifties=("runs_scored", lambda x: ((x >= 50) & (x < 100)).sum()),
    hundreds=("runs_scored", lambda x: (x >= 100).sum()),
    dismissals=("is_out", "sum"),
    
    # Phase/Context Batting
    runs_in_powerplay=("runs_in_powerplay", "sum"),
    balls_faced_powerplay=("balls_faced_powerplay", "sum"),
    runs_in_death=("runs_in_death", "sum"),
    balls_faced_death=("balls_faced_death", "sum"),
    runs_in_wins=("runs_in_wins_dummy", "sum"),
    runs_in_chases=("runs_in_chases_dummy", "sum"),
    playoff_runs=("playoff_runs_dummy", "sum"),
    avg_rrr_faced=("avg_rrr_faced", lambda x: x[x > 0].mean() if (x > 0).any() else 0),
    batting_failures=("is_batting_failure", "sum"),
    
    # Bowling
    innings_bowled=("balls_bowled", lambda x: (x > 0).sum()),
    wickets=("wickets_taken", "sum"),
    balls_bowled=("balls_bowled", "sum"),
    runs_conceded=("runs_conceded", "sum"),
    dot_balls=("dot_balls_bowled", "sum"),
    
    # Phase/Context Bowling
    powerplay_wickets=("powerplay_wickets", "sum"),
    death_wickets=("death_wickets", "sum"),
    balls_bowled_powerplay=("balls_bowled_powerplay", "sum"),
    balls_bowled_death=("balls_bowled_death", "sum"),
    wickets_in_wins=("wickets_in_wins_dummy", "sum"),
    playoff_wickets=("playoff_wickets_dummy", "sum"),
    runs_conceded_powerplay=("runs_conceded_powerplay", "sum"),
    runs_conceded_death=("runs_conceded_death", "sum"),
    avg_rrr_defended=("avg_rrr_defended", lambda x: x[x > 0].mean() if (x > 0).any() else 0),
    three_fers=("is_3_fer", "sum"),
    four_fers=("is_4_fer", "sum"),
    bowling_failures=("is_bowling_failure", "sum"),
    
    # Fielding & Impact
    catches=("catches", "sum"),
    stumpings=("stumpings", "sum"),
    run_outs=("run_outs", "sum"),
    avg_match_run_contribution=("match_run_contribution", lambda x: x[x > 0].mean() if (x > 0).any() else 0),
    avg_match_wicket_contribution=("match_wicket_contribution", lambda x: x[x > 0].mean() if (x > 0).any() else 0),
    potm_count=("is_potm", "sum")
).reset_index()

print("Calculating derived metrics...")
# Base batting derived
season_stats["is_unbeaten_season"] = season_stats["dismissals"] == 0
season_stats["batting_average"] = np.where(
    season_stats["is_unbeaten_season"],
    season_stats["runs"],
    season_stats["runs"] / season_stats["dismissals"]
)
season_stats["strike_rate"] = np.where(season_stats["balls_faced"] > 0, (season_stats["runs"] / season_stats["balls_faced"]) * 100, 0)
season_stats["powerplay_SR"] = np.where(season_stats["balls_faced_powerplay"] > 0, (season_stats["runs_in_powerplay"] / season_stats["balls_faced_powerplay"]) * 100, 0)
season_stats["death_SR"] = np.where(season_stats["balls_faced_death"] > 0, (season_stats["runs_in_death"] / season_stats["balls_faced_death"]) * 100, 0)
season_stats["boundary_pct"] = np.where(season_stats["runs"] > 0, ((season_stats["fours"] * 4) + (season_stats["sixes"] * 6)) / season_stats["runs"], 0)
season_stats["batting_failure_rate"] = np.where(season_stats["innings_batted"] > 0, season_stats["batting_failures"] / season_stats["innings_batted"], 0)

# Base bowling derived
overs_bowled = season_stats["balls_bowled"] / 6
season_stats["economy"] = np.where(overs_bowled > 0, season_stats["runs_conceded"] / overs_bowled, 0)
season_stats["bowling_average"] = np.where(season_stats["wickets"] > 0, season_stats["runs_conceded"] / season_stats["wickets"], np.nan)
season_stats["bowling_SR"] = np.where(season_stats["wickets"] > 0, season_stats["balls_bowled"] / season_stats["wickets"], np.nan)
season_stats["dot_ball_pct"] = np.where(season_stats["balls_bowled"] > 0, season_stats["dot_balls"] / season_stats["balls_bowled"], 0)

pp_overs = season_stats["balls_bowled_powerplay"] / 6
season_stats["powerplay_economy"] = np.where(pp_overs > 0, season_stats["runs_conceded_powerplay"] / pp_overs, 0)

death_overs = season_stats["balls_bowled_death"] / 6
season_stats["death_economy"] = np.where(death_overs > 0, season_stats["runs_conceded_death"] / death_overs, 0)

season_stats["bowling_failure_rate"] = np.where(season_stats["innings_bowled"] > 0, season_stats["bowling_failures"] / season_stats["innings_bowled"], 0)

print("Calculating League Baselines...")
league_stats = season_stats.groupby("season").agg(
    league_runs=("runs", "sum"),
    league_balls_faced=("balls_faced", "sum"),
    league_dismissals=("dismissals", "sum"),
    league_runs_conceded=("runs_conceded", "sum"),
    league_balls_bowled=("balls_bowled", "sum"),
    league_wickets=("wickets", "sum")
).reset_index()

league_stats["league_sr"] = (league_stats["league_runs"] / league_stats["league_balls_faced"]) * 100
league_stats["league_avg"] = league_stats["league_runs"] / league_stats["league_dismissals"]
league_stats["league_economy"] = league_stats["league_runs_conceded"] / (league_stats["league_balls_bowled"] / 6)
league_stats["league_bowling_avg"] = league_stats["league_runs_conceded"] / league_stats["league_wickets"]

print("Calculating Team Baselines...")
team_stats = season_stats.groupby(["season", "primary_team"]).agg(
    team_runs=("runs", "sum"),
    team_balls_faced=("balls_faced", "sum"),
    team_dismissals=("dismissals", "sum"),
    team_runs_conceded=("runs_conceded", "sum"),
    team_balls_bowled=("balls_bowled", "sum"),
    team_wickets=("wickets", "sum")
).reset_index()

team_stats["team_sr"] = (team_stats["team_runs"] / team_stats["team_balls_faced"]) * 100
team_stats["team_avg"] = team_stats["team_runs"] / team_stats["team_dismissals"]
team_stats["team_economy"] = team_stats["team_runs_conceded"] / (team_stats["team_balls_bowled"] / 6)
team_stats["team_bowling_avg"] = team_stats["team_runs_conceded"] / team_stats["team_wickets"]

print("Merging Baselines and Calculating Dominance...")
season_stats = pd.merge(season_stats, league_stats[["season", "league_runs", "league_wickets", "league_sr", "league_avg", "league_economy", "league_bowling_avg"]], on="season", how="left")
season_stats = pd.merge(season_stats, team_stats[["season", "primary_team", "team_runs", "team_wickets", "team_sr", "team_avg", "team_economy", "team_bowling_avg"]], on=["season", "primary_team"], how="left")

MIN_BALLS_FACED = 50
MIN_BALLS_BOWLED = 60

# League Dominance Batting
season_stats["league_relative_sr"] = np.where(season_stats["balls_faced"] >= MIN_BALLS_FACED, (season_stats["strike_rate"] - season_stats["league_sr"]) / season_stats["league_sr"], np.nan)
season_stats["league_relative_avg"] = np.where(season_stats["balls_faced"] >= MIN_BALLS_FACED, (season_stats["batting_average"] - season_stats["league_avg"]) / season_stats["league_avg"], np.nan)
season_stats["league_relative_runs"] = season_stats["runs"] / season_stats["league_runs"] * 100 # Relative runs is simply % of league runs

# League Dominance Bowling
season_stats["league_relative_economy"] = np.where(season_stats["balls_bowled"] >= MIN_BALLS_BOWLED, (season_stats["league_economy"] - season_stats["economy"]) / season_stats["league_economy"], np.nan)
season_stats["league_relative_bowling_avg"] = np.where((season_stats["balls_bowled"] >= MIN_BALLS_BOWLED) & (season_stats["wickets"] > 0), (season_stats["league_bowling_avg"] - season_stats["bowling_average"]) / season_stats["league_bowling_avg"], np.nan)
season_stats["league_relative_wickets"] = season_stats["wickets"] / season_stats["league_wickets"] * 100

print("Sorting and saving...")
season_stats = season_stats.sort_values(["season", "runs"], ascending=[True, False])

output_path = Path("d:/ipl-rating/ipl/data/player_season_stats.parquet")
output_path.parent.mkdir(parents=True, exist_ok=True)
season_stats.to_parquet(output_path, index=False)

print(f"Data saved to {output_path}")
print(f"Shape: {season_stats.shape}")
