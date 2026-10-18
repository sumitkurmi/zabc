import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { CheckCircle2, ArrowLeft, Home } from 'lucide-react';

export const Success: React.FC = () => {
  const { complaintId } = useParams<{ complaintId: string }>();

  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-lg w-full p-8 text-center">
        <div className="w-16 h-16 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto mb-4">
          <CheckCircle2 className="w-10 h-10" />
        </div>

        <h1 className="text-2xl font-bold text-slate-800 mb-2">Complaint Registered Successfully</h1>
        <p className="text-xs text-slate-500 mb-6">
          Your network problem report has been logged with MNNIT IT Support.
        </p>

        <div className="bg-slate-50 border border-slate-200 rounded-2xl p-5 mb-8">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Reference Number
          </span>
          <span className="text-2xl font-mono font-bold text-mnnit-blue select-all">
            {complaintId || 'NET-2026-000000'}
          </span>
          <p className="text-[11px] text-slate-400 mt-2">
            Save this reference number to track your ticket status with technical staff.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <Link
            to="/"
            className="flex-1 py-3 px-4 bg-mnnit-blue hover:bg-blue-800 text-white rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-colors"
          >
            <Home className="w-4 h-4" />
            <span>Return to Home</span>
          </Link>
        </div>
      </div>
    </div>
  );
};
