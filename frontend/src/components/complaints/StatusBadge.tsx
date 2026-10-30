// MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
// StatusBadge component rendering color-coded complaint lifecycle badges.

import React from 'react';

interface StatusBadgeProps {
  status: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const getBadgeStyle = (st: string) => {
    switch (st) {
      case 'SUBMITTED':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'CLASSIFIED':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'ASSIGNED':
        return 'bg-indigo-100 text-indigo-800 border-indigo-300';
      case 'DIAGNOSED':
        return 'bg-purple-100 text-purple-800 border-purple-300';
      case 'ACTION_TAKEN':
        return 'bg-cyan-100 text-cyan-800 border-cyan-300';
      case 'STUDENT_CONFIRMATION':
        return 'bg-amber-100 text-amber-900 border-amber-400 animate-pulse';
      case 'CLOSED':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      case 'JUNK':
        return 'bg-slate-200 text-slate-700 border-slate-400 line-through';
      default:
        return 'bg-slate-100 text-slate-800 border-slate-300';
    }
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold border ${getBadgeStyle(status)}`}>
      {status.replace(/_/g, ' ')}
    </span>
  );
};
