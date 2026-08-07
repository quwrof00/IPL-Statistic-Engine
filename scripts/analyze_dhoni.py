import json

with open('ipl/public/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

dhoni18 = next((p for p in data if p.get('player_name') == 'MS Dhoni' and p.get('season') == '2018'), {})
dhoni19 = next((p for p in data if p.get('player_name') == 'MS Dhoni' and p.get('season') == '2019'), {})

metrics = ['quwrof_v11', 'bat_percentile', 'bat_base', 'rae', 'bat_chase_impact', 'bat_playoff_impact']

print(f"{'Metric':<25} | {'Dhoni 2018':<12} | {'Dhoni 2019':<12}")
print("-" * 55)
for m in metrics:
    print(f"{m:<25} | {float(dhoni18.get(m, 0)):<12.2f} | {float(dhoni19.get(m, 0)):<12.2f}")
