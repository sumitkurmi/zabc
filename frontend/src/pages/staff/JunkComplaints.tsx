// MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
// JunkComplaints page for admins to view, restore, and permanently clear junk complaints.

import React, { useEffect, useState } from 'react';
import { fetchJunkComplaints, restoreJunk, clearAllJunk } from '../../api/complaints';
import { Trash2, RotateCcw, AlertTriangle, Shield, Calendar } from 'lucide-react';

export const JunkComplaints: React.FC = () => {
  const [junkList, setJunkList] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);

  const loadJunk = () => {
    setLoading(true);
    fetchJunkComplaints()
      .then((res) => {
        setJunkList(res.complaints);
        setTotal(res.total);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadJunk();
  }, []);

  const handleRestore = async (ticketId: string) => {
    try {
      await restoreJunk(ticketId);
      loadJunk();
    } catch (err: any) {
      alert(err.message || 'Failed to restore complaint');
    }
  };

  const handleClearAll = async () => {
    if (!window.confirm(`PERMANENT ACTION: Are you sure you want to permanently delete ALL ${total} junk complaint(s)? This cannot be undone.`)) return;

    try {
      await clearAllJunk(true);
      loadJunk();
    } catch (err: any) {
      alert(err.message || 'Failed to clear junk');
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden p-6 space-y-6">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4">
        <h1 className="text-base font-bold text-slate-900 flex items-center gap-2">
          <Trash2 className="w-5 h-5 text-amber-600" />
          Junk Complaints Management ({total})
        </h1>
        {total > 0 && (
          <button
            onClick={handleClearAll}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-xs font-semibold rounded-xl shadow transition-colors flex items-center gap-1.5"
          >
            <AlertTriangle className="w-4 h-4" />
            <span>Permanently Clear All Junk</span>
          </button>
        )}
      </div>

      {junkList.length === 0 ? (
        <div className="p-12 text-center text-slate-400 text-xs">No junk complaints in the bin.</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase">
                <th className="p-3">Ticket ID</th>
                <th className="p-3">Student Name</th>
                <th className="p-3">Problem Type</th>
                <th className="p-3">Location</th>
                <th className="p-3">Previous Status</th>
                <th className="p-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {junkList.map((c) => (
                <tr key={c.ticket_id} className="hover:bg-slate-50">
                  <td className="p-3 font-mono font-bold text-slate-700">#{c.ticket_id}</td>
                  <td className="p-3 font-semibold text-slate-900">{c.name}</td>
                  <td className="p-3 text-slate-700">{c.problem_type.replace(/_/g, ' ')}</td>
                  <td className="p-3 text-slate-600">{c.location}</td>
                  <td className="p-3 font-semibold text-indigo-700">{c.previous_status || 'CLASSIFIED'}</td>
                  <td className="p-3 text-right">
                    <button
                      onClick={() => handleRestore(c.ticket_id)}
                      className="px-3 py-1 bg-blue-50 text-blue-700 hover:bg-blue-100 font-semibold rounded-lg text-xs flex items-center gap-1 ml-auto"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                      <span>Restore Ticket</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
