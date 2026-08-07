import json

with open('ipl/public/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

g11 = next((p for p in data if p.get('player_name') == 'CH Gayle' and p.get('season') == '2011'), {})
g12 = next((p for p in data if p.get('player_name') == 'CH Gayle' and p.get('season') == '2012'), {})

metrics = ['quwrof_v11', 'bat_percentile', 'bat_base', 'rae', 'bat_chase_impact', 'bat_playoff_impact']

print(f"{'Metric':<25} | {'Gayle 2011':<12} | {'Gayle 2012':<12}")
print("-" * 55)
for m in metrics:
    print(f"{m:<25} | {float(g11.get(m, 0)):<12.2f} | {float(g12.get(m, 0)):<12.2f}")
