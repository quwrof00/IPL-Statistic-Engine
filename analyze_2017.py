import json

with open('ipl/public/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

warner = next((p for p in data if p.get('player_name') == 'DA Warner' and p.get('season') == '2017'), {})
stokes = next((p for p in data if p.get('player_name') == 'BA Stokes' and p.get('season') == '2017'), {})

metrics = [
    'quwrof_v11', 'bat_percentile', 'bowl_percentile', 
    'bat_base', 'rae', 'bowl_base', 'impact_score', 'volume_multiplier'
]

print(f"{'Metric':<25} | {'Warner 2017':<15} | {'Stokes 2017':<15}")
print("-" * 60)
for m in metrics:
    print(f"{m:<25} | {float(warner.get(m, 0)):<15.2f} | {float(stokes.get(m, 0)):<15.2f}")
