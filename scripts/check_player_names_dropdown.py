import pandas as pd
import numpy as np

# Load Data Pack players.csv to get the exact dropdown spelling
players_csv = pd.read_csv('C:/Users/Shourya/Downloads/6af458274c1e8_data_pack/Data Pack/players.csv')
print("Total players in players.csv:", len(players_csv))
print("Sample player names:", players_csv['player_name'].head(15).tolist())

# Check our top batters and bowlers in players.csv
bat_names = [
    'Namboori Tilak Varma', 'Suryakumar Yadav', 'David Miller', 'Rovman Powell', 
    'Nicholas Pooran', 'Tristan Stubbs', 'Jos Buttler', 'Aiden Markram', 
    'Tim David', 'Rinku Singh', 'Hardik Pandya', 'Marcus Stoinis', 'Heinrich Klaasen'
]

bowl_names = [
    'Wanindu Hasaranga', 'Rashid Khan', 'Axar Patel', 'Jasprit Bumrah', 
    'Arshdeep Singh', 'Varun Chakravarthy', 'Blessing Muzarabani', 'Kuldeep Yadav', 
    'Sunil Narine', 'Bhuvneshwar Kumar', 'Akeal Hosein', 'Yuzvendra Chahal'
]

print("\nChecking Batters match:")
for name in bat_names:
    matches = players_csv[players_csv['player_name'].str.contains(name.split()[-1], case=False, na=False)]['player_name'].tolist()
    print(f"Target: {name} -> Found: {matches}")

print("\nChecking Bowlers match:")
for name in bowl_names:
    matches = players_csv[players_csv['player_name'].str.contains(name.split()[-1], case=False, na=False)]['player_name'].tolist()
    print(f"Target: {name} -> Found: {matches}")
