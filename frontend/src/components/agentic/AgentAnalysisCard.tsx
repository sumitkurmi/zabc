// MODULE: Agentic Classification and Assignment (Module 2) - this file belongs to the code for this module.
// AgentAnalysisCard component rendering AI classification, priority reasoning, affected users/equipment, similar faults, and candidate scores.

import React, { useState } from 'react';
import { Bot, AlertTriangle, Users, HardDrive, FileText, CheckCircle2, Play, UserCheck, ShieldAlert } from 'lucide-react';
import { runAgentPipeline, acceptAgentSuggestion } from '../../api/complaints';

interface AgentAnalysisCardProps {
  ticketId: string;
  userRole: 'ADMIN' | 'MANAGER' | 'TECHNICIAN' | 'STUDENT';
  agentAnalysis?: any;
  assignedTechnicianId?: string | null;
  onRefresh?: () => void;
  onOpenManualAssign?: () => void;
}

export const AgentAnalysisCard: React.FC<AgentAnalysisCardProps> = ({
  ticketId,
  userRole,
  agentAnalysis,
  assignedTechnicianId,
  onRefresh,
  onOpenManualAssign
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  if (!agentAnalysis) return null;

  const isManagerOrAdmin = userRole === 'ADMIN' || userRole === 'MANAGER';
  const priority = agentAnalysis.priority || 'MEDIUM';
  const suggestion = agentAnalysis.agent_suggestion;

  const getPriorityBadgeClass = (p: string) => {
    switch (p.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-red-100 text-red-800 dark:bg-red-950/80 dark:text-red-300 border-red-200 dark:border-red-800';
      case 'HIGH':
        return 'bg-amber-100 text-amber-800 dark:bg-amber-950/80 dark:text-amber-300 border-amber-200 dark:border-amber-800';
      case 'MEDIUM':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-950/80 dark:text-blue-300 border-blue-200 dark:border-blue-800';
      case 'LOW':
      default:
        return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800';
    }
  };

  const handleRunAgent = async () => {
    setLoading(true);
    setError(null);
    setSuccessMsg(null);
    try {
      await runAgentPipeline(ticketId);
      setSuccessMsg('Agentic analysis job enqueued successfully.');
      if (onRefresh) onRefresh();
    } catch (err: any) {
      setError(err.message || 'Failed to trigger agent pipeline');
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptSuggestion = async () => {
    setLoading(true);
    setError(null);
    setSuccessMsg(null);
    try {
      await acceptAgentSuggestion(ticketId);
      setSuccessMsg('Agent suggestion accepted and technician assigned.');
      if (onRefresh) onRefresh();
    } catch (err: any) {
      setError(err.message || 'Failed to accept suggestion');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-100 dark:border-gray-700 pb-3">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
          <h3 className="text-base font-semibold text-gray-900 dark:text-white">AI Agentic Analysis</h3>
          {agentAnalysis.method && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300 font-medium">
              {agentAnalysis.method.toUpperCase()} {agentAnalysis.provider ? `(${agentAnalysis.provider})` : ''}
            </span>
          )}
        </div>

        {/* Priority Badge */}
        <div className="flex items-center gap-2">
          <span className={`text-xs px-3 py-1 rounded-full font-bold border ${getPriorityBadgeClass(priority)}`}>
            {priority} PRIORITY
          </span>
          {isManagerOrAdmin && !assignedTechnicianId && (
            <button
              onClick={handleRunAgent}
              disabled={loading}
              className="flex items-center gap-1.5 text-xs bg-indigo-600 text-white px-3 py-1.5 rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors font-medium"
            >
              <Play className="w-3.5 h-3.5" />
              Run Agent Now
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 text-xs p-3 rounded-lg border border-red-200">
          {error}
        </div>
      )}

      {successMsg && (
        <div className="bg-emerald-50 text-emerald-700 text-xs p-3 rounded-lg border border-emerald-200 flex items-center gap-1.5">
          <CheckCircle2 className="w-4 h-4" />
          {successMsg}
        </div>
      )}

      {/* Classification Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-gray-50 dark:bg-gray-900/50 p-3.5 rounded-lg">
        <div>
          <span className="text-xs text-gray-500 dark:text-gray-400 block font-medium">Student Selected Category</span>
          <span className="text-sm font-semibold text-gray-800 dark:text-gray-200">
            {agentAnalysis.student_category || 'N/A'}
          </span>
        </div>
        <div>
          <span className="text-xs text-gray-500 dark:text-gray-400 block font-medium">AI Classified Category</span>
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-indigo-700 dark:text-indigo-300">
              {agentAnalysis.ai_category || agentAnalysis.student_category}
            </span>
            {agentAnalysis.ai_confidence !== undefined && (
              <span className="text-xs bg-indigo-100 text-indigo-800 dark:bg-indigo-900/60 dark:text-indigo-300 px-2 py-0.5 rounded font-mono">
                {(Number(agentAnalysis.ai_confidence) * 100).toFixed(0)}% conf
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Priority Reason & Impact Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-1">
          <span className="text-xs font-medium text-gray-500 dark:text-gray-400 flex items-center gap-1">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-500" /> Priority Reasoning
          </span>
          <p className="text-xs text-gray-700 dark:text-gray-300 bg-amber-50/50 dark:bg-amber-950/20 p-2.5 rounded border border-amber-100 dark:border-amber-900/30">
            {agentAnalysis.priority_reason || 'Standard priority assignment.'}
          </p>
        </div>

        <div className="space-y-1">
          <span className="text-xs font-medium text-gray-500 dark:text-gray-400 flex items-center gap-1">
            <Users className="w-3.5 h-3.5 text-blue-500" /> Affected Users Count
          </span>
          <div className="text-sm font-semibold text-gray-800 dark:text-gray-200 bg-blue-50/50 dark:bg-blue-950/20 p-2.5 rounded border border-blue-100 dark:border-blue-900/30">
            {agentAnalysis.affected_users_count || 1} student(s) impacted in location cluster
          </div>
        </div>
      </div>

      {/* Affected Equipment */}
      {agentAnalysis.affected_equipment && agentAnalysis.affected_equipment.length > 0 && (
        <div className="space-y-1.5">
          <span className="text-xs font-medium text-gray-500 dark:text-gray-400 flex items-center gap-1">
            <HardDrive className="w-3.5 h-3.5 text-purple-500" /> Affected Network Equipment
          </span>
          <div className="flex flex-wrap gap-2">
            {agentAnalysis.affected_equipment.map((eq: any, i: number) => (
              <span key={i} className="text-xs bg-purple-50 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300 px-2.5 py-1 rounded border border-purple-200 dark:border-purple-800">
                {eq.category} ({eq.make} {eq.model})
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Similar Fault History */}
      {agentAnalysis.similar_complaints && agentAnalysis.similar_complaints.length > 0 && (
        <div className="space-y-1.5">
          <span className="text-xs font-medium text-gray-500 dark:text-gray-400 flex items-center gap-1">
            <FileText className="w-3.5 h-3.5 text-emerald-500" /> Related Complaint Faults & Solutions
          </span>
          <div className="space-y-1.5">
            {agentAnalysis.similar_complaints.map((sim: any, i: number) => (
              <div key={i} className="text-xs bg-gray-50 dark:bg-gray-900/60 p-2.5 rounded border border-gray-200 dark:border-gray-700 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <span className="font-semibold text-blue-600 dark:text-blue-400">#{sim.ticket_id}</span>{' '}
                  <span className="text-gray-400">({sim.relation})</span>
                  <p className="text-gray-600 dark:text-gray-300 mt-0.5">{sim.solution_snippet}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Suggest Mode Action Box */}
      {isManagerOrAdmin && suggestion && !assignedTechnicianId && (
        <div className="bg-indigo-50/80 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800 p-4 rounded-xl space-y-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <span className="text-xs font-bold text-indigo-900 dark:text-indigo-200 uppercase tracking-wide flex items-center gap-1">
                <UserCheck className="w-4 h-4 text-indigo-600" /> AI Technician Suggestion
              </span>
              <p className="text-sm font-semibold text-indigo-950 dark:text-indigo-100 mt-1">
                Suggests {suggestion.technician_name} (Score: {suggestion.score}/100)
              </p>
              <p className="text-xs text-indigo-800 dark:text-indigo-300 mt-0.5">{suggestion.reason}</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 pt-1">
            <button
              onClick={handleAcceptSuggestion}
              disabled={loading}
              className="bg-indigo-600 text-white text-xs font-semibold px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors shadow-sm disabled:opacity-50"
            >
              Accept Suggestion & Assign
            </button>
            {onOpenManualAssign && (
              <button
                onClick={onOpenManualAssign}
                className="bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 border border-gray-300 dark:border-gray-600 text-xs font-medium px-4 py-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Choose Another Technician
              </button>
            )}
          </div>
        </div>
      )}

      {/* Candidate Score Breakdown (Visible ONLY for Manager and Admin) */}
      {isManagerOrAdmin && agentAnalysis.top_candidates && agentAnalysis.top_candidates.length > 0 && (
        <div className="space-y-2 border-t border-gray-100 dark:border-gray-700 pt-3">
          <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Technician Candidate Score Ranking</span>
          <div className="space-y-2">
            {agentAnalysis.top_candidates.map((cand: any, idx: number) => (
              <div key={idx} className="text-xs bg-gray-50 dark:bg-gray-900/40 p-2.5 rounded-lg border border-gray-100 dark:border-gray-800 space-y-1">
                <div className="flex justify-between font-medium">
                  <span className="text-gray-800 dark:text-gray-200">{cand.full_name} ({cand.staff_id})</span>
                  <span className="font-bold text-indigo-600 dark:text-indigo-400">{cand.score} / 100</span>
                </div>
                {cand.breakdown && (
                  <p className="text-[11px] text-gray-500 dark:text-gray-400">
                    Zone: {cand.breakdown.zone_match} | Workload: {cand.breakdown.workload} | Exp: {cand.breakdown.experience} | Cluster: {cand.breakdown.cluster} | Perf: {cand.breakdown.performance}
                  </p>
                )}
                <p className="text-[11px] text-gray-600 dark:text-gray-300 italic">{cand.reason}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
