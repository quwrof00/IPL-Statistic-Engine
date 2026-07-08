import json

with open('ipl/public/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

sorted_death = sorted(data, key=lambda x: float(x.get('bowl_death_impact', 0)), reverse=True)
print('Top 10 Death Bowlers:')
for i, p in enumerate(sorted_death[:10]):
    print(f"{i+1}. {p.get('player_name')} ({p.get('season')}) - {float(p.get('bowl_death_impact', 0)):.2f}")
