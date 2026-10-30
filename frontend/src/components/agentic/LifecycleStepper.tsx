// MODULE: Agentic Classification and Assignment (Module 2) - this file belongs to the code for this module.
// LifecycleStepper component rendering 7-stage complaint progression with timestamps and actors.

import React from 'react';
import { CheckCircle2, Circle, Clock } from 'lucide-react';

export interface HistoryItem {
  event_type: string;
  from_status?: string | null;
  to_status?: string | null;
  actor_type: string;
  actor_name: string;
  note?: string | null;
  details?: any;
  at: string;
}

interface LifecycleStepperProps {
  currentStatus: string;
  history: HistoryItem[];
}

const STAGES = [
  { key: 'SUBMITTED', label: 'Submitted' },
  { key: 'CLASSIFIED', label: 'Classified' },
  { key: 'ASSIGNED', label: 'Assigned' },
  { key: 'DIAGNOSED', label: 'Diagnosed' },
  { key: 'ACTION_TAKEN', label: 'Action Taken' },
  { key: 'STUDENT_CONFIRMATION', label: 'Student Confirmation' },
  { key: 'CLOSED', label: 'Closed' }
];

const STAGE_ORDER: Record<string, number> = {
  SUBMITTED: 1,
  CLASSIFIED: 2,
  ASSIGNED: 3,
  DIAGNOSED: 4,
  ACTION_TAKEN: 5,
  STUDENT_CONFIRMATION: 6,
  CLOSED: 7,
  JUNK: 0
};

/**
 * Renders 7-stage visual lifecycle stepper. Responsive layout down to 360px.
 */
export const LifecycleStepper: React.FC<LifecycleStepperProps> = ({ currentStatus, history }) => {
  const currentStepNum = STAGE_ORDER[currentStatus] || 1;

  // Find history event for each stage
  const getStageInfo = (stageKey: string) => {
    if (!history) return null;
    // Find the latest history entry that transitioned TO this status or created SUBMITTED
    const match = history.slice().reverse().find((h) => {
      if (stageKey === 'SUBMITTED') {
        return h.from_status === 'SUBMITTED' || h.to_status === 'SUBMITTED' || h.event_type === 'STATUS_CHANGE';
      }
      return h.to_status === stageKey;
    });
    return match;
  };

  const formatDate = (isoStr?: string) => {
    if (!isoStr) return '';
    try {
      const dt = new Date(isoStr);
      return dt.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  return (
    <div className="w-full bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-6 shadow-sm border border-gray-100 dark:border-gray-700">
      <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
        <Clock className="w-4 h-4 text-blue-600 dark:text-blue-400" />
        Complaint Lifecycle Progress
      </h3>

      {/* Desktop / Tablet Horizontal Stepper */}
      <div className="hidden lg:flex items-start justify-between relative">
        {STAGES.map((stage, idx) => {
          const stepNum = idx + 1;
          const isDone = currentStepNum > stepNum || currentStatus === 'CLOSED';
          const isCurrent = currentStepNum === stepNum && currentStatus !== 'CLOSED';
          const stageInfo = getStageInfo(stage.key);

          return (
            <div key={stage.key} className="flex-1 flex flex-col items-center text-center relative z-10">
              {/* Connector line */}
              {idx > 0 && (
                <div
                  className={`absolute top-4 -left-1/2 w-full h-0.5 -z-10 ${
                    currentStepNum >= stepNum ? 'bg-blue-600 dark:bg-blue-500' : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                />
              )}

              {/* Node Icon */}
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs transition-colors ${
                  isDone
                    ? 'bg-blue-600 text-white dark:bg-blue-500'
                    : isCurrent
                    ? 'bg-blue-100 text-blue-700 ring-2 ring-blue-600 dark:bg-blue-900/50 dark:text-blue-300 dark:ring-blue-400'
                    : 'bg-gray-100 text-gray-400 dark:bg-gray-700 dark:text-gray-500'
                }`}
              >
                {isDone ? <CheckCircle2 className="w-5 h-5" /> : stepNum}
              </div>

              {/* Stage Title */}
              <p
                className={`mt-2 text-xs font-medium leading-tight ${
                  isCurrent
                    ? 'text-blue-700 dark:text-blue-300 font-semibold'
                    : isDone
                    ? 'text-gray-900 dark:text-gray-200'
                    : 'text-gray-400 dark:text-gray-500'
                }`}
              >
                {stage.label}
              </p>

              {/* Timestamp & Actor */}
              {stageInfo && (
                <div className="mt-1 text-[11px] text-gray-500 dark:text-gray-400 leading-tight">
                  <p className="font-medium text-gray-700 dark:text-gray-300">{stageInfo.actor_name}</p>
                  <p className="text-[10px] opacity-80">{formatDate(stageInfo.at)}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Mobile Vertical Stepper (<1024px, 360px friendly) */}
      <div className="lg:hidden flex flex-col gap-4 relative pl-4 border-l-2 border-gray-200 dark:border-gray-700 ml-2">
        {STAGES.map((stage, idx) => {
          const stepNum = idx + 1;
          const isDone = currentStepNum > stepNum || currentStatus === 'CLOSED';
          const isCurrent = currentStepNum === stepNum && currentStatus !== 'CLOSED';
          const stageInfo = getStageInfo(stage.key);

          return (
            <div key={stage.key} className="relative flex items-start gap-3">
              {/* Bullet node on line */}
              <div
                className={`absolute -left-[25px] top-0.5 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                  isDone
                    ? 'bg-blue-600 text-white dark:bg-blue-500'
                    : isCurrent
                    ? 'bg-blue-100 text-blue-700 ring-2 ring-blue-600 dark:bg-blue-900/50 dark:text-blue-300'
                    : 'bg-gray-100 text-gray-400 dark:bg-gray-700 dark:text-gray-500'
                }`}
              >
                {isDone ? <CheckCircle2 className="w-4 h-4" /> : stepNum}
              </div>

              {/* Content block */}
              <div className="flex-1">
                <p
                  className={`text-sm font-medium ${
                    isCurrent
                      ? 'text-blue-700 dark:text-blue-300 font-semibold'
                      : isDone
                      ? 'text-gray-900 dark:text-gray-200'
                      : 'text-gray-400 dark:text-gray-500'
                  }`}
                >
                  {stage.label}
                </p>
                {stageInfo && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                    <span className="font-medium text-gray-700 dark:text-gray-300">{stageInfo.actor_name}</span>
                    {formatDate(stageInfo.at) && ` • ${formatDate(stageInfo.at)}`}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
