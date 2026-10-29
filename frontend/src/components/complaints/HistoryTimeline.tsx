// MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
// HistoryTimeline component rendering chronological complaint audit trail events.

import React from 'react';
import { Clock, User, ShieldCheck, Cpu } from 'lucide-react';

interface HistoryItem {
  event_type: string;
  from_status?: string;
  to_status?: string;
  actor_type: string;
  actor_name: string;
  note?: string;
  details?: any;
  at: string;
}

interface HistoryTimelineProps {
  history: HistoryItem[];
}

export const HistoryTimeline: React.FC<HistoryTimelineProps> = ({ history }) => {
  const getActorIcon = (type: string) => {
    switch (type) {
      case 'USER':
        return <User className="w-4 h-4 text-blue-600" />;
      case 'AGENT':
        return <Cpu className="w-4 h-4 text-purple-600" />;
      default:
        return <ShieldCheck className="w-4 h-4 text-emerald-600" />;
    }
  };

  return (
    <div className="flow-root my-4">
      <ul className="-mb-8">
        {history.map((item, idx) => (
          <li key={idx}>
            <div className="relative pb-8">
              {idx !== history.length - 1 ? (
                <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-slate-200" aria-hidden="true" />
              ) : null}
              <div className="relative flex space-x-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 ring-8 ring-white">
                  {getActorIcon(item.actor_type)}
                </div>
                <div className="flex min-w-0 flex-1 justify-between space-x-4 pt-1.5">
                  <div>
                    <p className="text-xs text-slate-800 font-semibold">
                      {item.actor_name} ({item.actor_type}){' '}
                      <span className="font-normal text-slate-500">
                        {item.event_type === 'ASSIGNMENT'
                          ? `assigned complaint to ${item.details?.to_technician_name || 'technician'}`
                          : `changed status from ${item.from_status || 'NONE'} to ${item.to_status || 'NEW'}`}
                      </span>
                    </p>
                    {item.note && <p className="text-xs text-slate-600 bg-slate-50 p-2 rounded-lg mt-1 italic border border-slate-100">{item.note}</p>}
                  </div>
                  <div className="whitespace-nowrap text-right text-[11px] text-slate-400 flex items-center gap-1">
                    <Clock className="w-3 h-3 shrink-0" />
                    <span>{new Date(item.at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })}</span>
                  </div>
                </div>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};
