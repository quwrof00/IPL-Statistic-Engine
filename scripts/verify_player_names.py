import pandas as pd

mapping_csv = pd.read_csv('C:/Users/Shourya/Downloads/6af458274c1e8_data_pack/Data Pack/competition_team_player_mapping.csv')
unique_players = mapping_csv[['player_id', 'player_name']].drop_duplicates()
print("Total unique players in mapping:", len(unique_players))

bat_targets = [
    'Tilak Varma', 'Suryakumar Yadav', 'David Miller', 'Rovman Powell', 
    'Nicholas Pooran', 'Tristan Stubbs', 'Jos Buttler', 'Aiden Markram', 
    'Tim David', 'Rinku Singh', 'Hardik Pandya', 'Marcus Stoinis', 'Heinrich Klaasen'
]

bowl_targets = [
    'Wanindu Hasaranga', 'Rashid Khan', 'Axar Patel', 'Jasprit Bumrah', 
    'Arshdeep Singh', 'Varun Chakravarthy', 'Blessing Muzarabani', 'Kuldeep Yadav', 
    'Sunil Narine', 'Bhuvneshwar Kumar', 'Akeal Hosein', 'Yuzvendra Chahal'
]

print("\n--- BATTERS CHECK ---")
for t in bat_targets:
    match = unique_players[unique_players['player_name'].str.contains(t, case=False, na=False)]
    print(f"Target: {t} -> {match['player_name'].tolist()}")

print("\n--- BOWLERS CHECK ---")
for t in bowl_targets:
    match = unique_players[unique_players['player_name'].str.contains(t, case=False, na=False)]
    print(f"Target: {t} -> {match['player_name'].tolist()}")
