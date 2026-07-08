import json
import sys

with open('d:/ipl-rating/ipl/app/page.tsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the insertion point for state and useMemo
state_idx = -1
for i, line in enumerate(lines):
    if 'const [allRoundersPage, setAllRoundersPage] = useState(1);' in line:
        state_idx = i
        break

state_insertion = '''  const [playoffPage, setPlayoffPage] = useState(1);

  const playoffLegends = useMemo(() => {
    if (data.length === 0) return [];
    
    let maxBat = 0;
    let maxBowl = 0;
    data.forEach(p => {
      const batPlayoff = Number(p.bat_playoff_impact) || 0;
      const bowlPlayoff = Number(p.bowl_playoff_impact) || 0;
      if (batPlayoff > maxBat) maxBat = batPlayoff;
      if (bowlPlayoff > maxBowl) maxBowl = bowlPlayoff;
    });

    return [...data]
      .filter(p => (Number(p.bat_playoff_impact) > 0 || Number(p.bowl_playoff_impact) > 0))
      .map(p => {
        const batPlayoff = Number(p.bat_playoff_impact) || 0;
        const bowlPlayoff = Number(p.bowl_playoff_impact) || 0;
        
        const batNorm = maxBat > 0 ? batPlayoff / maxBat : 0;
        const bowlNorm = maxBowl > 0 ? bowlPlayoff / maxBowl : 0;
        
        const clutchScore = (batNorm + bowlNorm) * 50;
        
        return {
          ...p,
          batPlayoff,
          bowlPlayoff,
          clutchScore
        };
      })
      .sort((a, b) => b.clutchScore - a.clutchScore);
  }, [data]);
'''

if state_idx != -1:
    lines.insert(state_idx + 1, state_insertion)

# Re-read to find the next insertion point
for i, line in enumerate(lines):
    if '{/* 6.75 SCATTER PLOT */}' in line:
        ui_idx = i
        break

ui_insertion = '''      {/* 6.6. PLAYOFF LEGENDS */}
      {playoffLegends.length > 0 && (
        <section className="py-32 px-8 bg-zinc-950 text-white relative overflow-hidden">
          <div className="absolute inset-0 opacity-15 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-amber-900 via-zinc-950 to-zinc-950"></div>
          <div className="max-w-7xl mx-auto relative z-10">
            <div className="mb-16">
              <h2 className="text-4xl md:text-5xl font-bold tracking-tighter mb-4 text-white">Playoff Legends</h2>
              <p className="text-zinc-400 text-xl font-light">The ultimate clutch performers. Ranked by equal-weighted Playoff Impact for both batting and bowling.</p>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse whitespace-nowrap">
                <thead>
                  <tr className="border-b border-zinc-800">
                    <th className="px-6 py-4 text-[10px] font-black tracking-[0.2em] uppercase text-zinc-500">Rank</th>
                    <th className="px-4 py-4 text-[10px] font-black tracking-[0.2em] uppercase text-zinc-500">Player</th>
                    <th className="px-4 py-4 text-[10px] font-black tracking-[0.2em] uppercase text-zinc-500">Season</th>
                    <th className="px-4 py-4 text-[10px] font-black tracking-[0.2em] uppercase text-zinc-500">Team</th>
                    <th className="px-4 py-4 text-[10px] font-black tracking-[0.2em] uppercase text-amber-500">Clutch Score</th>
                    <th className="px-4 py-4 text-[10px] font-black tracking-[0.2em] uppercase text-zinc-500">Bat Playoff</th>
                    <th className="px-4 py-4 text-[10px] font-black tracking-[0.2em] uppercase text-zinc-500">Bowl Playoff</th>
                  </tr>
                </thead>
                <tbody>
                  {playoffLegends.slice((playoffPage - 1) * 20, playoffPage * 20).map((row: any, i: number) => {
                    const tColor = getTeamColor(row.primary_team);
                    return (
                      <tr 
                        key={i}
                        className="border-b border-zinc-800/50 hover:bg-zinc-900/50 transition-colors cursor-pointer group"
                        onClick={() => setSelectedPlayer(row)}
                      >
                        <td className="px-6 py-4 text-xs font-black text-zinc-500 tabular-nums">
                          #{(playoffPage - 1) * 20 + i + 1}
                        </td>
                        <td className="px-4 py-4 relative pl-6">
                          <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-3/4 opacity-70" style={{ backgroundColor: tColor }}></div>
                          <span className="font-semibold text-white text-[15px] tracking-tight">{row.player_name}</span>
                        </td>
                        <td className="px-4 py-4 text-sm text-zinc-400 tabular-nums">{row.season}</td>
                        <td className="px-4 py-4 text-[11px] font-bold tracking-wider text-zinc-500 uppercase">
                          {row.primary_team}
                        </td>
                        <td className="px-4 py-4 font-black text-sm tabular-nums text-amber-500">
                          {Number(row.clutchScore).toFixed(1)}
                        </td>
                        <td className="px-4 py-4 text-sm text-zinc-400 tabular-nums">
                          {Number(row.batPlayoff).toFixed(1)}
                        </td>
                        <td className="px-4 py-4 text-sm text-zinc-400 tabular-nums">
                          {Number(row.bowlPlayoff).toFixed(1)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            
            {playoffLegends.length > 20 && (
              <div className="flex justify-center items-center gap-4 mt-8 pt-8 border-t border-zinc-800">
                <button 
                  onClick={() => setPlayoffPage(p => Math.max(1, p - 1))}
                  disabled={playoffPage === 1}
                  className="px-6 py-2 border border-zinc-700 rounded-sm text-sm font-semibold text-zinc-400 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-zinc-800 transition-colors"
                >
                  Previous
                </button>
                <span className="text-sm font-semibold text-zinc-500">
                  Page {playoffPage} of {Math.ceil(playoffLegends.length / 20)}
                </span>
                <button 
                  onClick={() => setPlayoffPage(p => p + 1)}
                  disabled={playoffPage * 20 >= playoffLegends.length}
                  className="px-6 py-2 border border-zinc-700 rounded-sm text-sm font-semibold text-zinc-400 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-zinc-800 transition-colors"
                >
                  Next
                </button>
              </div>
            )}
          </div>
        </section>
      )}

'''

if ui_idx != -1:
    lines.insert(ui_idx, ui_insertion)

with open('d:/ipl-rating/ipl/app/page.tsx', 'w', encoding='utf-8') as f:
    f.writelines(lines)
