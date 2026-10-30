// MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
// Manager Dashboard page providing complaint queues, assignment, technician status, reports, and leaderboard.

import React, { useEffect, useState } from 'react';
import {
  fetchManagerSummary,
  fetchManagerComplaints,
  fetchManagerReports,
  fetchLeaderboard,
  fetchTechnicians,
  toggleTechnicianAvailability,
  fetchComplaintDetail
} from '../../api/complaints';
import { ComplaintList } from '../../components/complaints/ComplaintList';
import { ComplaintDetail } from '../../components/complaints/ComplaintDetail';
import { StarRating } from '../../components/complaints/StarRating';
import {
  LayoutDashboard,
  Inbox,
  Clock,
  CheckCircle2,
  Users,
  BarChart3,
  Trophy,
  Search,
  Filter,
  RefreshCw,
  LogOut,
  Shield,
  MapPin,
  AlertTriangle
} from 'lucide-react';

import logo from '../../assets/logo.jpeg'

export const ManagerDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'queue' | 'techs' | 'reports' | 'leaderboard'>('queue');
  const [queueView, setQueueView] = useState<'open_unassigned' | 'open' | 'closed' | 'all'>('open');
  const [summary, setSummary] = useState<any>(null);
  const [complaints, setComplaints] = useState<any[]>([]);
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);
  const [selectedComplaint, setSelectedComplaint] = useState<any>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [problemTypeFilter, setProblemTypeFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [locationFilter, setLocationFilter] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);

  // Technicians & Leaderboard
  const [technicians, setTechnicians] = useState<any[]>([]);
  const [leaderboard, setLeaderboard] = useState<any[]>([]);
  const [reports, setReports] = useState<any>(null);
  const [reportRange, setReportRange] = useState('today');

  const userRole = localStorage.getItem('staff_role') || 'MANAGER';

  const loadData = () => {
    setLoading(true);
    fetchManagerSummary().then((data) => setSummary(data)).catch(() => {});

    if (activeTab === 'queue') {
      fetchManagerComplaints({
        view: queueView,
        priority: priorityFilter || undefined,
        problem_type: problemTypeFilter || undefined,
        location: locationFilter || undefined,
        q: searchQuery || undefined,
        page,
        limit: 15
      })
        .then((res) => {
          setComplaints(res.complaints);
          setTotalPages(res.pages);
        })
        .finally(() => setLoading(false));
    } else if (activeTab === 'techs') {
      fetchTechnicians()
        .then((res) => setTechnicians(res))
        .finally(() => setLoading(false));
    } else if (activeTab === 'reports') {
      fetchManagerReports(reportRange)
        .then((res) => setReports(res))
        .finally(() => setLoading(false));
    } else if (activeTab === 'leaderboard') {
      fetchLeaderboard()
        .then((res) => setLeaderboard(res))
        .finally(() => setLoading(false));
    }
  };

  useEffect(() => {
    loadData();
  }, [activeTab, queueView, priorityFilter, problemTypeFilter, locationFilter, page, reportRange]);

  const handleSelectComplaint = async (ticketId: string) => {
    try {
      setLoading(true);
      const data = await fetchComplaintDetail(ticketId);
      setSelectedComplaint(data);
      setSelectedTicketId(ticketId);
    } catch (err: any) {
      alert(err.message || 'Failed to load complaint details');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleAvailability = async (techId: string, currentAvail: string) => {
    const targetAvail = currentAvail === 'AVAILABLE' ? 'UNAVAILABLE' : 'AVAILABLE';
    try {
      await toggleTechnicianAvailability(techId, targetAvail, false);
      loadData();
    } catch (err: any) {
      if (err.status === 409 || err.message?.includes('open assigned complaint')) {
        if (window.confirm(`${err.message}\nDo you still want to force mark this technician UNAVAILABLE?`)) {
          await toggleTechnicianAvailability(techId, targetAvail, true);
          loadData();
        }
      } else {
        alert(err.message || 'Failed to toggle availability');
      }
    }
  };

  const handleLogout = () => {
    document.cookie = 'staff_token=; path=/; max-age=0';
    document.cookie = 'admin_token=; path=/; max-age=0';
    localStorage.removeItem('staff_token');
    localStorage.removeItem('staff_role');
    window.location.href = '/login';
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col">
      {/* Top Header */}
      <header className="bg-mnnit-blue text-white shadow-md sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img
              src={logo}
              alt="MNNIT Allahabad Logo"
              className="w-10 h-10 rounded-xl object-contain bg-white p-0.5 border border-white/20 shadow-sm"
            />
            <div>
              <h1 className="text-base font-bold">Manager Operations Dashboard</h1>
              <p className="text-[11px] text-slate-200">Network Complaint Lifecycle & Dispatch</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <a
              href="/admin/network-assets"
              className="px-3 py-1.5 bg-white/10 hover:bg-white/20 rounded-xl text-xs font-semibold border border-white/20 transition-colors"
            >
              Network Assets (Read-Only)
            </a>
            <button
              onClick={handleLogout}
              className="p-2 bg-white/10 hover:bg-red-500/80 rounded-xl text-white transition-colors"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 py-6 w-full space-y-6">
        {/* Detail View Mode */}
        {selectedComplaint ? (
          <ComplaintDetail
            complaint={selectedComplaint}
            userRole={userRole}
            onBack={() => {
              setSelectedComplaint(null);
              setSelectedTicketId(null);
            }}
            onRefresh={() => handleSelectComplaint(selectedComplaint.ticket_id)}
          />
        ) : (
          <>
            {/* Summary Metrics Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div
                onClick={() => {
                  setActiveTab('queue');
                  setQueueView('open_unassigned');
                }}
                className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm cursor-pointer hover:border-blue-400 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500">Unassigned Queue</span>
                  <div className="p-2 bg-amber-50 text-amber-600 rounded-xl">
                    <Inbox className="w-5 h-5" />
                  </div>
                </div>
                <div className="text-2xl font-bold text-slate-900 mt-2">{summary?.open_unassigned ?? 0}</div>
                {summary?.by_priority && (
                  <div className="flex gap-1.5 mt-2 text-[10px] font-bold">
                    <span className="text-red-700 bg-red-50 px-1.5 py-0.5 rounded">{summary.by_priority.CRITICAL || 0} CRITICAL</span>
                    <span className="text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded">{summary.by_priority.HIGH || 0} HIGH</span>
                  </div>
                )}
              </div>

              <div
                onClick={() => {
                  setActiveTab('queue');
                  setQueueView('open');
                }}
                className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm cursor-pointer hover:border-blue-400 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500">Total Open Complaints</span>
                  <div className="p-2 bg-blue-50 text-blue-600 rounded-xl">
                    <Clock className="w-5 h-5" />
                  </div>
                </div>
                <div className="text-2xl font-bold text-slate-900 mt-2">{summary?.all_open ?? 0}</div>
              </div>

              <div
                onClick={() => {
                  setActiveTab('queue');
                  setQueueView('closed');
                }}
                className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm cursor-pointer hover:border-blue-400 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500">Closed Today</span>
                  <div className="p-2 bg-emerald-50 text-emerald-600 rounded-xl">
                    <CheckCircle2 className="w-5 h-5" />
                  </div>
                </div>
                <div className="text-2xl font-bold text-slate-900 mt-2">{summary?.closed_today ?? 0}</div>
              </div>

              <div
                onClick={() => setActiveTab('techs')}
                className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm cursor-pointer hover:border-blue-400 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500">Technician Fleet</span>
                  <div className="p-2 bg-purple-50 text-purple-600 rounded-xl">
                    <Users className="w-5 h-5" />
                  </div>
                </div>
                <div className="text-xs font-semibold text-purple-700 mt-2">Manage Status & Availability</div>
              </div>
            </div>

            {/* Navigation Sub-Tabs */}
            <div className="bg-white p-1.5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-2 overflow-x-auto text-xs font-semibold">
              <button
                onClick={() => setActiveTab('queue')}
                className={`px-4 py-2 rounded-xl transition-colors flex items-center gap-1.5 ${
                  activeTab === 'queue' ? 'bg-mnnit-blue text-white shadow' : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                <Inbox className="w-4 h-4" />
                <span>Complaints Queue</span>
              </button>

              <button
                onClick={() => setActiveTab('techs')}
                className={`px-4 py-2 rounded-xl transition-colors flex items-center gap-1.5 ${
                  activeTab === 'techs' ? 'bg-mnnit-blue text-white shadow' : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                <Users className="w-4 h-4" />
                <span>Technician Availability</span>
              </button>

              <button
                onClick={() => setActiveTab('reports')}
                className={`px-4 py-2 rounded-xl transition-colors flex items-center gap-1.5 ${
                  activeTab === 'reports' ? 'bg-mnnit-blue text-white shadow' : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                <BarChart3 className="w-4 h-4" />
                <span>Analytics & Reports</span>
              </button>

              <button
                onClick={() => setActiveTab('leaderboard')}
                className={`px-4 py-2 rounded-xl transition-colors flex items-center gap-1.5 ${
                  activeTab === 'leaderboard' ? 'bg-mnnit-blue text-white shadow' : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                <Trophy className="w-4 h-4 text-mnnit-gold" />
                <span>Technician Leaderboard</span>
              </button>
            </div>

            {/* Tab 1: Queue */}
            {activeTab === 'queue' && (
              <div className="space-y-4">
                {/* Search and Filters Bar */}
                <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4 text-xs">
                  <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto">
                    {(['open', 'open_unassigned', 'closed', 'all'] as const).map((vw) => (
                      <button
                        key={vw}
                        onClick={() => {
                          setQueueView(vw);
                          setPage(1);
                        }}
                        className={`px-3 py-1.5 rounded-xl capitalize font-semibold transition-colors shrink-0 ${
                          queueView === vw ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        }`}
                      >
                        {vw.replace('_', ' ')}
                      </button>
                    ))}
                  </div>

                  <div className="flex items-center gap-2 w-full md:w-auto flex-wrap">
                    <select
                      value={priorityFilter}
                      onChange={(e) => { setPriorityFilter(e.target.value); setPage(1); }}
                      className="px-2.5 py-1.5 border border-slate-300 rounded-xl bg-white text-xs font-semibold"
                    >
                      <option value="">All Priorities</option>
                      <option value="CRITICAL">CRITICAL</option>
                      <option value="HIGH">HIGH</option>
                      <option value="MEDIUM">MEDIUM</option>
                      <option value="LOW">LOW</option>
                    </select>

                    <select
                      value={problemTypeFilter}
                      onChange={(e) => { setProblemTypeFilter(e.target.value); setPage(1); }}
                      className="px-2.5 py-1.5 border border-slate-300 rounded-xl bg-white text-xs font-semibold"
                    >
                      <option value="">All Categories</option>
                      <option value="WIFI_PROBLEM">WIFI PROBLEM</option>
                      <option value="LAN_PROBLEM">LAN PROBLEM</option>
                      <option value="IP_ADDRESS_ISSUE">I.P ADDRESS ISSUE</option>
                      <option value="PROXY_ISSUE">PROXY ISSUE</option>
                      <option value="LAN_PORT_BROKEN">LAN PORT BROKEN</option>
                    </select>

                    <div className="relative flex-1 md:w-56">
                      <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
                      <input
                        type="text"
                        placeholder="Search ticket # or student..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && loadData()}
                        className="w-full pl-8 pr-3 py-1.5 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-600"
                      />
                    </div>
                    <button
                      onClick={loadData}
                      className="p-2 bg-slate-100 hover:bg-slate-200 rounded-xl text-slate-600 shrink-0"
                    >
                      <RefreshCw className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Complaint Table */}
                <ComplaintList complaints={complaints} onSelect={handleSelectComplaint} />
              </div>
            )}

            {/* Tab 2: Technicians Availability */}
            {activeTab === 'techs' && (
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden p-6 space-y-4">
                <h2 className="text-sm font-bold text-slate-800 flex items-center gap-2 border-b border-slate-100 pb-3">
                  <Users className="w-4 h-4 text-blue-600" />
                  Technician Fleet Status & Dispatch Availability
                </h2>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase">
                        <th className="p-3">Technician Name</th>
                        <th className="p-3">Username</th>
                        <th className="p-3">Assigned Zones</th>
                        <th className="p-3">Open Tickets</th>
                        <th className="p-3">Availability</th>
                        <th className="p-3 text-right">Toggle Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {technicians.map((t) => (
                        <tr key={t._id} className="hover:bg-slate-50">
                          <td className="p-3 font-semibold text-slate-900">{t.full_name}</td>
                          <td className="p-3 font-mono text-slate-500">{t.username}</td>
                          <td className="p-3 text-slate-600">{t.zones?.join(', ') || 'All Campus Zones'}</td>
                          <td className="p-3 font-bold text-blue-700">{t.open_complaints_count} open</td>
                          <td className="p-3">
                            <span
                              className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${
                                t.availability === 'AVAILABLE'
                                  ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                                  : 'bg-slate-100 text-slate-600 border-slate-300'
                              }`}
                            >
                              {t.availability}
                            </span>
                          </td>
                          <td className="p-3 text-right">
                            <button
                              onClick={() => handleToggleAvailability(t._id, t.availability)}
                              className="px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-lg text-xs"
                            >
                              Set {t.availability === 'AVAILABLE' ? 'Unavailable' : 'Available'}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Tab 3: Reports */}
            {activeTab === 'reports' && reports && (
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-6">
                <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                  <h2 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-blue-600" />
                    Analytics & Performance Report
                  </h2>
                  <select
                    value={reportRange}
                    onChange={(e) => setReportRange(e.target.value)}
                    className="p-2 border border-slate-300 rounded-xl text-xs font-semibold bg-white"
                  >
                    <option value="today">Today (IST)</option>
                    <option value="weekly">Last 7 Days</option>
                    <option value="all">All-Time Cumulative</option>
                  </select>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                    <span className="text-slate-500 block">Total Received</span>
                    <span className="text-2xl font-bold text-slate-900 mt-1 block">{reports.total_complaints}</span>
                  </div>
                  <div className="bg-emerald-50 p-4 rounded-xl border border-emerald-200">
                    <span className="text-emerald-700 block">Total Resolved</span>
                    <span className="text-2xl font-bold text-emerald-900 mt-1 block">{reports.total_resolved}</span>
                  </div>
                  <div className="bg-blue-50 p-4 rounded-xl border border-blue-200">
                    <span className="text-blue-700 block">Avg Resolution Time</span>
                    <span className="text-2xl font-bold text-blue-900 mt-1 block">{reports.avg_resolution_hours} Hours</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
                  <div>
                    <h3 className="font-bold text-slate-700 mb-2">Complaints by Problem Type</h3>
                    <ul className="divide-y divide-slate-100 border border-slate-200 rounded-xl bg-slate-50/50 overflow-hidden">
                      {Object.entries(reports.by_problem_type || {}).map(([pt, cnt]: any) => (
                        <li key={pt} className="p-2.5 flex justify-between">
                          <span>{pt.replace(/_/g, ' ')}</span>
                          <span className="font-bold text-slate-800">{cnt}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <h3 className="font-bold text-slate-700 mb-2">Complaints by Location</h3>
                    <ul className="divide-y divide-slate-100 border border-slate-200 rounded-xl bg-slate-50/50 overflow-hidden">
                      {Object.entries(reports.by_location || {}).map(([loc, cnt]: any) => (
                        <li key={loc} className="p-2.5 flex justify-between">
                          <span>{loc}</span>
                          <span className="font-bold text-slate-800">{cnt}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* Tab 4: Leaderboard */}
            {activeTab === 'leaderboard' && (
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden p-6 space-y-4">
                <h2 className="text-sm font-bold text-slate-800 flex items-center gap-2 border-b border-slate-100 pb-3">
                  <Trophy className="w-4 h-4 text-mnnit-gold" />
                  Technician Quality & Performance Leaderboard
                </h2>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase">
                        <th className="p-3">Rank</th>
                        <th className="p-3">Technician Name</th>
                        <th className="p-3">Average Rating</th>
                        <th className="p-3">Rating Count</th>
                        <th className="p-3">Resolved Count</th>
                        <th className="p-3 text-right">Computed Score</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {leaderboard.map((lb) => (
                        <tr key={lb.technician_id} className="hover:bg-slate-50">
                          <td className="p-3 font-mono font-bold text-slate-700">#{lb.rank}</td>
                          <td className="p-3 font-semibold text-slate-900">{lb.name}</td>
                          <td className="p-3">
                            {lb.average_rating ? (
                              <div className="flex items-center gap-2">
                                <StarRating value={Math.round(lb.average_rating)} readOnly size={16} />
                                <span className="font-bold text-amber-700">{lb.average_rating}</span>
                              </div>
                            ) : (
                              <span className="text-slate-400 italic">Unrated</span>
                            )}
                          </td>
                          <td className="p-3 font-semibold text-slate-700">{lb.rating_count} ratings</td>
                          <td className="p-3 font-bold text-emerald-700">{lb.resolved_count} closed</td>
                          <td className="p-3 text-right font-mono font-bold text-blue-700 text-sm">{lb.score}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
};
