// MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
// ComplaintList component rendering paginated complaint tables with search and filters.

import React from 'react';
import { StatusBadge } from './StatusBadge';
import { Calendar, User, MapPin, ChevronRight } from 'lucide-react';

interface ComplaintListProps {
  complaints: any[];
  onSelect: (ticketId: string) => void;
  showTechnician?: boolean;
}

export const ComplaintList: React.FC<ComplaintListProps> = ({
  complaints,
  onSelect,
  showTechnician = true
}) => {
  if (complaints.length === 0) {
    return (
      <div className="bg-white rounded-2xl p-12 text-center border border-slate-200 shadow-sm my-4">
        <p className="text-sm font-semibold text-slate-500">No complaints found matching criteria.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden my-4">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
              <th className="p-3">Ticket ID</th>
              <th className="p-3">Student Name</th>
              <th className="p-3">Problem Type</th>
              <th className="p-3">Location</th>
              <th className="p-3">Status</th>
              {showTechnician && <th className="p-3">Assigned Tech</th>}
              <th className="p-3">Registered At</th>
              <th className="p-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {complaints.map((c) => (
              <tr
                key={c.ticket_id}
                onClick={() => onSelect(c.ticket_id)}
                className="hover:bg-slate-50/80 cursor-pointer transition-colors"
              >
                <td className="p-3 font-mono font-bold text-blue-700">#{c.ticket_id}</td>
                <td className="p-3 font-semibold text-slate-800">
                  <div className="flex items-center gap-1.5">
                    <User className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span>{c.name}</span>
                  </div>
                </td>
                <td className="p-3 font-medium text-slate-700">{c.problem_type.replace(/_/g, ' ')}</td>
                <td className="p-3 text-slate-600">
                  <div className="flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span>{c.location} ({c.address_room})</span>
                  </div>
                </td>
                <td className="p-3">
                  <StatusBadge status={c.status} />
                </td>
                {showTechnician && (
                  <td className="p-3 font-medium text-slate-700">
                    {c.assigned_technician_name || <span className="text-slate-400 italic">Unassigned</span>}
                  </td>
                )}
                <td className="p-3 text-slate-500">
                  <div className="flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span>{new Date(c.created_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })}</span>
                  </div>
                </td>
                <td className="p-3 text-right">
                  <button className="inline-flex items-center gap-0.5 text-blue-600 hover:text-blue-800 font-semibold text-xs">
                    <span>View</span>
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
