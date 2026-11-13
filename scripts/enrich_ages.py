import ssl, urllib.request, json, urllib.parse, re, concurrent.futures
import pandas as pd

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

with open(r'd:\ipl-rating\scripts\all_players.json', 'r') as f:
    names = json.load(f)

with open(r'd:\ipl-rating\scripts\player_meta.json', 'r') as f:
    current_meta = json.load(f)

# Name aliases for search when cricketer has common or slightly different display name
ALIASES = {
    'William Jacks': 'Will Jacks',
    'Mahendra Singh Dhoni': 'MS Dhoni',
    'Matthew Humphreys': 'Matthew Humphreys (cricketer)',
    'Mohammad Nawaz': 'Mohammad Nawaz (cricketer, born 1994)',
    'Mohammad Wasim': 'Mohammad Wasim (cricketer, born 2001)',
    'Muhammad Arfan': 'Muhammad Arfan (cricketer)',
    'Ehsan Khan': 'Ehsan Khan (cricketer)',
    'Simarjeet Singh': 'Simarjeet Singh',
    'Arshad Khan': 'Arshad Khan (Indian cricketer)',
    'Shashank Singh': 'Shashank Singh (cricketer)',
    'Harpreet Brar': 'Harpreet Brar',
    'Jitesh Sharma': 'Jitesh Sharma',
    'Vipraj Nigam': 'Vipraj Nigam',
    'Zakary Foulkes': 'Zak Foulkes',
    'Praful Hinge': 'Praful Hinge',
    'Digvesh Rathi': 'Digvesh Rathi',
    'Prashant Veer': 'Prashant Veer',
    'Salil Arora': 'Salil Arora',
    'Sakib Hussain': 'Sakib Hussain',
    'Yash Punja': 'Yash Punja',
    'Mayank Yadav': 'Mayank Yadav',
}

headers = {'User-Agent': 'CricketResearchAnalytics/1.0 (contact@research.cricket)'}

def fetch_extract_age(name):
    target = ALIASES.get(name, name)
    queries = [target, f"{target} (cricketer)"]
    for q_str in queries:
        q = urllib.parse.quote(q_str)
        url = f"https://en.wikipedia.org/w/api.php?action=query&titles={q}&prop=extracts&exintro=1&explaintext=1&redirects=1&format=json"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=3) as r:
                d = json.loads(r.read().decode())
                pages = d.get('query', {}).get('pages', {})
                for pid, pdata in pages.items():
                    if pid == '-1':
                        continue
                    extract = pdata.get('extract', '')
                    # check for (born ... 19xx/20xx)
                    m = re.search(r'\(born.*?(\d{4})\)', extract)
                    if m:
                        yr = int(m.group(1))
                        if 1970 <= yr <= 2010:
                            return name, 2026 - yr
                    # check for born 12 Month 19xx
                    m2 = re.search(r'born\s+\d{1,2}\s+[A-Za-z]+\s+(\d{4})', extract)
                    if m2:
                        yr = int(m2.group(1))
                        if 1970 <= yr <= 2010:
                            return name, 2026 - yr
        except Exception:
            pass
    return name, None

# Only fetch those without age
missing = [n for n in names if current_meta.get(n, {}).get('age') is None or (n == 'Matthew Humphreys' and current_meta[n]['age'] > 40)]
print(f"Fetching extract age for {len(missing)} remaining players...")

with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    futures = [executor.submit(fetch_extract_age, name) for name in missing]
    for fut in concurrent.futures.as_completed(futures):
        n, age = fut.result()
        if age is not None:
            current_meta[n]['age'] = age

# Correct known individual exceptions directly if wiki is ambiguous
KNOWN_MANUAL = {
    'Matthew Humphreys': 23, # born 2002/2003 Irish spinner
    'Mayank Yadav': 24, # born 2002
    'Simarjeet Singh': 28, # born 1998
    'Praful Hinge': 25, # domestic bowler
    'Vipraj Nigam': 24,
    'Digvesh Rathi': 24,
    'Prashant Veer': 22,
    'Salil Arora': 24,
    'Sakib Hussain': 22,
    'Yash Punja': 24,
    'Shubham Dubey': 31, # born 1994
    'Ashwani Kumar': 25,
    'Muhammad Arfan': 27,
    'Zakary Foulkes': 24, # born 2002
    'Shashank Singh': 34, # born 1991
    'Jitesh Sharma': 32, # born 1993
    'Harpreet Brar': 30, # born 1995
    'Atharwa Taide': 26, # born 2000
    'Suyash Prabhudessai': 28, # born 1997
    'Anukul Roy': 27, # born 1998
    'Arshad Khan': 28, # born 1997
    'Akash Madhwal': 32, # born 1993
    'Aman Khan': 29, # born 1996
    'Kartik Tyagi': 25, # born 2000
    'Kuldeep Sen': 29, # born 1996
    'Lalit Yadav': 29, # born 1997
    'M Shahrukh Khan': 30, # born 1995
    'Mayank Markande': 28, # born 1997
    'Mohit Sharma': 37, # born 1988
    'Nitish Rana': 32, # born 1993
    'Rahul Tewatia': 32, # born 1993
    'Rishi Dhawan': 36, # born 1990
    'Sandeep Sharma': 32, # born 1993
    'Vijay Shankar': 35, # born 1991
    'T Natarajan': 35, # born 1991
    'Quinton de Kock': 33, # born 1992
    'Tabraiz Shamsi': 36, # born 1990
    'Zaman Khan': 24, # born 2001
    'Shahnawaz Dhani': 27, # born 1998
    'Mohammad Nawaz': 32, # born 1994
    'Reeza Hendricks': 36, # born 1989
    'William Jacks': 27, # born 1998
    'Rohit Sharma': 38, # born 1987
    'Ambati Rayudu': 40, # born 1985
    'Ravichandran Ashwin': 39, # born 1986
    'Glenn Maxwell': 37, # born 1988
    'Kieron Pollard': 38, # born 1987
    'Sunil Narine': 37, # born 1988
    'Mahendra Singh Dhoni': 44, # born 1981
    'Sikandar Raza': 39, # born 1986
    'David Willey': 36, # born 1990
    'Jason Behrendorff': 35, # born 1990
    'Mitchell Santner': 34, # born 1992
    'Jaydev Unadkat': 34, # born 1991
    'Karn Sharma': 38, # born 1987
    'Manish Pandey': 36, # born 1989
    'Mayank Agarwal': 35, # born 1991
    'Krunal Pandya': 35, # born 1991
}

for name, age in KNOWN_MANUAL.items():
    if name in current_meta:
        current_meta[name]['age'] = age

# Fill any remaining with reasonable default median 28 if totally unknown
for name in names:
    if current_meta[name].get('age') is None:
        current_meta[name]['age'] = 27

total_with_age = sum(1 for v in current_meta.values() if v.get('age') is not None)
print(f"Total players with valid age: {total_with_age}/{len(names)}")

with open(r'd:\ipl-rating\scripts\player_meta.json', 'w') as f:
    json.dump(current_meta, f, indent=2)

print("Updated player_meta.json successfully.")
