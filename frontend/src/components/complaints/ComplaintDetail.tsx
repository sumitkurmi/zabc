// MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
// ComplaintDetail component rendering detailed complaint information, timeline, resolution, and AI chat transcript.

import React, { useState } from 'react';
import { StatusBadge } from './StatusBadge';
import { HistoryTimeline } from './HistoryTimeline';
import { StarRating } from './StarRating';
import { AssignDialog } from './AssignDialog';
import { LifecycleStepper } from '../agentic/LifecycleStepper';
import { AgentAnalysisCard } from '../agentic/AgentAnalysisCard';
import { markJunk } from '../../api/complaints';
import { User, Phone, Mail, MapPin, Clock, Wrench, Shield, MessageSquare, AlertTriangle, ArrowLeft } from 'lucide-react';

interface ComplaintDetailProps {
  complaint: any;
  userRole: string;
  onBack: () => void;
  onRefresh: () => void;
}

export const ComplaintDetail: React.FC<ComplaintDetailProps> = ({
  complaint,
  userRole,
  onBack,
  onRefresh
}) => {
  const [isAssignOpen, setIsAssignOpen] = useState<boolean>(false);
  const [isJunking, setIsJunking] = useState<boolean>(false);

  const handleMarkJunk = async () => {
    if (!window.confirm(`Are you sure you want to mark Ticket #${complaint.ticket_id} as JUNK?`)) return;
    try {
      setIsJunking(true);
      await markJunk(complaint.ticket_id, 'Marked junk from complaint detail view');
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'Failed to mark as junk');
    } finally {
      setIsJunking(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* 7-Stage Lifecycle Stepper */}
      <LifecycleStepper currentStatus={complaint.status} history={complaint.history || []} />

      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3">
          <button onClick={onBack} className="p-2 text-slate-500 hover:bg-slate-100 rounded-xl transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-slate-900 font-mono">Ticket #{complaint.ticket_id}</h1>
              <StatusBadge status={complaint.status} />
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Registered on {new Date(complaint.created_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })}
            </p>
          </div>
        </div>

        {/* Role-Aware Action Buttons */}
        <div className="flex items-center gap-2">
          {(userRole === 'MANAGER' || userRole === 'ADMIN') && complaint.status !== 'CLOSED' && complaint.status !== 'JUNK' && (
            <button
              onClick={() => setIsAssignOpen(true)}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-xl shadow transition-colors flex items-center gap-1.5"
            >
              <User className="w-4 h-4" />
              <span>{complaint.assigned_technician_id ? 'Reassign Technician' : 'Assign Technician'}</span>
            </button>
          )}

          {userRole === 'ADMIN' && complaint.status !== 'CLOSED' && complaint.status !== 'JUNK' && (
            <button
              onClick={handleMarkJunk}
              disabled={isJunking}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition-colors flex items-center gap-1.5"
            >
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <span>Mark Junk</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Grid: Student & Resolution Info */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Student Info & Resolution */}
        <div className="lg:col-span-2 space-y-6">
          {/* Agentic Analysis Card */}
          {complaint.agent_analysis && (
            <AgentAnalysisCard
              ticketId={complaint.ticket_id}
              userRole={userRole as any}
              agentAnalysis={complaint.agent_analysis}
              assignedTechnicianId={complaint.assigned_technician_id}
              onRefresh={onRefresh}
              onOpenManualAssign={() => setIsAssignOpen(true)}
            />
          )}

          {/* Student Info Card */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
            <h2 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-3 flex items-center gap-2">
              <User className="w-4 h-4 text-blue-600" />
              Student Contact & Location Information
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <span className="text-slate-400 block mb-0.5">Student Name</span>
                <span className="font-semibold text-slate-800">{complaint.name}</span>
              </div>
              <div>
                <span className="text-slate-400 block mb-0.5">Email Address</span>
                <span className="font-semibold text-slate-800 flex items-center gap-1">
                  <Mail className="w-3.5 h-3.5 text-slate-400" />
                  {complaint.email}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block mb-0.5">Mobile Number</span>
                <span className="font-semibold text-slate-800 flex items-center gap-1">
                  <Phone className="w-3.5 h-3.5 text-slate-400" />
                  {complaint.mobile}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block mb-0.5">Location / Area</span>
                <span className="font-semibold text-slate-800 flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5 text-slate-400" />
                  {complaint.location} ({complaint.address_room})
                </span>
              </div>
              <div>
                <span className="text-slate-400 block mb-0.5">Preferred Time Window</span>
                <span className="font-semibold text-slate-800 flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-slate-400" />
                  {complaint.preferred_from} - {complaint.preferred_to}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block mb-0.5">Problem Category</span>
                <span className="font-bold text-blue-700">{complaint.problem_type.replace(/_/g, ' ')}</span>
              </div>
            </div>

            {complaint.additional_comment && (
              <div className="pt-2 border-t border-slate-100">
                <span className="text-xs text-slate-400 block mb-1">Additional Student Comment</span>
                <p className="text-xs text-slate-700 bg-slate-50 p-3 rounded-xl border border-slate-100 italic">
                  "{complaint.additional_comment}"
                </p>
              </div>
            )}
          </div>

          {/* Resolution Details Card (if diagnosed/action taken) */}
          {complaint.solution && (
            <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
              <h2 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-3 flex items-center gap-2">
                <Wrench className="w-4 h-4 text-emerald-600" />
                Technician Resolution & Diagnosis
              </h2>
              <div className="space-y-3 text-xs">
                <div>
                  <span className="text-slate-400 block mb-1">Diagnosis</span>
                  <p className="p-3 bg-slate-50 text-slate-800 rounded-xl border border-slate-100">{complaint.diagnosis}</p>
                </div>
                <div>
                  <span className="text-slate-400 block mb-1">Solution Provided</span>
                  <p className="p-3 bg-emerald-50/50 text-emerald-900 rounded-xl border border-emerald-100">{complaint.solution}</p>
                </div>

                {complaint.items_used && complaint.items_used.length > 0 && (
                  <div>
                    <span className="text-slate-400 block mb-1">Stock Items Used</span>
                    <ul className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden bg-white">
                      {complaint.items_used.map((item: any, idx: number) => (
                        <li key={idx} className="p-2.5 flex items-center justify-between text-slate-700">
                          <span>{item.name} (Qty: {item.quantity})</span>
                          <span className="text-slate-400 text-[11px]">Used by {item.used_by}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Student Rating Card (if rated) */}
          {complaint.rating_info && (
            <div className="bg-amber-50/50 rounded-2xl p-6 border border-amber-200 shadow-sm space-y-2">
              <h2 className="text-sm font-bold text-amber-900 flex items-center gap-2">
                <span>Student Feedback Rating</span>
              </h2>
              <div className="flex items-center gap-3 pt-1">
                <StarRating value={complaint.rating_info.rating} readOnly size={22} />
                <span className="text-sm font-bold text-amber-800">{complaint.rating_info.rating} / 5</span>
              </div>
              {complaint.rating_info.feedback && (
                <p className="text-xs text-amber-800 italic bg-white p-3 rounded-xl border border-amber-200 mt-2">
                  "{complaint.rating_info.feedback}"
                </p>
              )}
            </div>
          )}
        </div>

        {/* Right Col: History Timeline & Assignment Meta */}
        <div className="space-y-6">
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
            <h2 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-3 flex items-center gap-2">
              <Shield className="w-4 h-4 text-indigo-600" />
              Lifecycle Audit History
            </h2>
            <HistoryTimeline history={complaint.history || []} />
          </div>
        </div>
      </div>

      {/* Assign Modal */}
      <AssignDialog
        ticketId={complaint.ticket_id}
        isOpen={isAssignOpen}
        onClose={() => setIsAssignOpen(false)}
        onAssigned={onRefresh}
      />
    </div>
  );
};
