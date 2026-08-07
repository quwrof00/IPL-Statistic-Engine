import json
import pandas as pd
from pathlib import Path
import time

data_dir = Path("d:/ipl-rating/ipl/data/ipl-stats")
json_files = list(data_dir.glob("*.json"))

rows = []

print(f"Found {len(json_files)} JSON files. Starting parsing...")

start_time = time.time()

for file_path in json_files:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            match = json.load(f)
            
        info = match.get("info", {})
        season = str(info.get("season"))
        venue = info.get("venue")
        teams = info.get("teams", [])
        outcome = info.get("outcome", {})
        winner = outcome.get("winner")
        
        event = info.get("event", {})
        match_number = event.get("match_number")
        is_playoff = ("stage" in event) or (match_number is None)
        
        pom = info.get("player_of_match", [None])
        player_of_match = pom[0] if pom else None
        
        match_id = file_path.stem
        
        # Pre-calculate inning 1 total for chase context
        inning_1_total = 0
        if len(match.get("innings", [])) > 0:
            for over_obj in match["innings"][0].get("overs", []):
                for delivery in over_obj.get("deliveries", []):
                    inning_1_total += delivery["runs"]["total"]
        target = inning_1_total + 1
        
        for inning_no, inning in enumerate(match.get("innings", []), start=1):
            batting_team = inning.get("team")
            
            if len(teams) >= 2:
                bowling_team = teams[1] if teams[0] == batting_team else teams[0]
            else:
                bowling_team = None
                
            score = 0
            wickets = 0
            balls_elapsed = 0
            
            for over_obj in inning.get("overs", []):
                over_no = over_obj.get("over")
                
                for delivery in over_obj.get("deliveries", []):
                    batter_runs = delivery["runs"]["batter"]
                    extras = delivery["runs"]["extras"]
                    total_runs = delivery["runs"]["total"]
                    
                    is_wicket = "wickets" in delivery
                    is_four = batter_runs == 4
                    is_six = batter_runs == 6
                    is_dot = (total_runs == 0)
                    
                    extras_dict = delivery.get("extras", {})
                    is_wide = "wides" in extras_dict
                    is_noball = "noballs" in extras_dict
                    is_legbye = "legbyes" in extras_dict
                    is_bye = "byes" in extras_dict
                    
                    # Context features
                    if inning_no == 2:
                        runs_needed = target - score
                        balls_remaining = 120 - balls_elapsed
                        rrr = (runs_needed / (balls_remaining / 6)) if balls_remaining > 0 else 0
                    else:
                        runs_needed = 0
                        balls_remaining = 0
                        rrr = 0
                    
                    row = {
                        "season": season,
                        "venue": venue,
                        "match_id": match_id,
                        "inning": inning_no,
                        "batting_team": batting_team,
                        "bowling_team": bowling_team,
                        "winner": winner,
                        "is_playoff": is_playoff,
                        "player_of_match": player_of_match,
                        "over": over_no,
                        "ball": delivery.get("actual_delivery"),
                        "balls_elapsed": balls_elapsed,
                        "score_before": score,
                        "wickets_before": wickets,
                        "runs_needed": runs_needed,
                        "balls_remaining": balls_remaining,
                        "rrr": rrr,
                        "batter": delivery.get("batter"),
                        "non_striker": delivery.get("non_striker"),
                        "bowler": delivery.get("bowler"),
                        "batter_runs": batter_runs,
                        "extras": extras,
                        "total_runs": total_runs,
                        "is_wicket": is_wicket,
                        "is_four": is_four,
                        "is_six": is_six,
                        "is_dot": is_dot,
                        "is_wide": is_wide,
                        "is_noball": is_noball,
                        "is_legbye": is_legbye,
                        "is_bye": is_bye,
                    }
                    
                    if is_wicket:
                        wicket = delivery["wickets"][0]
                        row["player_out"] = wicket.get("player_out")
                        row["dismissal_kind"] = wicket.get("kind")
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
                        
                    score += total_runs
                    
                    if not is_wide and not is_noball:
                        balls_elapsed += 1
                    
                    rows.append(row)
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")

end_time = time.time()
print(f"Parsing complete. Generated {len(rows)} rows in {end_time - start_time:.2f} seconds.")

df = pd.DataFrame(rows)
output_path = Path("d:/ipl-rating/ipl/data/deliveries.parquet")
output_path.parent.mkdir(parents=True, exist_ok=True)
df.to_parquet(output_path, index=False)
print(f"Data saved to {output_path}")
