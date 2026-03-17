
import React from 'react';

const Logo: React.FC = () => {
  return (
    <div className="flex items-center gap-4">
      <div className="relative group cursor-pointer">
        {/* High-fidelity SVG recreation of the AI SAFE² Circuit-Shield Logo */}
        <img 
          src="../assets/AI SAFE2 Shield nbg.png" 
          alt="Logo" 
          className="w-12 h-12 object-contain" 
        />
      </div>
      <div>
        <h1 className="text-xl font-extrabold tracking-tight text-white flex flex-col leading-none">
          AI SAFE² <span className="text-[10px] tracking-[0.2em] text-[#f6921e] font-mono mt-1 uppercase">AGENTIC AI GRC OS LAYER</span>
        </h1>
      </div>
    </div>
  );
};

export default Logo;
