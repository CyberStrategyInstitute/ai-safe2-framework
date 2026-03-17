
import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Control } from '../types.ts';
import { ShieldCheck, Zap, Info, Layers, ChevronRight, Activity, RefreshCcw, Star, BookOpen } from './Icons.tsx';
import RiskBadge from './RiskBadge.tsx';

interface ControlModalProps {
  control: Control | null;
  onClose: () => void;
}

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

const ControlModal: React.FC<ControlModalProps> = ({ control, onClose }) => {
  if (!control) return null;
  const pillarColor = getPillarColor(control.pillar);

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-6 overflow-hidden">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-[#030712]/95 backdrop-blur-xl"
        />
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          className="relative w-full max-w-3xl bg-[#0f172a] border border-slate-800 rounded-xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col"
        >
          {/* Modal Header */}
          <div className="p-6 border-b border-slate-800 flex justify-between items-start bg-slate-900/50">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-3">
                <span 
                  className="text-[10px] mono font-bold px-2 py-1 rounded text-white uppercase tracking-widest whitespace-nowrap"
                  style={{ backgroundColor: `${pillarColor}20`, color: pillarColor, border: `1px solid ${pillarColor}40` }}
                >
                  {control.pillar}
                </span>
                <RiskBadge level={control.risk_level} />
                {control.is_gap_filler && (
                   <span className="text-[10px] font-black text-amber-500 flex items-center gap-1.5 uppercase tracking-widest px-2 py-1 bg-amber-500/10 border border-amber-500/20 rounded whitespace-nowrap">
                     <Star size={10} fill="currentColor" /> v2.1 Advanced
                   </span>
                )}
              </div>
              <h2 className="text-3xl font-extrabold text-white tracking-tight leading-none break-words">{control.name}</h2>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-slate-800 border border-slate-800 rounded-lg text-slate-500 hover:text-white transition-all ml-4"
            >
              <RefreshCcw size={18} className="rotate-45" />
            </button>
          </div>

          {/* Modal Content */}
          <div className="p-8 overflow-y-auto space-y-8 custom-scrollbar bg-[#0f172a]">
            <section>
              <h4 className="text-[11px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-3">Governance Description</h4>
              <p className="text-slate-300 leading-relaxed text-lg font-medium">{control.description}</p>
              {control.framework_note && (
                <div className="mt-4 p-4 rounded bg-slate-800/40 border border-slate-700/50 italic text-slate-400 text-sm flex gap-3">
                  <Info size={14} className="mt-1 flex-shrink-0" />
                  <span>{control.framework_note}</span>
                </div>
              )}
            </section>

            {control.components && control.components.length > 0 && (
              <section>
                <h4 className="text-[11px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                  <Layers size={14} /> Control Components
                </h4>
                <div className="grid gap-3">
                  {control.components.map((comp, idx) => (
                    <div key={idx} className="p-4 rounded-lg bg-slate-900 border border-slate-800 flex flex-col gap-1">
                      <span className="text-xs font-black text-white uppercase tracking-wider">{comp.title}</span>
                      <p className="text-sm text-slate-400">{comp.desc}</p>
                    </div>
                  ))}
                </div>
              </section>
            )}

            <section>
              <h4 className="text-[11px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-4">Strategic Impact & Guidance</h4>
              <div className="grid gap-4">
                <div className="p-5 rounded-lg border border-blue-500/20 bg-blue-500/5 flex gap-4">
                  <div className="flex-shrink-0 mt-1"><Info size={16} className="text-blue-400" /></div>
                  <div>
                    <span className="block text-[10px] font-black uppercase mb-1 text-blue-400 tracking-widest">CISO Decision Impact</span>
                    <p className="text-sm text-slate-200 leading-relaxed">{control.decision_maker_impact}</p>
                  </div>
                </div>
                
                <div className="p-5 rounded-lg border border-emerald-500/20 bg-emerald-500/5 flex gap-4">
                  <div className="flex-shrink-0 mt-1"><Zap size={16} className="text-emerald-400" /></div>
                  <div>
                    <span className="block text-[10px] font-black uppercase mb-1 text-emerald-400 tracking-widest">Implementation Guidance</span>
                    <p className="text-sm text-slate-200 leading-relaxed">{control.implementation_guidance}</p>
                  </div>
                </div>
              </div>
            </section>

            <section>
              <h4 className="text-[11px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-4">Cross-Framework Alignment</h4>
              <div className="flex flex-wrap gap-2">
                {control.related_frameworks.map((f) => (
                  <div key={f} className="px-3 py-2 bg-slate-900 border border-slate-800 rounded flex items-center gap-3">
                    <Activity size={12} className="text-slate-600" />
                    <span className="text-[11px] mono text-slate-300 font-bold uppercase">{f}</span>
                  </div>
                ))}
              </div>
              {control.cross_reference && (
                <div className="mt-4 flex items-center gap-2 text-xs font-bold text-blue-400 p-3 bg-blue-400/5 border border-blue-400/20 rounded">
                  <BookOpen size={14} />
                  <span>Complements System Control: {control.cross_reference}</span>
                </div>
              )}
            </section>
          </div>

          <div className="px-8 py-5 bg-slate-900 border-t border-slate-800 flex justify-between items-center">
            <span className="text-[10px] mono text-slate-500 font-bold tracking-widest">ID: {control.id}</span>
            <button
              onClick={onClose}
              className="px-8 py-3 bg-[#f6921e] hover:bg-orange-500 text-white rounded font-black text-xs shadow-xl shadow-orange-900/20 transition-all active:scale-95 uppercase tracking-widest"
            >
              Verify Control Access
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default ControlModal;
