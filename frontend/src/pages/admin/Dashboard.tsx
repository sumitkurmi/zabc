import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getAdminStats, adminLogout } from '../../api/admin';
import { AdminStatsResponse } from '../../types';
import { MessageSquare, BookOpen, LogOut, FileText, Activity, Server } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<AdminStatsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    getAdminStats()
      .then((data) => setStats(data))
      .catch((err) => {
        if (err.message && err.message.includes('401')) {
          navigate('/admin/login');
        }
      })
      .finally(() => setIsLoading(false));
  }, [navigate]);

  const handleLogout = () => {
    adminLogout();
    navigate('/admin/login');
  };

  return (
    <div className="min-h-screen bg-slate-100">
      {/* Header */}
      <header className="bg-mnnit-blue text-white shadow-md">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-bold">MNNIT Network Admin Dashboard</h1>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/" className="text-xs text-slate-200 hover:text-white underline">
              Student View
            </Link>
            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-red-600/80 hover:bg-red-600 text-white rounded-lg text-xs font-semibold transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" />
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-slate-800">Knowledge Base & Chat Curation Overview</h2>
          <p className="text-xs text-slate-500 mt-1">Review student chats, promote useful transcripts, and upload knowledge docs.</p>
        </div>

        {/* Three Large Action Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Card 1: See All Chats */}
          <Link
            to="/admin/chats"
            className="bg-white rounded-2xl shadow-md border border-slate-200 p-6 hover:shadow-xl hover:border-blue-300 transition-all group flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <MessageSquare className="w-6 h-6" />
                </div>
                <span className="text-2xl font-black text-blue-700 bg-blue-50 px-3 py-1 rounded-xl">
                  {isLoading ? '...' : stats?.unassigned_chats_count ?? 0}
                </span>
              </div>
              <h3 className="text-lg font-bold text-slate-800 mb-1">See All Unassigned Chats</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Review unassigned student chat transcripts, classify problem areas, and promote chats to curated reference categories.
              </p>
            </div>
            <div className="mt-6 text-xs font-semibold text-blue-600 flex items-center gap-1 group-hover:translate-x-1 transition-transform">
              <span>Manage unassigned chats</span> &rarr;
            </div>
          </Link>

          {/* Card 2: Reference Knowledge Base */}
          <Link
            to="/admin/reference"
            className="bg-white rounded-2xl shadow-md border border-slate-200 p-6 hover:shadow-xl hover:border-emerald-300 transition-all group flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <BookOpen className="w-6 h-6" />
                </div>
                <span className="text-2xl font-black text-emerald-700 bg-emerald-50 px-3 py-1 rounded-xl">
                  {isLoading ? '...' : stats?.reference_documents_count ?? 0}
                </span>
              </div>
              <h3 className="text-lg font-bold text-slate-800 mb-1">See Reference Chats & Documents</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Explore six reference categories, manage promoted chats, and upload SOPs or manuals (.pdf, .docx, .txt).
              </p>
            </div>
            <div className="mt-6 text-xs font-semibold text-emerald-600 flex items-center gap-1 group-hover:translate-x-1 transition-transform">
              <span>View reference categories</span> &rarr;
            </div>
          </Link>

          {/* Card 3: Network Assets and Stock */}
          <Link
            to="/admin/network-assets"
            className="bg-white rounded-2xl shadow-md border border-slate-200 p-6 hover:shadow-xl hover:border-indigo-300 transition-all group flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <Server className="w-6 h-6" />
                </div>
                <span className="text-xs font-bold text-indigo-700 bg-indigo-50 px-3 py-1.5 rounded-xl uppercase tracking-wider">
                  Assets & Stock
                </span>
              </div>
              <h3 className="text-lg font-bold text-slate-800 mb-1">Network Assets and Stock</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Manage hardware lifecycle (switches, routers, APs), campus location hierarchy, port mapping, and bulk stock inventory.
              </p>
            </div>
            <div className="mt-6 text-xs font-semibold text-indigo-600 flex items-center gap-1 group-hover:translate-x-1 transition-transform">
              <span>Open asset manager</span> &rarr;
            </div>
          </Link>
        </div>

        {/* Secondary Metrics Summary */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <p className="text-[11px] text-slate-500 font-medium">Complaints Today</p>
              <p className="text-lg font-bold text-slate-800">{isLoading ? '...' : stats?.complaints_today_count ?? 0}</p>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <p className="text-[11px] text-slate-500 font-medium">Total Conversations</p>
              <p className="text-lg font-bold text-slate-800">{isLoading ? '...' : stats?.total_chats_count ?? 0}</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};
