import json

with open('ipl/public/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

kohli = next(p for p in data if p.get('player_name') == 'V Kohli' and p.get('season') == '2016')
warner = next(p for p in data if p.get('player_name') == 'DA Warner' and p.get('season') == '2016')

metrics = ['quwrof_v11', 'bat_percentile', 'bat_base', 'rae', 'bat_chase_impact', 'bat_playoff_impact']

print(f"{'Metric':<25} | {'Kohli 2016':<12} | {'Warner 2016':<12}")
print("-" * 55)
for m in metrics:
    print(f"{m:<25} | {float(kohli.get(m, 0)):<12.2f} | {float(warner.get(m, 0)):<12.2f}")
