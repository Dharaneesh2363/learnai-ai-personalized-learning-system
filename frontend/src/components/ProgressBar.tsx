import React from 'react';

interface ProgressBarProps {
  value: number; // 0 to 100
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ value, showLabel = false, size = 'md' }) => {
  const clamped = Math.min(100, Math.max(0, value));

  // Determine color based on mastery tier
  let colorClass = 'bg-rose-500';
  if (clamped >= 80) {
    colorClass = 'bg-emerald-500';
  } else if (clamped >= 60) {
    colorClass = 'bg-indigo-500';
  } else if (clamped >= 40) {
    colorClass = 'bg-amber-500';
  }

  const heightClass = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
  }[size];

  return (
    <div className="w-full">
      {showLabel && (
        <div className="flex justify-between items-center text-xs mb-1 font-mono">
          <span className="text-slate-400">Mastery</span>
          <span className="text-slate-200 font-bold">{Math.round(clamped)}%</span>
        </div>
      )}
      <div className={`w-full bg-slate-800 rounded-full overflow-hidden ${heightClass}`}>
        <div
          className={`${heightClass} ${colorClass} rounded-full transition-all duration-500 ease-out`}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
};
