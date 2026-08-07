import re

with open('ipl/app/page.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

if 'const formatSeason' not in content:
    content = content.replace(
        'const v11MetricNames',
        'const formatSeason = (season: string | number) => {\n  const s = String(season);\n  if (s === \'2007/08\') return \'2008\';\n  if (s === \'2009/10\') return \'2010\';\n  if (s === \'2020/21\') return \'2020\';\n  return s;\n};\n\nconst v11MetricNames'
    )

content = content.replace('>{s}</option>', '>{formatSeason(s)}</option>')
content = content.replace('">{row.season}</td>', '">{formatSeason(row.season)}</td>')
content = content.replace('• {s.season}</span>', '• {formatSeason(s.season)}</span>')
content = content.replace('• {p.season}</span>', '• {formatSeason(p.season)}</span>')
content = content.replace('• {pData.season}</div>', '• {formatSeason(pData.season)}</div>')
content = content.replace('Season {selectedPlayer.season}', 'Season {formatSeason(selectedPlayer.season)}')
content = content.replace('String(p.season).slice(-2)', 'formatSeason(p.season).slice(-2)')
content = content.replace('String(cp.season).slice(-2)', 'formatSeason(cp.season).slice(-2)')
content = content.replace('>{s.season}</span>', '>{formatSeason(s.season)}</span>')

with open('ipl/app/page.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print('Replacements done.')
