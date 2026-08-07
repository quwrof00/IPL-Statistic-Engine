import json
from collections import defaultdict

with open('ipl/public/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Group players by season
seasons = defaultdict(list)
for p in data:
    season = p.get('season')
    seasons[season].append(p)

# Actual IPL MVPs mapped
actual_mvps = {
    '2007/08': 'Shane Watson',
    '2009': 'Adam Gilchrist',
    '2009/10': 'Sachin Tendulkar',
    '2011': 'Chris Gayle',
    '2012': 'Sunil Narine',
    '2013': 'Shane Watson',
    '2014': 'Glenn Maxwell',
    '2015': 'Andre Russell',
    '2016': 'Virat Kohli',
    '2017': 'Ben Stokes',
    '2018': 'Sunil Narine',
    '2019': 'Andre Russell',
    '2020/21': 'Jofra Archer', # Treating 2020 as 2020/21 based on available keys? Let's check keys.
    '2021': 'Harshal Patel',
    '2022': 'Jos Buttler',
    '2023': 'Shubman Gill',
    '2024': 'Sunil Narine'
}

print(f"{'Season':<10} | {'Our Model #1 (Quwrof V11)':<30} | {'Actual IPL MVP'}")
print("-" * 75)
for season in sorted(seasons.keys()):
    players = seasons[season]
    players.sort(key=lambda x: float(x.get('quwrof_v11', 0)), reverse=True)
    top_player = players[0]
    
    # Try to match the season key
    actual = actual_mvps.get(season, "Unknown")
    if season == "2020/21": actual = "Jofra Archer (2020)"
    
    print(f"{season:<10} | {top_player.get('player_name')} ({float(top_player.get('quwrof_v11', 0)):.2f})".ljust(43) + f"| {actual}")
