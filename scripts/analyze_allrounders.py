import json

with open('ipl/public/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Let's check different thresholds
thresholds = [50, 60, 70, 75, 80]

print(f"{'Threshold':<10} | {'Count':<10}")
print("-" * 25)
for t in thresholds:
    count = sum(1 for p in data if float(p.get('bat_percentile', 0)) >= t and float(p.get('bowl_percentile', 0)) >= t)
    print(f">{t}%{'':<6} | {count:<10}")

print("\nTop 10 All-Rounders (>70% in both) by QuwrofScore:")
all_rounders = [p for p in data if float(p.get('bat_percentile', 0)) >= 70 and float(p.get('bowl_percentile', 0)) >= 70]
all_rounders.sort(key=lambda x: float(x.get('quwrof_v11', 0)), reverse=True)

for i, p in enumerate(all_rounders[:10]):
    print(f"#{i+1}: {p.get('player_name')} ({p.get('season')}) - Bat: {float(p.get('bat_percentile', 0)):.1f}, Bowl: {float(p.get('bowl_percentile', 0)):.1f}, V11: {float(p.get('quwrof_v11', 0)):.2f}")
