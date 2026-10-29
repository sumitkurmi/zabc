// MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
// Admin Dashboard page integrating Part 1 chat/KB curation, network assets, and Part 2 complaint/staff management cards.

import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getAdminStats, adminLogout } from '../../api/admin';
import { AdminStatsResponse } from '../../types';
import { MessageSquare, BookOpen, LogOut, FileText, Activity, Server, Users, Trash2, Settings, Trophy, Shield, Inbox } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<AdminStatsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    getAdminStats()
      .then((data) => setStats(data))
      .catch((err) => {
        if (err.message && err.message.includes('401')) {
          navigate('/login');
        }
      })
      .finally(() => setIsLoading(false));
  }, [navigate]);

  const handleLogout = () => {
    adminLogout();
    navigate('/login');
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
      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">Admin Control Center</h2>
          <p className="text-xs text-slate-500 mt-1">Manage complaint dispatch, staff accounts, knowledge base, and network assets.</p>
        </div>

        {/* Part 2 Action Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card: Complaint Management */}
          <Link
            to="/manager"
            className="bg-white rounded-2xl shadow-md border border-slate-200 p-6 hover:shadow-xl hover:border-blue-300 transition-all group flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <Inbox className="w-6 h-6" />
                </div>
                <span className="text-xs font-bold text-blue-700 bg-blue-50 px-3 py-1.5 rounded-xl uppercase">
                  Complaint Manager
                </span>
              </div>
              <h3 className="text-lg font-bold text-slate-800 mb-1">Complaint Queue & Dispatch</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Assign complaints to technicians, monitor lifecycle transitions, view history timeline, and access reports.
              </p>
            </div>
            <div className="mt-6 text-xs font-semibold text-blue-600 flex items-center gap-1 group-hover:translate-x-1 transition-transform">
              <span>Open complaint manager</span> &rarr;
            </div>
          </Link>

          {/* Card: Staff Management */}
          <Link
            to="/admin/staff"
            className="bg-white rounded-2xl shadow-md border border-slate-200 p-6 hover:shadow-xl hover:border-purple-300 transition-all group flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 rounded-2xl bg-purple-50 text-purple-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <Users className="w-6 h-6" />
                </div>
                <span className="text-xs font-bold text-purple-700 bg-purple-50 px-3 py-1.5 rounded-xl uppercase">
                  Staff Accounts
                </span>
              </div>
              <h3 className="text-lg font-bold text-slate-800 mb-1">Staff User Management</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Create Manager/Technician accounts, assign technician zones, reset passwords, and soft deactivate staff.
              </p>
            </div>
            <div className="mt-6 text-xs font-semibold text-purple-600 flex items-center gap-1 group-hover:translate-x-1 transition-transform">
              <span>Manage staff accounts</span> &rarr;
            </div>
          </Link>

          {/* Card: Junk Complaints */}
          <Link
            to="/admin/junk"
            className="bg-white rounded-2xl shadow-md border border-slate-200 p-6 hover:shadow-xl hover:border-amber-300 transition-all group flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <Trash2 className="w-6 h-6" />
                </div>
                <span className="text-xs font-bold text-amber-700 bg-amber-50 px-3 py-1.5 rounded-xl uppercase">
                  Junk Bin
                </span>
              </div>
              <h3 className="text-lg font-bold text-slate-800 mb-1">Junk Complaints & Purge</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Review complaints marked as JUNK, restore tickets back to previous status, or permanently purge bin.
              </p>
            </div>
            <div className="mt-6 text-xs font-semibold text-amber-600 flex items-center gap-1 group-hover:translate-x-1 transition-transform">
              <span>View junk bin</span> &rarr;
            </div>
          </Link>
        </div>

        {/* Part 1 Action Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card: See All Chats */}
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
              <h3 className="text-lg font-bold text-slate-800 mb-1">Unassigned AI Chats</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Review student chat transcripts and promote helpful conversations to curated reference categories.
              </p>
            </div>
            <div className="mt-6 text-xs font-semibold text-blue-600 flex items-center gap-1 group-hover:translate-x-1 transition-transform">
              <span>Manage AI chats</span> &rarr;
            </div>
          </Link>

          {/* Card: Reference Knowledge Base */}
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
              <h3 className="text-lg font-bold text-slate-800 mb-1">Knowledge Base Documents</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Upload manuals, SOPs, and guide documents (.pdf, .docx, .txt) into six reference categories.
              </p>
            </div>
            <div className="mt-6 text-xs font-semibold text-emerald-600 flex items-center gap-1 group-hover:translate-x-1 transition-transform">
              <span>View reference categories</span> &rarr;
            </div>
          </Link>

          {/* Card: Network Assets and Stock */}
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
                Manage hardware lifecycle (switches, routers, APs), campus location hierarchy, port mapping, and bulk stock.
              </p>
            </div>
            <div className="mt-6 text-xs font-semibold text-indigo-600 flex items-center gap-1 group-hover:translate-x-1 transition-transform">
              <span>Open asset manager</span> &rarr;
            </div>
          </Link>
        </div>

        {/* Secondary Admin Settings Row */}
        <div className="flex items-center justify-between bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <div>
            <h3 className="text-sm font-bold text-slate-800">Admin Preferences & Settings</h3>
            <p className="text-xs text-slate-500 mt-0.5">Configure email copy notification settings on new student complaint submissions.</p>
          </div>
          <Link
            to="/admin/settings"
            className="px-4 py-2 bg-slate-900 hover:bg-black text-white font-semibold rounded-xl text-xs flex items-center gap-1.5"
          >
            <Settings className="w-4 h-4" />
            <span>Open Settings</span>
          </Link>
        </div>
      </main>
    </div>
  );
};
