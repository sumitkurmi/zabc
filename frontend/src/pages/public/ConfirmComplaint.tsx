// MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
// Public ConfirmComplaint page allowing students to confirm or reopen complaints via token link.

import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { fetchTokenInfo, confirmResolution } from '../../api/complaints';
import { CheckCircle2, XCircle, AlertCircle, ShieldCheck } from 'lucide-react';

export const ConfirmComplaint: React.FC = () => {
  const { token } = useParams<{ token: string }>();
  const [tokenInfo, setTokenInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [resultMessage, setResultMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (token) {
      fetchTokenInfo(token)
        .then((data) => setTokenInfo(data))
        .catch((err) => setError(err.message || 'Invalid or expired confirmation link'))
        .finally(() => setLoading(false));
    }
  }, [token]);

  const handleAction = async (solved: boolean) => {
    if (!token) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await confirmResolution(token, solved, comment);
      setResultMessage(res.message);
    } catch (err: any) {
      setError(err.message || 'Failed to submit response');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-xl border border-slate-200 overflow-hidden w-full max-w-lg p-8">
        <div className="text-center mb-6">
          <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-3">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <h1 className="text-xl font-bold text-slate-900">MNNIT IT Services</h1>
          <p className="text-xs text-slate-500 mt-1">Complaint Resolution Confirmation</p>
        </div>

        {resultMessage ? (
          <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-6 text-center space-y-3">
            <CheckCircle2 className="w-10 h-10 text-emerald-600 mx-auto" />
            <h2 className="text-sm font-bold text-emerald-900">Response Submitted</h2>
            <p className="text-xs text-emerald-800">{resultMessage}</p>
            <Link to="/" className="inline-block mt-2 text-xs font-semibold text-blue-600 hover:underline">
              Return to Home
            </Link>
          </div>
        ) : error || !tokenInfo?.is_valid ? (
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6 text-center space-y-3">
            <AlertCircle className="w-10 h-10 text-amber-600 mx-auto" />
            <h2 className="text-sm font-bold text-amber-900">Link Unavailable</h2>
            <p className="text-xs text-amber-800">
              {error || (tokenInfo?.is_used ? 'This confirmation link has already been used.' : 'This confirmation link has expired.')}
            </p>
            <Link to="/" className="inline-block mt-2 text-xs font-semibold text-blue-600 hover:underline">
              Return to Home
            </Link>
          </div>
        ) : (
          <div className="space-y-5">
            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 space-y-2 text-xs">
              <div className="flex justify-between font-mono">
                <span className="text-slate-400">Ticket ID:</span>
                <span className="font-bold text-blue-700">#{tokenInfo.ticket_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Technician:</span>
                <span className="font-semibold text-slate-800">{tokenInfo.technician_name || 'Network Technician'}</span>
              </div>
              {tokenInfo.solution && (
                <div className="pt-2 border-t border-slate-200">
                  <span className="text-slate-400 block mb-1">Solution Provided:</span>
                  <p className="bg-white p-2.5 rounded-xl border border-slate-200 text-slate-700 italic">
                    "{tokenInfo.solution}"
                  </p>
                </div>
              )}
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Optional Feedback / Remarks</label>
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                rows={3}
                placeholder="Let us know if your internet or LAN is working properly now..."
                className="w-full p-2.5 text-xs border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-600"
              />
            </div>

            <div className="grid grid-cols-2 gap-3 pt-2">
              <button
                type="button"
                disabled={submitting}
                onClick={() => handleAction(false)}
                className="py-3 bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 text-xs font-semibold rounded-xl transition-colors flex items-center justify-center gap-1.5"
              >
                <XCircle className="w-4 h-4" />
                <span>Not Solved (Reopen)</span>
              </button>

              <button
                type="button"
                disabled={submitting}
                onClick={() => handleAction(true)}
                className="py-3 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-xl shadow transition-colors flex items-center justify-center gap-1.5"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>Problem Solved</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
