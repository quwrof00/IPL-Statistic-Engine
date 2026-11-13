"use client";

import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import Link from 'next/link';
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Tooltip, Legend, ResponsiveContainer,
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, ZAxis, Cell, LabelList
} from 'recharts';

interface PressurePlayer {
  player_id: number;
  player_name: string;
  nationality: string;
  is_pakistani: boolean;
  is_retired?: boolean;
  total_pressure_balls: number;
  balls_faced?: number;
  total_balls?: number;
  total_runs?: number;
  wickets?: number;
  economy?: number;
  overall_sr?: number;
  overall_avg?: number;
  pressure_sr?: number;
  pressure_avg?: number;
  pressure_econ?: number;
  pressure_sr_bowl?: number;
  sr_lift?: number;
  econ_suppression?: number;
  lone_wolf_multiplier?: number;
  bat_chase_impact?: number;
  bowl_pressure_impact?: number;
  combined_score: number;
  pres_metric?: number | null;
  base_metric?: number | null;
  pres_wkts?: number;
  // Computed on view
  rank?: number;
  percentile?: number;
  delta?: number;
}

const metricDescriptions: Record<string, string> = {
  combined_score: "Apex Engine Pressure Impact: bat_chase_impact for batters (runs scored * (pressure_multiplier - 1) * 0.15) or bowl_pressure_impact for bowlers (wickets * runs_per_wicket * (lone_wolf * 0.15 + low_total_defend * 0.15)).",
  pres_metric: "Performance under pressure (top 30% leverage deliveries, overs 16-20, steep RRR chases, or rapid early collapses). Strike Rate for batters, Economy Rate for bowlers.",
  base_metric: "Standard unweighted baseline metric across all match situations. Strike Rate for batters, Economy Rate for bowlers.",
  delta: "Net performance differential in high pressure compared to baseline. Positive is superior for batters (higher SR); negative is superior for bowlers (lower economy conceded).",
  total_pressure_balls: "Total legal deliveries faced (batters) or bowled (bowlers) during qualified pressure deliveries in the 2022–2026 dataset.",
  pres_wkts: "Total bowler wickets claimed during high-pressure deliveries.",
  lone_wolf_multiplier: "Lone Wolf Multiplier: max(0, team_economy - bowler_economy). Measures bowler performance carrying the attack relative to teammates.",
  sr_lift: "Strike Rate Lift: Pressure Strike Rate minus Overall Strike Rate."
};

const COMPARE_COLORS = ['#ea1a85', '#ffffff', '#a1a1aa', '#71717a'];
const PINK = '#ea1a85';

const InfoTooltip = ({ text, align = 'center' }: { text?: string; align?: 'center' | 'left' | 'right' }) => {
  const [open, setOpen] = useState(false);
  if (!text) return null;

  const positionClasses = 
    align === 'right' 
      ? 'right-0 sm:right-auto sm:left-1/2 sm:-translate-x-1/2' 
      : align === 'left'
      ? 'left-0 sm:left-1/2 sm:-translate-x-1/2'
      : 'left-1/2 -translate-x-1/2';

  return (
    <div className="relative inline-block ml-1.5 align-middle">
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          setOpen(!open);
        }}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        className="w-3.5 h-3.5 rounded-full border border-zinc-600 text-zinc-400 hover:border-zinc-300 hover:text-white flex items-center justify-center text-[9px] font-bold transition-colors cursor-pointer"
        aria-label="Info"
      >
        i
      </button>

      {open && (
        <div
          role="tooltip"
          className={`absolute top-full mt-2 w-56 sm:w-64 p-3 bg-zinc-950 text-zinc-300 text-xs leading-relaxed rounded shadow-2xl transition-all whitespace-normal normal-case font-normal border border-zinc-800 text-left z-[120] pointer-events-none ${positionClasses}`}
        >
          {text}
        </div>
      )}
    </div>
  );
};

export default function SupeRRPage() {
  const [dataBatters, setDataBatters] = useState<PressurePlayer[]>([]);
  const [dataBowlers, setDataBowlers] = useState<PressurePlayer[]>([]);
  const [loading, setLoading] = useState(true);

  // Tabs: 'rankings' (default) | 'compare' | 'plots' | 'what_is_pressure' | 'methodology'
  const [activeTab, setActiveTab] = useState<'rankings' | 'compare' | 'plots' | 'what_is_pressure' | 'methodology'>('rankings');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [role, setRole] = useState<'batter' | 'bowler'>('batter');
  const [viewMode, setViewMode] = useState<'top10' | 'all'>('top10');

  // Sorting
  const [sortField, setSortField] = useState<string>('combined_score');
  const [sortAsc, setSortAsc] = useState<boolean>(false);

  // Filters
  const [originFilter, setOriginFilter] = useState<'all' | 'indian' | 'overseas'>('all');
  const [nationalityFilter, setNationalityFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [minBalls, setMinBalls] = useState<number>(50);

  // Modal / Selected Player
  const [selectedPlayer, setSelectedPlayer] = useState<PressurePlayer | null>(null);

  // Compare State
  const [comparedPlayers, setComparedPlayers] = useState<PressurePlayer[]>([]);
  const [compareSearch, setCompareSearch] = useState<string>('');

  // Scatter Plot State
  const [scatterX, setScatterX] = useState<string>('total_pressure_balls');
  const [scatterY, setScatterY] = useState<string>('pres_metric');

  useEffect(() => {
    async function loadData() {
      try {
        const res = await fetch('/pressure_data.json');
        const json = await res.json();
        const b = json.batters || [];
        const bw = json.bowlers || [];
        setDataBatters(b);
        setDataBowlers(bw);
        if (b.length >= 2) {
          setComparedPlayers([b[0], b[1]]);
        }
      } catch (err) {
        console.error('Failed to load pressure data', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // Modal scroll lock
  useEffect(() => {
    if (selectedPlayer) {
      document.body.style.overflow = 'hidden';
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape') setSelectedPlayer(null);
      };
      window.addEventListener('keydown', handleKeyDown);
      return () => {
        document.body.style.overflow = 'unset';
        window.removeEventListener('keydown', handleKeyDown);
      };
    } else {
      document.body.style.overflow = 'unset';
    }
  }, [selectedPlayer]);

  const rawPool = role === 'batter' ? dataBatters : dataBowlers;

  // Global canonical rank map (Never changes on search or filter)
  const globalRankMap = useMemo(() => {
    const pool = role === 'batter' ? dataBatters : dataBowlers;
    const qualified = pool.filter(p => p.total_pressure_balls >= 50);
    const sorted = [...qualified].sort((a, b) => b.combined_score - a.combined_score);
    const map = new Map<number, { rank: number; percentile: number; totalQualified: number }>();
    const n = sorted.length;

    sorted.forEach((p, idx) => {
      const rank = idx + 1;
      const percentile = n > 1 ? Math.round(((n - rank) / (n - 1)) * 100) : 100;
      map.set(p.player_id, { rank, percentile, totalQualified: n });
    });
    return map;
  }, [role, dataBatters, dataBowlers]);

  // Filter pool
  const filteredList = useMemo(() => {
    return rawPool.filter(p => {
      if (originFilter === 'indian' && p.nationality !== 'India') return false;
      if (originFilter === 'overseas' && p.nationality === 'India') return false;
      if (nationalityFilter !== 'all' && p.nationality !== nationalityFilter) return false;
      if (p.total_pressure_balls < minBalls) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        if (!p.player_name.toLowerCase().includes(q)) return false;
      }
      return true;
    });
  }, [rawPool, originFilter, nationalityFilter, minBalls, searchQuery]);

  // Sort and assign canonical ranks & percentiles
  const sortedList = useMemo(() => {
    const list = [...filteredList];

    list.sort((a, b) => {
      let va: any = a[sortField as keyof PressurePlayer];
      let vb: any = b[sortField as keyof PressurePlayer];

      if (va === null || va === undefined) va = sortAsc ? 999999 : -999999;
      if (vb === null || vb === undefined) vb = sortAsc ? 999999 : -999999;

      if (typeof va === 'string') {
        return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
      }
      return sortAsc ? va - vb : vb - va;
    });

    return list.map((p) => {
      const pres = p.pres_metric ?? 0;
      const base = p.base_metric ?? 0;
      const delta = pres - base;
      const canonical = globalRankMap.get(p.player_id);

      return {
        ...p,
        rank: canonical?.rank ?? 999,
        percentile: canonical?.percentile ?? 0,
        delta: Math.round(delta * 10) / 10
      };
    });
  }, [filteredList, sortField, sortAsc, globalRankMap]);

  const displayedList = viewMode === 'top10' ? sortedList.slice(0, 10) : sortedList;

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      if (field === 'pres_metric' && role === 'bowler') {
        setSortAsc(true);
      } else {
        setSortAsc(false);
      }
    }
  };

  const availableNationalities = useMemo(() => {
    const s = new Set<string>();
    rawPool.forEach(p => {
      if (p.nationality && p.nationality !== 'Unknown') s.add(p.nationality);
    });
    return Array.from(s).sort();
  }, [rawPool]);

  // Selected player navigation
  const selectedIndex = selectedPlayer ? displayedList.findIndex(p => p.player_id === selectedPlayer.player_id) : -1;
  const handlePrev = useCallback(() => {
    if (selectedIndex > 0) setSelectedPlayer(displayedList[selectedIndex - 1]);
  }, [selectedIndex, displayedList]);
  const handleNext = useCallback(() => {
    if (selectedIndex >= 0 && selectedIndex < displayedList.length - 1) setSelectedPlayer(displayedList[selectedIndex + 1]);
  }, [selectedIndex, displayedList]);

  // Touch Swipe for Mobile Modal
  const touchStartX = useRef<number | null>(null);
  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.targetTouches[0].clientX;
  };
  const handleTouchEnd = (e: React.TouchEvent) => {
    if (!touchStartX.current) return;
    const touchEndX = e.changedTouches[0].clientX;
    const diff = touchStartX.current - touchEndX;
    if (diff > 50) handleNext();
    else if (diff < -50) handlePrev();
    touchStartX.current = null;
  };

  // Compare Handlers & Radar Chart Data
  const toggleComparePlayer = (player: PressurePlayer) => {
    const exists = comparedPlayers.some(p => p.player_id === player.player_id);
    if (exists) {
      setComparedPlayers(comparedPlayers.filter(p => p.player_id !== player.player_id));
    } else {
      if (comparedPlayers.length < 4) {
        setComparedPlayers([...comparedPlayers, player]);
      }
    }
  };

  const radarChartData = useMemo(() => {
    if (comparedPlayers.length === 0) return [];

    const isBatter = role === 'batter';
    interface SubjectDef {
      subject: string;
      key: string;
      max: number;
      isDelta?: boolean;
      isInverted?: boolean;
    }

    const subjects: SubjectDef[] = isBatter
      ? [
          { subject: "Pressure Impact", key: "combined_score", max: 120 },
          { subject: "Pressure SR", key: "pres_metric", max: 200 },
          { subject: "Baseline SR", key: "base_metric", max: 180 },
          { subject: "SR Lift / Delta", key: "delta", max: 20, isDelta: true },
          { subject: "Pressure Volume", key: "total_pressure_balls", max: 600 },
        ]
      : [
          { subject: "Pressure Impact", key: "combined_score", max: 1000 },
          { subject: "Econ Resistance", key: "pres_metric", max: 12, isInverted: true },
          { subject: "Pressure Wkts", key: "pres_wkts", max: 40 },
          { subject: "Lone Wolf Diff", key: "lone_wolf_multiplier", max: 2.5 },
          { subject: "Pressure Volume", key: "total_pressure_balls", max: 800 },
        ];

    return subjects.map(s => {
      const row: Record<string, any> = { subject: s.subject };
      comparedPlayers.forEach(p => {
        let rawVal = (p as any)[s.key] ?? 0;
        let score = 0;
        if (s.isInverted) {
          score = Math.max(10, Math.min(100, Math.round(((12 - rawVal) / (12 - 6)) * 100)));
        } else if (s.isDelta) {
          score = Math.max(10, Math.min(100, Math.round(((rawVal + 10) / 30) * 100)));
        } else {
          score = Math.max(10, Math.min(100, Math.round((rawVal / s.max) * 100)));
        }
        row[p.player_name] = score;
      });
      return row;
    });
  }, [comparedPlayers, role]);

  // Scatter Plot Data
  const scatterPlotData = useMemo(() => {
    return sortedList.map(p => ({
      name: p.player_name,
      x: (p as any)[scatterX] ?? 0,
      y: (p as any)[scatterY] ?? 0,
      impact: p.combined_score,
      nationality: p.nationality
    }));
  }, [sortedList, scatterX, scatterY]);

  return (
    <div className="min-h-screen bg-[#0a0a0a] font-sans text-zinc-200 selection:bg-zinc-700 selection:text-white pb-32">
      {/* NAVBAR */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-4 md:px-10 py-4 bg-[#0a0a0a]/95 backdrop-blur-md border-b border-zinc-900">
        <div className="flex items-center gap-3">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="w-6 h-6 rounded-sm flex items-center justify-center" style={{ background: PINK }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3">
                <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
              </svg>
            </div>
            <span className="text-base font-bold tracking-tight text-white group-hover:text-zinc-300 transition">
              Apex<span className="text-zinc-500 font-normal">Pressure</span>
            </span>
          </Link>
        </div>

        {/* Desktop Navigation Links */}
        <div className="hidden md:flex items-center gap-6 text-sm font-medium">
          <button
            onClick={() => setActiveTab('rankings')}
            className={`transition-colors py-1 ${activeTab === 'rankings' ? 'text-white border-b-2 font-bold' : 'text-zinc-400 hover:text-white'}`}
            style={activeTab === 'rankings' ? { borderBottomColor: PINK } : {}}
          >
            Rankings
          </button>
          <button
            onClick={() => setActiveTab('compare')}
            className={`transition-colors py-1 ${activeTab === 'compare' ? 'text-white border-b-2 font-bold' : 'text-zinc-400 hover:text-white'}`}
            style={activeTab === 'compare' ? { borderBottomColor: PINK } : {}}
          >
            Compare ({comparedPlayers.length})
          </button>
          <button
            onClick={() => setActiveTab('plots')}
            className={`transition-colors py-1 ${activeTab === 'plots' ? 'text-white border-b-2 font-bold' : 'text-zinc-400 hover:text-white'}`}
            style={activeTab === 'plots' ? { borderBottomColor: PINK } : {}}
          >
            Plots
          </button>
          <button
            onClick={() => setActiveTab('what_is_pressure')}
            className={`transition-colors py-1 ${activeTab === 'what_is_pressure' ? 'text-white border-b-2 font-bold' : 'text-zinc-400 hover:text-white'}`}
            style={activeTab === 'what_is_pressure' ? { borderBottomColor: PINK } : {}}
          >
            What is Pressure?
          </button>
          <button
            onClick={() => setActiveTab('methodology')}
            className={`transition-colors py-1 ${activeTab === 'methodology' ? 'text-white border-b-2 font-bold' : 'text-zinc-400 hover:text-white'}`}
            style={activeTab === 'methodology' ? { borderBottomColor: PINK } : {}}
          >
            Methodology
          </button>
          <Link
            href="/"
            className="text-xs text-zinc-500 hover:text-white pl-4 border-l border-zinc-800 transition"
          >
            Apex Engine →
          </Link>
        </div>

        {/* Mobile Hamburger Button */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden p-2 rounded text-zinc-400 hover:text-white focus:outline-none"
          aria-label="Toggle menu"
        >
          {mobileMenuOpen ? (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          ) : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          )}
        </button>
      </nav>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden fixed top-[57px] left-0 right-0 bg-[#0c0c0c] border-b border-zinc-800 p-4 z-40 space-y-3 font-medium text-sm shadow-2xl">
          <button
            onClick={() => { setActiveTab('rankings'); setMobileMenuOpen(false); }}
            className={`block w-full text-left py-2 px-3 rounded ${activeTab === 'rankings' ? 'bg-zinc-800 text-white font-bold' : 'text-zinc-400'}`}
          >
            Rankings
          </button>
          <button
            onClick={() => { setActiveTab('compare'); setMobileMenuOpen(false); }}
            className={`block w-full text-left py-2 px-3 rounded ${activeTab === 'compare' ? 'bg-zinc-800 text-white font-bold' : 'text-zinc-400'}`}
          >
            Compare ({comparedPlayers.length})
          </button>
          <button
            onClick={() => { setActiveTab('plots'); setMobileMenuOpen(false); }}
            className={`block w-full text-left py-2 px-3 rounded ${activeTab === 'plots' ? 'bg-zinc-800 text-white font-bold' : 'text-zinc-400'}`}
          >
            Plots
          </button>
          <button
            onClick={() => { setActiveTab('what_is_pressure'); setMobileMenuOpen(false); }}
            className={`block w-full text-left py-2 px-3 rounded ${activeTab === 'what_is_pressure' ? 'bg-zinc-800 text-white font-bold' : 'text-zinc-400'}`}
          >
            What is Pressure?
          </button>
          <button
            onClick={() => { setActiveTab('methodology'); setMobileMenuOpen(false); }}
            className={`block w-full text-left py-2 px-3 rounded ${activeTab === 'methodology' ? 'bg-zinc-800 text-white font-bold' : 'text-zinc-400'}`}
          >
            Methodology
          </button>
          <Link
            href="/"
            className="block w-full text-left py-2 px-3 text-xs text-zinc-500 border-t border-zinc-800 pt-3"
          >
            Switch to Apex Engine →
          </Link>
        </div>
      )}

      {/* HEADER SECTION (CLEAN & SPACIOUS) */}
      <header className="pt-28 md:pt-36 pb-12 px-4 md:px-10 border-b border-zinc-900">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row md:items-end justify-between gap-8">
          <div className="space-y-3">
            <span className="text-[11px] font-mono uppercase tracking-widest text-zinc-500 block font-semibold">
              T20 Pressure Evaluation • 2022 to 2026
            </span>
            <h1 className="text-3xl sm:text-5xl md:text-6xl font-black text-white tracking-tight leading-tight">
              Pressure Index
            </h1>
            <p className="text-sm sm:text-base text-zinc-400 max-w-2xl leading-relaxed">
              Measuring absolute performance value added during high-leverage match situations across 200,999 ball-by-ball deliveries.
            </p>
          </div>

          <div className="flex items-center gap-4 shrink-0">
            <div className="p-4 rounded bg-zinc-950 border border-zinc-900 border-l-2" style={{ borderLeftColor: PINK }}>
              <span className="text-[10px] font-mono uppercase text-zinc-500 block">Pressure Sample</span>
              <span className="text-xl font-bold text-white font-mono">60,305 balls</span>
            </div>
            <div className="p-4 rounded bg-zinc-950 border border-zinc-900 border-l-2" style={{ borderLeftColor: PINK }}>
              <span className="text-[10px] font-mono uppercase text-zinc-500 block">Wicket Risk</span>
              <span className="text-xl font-bold text-white font-mono">1.61x surge</span>
            </div>
          </div>
        </div>
      </header>

      {/* MAIN CONTAINER */}
      <main className="max-w-6xl mx-auto px-4 md:px-10 pt-10">

        {/* ── TAB 1: RANKINGS (CLEAN & SPACIOUS) ── */}
        {activeTab === 'rankings' && (
          <div className="space-y-8">

            {/* Controls Row */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-900">
              <div className="flex items-center gap-3">
                {/* Batters vs Bowlers */}
                <div className="inline-flex rounded bg-zinc-950 border border-zinc-800 p-1">
                  <button
                    onClick={() => { setRole('batter'); setSortField('combined_score'); setSortAsc(false); }}
                    className={`px-5 py-2 text-xs font-bold uppercase tracking-wider rounded transition ${role === 'batter' ? 'bg-white text-black shadow-sm' : 'text-zinc-400 hover:text-white'}`}
                  >
                    Batters
                  </button>
                  <button
                    onClick={() => { setRole('bowler'); setSortField('combined_score'); setSortAsc(false); }}
                    className={`px-5 py-2 text-xs font-bold uppercase tracking-wider rounded transition ${role === 'bowler' ? 'bg-white text-black shadow-sm' : 'text-zinc-400 hover:text-white'}`}
                  >
                    Bowlers
                  </button>
                </div>

                {/* Top 10 vs All */}
                <div className="inline-flex rounded bg-zinc-950 border border-zinc-800 p-1">
                  <button
                    onClick={() => setViewMode('top10')}
                    className={`px-3.5 py-2 text-xs font-semibold rounded transition ${viewMode === 'top10' ? 'bg-zinc-800 text-white' : 'text-zinc-500 hover:text-white'}`}
                  >
                    Top 10
                  </button>
                  <button
                    onClick={() => setViewMode('all')}
                    className={`px-3.5 py-2 text-xs font-semibold rounded transition ${viewMode === 'all' ? 'bg-zinc-800 text-white' : 'text-zinc-500 hover:text-white'}`}
                  >
                    All ({sortedList.length})
                  </button>
                </div>
              </div>

              {/* Search */}
              <div className="w-full sm:w-64">
                <input
                  type="text"
                  placeholder="Search player..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-xs text-white placeholder-zinc-600 focus:outline-none focus:border-zinc-500 transition"
                />
              </div>
            </div>

            {/* Sub-Filters */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 bg-zinc-950 border border-zinc-900 p-4 rounded text-xs font-mono">
              <div>
                <label className="text-[10px] uppercase text-zinc-500 block mb-1.5">Origin</label>
                <select
                  value={originFilter}
                  onChange={e => setOriginFilter(e.target.value as any)}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded px-3 py-2 text-white focus:outline-none focus:border-zinc-600"
                >
                  <option value="all">All Origins</option>
                  <option value="indian">Indian Only</option>
                  <option value="overseas">Overseas Only</option>
                </select>
              </div>

              <div>
                <label className="text-[10px] uppercase text-zinc-500 block mb-1.5">Nationality</label>
                <select
                  value={nationalityFilter}
                  onChange={e => setNationalityFilter(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded px-3 py-2 text-white focus:outline-none focus:border-zinc-600"
                >
                  <option value="all">All Nations ({availableNationalities.length})</option>
                  {availableNationalities.map(nat => (
                    <option key={nat} value={nat}>{nat}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[10px] uppercase text-zinc-500 block mb-1.5">Min Pressure Balls</label>
                <select
                  value={minBalls}
                  onChange={e => setMinBalls(Number(e.target.value))}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded px-3 py-2 text-white focus:outline-none focus:border-zinc-600"
                >
                  <option value={30}>30+ Balls</option>
                  <option value={50}>50+ Balls (Official)</option>
                  <option value={100}>100+ Balls</option>
                  <option value={150}>150+ Balls</option>
                </select>
              </div>
            </div>

            {/* MAIN RANKINGS LIST / TABLE */}
            <div className="rounded border border-zinc-800 bg-[#0d0d0d] overflow-hidden shadow-2xl">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-zinc-800 bg-[#121212] text-[10px] font-mono uppercase text-zinc-400 tracking-wider">
                    <th onClick={() => handleSort('rank')} className="py-4 px-4 sm:px-6 cursor-pointer hover:text-white select-none w-16">
                      # {sortField === 'rank' && (sortAsc ? '↑' : '↓')}
                    </th>
                    <th onClick={() => handleSort('player_name')} className="py-4 px-4 sm:px-6 cursor-pointer hover:text-white select-none">
                      Player {sortField === 'player_name' && (sortAsc ? '↑' : '↓')}
                    </th>
                    <th className="hidden md:table-cell py-4 px-4 text-zinc-500">Nation</th>
                    <th onClick={() => handleSort('total_pressure_balls')} className="hidden md:table-cell py-4 px-4 text-right cursor-pointer hover:text-white select-none">
                      Balls <InfoTooltip text={metricDescriptions.total_pressure_balls} />
                    </th>
                    <th onClick={() => handleSort('pres_metric')} className="hidden sm:table-cell py-4 px-4 text-right cursor-pointer hover:text-white select-none">
                      {role === 'batter' ? 'Pressure SR' : 'Pressure Econ'} <InfoTooltip text={metricDescriptions.pres_metric} />
                    </th>
                    <th onClick={() => handleSort('base_metric')} className="hidden lg:table-cell py-4 px-4 text-right cursor-pointer hover:text-white select-none">
                      {role === 'batter' ? 'Base SR' : 'Base Econ'} <InfoTooltip text={metricDescriptions.base_metric} />
                    </th>
                    <th onClick={() => handleSort('delta')} className="hidden md:table-cell py-4 px-4 text-right cursor-pointer hover:text-white select-none">
                      Delta <InfoTooltip text={metricDescriptions.delta} />
                    </th>
                    {role === 'bowler' && (
                      <th onClick={() => handleSort('pres_wkts')} className="hidden lg:table-cell py-4 px-4 text-right cursor-pointer hover:text-white select-none">
                        Wkts <InfoTooltip text={metricDescriptions.pres_wkts} />
                      </th>
                    )}
                    <th onClick={() => handleSort('combined_score')} className="py-4 px-4 sm:px-6 text-right font-bold cursor-pointer hover:text-zinc-300 select-none" style={{ color: PINK }}>
                      Score <InfoTooltip text={metricDescriptions.combined_score} align="right" /> {sortField === 'combined_score' && (sortAsc ? '↑' : '↓')}
                    </th>
                    <th className="hidden sm:table-cell py-4 px-4 text-center w-24">Compare</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-900 font-mono text-sm">
                  {displayedList.map(p => {
                    const isBatter = role === 'batter';
                    const presVal = p.pres_metric ?? 0;
                    const baseVal = p.base_metric ?? 0;
                    const delta = p.delta ?? (presVal - baseVal);
                    const isPositive = isBatter ? delta > 0 : delta < 0;
                    const isCompared = comparedPlayers.some(cp => cp.player_id === p.player_id);

                    return (
                      <tr
                        key={p.player_id}
                        onClick={() => setSelectedPlayer(p)}
                        className="hover:bg-zinc-900/60 transition cursor-pointer group"
                      >
                        {/* Rank */}
                        <td className="py-4 px-4 sm:px-6 font-bold transition group-hover:opacity-80"
                          style={{
                            color: p.rank === 1 ? PINK : p.rank === 2 ? '#e4e4e7' : p.rank === 3 ? '#a1a1aa' : '#52525b'
                          }}>
                          #{p.rank}
                        </td>

                        {/* Player Name */}
                        <td className="py-4 px-4 sm:px-6 font-sans font-bold text-white group-hover:text-zinc-300 transition">
                          <div className="flex flex-col">
                            <span className="text-sm sm:text-base">{p.player_name}</span>
                            {/* Mobile Subtitle showing Nationality */}
                            <span className="md:hidden text-[11px] font-normal text-zinc-500 font-mono">
                              {p.nationality}
                            </span>
                          </div>
                        </td>

                        {/* Nationality (Desktop) */}
                        <td className="hidden md:table-cell py-4 px-4 font-sans text-zinc-400">
                          {p.nationality}
                        </td>

                        {/* Pressure Balls (Desktop) */}
                        <td className="hidden md:table-cell py-4 px-4 text-right text-zinc-400">
                          {p.total_pressure_balls}
                        </td>

                        {/* Pressure Metric (Tablet + Desktop) */}
                        <td className="hidden sm:table-cell py-4 px-4 text-right font-bold text-white">
                          {presVal.toFixed(1)}
                        </td>

                        {/* Base Metric (Desktop Large) */}
                        <td className="hidden lg:table-cell py-4 px-4 text-right text-zinc-500">
                          {baseVal.toFixed(1)}
                        </td>

                        {/* Delta (Desktop) */}
                        <td className={`hidden md:table-cell py-4 px-4 text-right font-semibold ${isPositive ? 'text-white' : 'text-zinc-500'}`}>
                          {delta > 0 ? `+${delta.toFixed(1)}` : delta.toFixed(1)}
                        </td>

                        {/* Bowler Wickets */}
                        {!isBatter && (
                          <td className="hidden lg:table-cell py-4 px-4 text-right text-zinc-400">
                            {p.pres_wkts ?? 0}
                          </td>
                        )}

                        {/* Combined Score (Always Visible, Prominent) */}
                        <td className="py-4 px-4 sm:px-6 text-right font-black text-base sm:text-lg"
                          style={{ color: p.rank === 1 ? PINK : '#ffffff' }}>
                          {p.combined_score.toFixed(2)}
                        </td>

                        {/* Compare Action */}
                        <td className="hidden sm:table-cell py-4 px-4 text-center">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleComparePlayer(p);
                            }}
                            className={`px-2.5 py-1 rounded text-[10px] font-mono uppercase font-bold transition ${isCompared ? 'text-white' : 'bg-zinc-800 text-zinc-400 hover:text-white'}`}
                            style={isCompared ? { background: PINK } : {}}
                          >
                            {isCompared ? '✓ Added' : '+ Compare'}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="flex items-center justify-between text-xs text-zinc-500 font-mono pt-2">
              <span>Showing {displayedList.length} of {filteredList.length} players</span>
              <span className="hidden sm:inline">Tap any row for details</span>
            </div>
          </div>
        )}

        {/* ── TAB 2: HEAD-TO-HEAD COMPARE (CLEAN RADAR) ── */}
        {activeTab === 'compare' && (
          <div className="space-y-10 max-w-5xl mx-auto py-4">
            <div className="border-b border-zinc-900 pb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-widest text-zinc-500 font-bold block">
                  Head-to-Head Comparison
                </span>
                <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight mt-1">
                  Radar Profiles
                </h2>
              </div>

              <div className="inline-flex rounded bg-zinc-950 border border-zinc-800 p-1">
                <button
                  onClick={() => {
                    setRole('batter');
                    setComparedPlayers(dataBatters.slice(0, 2));
                  }}
                  className={`px-4 py-1.5 text-xs font-bold uppercase tracking-wider rounded transition ${role === 'batter' ? 'bg-white text-black' : 'text-zinc-400 hover:text-white'}`}
                >
                  Batters
                </button>
                <button
                  onClick={() => {
                    setRole('bowler');
                    setComparedPlayers(dataBowlers.slice(0, 2));
                  }}
                  className={`px-4 py-1.5 text-xs font-bold uppercase tracking-wider rounded transition ${role === 'bowler' ? 'bg-white text-black' : 'text-zinc-400 hover:text-white'}`}
                >
                  Bowlers
                </button>
              </div>
            </div>

            {/* Active Compare Chips */}
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-mono uppercase text-zinc-500 mr-2">Selected:</span>
              {comparedPlayers.map((p, idx) => (
                <div
                  key={p.player_id}
                  className="flex items-center gap-2 px-3 py-1.5 rounded bg-zinc-900 border border-zinc-800 text-xs text-white font-mono"
                  style={{ borderLeftColor: COMPARE_COLORS[idx % COMPARE_COLORS.length], borderLeftWidth: '3px' }}
                >
                  <span className="font-bold">{p.player_name}</span>
                  <button
                    onClick={() => toggleComparePlayer(p)}
                    className="text-zinc-500 hover:text-red-400 ml-1 font-bold"
                  >
                    ✕
                  </button>
                </div>
              ))}
              {comparedPlayers.length === 0 && (
                <span className="text-xs text-zinc-500 italic">No players selected. Use search below to add.</span>
              )}
            </div>

            {/* Search Input */}
            <div className="relative max-w-sm">
              <input
                type="text"
                placeholder="Search player to add..."
                value={compareSearch}
                onChange={e => setCompareSearch(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-xs text-white placeholder-zinc-600 focus:outline-none focus:border-zinc-500"
              />
              {compareSearch.trim() && (
                <div className="absolute top-full left-0 right-0 mt-1 max-h-48 overflow-y-auto bg-zinc-900 border border-zinc-800 rounded shadow-2xl z-30 divide-y divide-zinc-800">
                  {rawPool
                    .filter(p => p.player_name.toLowerCase().includes(compareSearch.toLowerCase()))
                    .slice(0, 8)
                    .map(p => (
                      <button
                        key={p.player_id}
                        onClick={() => {
                          toggleComparePlayer(p);
                          setCompareSearch('');
                        }}
                        className="w-full text-left px-3 py-2 text-xs hover:bg-zinc-800 flex items-center justify-between text-zinc-200"
                      >
                        <span>{p.player_name} ({p.nationality})</span>
                        <span className="font-mono text-zinc-400 font-bold">{p.combined_score.toFixed(1)}</span>
                      </button>
                    ))}
                </div>
              )}
            </div>

            {/* Radar Chart */}
            {comparedPlayers.length > 0 && (
              <div className="p-6 rounded bg-[#111] border border-zinc-800 shadow-xl space-y-4">
                <span className="text-xs font-mono uppercase text-zinc-400 tracking-wider font-bold block">
                  Normalized Metric Radar (0–100 Scale)
                </span>
                <div className="w-full h-80 sm:h-96">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarChartData}>
                      <PolarGrid stroke="#27272a" />
                      <PolarAngleAxis dataKey="subject" tick={{ fill: '#a1a1aa', fontSize: 11, fontWeight: 700 }} />
                      <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#09090b', borderColor: '#27272a', borderRadius: '4px', fontSize: '11px', color: '#fff' }}
                      />
                      <Legend wrapperStyle={{ fontSize: '12px', fontWeight: 600, paddingTop: '10px' }} />
                      {comparedPlayers.map((p, idx) => (
                        <Radar
                          key={p.player_id}
                          name={p.player_name}
                          dataKey={p.player_name}
                          stroke={COMPARE_COLORS[idx % COMPARE_COLORS.length]}
                          fill={COMPARE_COLORS[idx % COMPARE_COLORS.length]}
                          fillOpacity={0.15}
                          strokeWidth={2}
                        />
                      ))}
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {/* Stat Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {comparedPlayers.map((p, idx) => (
                <div
                  key={p.player_id}
                  className="p-5 rounded bg-[#111] border border-zinc-800 space-y-4"
                  style={{ borderTopColor: COMPARE_COLORS[idx % COMPARE_COLORS.length], borderTopWidth: '3px' }}
                >
                  <div>
                    <h3 className="text-lg font-bold text-white tracking-tight">{p.player_name}</h3>
                    <div className="text-xs font-mono text-zinc-400">{p.nationality} • {p.total_pressure_balls} Balls</div>
                  </div>

                  <div className="space-y-3 font-mono text-xs pt-2 border-t border-zinc-800">
                    <div className="flex justify-between items-center">
                      <span className="text-zinc-500 uppercase">Score</span>
                      <span className="text-base font-black text-white">{p.combined_score.toFixed(2)}</span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-zinc-500 uppercase">{role === 'batter' ? 'Pressure SR' : 'Pressure Econ'}</span>
                      <span className="text-white font-bold">{p.pres_metric?.toFixed(1) ?? '—'}</span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-zinc-500 uppercase">{role === 'batter' ? 'Baseline SR' : 'Baseline Econ'}</span>
                      <span className="text-zinc-400">{p.base_metric?.toFixed(1) ?? '—'}</span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-zinc-500 uppercase">Delta</span>
                      <span className="text-white font-bold">
                        {(p.delta ?? 0) > 0 ? `+${p.delta?.toFixed(1)}` : p.delta?.toFixed(1)}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── TAB 3: PLOTS (SCATTER) ── */}
        {activeTab === 'plots' && (
          <div className="space-y-8 max-w-5xl mx-auto py-4">
            <div className="border-b border-zinc-900 pb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-widest text-zinc-500 font-bold block">
                  Bivariate Analysis
                </span>
                <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight mt-1">
                  Distribution Plot
                </h2>
              </div>

              {/* Axis Selectors */}
              <div className="flex flex-wrap items-center gap-3 text-xs font-mono">
                <div>
                  <span className="text-zinc-500 block text-[10px] uppercase mb-1">X-Axis</span>
                  <select
                    value={scatterX}
                    onChange={e => setScatterX(e.target.value)}
                    className="bg-zinc-900 border border-zinc-800 rounded px-2.5 py-1.5 text-white focus:outline-none"
                  >
                    <option value="total_pressure_balls">Pressure Balls</option>
                    <option value="base_metric">{role === 'batter' ? 'Base SR' : 'Base Econ'}</option>
                    <option value="combined_score">Score</option>
                  </select>
                </div>

                <div>
                  <span className="text-zinc-500 block text-[10px] uppercase mb-1">Y-Axis</span>
                  <select
                    value={scatterY}
                    onChange={e => setScatterY(e.target.value)}
                    className="bg-zinc-900 border border-zinc-800 rounded px-2.5 py-1.5 text-white focus:outline-none"
                  >
                    <option value="pres_metric">{role === 'batter' ? 'Pressure SR' : 'Pressure Econ'}</option>
                    <option value="combined_score">Score</option>
                    <option value="delta">Delta vs Baseline</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Scatter Chart */}
            <div className="p-6 rounded bg-[#111] border border-zinc-800 shadow-xl space-y-4">
              <div className="w-full h-80 sm:h-96 md:h-[450px]">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                    <XAxis
                      type="number"
                      dataKey="x"
                      name={scatterX}
                      tick={{ fill: '#71717a', fontSize: 11 }}
                      tickLine={false}
                      axisLine={{ stroke: '#3f3f46' }}
                    />
                    <YAxis
                      type="number"
                      dataKey="y"
                      name={scatterY}
                      tick={{ fill: '#71717a', fontSize: 11 }}
                      tickLine={false}
                      axisLine={{ stroke: '#3f3f46' }}
                    />
                    <ZAxis type="number" range={[45, 45]} />
                    <Tooltip
                      cursor={{ strokeDasharray: '3 3', stroke: '#71717a' }}
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0].payload;
                          return (
                            <div className="bg-zinc-950 border border-zinc-800 p-3 rounded shadow-2xl text-xs font-mono text-white space-y-1">
                              <div className="font-bold text-sm text-white font-sans">{data.name}</div>
                              <div className="text-zinc-400 text-[11px]">{data.nationality}</div>
                              <div className="pt-1 text-zinc-300">X: <span className="font-bold text-white">{Number(data.x).toFixed(1)}</span></div>
                              <div className="text-zinc-300">Y: <span className="font-bold text-white">{Number(data.y).toFixed(1)}</span></div>
                              <div className="text-zinc-300">Score: <span className="font-bold text-white">{Number(data.impact).toFixed(2)}</span></div>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Scatter data={scatterPlotData} fill="#ffffff">
                      <LabelList dataKey="name" position="top" offset={8} style={{ fontSize: '10px', fill: '#d4d4d8', fontWeight: 600, pointerEvents: 'none' }} />
                      {scatterPlotData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={entry.impact > 80 ? PINK : '#71717a'}
                          fillOpacity={entry.impact > 80 ? 0.9 : 0.4}
                        />
                      ))}
                    </Scatter>
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}

        {/* ── TAB 4: WHAT IS PRESSURE? ── */}
        {activeTab === 'what_is_pressure' && (
          <div className="space-y-12 max-w-4xl mx-auto py-6">

            <div className="border-b border-zinc-900 pb-8 space-y-3">
              <span className="text-[11px] font-mono uppercase tracking-widest text-zinc-500 font-bold block">
                Empirical Match Analysis • 2022 to 2026
              </span>
              <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight">
                What Counts as Pressure?
              </h2>
              <p className="text-base text-zinc-300 leading-relaxed font-sans">
                Pressure in T20 cricket is an empirically measurable match condition where the margin for error collapses, the probability of a dismissal escalates sharply, and single delivery swings dictate win expectancy.
              </p>
            </div>

            {/* 4 Concrete Data Points */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="p-6 rounded bg-[#121212] border border-zinc-800 space-y-2">
                <span className="text-[10px] font-mono uppercase text-zinc-500 tracking-wider block">Risk of Dismissal</span>
                <div className="text-4xl font-black font-mono" style={{ color: PINK }}>1.61x</div>
                <h4 className="text-base font-bold text-white">Wicket Rate Spikes Under Pressure</h4>
                <p className="text-sm text-zinc-300 leading-relaxed font-sans">
                  Normal baseline deliveries produce a wicket rate of <strong>4.76%</strong>. During qualified pressure deliveries, this spikes to <strong>7.65%</strong> — a 61% surge in risk of dismissal.
                </p>
              </div>

              <div className="p-6 rounded bg-[#121212] border border-zinc-800 space-y-2">
                <span className="text-[10px] font-mono uppercase text-zinc-500 tracking-wider block">Required Run Rate</span>
                <div className="text-4xl font-black font-mono" style={{ color: PINK }}>27.9%</div>
                <h4 className="text-base font-bold text-white">Win Rate at RRR &gt; 10.0 RPO</h4>
                <p className="text-sm text-zinc-300 leading-relaxed font-sans">
                  Chasing teams maintain a 49.9% baseline win rate. Once RRR exceeds 10.0 RPO, win conversion plummets to 27.9%, and to 14.3% at RRR &gt; 12.0.
                </p>
              </div>

              <div className="p-6 rounded bg-[#121212] border border-zinc-800 space-y-2">
                <span className="text-[10px] font-mono uppercase text-zinc-500 tracking-wider block">Phase Concentration</span>
                <div className="text-4xl font-black font-mono" style={{ color: PINK }}>65.0%</div>
                <h4 className="text-base font-bold text-white">Death Overs Pressure Density</h4>
                <p className="text-sm text-zinc-300 leading-relaxed font-sans">
                  Pressure concentrates heavily in overs 16–20: <strong>28,900 of 44,454 death deliveries</strong> qualify as high-pressure situations.
                </p>
              </div>

              <div className="p-6 rounded bg-[#121212] border border-zinc-800 space-y-2">
                <span className="text-[10px] font-mono uppercase text-zinc-500 tracking-wider block">High-Leverage Sample</span>
                <div className="text-4xl font-black font-mono" style={{ color: PINK }}>60,305</div>
                <h4 className="text-base font-bold text-white">Deliveries Isolated (30.0%)</h4>
                <p className="text-sm text-zinc-300 leading-relaxed font-sans">
                  Our rating system isolates the top 30% most demanding deliveries in the 2022–2026 timeline across both IPL and T20 Internationals.
                </p>
              </div>
            </div>

            {/* Concrete Signals */}
            <div className="p-6 rounded bg-[#121212] border border-zinc-800 space-y-4">
              <h3 className="text-xl font-bold text-white tracking-tight">The 4 Match-Context Signals</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-sans">
                <div className="p-4 rounded bg-zinc-950 border border-zinc-800 space-y-1.5">
                  <span className="font-mono text-[11px] uppercase font-bold text-white block">1. Required Run Rate Leverage</span>
                  <div className="font-mono text-zinc-400 text-[11px]">RRR_Pressure = clip(RRR / Season_RRR, 1.0, 2.0)</div>
                  <p className="text-zinc-400 text-xs">Evaluates chasing difficulty, scaling up to 2.0x when required rate exceeds league average.</p>
                </div>

                <div className="p-4 rounded bg-zinc-950 border border-zinc-800 space-y-1.5">
                  <span className="font-mono text-[11px] uppercase font-bold text-white block">2. Batting Collapse & Wickets in Hand</span>
                  <div className="font-mono text-zinc-400 text-[11px]">Wicket_Pressure = (Wkts_Fallen + 1) / (Exp_Wkts + 1)</div>
                  <p className="text-zinc-400 text-xs">Quantifies innings-1 rescue knocks when early top-order collapses occur.</p>
                </div>

                <div className="p-4 rounded bg-zinc-950 border border-zinc-800 space-y-1.5">
                  <span className="font-mono text-[11px] uppercase font-bold text-white block">3. Lone Wolf Bowler Multiplier</span>
                  <div className="font-mono text-zinc-400 text-[11px]">Lone_Wolf = max(0, Team_Economy - Bowler_Economy)</div>
                  <p className="text-zinc-400 text-xs">Rewards bowlers who restrict scoring when teammates are conceding heavily.</p>
                </div>

                <div className="p-4 rounded bg-zinc-950 border border-zinc-800 space-y-1.5">
                  <span className="font-mono text-[11px] uppercase font-bold text-white block">4. Low Total Defensive Resistance</span>
                  <div className="font-mono text-zinc-400 text-[11px]">Low_Total = max(0, League_Economy - Defended_RRR)</div>
                  <p className="text-zinc-400 text-xs">Elevates bowlers defending sub-par totals where every extra run threatens defeat.</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── TAB 5: METHODOLOGY ── */}
        {activeTab === 'methodology' && (
          <div className="space-y-12 max-w-4xl mx-auto py-6">

            <div className="border-b border-zinc-900 pb-8 space-y-3">
              <span className="text-[11px] font-mono uppercase tracking-widest text-zinc-500 font-bold block">
                Technical Foundation
              </span>
              <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight">
                Eliminating the "Mediocre Baseline Trap"
              </h2>
              <p className="text-base text-zinc-300 leading-relaxed font-sans">
                Documenting why simple ratio metrics fail and how absolute value added under leverage provides fair player ratings.
              </p>
            </div>

            {/* The Flaw */}
            <div className="p-6 rounded bg-[#121212] border border-zinc-800 space-y-4">
              <h3 className="text-lg font-bold text-white tracking-tight">The Flaw in Simple Ratio Metrics</h3>
              <p className="text-sm text-zinc-300 font-sans leading-relaxed">
                Conventional ratio metrics evaluate pressure by dividing pressure strike rate by baseline strike rate: <code className="text-white bg-black px-1.5 py-0.5 rounded font-mono text-xs">Ratio = SR_pres / SR_base</code>. This introduces two fatal distortions:
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-sans">
                <div className="p-4 rounded bg-zinc-950 border border-zinc-800 space-y-1.5">
                  <span className="text-zinc-300 font-bold block uppercase">Case A: The Mediocre Batter Trap</span>
                  <div className="text-zinc-500 font-mono">Baseline SR: 100 → Pressure SR: 120</div>
                  <div className="text-white font-bold font-mono">Ratio = 1.20x (+20% Boost)</div>
                  <p className="text-zinc-400">Receives an elite rating simply because their baseline was low, despite a 120 SR under pressure losing matches.</p>
                </div>

                <div className="p-4 rounded bg-zinc-950 border border-zinc-800 space-y-1.5">
                  <span className="text-zinc-300 font-bold block uppercase">Case B: The Dominant Finisher Penalty</span>
                  <div className="text-zinc-500 font-mono">Baseline SR: 175 → Pressure SR: 180</div>
                  <div className="text-white font-bold font-mono">Ratio = 1.03x (+3% Boost)</div>
                  <p className="text-zinc-400">Penalized simply because their ordinary baseline was already historically dominant.</p>
                </div>
              </div>
            </div>

            {/* The Solution */}
            <div className="p-6 rounded bg-[#121212] border border-zinc-800 space-y-4">
              <h3 className="text-lg font-bold text-white tracking-tight">The Apex Engine Solution</h3>
              <p className="text-sm text-zinc-300 font-sans leading-relaxed">
                The Apex Engine rates players on <strong>Absolute Value Added Under Leverage</strong>:
              </p>

              <div className="space-y-4 text-xs font-sans">
                <div className="p-4 rounded bg-zinc-950 border border-zinc-800 space-y-2">
                  <span className="font-mono text-[11px] uppercase font-bold text-white block">Batting Chase & Pressure Impact (bat_chase_impact)</span>
                  <div className="font-mono text-white bg-zinc-900 p-2.5 rounded">
                    bat_chase_impact = sum( runs * (pressure_multiplier - 1.0) ) * 0.15
                  </div>
                  <p className="text-zinc-400">
                    Runs scored when leverage is high receive bonus weighting proportional to match difficulty. Low-pressure stat-padding receives zero bonus.
                  </p>
                </div>

                <div className="p-4 rounded bg-zinc-950 border border-zinc-800 space-y-2">
                  <span className="font-mono text-[11px] uppercase font-bold text-white block">Bowling Pressure Impact (bowl_pressure_impact)</span>
                  <div className="font-mono text-white bg-zinc-900 p-2.5 rounded">
                    bowl_pressure_impact = wickets * runs_per_wicket * (lone_wolf * 0.15 + low_total_defend * 0.15)
                  </div>
                  <p className="text-zinc-400">
                    Wickets taken and runs suppressed when defending small totals or carrying struggling attacks are scaled by the runs-per-wicket baseline (~26.13).
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

      </main>

      {/* ── MODAL OVERLAY CARD (MOBILE BOTTOM SHEET & DESKTOP CENTER) ── */}
      {selectedPlayer && (
        <div className="fixed inset-0 z-[100] flex items-end md:items-center justify-center p-0 sm:p-4 md:p-6">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/85 backdrop-blur-sm transition-opacity"
            onClick={() => setSelectedPlayer(null)}
          ></div>

          {/* Modal Card */}
          <div
            onTouchStart={handleTouchStart}
            onTouchEnd={handleTouchEnd}
            className="relative bg-[#111111] border-t md:border border-zinc-800 w-full max-w-3xl h-auto max-h-[90vh] overflow-y-auto overscroll-contain shadow-2xl flex flex-col rounded-t-xl md:rounded z-[101]"
          >

            {/* Header */}
            <div className="sticky top-0 bg-[#161616] border-b border-zinc-800 px-5 sm:px-8 py-5 flex items-center justify-between z-40">
              <div className="flex items-center gap-3 sm:gap-4 pr-4">
                <div className="w-1.5 h-10 sm:h-12 rounded-full shrink-0" style={{ background: PINK }}></div>
                <div className="min-w-0">
                  <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight leading-none truncate">
                    {selectedPlayer.player_name}
                  </h2>
                  <div className="text-[11px] sm:text-xs font-mono text-zinc-400 mt-1 uppercase tracking-wider flex items-center gap-2 truncate">
                    <span>{selectedPlayer.nationality}</span>
                    <span>•</span>
                    <span className="font-bold" style={{ color: selectedPlayer.rank === 1 ? PINK : '#ffffff' }}>Rank #{selectedPlayer.rank}</span>
                  </div>
                </div>
              </div>

              {/* Prev / Next & Close */}
              <div className="flex items-center gap-1 sm:gap-2 shrink-0">
                <button
                  onClick={handlePrev}
                  disabled={selectedIndex <= 0}
                  className="w-8 h-8 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 disabled:opacity-30 transition flex items-center justify-center font-bold text-xs"
                  aria-label="Previous player"
                >
                  ←
                </button>
                <button
                  onClick={handleNext}
                  disabled={selectedIndex < 0 || selectedIndex >= displayedList.length - 1}
                  className="w-8 h-8 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 disabled:opacity-30 transition flex items-center justify-center font-bold text-xs"
                  aria-label="Next player"
                >
                  →
                </button>
                <button
                  onClick={() => setSelectedPlayer(null)}
                  className="w-8 h-8 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-white transition flex items-center justify-center font-bold text-xs ml-1 sm:ml-2"
                  aria-label="Close modal"
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Card Body */}
            <div className="p-5 sm:p-8 space-y-6">

              {/* Highlights */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
                  <div className="p-4 rounded bg-zinc-950 border border-zinc-800" style={{ borderTopColor: PINK, borderTopWidth: '2px' }}>
                  <span className="text-[10px] font-mono uppercase text-zinc-500 block">Score</span>
                  <div className="text-2xl font-black font-mono mt-1" style={{ color: PINK }}>
                    {selectedPlayer.combined_score.toFixed(2)}
                  </div>
                  <span className="text-[10px] text-zinc-500 font-mono truncate block">
                    {role === 'batter' ? 'bat_chase_impact' : 'bowl_pressure_impact'}
                  </span>
                </div>

                <div className="p-4 rounded bg-zinc-950 border border-zinc-800">
                  <span className="text-[10px] font-mono uppercase text-zinc-500 block">Percentile</span>
                  <div className="text-2xl font-black text-white font-mono mt-1">
                    {selectedPlayer.percentile}%
                  </div>
                  <span className="text-[10px] text-zinc-500 font-mono">Top {100 - (selectedPlayer.percentile ?? 100)}%</span>
                </div>

                <div className="p-4 rounded bg-zinc-950 border border-zinc-800">
                  <span className="text-[10px] font-mono uppercase text-zinc-500 block">
                    {role === 'batter' ? 'Pressure SR' : 'Pressure Econ'}
                  </span>
                  <div className="text-2xl font-black text-white font-mono mt-1">
                    {selectedPlayer.pres_metric?.toFixed(1) ?? '—'}
                  </div>
                  <span className="text-[10px] text-zinc-500 font-mono">In leverage balls</span>
                </div>

                <div className="p-4 rounded bg-zinc-950 border border-zinc-800">
                  <span className="text-[10px] font-mono uppercase text-zinc-500 block">Delta</span>
                  <div className={`text-2xl font-black font-mono mt-1 ${(role === 'batter' ? (selectedPlayer.delta ?? 0) > 0 : (selectedPlayer.delta ?? 0) < 0) ? 'text-white' : 'text-zinc-500'}`}>
                    {(selectedPlayer.delta ?? 0) > 0 ? `+${selectedPlayer.delta?.toFixed(1)}` : selectedPlayer.delta?.toFixed(1)}
                  </div>
                  <span className="text-[10px] text-zinc-500 font-mono">Base: {selectedPlayer.base_metric?.toFixed(1)}</span>
                </div>
              </div>

              {/* Submetric Cards */}
              <div>
                <h3 className="text-sm font-bold text-white tracking-tight mb-3 uppercase font-mono text-zinc-400">
                  Metric Breakdown
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">

                  {/* Pressure Deliveries */}
                  <div className="p-4 rounded bg-zinc-950 border border-zinc-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono uppercase text-zinc-400 font-bold">Pressure Deliveries</span>
                      <InfoTooltip text={metricDescriptions.total_pressure_balls} />
                    </div>
                    <div className="text-xl font-black text-white font-mono">{selectedPlayer.total_pressure_balls}</div>
                    <div className="w-full h-1 bg-zinc-800 rounded-full overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${Math.min(100, (selectedPlayer.total_pressure_balls / 500) * 100)}%`, background: PINK }}></div>
                    </div>
                  </div>

                  {/* Pressure Metric */}
                  <div className="p-4 rounded bg-zinc-950 border border-zinc-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono uppercase text-zinc-400 font-bold">
                        {role === 'batter' ? 'Pressure Strike Rate' : 'Pressure Economy'}
                      </span>
                      <InfoTooltip text={metricDescriptions.pres_metric} />
                    </div>
                    <div className="text-xl font-black text-white font-mono">{selectedPlayer.pres_metric?.toFixed(1) ?? '—'}</div>
                    <div className="w-full h-1 bg-zinc-800 rounded-full overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${selectedPlayer.percentile}%`, background: PINK }}></div>
                    </div>
                  </div>

                  {/* Baseline Metric */}
                  <div className="p-4 rounded bg-zinc-950 border border-zinc-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono uppercase text-zinc-400 font-bold">
                        {role === 'batter' ? 'Baseline Strike Rate' : 'Baseline Economy'}
                      </span>
                      <InfoTooltip text={metricDescriptions.base_metric} />
                    </div>
                    <div className="text-xl font-black text-zinc-400 font-mono">{selectedPlayer.base_metric?.toFixed(1) ?? '—'}</div>
                    <div className="w-full h-1 bg-zinc-800 rounded-full overflow-hidden">
                      <div className="h-full bg-zinc-600" style={{ width: '70%' }}></div>
                    </div>
                  </div>

                  {/* Role specifics */}
                  {role === 'bowler' ? (
                    <>
                      <div className="p-4 rounded bg-zinc-950 border border-zinc-800 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-mono uppercase text-zinc-400 font-bold">Pressure Wickets</span>
                          <InfoTooltip text={metricDescriptions.pres_wkts} />
                        </div>
                        <div className="text-xl font-black text-white font-mono">{selectedPlayer.pres_wkts ?? 0}</div>
                        <div className="w-full h-1 bg-zinc-800 rounded-full overflow-hidden">
                          <div className="h-full bg-white" style={{ width: `${Math.min(100, ((selectedPlayer.pres_wkts ?? 0) / 40) * 100)}%` }}></div>
                        </div>
                      </div>

                      <div className="p-4 rounded bg-zinc-950 border border-zinc-800 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-mono uppercase text-zinc-400 font-bold">Lone Wolf Multiplier</span>
                          <InfoTooltip text={metricDescriptions.lone_wolf_multiplier} />
                        </div>
                        <div className="text-xl font-black text-white font-mono">
                          +{selectedPlayer.lone_wolf_multiplier?.toFixed(2) ?? '0.00'}
                        </div>
                        <div className="w-full h-1 bg-zinc-800 rounded-full overflow-hidden">
                          <div className="h-full bg-white" style={{ width: `${Math.min(100, ((selectedPlayer.lone_wolf_multiplier ?? 0) / 2.0) * 100)}%` }}></div>
                        </div>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="p-4 rounded bg-zinc-950 border border-zinc-800 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-mono uppercase text-zinc-400 font-bold">Strike Rate Lift</span>
                          <InfoTooltip text={metricDescriptions.sr_lift} />
                        </div>
                        <div className="text-xl font-black text-white font-mono">
                          {(selectedPlayer.delta ?? 0) > 0 ? `+${selectedPlayer.delta?.toFixed(1)}` : selectedPlayer.delta?.toFixed(1)}
                        </div>
                        <div className="w-full h-1 bg-zinc-800 rounded-full overflow-hidden">
                          <div className="h-full bg-white" style={{ width: `${Math.min(100, Math.max(10, ((selectedPlayer.delta ?? 0) + 15) * 3))}%` }}></div>
                        </div>
                      </div>

                      <div className="p-4 rounded bg-zinc-950 border border-zinc-800 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-mono uppercase text-zinc-400 font-bold">Total Runs</span>
                          <InfoTooltip text="Total career runs scored in 2022-2026 dataset" />
                        </div>
                        <div className="text-xl font-black text-zinc-300 font-mono">{selectedPlayer.total_runs ?? '—'}</div>
                        <div className="w-full h-1 bg-zinc-800 rounded-full overflow-hidden">
                          <div className="h-full bg-zinc-600" style={{ width: '80%' }}></div>
                        </div>
                      </div>
                    </>
                  )}

                  {/* Impact Rating */}
                  <div className="p-4 rounded bg-zinc-950 border border-zinc-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono uppercase text-zinc-400 font-bold">Overall Rating</span>
                      <InfoTooltip text={metricDescriptions.combined_score} align="right" />
                    </div>
                    <div className="text-xl font-black text-white font-mono">{selectedPlayer.combined_score.toFixed(2)}</div>
                    <div className="w-full h-1 bg-zinc-800 rounded-full overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${selectedPlayer.percentile}%`, background: PINK }}></div>
                    </div>
                  </div>

                </div>
              </div>

            </div>

            {/* Footer */}
            <div className="bg-[#141414] border-t border-zinc-800 px-5 sm:px-6 py-4 flex items-center justify-between text-xs text-zinc-500 font-mono">
              <span className="truncate pr-2">Rajasthan Royals SupeRR</span>
              <button
                onClick={() => setSelectedPlayer(null)}
                className="px-4 py-1.5 rounded bg-zinc-800 text-white hover:bg-zinc-700 transition shrink-0"
              >
                Close
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
