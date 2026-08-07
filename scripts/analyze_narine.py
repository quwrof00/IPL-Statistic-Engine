import json

with open('ipl/public/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

narine = next((p for p in data if p.get('player_name') == 'SP Narine' and p.get('season') == '2024'), {})
varun = next((p for p in data if p.get('player_name') == 'CV Varun' and p.get('season') == '2024'), {})

metrics = [
    'quwrof_v11', 'bat_percentile', 'bowl_percentile', 
    'bat_base', 'rae', 'bat_chase_impact', 'bat_playoff_impact',
    'bowl_base', 'smart_wickets', 'empirical_wickets', 'bowl_death_impact', 'bowl_playoff_impact',
    'impact_score', 'volume_multiplier'
]

print(f"{'Metric':<25} | {'Narine 2024':<15} | {'Varun 2024':<15}")
print("-" * 60)
for m in metrics:
    print(f"{m:<25} | {float(narine.get(m, 0)):<15.2f} | {float(varun.get(m, 0)):<15.2f}")
