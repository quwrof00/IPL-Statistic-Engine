import json
from collections import defaultdict

with open('ipl/public/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

sorted_players = sorted(data, key=lambda x: float(x.get('quwrof_v11', 0)), reverse=True)

print('--- TOP 10 PLAYERS ALL TIME ---')
for i, p in enumerate(sorted_players[:10]):
    print(f"#{i+1}: {p.get('player_name')} ({p.get('season')}) - {float(p.get('quwrof_v11', 0)):.2f}")

print('\n--- TOP 50 DISTRIBUTION ---')
season_counts = defaultdict(int)
for p in sorted_players[:50]:
    season_counts[p.get('season')] += 1
for season, count in sorted(season_counts.items(), key=lambda x: x[1], reverse=True):
    print(f'{season}: {count} players')

print('\n--- TOP 100 DISTRIBUTION ---')
season_counts_100 = defaultdict(int)
for p in sorted_players[:100]:
    season_counts_100[p.get('season')] += 1
for season, count in sorted(season_counts_100.items(), key=lambda x: x[1], reverse=True):
    print(f'{season}: {count} players')

print('\n--- AVERAGE OF TOP 5 PLAYERS PER SEASON ---')
season_players = defaultdict(list)
for p in data:
    season_players[p.get('season')].append(float(p.get('quwrof_v11', 0)))
season_top5_avg = {}
for season, scores in season_players.items():
    scores.sort(reverse=True)
    top5 = scores[:5]
    if top5:
        season_top5_avg[season] = sum(top5) / len(top5)
for season, avg in sorted(season_top5_avg.items(), key=lambda x: x[1], reverse=True):
    print(f'{season}: {avg:.2f}')
