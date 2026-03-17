
import React from 'react';
import { RiskLevel } from '../types.ts';

interface RiskBadgeProps {
  level: RiskLevel;
}

const RiskBadge: React.FC<RiskBadgeProps> = ({ level }) => {
  const styles = {
    Critical: "bg-red-500/10 text-red-500 border-red-500/30",
    High: "bg-orange-500/10 text-orange-500 border-orange-500/30",
    Medium: "bg-yellow-500/10 text-yellow-500 border-yellow-500/30",
    Low: "bg-emerald-500/10 text-emerald-500 border-emerald-500/30"
  };

  return (
    <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase tracking-widest border ${styles[level]}`}>
      {level}
    </span>
  );
};

export default RiskBadge;
