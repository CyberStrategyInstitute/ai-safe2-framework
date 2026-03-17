
import React from 'react';
import { PillarType, RiskLevel, TaxonomyFilter } from '../types.ts';
import { Filter, Star, ShieldCheck, AlertCircle } from './Icons.tsx';

interface SidebarProps {
  filters: TaxonomyFilter;
  setFilters: React.Dispatch<React.SetStateAction<TaxonomyFilter>>;
  pillars: PillarType[];
}

const Sidebar: React.FC<SidebarProps> = ({ filters, setFilters, pillars }) => {
  const risks: RiskLevel[] = ["Critical", "High", "Medium", "Low"];

  return (
    <aside className="w-full lg:w-72 flex-shrink-0 bg-slate-900/50 border-r border-slate-800 p-6 flex flex-col gap-8 h-full overflow-y-auto">
      <div>
        <div className="flex items-center gap-2 text-slate-400 mb-4 text-xs font-bold uppercase tracking-widest">
          <Filter size={14} /> Framework Pillars
        </div>
        <div className="space-y-1">
          <button
            onClick={() => setFilters(prev => ({ ...prev, pillar: 'All' }))}
            className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all ${
              filters.pillar === 'All' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
            }`}
          >
            All Controls
          </button>
          {pillars.map(p => (
            <button
              key={p}
              onClick={() => setFilters(prev => ({ ...prev, pillar: p }))}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all ${
                filters.pillar === p ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      <div>
        <div className="flex items-center gap-2 text-slate-400 mb-4 text-xs font-bold uppercase tracking-widest">
          <AlertCircle size={14} /> Risk Profile
        </div>
        <div className="grid grid-cols-2 gap-2">
          {risks.map(r => (
            <button
              key={r}
              onClick={() => setFilters(prev => ({ ...prev, riskLevel: filters.riskLevel === r ? 'All' : r }))}
              className={`px-3 py-2 rounded-lg text-xs font-bold transition-all border ${
                filters.riskLevel === r 
                  ? 'bg-slate-700 border-blue-500 text-white' 
                  : 'bg-slate-900/50 border-slate-800 text-slate-500 hover:border-slate-700'
              }`}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      <div>
        <div className="flex items-center gap-2 text-slate-400 mb-4 text-xs font-bold uppercase tracking-widest">
          <Star size={14} /> v2.1 Gap Analysis
        </div>
        <label className="group flex items-center justify-between p-3 rounded-xl bg-slate-900/50 border border-slate-800 hover:border-amber-500/30 transition-all cursor-pointer">
          <span className="text-sm text-slate-300 flex items-center gap-2">
            <ShieldCheck size={16} className="text-amber-500" /> Gap Fillers Only
          </span>
          <input 
            type="checkbox" 
            checked={!!filters.isGapFiller} 
            onChange={(e) => setFilters(prev => ({ ...prev, isGapFiller: e.target.checked || null }))}
            className="w-4 h-4 rounded border-slate-700 bg-slate-800 text-amber-500 focus:ring-amber-500 transition-all"
          />
        </label>
        <p className="mt-2 text-[10px] text-slate-500 leading-relaxed italic">
          v2.1 Gap Fillers address Swarms, Distributed Agents, and Non-Human Identity risks.
        </p>
      </div>

      <div className="mt-auto pt-6 border-t border-slate-800">
        <div className="p-4 rounded-xl bg-blue-900/10 border border-blue-500/20">
          <h4 className="text-xs font-bold text-blue-400 mb-1">AI SAFE² Framework</h4>
          <p className="text-[10px] text-slate-400">Board-Approved Strategic Framework for Advanced Agentic & Distributed AI Compliance.</p>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
