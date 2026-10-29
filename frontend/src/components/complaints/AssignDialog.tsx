// MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
// AssignDialog modal for managers/admins to assign complaints to available technicians.

import React, { useState, useEffect } from 'react';
import { fetchTechnicians, assignComplaint } from '../../api/complaints';
import { X, UserCheck, AlertCircle } from 'lucide-react';

interface AssignDialogProps {
  ticketId: string;
  isOpen: boolean;
  onClose: () => void;
  onAssigned: () => void;
}

export const AssignDialog: React.FC<AssignDialogProps> = ({
  ticketId,
  isOpen,
  onClose,
  onAssigned
}) => {
  const [technicians, setTechnicians] = useState<any[]>([]);
  const [selectedTechId, setSelectedTechId] = useState<string>('');
  const [reason, setReason] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchTechnicians()
        .then((data) => {
          // Filter available technicians
          const avail = data.filter((t) => t.availability === 'AVAILABLE');
          setTechnicians(avail);
          if (avail.length > 0) {
            setSelectedTechId(avail[0]._id);
          }
        })
        .catch((err) => setError('Failed to load technicians list'));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTechId) {
      setError('Please select a technician');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await assignComplaint(ticketId, selectedTechId, reason);
      onAssigned();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to assign technician');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-xl border border-slate-200 w-full max-w-md overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-slate-100 bg-slate-50">
          <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
            <UserCheck className="w-4 h-4 text-blue-600" />
            Assign Technician (Ticket #{ticketId})
          </h3>
          <button onClick={onClose} className="p-1 text-slate-400 hover:text-slate-600 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="p-3 bg-red-50 text-red-700 text-xs flex items-center gap-2 border-b border-red-100">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Select Available Technician <span className="text-red-500">*</span>
            </label>
            {technicians.length === 0 ? (
              <p className="text-xs text-amber-600 bg-amber-50 p-2.5 rounded-xl border border-amber-200">
                No technicians are currently marked AVAILABLE.
              </p>
            ) : (
              <select
                value={selectedTechId}
                onChange={(e) => setSelectedTechId(e.target.value)}
                className="w-full p-2.5 text-sm border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-600 bg-white"
              >
                {technicians.map((t) => (
                  <option key={t._id} value={t._id}>
                    {t.full_name} ({t.open_complaints_count} open ticket(s)) - Zones: {t.zones?.join(', ') || 'All'}
                  </option>
                ))}
              </select>
            )}
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Assignment Note / Reason (Optional)
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              placeholder="e.g. Assigned based on hostel zone location"
              className="w-full p-2.5 text-sm border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-600"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || technicians.length === 0}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-xl shadow disabled:opacity-50"
            >
              {loading ? 'Assigning...' : 'Confirm Assignment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
