// MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
// Technician Workbench page for resolving assigned complaints, issuing stock items, and viewing rating feedback.

import React, { useEffect, useState } from 'react';
import {
  fetchTechnicianComplaints,
  fetchTechnicianComplaintDetail,
  resolveComplaint,
  fetchMyRatings,
  fetchStockItems
} from '../../api/complaints';
import { ComplaintList } from '../../components/complaints/ComplaintList';
import { ComplaintDetail } from '../../components/complaints/ComplaintDetail';
import { StarRating } from '../../components/complaints/StarRating';
import {
  Wrench,
  Inbox,
  CheckCircle2,
  Star,
  Plus,
  Trash2,
  LogOut,
  AlertCircle,
  ArrowLeft
} from 'lucide-react';

export const TechnicianDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'open' | 'closed' | 'ratings'>('open');
  const [complaints, setComplaints] = useState<any[]>([]);
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);
  const [selectedComplaint, setSelectedComplaint] = useState<any>(null);

  // Resolution Form State
  const [diagnosis, setDiagnosis] = useState('');
  const [solution, setSolution] = useState('');
  const [itemsUsed, setItemsUsed] = useState<{ stock_item_id: string; quantity: number }[]>([]);
  const [stockItems, setStockItems] = useState<any[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [resolveError, setResolveError] = useState<string | null>(null);

  // My Ratings
  const [myRatings, setMyRatings] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const loadData = () => {
    setLoading(true);
    if (activeTab === 'ratings') {
      fetchMyRatings()
        .then((res) => setMyRatings(res))
        .finally(() => setLoading(false));
    } else {
      fetchTechnicianComplaints(activeTab)
        .then((res) => setComplaints(res.complaints))
        .finally(() => setLoading(false));
    }
  };

  useEffect(() => {
    loadData();
    fetchStockItems().then((items:any[]) => setStockItems(items)).catch(() => {});
  }, [activeTab]);

  const handleSelectComplaint = async (ticketId: string) => {
    try {
      setLoading(true);
      const data = await fetchTechnicianComplaintDetail(ticketId);
      setSelectedComplaint(data);
      setSelectedTicketId(ticketId);
      // Reset form
      setDiagnosis(data.diagnosis || '');
      setSolution(data.solution || '');
      setItemsUsed([]);
      setResolveError(null);
    } catch (err: any) {
      alert(err.message || 'Failed to load complaint detail');
    } finally {
      setLoading(false);
    }
  };

  const handleAddItem = () => {
    if (stockItems.length === 0) return;
    setItemsUsed((prev) => [...prev, { stock_item_id: stockItems[0]._id, quantity: 1 }]);
  };

  const handleRemoveItem = (idx: number) => {
    setItemsUsed((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleResolveSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTicketId) return;

    if (!diagnosis.trim() || !solution.trim()) {
      setResolveError('Diagnosis and Solution fields are required.');
      return;
    }

    setSubmitting(true);
    setResolveError(null);

    try {
      await resolveComplaint(selectedTicketId, {
        diagnosis,
        solution,
        items_used: itemsUsed
      });
      alert('Complaint resolution submitted and confirmation email sent to student!');
      setSelectedComplaint(null);
      setSelectedTicketId(null);
      loadData();
    } catch (err: any) {
      setResolveError(err.message || 'Failed to submit resolution');
    } finally {
      setSubmitting(false);
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
            <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center font-bold text-mnnit-gold border border-white/20 text-sm">
              MNNIT
            </div>
            <div>
              <h1 className="text-base font-bold">Technician Workbench</h1>
              <p className="text-[11px] text-slate-200">On-Site Network Repair & Stock Dispatch</p>
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
        {selectedComplaint ? (
          <div className="space-y-6">
            <ComplaintDetail
              complaint={selectedComplaint}
              userRole="TECHNICIAN"
              onBack={() => {
                setSelectedComplaint(null);
                setSelectedTicketId(null);
              }}
              onRefresh={() => handleSelectComplaint(selectedComplaint.ticket_id)}
            />

            {/* Resolution Form (if assigned and open) */}
            {(selectedComplaint.status === 'ASSIGNED' || selectedComplaint.status === 'DIAGNOSED') && (
              <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-5">
                <h2 className="text-sm font-bold text-slate-800 flex items-center gap-2 border-b border-slate-100 pb-3">
                  <Wrench className="w-4 h-4 text-emerald-600" />
                  Submit Diagnosis & Solution (Ticket #{selectedComplaint.ticket_id})
                </h2>

                {resolveError && (
                  <div className="p-3 bg-red-50 text-red-700 text-xs flex items-center gap-2 rounded-xl border border-red-100">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    <span>{resolveError}</span>
                  </div>
                )}

                <form onSubmit={handleResolveSubmit} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Technical Diagnosis <span className="text-red-500">*</span>
                    </label>
                    <textarea
                      value={diagnosis}
                      onChange={(e) => setDiagnosis(e.target.value)}
                      rows={3}
                      placeholder="e.g. Blown RJ45 keystone jack in wall socket due to physical cable pull"
                      required
                      className="w-full p-2.5 text-xs border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-600"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Solution Provided (Will be emailed to student) <span className="text-red-500">*</span>
                    </label>
                    <textarea
                      value={solution}
                      onChange={(e) => setSolution(e.target.value)}
                      rows={3}
                      placeholder="e.g. Replaced RJ45 keystone jack in Room 214 and tested LAN connection at 1Gbps speed."
                      required
                      className="w-full p-2.5 text-xs border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-600"
                    />
                  </div>

                  {/* Stock Usage Selector */}
                  <div className="space-y-2 pt-2 border-t border-slate-100">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-semibold text-slate-700">Stock Inventory Used (Optional)</label>
                      <button
                        type="button"
                        onClick={handleAddItem}
                        className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        <span>Add Stock Item</span>
                      </button>
                    </div>

                    {itemsUsed.length > 0 && (
                      <div className="space-y-2">
                        {itemsUsed.map((item, idx) => (
                          <div key={idx} className="flex items-center gap-2">
                            <select
                              value={item.stock_item_id}
                              onChange={(e) => {
                                const newId = e.target.value;
                                setItemsUsed((prev) => prev.map((it, i) => (i === idx ? { ...it, stock_item_id: newId } : it)));
                              }}
                              className="flex-1 p-2 text-xs border border-slate-300 rounded-xl bg-white"
                            >
                              {stockItems.map((st) => (
                                <option key={st._id} value={st._id}>
                                  {st.item_type} ({st.quantity_available} available)
                                </option>
                              ))}
                            </select>

                            <input
                              type="number"
                              min={1}
                              value={item.quantity}
                              onChange={(e) => {
                                const q = parseInt(e.target.value) || 1;
                                setItemsUsed((prev) => prev.map((it, i) => (i === idx ? { ...it, quantity: q } : it)));
                              }}
                              className="w-20 p-2 text-xs border border-slate-300 rounded-xl"
                            />

                            <button
                              type="button"
                              onClick={() => handleRemoveItem(idx)}
                              className="p-2 text-red-500 hover:bg-red-50 rounded-xl"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <button
                    type="submit"
                    disabled={submitting}
                    className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-xl shadow transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {submitting ? 'Submitting Resolution...' : 'Submit Resolution & Notify Student'}
                  </button>
                </form>
              </div>
            )}
          </div>
        ) : (
          <>
            {/* Sub Navigation */}
            <div className="bg-white p-1.5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-2 text-xs font-semibold">
              <button
                onClick={() => setActiveTab('open')}
                className={`px-4 py-2 rounded-xl transition-colors flex items-center gap-1.5 ${
                  activeTab === 'open' ? 'bg-mnnit-blue text-white shadow' : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                <Inbox className="w-4 h-4" />
                <span>My Assigned Complaints (Open)</span>
              </button>

              <button
                onClick={() => setActiveTab('closed')}
                className={`px-4 py-2 rounded-xl transition-colors flex items-center gap-1.5 ${
                  activeTab === 'closed' ? 'bg-mnnit-blue text-white shadow' : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>My Resolved History</span>
              </button>

              <button
                onClick={() => setActiveTab('ratings')}
                className={`px-4 py-2 rounded-xl transition-colors flex items-center gap-1.5 ${
                  activeTab === 'ratings' ? 'bg-mnnit-blue text-white shadow' : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                <Star className="w-4 h-4 text-mnnit-gold" />
                <span>My Service Ratings & Position</span>
              </button>
            </div>

            {/* Content Tabs */}
            {activeTab === 'ratings' ? (
              myRatings && (
                <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                    <div className="bg-amber-50 p-4 rounded-xl border border-amber-200">
                      <span className="text-amber-800 block">Average Rating Score</span>
                      <div className="flex items-center gap-2 mt-1">
                        <StarRating value={Math.round(myRatings.average_rating || 0)} readOnly size={20} />
                        <span className="text-2xl font-bold text-amber-900">{myRatings.average_rating || 'N/A'}</span>
                      </div>
                    </div>

                    <div className="bg-blue-50 p-4 rounded-xl border border-blue-200">
                      <span className="text-blue-800 block">Total Ratings Received</span>
                      <span className="text-2xl font-bold text-blue-900 mt-1 block">{myRatings.rating_count}</span>
                    </div>

                    <div className="bg-purple-50 p-4 rounded-xl border border-purple-200">
                      <span className="text-purple-800 block">Leaderboard Rank Position</span>
                      <span className="text-2xl font-bold text-purple-900 mt-1 block">{myRatings.rank_position}</span>
                    </div>
                  </div>

                  <div>
                    <h3 className="font-bold text-slate-800 border-b border-slate-100 pb-2 mb-3 text-xs">
                      Anonymous Student Feedback History
                    </h3>
                    {myRatings.ratings.length === 0 ? (
                      <p className="text-xs text-slate-400 italic">No rating feedback received yet.</p>
                    ) : (
                      <div className="space-y-3">
                        {myRatings.ratings.map((r: any, idx: number) => (
                          <div key={idx} className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-1">
                            <div className="flex items-center justify-between">
                              <StarRating value={r.rating} readOnly size={16} />
                              <span className="text-[11px] text-slate-400">
                                {new Date(r.created_at).toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata' })}
                              </span>
                            </div>
                            {r.feedback && <p className="text-slate-700 italic pt-1">"{r.feedback}"</p>}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )
            ) : (
              <ComplaintList complaints={complaints} onSelect={handleSelectComplaint} showTechnician={false} />
            )}
          </>
        )}
      </main>
    </div>
  );
};
