"use client";

import { useState, useEffect, useMemo } from 'react';

// ── Types ────────────────────────────────────────────────────────────────────
interface PressurePlayer {
  player_id: number;
  player_name: string;
  nationality: string;
  age: number | null;
  is_pakistani: boolean;
  has_ipl: boolean;
  has_t20i: boolean;
  ipl_balls: number;
  t20i_balls: number;
  total_pressure_balls: number;
  ipl_rating: number | null;
  t20i_rating: number | null;
  pres_metric: number | null;
  base_metric: number | null;
  pres_wkts?: number;
  combined_score: number;
}

interface WarRoomData {
  metadata: {
    title: string;
    author: string;
    season_target: string;
    dataset_scope: string;
    heritage: string;
  };
  audit_2026: {
    record: { matches: number; wins: number; losses: number; finish: string };
    phase_comparison: {
      bowling: Array<{
        phase: string;
        win_econ: number;
        loss_econ: number;
        win_wkts: number;
        loss_wkts: number;
        delta_econ: string;
        verdict: string;
      }>;
      batting: Array<{
        phase: string;
        win_sr: number;
        loss_sr: number;
        delta_sr: string;
        verdict: string;
      }>;
    };
    squad_apex_ratings: Array<{
      name: string;
      role: string;
      runs: number;
      sr: number;
      wkts: number;
      econ: number;
      quwrof_pctile: number;
      notes: string;
    }>;
  };
  gaps: Array<{
    gap_id: string;
    title: string;
    phase: string;
    problem: string;
    benchmark: string;
    recommendations: Array<{
      name: string;
      country: string;
      age: number;
      type: string;
      death_pres_econ?: number;
      overall_bowpr?: number;
      pp_wkts?: number;
      pp_econ?: number;
      death_pres_sr?: number;
      overall_bpr?: number;
      verdict: string;
    }>;
  }>;
  top10_batters: Array<{
    rank: number;
    name: string;
    nationality: string;
    age: number;
    score: number;
    pres_balls: number;
    pres_sr: number;
    base_sr: number;
    role: string;
    rr_fit: string;
  }>;
  top10_bowlers: Array<{
    rank: number;
    name: string;
    nationality: string;
    age: number;
    score: number;
    pres_balls: number;
    pres_econ: number;
    base_econ: number;
    pres_wkts: number;
    role: string;
    rr_fit: string;
  }>;
}

// Tactical Player Archetypes Needed by RR
const tacticalArchetypes = [
  {
    id: 'archetype-1',
    code: 'ARCHETYPE 01',
    title: "Archer's Death Lockdown Partner",
    role: "Heavy-Ball Fast Seamer (Overs 16-20)",
    deficitAddressed: "Conceding 12.30 RPO in death overs in defeats (vs 9.24 in wins). Sandeep Sharma & Tushar Deshpande collapsed when Archer bowled out.",
    physicalProfile: "Tall hit-the-deck pacer capable of 142-148 km/h. High release point to generate steep bounce.",
    technicalRepertoire: [
      "Wide yorkers outside off stump denying straight boundary arc",
      "Hard back-of-a-length deliveries into the pitch forcing mistimed pulls",
      "Off-cutter and knuckle-ball variations with disguise"
    ],
    venueFitJaipur: "Sawai Mansingh Stadium has 75m-80m square boundaries. Steep bounce into the pitch prevents mis-hits from clearing the rope.",
    benchmarkMetrics: "Death Pressure Economy < 9.50 RPO | Pressure Dot % > 32% | Yorker execution rate > 40%",
    primaryTargets: [
      { name: "Jamie Overton", origin: "England", age: 32, stat: "6.62 Death Pres Econ", score: "1.3119 BowPR", notes: "Nails wide yorkers at high pace; lower-order hitting weapon." },
      { name: "Sakib Hussain", origin: "India", age: 22, stat: "7.70 Death Pres Econ", score: "1.3108 BowPR", notes: "Uncapped Indian diamond; 11 pressure wkts; frees an overseas slot." },
      { name: "Maheesh Theekshana", origin: "Sri Lanka", age: 26, stat: "6.00 Death Pres Econ", score: "1.1779 BowPR", notes: "Mystery spin choke; lethal on SMS Jaipur's abrasive clay surface." }
    ]
  },
  {
    id: 'archetype-2',
    code: 'ARCHETYPE 02',
    title: "Powerplay Breakthrough Seamer",
    role: "Frontline New-Ball Striker (Overs 1-6)",
    deficitAddressed: "Taking only 4 wickets across 42 powerplay overs in 7 defeats (0.57 wkts/match) while leaking 11.50 RPO.",
    physicalProfile: "Dynamic swing or seam bowler with rapid arm speed, presenting a proud upright seam.",
    technicalRepertoire: [
      "Conventional outswing to right-handers testing the outside edge",
      "Sharp nip-backer targeting top of off-stump / front pad",
      "Controlled wobble seam on hard lengths to eliminate drive options"
    ],
    venueFitJaipur: "Early evening air in Jaipur aids seam movement. Early wickets push opposition into defensive middle-overs rebuilding.",
    benchmarkMetrics: "Powerplay Wickets > 1.2 per game | Powerplay Economy < 8.20 RPO | Powerplay Dot % > 45%",
    primaryTargets: [
      { name: "Mohammed Siraj", origin: "India", age: 32, stat: "45 PP Wickets, 7.98 Econ", score: "1.1521 BowPR", notes: "Proven Indian frontline spearhead with relentless aggression." },
      { name: "Khaleel Ahmed", origin: "India", age: 29, stat: "26 PP Wickets, 7.79 Econ", score: "1.1080 BowPR", notes: "Native Rajasthan experience; left-arm angle across right-handers." },
      { name: "Arshdeep Singh", origin: "India", age: 27, stat: "31 PP Wickets, 8.47 Econ", score: "1.1295 BowPR", notes: "Dual-phase weapon; can bowl overs 1, 3, 18, and 20." }
    ]
  },
  {
    id: 'archetype-3',
    code: 'ARCHETYPE 03',
    title: "Clutch Middle/Death Finisher",
    role: "360-Degree Finisher & Spin Neutralizer (Overs 12-20)",
    deficitAddressed: "Shimron Hetmyer slump (113.0 SR, 0 bat impact points). Middle overs SR fell from 161.9 in wins down to 142.6 in defeats.",
    physicalProfile: "Quick-wristed power hitter with agile footwork, high bat speed, and athletic between-the-wickets acceleration.",
    technicalRepertoire: [
      "Uninhibited bat-swing against high pace into the blockhole",
      "Sweep and reverse-sweep proficiency against wrist-spin and finger-spin",
      "Ability to score boundaries immediately without needing a 10-ball warm-up"
    ],
    venueFitJaipur: "Cavernous Jaipur outfield demands running hard twos alongside boundaries. 360-degree shot-making splits defensive boundary riders.",
    benchmarkMetrics: "Pressure Death SR > 185.0 | Boundary % > 22% | Chase Win Involvement > 60%",
    primaryTargets: [
      { name: "Naman Dhir", origin: "India", age: 27, stat: "209.5 Death Pres SR", score: "1.0362 BPR", notes: "Attacks spin in middle overs and pace at the death; saves overseas slot." },
      { name: "Cooper Connolly", origin: "Australia", age: 23, stat: "212.8 Death Pres SR", score: "1.0514 BPR", notes: "Left-handed composure; agile fielder; delivers left-arm orthodox." },
      { name: "Shashank Singh", origin: "India", age: 34, stat: "185.1 Pressure SR", score: "1.0269 BPR", notes: "Battle-hardened domestic finisher with multiple 200+ IPL chase rescues." }
    ]
  }
];

export default function RRWarRoomPage() {
  const [data, setData] = useState<WarRoomData | null>(null);
  const [pressureBatters, setPressureBatters] = useState<PressurePlayer[]>([]);
  const [pressureBowlers, setPressureBowlers] = useState<PressurePlayer[]>([]);
  const [loading, setLoading] = useState(true);

  // View state
  const [activeSection, setActiveSection] = useState<'rankings' | 'archetypes' | 'audit' | 'metrics' | 'dossier'>('rankings');
  const [role, setRole] = useState<'batter' | 'bowler'>('batter');
  const [viewMode, setViewMode] = useState<'targets' | 'all'>('targets');

  // Filters
  const [originFilter, setOriginFilter] = useState<'all' | 'indian' | 'overseas'>('all');
  const [nationalityFilter, setNationalityFilter] = useState<string>('all');
  const [ageFilter, setAgeFilter] = useState<'all' | 'u25' | '25-30' | '30plus'>('all');
  const [includePakistani, setIncludePakistani] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [minBalls, setMinBalls] = useState<number>(50);
  const [selectedPlayer, setSelectedPlayer] = useState<PressurePlayer | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [resWarRoom, resPressure] = await Promise.all([
          fetch('/rr_war_room_data.json'),
          fetch('/pressure_data.json')
        ]);
        const wData = await resWarRoom.json();
        const pData = await resPressure.json();
        setData(wData);
        setPressureBatters(pData.batters || []);
        setPressureBowlers(pData.bowlers || []);
      } catch (err) {
        console.error('Failed to load war room data', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const currentPool = role === 'batter' ? pressureBatters : pressureBowlers;

  const availableNationalities = useMemo(() => {
    const setN = new Set<string>();
    currentPool.forEach(p => {
      if (p.nationality && p.nationality !== 'Unknown') {
        if (!includePakistani && (p.nationality === 'Pakistan' || p.is_pakistani)) return;
        setN.add(p.nationality);
      }
    });
    return Array.from(setN).sort();
  }, [currentPool, includePakistani]);

  const filteredList = useMemo(() => {
    return currentPool.filter(p => {
      // Pakistani filter
      if (!includePakistani && (p.is_pakistani || p.nationality === 'Pakistan')) return false;

      // Origin filter
      if (originFilter === 'indian' && p.nationality !== 'India') return false;
      if (originFilter === 'overseas' && p.nationality === 'India') return false;

      // Nationality dropdown
      if (nationalityFilter !== 'all' && p.nationality !== nationalityFilter) return false;

      // Age filter
      if (ageFilter === 'u25' && (p.age === null || p.age >= 25)) return false;
      if (ageFilter === '25-30' && (p.age === null || p.age < 25 || p.age > 30)) return false;
      if (ageFilter === '30plus' && (p.age === null || p.age <= 30)) return false;

      // Min balls
      if (p.total_pressure_balls < minBalls) return false;

      // Search
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        if (!p.player_name.toLowerCase().includes(q)) return false;
      }

      return true;
    });
  }, [currentPool, includePakistani, originFilter, nationalityFilter, ageFilter, minBalls, searchQuery]);

  const displayedList = viewMode === 'targets' ? filteredList.slice(0, 10) : filteredList;

  if (loading || !data) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] text-zinc-300 flex flex-col items-center justify-center p-6">
        <div className="w-8 h-8 border-2 border-zinc-500 border-t-white rounded-full animate-spin mb-3" />
        <div className="text-xs font-mono uppercase tracking-widest text-zinc-400">Loading Pressure Engine & Squad Audit...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-zinc-200 font-sans selection:bg-[#b39170] selection:text-white">
      {/* ── NAVBAR ──────────────────────────────────────────────────────── */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-4 sm:px-8 py-3.5 bg-[#0a0a0a]/95 backdrop-blur border-b border-zinc-900">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 bg-[#b39170] rounded-sm flex items-center justify-center font-bold text-black text-xs shadow-md shadow-[#b39170]/20">
            RR
          </div>
          <div>
            <span className="text-sm font-bold tracking-tight text-white">SupeRR Selector</span>
            <span className="text-[10px] text-zinc-500 font-mono ml-2 uppercase">2027 War Room</span>
          </div>
        </div>

        <div className="flex items-center gap-1 sm:gap-2">
          {[
            { id: 'rankings', label: 'Rankings & Pool' },
            { id: 'archetypes', label: 'Target Profiles' },
            { id: 'audit', label: '2026 Season Audit' },
            { id: 'metrics', label: 'Engine Methodology' },
            { id: 'dossier', label: 'Executive Dossier' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveSection(tab.id as any)}
              className={`px-3 py-1.5 rounded-sm text-xs font-medium transition-colors ${
                activeSection === tab.id
                  ? 'bg-zinc-800 text-white font-semibold border border-zinc-700'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </nav>

      {/* ── BODY ────────────────────────────────────────────────────────── */}
      <div className="pt-20 pb-20 max-w-7xl mx-auto px-4 sm:px-8 space-y-12">

        {/* ── SECTION 1: RANKINGS & PLAYER POOL (FIRST THING VISIBLE) ── */}
        {activeSection === 'rankings' && (
          <div className="space-y-6">
            {/* Context Header */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-zinc-900 pb-5">
              <div>
                <div className="text-[11px] font-mono uppercase tracking-widest text-[#b39170] mb-1">
                  Dual-Criterion Pressure Performance Index
                </div>
                <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white">
                  {role === 'batter' ? 'Top Batsmen Under Pressure' : 'Top Bowlers Under Pressure'}
                </h1>
                <p className="text-xs text-zinc-400 mt-1 max-w-2xl leading-relaxed">
                  Evaluated across 200,999 deliveries (IPL 2022–2026 & T20Is). 
                  Combines 50% Normalized Absolute Output with 50% Relative Maintenance via 65:35 IPL-weighted Bayesian shrinkage.
                </p>
              </div>

              {/* Primary Role Switcher */}
              <div className="flex items-center gap-2 self-start md:self-auto">
                <div className="inline-flex rounded-sm bg-zinc-900 p-0.5 border border-zinc-800">
                  <button
                    onClick={() => { setRole('batter'); setSelectedPlayer(null); }}
                    className={`px-4 py-1.5 rounded-sm text-xs font-semibold transition ${
                      role === 'batter' ? 'bg-[#b39170] text-black font-bold' : 'text-zinc-400 hover:text-white'
                    }`}
                  >
                    Batsmen ({pressureBatters.length})
                  </button>
                  <button
                    onClick={() => { setRole('bowler'); setSelectedPlayer(null); }}
                    className={`px-4 py-1.5 rounded-sm text-xs font-semibold transition ${
                      role === 'bowler' ? 'bg-[#b39170] text-black font-bold' : 'text-zinc-400 hover:text-white'
                    }`}
                  >
                    Bowlers ({pressureBowlers.length})
                  </button>
                </div>

                <div className="inline-flex rounded-sm bg-zinc-900 p-0.5 border border-zinc-800">
                  <button
                    onClick={() => setViewMode('targets')}
                    className={`px-3 py-1.5 rounded-sm text-xs font-semibold transition ${
                      viewMode === 'targets' ? 'bg-zinc-800 text-white' : 'text-zinc-500 hover:text-zinc-300'
                    }`}
                  >
                    Top 10 Targets
                  </button>
                  <button
                    onClick={() => setViewMode('all')}
                    className={`px-3 py-1.5 rounded-sm text-xs font-semibold transition ${
                      viewMode === 'all' ? 'bg-zinc-800 text-white' : 'text-zinc-500 hover:text-zinc-300'
                    }`}
                  >
                    Full Pool
                  </button>
                </div>
              </div>
            </div>

            {/* Filter Bar */}
            <div className="p-3.5 rounded-sm bg-[#111] border border-zinc-900 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
              <div className="lg:col-span-2">
                <label className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 block mb-1">Search Player</label>
                <input
                  type="text"
                  placeholder="Filter by name..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-sm px-3 py-1.5 text-xs text-white placeholder-zinc-600 focus:outline-none focus:border-zinc-600"
                />
              </div>

              <div>
                <label className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 block mb-1">Origin</label>
                <select
                  value={originFilter}
                  onChange={e => setOriginFilter(e.target.value as any)}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-sm px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-zinc-600"
                >
                  <option value="all">All Origins</option>
                  <option value="indian">Indian Only</option>
                  <option value="overseas">Overseas Only</option>
                </select>
              </div>

              <div>
                <label className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 block mb-1">Nationality</label>
                <select
                  value={nationalityFilter}
                  onChange={e => setNationalityFilter(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-sm px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-zinc-600"
                >
                  <option value="all">All Countries</option>
                  {availableNationalities.map(n => (
                    <option key={n} value={n}>{n}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 block mb-1">Age Bracket</label>
                <select
                  value={ageFilter}
                  onChange={e => setAgeFilter(e.target.value as any)}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-sm px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-zinc-600"
                >
                  <option value="all">All Ages</option>
                  <option value="u25">Under 25</option>
                  <option value="25-30">25 to 30</option>
                  <option value="30plus">30+ Years</option>
                </select>
              </div>

              <div>
                <label className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 block mb-1">Min Pressure Balls</label>
                <select
                  value={minBalls}
                  onChange={e => setMinBalls(Number(e.target.value))}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-sm px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-zinc-600"
                >
                  <option value={30}>30+ Balls</option>
                  <option value={50}>50+ Balls (Official)</option>
                  <option value={100}>100+ Balls (High Vol)</option>
                  <option value={200}>200+ Balls (Core)</option>
                </select>
              </div>
            </div>

            {/* Ineligibility Toggle Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 px-3.5 py-2 rounded-sm bg-zinc-950 border border-zinc-900 text-xs">
              <div className="text-[11px] text-zinc-400">
                <span className="font-semibold text-zinc-300">IPL Eligibility Filter:</span> Pakistani players excluded from primary auction submission.
              </div>
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={includePakistani}
                  onChange={e => setIncludePakistani(e.target.checked)}
                  className="rounded border-zinc-700 bg-zinc-800 text-zinc-300 focus:ring-0"
                />
                <span className="text-zinc-400 text-xs font-mono">Show Pakistani Players ({includePakistani ? 'Visible' : 'Hidden'})</span>
              </label>
            </div>

            {/* Main Table */}
            <div className="rounded-sm border border-zinc-900 bg-[#111] overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#141414] text-zinc-400 uppercase tracking-wider text-[10px] font-mono border-b border-zinc-800">
                  <tr>
                    <th className="py-3 px-4">Rank</th>
                    <th className="py-3 px-4">Player</th>
                    <th className="py-3 px-3">Origin</th>
                    <th className="py-3 px-3">Age</th>
                    <th className="py-3 px-3 text-right">Pres Balls</th>
                    <th className="py-3 px-3 text-right">{role === 'batter' ? 'Pres SR' : 'Pres Econ'}</th>
                    <th className="py-3 px-3 text-right">{role === 'batter' ? 'Base SR' : 'Base Econ'}</th>
                    <th className="py-3 px-3 text-right">Delta</th>
                    {role === 'bowler' && <th className="py-3 px-3 text-right">Pres Wkts</th>}
                    <th className="py-3 px-3 text-right">IPL Index</th>
                    <th className="py-3 px-3 text-right">T20I Index</th>
                    <th className="py-3 px-4 text-right font-bold text-white">Combined Rating</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-900 font-mono">
                  {displayedList.map((p, idx) => {
                    const isBatter = role === 'batter';
                    const presVal = p.pres_metric ?? 0;
                    const baseVal = p.base_metric ?? 0;
                    const delta = presVal - baseVal;
                    const isPositive = isBatter ? delta > 0 : delta < 0;

                    return (
                      <tr 
                        key={p.player_id} 
                        onClick={() => setSelectedPlayer(p)}
                        className="hover:bg-zinc-800/40 transition cursor-pointer"
                      >
                        <td className="py-3 px-4 font-bold text-zinc-500">#{idx + 1}</td>
                        <td className="py-3 px-4 font-sans font-bold text-white">
                          <div className="flex items-center gap-2">
                            <span>{p.player_name}</span>
                            {p.is_pakistani && (
                              <span className="text-[9px] px-1 py-0.2 rounded bg-zinc-800 text-zinc-400 border border-zinc-700 font-mono">
                                PAK
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-3 font-sans text-zinc-400">{p.nationality}</td>
                        <td className="py-3 px-3 text-zinc-400">{p.age ? `${p.age}` : '—'}</td>
                        <td className="py-3 px-3 text-right text-zinc-300">{p.total_pressure_balls}</td>
                        <td className="py-3 px-3 text-right font-bold text-white">{presVal.toFixed(1)}</td>
                        <td className="py-3 px-3 text-right text-zinc-500">{baseVal.toFixed(1)}</td>
                        <td className={`py-3 px-3 text-right font-bold ${isPositive ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {delta > 0 ? `+${delta.toFixed(1)}` : delta.toFixed(1)}
                        </td>
                        {!isBatter && (
                          <td className="py-3 px-3 text-right text-zinc-300">{p.pres_wkts ?? 0}</td>
                        )}
                        <td className="py-3 px-3 text-right text-zinc-500">
                          {p.ipl_rating ? p.ipl_rating.toFixed(3) : '—'}
                        </td>
                        <td className="py-3 px-3 text-right text-zinc-500">
                          {p.t20i_rating ? p.t20i_rating.toFixed(3) : '—'}
                        </td>
                        <td className="py-3 px-4 text-right font-black text-[#b39170] text-sm">
                          {p.combined_score.toFixed(4)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            
            <div className="text-right text-[11px] text-zinc-500">
              Showing {displayedList.length} of {filteredList.length} matching candidates
            </div>

            {/* Selected Player Detail Card */}
            {selectedPlayer && (
              <div className="p-5 rounded-sm bg-[#141414] border border-zinc-800 space-y-4">
                <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
                  <div>
                    <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500">Selected Player Profile</span>
                    <h3 className="text-lg font-bold text-white">{selectedPlayer.player_name}</h3>
                    <div className="text-xs text-zinc-400 mt-0.5">
                      {selectedPlayer.nationality} • Age {selectedPlayer.age ?? 'Unknown'} • Total Pressure Deliveries: {selectedPlayer.total_pressure_balls}
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedPlayer(null)}
                    className="text-xs text-zinc-500 hover:text-white px-2 py-1 rounded border border-zinc-800"
                  >
                    Close
                  </button>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
                  <div className="p-3 rounded bg-zinc-900 border border-zinc-800">
                    <span className="text-zinc-500 block text-[10px] uppercase">Combined Rating</span>
                    <span className="text-base font-bold text-[#b39170]">{selectedPlayer.combined_score.toFixed(4)}</span>
                  </div>
                  <div className="p-3 rounded bg-zinc-900 border border-zinc-800">
                    <span className="text-zinc-500 block text-[10px] uppercase">{role === 'batter' ? 'Pressure SR' : 'Pressure Econ'}</span>
                    <span className="text-base font-bold text-white">{(selectedPlayer.pres_metric ?? 0).toFixed(1)}</span>
                  </div>
                  <div className="p-3 rounded bg-zinc-900 border border-zinc-800">
                    <span className="text-zinc-500 block text-[10px] uppercase">{role === 'batter' ? 'Baseline SR' : 'Baseline Econ'}</span>
                    <span className="text-base font-bold text-zinc-400">{(selectedPlayer.base_metric ?? 0).toFixed(1)}</span>
                  </div>
                  <div className="p-3 rounded bg-zinc-900 border border-zinc-800">
                    <span className="text-zinc-500 block text-[10px] uppercase">Format Sub-Scores</span>
                    <span className="text-xs text-zinc-300 block mt-1">
                      IPL: {selectedPlayer.ipl_rating ? selectedPlayer.ipl_rating.toFixed(2) : 'None'} | T20I: {selectedPlayer.t20i_rating ? selectedPlayer.t20i_rating.toFixed(2) : 'None'}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── SECTION 2: TARGET ARCHETYPES (REPLACING PLAYING XI) ── */}
        {activeSection === 'archetypes' && (
          <div className="space-y-8">
            <div className="border-b border-zinc-900 pb-4">
              <div className="text-[11px] font-mono uppercase tracking-widest text-[#b39170] mb-1">
                Franchise War Room Blueprint
              </div>
              <h2 className="text-2xl font-black text-white tracking-tight">
                Target Player Archetypes to Solve RR's 3 Defeat Gaps
              </h2>
              <p className="text-xs text-zinc-400 mt-1 max-w-2xl leading-relaxed">
                Rather than prescribing a fixed starting XI, our model defines the precise physical, tactical, and venue-specific profiles needed to eliminate the three phase deficits from IPL 2026.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-8">
              {tacticalArchetypes.map(arc => (
                <div key={arc.id} className="p-6 rounded-sm bg-[#111] border border-zinc-900 space-y-6">
                  {/* Top Bar */}
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-800/80 pb-4">
                    <div>
                      <span className="text-[10px] font-mono tracking-widest text-[#b39170] uppercase block">{arc.code}</span>
                      <h3 className="text-lg font-bold text-white tracking-tight mt-0.5">{arc.title}</h3>
                      <span className="text-xs text-zinc-400 font-mono">{arc.role}</span>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] font-mono uppercase text-zinc-500 block">Benchmark Standard</span>
                      <span className="text-xs font-mono font-semibold text-zinc-300">{arc.benchmarkMetrics}</span>
                    </div>
                  </div>

                  {/* Core Tactical Deficit */}
                  <div className="p-3.5 rounded bg-zinc-950 border border-zinc-900 text-xs">
                    <span className="font-mono text-rose-400 uppercase tracking-wider font-semibold block mb-1">Quantified Deficit in 2026</span>
                    <span className="text-zinc-300 leading-relaxed">{arc.deficitAddressed}</span>
                  </div>

                  {/* Profile Details */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                    <div className="space-y-2">
                      <span className="font-mono text-[11px] uppercase tracking-wider text-zinc-400 block font-semibold">Physical Attributes</span>
                      <p className="text-zinc-300 leading-relaxed">{arc.physicalProfile}</p>
                    </div>

                    <div className="space-y-2">
                      <span className="font-mono text-[11px] uppercase tracking-wider text-zinc-400 block font-semibold">Technical Repertoire</span>
                      <ul className="space-y-1 text-zinc-300">
                        {arc.technicalRepertoire.map((tech, idx) => (
                          <li key={idx} className="flex items-start gap-1.5">
                            <span className="text-zinc-500">•</span>
                            <span>{tech}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="space-y-2">
                      <span className="font-mono text-[11px] uppercase tracking-wider text-zinc-400 block font-semibold">SMS Jaipur Venue Fit</span>
                      <p className="text-zinc-300 leading-relaxed">{arc.venueFitJaipur}</p>
                    </div>
                  </div>

                  {/* Qualified Target Shortlist */}
                  <div className="space-y-3 pt-2">
                    <span className="font-mono text-[10px] uppercase tracking-wider text-zinc-500 block">Identified Candidates from Engine</span>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      {arc.primaryTargets.map((tar, tIdx) => (
                        <div key={tIdx} className="p-3 rounded bg-zinc-900/80 border border-zinc-800">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-white text-xs">{tar.name}</span>
                            <span className="text-[10px] font-mono text-zinc-400">{tar.origin}</span>
                          </div>
                          <div className="text-[11px] font-mono text-emerald-400 mt-1 font-semibold">{tar.stat}</div>
                          <div className="text-[10px] font-mono text-[#b39170]">{tar.score}</div>
                          <p className="text-[11px] text-zinc-400 mt-2 border-t border-zinc-800 pt-1.5 leading-tight">{tar.notes}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── SECTION 3: RR 2026 AUDIT ── */}
        {activeSection === 'audit' && (
          <div className="space-y-8">
            <div className="border-b border-zinc-900 pb-4">
              <div className="text-[11px] font-mono uppercase tracking-widest text-[#b39170] mb-1">
                Season Diagnostics
              </div>
              <h2 className="text-2xl font-black text-white tracking-tight">
                Rajasthan Royals IPL 2026 Season Post-Mortem
              </h2>
              <p className="text-xs text-zinc-400 mt-1 max-w-2xl leading-relaxed">
                Analysis of 17,527 deliveries across 16 matches (9 Wins, 7 Losses). Demonstrates where games were won and where breakdowns dictated defeat.
              </p>
            </div>

            {/* Wins vs Losses Breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Bowling Comparison */}
              <div className="p-5 rounded-sm bg-[#111] border border-zinc-900 space-y-4">
                <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
                  <span className="text-xs font-mono font-bold uppercase text-white">Bowling Phase Contrast</span>
                  <span className="text-[10px] font-mono text-zinc-500">Economy & Wickets</span>
                </div>

                <div className="space-y-3 font-mono text-xs">
                  {data.audit_2026.phase_comparison.bowling.map((b, idx) => (
                    <div key={idx} className="p-3 rounded bg-zinc-950 border border-zinc-900 space-y-2">
                      <div className="flex items-center justify-between font-bold text-white">
                        <span>{b.phase}</span>
                        <span className="text-rose-400">{b.delta_econ} RPO in Losses</span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-[11px]">
                        <div className="p-2 rounded bg-zinc-900 text-zinc-300">
                          <span className="text-[10px] text-zinc-500 block">9 WINS</span>
                          {b.win_econ} RPO • {b.win_wkts} Wkts
                        </div>
                        <div className="p-2 rounded bg-zinc-900 text-zinc-300">
                          <span className="text-[10px] text-zinc-500 block">7 LOSSES</span>
                          {b.loss_econ} RPO • {b.loss_wkts} Wkts
                        </div>
                      </div>
                      <p className="text-[11px] font-sans text-zinc-400">{b.verdict}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Batting Comparison */}
              <div className="p-5 rounded-sm bg-[#111] border border-zinc-900 space-y-4">
                <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
                  <span className="text-xs font-mono font-bold uppercase text-white">Batting Phase Contrast</span>
                  <span className="text-[10px] font-mono text-zinc-500">Strike Rates</span>
                </div>

                <div className="space-y-3 font-mono text-xs">
                  {data.audit_2026.phase_comparison.batting.map((bt, idx) => (
                    <div key={idx} className="p-3 rounded bg-zinc-950 border border-zinc-900 space-y-2">
                      <div className="flex items-center justify-between font-bold text-white">
                        <span>{bt.phase}</span>
                        <span className="text-amber-400">{bt.delta_sr} SR in Losses</span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-[11px]">
                        <div className="p-2 rounded bg-zinc-900 text-zinc-300">
                          <span className="text-[10px] text-zinc-500 block">9 WINS</span>
                          {bt.win_sr} SR
                        </div>
                        <div className="p-2 rounded bg-zinc-900 text-zinc-300">
                          <span className="text-[10px] text-zinc-500 block">7 LOSSES</span>
                          {bt.loss_sr} SR
                        </div>
                      </div>
                      <p className="text-[11px] font-sans text-zinc-400">{bt.verdict}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* RR 2026 Squad Apex Percentiles Table */}
            <div className="p-5 rounded-sm bg-[#111] border border-zinc-900 space-y-4">
              <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
                <span className="text-xs font-mono font-bold uppercase text-white">RR 2026 Squad: QUWROF Apex Percentiles</span>
                <span className="text-[10px] font-mono text-zinc-500">Data Source: data_v2.json</span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#141414] text-zinc-500 font-mono text-[10px] uppercase border-b border-zinc-800">
                    <tr>
                      <th className="py-2.5 px-3">Player</th>
                      <th className="py-2.5 px-3">Role</th>
                      <th className="py-2.5 px-3 text-right">Runs</th>
                      <th className="py-2.5 px-3 text-right">SR</th>
                      <th className="py-2.5 px-3 text-right">Wkts</th>
                      <th className="py-2.5 px-3 text-right">Econ</th>
                      <th className="py-2.5 px-3 text-right">QUWROF Pctile</th>
                      <th className="py-2.5 px-3">Evaluation</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-900 font-mono">
                    {data.audit_2026.squad_apex_ratings.map((s, idx) => (
                      <tr key={idx} className="hover:bg-zinc-800/30 transition">
                        <td className="py-2.5 px-3 font-sans font-bold text-white">{s.name}</td>
                        <td className="py-2.5 px-3 font-sans text-zinc-400">{s.role}</td>
                        <td className="py-2.5 px-3 text-right text-zinc-300">{s.runs}</td>
                        <td className="py-2.5 px-3 text-right text-zinc-300">{s.sr.toFixed(1)}</td>
                        <td className="py-2.5 px-3 text-right text-zinc-300">{s.wkts}</td>
                        <td className="py-2.5 px-3 text-right text-zinc-300">{s.econ.toFixed(2)}</td>
                        <td className="py-2.5 px-3 text-right font-bold">
                          <span className={`${s.quwrof_pctile >= 80 ? 'text-emerald-400' : s.quwrof_pctile >= 50 ? 'text-zinc-300' : 'text-rose-400'}`}>
                            {s.quwrof_pctile.toFixed(1)}%
                          </span>
                        </td>
                        <td className="py-2.5 px-3 font-sans text-zinc-400 text-[11px]">{s.notes}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ── SECTION 4: METRIC ARCHITECTURE & FLAW SOLUTIONS ── */}
        {activeSection === 'metrics' && (
          <div className="space-y-8 max-w-4xl mx-auto">
            <div className="border-b border-zinc-900 pb-4">
              <div className="text-[11px] font-mono uppercase tracking-widest text-[#b39170] mb-1">
                Technical Foundation
              </div>
              <h2 className="text-2xl font-black text-white tracking-tight">
                Pressure Engine Architecture & Ratio Flaw Elimination
              </h2>
              <p className="text-xs text-zinc-400 mt-1 max-w-2xl leading-relaxed">
                Documenting the mathematical lessons from QUWROF v1–v14 and explaining the Dual-Criterion model.
              </p>
            </div>

            {/* The Flaw and The Fix */}
            <div className="p-5 rounded-sm bg-[#111] border border-zinc-900 space-y-4">
              <span className="text-xs font-mono uppercase tracking-wider text-rose-400 font-bold block">
                The Inherent Flaw in Simple Ratio Metrics
              </span>
              <p className="text-xs text-zinc-300 leading-relaxed font-sans">
                Many conventional pressure models divide a player's pressure strike rate by their baseline strike rate: <code className="text-zinc-200 bg-zinc-900 px-1 py-0.5 rounded font-mono">SR_pres / SR_base</code>. 
                In our June 2026 experiments, this was found to introduce severe structural distortion:
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
                <div className="p-3.5 rounded bg-zinc-950 border border-zinc-900 space-y-1">
                  <span className="text-rose-400 font-bold block">Below-Average Batter</span>
                  <div className="text-zinc-400">Baseline SR: 100 → Pressure SR: 120</div>
                  <div className="text-white font-bold">Ratio = 1.20x (+20% increase)</div>
                  <span className="text-zinc-500 block text-[11px] pt-1">Inappropriately boosted to the top despite striking at only 120.</span>
                </div>
                <div className="p-3.5 rounded bg-zinc-950 border border-zinc-900 space-y-1">
                  <span className="text-emerald-400 font-bold block">Elite Power Finisher</span>
                  <div className="text-zinc-400">Baseline SR: 175 → Pressure SR: 180</div>
                  <div className="text-white font-bold">Ratio = 1.03x (+3% increase)</div>
                  <span className="text-zinc-500 block text-[11px] pt-1">Penalized simply because their baseline was already historically dominant.</span>
                </div>
              </div>
            </div>

            {/* Dual Criterion Formulation */}
            <div className="p-5 rounded-sm bg-[#111] border border-zinc-900 space-y-4">
              <span className="text-xs font-mono uppercase tracking-wider text-[#b39170] font-bold block">
                The Solution: Dual-Criterion Blended Model
              </span>
              <p className="text-xs text-zinc-300 leading-relaxed font-sans">
                Our model blends 50% Normalized Absolute Output (calibrated against the 85th/90th percentile of all high-pressure deliveries) with 50% Relative Maintenance:
              </p>

              <div className="space-y-3 font-mono text-xs">
                <div className="p-4 rounded bg-zinc-950 border border-zinc-900 space-y-1">
                  <span className="text-zinc-400 block text-[11px] uppercase font-bold text-[#b39170]">Batter Pressure Rating (BPR)</span>
                  <div className="text-zinc-200">
                    BPR = 0.40 * (SR_pres / P85_pres_SR) + 0.35 * (SR_pres / SR_base) + 0.15 * clip(Avg_pres / Avg_base, 0.5, 2.0) - 0.20 * (ΔDot%)
                  </div>
                  <span className="text-zinc-500 text-[11px] block pt-1 font-sans">
                    Where ΔDot% penalizes batters whose dot ball percentage increases under pressure.
                  </span>
                </div>

                <div className="p-4 rounded bg-zinc-950 border border-zinc-900 space-y-1">
                  <span className="text-zinc-400 block text-[11px] uppercase font-bold text-[#b39170]">Bowler Pressure Rating (BowPR)</span>
                  <div className="text-zinc-200">
                    BowPR = 0.40 * clip(P15_pres_econ / Econ_pres, 0.5, 2.0) + 0.30 * clip(Econ_base / Econ_pres, 0.5, 2.0) + 0.20 * (WktRate_pres / 0.80) + 0.10 * (1.0 + ΔDot%)
                  </div>
                  <span className="text-zinc-500 text-[11px] block pt-1 font-sans">
                    Where P15_pres_econ represents the benchmark death economy standard (~7.50 RPO).
                  </span>
                </div>
              </div>
            </div>

            {/* 65:35 Architecture */}
            <div className="p-5 rounded-sm bg-[#111] border border-zinc-900 space-y-3 text-xs">
              <span className="font-mono uppercase tracking-wider text-zinc-400 font-bold block">
                65:35 IPL : T20I Weighting Architecture with Bayesian Shrinkage
              </span>
              <p className="text-zinc-300 leading-relaxed font-sans">
                In QUWROF V11–V14, cross-validation established that IPL talent density is uniform across all 10 franchises, whereas international bilaterals exhibit high variance (frequently featuring rotational squads or Associate fixtures).
              </p>
              <div className="p-3 rounded bg-zinc-950 border border-zinc-900 font-mono text-zinc-200">
                Combined Score = 0.65 * Rating_IPL + 0.35 * Rating_T20I
              </div>
              <p className="text-zinc-400 font-sans">
                Players with samples in only one format have the missing format regressed toward the neutral anchor (1.00) via Bayesian shrinkage: <code className="text-zinc-300 font-mono">k = min(balls / 120, 1.0)</code>.
              </p>
            </div>
          </div>
        )}

        {/* ── SECTION 5: EXECUTIVE DOSSIER (PRINT / PDF READY) ── */}
        {activeSection === 'dossier' && (
          <div className="space-y-8 max-w-4xl mx-auto p-6 sm:p-10 rounded-sm bg-[#111] border border-zinc-900 shadow-2xl">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-widest text-zinc-500">Unstop SupeRR Selector • Round 1</span>
                <h2 className="text-xl font-black text-white mt-0.5">Rajasthan Royals 2027 Mega Auction Dossier</h2>
                <span className="text-xs text-zinc-400">Author: Shourya • Framework: QUWROF Pressure Engine</span>
              </div>
              <button
                onClick={() => window.print()}
                className="px-3.5 py-1.5 rounded-sm bg-zinc-800 text-white text-xs font-semibold hover:bg-zinc-700 transition border border-zinc-700 font-mono"
              >
                Print / Save PDF
              </button>
            </div>

            <div className="space-y-4 text-xs text-zinc-300 leading-relaxed font-sans">
              <span className="font-mono text-xs uppercase tracking-wider text-white font-bold block">1. Executive Summary</span>
              <p>
                A forensic analysis of the 200,999 delivery dataset confirms that Rajasthan Royals' 2026 season (9 wins, 7 losses) fell short of the championship due to three specific phase deficits:
              </p>
              <div className="space-y-2 pl-3 border-l-2 border-zinc-800">
                <div><strong className="text-white">Death Bowling Run Leakage:</strong> In 7 defeats, RR conceded 12.30 RPO in overs 16–20 (vs 9.24 in wins). Sandeep Sharma (13.3 ER) and Tushar Deshpande (11.25 ER) collapsed when Archer finished his overs.</div>
                <div><strong className="text-white">Powerplay Wicket Drought:</strong> In 7 defeats, RR took just 4 powerplay wickets across 42 overs (0.57 per match) while bleeding 11.50 RPO.</div>
                <div><strong className="text-white">Finisher Isolation:</strong> Outside Donovan Ferreira, RR lacked late-overs boundary hitting. Shimron Hetmyer collapsed to a 113.0 SR (22nd percentile in QUWROF).</div>
              </div>
            </div>

            <div className="space-y-4 text-xs font-sans">
              <span className="font-mono text-xs uppercase tracking-wider text-white font-bold block">2. High-Conviction Acquisition Targets</span>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-4 rounded bg-zinc-950 border border-zinc-900 space-y-2">
                  <span className="text-[10px] font-mono uppercase text-[#b39170] block">GAP 1: ARCHER DEATH PARTNER</span>
                  <div className="font-bold text-white text-sm">Jamie Overton (ENG)</div>
                  <p className="text-zinc-400 text-xs">6.62 ER in death pressure. 145 km/h wide yorkers + power batting.</p>
                  <div className="text-zinc-400 text-[11px] pt-2 border-t border-zinc-900 font-mono">
                    Alt Indian: Sakib Hussain (7.70 ER, 11 wkts)
                  </div>
                </div>

                <div className="p-4 rounded bg-zinc-950 border border-zinc-900 space-y-2">
                  <span className="text-[10px] font-mono uppercase text-[#b39170] block">GAP 2: POWERPLAY STRIKER</span>
                  <div className="font-bold text-white text-sm">Mohammed Siraj (IND)</div>
                  <p className="text-zinc-400 text-xs">45 PP wickets at 7.98 economy. Premier new-ball strike seamer.</p>
                  <div className="text-zinc-400 text-[11px] pt-2 border-t border-zinc-900 font-mono">
                    Alt Local: Khaleel Ahmed (26 wkts, 7.79 ER)
                  </div>
                </div>

                <div className="p-4 rounded bg-zinc-950 border border-zinc-900 space-y-2">
                  <span className="text-[10px] font-mono uppercase text-[#b39170] block">GAP 3: CLUTCH FINISHER</span>
                  <div className="font-bold text-white text-sm">Naman Dhir (IND)</div>
                  <p className="text-zinc-400 text-xs">209.5 death pressure SR. Attacks spin & pace; frees overseas slot.</p>
                  <div className="text-zinc-400 text-[11px] pt-2 border-t border-zinc-900 font-mono">
                    Alt Overseas: Cooper Connolly (212.8 SR)
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-3 text-xs text-zinc-300 leading-relaxed font-sans">
              <span className="font-mono text-xs uppercase tracking-wider text-white font-bold block">3. SMS Jaipur Venue Synergy</span>
              <p>
                Sawai Mansingh Stadium features 75m–80m square boundaries and abrasive clay that grips early before dew arrives. Jamie Overton's hard back-of-a-length bounce forces mistimed pulls to deep midwicket. Furthermore, wide yorker bowlers (Overton and Sakib Hussain) prevent dew-slicked wet ball slips during second-innings chases.
              </p>
            </div>

            <div className="pt-4 border-t border-zinc-900 text-center text-[10px] font-mono text-zinc-600">
              Generated by SupeRR Selector Engine • Based on 200,999 Historical Deliveries • Rajasthan Royals War Room
            </div>
          </div>
        )}

      </div>

      {/* ── FOOTER ──────────────────────────────────────────────────────── */}
      <footer className="border-t border-zinc-900 bg-[#0a0a0a] py-6 text-center text-xs text-zinc-500 font-mono">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>SupeRR Selector 2027 • Technical Submission</span>
          <span>QUWROF Heritage • Next.js & Turbopack</span>
        </div>
      </footer>
    </div>
  );
}
