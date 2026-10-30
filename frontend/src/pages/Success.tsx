import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { CheckCircle2, ArrowLeft, Home } from 'lucide-react';

import { Shield } from 'lucide-react';

export const Success: React.FC = () => {
  const { complaintId } = useParams<{ complaintId: string }>();

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col">
      {/* College Header */}
      <header className="bg-mnnit-blue text-white shadow-lg sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center font-bold text-mnnit-gold border border-white/20 text-sm">
              MNNIT
            </div>
            <div>
              <h1 className="text-base sm:text-lg font-bold tracking-tight">
                MNNIT Allahabad
              </h1>
              <p className="text-[11px] text-slate-200">Network Complaint & AI Diagnosis Portal</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <Link
              to="/login"
              className="text-xs font-semibold text-slate-200 hover:text-white flex items-center gap-1 transition-colors"
            >
              <Shield className="w-3.5 h-3.5 text-mnnit-gold" />
              <span>Staff Login</span>
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center p-4">
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
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-400">
        © {new Date().getFullYear()} MNNIT Allahabad IT Services. All Rights Reserved.
      </footer>
    </div>
  );
};
