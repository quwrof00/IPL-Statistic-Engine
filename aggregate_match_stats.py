import pandas as pd
import numpy as np
from pathlib import Path

print("Loading deliveries...")
df = pd.read_parquet("d:/ipl-rating/ipl/data/deliveries.parquet")

# Exclude super overs (innings > 2)
df = df[df["inning"] <= 2]

# Wickets taken by bowler (excluding run outs, retired hurt, obstructing field)
non_bowler_wickets = ["run out", "retired hurt", "obstructing the field"]

# Add phase flags
df["is_powerplay"] = df["over"] < 6
df["is_death"] = df["over"] >= 15

# Dummy columns for efficient aggregation
df["is_ball_faced"] = ~df["is_wide"]
df["balls_faced_powerplay"] = df["is_ball_faced"] & df["is_powerplay"]
df["balls_faced_death"] = df["is_ball_faced"] & df["is_death"]
df["batter_runs_powerplay"] = np.where(df["is_powerplay"], df["batter_runs"], 0)
df["batter_runs_death"] = np.where(df["is_death"], df["batter_runs"], 0)

# Bowler dummies
df["bowler_runs_conceded"] = np.where(df["is_bye"] | df["is_legbye"], 0, df["total_runs"])
df["is_legal_ball"] = ~(df["is_wide"] | df["is_noball"])
df["bowler_runs_powerplay"] = np.where(df["is_powerplay"], df["bowler_runs_conceded"], 0)
df["bowler_runs_death"] = np.where(df["is_death"], df["bowler_runs_conceded"], 0)
df["bowler_balls_powerplay"] = df["is_legal_ball"] & df["is_powerplay"]
df["bowler_balls_death"] = df["is_legal_ball"] & df["is_death"]

print("Aggregating batting stats...")
# 1. Batting Stats
bat_grp = df.groupby(["match_id", "season", "batting_team", "batter"])
batting = bat_grp.agg(
    runs_scored=("batter_runs", "sum"),
    balls_faced=("is_ball_faced", "sum"),
    fours=("is_four", "sum"),
    sixes=("is_six", "sum"),
    runs_in_powerplay=("batter_runs_powerplay", "sum"),
    balls_faced_powerplay=("balls_faced_powerplay", "sum"),
    runs_in_death=("batter_runs_death", "sum"),
    balls_faced_death=("balls_faced_death", "sum"),
    avg_rrr_faced=("rrr", "mean"), # Chase pressure
    is_chase=("inning", lambda x: (x == 2).any())
).reset_index()
batting = batting.rename(columns={"batter": "player_name", "batting_team": "team"})

# Did the batter get out?
dismissals = df.dropna(subset=["player_out"]).groupby(["match_id", "player_out"]).size().reset_index(name="is_out")
dismissals["is_out"] = dismissals["is_out"] > 0
dismissals = dismissals.rename(columns={"player_out": "player_name"})

# Merge dismissals into batting
batting = pd.merge(batting, dismissals, on=["match_id", "player_name"], how="left")
batting["is_out"] = batting["is_out"].fillna(False)

print("Aggregating bowling stats...")
# 2. Bowling Stats
bowl_grp = df.groupby(["match_id", "season", "bowling_team", "bowler"])
bowling = bowl_grp.agg(
    balls_bowled=("is_legal_ball", "sum"),
    runs_conceded=("bowler_runs_conceded", "sum"),
    dot_balls_bowled=("is_dot", "sum"),
    balls_bowled_powerplay=("bowler_balls_powerplay", "sum"),
    balls_bowled_death=("bowler_balls_death", "sum"),
    runs_conceded_powerplay=("bowler_runs_powerplay", "sum"),
    runs_conceded_death=("bowler_runs_death", "sum"),
    avg_rrr_defended=("rrr", lambda x: x[x > 0].mean() if (x > 0).any() else 0.0)
).reset_index()
bowling = bowling.rename(columns={"bowler": "player_name", "bowling_team": "team"})

# Wickets taken by bowler
bowler_wickets_df = df[df["is_wicket"] & ~df["dismissal_kind"].isin(non_bowler_wickets)]
wickets = bowler_wickets_df.groupby(["match_id", "bowler"]).agg(
    wickets_taken=("is_wicket", "sum"),
    powerplay_wickets=("is_powerplay", "sum"),
    death_wickets=("is_death", "sum")
).reset_index()
wickets = wickets.rename(columns={"bowler": "player_name"})

bowling = pd.merge(bowling, wickets, on=["match_id", "player_name"], how="left")
bowling["wickets_taken"] = bowling["wickets_taken"].fillna(0).astype(int)
bowling["powerplay_wickets"] = bowling["powerplay_wickets"].fillna(0).astype(int)
bowling["death_wickets"] = bowling["death_wickets"].fillna(0).astype(int)

# 3-fers and 4-fers per match
bowling["is_3_fer"] = bowling["wickets_taken"] >= 3
bowling["is_4_fer"] = bowling["wickets_taken"] >= 4

print("Aggregating fielding stats...")
# 3. Fielding Stats
fielding_df = df.dropna(subset=["fielder"]).copy()
fielding_exploded = fielding_df.assign(fielder=fielding_df["fielder"].str.split(", ")).explode("fielder")

catches = fielding_exploded[fielding_exploded["dismissal_kind"].isin(["caught", "caught and bowled"])].groupby(["match_id", "season", "bowling_team", "fielder"]).size().reset_index(name="catches")
stumpings = fielding_exploded[fielding_exploded["dismissal_kind"] == "stumped"].groupby(["match_id", "season", "bowling_team", "fielder"]).size().reset_index(name="stumpings")
run_outs = fielding_exploded[fielding_exploded["dismissal_kind"] == "run out"].groupby(["match_id", "season", "bowling_team", "fielder"]).size().reset_index(name="run_outs")

fielding = catches.merge(stumpings, on=["match_id", "season", "bowling_team", "fielder"], how="outer")
fielding = fielding.merge(run_outs, on=["match_id", "season", "bowling_team", "fielder"], how="outer")
fielding = fielding.rename(columns={"fielder": "player_name", "bowling_team": "team"})
for col in ["catches", "stumpings", "run_outs"]:
    fielding[col] = fielding[col].fillna(0).astype(int)

print("Extracting match context...")
match_context = df.groupby(["match_id"]).agg(
    winner=("winner", "first"),
    is_playoff=("is_playoff", "first"),
    player_of_match=("player_of_match", "first")
).reset_index()

print("Merging stats...")
# 4. Merging all together
player_match_stats = pd.merge(batting, bowling, on=["match_id", "season", "player_name", "team"], how="outer")
player_match_stats = pd.merge(player_match_stats, fielding, on=["match_id", "season", "player_name", "team"], how="outer")
player_match_stats = pd.merge(player_match_stats, match_context, on="match_id", how="left")

player_match_stats["is_win"] = player_match_stats["team"] == player_match_stats["winner"]
player_match_stats["is_potm"] = player_match_stats["player_name"] == player_match_stats["player_of_match"]

# Fill NaNs
fill_cols = ["runs_scored", "balls_faced", "fours", "sixes", 
             "runs_in_powerplay", "balls_faced_powerplay", "runs_in_death", "balls_faced_death",
             "balls_bowled", "runs_conceded", "dot_balls_bowled", 
             "balls_bowled_powerplay", "balls_bowled_death",
             "runs_conceded_powerplay", "runs_conceded_death",
             "wickets_taken", "powerplay_wickets", "death_wickets",
             "catches", "stumpings", "run_outs"]
for col in fill_cols:
    player_match_stats[col] = player_match_stats[col].fillna(0).astype(int)

player_match_stats["is_out"] = player_match_stats["is_out"].fillna(False)
player_match_stats["is_chase"] = player_match_stats["is_chase"].fillna(False)
player_match_stats["is_3_fer"] = player_match_stats["is_3_fer"].fillna(False)
player_match_stats["is_4_fer"] = player_match_stats["is_4_fer"].fillna(False)
player_match_stats["avg_rrr_faced"] = player_match_stats["avg_rrr_faced"].fillna(0.0)

print("Calculating match contributions...")
# 5. Calculate Match Totals
team_match_runs = df.groupby(["match_id", "batting_team"])["total_runs"].sum().reset_index(name="team_match_runs")
team_match_runs = team_match_runs.rename(columns={"batting_team": "team"})

team_match_wickets = bowler_wickets_df.groupby(["match_id", "bowling_team"]).size().reset_index(name="team_match_wickets")
team_match_wickets = team_match_wickets.rename(columns={"bowling_team": "team"})

player_match_stats = pd.merge(player_match_stats, team_match_runs, on=["match_id", "team"], how="left")
player_match_stats = pd.merge(player_match_stats, team_match_wickets, on=["match_id", "team"], how="left")
player_match_stats["team_match_runs"] = player_match_stats["team_match_runs"].fillna(0)
player_match_stats["team_match_wickets"] = player_match_stats["team_match_wickets"].fillna(0)

player_match_stats["match_run_contribution"] = np.where(
    player_match_stats["team_match_runs"] > 0, 
    player_match_stats["runs_scored"] / player_match_stats["team_match_runs"], 
    0
)
player_match_stats["match_wicket_contribution"] = np.where(
    player_match_stats["team_match_wickets"] > 0, 
    player_match_stats["wickets_taken"] / player_match_stats["team_match_wickets"], 
    0
)

print("Sorting and saving...")
player_match_stats = player_match_stats.sort_values(["season", "match_id", "team", "player_name"])

output_path = Path("d:/ipl-rating/ipl/data/player_match_stats.parquet")
output_path.parent.mkdir(parents=True, exist_ok=True)
player_match_stats.to_parquet(output_path, index=False)

print(f"Data saved to {output_path}")
print(f"Shape: {player_match_stats.shape}")
