import ssl, urllib.request, json, urllib.parse, re, time
import pandas as pd

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

with open(r'd:\ipl-rating\scripts\all_players.json', 'r') as f:
    names = json.load(f)

# Nationality resolution first
data_path = r'c:\Users\Shourya\Downloads\6af458274c1e8_data_pack\Data Pack'
ctpm = pd.read_csv(data_path + r'\competition_team_player_mapping.csv')

national_teams = ['India', 'Pakistan', 'Australia', 'England', 'South Africa', 'New Zealand', 
                  'West Indies', 'Sri Lanka', 'Bangladesh', 'Afghanistan', 'Zimbabwe', 'Ireland', 
                  'Netherlands', 'Scotland', 'United Arab Emirates', 'Hong Kong', 'Canada', 
                  'United States Of America', 'Nepal', 'Oman', 'Singapore', 'Kuwait', 'Japan']

p_nationalities = {}
for name in names:
    teams_for_player = ctpm[ctpm.player_name == name]['team_name'].unique().tolist()
    nat = None
    for t in teams_for_player:
        for nt in national_teams:
            if t == nt or t == f'{nt} A':
                nat = nt
                break
        if nat:
            break
    if not nat:
        if name == 'Sunil Narine':
            nat = 'West Indies'
        else:
            nat = 'India'
    p_nationalities[name] = nat

headers = {'User-Agent': 'CricketAnalyticsApp/1.0 (cricket_research@edu.org)'}

def fetch_player_age(name):
    # Try direct name
    queries = [name, f"{name} (cricketer)"]
    for q_str in queries:
        q = urllib.parse.quote(q_str)
        url = f"https://en.wikipedia.org/w/api.php?action=query&titles={q}&prop=revisions&rvprop=content&rvsection=0&redirects=1&format=json"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=4) as r:
                d = json.loads(r.read().decode())
                pages = d.get('query', {}).get('pages', {})
                for pid, pdata in pages.items():
                    if pid == '-1':
                        continue
                    content = pdata.get('revisions', [{}])[0].get('*', '')
                    m = re.search(r'\{\{birth[ _]date[ _]and[ _]age\|(\d{4})\|(\d{1,2})\|(\d{1,2})', content, re.I)
                    if not m:
                        m = re.search(r'\{\{birth[ _]date\|(\d{4})\|(\d{1,2})\|(\d{1,2})', content, re.I)
                    if not m:
                        m = re.search(r'birth_date\s*=\s*.*?(\d{4})', content)
                    if m:
                        byear = int(m.group(1))
                        if 1970 <= byear <= 2010:
                            return 2026 - byear
        except Exception:
            pass
    return None

print(f"Fetching ages for {len(names)} players...")
player_meta = {}
success_count = 0

for i, name in enumerate(names):
    age = fetch_player_age(name)
    if age is not None:
        success_count += 1
    player_meta[name] = {
        'nationality': p_nationalities[name],
        'age': age
    }
    if (i + 1) % 25 == 0:
        print(f"Progress: {i+1}/{len(names)} (Ages found: {success_count})")

print(f"Finished! Found ages for {success_count}/{len(names)} players.")

with open(r'd:\ipl-rating\scripts\player_meta.json', 'w') as f:
    json.dump(player_meta, f, indent=2)
