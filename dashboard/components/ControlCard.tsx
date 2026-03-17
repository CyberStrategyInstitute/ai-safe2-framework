
import React from 'react';
import { motion } from 'framer-motion';
import { Control } from '../types.ts';
import RiskBadge from './RiskBadge.tsx';
import { Star, BookOpen, Activity, CheckSquare } from './Icons.tsx';

interface ControlCardProps {
  control: Control;
  onClick: (control: Control) => void;
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

const ControlCard: React.FC<ControlCardProps> = ({ control, onClick }) => {
  const pillarColor = getPillarColor(control.pillar);
  const hasComponents = control.components && control.components.length > 0;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ y: -6, backgroundColor: 'rgba(30, 41, 59, 0.4)' }}
      className="group relative flex flex-col bg-[#0f172a]/60 border border-slate-800/80 rounded-lg p-6 cursor-pointer shadow-xl overflow-hidden transition-all h-full"
      onClick={() => onClick(control)}
    >
      <div className="absolute left-0 top-0 bottom-0 w-[3px]" style={{ backgroundColor: pillarColor }} />

      <div className="flex justify-between items-start mb-4">
        <div className="flex flex-col gap-1.5 flex-1 min-w-0">
          <h3 className="text-[15px] font-extrabold text-slate-100 group-hover:text-white leading-tight tracking-tight pr-2 truncate">
            {control.name}
          </h3>
          <div className="flex flex-wrap gap-1.5">
            <span className="text-[9px] mono font-bold px-1.5 py-0.5 rounded bg-slate-800/80 text-slate-400 uppercase tracking-widest border border-slate-700">
              {control.id}
            </span>
            {control.cross_reference && (
              <span className="text-[9px] font-black text-blue-400 uppercase tracking-widest bg-blue-500/10 border border-blue-500/20 px-1.5 py-0.5 rounded">
                Complements {control.cross_reference}
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="mb-6 flex-1">
        {hasComponents ? (
          <div className="space-y-3">
            {control.components?.map((comp, idx) => (
              <div key={idx} className="flex items-start gap-2.5">
                <CheckSquare size={12} className="mt-0.5 text-slate-500 flex-shrink-0" />
                <div className="flex flex-col min-w-0">
                  <span className="text-[10px] font-black text-slate-200 uppercase leading-none truncate">{comp.title}</span>
                  <p className="text-[10px] text-slate-500 mt-1 line-clamp-1 leading-tight">{comp.desc}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed font-medium">
            {control.description}
          </p>
        )}
      </div>

      <div className="flex items-center gap-4 mb-4">
        <div className="flex items-center gap-1.5 text-[9px] text-slate-500 font-black uppercase tracking-widest">
          <Activity size={10} className="opacity-50" />
          <span className="truncate">{control.sub_topic.split(' ')[0]}</span>
        </div>
        <div className="flex items-center gap-1.5 text-[9px] text-slate-500 font-black uppercase tracking-widest">
          <BookOpen size={10} className="opacity-50" />
          <span>{control.related_frameworks.length} REF</span>
        </div>
      </div>

      <div className="pt-4 border-t border-slate-800/60 flex justify-between items-center mt-auto">
        <RiskBadge level={control.risk_level} />
        {control.is_gap_filler && (
           <span className="text-[10px] font-black text-amber-500 flex items-center gap-1.5 uppercase tracking-tighter">
             <Star size={10} fill="currentColor" /> v2.1 GAP
           </span>
        )}
      </div>
    </motion.div>
  );
};

export default ControlCard;
