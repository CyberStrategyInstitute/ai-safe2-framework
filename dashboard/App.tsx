
import React, { useState, useMemo, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PillarType, Control, TaxonomyFilter } from './types.ts';
import ControlCard from './components/ControlCard.tsx';
import ControlModal from './components/ControlModal.tsx';
import Logo from './components/Logo.tsx';
import { Search, ShieldCheck, Activity, RefreshCcw, ExternalLink } from './components/Icons.tsx';

// Configuration for remote data
const GITHUB_REPO_URL = "https://raw.githubusercontent.com/CyberStrategyInstitute/ai-safe2-framework/main/data/controls.json";
const LOCAL_FALLBACK_URL = "./data/controls.json";

const getPillarColor = (pillar: string) => {
  switch (pillar) {
    case "Sanitize & Isolate": return "#D1E015";
    case "Audit & Inventory": return "#2AC918";
    case "Fail-Safe & Recovery": return "#20D9CC";
    case "Engage & Monitor": return "#4E52A6";
    case "Evolve & Educate": return "#DD1ACC";
    default: return "#f6921e";
  }
};

const App: React.FC = () => {
  const [controls, setControls] = useState<Control[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedControl, setSelectedControl] = useState<Control | null>(null);
  const [dataSource, setDataSource] = useState<'remote' | 'local' | 'loading'>('loading');
  
  const [filters, setFilters] = useState<TaxonomyFilter>({
    pillar: 'All',
    riskLevel: 'All',
    isGapFiller: null,
    searchQuery: ''
  });

  const pillars: PillarType[] = [
    "Sanitize & Isolate",
    "Audit & Inventory",
    "Fail-Safe & Recovery",
    "Engage & Monitor",
    "Evolve & Educate"
  ];

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Try fetching from GitHub
      const response = await fetch(GITHUB_REPO_URL, { cache: 'no-cache' });
      if (!response.ok) throw new Error('Remote source unavailable');
      const data = await response.json();
      setControls(data);
      setDataSource('remote');
    } catch (err) {
      console.warn("GitHub fetch failed, falling back to local data:", err);
      try {
        // 2. Fallback to local file
        const localResponse = await fetch(LOCAL_FALLBACK_URL);
        if (!localResponse.ok) throw new Error('Local fallback failed');
        const localData = await localResponse.json();
        setControls(localData);
        setDataSource('local');
      } catch (localErr) {
        setError("Critical Error: Unable to load framework data from any source.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const filteredControls = useMemo(() => {
    return controls.filter(c => {
      const matchPillar = filters.pillar === 'All' || c.pillar === filters.pillar;
      const matchRisk = filters.riskLevel === 'All' || c.risk_level === filters.riskLevel;
      const matchGap = filters.isGapFiller === null || c.is_gap_filler === filters.isGapFiller;
      const matchSearch = 
        c.name.toLowerCase().includes(filters.searchQuery.toLowerCase()) ||
        c.description.toLowerCase().includes(filters.searchQuery.toLowerCase()) ||
        c.id.toLowerCase().includes(filters.searchQuery.toLowerCase());

      return matchPillar && matchRisk && matchGap && matchSearch;
    });
  }, [filters, controls]);

  const stats = useMemo(() => {
    const total = controls.length;
    const critical = controls.filter(c => c.risk_level === 'Critical').length;
    const gaps = controls.filter(c => c.is_gap_filler).length;
    const pillarsCount = new Set(controls.map(c => c.pillar)).size;
    return { total, critical, gaps, pillarsCount };
  }, [controls]);

  const groupedControls = useMemo(() => {
    const groups: Record<string, Control[]> = {};
    filteredControls.forEach(c => {
      if (!groups[c.pillar]) groups[c.pillar] = [];
      groups[c.pillar].push(c);
    });
    return groups;
  }, [filteredControls]);

  if (loading && dataSource === 'loading') {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-[#030712] text-slate-500 gap-4">
        <RefreshCcw className="animate-spin text-orange-500" size={32} />
        <p className="font-mono text-xs uppercase tracking-widest animate-pulse">Synchronizing with AI SAFE² Repository...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-[#030712] text-red-500 gap-4 p-8 text-center">
        <Activity size={48} />
        <h2 className="text-xl font-bold uppercase tracking-widest">Synchronization Failed</h2>
        <p className="text-sm font-mono max-w-md bg-red-900/10 border border-red-900/20 p-4 rounded">{error}</p>
        <button onClick={loadData} className="px-6 py-2 bg-red-500 text-white rounded font-bold text-xs uppercase tracking-widest hover:bg-red-400 transition-colors">
          Retry Sync
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen bg-[#030712] dashboard-grid">
      {/* Sticky Navigation & Filter Bar */}
      <div className="sticky top-0 z-40 bg-[#030712]/95 backdrop-blur-xl border-b border-white/5 shadow-2xl shadow-black/50">
        {/* Header & High-Level Counters */}
        <header className="px-4 sm:px-8 py-4 flex flex-col sm:flex-row items-center justify-between gap-4 border-b border-white/5 bg-[#0f172a]/20">
          <Logo />
          
          <div className="flex items-center gap-4 sm:gap-6">
            <div className="flex items-center gap-3 border-r border-white/10 pr-4 sm:pr-6">
               <div className="flex flex-col items-end">
                  <span className={`text-[8px] sm:text-[9px] font-black uppercase tracking-[0.2em] ${dataSource === 'remote' ? 'text-emerald-500' : 'text-amber-500'}`}>
                     {dataSource === 'remote' ? '● REPO LIVE' : '○ LOCAL CACHE'}
                  </span>
                  <button 
                    onClick={loadData}
                    className="text-[9px] sm:text-[10px] text-slate-500 hover:text-white transition-colors flex items-center gap-1 group"
                  >
                    <RefreshCcw size={10} className="group-hover:rotate-180 transition-transform duration-500" />
                    SYNC
                  </button>
               </div>
            </div>
            <StatBox label="ENTRIES" value={stats.total} color="text-slate-100" />
            <StatBox label="PILLARS" value={stats.pillarsCount} color="text-blue-400" />
            <StatBox label="CRITICAL" value={stats.critical} color="text-red-500" />
          </div>
        </header>

        {/* Global Filter Bar */}
        <div className="px-4 sm:px-8 py-4 flex flex-col md:flex-row gap-4 md:gap-6 items-center justify-between">
          <div className="relative w-full md:w-[400px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
            <input
              type="text"
              placeholder="Search taxonomy (e.g. Swarm, Validation)..."
              className="w-full bg-[#0f172a] border border-slate-800 rounded-lg py-2 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-[#f6921e]/50 transition-all placeholder:text-slate-600 shadow-inner"
              value={filters.searchQuery}
              onChange={(e) => setFilters(prev => ({ ...prev, searchQuery: e.target.value }))}
            />
          </div>

          <div className="flex items-center gap-2 overflow-x-auto pb-2 md:pb-0 w-full md:w-auto scrollbar-thin scrollbar-thumb-slate-800 scrollbar-track-transparent">
            <Tab 
              label="All" 
              active={filters.pillar === 'All'} 
              onClick={() => setFilters(prev => ({ ...prev, pillar: 'All' }))} 
            />
            {pillars.map(p => (
              <Tab 
                key={p} 
                label={p} 
                active={filters.pillar === p} 
                onClick={() => setFilters(prev => ({ ...prev, pillar: p }))}
                dotColor={getPillarColor(p)}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Grouped Content Sections */}
      <main className="flex-1 p-4 sm:p-8">
        <div className="max-w-[1500px] mx-auto space-y-16 pb-32">
          
          {Object.entries(groupedControls).length > 0 ? (
            Object.entries(groupedControls).map(([pillarName, pControls]) => (
              <section key={pillarName} className="space-y-8">
                <div className="flex items-center gap-5 border-b border-white/5 pb-5">
                  <div 
                    className="p-3.5 rounded-lg border flex items-center justify-center shadow-lg"
                    style={{ 
                        backgroundColor: `${getPillarColor(pillarName)}10`, 
                        borderColor: `${getPillarColor(pillarName)}30`,
                        boxShadow: `0 0 20px ${getPillarColor(pillarName)}05`
                    }}
                  >
                    <ShieldCheck size={24} style={{ color: getPillarColor(pillarName) }} />
                  </div>
                  <div>
                    <h2 className="text-2xl font-extrabold text-white tracking-tight">{pillarName}</h2>
                    <p className="text-xs text-slate-500 font-bold uppercase tracking-[0.2em] mt-1 opacity-70">
                      Primary AI SAFE² Strategic Domain
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                  {pControls.map(control => (
                    <ControlCard 
                      key={control.id} 
                      control={control} 
                      onClick={(c) => setSelectedControl(c)} 
                    />
                  ))}
                </div>
              </section>
            ))
          ) : (
            <div className="flex flex-col items-center justify-center py-48 glass-panel rounded-2xl border-dashed">
              <Activity className="text-slate-800 mb-6 animate-pulse" size={64} />
              <p className="text-slate-400 font-bold tracking-widest uppercase">No controls match your query</p>
              <button 
                onClick={() => setFilters({ pillar: 'All', riskLevel: 'All', isGapFiller: null, searchQuery: '' })}
                className="mt-6 px-8 py-3 bg-[#f6921e]/10 text-[#f6921e] border border-[#f6921e]/20 rounded-full text-xs font-black hover:bg-[#f6921e] hover:text-white transition-all uppercase tracking-widest"
              >
                Reset Dashboard
              </button>
            </div>
          )}
        </div>
      </main>

      <footer className="fixed bottom-0 left-0 right-0 h-10 bg-[#0f172a] border-t border-white/5 px-8 flex items-center justify-between z-20">
          <div className="flex items-center gap-4 text-[10px] text-slate-500 font-bold uppercase tracking-widest">
            <span>Source: Cyber Strategy Institute | AI SAFE² Framework</span>
            <span className="w-1 h-1 rounded-full bg-slate-700"></span>
            <a 
              href="https://github.com/CyberStrategyInstitute/ai-safe2-framework" 
              target="_blank" 
              rel="noreferrer"
              className="flex items-center gap-1 hover:text-white transition-colors"
            >
              Github Repository <ExternalLink size={10} />
            </a>
          </div>
          <div className="text-[10px] text-slate-600 font-mono">
            BUILD_VER: 2.1.0-DYNAMIC
          </div>
      </footer>

      <ControlModal control={selectedControl} onClose={() => setSelectedControl(null)} />
    </div>
  );
};

// --- Sub-components ---

const StatBox: React.FC<{ label: string, value: number, color: string }> = ({ label, value, color }) => (
  <div className="bg-[#1e293b]/20 border border-white/5 rounded-md px-5 py-2.5 min-w-[120px] text-center shadow-sm">
    <div className={`text-2xl font-black tracking-tighter ${color}`}>{value}</div>
    <div className="text-[10px] font-extrabold text-slate-600 uppercase tracking-[0.15em]">{label}</div>
  </div>
);

const Tab: React.FC<{ label: string, active: boolean, onClick: () => void, dotColor?: string }> = ({ label, active, onClick, dotColor }) => (
  <button
    onClick={onClick}
    className={`px-5 py-2 rounded text-[11px] font-black transition-all border flex items-center gap-2.5 whitespace-nowrap uppercase tracking-widest ${
      active 
        ? 'bg-[#f6921e] border-[#f6921e] text-white shadow-lg shadow-orange-900/20' 
        : 'bg-[#1e293b]/40 border-slate-800 text-slate-500 hover:border-slate-600 hover:text-slate-300'
    }`}
  >
    {dotColor && <div className="w-1.5 h-1.5 rounded-full shadow-sm" style={{ backgroundColor: dotColor }} />}
    {label}
  </button>
);

export default App;
