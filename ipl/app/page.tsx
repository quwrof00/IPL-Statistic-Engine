"use client";

import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import Image from 'next/image';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, ZAxis, Cell, LabelList } from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';

const CHART_COLORS = ['#b39170', '#3b82f6', '#ef4444', '#10b981'];

const modalSlideVariants = {
  enter: (dir: number) => {
    const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;
    if (!isMobile) return { x: 0, opacity: 1, transition: { duration: 0 } };
    return { x: dir === 1 ? 50 : (dir === -1 ? -50 : 0), opacity: 0 };
  },
  center: {
    x: 0,
    opacity: 1,
    transition: { type: "spring" as const, stiffness: 350, damping: 30 }
  },
  exit: (dir: number) => {
    const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;
    if (!isMobile) return { x: 0, opacity: 0, transition: { duration: 0 } };
    return { x: dir === 1 ? -50 : (dir === -1 ? 50 : 0), opacity: 0 };
  }
};

type PlayerSeason = {
  player_name: string;
  season: string;
  primary_team: string;
  matches?: number;
  quwrof_v11: number;
  quwrof_v14: number;
  bat_points: number;
  bowl_points: number;
  quwrof_final: number;
  bat_percentile: number;
  bowl_percentile: number;
  v14_percentile: number;
  v14_bat_percentile: number;
  v14_bowl_percentile: number;
  runs?: number;
  batting_average?: number;
  strike_rate?: number;
  wickets?: number;
  bowling_average?: number;
  economy?: number;
  [key: string]: any;
};

const formatSeason = (season: string | number) => {
  const s = String(season);
  if (s === '2007/08') return '2008';
  if (s === '2009/10') return '2010';
  if (s === '2020/21') return '2020';
  return s;
};

const v11MetricNames: Record<string, string> = {
  raw_bat: "Basic Batting",
  rae: "Added Runs",
  bat_base: "Batting Rating",
  bat_chase_impact: "Chase & Pressure",
  bat_playoff_impact: "Playoff Clutch",
  raw_bowl: "Basic Bowling",
  bowl_base: "Bowling Rating",
  bowl_pp_impact: "Powerplay Wickets",
  bowl_death_impact: "Death Overs",
  bowl_playoff_impact: "Playoff Clutch",
  bowl_pressure_impact: "Lone Wolf Impact",
  smart_wickets: "High-Value Wickets",
  empirical_wickets: "Adjusted Wickets"
};

const v11MetricDescriptions: Record<string, string> = {
  raw_bat: "A player's standard average and strike rate combined into one score, before considering match context.",
  rae: "How many more runs this batter scored compared to what an average batter would have scored in the exact same match situation.",
  bat_base: "The main batting score. It combines Basic Batting and Added Runs to rate the batter's baseline skill.",
  bat_chase_impact: "Bonus points for scoring heavily in difficult run chases or stopping batting collapses.",
  bat_playoff_impact: "Bonus points for performing under the pressure of playoff and knockout matches.",
  raw_bowl: "A bowler's standard economy and strike rate combined into one score, before considering match context.",
  bowl_base: "The main bowling score. It rates the bowler's overall run prevention and wicket-taking ability.",
  bowl_pp_impact: "Effectiveness at taking wickets and restricting runs in the first 6 overs.",
  bowl_death_impact: "Effectiveness at restricting boundaries during the final 4 overs (16-20).",
  bowl_playoff_impact: "Bonus points for performing under the pressure of playoff and knockout matches.",
  bowl_pressure_impact: "Bonus points for 'lone wolf' bowlers who defended low totals or carried a weak bowling attack.",
  smart_wickets: "Wickets that are given higher value based on the quality of the batter dismissed (e.g., getting Kohli out is worth more).",
  empirical_wickets: "Total wickets taken, adjusted for the specific era and pitch conditions they played in."
};

const basicMetricNames: Record<string, string> = {
  runs: "Runs",
  strike_rate: "Strike Rate",
  batting_average: "Batting Average",
  wickets: "Wickets",
  economy: "Economy",
  bowling_average: "Bowling Average"
};

const v14MetricNames: Record<string, string> = {
  bat_points: "Batting Points",
  bowl_points: "Bowling Points",
  bat_z: "Batting Score (Z)",
  bowl_z: "Bowling Score (Z)",
  z_sr: "Strike Rate Score",
  z_econ: "Economy Score",
  bat_playoff_impact_points: "Bat Playoff Pts",
  bowl_playoff_impact_points: "Bowl Playoff Pts",
  pca_efficiency: "Role Efficiency",
  impact_score: "Match Impact",
  rarity_score: "Freak Factor",
  dominance_percentile: "Dominance Pct"
};

const engineNames: Record<string, string> = {
  quwrof_v11: "Contextual Percentile",
  quwrof_v14: "Apex Z-Score",
  quwrof_final: "Final Engine"
};

const allMetricNames: Record<string, string> = {
  ...v11MetricNames,
  ...basicMetricNames,
  ...v14MetricNames,
  quwrof_v11: "Contextual Percentile",
  quwrof_v14: "Apex Z-Score",
  v14_percentile: "Overall Pct (V14)",
  v14_bat_percentile: "Batting Pct (V14)",
  v14_bowl_percentile: "Bowling Pct (V14)",
  bat_percentile: "Batting Pct (V11)",
  bowl_percentile: "Bowling Pct (V11)"
};

const metricDescriptions: Record<string, string> = {
  ...v11MetricDescriptions,
  quwrof_v11: "Contextual Percentile: The player's overall rating out of 100, factoring in match pressure, phase of play, and pitch conditions.",
  quwrof_v14: "Apex Z-Score: The player's overall rating compared to the average player, without any maximum limit.",
  v14_percentile: "Overall Percentile: The player's overall rating out of 100.",
  v14_bat_percentile: "Batting Percentile: The player's batting rating out of 100.",
  v14_bowl_percentile: "Bowling Percentile: The player's bowling rating out of 100.",
  bat_percentile: "Batting Percentile: The player's batting rating out of 100, factoring in match context.",
  bowl_percentile: "Bowling Percentile: The player's bowling rating out of 100, factoring in match context.",
  bat_points: "Batting Points: Uncapped points awarded for batting performances.",
  bowl_points: "Bowling Points: Uncapped points awarded for bowling performances."
};

const InfoTooltip = ({ text }: { text?: string }) => {
  if (!text) return null;
  return (
    <button type="button" className="group/tooltip relative inline-block ml-1.5 align-middle cursor-help z-50 focus:outline-none">
      <div className="w-4 h-4 rounded-full border border-[#b39170] text-[#b39170] opacity-70 flex items-center justify-center text-[9px] font-black group-hover/tooltip:opacity-100 group-focus/tooltip:opacity-100 group-hover/tooltip:bg-[#b39170] group-focus/tooltip:bg-[#b39170] group-hover/tooltip:text-white group-focus/tooltip:text-white transition-colors">i</div>
      <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 w-48 sm:w-56 p-2.5 bg-zinc-950 text-zinc-300 text-[11px] leading-relaxed rounded-sm shadow-2xl opacity-0 invisible group-hover/tooltip:opacity-100 group-focus/tooltip:opacity-100 group-hover/tooltip:visible group-focus/tooltip:visible transition-all pointer-events-none whitespace-normal normal-case tracking-normal font-normal border border-zinc-700 text-left z-[100]">
        {text}
      </div>
    </button>
  );
};

const getTeamColor = (team: string) => {
  const t = team.toLowerCase();
  if (t.includes('chennai')) return '#F9CD05';
  if (t.includes('mumbai')) return '#004BA0';
  if (t.includes('kolkata')) return '#3A225D';
  if (t.includes('bangalore') || t.includes('bengaluru')) return '#EC1C24';
  if (t.includes('rajasthan')) return '#EA1A85';
  if (t.includes('delhi')) return '#00008B';
  if (t.includes('punjab') || t.includes('kings xi')) return '#ED1B24';
  if (t.includes('sunrisers') || t.includes('hyderabad')) return '#FF822A';
  if (t.includes('gujarat')) return '#1B2133';
  if (t.includes('lucknow')) return '#A7F2F1';
  if (t.includes('pune')) return '#D11D9B';
  return '#d2b89d'; // Default fallback
};

export default function Home() {
  const [data, setData] = useState<PlayerSeason[]>([]);

  // Main Table State
  const [search, setSearch] = useState("");
  const [teamFilter, setTeamFilter] = useState("All");
  const [seasonFilter, setSeasonFilter] = useState("All");
  const [sortKey, setSortKey] = useState<keyof PlayerSeason | null>(null);
  const [sortDirection, setSortDirection] = useState<'desc' | 'asc'>('desc');
  const [engine, setEngine] = useState<keyof PlayerSeason>('quwrof_v14');

  // Pre-calculate ranks for all metrics to avoid O(N) calculations in render cycle
  const metricRanks = useMemo(() => {
    if (data.length === 0) return {};
    const ranks: Record<string, Map<string, number>> = {};
    const keys = Object.keys(allMetricNames);
    keys.forEach(key => {
      const sorted = [...data].sort((a, b) => (Number(b[key as keyof PlayerSeason]) || 0) - (Number(a[key as keyof PlayerSeason]) || 0));
      const map = new Map<string, number>();
      sorted.forEach((d, i) => map.set(`${d.player_name}-${d.season}-${d.primary_team}`, i + 1));
      ranks[key] = map;
    });
    return ranks;
  }, [data]);

  // Modal State
  const [selectedPlayer, setSelectedPlayer] = useState<PlayerSeason | null>(null);
  const [modalTab, setModalTab] = useState<'batting' | 'bowling'>('batting');

  // Comparison Dashboard State
  const [comparedPlayers, setComparedPlayers] = useState<PlayerSeason[]>([]);
  const [compareSearch, setCompareSearch] = useState("");
  const [compareSuggestions, setCompareSuggestions] = useState<PlayerSeason[]>([]);
  const [comparisonTab, setComparisonTab] = useState<'all' | 'batting' | 'bowling'>('all');
  const [compareEngine, setCompareEngine] = useState<'quwrof_v11' | 'quwrof_v14'>('quwrof_v14');

  const [scatterEngine, setScatterEngine] = useState<'quwrof_v11' | 'quwrof_v14'>('quwrof_v14');
  const [scatterXMetric, setScatterXMetric] = useState<keyof PlayerSeason>('bat_base');
  const [scatterYMetric, setScatterYMetric] = useState<keyof PlayerSeason>('bat_chase_impact');
  const [scatterCustomPlayers, setScatterCustomPlayers] = useState<PlayerSeason[]>([]);
  const [scatterSearch, setScatterSearch] = useState("");
  const [scatterSuggestions, setScatterSuggestions] = useState<PlayerSeason[]>([]);

  const scatterData = useMemo(() => {
    if (data.length === 0) return [];

    // Find max for normalization
    let maxX = 0;
    let maxY = 0;
    data.forEach(p => {
      const x = Number(p[scatterXMetric]) || 0;
      const y = Number(p[scatterYMetric]) || 0;
      if (x > maxX) maxX = x;
      if (y > maxY) maxY = y;
    });

    const mapped = [...data]
      .filter(p => Number(p[scatterXMetric]) > 0 || Number(p[scatterYMetric]) > 0)
      .map(p => {
        const xVal = Number(p[scatterXMetric]) || 0;
        const yVal = Number(p[scatterYMetric]) || 0;
        const xNorm = maxX > 0 ? xVal / maxX : 0;
        const yNorm = maxY > 0 ? yVal / maxY : 0;
        return {
          ...p,
          xVal,
          yVal,
          xNorm,
          yNorm,
          nameAndSeason: `${p.player_name} '${formatSeason(p.season).slice(-2)}`
        };
      });

    // Sort by sum of normalized scores
    const top20 = mapped.sort((a, b) => (b.xNorm + b.yNorm) - (a.xNorm + a.yNorm)).slice(0, 20);

    // Force add custom players if they aren't already in the top 20
    const customToAdd = scatterCustomPlayers.map(cp => {
      const xVal = Number(cp[scatterXMetric]) || 0;
      const yVal = Number(cp[scatterYMetric]) || 0;
      return {
        ...cp,
        xVal,
        yVal,
        nameAndSeason: `${cp.player_name} '${formatSeason(cp.season).slice(-2)}`
      };
    }).filter(cp => !top20.some(t => t.player_name === cp.player_name && t.season === cp.season));

    return [...top20, ...customToAdd];
  }, [data, scatterXMetric, scatterYMetric, scatterCustomPlayers]);

  const ScatterTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const pData = payload[0].payload;
      return (
        <div className="bg-[#111] border border-zinc-800 p-4 rounded-sm shadow-xl text-xs z-50">
          <div className="flex items-center gap-2 mb-2">
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: getTeamColor(pData.primary_team) }}></span>
            <span className="font-bold text-white text-sm tracking-tight">{pData.player_name}</span>
          </div>
          <div className="text-[10px] font-bold text-zinc-500 tracking-wider uppercase mb-3">{pData.primary_team} • {formatSeason(pData.season)}</div>
          <div className="space-y-1.5">
            <div className="flex justify-between gap-6">
              <span className="text-zinc-400 font-semibold">{allMetricNames[scatterXMetric as string] || scatterXMetric}</span>
              <span className="text-zinc-200 font-black">{pData.xVal.toFixed(2)}</span>
            </div>
            <div className="flex justify-between gap-6">
              <span className="text-zinc-400 font-semibold">{allMetricNames[scatterYMetric as string] || scatterYMetric}</span>
              <span className="text-zinc-200 font-black">{pData.yVal.toFixed(2)}</span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  const chartData = useMemo(() => {
    if (comparedPlayers.length === 0) return [];

    let metrics: any[] = [];
    if (compareEngine === 'quwrof_v14') {
      if (comparisonTab === 'all' || comparisonTab === 'batting') {
        metrics.push(
          { key: 'bat_base_points', label: 'Bat Base', max: 1800 },
          { key: 'bat_chase_impact_points', label: 'Pressure', max: 300 },
          { key: 'bat_playoff_impact_points', label: 'Playoff Bat', max: 300 }
        );
      }
      if (comparisonTab === 'all' || comparisonTab === 'bowling') {
        metrics.push(
          { key: 'bowl_base_points', label: 'Bowl Base', max: 1800 },
          { key: 'bowl_pp_impact_points', label: 'Powerplay', max: 200 },
          { key: 'bowl_death_impact_points', label: 'Death Impact', max: 200 },
          { key: 'bowl_pressure_impact_points', label: 'Bowl Pressure', max: 200 },
          { key: 'bowl_playoff_impact_points', label: 'Playoff Bowl', max: 300 }
        );
      }
    } else {
      if (comparisonTab === 'all' || comparisonTab === 'batting') {
        metrics.push(
          { key: 'bat_base', label: 'Bat Base', max: 1500 },
          { key: 'rae', label: 'RAE', max: 300 },
          { key: 'bat_chase_impact', label: 'Pressure', max: 50 },
          { key: 'bat_playoff_impact', label: 'Playoff Bat', max: 100 }
        );
      }
      if (comparisonTab === 'all' || comparisonTab === 'bowling') {
        metrics.push(
          { key: 'bowl_base', label: 'Bowl Base', max: 4000 },
          { key: 'smart_wickets', label: 'Smart Wkts', max: 50 },
          { key: 'bowl_death_impact', label: 'Death Impact', max: 100 },
          { key: 'bowl_playoff_impact', label: 'Playoff Bowl', max: 150 }
        );
      }
    }

    return metrics.map(m => {
      const dataPoint: any = { subject: m.label, fullMark: m.max };
      comparedPlayers.forEach(p => {
        const pKey = `${p.player_name} ${formatSeason(p.season)}`;
        const val = Math.max(0, Number(p[m.key as keyof PlayerSeason]) || 0);
        dataPoint[pKey] = (val / m.max) * 100;
        dataPoint[`${pKey}_raw`] = val;
      });
      return dataPoint;
    });
  }, [comparedPlayers, comparisonTab, compareEngine]);

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-zinc-900 border border-zinc-800 p-4 rounded-sm shadow-xl text-xs z-50 relative">
          <p className="text-zinc-400 font-bold tracking-widest uppercase mb-2">{payload[0].payload.subject}</p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center justify-between gap-6 py-1">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }}></span>
                <span className="text-zinc-300 font-semibold">{entry.name}</span>
              </div>
              <span className="text-white font-black">{Number(entry.payload[`${entry.name}_raw`]).toFixed(1)}</span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  // Pagination States
  const [mainTablePage, setMainTablePage] = useState(1);
  const [allRoundersPage, setAllRoundersPage] = useState(1);
  const [playoffPage, setPlayoffPage] = useState(1);
  const [allRounderEngine, setAllRounderEngine] = useState<'quwrof_v11' | 'quwrof_v14'>('quwrof_v14');
  const [playoffEngine, setPlayoffEngine] = useState<'quwrof_v11' | 'quwrof_v14'>('quwrof_v14');

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
      .filter(p => playoffEngine === 'quwrof_v14' ? (Number(p.bat_playoff_impact_points) > 0 || Number(p.bowl_playoff_impact_points) > 0) : (Number(p.bat_playoff_impact) > 0 || Number(p.bowl_playoff_impact) > 0))
      .map(p => {
        if (playoffEngine === 'quwrof_v14') {
          const batPlayoff = Number(p.bat_playoff_impact_points) || 0;
          const bowlPlayoff = Number(p.bowl_playoff_impact_points) || 0;
          const clutchScore = batPlayoff + bowlPlayoff;
          return {
            ...p,
            batPlayoff,
            bowlPlayoff,
            clutchScore
          };
        } else {
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
        }
      })
      .sort((a, b) => b.clutchScore - a.clutchScore);
  }, [data, playoffEngine]);

  const eliteAllRounders = useMemo(() => {
    if (data.length === 0) return [];
    if (allRounderEngine === 'quwrof_v14') {
      return [...data]
        .filter(p => Number(p.v14_bat_percentile) >= 60 && Number(p.v14_bowl_percentile) >= 60)
        .sort((a, b) => Number(b.quwrof_v14) - Number(a.quwrof_v14));
    } else {
      return [...data]
        .filter(p => Number(p.bat_percentile) >= 60 && Number(p.bowl_percentile) >= 60)
        .sort((a, b) => Number(b.quwrof_v11) - Number(a.quwrof_v11));
    }
  }, [data, allRounderEngine]);

  // Reset pagination on filter changes
  useEffect(() => { setMainTablePage(1); }, [search, teamFilter, seasonFilter, sortKey, sortDirection, engine]);

  useEffect(() => { setSortKey(null); }, [engine]);

  useEffect(() => {
    fetch(`/data_v2.json?v=${new Date().getTime()}`)
      .then((res) => res.json())
      .then((json) => setData(json));
  }, []);

  const uniqueTeams = useMemo(() => Array.from(new Set(data.map(d => d.primary_team).filter(Boolean))).sort(), [data]);
  const uniqueSeasons = useMemo(() => Array.from(new Set(data.map(d => d.season).filter(Boolean))).sort(), [data]);

  // Main Table Filter
  const filteredData = useMemo(() => {
    return data
      .filter(d => {
        const matchesSearch = d.player_name.toLowerCase().includes(search.toLowerCase());
        const matchesTeam = teamFilter === "All" || d.primary_team === teamFilter;
        const matchesSeason = seasonFilter === "All" || String(d.season) === seasonFilter;
        return matchesSearch && matchesTeam && matchesSeason;
      })
      .sort((a, b) => {
        const key = sortKey || engine;
        let valA = Number(a[key]) || 0;
        let valB = Number(b[key]) || 0;

        if (key === 'impact_per_match' as any) {
          valA = a.matches ? (Number(a[engine]) / a.matches) : 0;
          valB = b.matches ? (Number(b[engine]) / b.matches) : 0;
        }

        return sortDirection === 'desc' ? valB - valA : valA - valB;
      })
      .slice(0, 50);
  }, [data, search, teamFilter, seasonFilter, engine, sortKey, sortDirection]);

  // Comparison Search Logic
  useEffect(() => {
    if (compareSearch.length > 1) {
      setCompareSuggestions(data.filter(d =>
        d.player_name.toLowerCase().includes(compareSearch.toLowerCase()) &&
        !comparedPlayers.some(cp => cp.player_name === d.player_name && cp.season === d.season && cp.primary_team === d.primary_team)
      ).slice(0, 6));
    } else {
      setCompareSuggestions([]);
    }
  }, [compareSearch, data, comparedPlayers]);

  const handleAddComparePlayer = (p: PlayerSeason) => {
    if (comparedPlayers.length < 6) {
      setComparedPlayers([...comparedPlayers, p]);
    }
    setCompareSearch("");
    setCompareSuggestions([]);
  };

  // Scatter Plot Search Logic
  useEffect(() => {
    if (scatterSearch.length > 1) {
      setScatterSuggestions(data.filter(d =>
        d.player_name.toLowerCase().includes(scatterSearch.toLowerCase()) &&
        !scatterCustomPlayers.some(cp => cp.player_name === d.player_name && cp.season === d.season && cp.primary_team === d.primary_team)
      ).slice(0, 6));
    } else {
      setScatterSuggestions([]);
    }
  }, [scatterSearch, data, scatterCustomPlayers]);

  const handleAddScatterPlayer = (p: PlayerSeason) => {
    setScatterCustomPlayers([...scatterCustomPlayers, p]);
    setScatterSearch("");
    setScatterSuggestions([]);
  };

  const handleSort = (key: keyof PlayerSeason) => {
    if (sortKey === key) setSortDirection(sortDirection === 'desc' ? 'asc' : 'desc');
    else { setSortKey(key); setSortDirection('desc'); }
  };

  const renderSortableHeader = (label: React.ReactNode | string, key: keyof PlayerSeason) => (
    <th
      className="px-2 md:px-4 py-4 text-[10px] font-bold text-zinc-500 uppercase tracking-widest cursor-pointer hover:text-white transition-colors select-none text-right md:text-left"
      onClick={() => handleSort(key)}
    >
      <div className="flex items-center justify-end md:justify-start gap-1.5">
        {label}
        <span className="text-[#b39170] text-[10px]">
          {sortKey === key ? (sortDirection === 'desc' ? '▼' : '▲') : ''}
        </span>
      </div>
    </th>
  );

  const modalStats = useMemo(() => {
    if (!selectedPlayer || data.length === 0) return null;
    const stats: Record<string, { val: number; rank: number; percentile: number; seasonRank: number; seasonN: number }> = {};
    const N = data.length;
    const pKey = `${selectedPlayer.player_name}-${selectedPlayer.season}-${selectedPlayer.primary_team}`;

    const seasonPlayers = data.filter(p => p.season === selectedPlayer.season);
    const seasonN = seasonPlayers.length;

    Object.keys(allMetricNames).forEach((metricKey) => {
      const key = metricKey as keyof PlayerSeason;
      const val = Number(selectedPlayer[key]) || 0;
      const rank = metricRanks[key]?.get(pKey) || N;
      const percentile = ((N - rank) / N) * 100;

      let higherCount = 0;
      for (let i = 0; i < seasonN; i++) {
        if ((Number(seasonPlayers[i][key]) || 0) > val) {
          higherCount++;
        }
      }
      const seasonRank = higherCount + 1;

      stats[key] = { val, rank, percentile, seasonRank, seasonN };
    });
    return stats;
  }, [selectedPlayer, data, metricRanks]);

  const comparisonStats = useMemo(() => {
    if (comparedPlayers.length === 0 || data.length === 0) return null;
    const stats: Record<string, { val: number; rank: number; percentile: number }[]> = {};
    const keys = ['quwrof_v11', 'quwrof_v14', 'impact_per_match', 'bat_percentile', 'bowl_percentile', 'bat_points', 'bowl_points', ...Object.keys(allMetricNames)];
    const N = data.length;

    keys.forEach((metricKey) => {
      const key = metricKey as keyof PlayerSeason;

      // Calculate max val if it's impact_per_match to create a local relative percentile
      let maxLocalImpact = 0;
      if (key === 'impact_per_match') {
        maxLocalImpact = Math.max(...data.map(p => p.matches ? (Number(p[engine]) / p.matches) : 0));
      }

      stats[key] = comparedPlayers.map(player => {
        const pKey = `${player.player_name}-${player.season}-${player.primary_team}`;
        const val = key === 'impact_per_match'
          ? (player.matches ? (Number(player[engine]) / player.matches) : 0)
          : (Number(player[key]) || 0);

        let percentile = 0;
        if (key === 'impact_per_match') {
          percentile = maxLocalImpact > 0 ? (val / maxLocalImpact) * 100 : 0;
        } else {
          const rank = metricRanks[key]?.get(pKey) || N;
          percentile = ((N - rank) / N) * 100;
        }

        return { val, rank: 0, percentile };
      });
    });
    return stats;
  }, [comparedPlayers, data, metricRanks]);

  const selectedIndex = selectedPlayer ? filteredData.findIndex(p => p.player_name === selectedPlayer.player_name && p.season === selectedPlayer.season && p.primary_team === selectedPlayer.primary_team) : -1;

  const [slideDirection, setSlideDirection] = useState<number>(0);

  const handlePrev = useCallback(() => {
    if (selectedIndex > 0) {
      setSlideDirection(-1);
      setSelectedPlayer(filteredData[selectedIndex - 1]);
    }
  }, [selectedIndex, filteredData]);

  const handleNext = useCallback(() => {
    if (selectedIndex >= 0 && selectedIndex < filteredData.length - 1) {
      setSlideDirection(1);
      setSelectedPlayer(filteredData[selectedIndex + 1]);
    }
  }, [selectedIndex, filteredData]);
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

  // Modal Keyboard Shortcuts
  useEffect(() => {
    if (selectedPlayer) {
      document.body.style.overflow = 'hidden';
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape') setSelectedPlayer(null);
        else if (e.key === 'ArrowLeft') handlePrev();
        else if (e.key === 'ArrowRight') handleNext();
      };
      window.addEventListener('keydown', handleKeyDown);
      return () => { document.body.style.overflow = 'unset'; window.removeEventListener('keydown', handleKeyDown); };
    } else {
      document.body.style.overflow = 'unset';
    }
  }, [selectedPlayer, handlePrev, handleNext]);

  const teamColor = selectedPlayer ? getTeamColor(selectedPlayer.primary_team) : "#b39170";

  return (
    <div className="min-h-screen bg-[#0a0a0a] font-sans text-zinc-200 selection:bg-[#b39170] selection:text-white pb-24">

      {/* 0. NAVBAR */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-3 md:px-8 py-4 bg-[#0a0a0a]/90 backdrop-blur-md border-b border-zinc-900/50">
        <div 
          className="flex items-center gap-2 cursor-pointer"
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
        >
          <div className="w-5 h-5 md:w-8 md:h-8 bg-[#b39170] rounded-sm flex items-center justify-center shadow-lg shadow-[#b39170]/20">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" className="md:w-[14px] md:h-[14px]"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /></svg>
          </div>
          <span className="text-lg md:text-xl font-bold tracking-tight text-white">Apex<span className="text-[#b39170]">Score</span></span>
        </div>
        <div className="flex items-center gap-3 md:gap-8 text-[11px] sm:text-xs md:text-sm font-semibold text-zinc-400">
          <a href="#home" onClick={(e) => { e.preventDefault(); document.getElementById('home')?.scrollIntoView({ behavior: 'smooth' }); }} className="hover:text-white transition-colors">Home</a>
          <a href="#leaderboards" onClick={(e) => { e.preventDefault(); document.getElementById('leaderboards')?.scrollIntoView({ behavior: 'smooth' }); }} className="hover:text-white transition-colors">Leaderboards</a>
          <a href="#compare" onClick={(e) => { e.preventDefault(); document.getElementById('compare')?.scrollIntoView({ behavior: 'smooth' }); }} className="hover:text-white transition-colors">Compare</a>
        </div>
      </nav>

      {/* 1. HERO SECTION */}
      <section id="home" className="relative h-screen min-h-[700px] flex items-center justify-center overflow-hidden">
        <div className="absolute inset-0 z-0 bg-black">
          <Image
            src="/hero_split_bg.png"
            alt="Hero Background"
            fill
            className="object-cover opacity-20"
            priority
          />
        </div>
        <div className="absolute inset-0 z-0 bg-gradient-to-t from-[#0a0a0a] to-transparent"></div>
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-zinc-900/40 via-[#0a0a0a] to-[#0a0a0a]"></div>
        <div className="relative z-10 text-center max-w-5xl px-4 md:px-8">
          <h1 className="text-6xl md:text-9xl font-black tracking-tighter mb-8 leading-none bg-clip-text text-transparent bg-gradient-to-br from-white via-zinc-400 to-zinc-800">
            Cricket, <br /> Quantified.
          </h1>
          <p className="text-lg md:text-2xl text-zinc-500 font-light max-w-2xl mx-auto leading-relaxed mb-12">
            The most mathematically advanced evaluation engine for T20 cricket, removing era bias and narrative distortion.
          </p>
          <div className="flex items-center justify-center gap-4">
            <button
              onClick={() => { document.getElementById('leaderboards')?.scrollIntoView({ behavior: 'smooth' }); }}
              className="px-8 py-4 bg-[#b39170] text-white font-bold tracking-widest uppercase text-sm hover:bg-white hover:text-black transition-all rounded-sm shadow-xl"
            >
              View Ranking
            </button>
            <button
              onClick={() => window.scrollTo({ top: window.innerHeight, behavior: 'smooth' })}
              className="px-8 py-4 bg-white text-black font-bold tracking-widest uppercase text-sm hover:bg-[#b39170] hover:text-white transition-all rounded-sm shadow-xl"
            >
              Explore Analysis
            </button>
          </div>
        </div>
      </section>

      {/* 4. UNDERSTANDING THE ENGINES */}
      <section className="py-32 md:py-40 px-4 md:px-8 max-w-4xl mx-auto">
        <div className="text-center mb-24">
          <h2 className="text-5xl md:text-7xl font-black tracking-tighter mb-6 bg-clip-text text-transparent bg-gradient-to-br from-white to-zinc-600">The Evolution of ApexScore</h2>
          <p className="text-xl md:text-2xl text-zinc-500 font-light">From evaluating context to measuring pure statistical dominance.</p>
        </div>

        <div className="relative border-l-2 border-zinc-800 pl-8 md:pl-20 py-8 space-y-24 md:space-y-32">
          {/* V1 Story Node */}
          <div className="relative">
            <div className="absolute -left-[41px] md:-left-[89px] top-0 w-8 h-8 rounded-full bg-black border-4 border-zinc-700 flex items-center justify-center">
              <div className="w-2 h-2 rounded-full bg-zinc-500"></div>
            </div>

            <div className="mb-4 flex items-baseline gap-4">
              <h3 className="text-4xl md:text-5xl font-black text-white">Contextual Percentile</h3>
              <span className="text-sm font-bold tracking-widest uppercase text-zinc-500">Engine V1</span>
            </div>

            <p className="text-zinc-400 font-light leading-relaxed text-xl mb-8">
              Our foundational V1 engine proved <strong className="text-white font-semibold">how hard</strong> a performance was. By mathematically factoring in match pressure, phase of play, and the quality of opponents, it stripped away surface-level stats.
            </p>

            <div className="space-y-6 text-lg text-zinc-500">
              <div className="flex items-start gap-4">
                <span className="text-[#b39170] mt-1 text-xl">✦</span>
                <p><strong className="text-zinc-300 font-semibold">Pressure Impact:</strong> Heavily rewards runs scored in steep run chases.</p>
              </div>
              <div className="flex items-start gap-4">
                <span className="text-[#b39170] mt-1 text-xl">✦</span>
                <p><strong className="text-zinc-300 font-semibold">Smart Wickets:</strong> Dismissing a premier batsman yields a significantly higher weight than a tail-ender.</p>
              </div>
              <div className="flex items-start gap-4 mt-8 p-6 bg-red-950/20 border border-red-900/30 rounded-sm">
                <span className="text-red-500 mt-1 text-xl">✕</span>
                <p className="text-zinc-400"><strong className="text-red-400 font-semibold">The Limitation:</strong> V1 ranked players from 0-100. The problem? A percentile ceiling <strong className="text-white font-medium">squashes generational, historical outliers</strong> against merely "great" seasons. It couldn't express *how much better* a player was once they hit the 99th percentile.</p>
              </div>
            </div>
          </div>

          {/* V2 Story Node */}
          <div className="relative">
            <div className="absolute -left-[41px] md:-left-[89px] top-0 w-8 h-8 rounded-full bg-[#b39170] shadow-[0_0_20px_rgba(179,145,112,0.4)] flex items-center justify-center">
              <div className="w-2 h-2 rounded-full bg-black"></div>
            </div>

            <div className="mb-4 flex items-baseline gap-4">
              <h3 className="text-4xl md:text-5xl font-black text-[#b39170]">Apex Z-Score</h3>
              <span className="text-sm font-bold tracking-widest uppercase text-[#b39170]">Engine V2 • Current Standard</span>
            </div>

            <p className="text-zinc-300 font-light leading-relaxed text-xl mb-8">
              To shatter the percentile ceiling, V2 implements <strong className="text-white font-semibold">Uncapped Z-Score Scaling</strong>. We measure exactly how many Standard Deviations a player was above the true mean.
            </p>

            <div className="space-y-6 text-lg text-zinc-400">
              <div className="flex items-start gap-4 p-6 bg-[#b39170]/10 border border-[#b39170]/30 rounded-sm">
                <span className="text-[#b39170] mt-1 text-xl">✦</span>
                <p><strong className="text-white font-semibold">Uncapped Scaling:</strong> Generational seasons (like Kohli '16, Gayle '12) are allowed to stack points infinitely, <strong className="text-[#b39170] font-medium">proving exactly how much better they were</strong> than the rest of the league.</p>
              </div>
              <div className="flex items-start gap-4">
                <span className="text-zinc-500 mt-1 text-xl">✦</span>
                <p><strong className="text-zinc-300 font-semibold">Specialist Floor:</strong> Negative Z-Scores are floored at 0, protecting pure specialists from being mathematically dragged down by their non-primary skill.</p>
              </div>
              <div className="flex items-start gap-4">
                <span className="text-zinc-500 mt-1 text-xl">✦</span>
                <p><strong className="text-zinc-300 font-semibold">Empirical Weights:</strong> V2 hardcodes an economy derived from machine learning data variance (e.g., Base=1800, Pressure=300).</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 5. STATS SUMMARY */}
      <section className="py-24 md:py-32 px-4 md:px-8 relative mt-16 bg-[#050505] border-y border-zinc-800">
        <div className="max-w-5xl mx-auto text-center mb-16 md:mb-24">
          <h2 className="text-4xl md:text-6xl font-bold tracking-tighter mb-6 leading-tight text-white">Z-Score Analytics, <br /> Uncapped Performance Tracking.</h2>
        </div>

        <div className="max-w-5xl mx-auto flex flex-col md:flex-row rounded-sm overflow-hidden shadow-2xl relative z-10">
          <div className="bg-[#b39170] text-white py-20 px-8 flex-1 flex flex-col items-center justify-center transition-colors hover:bg-[#a68461]">
            <span className="text-7xl font-bold mb-4">14</span>
            <span className="text-xs tracking-[0.2em] uppercase font-bold opacity-90">Seasons</span>
          </div>
          <div className="bg-[#c2a486] text-white py-20 px-8 flex-1 flex flex-col items-center justify-center transition-colors hover:bg-[#b59577]">
            <span className="text-7xl font-bold mb-4">300+</span>
            <span className="text-xs tracking-[0.2em] uppercase font-bold opacity-90">Players</span>
          </div>
          <div className="bg-[#d2b89d] text-white py-20 px-8 flex-1 flex flex-col items-center justify-center transition-colors hover:bg-[#c7aa8d]">
            <span className="text-7xl font-bold mb-4">100%</span>
            <span className="text-xs tracking-[0.2em] uppercase font-bold opacity-90">Context Mapped</span>
          </div>
        </div>
      </section>

      {/* 6. INTERACTIVE DATA EXPLORER */}
      <section id="leaderboards" className="pt-32 md:pt-40 pb-20 px-0 md:px-8 bg-[#0a0a0a]">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-8 md:mb-12 gap-8 px-4 md:px-0">
            <div>
              <h2 className="text-4xl md:text-5xl font-bold tracking-tighter mb-4 text-white">Best IPL Seasons Of All Time</h2>
              <p className="text-zinc-400 text-lg md:text-xl font-light">Explore the ApexScore architecture.</p>
            </div>

            <div className="flex flex-col md:flex-row flex-wrap gap-4 bg-zinc-900 border border-zinc-800 p-4 rounded-sm w-full md:w-auto">
              <input
                type="text"
                placeholder="Search Player..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full md:w-48 px-4 py-3 bg-zinc-950 border border-zinc-800 rounded-sm focus:outline-none focus:border-[#b39170] transition-colors text-sm text-zinc-200"
              />
              <select
                value={teamFilter}
                onChange={(e) => setTeamFilter(e.target.value)}
                className="w-full md:w-48 px-4 py-3 bg-zinc-950 border border-zinc-800 rounded-sm focus:outline-none focus:border-[#b39170] transition-colors text-sm text-zinc-200 appearance-none"
              >
                <option value="All">All Teams</option>
                {uniqueTeams.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
              <select
                value={seasonFilter}
                onChange={(e) => setSeasonFilter(e.target.value)}
                className="w-full md:w-48 px-4 py-3 bg-zinc-950 border border-zinc-800 rounded-sm focus:outline-none focus:border-[#b39170] transition-colors text-sm text-zinc-200 appearance-none"
              >
                <option value="All">All Seasons</option>
                {uniqueSeasons.map(s => <option key={s} value={String(s)}>{formatSeason(s)}</option>)}
              </select>
              {(search !== "" || teamFilter !== "All" || seasonFilter !== "All") && (
                <button
                  onClick={() => {
                    setSearch("");
                    setTeamFilter("All");
                    setSeasonFilter("All");
                  }}
                  className="w-full md:w-auto px-4 py-3 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-sm font-bold tracking-widest uppercase transition-colors rounded-sm"
                >
                  Reset
                </button>
              )}
              <div className="grid grid-cols-2 gap-1 p-1 bg-zinc-900 border border-zinc-800 rounded-sm w-full md:w-auto md:flex">
                <button
                  onClick={() => { setEngine('quwrof_v11'); setSortKey(null); }}
                  className={`flex items-center justify-center px-2 md:px-5 py-2 text-[10px] md:text-xs font-bold tracking-widest uppercase transition-colors rounded-sm ${engine === 'quwrof_v11' ? 'bg-[#b39170] text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800'}`}
                >
                  <span className="hidden md:inline">Contextual Percentile</span>
                  <span className="inline md:hidden">Contextual Pct</span>
                </button>
                <button
                  onClick={() => { setEngine('quwrof_v14'); setSortKey(null); }}
                  className={`flex items-center justify-center px-2 md:px-5 py-2 text-[10px] md:text-xs font-bold tracking-widest uppercase transition-colors rounded-sm ${engine === 'quwrof_v14' ? 'bg-[#b39170] text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800'}`}
                >
                  <span className="hidden md:inline">Apex Score</span>
                  <span className="inline md:hidden">Apex Score</span>
                </button>
              </div>
              <select
                value={sortKey || engine}
                onChange={(e) => {
                  setSortKey(e.target.value as keyof PlayerSeason);
                  setSortDirection('desc');
                }}
                className="w-full md:w-56 px-4 py-3 bg-zinc-950 border border-[#b39170] rounded-sm focus:outline-none focus:border-[#b39170] transition-colors text-sm font-semibold text-[#b39170] appearance-none"
              >
                <option value={engine}>Sort: {engineNames[engine as keyof typeof engineNames]}</option>
                <option value="impact_per_match">Sort: Impact/Match</option>
                {engine === 'quwrof_v11' && (
                  <>
                    <option value="bat_percentile">Sort: Bat Pct</option>
                    <option value="bowl_percentile">Sort: Bowl Pct</option>
                  </>
                )}
                {engine === 'quwrof_v14' && (
                  <>
                    <option value="v14_percentile">Sort: Overall Pct</option>
                    <option value="bat_points">Sort: Bat Pts</option>
                    <option value="v14_bat_percentile">Sort: Bat Pct (V14)</option>
                    <option value="bowl_points">Sort: Bowl Pts</option>
                    <option value="v14_bowl_percentile">Sort: Bowl Pct (V14)</option>
                  </>
                )}
                <optgroup label="Batting Metrics">
                  {Object.entries(v11MetricNames).filter(([k]) => k.includes('bat') || k === 'rae').map(([k, label]) => (
                    <option key={k} value={k}>Sort: {label}</option>
                  ))}
                </optgroup>
                <optgroup label="Bowling Metrics">
                  {Object.entries(v11MetricNames).filter(([k]) => !k.includes('bat') && k !== 'rae').map(([k, label]) => (
                    <option key={k} value={k}>Sort: {label}</option>
                  ))}
                </optgroup>
              </select>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse whitespace-nowrap">
              <thead>
                <tr className="border-b border-zinc-800">
                  <th className="px-2 md:px-6 py-5 text-[10px] font-bold text-zinc-400 uppercase tracking-widest sticky left-0 z-10 bg-[#0a0a0a]">Rank</th>
                  <th className="w-full px-2 md:px-6 py-5 text-[10px] font-bold text-zinc-400 uppercase tracking-widest sticky left-[36px] md:left-[60px] z-10 bg-[#0a0a0a]">Player</th>
                  <th className="hidden md:table-cell px-4 py-5 text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Season</th>
                  {renderSortableHeader(
                    <><span className="hidden md:inline">{engineNames[engine as keyof typeof engineNames]}</span><span className="inline md:hidden">{engine === 'quwrof_v14' ? 'Apex Score' : 'Percentile'}</span></>,
                    engine as keyof PlayerSeason
                  )}
                  {(!sortKey || sortKey === engine || sortKey === 'impact_per_match') && (
                    <th className="hidden md:table-cell px-4 py-5 text-[10px] font-bold text-zinc-500 uppercase tracking-widest group cursor-pointer hover:text-white transition-colors" onClick={() => { setSortKey('impact_per_match' as keyof PlayerSeason); setSortDirection(sortKey === 'impact_per_match' && sortDirection === 'desc' ? 'asc' : 'desc'); }}>
                      Impact/Match <InfoTooltip text="Season Score divided by total matches played in that season" /> {sortKey === 'impact_per_match' && (sortDirection === 'desc' ? '↓' : '↑')}
                    </th>
                  )}
                  {engine === 'quwrof_v11' && (
                    <>
                      <th className="hidden md:table-cell px-4 py-5 text-[10px] font-bold text-zinc-500 uppercase tracking-widest group cursor-pointer hover:text-white transition-colors" onClick={() => { setSortKey('bat_percentile'); setSortDirection(sortKey === 'bat_percentile' && sortDirection === 'desc' ? 'asc' : 'desc'); }}>
                        Bat Pct <InfoTooltip text={metricDescriptions['bat_percentile']} /> {sortKey === 'bat_percentile' && (sortDirection === 'desc' ? '↓' : '↑')}
                      </th>
                      <th className="hidden md:table-cell px-4 py-5 text-[10px] font-bold text-zinc-500 uppercase tracking-widest group cursor-pointer hover:text-white transition-colors" onClick={() => { setSortKey('bowl_percentile'); setSortDirection(sortKey === 'bowl_percentile' && sortDirection === 'desc' ? 'asc' : 'desc'); }}>
                        Bowl Pct <InfoTooltip text={metricDescriptions['bowl_percentile']} /> {sortKey === 'bowl_percentile' && (sortDirection === 'desc' ? '↓' : '↑')}
                      </th>
                    </>
                  )}
                  {engine === 'quwrof_v14' && (
                    <>
                      <th className="hidden md:table-cell px-4 py-5 text-[10px] font-bold text-zinc-500 uppercase tracking-widest group cursor-pointer hover:text-white transition-colors" onClick={() => { setSortKey('v14_percentile'); setSortDirection(sortKey === 'v14_percentile' && sortDirection === 'desc' ? 'asc' : 'desc'); }}>
                        Overall Pct <InfoTooltip text={metricDescriptions['v14_percentile']} /> {sortKey === 'v14_percentile' && (sortDirection === 'desc' ? '↓' : '↑')}
                      </th>
                      <th className="hidden md:table-cell px-4 py-5 text-[10px] font-bold text-zinc-500 uppercase tracking-widest group cursor-pointer hover:text-white transition-colors" onClick={() => { setSortKey('bat_points'); setSortDirection(sortKey === 'bat_points' && sortDirection === 'desc' ? 'asc' : 'desc'); }}>
                        Bat Pts <InfoTooltip text={metricDescriptions['bat_points']} /> {sortKey === 'bat_points' && (sortDirection === 'desc' ? '↓' : '↑')}
                      </th>
                      <th className="hidden md:table-cell px-4 py-5 text-[10px] font-bold text-zinc-500 uppercase tracking-widest group cursor-pointer hover:text-white transition-colors" onClick={() => { setSortKey('v14_bat_percentile'); setSortDirection(sortKey === 'v14_bat_percentile' && sortDirection === 'desc' ? 'asc' : 'desc'); }}>
                        Bat Pct <InfoTooltip text={metricDescriptions['v14_bat_percentile']} /> {sortKey === 'v14_bat_percentile' && (sortDirection === 'desc' ? '↓' : '↑')}
                      </th>
                      <th className="hidden md:table-cell px-4 py-5 text-[10px] font-bold text-zinc-500 uppercase tracking-widest group cursor-pointer hover:text-white transition-colors" onClick={() => { setSortKey('bowl_points'); setSortDirection(sortKey === 'bowl_points' && sortDirection === 'desc' ? 'asc' : 'desc'); }}>
                        Bowl Pts <InfoTooltip text={metricDescriptions['bowl_points']} /> {sortKey === 'bowl_points' && (sortDirection === 'desc' ? '↓' : '↑')}
                      </th>
                      <th className="hidden md:table-cell px-4 py-5 text-[10px] font-bold text-zinc-500 uppercase tracking-widest group cursor-pointer hover:text-white transition-colors" onClick={() => { setSortKey('v14_bowl_percentile'); setSortDirection(sortKey === 'v14_bowl_percentile' && sortDirection === 'desc' ? 'asc' : 'desc'); }}>
                        Bowl Pct <InfoTooltip text={metricDescriptions['v14_bowl_percentile']} /> {sortKey === 'v14_bowl_percentile' && (sortDirection === 'desc' ? '↓' : '↑')}
                      </th>
                    </>
                  )}
                  {sortKey && sortKey !== engine && sortKey !== 'impact_per_match' && sortKey !== 'bat_percentile' && sortKey !== 'bowl_percentile' && sortKey !== 'bat_points' && sortKey !== 'bowl_points' && sortKey !== 'v14_percentile' && sortKey !== 'v14_bat_percentile' && sortKey !== 'v14_bowl_percentile' && v11MetricNames[sortKey] && (
                    <th className="hidden md:table-cell px-4 py-5 text-[10px] font-bold text-[#b39170] uppercase tracking-widest group cursor-pointer hover:text-white transition-colors" onClick={() => { setSortKey(sortKey as keyof PlayerSeason); setSortDirection(sortDirection === 'desc' ? 'asc' : 'desc'); }}>{v11MetricNames[sortKey]} {sortDirection === 'desc' ? '↓' : '↑'}</th>
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/50">
                {filteredData.slice((mainTablePage - 1) * 20, mainTablePage * 20).map((row, i) => {
                  const tColor = getTeamColor(row.primary_team);
                  const rank = metricRanks[engine as string]?.get(`${row.player_name}-${row.season}-${row.primary_team}`) || 0;

                  return (
                    <tr
                      key={i}
                      className="hover:bg-[var(--hover-bg)] cursor-pointer transition-colors group"
                      style={{ '--hover-bg': `${tColor}1A` } as React.CSSProperties}
                      onClick={() => setSelectedPlayer(row)}
                    >
                      <td className="px-2 md:px-6 py-4 sticky left-0 bg-[#0a0a0a] group-hover:bg-[var(--hover-bg)] transition-colors relative z-10 border-b border-zinc-800/50">
                        <div className="text-xs font-bold text-zinc-500 tabular-nums">#{rank || i + 1}</div>
                      </td>
                      <td className="w-full px-2 md:px-6 py-4 sticky left-[36px] md:left-[60px] bg-[#0a0a0a] group-hover:bg-[var(--hover-bg)] transition-colors relative z-10 border-b border-zinc-800/50">
                        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-3/4 opacity-70" style={{ backgroundColor: tColor }}></div>
                        <div className="flex flex-col ml-1 md:ml-3 gap-0.5 md:gap-1 max-w-[130px] sm:max-w-[200px] md:max-w-none">
                          <span className="font-semibold text-zinc-200 text-[13px] md:text-[15px] tracking-tight leading-none truncate">
                            {row.player_name} <span className="inline md:hidden text-zinc-500">'{formatSeason(row.season).slice(-2)}</span>
                          </span>
                          <span className="text-[9px] font-bold tracking-wider text-zinc-500 uppercase leading-none truncate">{row.primary_team}</span>
                        </div>
                      </td>
                      <td className="hidden md:table-cell px-4 py-4 text-sm text-zinc-400 tabular-nums border-b border-zinc-800/50">{formatSeason(row.season)}</td>
                      <td className={`px-2 md:px-4 py-4 text-right md:text-left tabular-nums transition-colors border-b border-zinc-800/50 ${(!sortKey || sortKey === engine) ? 'bg-[#b39170]/10' : ''}`}>
                        <div className="flex flex-col items-end md:items-start justify-center h-full">
                          <div className={`text-sm ${(!sortKey || sortKey === engine) ? 'text-[#b39170] font-black' : 'text-zinc-200 font-bold'}`}>
                            {Number(row[engine as keyof PlayerSeason]).toFixed(2)}
                          </div>
                          {sortKey && sortKey !== engine && (
                            <div className="md:hidden text-[9px] sm:text-[10px] font-black text-[#b39170] mt-0.5 whitespace-nowrap tracking-wide">
                              <span className="opacity-70 font-bold mr-1 uppercase">{allMetricNames[sortKey as string] || sortKey}:</span>
                              {sortKey === 'impact_per_match'
                                ? (row.matches ? (Number(row[engine as keyof PlayerSeason]) / row.matches).toFixed(2) : '-')
                                : (sortKey as string).includes('percentile')
                                  ? `${Number(row[sortKey as keyof PlayerSeason]).toFixed(1)}%`
                                  : Number(row[sortKey as keyof PlayerSeason]).toFixed(2)}
                            </div>
                          )}
                        </div>
                      </td>
                      {(!sortKey || sortKey === engine || sortKey === 'impact_per_match') && (
                        <td className={`hidden md:table-cell px-4 py-4 text-sm tabular-nums transition-colors border-b border-zinc-800/50 ${sortKey === 'impact_per_match' ? 'bg-[#b39170]/10 text-[#b39170] font-bold' : 'text-zinc-400 font-semibold'}`}>
                          {row.matches ? (Number(row[engine as keyof PlayerSeason]) / row.matches).toFixed(2) : '-'}
                        </td>
                      )}
                      {engine === 'quwrof_v11' && (
                        <>
                          <td className={`hidden md:table-cell px-4 py-4 text-sm tabular-nums transition-colors border-b border-zinc-800/50 ${sortKey === 'bat_percentile' ? 'bg-[#b39170]/10 text-[#b39170] font-bold' : 'text-zinc-400 font-semibold'}`}>
                            {Number(row.bat_percentile).toFixed(1)}%
                          </td>
                          <td className={`hidden md:table-cell px-4 py-4 text-sm tabular-nums transition-colors border-b border-zinc-800/50 ${sortKey === 'bowl_percentile' ? 'bg-[#b39170]/10 text-[#b39170] font-bold' : 'text-zinc-400 font-semibold'}`}>
                            {Number(row.bowl_percentile).toFixed(1)}%
                          </td>
                        </>
                      )}
                      {engine === 'quwrof_v14' && (
                        <>
                          <td className={`hidden md:table-cell px-4 py-4 text-sm tabular-nums transition-colors border-b border-zinc-800/50 ${sortKey === 'v14_percentile' ? 'bg-[#b39170]/10 text-[#b39170] font-bold' : 'text-zinc-400 font-semibold'}`}>
                            {Number(row.v14_percentile).toFixed(1)}%
                          </td>
                          <td className={`hidden md:table-cell px-4 py-4 text-sm tabular-nums transition-colors border-b border-zinc-800/50 ${sortKey === 'bat_points' ? 'bg-[#b39170]/10 text-[#b39170] font-bold' : 'text-zinc-400 font-semibold'}`}>
                            {Number(row.bat_points).toFixed(1)}
                          </td>
                          <td className={`hidden md:table-cell px-4 py-4 text-sm tabular-nums transition-colors border-b border-zinc-800/50 ${sortKey === 'v14_bat_percentile' ? 'bg-[#b39170]/10 text-[#b39170] font-bold' : 'text-zinc-400 font-semibold'}`}>
                            {row.bat_points > 0 ? `${Number(row.v14_bat_percentile).toFixed(1)}%` : '-'}
                          </td>
                          <td className={`hidden md:table-cell px-4 py-4 text-sm tabular-nums transition-colors border-b border-zinc-800/50 ${sortKey === 'bowl_points' ? 'bg-[#b39170]/10 text-[#b39170] font-bold' : 'text-zinc-400 font-semibold'}`}>
                            {Number(row.bowl_points).toFixed(1)}
                          </td>
                          <td className={`hidden md:table-cell px-4 py-4 text-sm tabular-nums transition-colors border-b border-zinc-800/50 ${sortKey === 'v14_bowl_percentile' ? 'bg-[#b39170]/10 text-[#b39170] font-bold' : 'text-zinc-400 font-semibold'}`}>
                            {row.bowl_points > 0 ? `${Number(row.v14_bowl_percentile).toFixed(1)}%` : '-'}
                          </td>
                        </>
                      )}
                      {sortKey && sortKey !== engine && sortKey !== 'bat_percentile' && sortKey !== 'bowl_percentile' && sortKey !== 'bat_points' && sortKey !== 'bowl_points' && sortKey !== 'v14_percentile' && sortKey !== 'v14_bat_percentile' && sortKey !== 'v14_bowl_percentile' && v11MetricNames[sortKey] && (
                        <td className="hidden md:table-cell px-4 py-4 text-sm font-black tabular-nums text-[#b39170] bg-[#b39170]/10 transition-colors border-b border-zinc-800/50">
                          {Number(row[sortKey as keyof PlayerSeason]).toFixed(2)}
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
            {filteredData.length === 0 && (
              <div className="py-24 text-center text-zinc-400 font-light text-lg">
                No players found matching your criteria.
              </div>
            )}
            {filteredData.length > 20 && (
              <div className="flex justify-center items-center gap-4 py-8 border-t border-zinc-200">
                <button
                  onClick={() => setMainTablePage(p => Math.max(1, p - 1))}
                  disabled={mainTablePage === 1}
                  className="px-6 py-2 border border-zinc-300 rounded-sm text-sm font-semibold text-zinc-600 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-zinc-50 transition-colors"
                >
                  Previous
                </button>
                <span className="text-sm font-semibold text-zinc-400">
                  Page {mainTablePage} of {Math.ceil(filteredData.length / 20)}
                </span>
                <button
                  onClick={() => setMainTablePage(p => p + 1)}
                  disabled={mainTablePage * 20 >= filteredData.length}
                  className="px-6 py-2 border border-zinc-300 rounded-sm text-sm font-semibold text-zinc-600 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-zinc-50 transition-colors"
                >
                  Next
                </button>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* 6.5. ELITE ALL-ROUNDERS */}
      {eliteAllRounders.length > 0 && (
        <section className="py-32 px-8 bg-zinc-950 text-white relative overflow-hidden">
          <div className="absolute inset-0 opacity-10 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-[#b39170] via-zinc-950 to-zinc-950"></div>
          <div className="max-w-7xl mx-auto relative z-10">
            <div className="mb-16 flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
              <div>
                <h2 className="text-4xl md:text-5xl font-bold tracking-tighter mb-4 text-white">Elite All-Rounders</h2>
                <p className="text-zinc-400 text-xl font-light">The rarest tier of performance. Players above the 60th percentile in both batting and bowling.</p>
              </div>
              <div className="flex bg-zinc-900 p-1 rounded-sm border border-zinc-800">
                <button onClick={() => setAllRounderEngine('quwrof_v11')} className={`px-4 py-2 text-xs font-bold uppercase tracking-widest rounded-sm transition-colors ${allRounderEngine === 'quwrof_v11' ? 'bg-[#b39170] text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-300'}`}>Contextual Pct</button>
                <button onClick={() => setAllRounderEngine('quwrof_v14')} className={`px-4 py-2 text-xs font-bold uppercase tracking-widest rounded-sm transition-colors ${allRounderEngine === 'quwrof_v14' ? 'bg-[#b39170] text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-300'}`}>Apex Score</button>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse whitespace-nowrap">
                <thead>
                  <tr className="border-b border-zinc-800">
                    <th className="px-2 md:px-6 py-4 text-[10px] font-black tracking-[0.2em] uppercase text-zinc-500">Rank</th>
                    <th className="w-full px-2 md:px-4 py-4 text-[10px] font-black tracking-[0.2em] uppercase text-zinc-500 text-left">Player</th>
                    <th className="hidden md:table-cell px-4 py-4 text-[10px] font-black tracking-[0.2em] uppercase text-zinc-500">Season</th>
                    <th className="px-2 md:px-4 py-4 text-[10px] font-black tracking-[0.2em] uppercase text-[#b39170] text-right md:text-left">{allRounderEngine === 'quwrof_v11' ? 'Contextual Pct' : 'Apex Score'}</th>
                    <th className="hidden md:table-cell px-4 py-4 text-[10px] font-black tracking-[0.2em] uppercase text-zinc-500">Batting Pct</th>
                    <th className="hidden md:table-cell px-4 py-4 text-[10px] font-black tracking-[0.2em] uppercase text-zinc-500">Bowling Pct</th>
                  </tr>
                </thead>
                <tbody>
                  {eliteAllRounders.slice((allRoundersPage - 1) * 20, allRoundersPage * 20).map((row, i) => {
                    const tColor = getTeamColor(row.primary_team);
                    return (
                      <tr
                        key={i}
                        className="border-b border-zinc-800/50 hover:bg-[var(--hover-bg)] transition-colors cursor-pointer group"
                        style={{ '--hover-bg': `${tColor}1A` } as React.CSSProperties}
                        onClick={() => setSelectedPlayer(row)}
                      >
                        <td className="px-2 md:px-6 py-4 text-xs font-black text-zinc-500 tabular-nums">
                          #{(allRoundersPage - 1) * 20 + i + 1}
                        </td>
                        <td className="w-full px-2 md:px-4 py-4 relative pl-4 md:pl-6">
                          <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-3/4 opacity-70" style={{ backgroundColor: tColor }}></div>
                          <div className="flex flex-col gap-0.5 md:gap-1 max-w-[130px] sm:max-w-[200px] md:max-w-none">
                            <span className="font-semibold text-white text-[13px] md:text-[15px] tracking-tight leading-none truncate">
                              {row.player_name} <span className="inline md:hidden text-zinc-500">'{formatSeason(row.season).slice(-2)}</span>
                            </span>
                            <span className="text-[9px] font-bold tracking-wider text-zinc-500 uppercase leading-none truncate">{row.primary_team}</span>
                          </div>
                        </td>
                        <td className="hidden md:table-cell px-4 py-4 text-sm text-zinc-400 tabular-nums border-b border-zinc-800/50">{formatSeason(row.season)}</td>
                        <td className="px-2 md:px-4 py-4 text-right md:text-left text-sm font-black text-[#b39170] tabular-nums bg-[#b39170]/10 border-b border-zinc-800/50">
                          {Number(row[allRounderEngine]).toFixed(2)}
                        </td>
                        <td className="hidden md:table-cell px-4 py-4">
                          <div className="flex items-center gap-3">
                            <span className="text-sm font-semibold tabular-nums text-white w-12">{Number(allRounderEngine === 'quwrof_v11' ? row.bat_percentile : row.v14_bat_percentile).toFixed(1)}%</span>
                            <div className="h-1.5 w-24 bg-zinc-800 rounded-full overflow-hidden hidden md:block">
                              <div className="h-full bg-white rounded-full opacity-80 group-hover:bg-[#b39170] transition-colors" style={{ width: `${allRounderEngine === 'quwrof_v11' ? row.bat_percentile : row.v14_bat_percentile}%` }}></div>
                            </div>
                          </div>
                        </td>
                        <td className="hidden md:table-cell px-4 py-4">
                          <div className="flex items-center gap-3">
                            <span className="text-sm font-semibold tabular-nums text-white w-12">{Number(allRounderEngine === 'quwrof_v11' ? row.bowl_percentile : row.v14_bowl_percentile).toFixed(1)}%</span>
                            <div className="h-1.5 w-24 bg-zinc-800 rounded-full overflow-hidden hidden md:block">
                              <div className="h-full bg-white rounded-full opacity-80 group-hover:bg-[#b39170] transition-colors" style={{ width: `${allRounderEngine === 'quwrof_v11' ? row.bowl_percentile : row.v14_bowl_percentile}%` }}></div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {eliteAllRounders.length > 20 && (
              <div className="flex justify-center items-center gap-4 mt-8 pt-8 border-t border-zinc-800">
                <button
                  onClick={() => setAllRoundersPage(p => Math.max(1, p - 1))}
                  disabled={allRoundersPage === 1}
                  className="px-6 py-2 border border-zinc-700 rounded-sm text-sm font-semibold text-zinc-400 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-zinc-800 transition-colors"
                >
                  Previous
                </button>
                <span className="text-sm font-semibold text-zinc-500">
                  Page {allRoundersPage} of {Math.ceil(eliteAllRounders.length / 20)}
                </span>
                <button
                  onClick={() => setAllRoundersPage(p => p + 1)}
                  disabled={allRoundersPage * 20 >= eliteAllRounders.length}
                  className="px-6 py-2 border border-zinc-700 rounded-sm text-sm font-semibold text-zinc-400 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-zinc-800 transition-colors"
                >
                  Next
                </button>
              </div>
            )}
          </div>
        </section>
      )}

      {/* 6.6. PLAYOFF PERFORMERS */}
      {playoffLegends.length > 0 && (
        <section className="py-24 md:py-32 px-0 md:px-8 bg-zinc-950 text-white relative overflow-hidden">
          <div className="absolute inset-0 opacity-15 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-amber-900 via-zinc-950 to-zinc-950"></div>
          <div className="max-w-7xl mx-auto relative z-10">
            <div className="mb-8 md:mb-16 flex flex-col md:flex-row justify-between items-start md:items-end gap-6 px-4 md:px-0">
              <div>
                <h2 className="text-4xl md:text-5xl font-bold tracking-tighter mb-4 text-white">Playoff Performers</h2>
                <p className="text-zinc-400 text-xl font-light">The ultimate clutch performers. Ranked by equal-weighted Playoff Impact for both batting and bowling.</p>
              </div>
              <div className="flex bg-zinc-900 p-1 rounded-sm border border-zinc-800">
                <button onClick={() => setPlayoffEngine('quwrof_v11')} className={`px-4 py-2 text-xs font-bold uppercase tracking-widest rounded-sm transition-colors ${playoffEngine === 'quwrof_v11' ? 'bg-[#b39170] text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-300'}`}>Contextual Pct</button>
                <button onClick={() => setPlayoffEngine('quwrof_v14')} className={`px-4 py-2 text-xs font-bold uppercase tracking-widest rounded-sm transition-colors ${playoffEngine === 'quwrof_v14' ? 'bg-[#b39170] text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-300'}`}>Apex Score</button>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse whitespace-nowrap">
                <thead>
                  <tr className="border-b border-zinc-800">
                    <th className="px-2 md:px-6 py-4 text-[10px] font-black tracking-[0.2em] uppercase text-zinc-500">Rank</th>
                    <th className="w-full px-2 md:px-4 py-4 text-[10px] font-black tracking-[0.2em] uppercase text-zinc-500 text-left">Player</th>
                    <th className="hidden md:table-cell px-4 py-4 text-[10px] font-black tracking-[0.2em] uppercase text-zinc-500">Season</th>
                    <th className="px-2 md:px-4 py-4 text-[10px] font-black tracking-[0.2em] uppercase text-amber-500 text-right md:text-left">{playoffEngine === 'quwrof_v11' ? 'Clutch Score' : 'Playoff Total'}</th>
                    <th className="hidden md:table-cell px-4 py-4 text-[10px] font-black tracking-[0.2em] uppercase text-zinc-500">{playoffEngine === 'quwrof_v11' ? 'Contextual Pct' : 'Apex Score'}</th>
                    <th className="hidden md:table-cell px-4 py-4 text-[10px] font-black tracking-[0.2em] uppercase text-zinc-500">{playoffEngine === 'quwrof_v11' ? 'Bat Playoff' : 'Bat Playoff Pts'}</th>
                    <th className="hidden md:table-cell px-4 py-4 text-[10px] font-black tracking-[0.2em] uppercase text-zinc-500">{playoffEngine === 'quwrof_v11' ? 'Bowl Playoff' : 'Bowl Playoff Pts'}</th>
                  </tr>
                </thead>
                <tbody>
                  {playoffLegends.slice((playoffPage - 1) * 20, playoffPage * 20).map((row: any, i: number) => {
                    const tColor = getTeamColor(row.primary_team);
                    return (
                      <tr
                        key={i}
                        className="border-b border-zinc-800/50 hover:bg-[var(--hover-bg)] transition-colors cursor-pointer group"
                        style={{ '--hover-bg': `${tColor}1A` } as React.CSSProperties}
                        onClick={() => setSelectedPlayer(row)}
                      >
                        <td className="px-2 md:px-6 py-4 text-xs font-black text-zinc-500 tabular-nums">
                          #{(playoffPage - 1) * 20 + i + 1}
                        </td>
                        <td className="w-full px-2 md:px-4 py-4 relative pl-4 md:pl-6">
                          <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-3/4 opacity-70" style={{ backgroundColor: tColor }}></div>
                          <div className="flex flex-col gap-0.5 md:gap-1 max-w-[130px] sm:max-w-[200px] md:max-w-none">
                            <span className="font-semibold text-white text-[13px] md:text-[15px] tracking-tight leading-none truncate">
                              {row.player_name} <span className="inline md:hidden text-zinc-500">'{formatSeason(row.season).slice(-2)}</span>
                            </span>
                            <span className="text-[9px] font-bold tracking-wider text-zinc-500 uppercase leading-none truncate">{row.primary_team}</span>
                          </div>
                        </td>
                        <td className="hidden md:table-cell px-4 py-4 text-sm text-zinc-400 tabular-nums border-b border-zinc-800/50">{formatSeason(row.season)}</td>
                        <td className="px-2 md:px-4 py-4 text-right md:text-left text-sm font-black text-amber-500 tabular-nums bg-amber-500/10 border-b border-zinc-800/50">
                          {Number(row.clutchScore).toFixed(1)}
                        </td>
                        <td className="hidden md:table-cell px-4 py-4 text-sm font-black text-zinc-300 tabular-nums">
                          {Number(row[playoffEngine]).toFixed(1)}
                        </td>
                        <td className="hidden md:table-cell px-4 py-4 text-sm text-zinc-400 tabular-nums">
                          {Number(row.batPlayoff).toFixed(1)}
                        </td>
                        <td className="hidden md:table-cell px-4 py-4 text-sm text-zinc-400 tabular-nums">
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

      {/* 7. COMPARISON DASHBOARD */}
      <section id="compare" className="py-24 md:py-32 px-0 md:px-8 bg-[#0a0a0a] border-t border-zinc-800">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col lg:flex-row justify-between items-start lg:items-end mb-16 gap-8 px-4 md:px-0">
            <div>
              <div className="flex flex-col md:flex-row md:items-center gap-4 md:gap-6 mb-4">
                <h2 className="text-4xl md:text-5xl font-bold tracking-tighter text-white">Player Comparison</h2>
                <div className="flex bg-zinc-900 p-1 rounded-sm border border-zinc-800 self-start">
                  <button onClick={() => setCompareEngine('quwrof_v11')} className={`px-4 py-2 text-xs font-bold uppercase tracking-widest rounded-sm transition-colors ${compareEngine === 'quwrof_v11' ? 'bg-[#b39170] text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-300'}`}>Contextual Pct</button>
                  <button onClick={() => setCompareEngine('quwrof_v14')} className={`px-4 py-2 text-xs font-bold uppercase tracking-widest rounded-sm transition-colors ${compareEngine === 'quwrof_v14' ? 'bg-[#b39170] text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-300'}`}>Apex Score</button>
                </div>
              </div>
              <p className="text-zinc-400 text-xl font-light">Add up to 6 players to compare metrics side-by-side.</p>
            </div>

            <div className="w-full lg:w-[400px] relative">
              <div className="flex items-center border-b border-zinc-800 focus-within:border-[#b39170] transition-colors pb-2">
                <span className="text-zinc-500 mr-3">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" /></svg>
                </span>
                <input
                  type="text"
                  placeholder="Search player to add..."
                  value={compareSearch}
                  onChange={(e) => setCompareSearch(e.target.value)}
                  disabled={comparedPlayers.length >= 6}
                  className="flex-1 bg-transparent border-none focus:outline-none text-lg placeholder-zinc-600 text-zinc-200 disabled:opacity-50"
                />
              </div>

              {compareSuggestions.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-4 bg-[#111] rounded-sm shadow-xl z-20 border border-zinc-800 overflow-hidden">
                  {compareSuggestions.map((s, i) => (
                    <div
                      key={i}
                      className="px-6 py-4 border-b border-zinc-800/50 hover:bg-zinc-900/50 cursor-pointer flex justify-between items-center transition-colors group"
                      onClick={() => handleAddComparePlayer(s)}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: getTeamColor(s.primary_team) }}></div>
                        <span className="font-semibold text-zinc-200 group-hover:text-[#b39170] transition-colors">{s.player_name}</span>
                      </div>
                      <div className="flex items-center gap-4 text-[10px] font-bold text-zinc-500 tracking-wider uppercase">
                        <span>{s.primary_team}</span>
                        <span>{formatSeason(s.season)}</span>
                        <span className="text-[#b39170] opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                          Add <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5v14" /></svg>
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {comparedPlayers.length > 0 ? (
            <div className="bg-zinc-950 p-4 md:p-12 shadow-sm border-y md:border border-zinc-800 rounded-none md:rounded-sm">
              {/* Selected Players Header */}
              <div className="flex justify-between items-start md:items-center mb-8 md:mb-12 border-b border-zinc-800/50 pb-8 flex-col md:flex-row gap-6">
                <div className="flex gap-4 md:gap-8 flex-wrap">
                  {comparedPlayers.map((p, idx) => (
                    <div key={idx} className="flex flex-col relative group">
                      <div className="flex items-center gap-2 mb-1">
                        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: getTeamColor(p.primary_team) }}></div>
                        <span className="font-bold text-xl tracking-tight text-white">{p.player_name} <span className="text-zinc-500 font-medium text-lg ml-1">'{formatSeason(p.season).slice(-2)}</span></span>
                      </div>
                      <span className="text-[10px] font-bold text-zinc-500 tracking-wider uppercase">{p.primary_team}</span>

                      <button
                        onClick={() => setComparedPlayers(prev => prev.filter((_, i) => i !== idx))}
                        className="absolute -top-3 -right-6 w-6 h-6 flex items-center justify-center bg-zinc-900 text-zinc-500 hover:bg-red-900/30 hover:text-red-400 rounded-full transition-colors opacity-0 group-hover:opacity-100 shadow-sm"
                      >
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6L6 18M6 6l12 12" /></svg>
                      </button>
                    </div>
                  ))}
                </div>
                <button
                  onClick={() => setComparedPlayers([])}
                  className="text-xs font-bold tracking-widest uppercase text-zinc-400 hover:text-red-500 transition-colors"
                >
                  Clear All
                </button>
              </div>

              <div className="flex justify-between items-end mb-8 border-b border-zinc-800/50 pb-4 mt-8">
                <h3 className="text-xl font-bold text-white tracking-tight">Metrics Breakdown</h3>
                <div className="flex bg-zinc-900 p-1 rounded-md border border-zinc-800">
                  <button onClick={() => setComparisonTab('all')} className={`px-4 py-1.5 text-[10px] font-bold uppercase tracking-widest rounded transition-colors ${comparisonTab === 'all' ? 'bg-[#b39170] shadow-sm text-white' : 'text-zinc-500 hover:text-zinc-300'}`}>All</button>
                  <button onClick={() => setComparisonTab('batting')} className={`px-4 py-1.5 text-[10px] font-bold uppercase tracking-widest rounded transition-colors ${comparisonTab === 'batting' ? 'bg-[#b39170] shadow-sm text-white' : 'text-zinc-500 hover:text-zinc-300'}`}>Batting</button>
                  <button onClick={() => setComparisonTab('bowling')} className={`px-4 py-1.5 text-[10px] font-bold uppercase tracking-widest rounded transition-colors ${comparisonTab === 'bowling' ? 'bg-[#b39170] shadow-sm text-white' : 'text-zinc-500 hover:text-zinc-300'}`}>Bowling</button>
                </div>
              </div>

              {/* Radar Chart */}
              {chartData.length > 0 && (
                <div className="w-full h-[300px] md:h-[450px] mb-12 bg-[#0a0a0a] border border-zinc-800 rounded-sm p-0 md:p-4 relative">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart cx="50%" cy="50%" outerRadius="60%" data={chartData}>
                      <PolarGrid stroke="#27272a" />
                      <PolarAngleAxis dataKey="subject" tick={{ fill: '#71717a', fontSize: 10, fontWeight: 700 }} />
                      <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend wrapperStyle={{ fontSize: '12px', fontWeight: 600, paddingTop: '20px' }} />
                      {comparedPlayers.map((p, idx) => {
                        const pKey = `${p.player_name} ${formatSeason(p.season)}`;
                        return (
                          <Radar
                            key={idx}
                            name={pKey}
                            dataKey={pKey}
                            stroke={CHART_COLORS[idx % CHART_COLORS.length]}
                            fill={CHART_COLORS[idx % CHART_COLORS.length]}
                            fillOpacity={0.15}
                            strokeWidth={2}
                          />
                        );
                      })}
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* Metric Breakdown Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-16 gap-y-12">
                {['quwrof_v11', 'quwrof_v14', 'impact_per_match', 'bat_percentile', 'bowl_percentile', 'bat_points', 'bowl_points', ...Object.keys(v11MetricNames)].map((key) => {
                  if (comparisonTab !== 'all') {
                    if (key === 'quwrof_v11' || key === 'quwrof_v14' || key === 'impact_per_match') return null;
                    const isBattingMetric = key.includes('bat') || key === 'rae';
                    if (comparisonTab === 'batting' && !isBattingMetric) return null;
                    if (comparisonTab === 'bowling' && isBattingMetric) return null;
                  }

                  // Hide engine-specific metrics if that engine isn't selected
                  if (compareEngine === 'quwrof_v11' && (key === 'quwrof_v14' || key === 'bat_points' || key === 'bowl_points' || key === 'v14_percentile' || key === 'v14_bat_percentile' || key === 'v14_bowl_percentile')) return null;
                  if (compareEngine === 'quwrof_v14' && (key === 'quwrof_v11' || key === 'bat_percentile' || key === 'bowl_percentile')) return null;

                  const stats = comparisonStats?.[key];
                  if (!stats) return null;

                  const bestVal = Math.max(...stats.map(s => s.percentile));
                  const label = key === compareEngine ? engineNames[compareEngine as keyof typeof engineNames] : (key === 'impact_per_match' ? 'Impact/Match' : (key === 'bat_percentile' ? 'Batting Pct' : (key === 'bowl_percentile' ? 'Bowling Pct' : (key === 'bat_points' ? 'Batting Pts' : (key === 'bowl_points' ? 'Bowling Pts' : v11MetricNames[key])))));

                  return (
                    <div key={key} className="flex flex-col">
                      <div className="flex items-center gap-2 mb-6">
                        <div className="text-[10px] font-bold text-zinc-400 tracking-widest uppercase truncate">
                          {label}
                        </div>
                        <InfoTooltip text={metricDescriptions[key]} />
                      </div>

                      <div className="flex flex-col gap-5">
                        {comparedPlayers
                          .map((player, idx) => ({ player, stat: stats[idx], originalIdx: idx }))
                          .sort((a, b) => b.stat.val - a.stat.val)
                          .map(({ player, stat, originalIdx }) => {
                            const isBest = stat.percentile === bestVal && comparedPlayers.length > 1;
                            const pColor = getTeamColor(player.primary_team);

                            return (
                              <div key={originalIdx} className="flex flex-col gap-2">
                                <div className="flex justify-between items-end">
                                  <span className={`text-sm font-semibold flex items-baseline gap-1.5 ${isBest ? 'text-zinc-200' : 'text-zinc-500'}`}>
                                    <span>{player.player_name.split(' ')[0][0]}. {player.player_name.split(' ').slice(1).join(' ') || player.player_name}</span>
                                    <span className={`text-[10px] font-bold ${isBest ? 'text-zinc-400' : 'text-zinc-600'}`}>'{formatSeason(player.season).slice(-2)}</span>
                                  </span>
                                  <span className={`text-sm font-bold tabular-nums ${isBest ? 'text-zinc-200' : 'text-zinc-500'}`}>
                                    {stat.val > 0 && stat.val < 1 ? stat.val.toFixed(3) : stat.val.toFixed(2)}
                                  </span>
                                </div>
                                <div className="w-full h-1 bg-zinc-900 rounded-full overflow-hidden">
                                  <div
                                    className="h-full transition-all duration-700 ease-out rounded-full"
                                    style={{
                                      width: `${stat.percentile}%`,
                                      backgroundColor: isBest || comparedPlayers.length === 1 ? pColor : '#3f3f46',
                                    }}
                                  ></div>
                                </div>
                              </div>
                            );
                          })}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="bg-white p-20 shadow-sm border border-zinc-100 rounded-sm text-center flex flex-col items-center justify-center">
              <div className="w-20 h-20 bg-[#f5f3f0] rounded-full flex items-center justify-center mb-8 text-[#b39170]">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></svg>
              </div>
              <h3 className="text-3xl font-bold text-zinc-900 mb-3 tracking-tight">No players selected</h3>
              <p className="text-zinc-500 font-light max-w-md text-lg">Use the search bar above to select players and compare their metrics side-by-side.</p>
            </div>
          )}
        </div>
      </section>

      {/* 6.75 SCATTER PLOT */}
      <section className="py-24 md:py-32 px-4 md:px-8 bg-[#0a0a0a] border-t border-zinc-800">
        <div className="max-w-7xl mx-auto">
          <div className="mb-12 flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
            <div>
              <h2 className="text-4xl md:text-5xl font-bold tracking-tighter mb-4 text-white">Scatter Plot Analytics</h2>
              <p className="text-zinc-400 text-xl font-light">Select any two metrics to visually map out the Top 20 performers and find statistical outliers.</p>
            </div>
            <div className="flex bg-zinc-900 p-1 rounded-sm border border-zinc-800">
              <button onClick={() => setScatterEngine('quwrof_v11')} className={`px-4 py-2 text-xs font-bold uppercase tracking-widest rounded-sm transition-colors ${scatterEngine === 'quwrof_v11' ? 'bg-[#b39170] text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-300'}`}>Contextual Pct</button>
              <button onClick={() => setScatterEngine('quwrof_v14')} className={`px-4 py-2 text-xs font-bold uppercase tracking-widest rounded-sm transition-colors ${scatterEngine === 'quwrof_v14' ? 'bg-[#b39170] text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-300'}`}>Apex Score</button>
            </div>
          </div>

          <div className="flex flex-col lg:flex-row gap-6 mb-12">
            <div className="flex-1 flex flex-col md:flex-row gap-6">
              <div className="flex-1">
                <label className="block text-xs font-bold uppercase tracking-widest text-zinc-400 mb-2">X-Axis Metric</label>
                <select
                  value={scatterXMetric as string}
                  onChange={(e) => setScatterXMetric(e.target.value as keyof PlayerSeason)}
                  className="w-full px-4 py-3 bg-zinc-950 border border-zinc-800 rounded-sm focus:outline-none focus:border-[#b39170] transition-colors text-sm font-semibold text-zinc-200 appearance-none"
                >
                  {scatterEngine === 'quwrof_v11' ? (
                    <>
                      <option value="quwrof_v11">Contextual Pct (V1)</option>
                      <option value="bat_percentile">Batting Pct (V1)</option>
                      <option value="bowl_percentile">Bowling Pct (V1)</option>
                      <optgroup label="Basic Stats">
                        {Object.entries(basicMetricNames).map(([k, label]) => (
                          <option key={k} value={k}>{label}</option>
                        ))}
                      </optgroup>
                      <optgroup label="V1 Advanced Metrics">
                        {Object.entries(v11MetricNames).map(([k, label]) => (
                          <option key={k} value={k}>{label}</option>
                        ))}
                      </optgroup>
                    </>
                  ) : (
                    <>
                      <option value="quwrof_v14">Apex Score (V2)</option>
                      <option value="v14_percentile">Overall Pct (V2)</option>
                      <option value="v14_bat_percentile">Batting Pct (V2)</option>
                      <option value="v14_bowl_percentile">Bowling Pct (V2)</option>
                      <optgroup label="Basic Stats">
                        {Object.entries(basicMetricNames).map(([k, label]) => (
                          <option key={k} value={k}>{label}</option>
                        ))}
                      </optgroup>
                      <optgroup label="V2 Advanced Metrics">
                        {Object.entries(v14MetricNames).map(([k, label]) => (
                          <option key={k} value={k}>{label}</option>
                        ))}
                      </optgroup>
                    </>
                  )}
                </select>
              </div>
              <div className="flex-1">
                <label className="block text-xs font-bold uppercase tracking-widest text-zinc-400 mb-2">Y-Axis Metric</label>
                <select
                  value={scatterYMetric as string}
                  onChange={(e) => setScatterYMetric(e.target.value as keyof PlayerSeason)}
                  className="w-full px-4 py-3 bg-zinc-950 border border-zinc-800 rounded-sm focus:outline-none focus:border-[#b39170] transition-colors text-sm font-semibold text-zinc-200 appearance-none"
                >
                  {scatterEngine === 'quwrof_v11' ? (
                    <>
                      <option value="quwrof_v11">Contextual Pct (V1)</option>
                      <option value="bat_percentile">Batting Pct (V1)</option>
                      <option value="bowl_percentile">Bowling Pct (V1)</option>
                      <optgroup label="Basic Stats">
                        {Object.entries(basicMetricNames).map(([k, label]) => (
                          <option key={k} value={k}>{label}</option>
                        ))}
                      </optgroup>
                      <optgroup label="V1 Advanced Metrics">
                        {Object.entries(v11MetricNames).map(([k, label]) => (
                          <option key={k} value={k}>{label}</option>
                        ))}
                      </optgroup>
                    </>
                  ) : (
                    <>
                      <option value="quwrof_v14">Apex Score (V2)</option>
                      <option value="v14_percentile">Overall Pct (V2)</option>
                      <option value="v14_bat_percentile">Batting Pct (V2)</option>
                      <option value="v14_bowl_percentile">Bowling Pct (V2)</option>
                      <optgroup label="Basic Stats">
                        {Object.entries(basicMetricNames).map(([k, label]) => (
                          <option key={k} value={k}>{label}</option>
                        ))}
                      </optgroup>
                      <optgroup label="V2 Advanced Metrics">
                        {Object.entries(v14MetricNames).map(([k, label]) => (
                          <option key={k} value={k}>{label}</option>
                        ))}
                      </optgroup>
                    </>
                  )}
                </select>
              </div>
            </div>

            <div className="flex-1">
              <label className="block text-xs font-bold uppercase tracking-widest text-zinc-400 mb-2">Add Custom Players</label>
              <div className="relative">
                <div className="flex items-center bg-zinc-950 border border-zinc-800 rounded-sm focus-within:border-[#b39170] transition-colors px-4 py-2 h-[46px]">
                  <span className="text-zinc-400 mr-2">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" /></svg>
                  </span>
                  <input
                    type="text"
                    placeholder="Search player..."
                    value={scatterSearch}
                    onChange={(e) => setScatterSearch(e.target.value)}
                    className="flex-1 bg-transparent border-none focus:outline-none text-sm placeholder-zinc-600 text-zinc-200"
                  />
                </div>

                {scatterSuggestions.length > 0 && (
                  <div className="absolute top-full left-0 right-0 mt-2 bg-[#111] rounded-sm shadow-xl z-20 border border-zinc-800 overflow-hidden">
                    {scatterSuggestions.map((s, i) => (
                      <div
                        key={i}
                        className="px-4 py-3 border-b border-zinc-800 hover:bg-zinc-900/50 cursor-pointer flex justify-between items-center transition-colors group"
                        onClick={() => handleAddScatterPlayer(s)}
                      >
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: getTeamColor(s.primary_team) }}></div>
                          <span className="font-semibold text-zinc-200 text-sm group-hover:text-[#b39170] transition-colors">{s.player_name}</span>
                        </div>
                        <span className="text-[10px] font-bold text-zinc-500 tracking-wider uppercase">{s.primary_team} • {formatSeason(s.season)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {scatterCustomPlayers.length > 0 && (
            <div className="flex flex-wrap gap-3 mb-8">
              {scatterCustomPlayers.map((p, idx) => (
                <div key={idx} className="flex items-center gap-2 bg-zinc-900 border border-zinc-800 px-3 py-1.5 rounded-sm shadow-sm group">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: getTeamColor(p.primary_team) }}></div>
                  <span className="text-xs font-bold text-zinc-300">{p.player_name} '{formatSeason(p.season).slice(-2)}</span>
                  <button
                    onClick={() => setScatterCustomPlayers(prev => prev.filter((_, i) => i !== idx))}
                    className="ml-1 text-zinc-400 hover:text-red-500 transition-colors"
                  >
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6L6 18M6 6l12 12" /></svg>
                  </button>
                </div>
              ))}
              <button
                onClick={() => setScatterCustomPlayers([])}
                className="text-xs font-bold text-zinc-400 hover:text-red-500 transition-colors px-2"
              >
                Clear All
              </button>
            </div>
          )}

          <div className="w-full h-[400px] md:h-[600px] bg-zinc-950 border border-zinc-800 rounded-sm p-2 md:p-4 relative shadow-sm">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis type="number" dataKey="xVal" name={allMetricNames[scatterXMetric as string] || scatterXMetric as string} tick={{ fontSize: 12, fill: '#71717a' }} tickLine={false} axisLine={{ stroke: '#3f3f46' }} />
                <YAxis type="number" dataKey="yVal" name={allMetricNames[scatterYMetric as string] || scatterYMetric as string} tick={{ fontSize: 12, fill: '#71717a' }} tickLine={false} axisLine={{ stroke: '#3f3f46' }} />
                <ZAxis type="number" range={[80, 80]} />
                <Tooltip content={<ScatterTooltip />} cursor={{ strokeDasharray: '3 3', stroke: '#52525b' }} />
                <Scatter data={scatterData} fill="#b39170">
                  <LabelList dataKey="nameAndSeason" position="top" offset={10} style={{ fontSize: '10px', fill: '#a1a1aa', fontWeight: 600, pointerEvents: 'none' }} />
                  {scatterData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={getTeamColor(entry.primary_team)} fillOpacity={0.8} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      {/* MODAL Overlay */}
      <AnimatePresence>
        {selectedPlayer && modalStats && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-[100] flex items-center justify-center p-0 md:p-4"
          >
            <div className="absolute inset-0 bg-zinc-900/80 transition-opacity" onClick={() => setSelectedPlayer(null)}></div>
            <AnimatePresence mode="wait" initial={false} custom={slideDirection}>
              <motion.div
                key={`${selectedPlayer.player_name}-${selectedPlayer.season}`}
                custom={slideDirection}
                variants={modalSlideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                onTouchStart={handleTouchStart}
                onTouchEnd={handleTouchEnd}
                className="relative bg-white w-full max-w-5xl h-full md:h-auto max-h-[100vh] md:max-h-[90vh] overflow-y-auto overscroll-contain shadow-2xl flex flex-col rounded-none md:rounded-sm z-[101]"
              >
                {/* Modal Header */}
                <div className="sticky top-0 bg-white border-b border-zinc-100 px-4 md:px-10 py-6 md:py-8 flex flex-col md:flex-row justify-between items-start md:items-center z-40 relative">

                  <div className="absolute top-4 right-4 flex md:hidden items-center gap-1 z-50">
                    <button onClick={handlePrev} disabled={selectedIndex <= 0} className="w-8 h-8 rounded-full flex items-center justify-center bg-zinc-100 hover:bg-zinc-200 text-zinc-600 transition-colors disabled:opacity-30">←</button>
                    <button onClick={handleNext} disabled={selectedIndex < 0 || selectedIndex >= filteredData.length - 1} className="w-8 h-8 rounded-full flex items-center justify-center bg-zinc-100 hover:bg-zinc-200 text-zinc-600 transition-colors disabled:opacity-30">→</button>
                    <button onClick={() => setSelectedPlayer(null)} className="w-8 h-8 rounded-full flex items-center justify-center bg-zinc-200 text-zinc-600 hover:text-red-500 hover:bg-red-50 transition-colors ml-2">✕</button>
                  </div>

                  <div className="flex flex-col relative pl-4 md:pl-6 pr-28 md:pr-0 w-full md:w-auto">
                    <div className="absolute left-0 top-0 bottom-0 w-1 rounded-r-full opacity-60" style={{ backgroundColor: teamColor }}></div>
                    <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold tracking-tighter mb-1 md:mb-2 text-zinc-900 leading-none truncate">
                      {selectedPlayer.player_name}
                    </h2>
                    <div className="text-[9px] md:text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                      {selectedPlayer.primary_team} <span className="mx-1 md:mx-2">•</span> Season {formatSeason(selectedPlayer.season)}
                    </div>
                  </div>

                  <div className="flex items-center justify-between w-full md:w-auto mt-6 md:mt-0">
                    <div className="flex items-center justify-between md:justify-end gap-2 md:gap-8 text-right w-full md:w-auto md:pr-8 md:border-r border-zinc-100">
                      <div className="flex gap-2 md:gap-6 pr-2 md:pr-4">
                        <div className="text-right">
                          <div className="text-[8px] md:text-[10px] font-bold uppercase tracking-widest text-zinc-400 mb-1">Season Rank</div>
                          <div className="text-lg sm:text-xl md:text-3xl font-black tabular-nums leading-none text-zinc-800 flex items-baseline justify-end gap-0.5 md:gap-1">
                            <span className="text-xs md:text-xl text-zinc-400 font-normal">#</span>{modalStats[engine as string]?.seasonRank} <span className="text-[9px] md:text-xs font-bold text-zinc-400">/ {modalStats[engine as string]?.seasonN}</span>
                          </div>
                        </div>
                        <div className="w-px h-8 md:h-10 bg-zinc-200 mt-1 md:mt-2"></div>
                        <div className="text-right">
                          <div className="text-[8px] md:text-[10px] font-bold uppercase tracking-widest text-zinc-400 mb-1">Global Rank</div>
                          <div className="text-lg sm:text-xl md:text-3xl font-black tabular-nums leading-none text-[#b39170] flex items-baseline justify-end gap-0.5 md:gap-1">
                            <span className="text-xs md:text-xl opacity-70 font-normal">#</span>{modalStats[engine as string]?.rank} <span className="text-[9px] md:text-xs font-bold text-[#b39170]/70">/ {data.length}</span>
                          </div>
                        </div>
                      </div>
                      <div className="pl-2 border-l border-zinc-100 md:border-none md:pl-0">
                        <div className="text-[8px] md:text-[10px] font-bold uppercase tracking-widest text-zinc-400 mb-1 whitespace-nowrap">{engineNames[engine as keyof typeof engineNames]}</div>
                        <div className="text-xl sm:text-2xl md:text-3xl font-black tabular-nums leading-none text-zinc-900">
                          {Number(selectedPlayer[engine as keyof PlayerSeason]).toFixed(2)}
                        </div>
                      </div>
                    </div>

                    {/* Desktop End Buttons */}
                    <div className="hidden md:flex items-center gap-2 pl-0 md:pl-8">
                      <button onClick={handlePrev} disabled={selectedIndex <= 0} className="w-10 h-10 rounded-full flex items-center justify-center bg-zinc-50 hover:bg-zinc-100 text-zinc-600 transition-colors disabled:opacity-30">←</button>
                      <button onClick={handleNext} disabled={selectedIndex < 0 || selectedIndex >= filteredData.length - 1} className="w-10 h-10 rounded-full flex items-center justify-center bg-zinc-50 hover:bg-zinc-100 text-zinc-600 transition-colors disabled:opacity-30">→</button>
                      <button onClick={() => setSelectedPlayer(null)} className="w-10 h-10 rounded-full flex items-center justify-center bg-transparent text-zinc-400 hover:text-red-500 hover:bg-red-50 transition-colors ml-2 z-50">✕</button>
                    </div>
                  </div>
                </div>

                {/* Modal Body */}
                <div className="p-4 md:p-10 bg-[#fdfdfc] overflow-y-auto flex-1">
                  <div className="mb-8 md:mb-10 flex flex-col rounded-sm overflow-hidden shadow-sm">
                    {modalTab === 'batting' && (
                      <>
                        <div className="py-6 px-4 md:px-10 bg-zinc-900 flex flex-col md:flex-row justify-between items-start md:items-center relative gap-4">
                          <div className="text-xs md:text-sm font-bold uppercase tracking-[0.2em] text-zinc-500">Batting Performance</div>
                          <div className="flex items-center gap-4 md:gap-10 w-full md:w-auto justify-between md:justify-end">
                            <div className="text-right flex flex-col items-end">
                              <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500 mb-1">{engine === 'quwrof_v11' ? 'Percentile' : 'Points'}</div>
                              <div className="text-4xl font-black tracking-tighter tabular-nums text-white leading-none">{engine === 'quwrof_v11' ? modalStats['bat_percentile']?.val.toFixed(1) + '%' : modalStats['bat_points']?.val.toFixed(1)}</div>
                            </div>
                            <div className="w-px h-10 bg-zinc-700"></div>
                            <div className="text-left flex flex-col items-start mr-4">
                              <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400 mb-1">Season Rank</div>
                              <div className="text-4xl font-black tracking-tighter tabular-nums text-zinc-300 leading-none flex items-baseline gap-1">
                                <span className="text-2xl font-normal text-zinc-500">#</span>{engine === 'quwrof_v11' ? modalStats['bat_percentile']?.seasonRank : modalStats['bat_points']?.seasonRank}
                                <span className="text-[10px] font-bold text-zinc-500 tracking-widest uppercase ml-1">/ {modalStats['bat_points']?.seasonN}</span>
                              </div>
                            </div>
                            <div className="text-left flex flex-col items-start">
                              <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#b39170] mb-1">Global Rank</div>
                              <div className="text-4xl font-black tracking-tighter tabular-nums text-[#b39170] leading-none flex items-baseline gap-1">
                                <span className="text-2xl font-normal opacity-70">#</span>{engine === 'quwrof_v11' ? modalStats['bat_percentile']?.rank : modalStats['bat_points']?.rank}
                              </div>
                            </div>
                          </div>
                        </div>
                        <div className="py-4 px-4 md:px-10 bg-zinc-50 border-t border-zinc-200 border-x border-b flex justify-between items-center">
                          <div className="flex gap-6 md:gap-12 w-full justify-between md:justify-start">
                            <div className="flex flex-col"><span className="text-zinc-400 text-[10px] font-bold uppercase tracking-widest mb-1">Runs</span><span className="text-zinc-900 font-black text-xl tabular-nums leading-none">{selectedPlayer.runs || 0}</span></div>
                            <div className="flex flex-col"><span className="text-zinc-400 text-[10px] font-bold uppercase tracking-widest mb-1">Avg</span><span className="text-zinc-900 font-black text-xl tabular-nums leading-none">{selectedPlayer.batting_average ? selectedPlayer.batting_average.toFixed(2) : '-'}</span></div>
                            <div className="flex flex-col"><span className="text-zinc-400 text-[10px] font-bold uppercase tracking-widest mb-1">SR</span><span className="text-zinc-900 font-black text-xl tabular-nums leading-none">{selectedPlayer.strike_rate ? selectedPlayer.strike_rate.toFixed(2) : '-'}</span></div>
                          </div>
                        </div>
                      </>
                    )}
                    {modalTab === 'bowling' && (
                      <>
                        <div className="py-6 px-4 md:px-10 bg-zinc-900 flex flex-col md:flex-row justify-between items-start md:items-center relative gap-4">
                          <div className="text-xs md:text-sm font-bold uppercase tracking-[0.2em] text-zinc-500">Bowling Performance</div>
                          <div className="flex items-center gap-4 md:gap-10 w-full md:w-auto justify-between md:justify-end">
                            <div className="text-right flex flex-col items-end">
                              <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-500 mb-1">{engine === 'quwrof_v11' ? 'Percentile' : 'Points'}</div>
                              <div className="text-4xl font-black tracking-tighter tabular-nums text-white leading-none">{engine === 'quwrof_v11' ? modalStats['bowl_percentile']?.val.toFixed(1) + '%' : modalStats['bowl_points']?.val.toFixed(1)}</div>
                            </div>
                            <div className="w-px h-10 bg-zinc-700"></div>
                            <div className="text-left flex flex-col items-start mr-4">
                              <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400 mb-1">Season Rank</div>
                              <div className="text-4xl font-black tracking-tighter tabular-nums text-zinc-300 leading-none flex items-baseline gap-1">
                                <span className="text-2xl font-normal text-zinc-500">#</span>{engine === 'quwrof_v11' ? modalStats['bowl_percentile']?.seasonRank : modalStats['bowl_points']?.seasonRank}
                                <span className="text-[10px] font-bold text-zinc-500 tracking-widest uppercase ml-1">/ {modalStats['bowl_points']?.seasonN}</span>
                              </div>
                            </div>
                            <div className="text-left flex flex-col items-start">
                              <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#b39170] mb-1">Global Rank</div>
                              <div className="text-4xl font-black tracking-tighter tabular-nums text-[#b39170] leading-none flex items-baseline gap-1">
                                <span className="text-2xl font-normal opacity-70">#</span>{engine === 'quwrof_v11' ? modalStats['bowl_percentile']?.rank : modalStats['bowl_points']?.rank}
                              </div>
                            </div>
                          </div>
                        </div>
                        <div className="py-4 px-4 md:px-10 bg-zinc-50 border-t border-zinc-200 border-x border-b flex justify-between items-center">
                          <div className="flex gap-6 md:gap-12 w-full justify-between md:justify-start">
                            <div className="flex flex-col"><span className="text-zinc-400 text-[10px] font-bold uppercase tracking-widest mb-1">Wickets</span><span className="text-zinc-900 font-black text-xl tabular-nums leading-none">{selectedPlayer.wickets || 0}</span></div>
                            <div className="flex flex-col"><span className="text-zinc-400 text-[10px] font-bold uppercase tracking-widest mb-1">Avg</span><span className="text-zinc-900 font-black text-xl tabular-nums leading-none">{selectedPlayer.bowling_average ? selectedPlayer.bowling_average.toFixed(2) : '-'}</span></div>
                            <div className="flex flex-col"><span className="text-zinc-400 text-[10px] font-bold uppercase tracking-widest mb-1">Econ</span><span className="text-zinc-900 font-black text-xl tabular-nums leading-none">{selectedPlayer.economy ? selectedPlayer.economy.toFixed(2) : '-'}</span></div>
                          </div>
                        </div>
                      </>
                    )}
                  </div>

                  <div className="mb-8 flex justify-between items-end border-b border-zinc-200 pb-4">
                    <h3 className="text-2xl font-bold tracking-tight text-zinc-900">Metrics Breakdown</h3>
                    <div className="flex bg-zinc-100 p-1 rounded-md">
                      <button onClick={() => setModalTab('batting')} className={`px-4 py-1.5 text-[10px] font-bold uppercase tracking-widest rounded transition-colors ${modalTab === 'batting' ? 'bg-white shadow-sm text-zinc-900' : 'text-zinc-500 hover:text-zinc-700'}`}>Batting</button>
                      <button onClick={() => setModalTab('bowling')} className={`px-4 py-1.5 text-[10px] font-bold uppercase tracking-widest rounded transition-colors ${modalTab === 'bowling' ? 'bg-white shadow-sm text-zinc-900' : 'text-zinc-500 hover:text-zinc-700'}`}>Bowling</button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {Object.entries(v11MetricNames).map(([key, label]) => {
                      const isBattingMetric = key.includes('bat') || key === 'rae';
                      if (modalTab === 'batting' && !isBattingMetric) return null;
                      if (modalTab === 'bowling' && isBattingMetric) return null;

                      const stat = modalStats[key];
                      if (!stat) return null;

                      let tagElement = null;

                      if (stat.rank === 1) {
                        tagElement = <div className="inline-flex items-center justify-center px-2 py-1 bg-[#F9CD05] text-black text-[10px] font-black tracking-widest uppercase shadow-sm border border-yellow-500">TOP 1 ALL TIME</div>;
                      } else if (stat.rank <= 10) {
                        tagElement = <div className="inline-flex items-center justify-center px-2 py-1 bg-zinc-900 text-white text-[10px] font-black tracking-widest uppercase shadow-sm border border-black">TOP 10</div>;
                      } else if (stat.rank <= 50) {
                        tagElement = <div className="inline-flex items-center justify-center px-2 py-1 bg-[#b39170] text-white text-[10px] font-black tracking-widest uppercase shadow-sm border border-[#9c7d5f]">TOP 50</div>;
                      } else if (stat.rank <= 100) {
                        tagElement = <div className="inline-flex items-center justify-center px-2 py-1 bg-zinc-100 text-zinc-700 border border-zinc-300 text-[10px] font-bold tracking-widest uppercase">TOP 100</div>;
                      }

                      return (
                        <div key={key} className="bg-white p-4 border border-zinc-200 hover:border-zinc-900 hover:shadow-xl transition-all duration-300 relative group flex flex-col rounded-md">
                          <div className="absolute top-0 left-0 w-full h-1.5 opacity-0 group-hover:opacity-100 transition-opacity rounded-t-md" style={{ backgroundColor: teamColor }}></div>

                          {tagElement && (
                            <div className="mb-3 flex items-start">
                              {tagElement}
                            </div>
                          )}

                          <div className="flex items-center gap-2 mb-4">
                            <div className="text-xs font-bold text-zinc-500 uppercase tracking-widest truncate" title={label}>{label}</div>
                            <InfoTooltip text={metricDescriptions[key]} />
                          </div>

                          <div className="flex items-end justify-between mb-5">
                            <div className="flex flex-col">
                              <span className="mb-1 text-[9px] font-bold text-zinc-400 uppercase tracking-widest">Rank</span>
                              <span className="text-zinc-900 text-2xl font-black tracking-tighter leading-none">#{stat.rank}</span>
                            </div>
                            <div className="flex flex-col items-end">
                              <span className="mb-1 text-[9px] font-bold text-zinc-400 uppercase tracking-widest">Percentile</span>
                              <span className="text-zinc-900 text-2xl font-black tracking-tighter leading-none">{stat.percentile.toFixed(1)}%</span>
                            </div>
                          </div>

                          <div className="mt-auto">
                            <div className="flex justify-between items-center text-[10px] font-bold text-zinc-500 mb-2.5">
                              <div className="uppercase tracking-widest">Raw Score</div>
                              <div className="text-zinc-700 tabular-nums font-black text-sm">{stat.val > 0 && stat.val < 1 ? stat.val.toFixed(3) : stat.val.toFixed(2)}</div>
                            </div>
                            <div className="w-full h-1.5 bg-zinc-100 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-zinc-900 transition-all duration-700 ease-out"
                                style={{ width: `${stat.percentile}%` }}
                              />
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </motion.div>
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
