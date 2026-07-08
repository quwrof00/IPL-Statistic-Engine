import json
import pandas as pd
from pathlib import Path

# Load one match
file_path = Path("d:/ipl-rating/ipl/data/ipl-stats/335982.json")
with open(file_path, "r", encoding="utf-8") as f:
    match = json.load(f)

# Step 1: Metadata extraction
info = match["info"]
season = info.get("season")
venue = info.get("venue")
teams = info.get("teams", [])
outcome = info.get("outcome", {})

winner = outcome.get("winner")
pom = info.get("player_of_match", [])

rows = []
match_id = file_path.stem

# Step 2: Iterate through innings
for inning_no, inning in enumerate(match["innings"], start=1):
    batting_team = inning["team"]
    
    # Bowling Team
    bowling_team = teams[1] if teams[0] == batting_team else teams[0]
    
    # Step 3: Initialize innings state
    score = 0
    wickets = 0
    balls = 0
    
    # Step 4: Iterate through overs
    for over_obj in inning.get("overs", []):
        over_no = over_obj["over"]
        
        # Step 5: Iterate through deliveries
        for delivery in over_obj.get("deliveries", []):
            
            # Extract basic runs info
            batter_runs = delivery["runs"]["batter"]
            extras = delivery["runs"]["extras"]
            total_runs = delivery["runs"]["total"]
            
            # Build ONE row
            row = {
                "season": season,
                "venue": venue,
                "match_id": match_id,
                "inning": inning_no,
                "batting_team": batting_team,
                "bowling_team": bowling_team,
                "winner": winner,
                "over": over_no,
                "ball": delivery.get("actual_delivery"),
                "score_before": score,
                "wickets_before": wickets,
                "batter": delivery.get("batter"),
                "non_striker": delivery.get("non_striker"),
                "bowler": delivery.get("bowler"),
                "batter_runs": batter_runs,
                "extras": extras,
                "total_runs": total_runs,
            }
            
            # Process wicket
            if "wickets" in delivery:
                # there could be multiple wickets on a ball (rare, but theoretically possible like Mankad + run out, etc)
                # usually it's just one, let's take the first
                wicket = delivery["wickets"][0]
                row["player_out"] = wicket.get("player_out")
                row["dismissal_kind"] = wicket.get("kind")
                # fielders can be a list of dicts
                fielders = wicket.get("fielders", [])
                if fielders:
                    row["fielder"] = ", ".join([f.get("name", "") for f in fielders])
                else:
                    row["fielder"] = None
                
                wickets += 1
            else:
                row["player_out"] = None
                row["dismissal_kind"] = None
                row["fielder"] = None
                
            # Then update score
            score += total_runs
            
            # Then append row
            rows.append(row)

# Make dataframe
df = pd.DataFrame(rows)

print("--- df.head() ---")
print(df.head())
print("\n--- df.columns ---")
for col in df.columns:
    print(f"- {col}")
print(f"\n--- df.shape ---\n{df.shape}")
