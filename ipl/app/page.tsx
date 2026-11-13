"use client";

import { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';

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
  journey_thread: Array<{
    tweet_num: number;
    text: string;
  }>;
  starting_xi: Array<{
    num: number;
    name: string;
    type: string;
    role: string;
    tag: string;
  }>;
}

export default function RRWarRoomPage() {
  const [activeTab, setActiveTab] = useState<'targets' | 'explorer' | 'audit' | 'metrics' | 'journey' | 'report'>('targets');
  const [warRoomData, setWarRoomData] = useState<WarRoomData | null>(null);
  const [pressureBatters, setPressureBatters] = useState<PressurePlayer[]>([]);
  const [pressureBowlers, setPressureBowlers] = useState<PressurePlayer[]>([]);
  const [loading, setLoading] = useState(true);

  // Explorer Filters
  const [explorerRole, setExplorerRole] = useState<'batter' | 'bowler'>('batter');
  const [originFilter, setOriginFilter] = useState<'all' | 'indian' | 'overseas'>('all');
  const [nationalityFilter, setNationalityFilter] = useState<string>('all');
  const [ageFilter, setAgeFilter] = useState<'all' | 'u25' | '25-30' | '30plus'>('all');
  const [includePakistani, setIncludePakistani] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [minBalls, setMinBalls] = useState<number>(50);
  const [copiedTweet, setCopiedTweet] = useState<number | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [resWarRoom, resPressure] = await Promise.all([
          fetch('/rr_war_room_data.json'),
          fetch('/pressure_data.json')
        ]);
        const wData = await resWarRoom.json();
        const pData = await resPressure.json();
        setWarRoomData(wData);
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

  // Filtered Explorer List
  const activeList = explorerRole === 'batter' ? pressureBatters : pressureBowlers;

  const availableNationalities = useMemo(() => {
    const nats = new Set<string>();
    activeList.forEach(p => {
      if (p.nationality && p.nationality !== 'Unknown') {
        if (!includePakistani && (p.nationality === 'Pakistan' || p.is_pakistani)) return;
        nats.add(p.nationality);
      }
    });
    return Array.from(nats).sort();
  }, [activeList, includePakistani]);

  const filteredExplorerList = useMemo(() => {
    return activeList.filter(p => {
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
  }, [activeList, includePakistani, originFilter, nationalityFilter, ageFilter, minBalls, searchQuery]);

  const handleCopyTweet = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedTweet(idx);
    setTimeout(() => setCopiedTweet(null), 2000);
  };

  const handleCopyAllTweets = () => {
    if (!warRoomData) return;
    const allText = warRoomData.journey_thread.map(t => t.text).join('\n\n');
    navigator.clipboard.writeText(allText);
    setCopiedTweet(999);
    setTimeout(() => setCopiedTweet(null), 2500);
  };

  if (loading || !warRoomData) {
    return (
      <div className="min-h-screen bg-[#070b14] text-white flex flex-col items-center justify-center p-6">
        <div className="w-12 h-12 border-4 border-[#ff2a85] border-t-transparent rounded-full animate-spin mb-4" />
        <h2 className="text-xl font-semibold tracking-wide text-zinc-200">Initializing Rajasthan Royals War Room Engine...</h2>
        <p className="text-sm text-zinc-500 mt-2">Loading 200,999 deliveries & QUWROF 2026 Audit</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#070b14] text-zinc-100 flex flex-col font-sans selection:bg-[#ff2a85] selection:text-white">
      {/* ── HEADER ────────────────────────────────────────────────────────── */}
      <header className="border-b border-zinc-800/80 bg-[#0b1021]/90 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3.5 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#ff2a85] to-[#2563eb] flex items-center justify-center font-black text-white text-lg shadow-lg shadow-[#ff2a85]/20">
              RR
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-base font-black tracking-wider text-white">SupeRR Selector</span>
                <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-[#ff2a85]/20 text-[#ff2a85] border border-[#ff2a85]/40">
                  WAR ROOM 2027
                </span>
              </div>
              <p className="text-[11px] text-zinc-400">Tactical Gap Analysis & Pressure Engine for Rajasthan Royals</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center gap-1 overflow-x-auto py-1">
            {[
              { id: 'targets', label: 'War Room Picks', icon: '🎯' },
              { id: 'explorer', label: 'Pressure Explorer', icon: '📊' },
              { id: 'audit', label: 'RR 2026 Audit', icon: '🔍' },
              { id: 'metrics', label: 'Metric Deep-Dive', icon: '🧠' },
              { id: 'journey', label: 'Journey (X Thread)', icon: '🧵' },
              { id: 'report', label: 'Submission Dossier', icon: '📄' },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap flex items-center gap-1.5 ${
                  activeTab === tab.id
                    ? 'bg-gradient-to-r from-[#ff2a85] to-[#e11d48] text-white shadow-md shadow-[#ff2a85]/25 font-bold'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/60'
                }`}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* ── MAIN CONTENT ─────────────────────────────────────────────────── */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-8">
        
        {/* TAB 1: WAR ROOM TARGETS & THE 3 GAPS */}
        {activeTab === 'targets' && (
          <div className="space-y-10">
            {/* Mission Hero Banner */}
            <div className="rounded-2xl border border-zinc-800 bg-gradient-to-br from-[#0e162f] via-[#0b1021] to-[#120f24] p-6 sm:p-8 relative overflow-hidden">
              <div className="absolute -top-16 -right-16 w-64 h-64 bg-[#ff2a85]/10 rounded-full blur-3xl pointer-events-none" />
              <div className="absolute -bottom-16 -left-16 w-64 h-64 bg-[#2563eb]/10 rounded-full blur-3xl pointer-events-none" />
              
              <div className="relative z-10 max-w-3xl">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#ff2a85]/15 border border-[#ff2a85]/30 text-[#ff2a85] text-xs font-semibold mb-4">
                  <span>Rajasthan Royals Mega Auction Strategy</span>
                </div>
                <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight">
                  Plugging RR's 3 Defeat Factors via the Dual-Criterion Pressure Engine
                </h1>
                <p className="mt-3 text-sm sm:text-base text-zinc-300 leading-relaxed">
                  In IPL 2026, Rajasthan Royals went 9–7. All 7 losses stemmed from 3 quantifiable collapses: 
                  <strong className="text-[#ff4d9d]"> 12.30 Death Bowling Economy</strong>, 
                  <strong className="text-[#ff4d9d]"> taking only 4 Powerplay wickets in 42 overs</strong>, and 
                  <strong className="text-[#ff4d9d]"> finishing stagnation outside Donovan Ferreira</strong>. 
                  Here are the auction targets calibrated to solve each deficit.
                </p>
              </div>

              {/* 3 Gap Stat Pills */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
                <div className="p-4 rounded-xl bg-zinc-900/80 border border-zinc-800">
                  <div className="text-xs font-semibold text-rose-400 uppercase tracking-wider">Deficit 1 • Death Leaks</div>
                  <div className="text-2xl font-black text-white mt-1">12.30 RPO</div>
                  <p className="text-xs text-zinc-400 mt-1">Conceded in overs 16–20 in losses (vs 9.24 in wins). Sandeep (13.3) & Deshpande (11.2) collapsed.</p>
                  <div className="mt-3 text-[11px] font-bold text-emerald-400 flex items-center gap-1">
                    <span>Target:</span> Jamie Overton (6.62 ER) & Sakib Hussain
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-zinc-900/80 border border-zinc-800">
                  <div className="text-xs font-semibold text-amber-400 uppercase tracking-wider">Deficit 2 • PP Drought</div>
                  <div className="text-2xl font-black text-white mt-1">4 Wkts in 42 Overs</div>
                  <p className="text-xs text-zinc-400 mt-1">In 7 losses, RR took just 0.57 PP wkts/match at 11.50 RPO. Openers attacked unchallenged.</p>
                  <div className="mt-3 text-[11px] font-bold text-emerald-400 flex items-center gap-1">
                    <span>Target:</span> Mohammed Siraj (45 PP wkts) & Khaleel
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-zinc-900/80 border border-zinc-800">
                  <div className="text-xs font-semibold text-sky-400 uppercase tracking-wider">Deficit 3 • Finisher Void</div>
                  <div className="text-2xl font-black text-white mt-1">Hetmyer SR 113.0</div>
                  <p className="text-xs text-zinc-400 mt-1">Outside Ferreira, RR had 0 finishing support. Middle overs SR collapsed to 142.6 in defeats.</p>
                  <div className="mt-3 text-[11px] font-bold text-emerald-400 flex items-center gap-1">
                    <span>Target:</span> Naman Dhir (209.5 SR) & Cooper Connolly
                  </div>
                </div>
              </div>
            </div>

            {/* Gap Tactical Solutions Cards */}
            <div className="space-y-6">
              <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <span className="text-[#ff2a85]">Auction Mandates:</span> Plugging the 3 Critical Structural Gaps
                </h2>
                <span className="text-xs text-zinc-400">SMS Jaipur Ground Dimensions & Dew Factored</span>
              </div>

              <div className="grid grid-cols-1 gap-6">
                {warRoomData.gaps.map((gap, idx) => (
                  <div key={gap.gap_id} className="rounded-xl border border-zinc-800 bg-[#0d1326] p-6 hover:border-zinc-700 transition">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-3">
                        <span className="w-7 h-7 rounded-lg bg-[#ff2a85]/20 text-[#ff2a85] font-black text-xs flex items-center justify-center border border-[#ff2a85]/30">
                          0{idx + 1}
                        </span>
                        <div>
                          <h3 className="text-lg font-bold text-white">{gap.title}</h3>
                          <span className="text-xs text-zinc-400">{gap.phase}</span>
                        </div>
                      </div>
                      <span className="text-xs px-2.5 py-1 rounded-full bg-zinc-800 text-zinc-300 border border-zinc-700">
                        Benchmark: {gap.benchmark}
                      </span>
                    </div>

                    <div className="mt-4 p-3 rounded-lg bg-zinc-900/60 border border-zinc-800 text-xs text-zinc-300">
                      <strong className="text-rose-400 font-semibold">The 2026 Deficit:</strong> {gap.problem}
                    </div>

                    {/* Recommendations table */}
                    <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
                      {gap.recommendations.map((rec, rIdx) => (
                        <div key={rIdx} className="p-3.5 rounded-lg bg-zinc-900/90 border border-zinc-800 hover:border-[#ff2a85]/50 transition flex flex-col justify-between">
                          <div>
                            <div className="flex items-center justify-between">
                              <span className="font-bold text-sm text-white">{rec.name}</span>
                              <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">{rec.type}</span>
                            </div>
                            <div className="text-[11px] text-zinc-400 mt-0.5">{rec.country} • Age {rec.age}</div>
                            
                            <div className="flex items-center gap-3 mt-3 text-xs">
                              {rec.death_pres_econ !== undefined && (
                                <div className="bg-zinc-800/80 px-2 py-1 rounded">
                                  <span className="text-zinc-400 text-[10px] block">Death Pres ER</span>
                                  <span className="font-bold text-emerald-400">{rec.death_pres_econ}</span>
                                </div>
                              )}
                              {rec.death_pres_sr !== undefined && (
                                <div className="bg-zinc-800/80 px-2 py-1 rounded">
                                  <span className="text-zinc-400 text-[10px] block">Death Pres SR</span>
                                  <span className="font-bold text-emerald-400">{rec.death_pres_sr}</span>
                                </div>
                              )}
                              {rec.pp_wkts !== undefined && (
                                <div className="bg-zinc-800/80 px-2 py-1 rounded">
                                  <span className="text-zinc-400 text-[10px] block">PP Wickets</span>
                                  <span className="font-bold text-emerald-400">{rec.pp_wkts}</span>
                                </div>
                              )}
                              {rec.overall_bowpr !== undefined && (
                                <div className="bg-zinc-800/80 px-2 py-1 rounded">
                                  <span className="text-zinc-400 text-[10px] block">BowPR Index</span>
                                  <span className="font-bold text-amber-400">{rec.overall_bowpr}</span>
                                </div>
                              )}
                              {rec.overall_bpr !== undefined && (
                                <div className="bg-zinc-800/80 px-2 py-1 rounded">
                                  <span className="text-zinc-400 text-[10px] block">BPR Index</span>
                                  <span className="font-bold text-amber-400">{rec.overall_bpr}</span>
                                </div>
                              )}
                            </div>
                          </div>

                          <p className="text-[11px] text-zinc-400 mt-3 pt-2 border-t border-zinc-800/80 leading-relaxed">
                            {rec.verdict}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Official Top 10 Batters & Bowlers (Dual Column Cards) */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* TOP 10 BATTERS */}
              <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <span className="text-[#ff2a85]">Top 10 Batters</span> Under Pressure
                  </h3>
                  <span className="text-xs text-zinc-400">IPL-Eligible • 65:35 Blended Index</span>
                </div>

                <div className="space-y-2.5">
                  {warRoomData.top10_batters.map(b => (
                    <div key={b.rank} className="p-3.5 rounded-xl bg-[#0d1326] border border-zinc-800 hover:border-zinc-700 transition flex items-center justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <span className={`w-6 h-6 rounded-md flex items-center justify-center font-bold text-xs ${
                          b.rank <= 3 ? 'bg-amber-400/20 text-amber-400 border border-amber-400/40' : 'bg-zinc-800 text-zinc-400'
                        }`}>
                          {b.rank}
                        </span>
                        <div>
                          <div className="font-bold text-sm text-white flex items-center gap-2">
                            <span>{b.name}</span>
                            <span className="text-[10px] font-normal px-1.5 py-0.2 rounded bg-zinc-800 text-zinc-400">{b.nationality} • {b.age}y</span>
                          </div>
                          <span className="text-[11px] text-[#ff4d9d] font-medium">{b.role}</span>
                          <p className="text-[11px] text-zinc-400 mt-0.5 line-clamp-1">{b.rr_fit}</p>
                        </div>
                      </div>

                      <div className="text-right shrink-0">
                        <div className="text-sm font-black text-white">{b.score.toFixed(4)}</div>
                        <div className="text-[10px] text-zinc-400">Pres SR: <span className="text-emerald-400 font-bold">{b.pres_sr}</span></div>
                        <div className="text-[10px] text-zinc-500">Base SR: {b.base_sr}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* TOP 10 BOWLERS */}
              <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <span className="text-[#2563eb]">Top 10 Bowlers</span> Under Pressure
                  </h3>
                  <span className="text-xs text-zinc-400">IPL-Eligible • 65:35 Blended Index</span>
                </div>

                <div className="space-y-2.5">
                  {warRoomData.top10_bowlers.map(bw => (
                    <div key={bw.rank} className="p-3.5 rounded-xl bg-[#0d1326] border border-zinc-800 hover:border-zinc-700 transition flex items-center justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <span className={`w-6 h-6 rounded-md flex items-center justify-center font-bold text-xs ${
                          bw.rank <= 3 ? 'bg-amber-400/20 text-amber-400 border border-amber-400/40' : 'bg-zinc-800 text-zinc-400'
                        }`}>
                          {bw.rank}
                        </span>
                        <div>
                          <div className="font-bold text-sm text-white flex items-center gap-2">
                            <span>{bw.name}</span>
                            <span className="text-[10px] font-normal px-1.5 py-0.2 rounded bg-zinc-800 text-zinc-400">{bw.nationality} • {bw.age}y</span>
                          </div>
                          <span className="text-[11px] text-sky-400 font-medium">{bw.role}</span>
                          <p className="text-[11px] text-zinc-400 mt-0.5 line-clamp-1">{bw.rr_fit}</p>
                        </div>
                      </div>

                      <div className="text-right shrink-0">
                        <div className="text-sm font-black text-white">{bw.score.toFixed(4)}</div>
                        <div className="text-[10px] text-zinc-400">Pres ER: <span className="text-emerald-400 font-bold">{bw.pres_econ}</span></div>
                        <div className="text-[10px] text-zinc-500">Wkts: {bw.pres_wkts} | Base: {bw.base_econ}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Starting XI Simulation Banner */}
            <div className="rounded-xl border border-zinc-800 bg-[#0e162f] p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <span>👑</span> Recommended Rajasthan Royals Starting XI (IPL 2027)
                  </h3>
                  <p className="text-xs text-zinc-400">Engineered to eliminate the 12.30 death economy leak and powerplay wicket drought</p>
                </div>
                <span className="text-xs px-2.5 py-1 rounded bg-[#ff2a85]/20 text-[#ff2a85] font-bold border border-[#ff2a85]/40">
                  4 Overseas Slots Maximized
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {warRoomData.starting_xi.map(p => (
                  <div key={p.num} className="p-3 rounded-lg bg-zinc-900/80 border border-zinc-800 flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2.5">
                      <span className="w-6 h-6 rounded bg-zinc-800 text-zinc-400 text-xs font-bold flex items-center justify-center shrink-0">
                        {p.num}
                      </span>
                      <div>
                        <div className="text-sm font-bold text-white">{p.name}</div>
                        <div className="text-[11px] text-zinc-400">{p.role}</div>
                      </div>
                    </div>
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded whitespace-nowrap ${
                      p.tag.includes('Target') 
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' 
                        : 'bg-zinc-800 text-zinc-400'
                    }`}>
                      {p.tag}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: INTERACTIVE PRESSURE EXPLORER */}
        {activeTab === 'explorer' && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-zinc-800 pb-4">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <span>📊</span> Complete Pressure Performance Explorer
                </h2>
                <p className="text-xs text-zinc-400">Search and filter across 300+ rated players from 200,999 delivery records</p>
              </div>

              {/* Role Toggle */}
              <div className="flex items-center rounded-lg bg-zinc-900 p-1 border border-zinc-800">
                <button
                  onClick={() => setExplorerRole('batter')}
                  className={`px-4 py-1.5 rounded-md text-xs font-bold transition ${
                    explorerRole === 'batter' ? 'bg-[#ff2a85] text-white' : 'text-zinc-400 hover:text-white'
                  }`}
                >
                  Batters ({pressureBatters.length})
                </button>
                <button
                  onClick={() => setExplorerRole('bowler')}
                  className={`px-4 py-1.5 rounded-md text-xs font-bold transition ${
                    explorerRole === 'bowler' ? 'bg-[#2563eb] text-white' : 'text-zinc-400 hover:text-white'
                  }`}
                >
                  Bowlers ({pressureBowlers.length})
                </button>
              </div>
            </div>

            {/* Filter Bar */}
            <div className="p-4 rounded-xl bg-[#0d1326] border border-zinc-800 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
              {/* Search */}
              <div className="lg:col-span-2">
                <label className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block mb-1">Search Player</label>
                <input
                  type="text"
                  placeholder="Type player name..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-1.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-[#ff2a85]"
                />
              </div>

              {/* Origin */}
              <div>
                <label className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block mb-1">Origin</label>
                <select
                  value={originFilter}
                  onChange={e => setOriginFilter(e.target.value as any)}
                  className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-[#ff2a85]"
                >
                  <option value="all">All Origins</option>
                  <option value="indian">Indian Only</option>
                  <option value="overseas">Overseas Only</option>
                </select>
              </div>

              {/* Nationality */}
              <div>
                <label className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block mb-1">Nationality</label>
                <select
                  value={nationalityFilter}
                  onChange={e => setNationalityFilter(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-[#ff2a85]"
                >
                  <option value="all">All Countries</option>
                  {availableNationalities.map(n => (
                    <option key={n} value={n}>{n}</option>
                  ))}
                </select>
              </div>

              {/* Age Bracket */}
              <div>
                <label className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block mb-1">Age Bracket</label>
                <select
                  value={ageFilter}
                  onChange={e => setAgeFilter(e.target.value as any)}
                  className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-[#ff2a85]"
                >
                  <option value="all">All Ages</option>
                  <option value="u25">Under 25</option>
                  <option value="25-30">25 to 30</option>
                  <option value="30plus">30+ Years</option>
                </select>
              </div>

              {/* Min Balls */}
              <div>
                <label className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block mb-1">Min Pressure Balls</label>
                <select
                  value={minBalls}
                  onChange={e => setMinBalls(Number(e.target.value))}
                  className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-[#ff2a85]"
                >
                  <option value={30}>30+ Balls</option>
                  <option value={50}>50+ Balls (Official)</option>
                  <option value={100}>100+ Balls (High Vol)</option>
                  <option value={200}>200+ Balls (Core)</option>
                </select>
              </div>
            </div>

            {/* Pakistani Toggle Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 rounded-lg bg-zinc-900/50 border border-zinc-800 text-xs">
              <div className="flex items-center gap-2">
                <span className="text-zinc-300">IPL Eligibility Rule:</span>
                <span className="text-zinc-500">Pakistani players are excluded from primary IPL auction recommendations by default.</span>
              </div>
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={includePakistani}
                  onChange={e => setIncludePakistani(e.target.checked)}
                  className="rounded border-zinc-700 bg-zinc-800 text-[#ff2a85] focus:ring-0"
                />
                <span className="text-zinc-300 font-medium">Include Pakistani Players ({includePakistani ? 'Shown' : 'Excluded'})</span>
              </label>
            </div>

            {/* Active Count */}
            <div className="text-xs text-zinc-400">
              Showing <strong className="text-white">{filteredExplorerList.length}</strong> qualified {explorerRole}s matching filters
            </div>

            {/* Data Table */}
            <div className="rounded-xl border border-zinc-800 bg-[#0d1326] overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-zinc-900/80 text-zinc-400 uppercase tracking-wider text-[10px] border-b border-zinc-800">
                  <tr>
                    <th className="py-3 px-4">#</th>
                    <th className="py-3 px-4">Player</th>
                    <th className="py-3 px-3">Nationality</th>
                    <th className="py-3 px-3">Age</th>
                    <th className="py-3 px-3 text-right">Pres Balls</th>
                    <th className="py-3 px-3 text-right">{explorerRole === 'batter' ? 'Pres SR' : 'Pres Econ'}</th>
                    <th className="py-3 px-3 text-right">{explorerRole === 'batter' ? 'Base SR' : 'Base Econ'}</th>
                    <th className="py-3 px-3 text-right">Delta</th>
                    {explorerRole === 'bowler' && <th className="py-3 px-3 text-right">Pres Wkts</th>}
                    <th className="py-3 px-3 text-right">IPL Score</th>
                    <th className="py-3 px-3 text-right">T20I Score</th>
                    <th className="py-3 px-4 text-right font-bold text-white">Combined Index</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/60 font-mono">
                  {filteredExplorerList.slice(0, 50).map((p, idx) => {
                    const isBatter = explorerRole === 'batter';
                    const presVal = p.pres_metric ?? 0;
                    const baseVal = p.base_metric ?? 0;
                    const delta = presVal - baseVal;
                    const isGoodDelta = isBatter ? delta > 0 : delta < 0;

                    return (
                      <tr key={p.player_id} className="hover:bg-zinc-800/40 transition">
                        <td className="py-3 px-4 font-bold text-zinc-500">{idx + 1}</td>
                        <td className="py-3 px-4 font-sans font-bold text-white">
                          <div className="flex items-center gap-2">
                            <span>{p.player_name}</span>
                            {p.is_pakistani && (
                              <span className="text-[9px] px-1 py-0.2 rounded bg-rose-900/60 text-rose-300 border border-rose-800 font-mono">
                                PAK
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-3 font-sans text-zinc-300">{p.nationality}</td>
                        <td className="py-3 px-3 text-zinc-400">{p.age ? `${p.age}y` : '—'}</td>
                        <td className="py-3 px-3 text-right text-zinc-300">{p.total_pressure_balls}</td>
                        <td className="py-3 px-3 text-right font-bold text-white">{presVal.toFixed(1)}</td>
                        <td className="py-3 px-3 text-right text-zinc-400">{baseVal.toFixed(1)}</td>
                        <td className={`py-3 px-3 text-right font-bold ${isGoodDelta ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {delta > 0 ? `+${delta.toFixed(1)}` : delta.toFixed(1)}
                        </td>
                        {!isBatter && (
                          <td className="py-3 px-3 text-right text-zinc-300">{p.pres_wkts ?? 0}</td>
                        )}
                        <td className="py-3 px-3 text-right text-zinc-400">
                          {p.ipl_rating ? p.ipl_rating.toFixed(3) : '—'}
                        </td>
                        <td className="py-3 px-3 text-right text-zinc-400">
                          {p.t20i_rating ? p.t20i_rating.toFixed(3) : '—'}
                        </td>
                        <td className="py-3 px-4 text-right font-black text-amber-400 text-sm">
                          {p.combined_score.toFixed(4)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 3: RR 2026 AUDIT & GAP BREAKDOWN */}
        {activeTab === 'audit' && (
          <div className="space-y-8">
            <div className="border-b border-zinc-800 pb-3">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <span>🔍</span> Rajasthan Royals IPL 2026 Season Audit (17,527 Deliveries)
              </h2>
              <p className="text-xs text-zinc-400">Rigorous post-mortem comparing performance in 9 Wins vs 7 Losses</p>
            </div>

            {/* Wins vs Losses Comparison Tables */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Bowling Comparison */}
              <div className="rounded-xl border border-zinc-800 bg-[#0d1326] p-5">
                <div className="text-sm font-bold text-rose-400 mb-3 flex items-center justify-between">
                  <span>Bowling Phase Comparison: Wins vs Losses</span>
                  <span className="text-[11px] text-zinc-400 font-normal">Runs Conceded & Wickets</span>
                </div>

                <div className="space-y-3">
                  {warRoomData.audit_2026.phase_comparison.bowling.map((b, i) => (
                    <div key={i} className="p-3 rounded-lg bg-zinc-900/70 border border-zinc-800">
                      <div className="flex items-center justify-between font-bold text-xs text-white">
                        <span>{b.phase}</span>
                        <span className="text-rose-400">{b.delta_econ} Economy Bleed</span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 mt-2 text-xs">
                        <div className="bg-emerald-950/30 border border-emerald-900/40 p-2 rounded">
                          <span className="text-[10px] text-emerald-400 block font-semibold">IN 9 WINS</span>
                          <span className="text-white font-bold">{b.win_econ} Econ</span> • {b.win_wkts} Wickets
                        </div>
                        <div className="bg-rose-950/30 border border-rose-900/40 p-2 rounded">
                          <span className="text-[10px] text-rose-400 block font-semibold">IN 7 LOSSES</span>
                          <span className="text-white font-bold">{b.loss_econ} Econ</span> • {b.loss_wkts} Wickets
                        </div>
                      </div>
                      <p className="text-[11px] text-zinc-400 mt-2 font-sans italic">{b.verdict}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Batting Comparison */}
              <div className="rounded-xl border border-zinc-800 bg-[#0d1326] p-5">
                <div className="text-sm font-bold text-sky-400 mb-3 flex items-center justify-between">
                  <span>Batting Phase Comparison: Wins vs Losses</span>
                  <span className="text-[11px] text-zinc-400 font-normal">Strike Rates</span>
                </div>

                <div className="space-y-3">
                  {warRoomData.audit_2026.phase_comparison.batting.map((bt, i) => (
                    <div key={i} className="p-3 rounded-lg bg-zinc-900/70 border border-zinc-800">
                      <div className="flex items-center justify-between font-bold text-xs text-white">
                        <span>{bt.phase}</span>
                        <span className="text-amber-400">{bt.delta_sr} Strike Rate Deficit</span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 mt-2 text-xs">
                        <div className="bg-emerald-950/30 border border-emerald-900/40 p-2 rounded">
                          <span className="text-[10px] text-emerald-400 block font-semibold">IN 9 WINS</span>
                          <span className="text-white font-bold">{bt.win_sr} SR</span>
                        </div>
                        <div className="bg-amber-950/30 border border-amber-900/40 p-2 rounded">
                          <span className="text-[10px] text-amber-400 block font-semibold">IN 7 LOSSES</span>
                          <span className="text-white font-bold">{bt.loss_sr} SR</span>
                        </div>
                      </div>
                      <p className="text-[11px] text-zinc-400 mt-2 font-sans italic">{bt.verdict}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* RR 2026 Squad Apex Ratings */}
            <div className="rounded-xl border border-zinc-800 bg-[#0d1326] p-5">
              <h3 className="text-sm font-bold text-white mb-3">RR 2026 Squad: QUWROF ApexScore Percentiles & Key Outputs</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-zinc-900/80 text-zinc-400 text-[10px] uppercase border-b border-zinc-800">
                    <tr>
                      <th className="py-2.5 px-3">Player</th>
                      <th className="py-2.5 px-3">Role</th>
                      <th className="py-2.5 px-3 text-right">Runs</th>
                      <th className="py-2.5 px-3 text-right">SR</th>
                      <th className="py-2.5 px-3 text-right">Wkts</th>
                      <th className="py-2.5 px-3 text-right">Econ</th>
                      <th className="py-2.5 px-3 text-right">QUWROF Pctile</th>
                      <th className="py-2.5 px-3">Tactical Diagnosis</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/60 font-mono">
                    {warRoomData.audit_2026.squad_apex_ratings.map((s, idx) => (
                      <tr key={idx} className="hover:bg-zinc-800/40 transition">
                        <td className="py-2.5 px-3 font-sans font-bold text-white">{s.name}</td>
                        <td className="py-2.5 px-3 font-sans text-zinc-400 text-[11px]">{s.role}</td>
                        <td className="py-2.5 px-3 text-right text-zinc-300">{s.runs}</td>
                        <td className="py-2.5 px-3 text-right text-zinc-300">{s.sr.toFixed(1)}</td>
                        <td className="py-2.5 px-3 text-right text-zinc-300">{s.wkts}</td>
                        <td className="py-2.5 px-3 text-right text-zinc-300">{s.econ.toFixed(2)}</td>
                        <td className="py-2.5 px-3 text-right font-bold">
                          <span className={`px-2 py-0.5 rounded text-[11px] ${
                            s.quwrof_pctile >= 90 ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' :
                            s.quwrof_pctile >= 70 ? 'bg-sky-500/20 text-sky-400 border border-sky-500/40' :
                            'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                          }`}>
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

        {/* TAB 4: METRIC ARCHITECTURE & PRIOR FLAW SOLUTIONS */}
        {activeTab === 'metrics' && (
          <div className="space-y-8 max-w-4xl mx-auto">
            <div className="border-b border-zinc-800 pb-3">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <span>🧠</span> Pressure Rating Engine: Architecture & Mathematical Formulation
              </h2>
              <p className="text-xs text-zinc-400">Addressing the flaws of naive ratio models and explaining our dual-criterion solution</p>
            </div>

            {/* The Flaw and The Fix */}
            <div className="rounded-xl border border-amber-500/30 bg-amber-950/10 p-5 space-y-3">
              <div className="text-amber-400 font-bold text-sm flex items-center gap-2">
                <span>⚠️</span> The Flaw in Naive Pressure Ratings: The "Mediocre Baseline" Bias
              </div>
              <p className="text-xs text-zinc-300 leading-relaxed">
                Prior pressure studies often use simple ratio metrics: <code className="text-amber-300 bg-zinc-900 px-1 py-0.5 rounded">SR_pressure / SR_baseline</code>. 
                In our June 2026 QUWROF experiments, we discovered that this creates severe distortion:
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                <div className="p-3 rounded bg-zinc-900 border border-zinc-800">
                  <span className="text-rose-400 font-bold block mb-1">Below-Average Batter</span>
                  Baseline SR: 100 → Pressure SR: 120. Ratio = <strong className="text-rose-400">1.20x (+20%)</strong>.
                  <span className="text-zinc-500 block mt-1">Inflated to the top of rankings despite striking at only 120!</span>
                </div>
                <div className="p-3 rounded bg-zinc-900 border border-zinc-800">
                  <span className="text-emerald-400 font-bold block mb-1">Elite World-Class Finisher</span>
                  Baseline SR: 175 → Pressure SR: 180. Ratio = <strong className="text-emerald-400">1.03x (+3%)</strong>.
                  <span className="text-zinc-500 block mt-1">Penalized because their baseline was already historically dominant.</span>
                </div>
              </div>
            </div>

            {/* The Dual-Criterion Solution */}
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/10 p-5 space-y-4">
              <div className="text-emerald-400 font-bold text-sm flex items-center gap-2">
                <span>✅</span> The Solution: Dual-Criterion Blended Model
              </div>
              <p className="text-xs text-zinc-300 leading-relaxed">
                We combine <strong>50% Normalized Absolute Output</strong> (benchmarked against the 85th/90th percentile of all high-pressure deliveries) with <strong>50% Relative Maintenance</strong>:
              </p>

              <div className="p-4 rounded-lg bg-zinc-900/90 border border-zinc-800 font-mono text-xs text-zinc-200 space-y-2">
                <div className="text-[#ff4d9d] font-bold">// Batter Pressure Rating (BPR)</div>
                <div>BPR = 0.40 * (SR_pres / P85_pres_SR) + 0.35 * (SR_pres / SR_base) + 0.15 * clip(Avg_pres / Avg_base, 0.5, 2.0) - 0.20 * (ΔDot%)</div>
                <div className="text-zinc-500 text-[11px]">// Where ΔDot% = Dot%_pres - Dot%_base (penalizes freezing)</div>
              </div>

              <div className="p-4 rounded-lg bg-zinc-900/90 border border-zinc-800 font-mono text-xs text-zinc-200 space-y-2">
                <div className="text-sky-400 font-bold">// Bowler Pressure Rating (BowPR)</div>
                <div>BowPR = 0.40 * clip(P15_pres_econ / Econ_pres, 0.5, 2.0) + 0.30 * clip(Econ_base / Econ_pres, 0.5, 2.0) + 0.20 * (WktRate_pres / 0.80) + 0.10 * (1.0 + ΔDot%)</div>
                <div className="text-zinc-500 text-[11px]">// Where P15_pres_econ represents elite death economy benchmark (~7.50 RPO)</div>
              </div>
            </div>

            {/* 65:35 Architecture */}
            <div className="rounded-xl border border-zinc-800 bg-[#0d1326] p-5 space-y-3">
              <h3 className="text-sm font-bold text-white">65:35 IPL : T20I Architecture with Bayesian Shrinkage</h3>
              <p className="text-xs text-zinc-300 leading-relaxed">
                Why 65:35? In QUWROF V11–V14, cross-validation demonstrated that IPL competition density is strictly uniform (10 world-class XIs with intense auction scouting). International T20Is include bilateral matches against rotating squads or Associate teams.
              </p>
              <div className="p-3 rounded bg-zinc-900 border border-zinc-800 font-mono text-xs text-amber-300">
                Combined Score = 0.65 * Rating_IPL + 0.35 * Rating_T20I
              </div>
              <p className="text-xs text-zinc-400">
                For single-format players, the unobserved format is regressed toward the baseline neutral anchor (1.00) via Bayesian shrinkage <code className="text-zinc-300">k = min(balls / 120, 1.0)</code>, eliminating small-sample fluke inflation.
              </p>
            </div>
          </div>
        )}

        {/* TAB 5: JOURNEY / X THREAD */}
        {activeTab === 'journey' && (
          <div className="space-y-6 max-w-2xl mx-auto">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <span>🧵</span> The Journey: From QUWROF to SupeRR Selector
                </h2>
                <p className="text-xs text-zinc-400">Ready-to-post Twitter / X thread documenting the engineering journey</p>
              </div>
              <button
                onClick={handleCopyAllTweets}
                className="px-3 py-1.5 rounded-lg bg-[#ff2a85] text-white text-xs font-bold hover:bg-[#e11d48] transition flex items-center gap-1.5 shadow-md shadow-[#ff2a85]/20"
              >
                <span>{copiedTweet === 999 ? '✓ Copied All!' : 'Copy Full Thread'}</span>
              </button>
            </div>

            <div className="space-y-4">
              {warRoomData.journey_thread.map(t => (
                <div key={t.tweet_num} className="p-4 rounded-xl bg-[#0d1326] border border-zinc-800 hover:border-zinc-700 transition relative">
                  <div className="flex items-center justify-between text-xs text-zinc-500 mb-2">
                    <span className="font-bold text-[#ff2a85]">Tweet {t.tweet_num} of {warRoomData.journey_thread.length}</span>
                    <button
                      onClick={() => handleCopyTweet(t.text, t.tweet_num)}
                      className="text-zinc-400 hover:text-white transition text-[11px] px-2 py-0.5 rounded bg-zinc-800"
                    >
                      {copiedTweet === t.tweet_num ? '✓ Copied' : 'Copy'}
                    </button>
                  </div>
                  <p className="text-sm text-zinc-200 whitespace-pre-line leading-relaxed font-sans">{t.text}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 6: SUBMISSION REPORT (PDF READY) */}
        {activeTab === 'report' && (
          <div className="space-y-8 max-w-4xl mx-auto bg-zinc-950 p-6 sm:p-10 rounded-2xl border border-zinc-800 shadow-2xl">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
              <div>
                <div className="text-xs font-bold text-[#ff2a85] uppercase tracking-wider">Unstop SupeRR Selector Season 2 • Round 1</div>
                <h2 className="text-2xl font-black text-white mt-1">Rajasthan Royals 2027 Mega Auction Dossier</h2>
                <p className="text-xs text-zinc-400">Author: Shourya • Date: November 2026</p>
              </div>
              <button
                onClick={() => window.print()}
                className="px-4 py-2 rounded-lg bg-zinc-800 text-white text-xs font-bold hover:bg-zinc-700 transition border border-zinc-700 flex items-center gap-1.5"
              >
                <span>🖨️</span> Print / Save as PDF
              </button>
            </div>

            {/* Executive Summary */}
            <div className="space-y-4 text-xs text-zinc-300 leading-relaxed">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider border-b border-zinc-800 pb-1">1. Executive Summary</h3>
              <p>
                An exhaustive audit of the 200,999 delivery dataset reveals that the Rajasthan Royals' 2026 campaign (9 wins, 7 losses) fell short due to three acute phase-specific vulnerabilities:
              </p>
              <ul className="list-disc pl-5 space-y-1 text-zinc-300">
                <li><strong className="text-white">Death Bowling Run Leakage:</strong> In 7 losses, RR conceded 12.30 runs per over in overs 16–20 (vs 9.24 in wins). Sandeep Sharma (13.3 ER) and Tushar Deshpande (11.25 ER) collapsed when Archer was bowled out.</li>
                <li><strong className="text-white">Powerplay Wicket Drought:</strong> In 7 losses, RR took just 4 powerplay wickets total across 42 overs (0.57 per match) while bleeding 11.50 RPO.</li>
                <li><strong className="text-white">Finisher Isolation:</strong> Outside Donovan Ferreira, RR lacked late-overs boundary hitting. Shimron Hetmyer collapsed to a 113.0 SR (22nd percentile in QUWROF).</li>
              </ul>
            </div>

            {/* Official Picks Summary Table */}
            <div className="space-y-4 text-xs">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider border-b border-zinc-800 pb-1">2. Target Picks by Strategic Gap</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 rounded-xl bg-zinc-900 border border-zinc-800 space-y-2">
                  <div className="text-xs font-bold text-rose-400">GAP 1: ARCHER DEATH PARTNER</div>
                  <div className="font-bold text-white text-sm">Jamie Overton (ENG)</div>
                  <p className="text-zinc-400 text-[11px]">6.62 ER in death pressure. 145 km/h wide yorkers + power batting.</p>
                  <div className="text-zinc-300 text-[11px] pt-2 border-t border-zinc-800">
                    <span className="text-zinc-500">Alt Indian:</span> Sakib Hussain (7.70 ER, 11 wkts)
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-zinc-900 border border-zinc-800 space-y-2">
                  <div className="text-xs font-bold text-amber-400">GAP 2: POWERPLAY STRIKER</div>
                  <div className="font-bold text-white text-sm">Mohammed Siraj (IND)</div>
                  <p className="text-zinc-400 text-[11px]">45 PP wickets at 7.98 economy. Premier new-ball strike seamer.</p>
                  <div className="text-zinc-300 text-[11px] pt-2 border-t border-zinc-800">
                    <span className="text-zinc-500">Alt Local:</span> Khaleel Ahmed (26 wkts, 7.79 ER)
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-zinc-900 border border-zinc-800 space-y-2">
                  <div className="text-xs font-bold text-sky-400">GAP 3: CLUTCH FINISHER</div>
                  <div className="font-bold text-white text-sm">Naman Dhir (IND)</div>
                  <p className="text-zinc-400 text-[11px]">209.5 death pressure SR. Attacks spin & pace; frees overseas slot.</p>
                  <div className="text-zinc-300 text-[11px] pt-2 border-t border-zinc-800">
                    <span className="text-zinc-500">Alt Overseas:</span> Cooper Connolly (212.8 SR)
                  </div>
                </div>
              </div>
            </div>

            {/* SMS Jaipur Ground Fit */}
            <div className="space-y-3 text-xs text-zinc-300 leading-relaxed">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider border-b border-zinc-800 pb-1">3. Sawai Mansingh Stadium (Jaipur) Fit</h3>
              <p>
                Sawai Mansingh Stadium features cavernous square boundaries (75m–80m) and an abrasive surface that grips early before dew arrives. Jamie Overton's hard lengths and steep bounce induce mistimed pulls to deep midwicket. Furthermore, wide yorker specialists (Overton and Sakib Hussain) mitigate dew-slicked wet ball slip during 2nd innings chases.
              </p>
            </div>

            <div className="pt-4 border-t border-zinc-800 text-center text-[11px] text-zinc-500">
              Generated by SupeRR Selector Engine • Based on 200,999 Historical Deliveries • Antigravity AI
            </div>
          </div>
        )}

      </main>

      {/* ── FOOTER ────────────────────────────────────────────────────────── */}
      <footer className="border-t border-zinc-800/80 bg-[#0b1021] py-6 text-center text-xs text-zinc-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div>
            <span className="font-bold text-zinc-400">SupeRR Selector 2027</span> — Official Hackathon Technical Submission
          </div>
          <div className="text-zinc-500 text-[11px]">
            Engineered by Shourya • June 2026 QUWROF Heritage • Next.js & Turbopack
          </div>
        </div>
      </footer>
    </div>
  );
}
