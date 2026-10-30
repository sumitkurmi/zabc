// MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
// Public RateComplaint page allowing students to submit 1-5 star service quality rating.

import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { fetchTokenInfo, submitRating } from '../../api/complaints';
import { StarRating } from '../../components/complaints/StarRating';
import { Star, CheckCircle2, AlertCircle, ShieldCheck, Shield } from 'lucide-react';

export const RateComplaint: React.FC = () => {
  const { token } = useParams<{ token: string }>();
  const [tokenInfo, setTokenInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [rating, setRating] = useState<number>(5);
  const [feedback, setFeedback] = useState<string>('');
  const [submitting, setSubmitting] = useState(false);
  const [resultMessage, setResultMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (token) {
      fetchTokenInfo(token)
        .then((data) => setTokenInfo(data))
        .catch((err) => setError(err.message || 'Invalid or expired rating link'))
        .finally(() => setLoading(false));
    }
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await submitRating(token, rating, feedback);
      setResultMessage(res.message);
    } catch (err: any) {
      setError(err.message || 'Failed to submit rating');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col">
        <header className="bg-mnnit-blue text-white shadow-lg sticky top-0 z-30">
          <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center font-bold text-mnnit-gold border border-white/20 text-sm">
                MNNIT
              </div>
              <div>
                <h1 className="text-base sm:text-lg font-bold tracking-tight">MNNIT Allahabad</h1>
                <p className="text-[11px] text-slate-200">Network Complaint & AI Diagnosis Portal</p>
              </div>
            </div>
          </div>
        </header>
        <div className="flex-1 flex items-center justify-center p-4">
          <div className="w-8 h-8 border-4 border-amber-500 border-t-transparent rounded-full animate-spin" />
        </div>
      </div>
    );
  }

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
        <div className="bg-white rounded-3xl shadow-xl border border-slate-200 overflow-hidden w-full max-w-lg p-8">
        <div className="text-center mb-6">
          <div className="w-12 h-12 bg-amber-50 text-amber-600 rounded-2xl flex items-center justify-center mx-auto mb-3">
            <Star className="w-6 h-6 fill-amber-500" />
          </div>
          <h1 className="text-xl font-bold text-slate-900">MNNIT IT Services</h1>
          <p className="text-xs text-slate-500 mt-1">Rate Technician Service Quality</p>
        </div>

        {resultMessage ? (
          <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-6 text-center space-y-3">
            <CheckCircle2 className="w-10 h-10 text-emerald-600 mx-auto" />
            <h2 className="text-sm font-bold text-emerald-900">Rating Submitted</h2>
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
              {error || (tokenInfo?.is_used ? 'This rating link has already been used.' : 'This rating link has expired.')}
            </p>
            <Link to="/" className="inline-block mt-2 text-xs font-semibold text-blue-600 hover:underline">
              Return to Home
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 text-xs space-y-2 text-center">
              <span className="text-slate-400 block">Assigned Technician:</span>
              <span className="font-bold text-slate-800 text-sm">{tokenInfo.technician_name || 'Network Technician'}</span>
            </div>

            <div className="flex flex-col items-center gap-2 py-2">
              <label className="text-xs font-semibold text-slate-700">Select Rating (1 to 5 Stars)</label>
              <StarRating value={rating} onChange={setRating} size={32} />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Written Feedback (Optional)</label>
              <textarea
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                rows={3}
                maxLength={1000}
                placeholder="How satisfied were you with the response speed and solution quality?"
                className="w-full p-2.5 text-xs border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-3 bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold rounded-xl shadow transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {submitting ? 'Submitting...' : 'Submit Service Rating'}
            </button>
          </form>
        )}
        </div>
      </main>

      <footer className="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-400">
        © {new Date().getFullYear()} MNNIT Allahabad IT Services. All Rights Reserved.
      </footer>
    </div>
  );
};
