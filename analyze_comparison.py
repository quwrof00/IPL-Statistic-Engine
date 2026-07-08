import json

with open('ipl/public/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

jadeja = next((p for p in data if p.get('player_name') == 'RA Jadeja' and p.get('season') == '2023'), {})
rabada = next((p for p in data if p.get('player_name') == 'K Rabada' and p.get('season') == '2026'), {})
warner = next((p for p in data if p.get('player_name') == 'DA Warner' and p.get('season') == '2016'), {})

metrics = [
    'quwrof_v11', 'bat_percentile', 'bowl_percentile', 
    'bat_base', 'rae', 'bat_chase_impact', 'bat_playoff_impact',
    'bowl_base', 'smart_wickets', 'bowl_death_impact', 'bowl_playoff_impact',
    'impact_score', 'volume_multiplier'
]

players = [('Jadeja 23', jadeja), ('Rabada 26', rabada), ('Warner 16', warner)]

print(f"{'Metric':<20} | {'Jadeja 23':<12} | {'Rabada 26':<12} | {'Warner 16':<12}")
print("-" * 65)
for m in metrics:
    print(f"{m:<20} | {float(jadeja.get(m, 0)):<12.2f} | {float(rabada.get(m, 0)):<12.2f} | {float(warner.get(m, 0)):<12.2f}")
