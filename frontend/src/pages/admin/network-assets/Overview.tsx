// MODULE: Network Asset and Stock Management - this file belongs to the code for this module.
// Overview dashboard page displaying asset summary cards and report actions.

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchAssetSummary } from '../../../api/networkAssets';
import { NetworkAssetsNav } from '../../../components/network-assets/NetworkAssetsNav';
import {
  Server,
  CheckCircle2,
  AlertTriangle,
  Wrench,
  Boxes,
  FileSpreadsheet,
  Plus,
  ArrowLeft
} from 'lucide-react';

export const Overview: React.FC = () => {
  const [summary, setSummary] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchAssetSummary()
      .then((data) => setSummary(data))
      .catch((err) => console.error(err))
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-slate-100">
      {/* Top Bar Header */}
      <header className="bg-mnnit-blue text-white shadow-md">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/admin" className="p-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <h1 className="text-lg font-bold">Network Asset and Stock Management</h1>
          </div>
          <div className="flex items-center gap-2">
            <a
              href="/api/admin/network-assets/reports/export"
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-1.5 bg-white/10 hover:bg-white/20 text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 transition-colors"
            >
              <FileSpreadsheet className="w-4 h-4" />
              <span>Export CSV</span>
            </a>
            <Link
              to="/admin/network-assets/new"
              className="px-3 py-1.5 bg-mnnit-gold hover:bg-amber-400 text-mnnit-blue text-xs font-bold rounded-lg flex items-center gap-1.5 transition-colors shadow-sm"
            >
              <Plus className="w-4 h-4" />
              <span>Add Asset</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Sub Navigation */}
      <NetworkAssetsNav />

      {/* Main Overview Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {isLoading ? (
          <div className="p-12 text-center text-slate-400 text-sm">Loading summary metrics...</div>
        ) : (
          <div className="space-y-8">
            {/* Top Metric Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Assets</p>
                  <p className="text-2xl font-bold text-slate-900 mt-1">{summary?.total_assets || 0}</p>
                </div>
                <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                  <Server className="w-5 h-5" />
                </div>
              </div>

              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Spare Available</p>
                  <p className="text-2xl font-bold text-emerald-600 mt-1">{summary?.spare_total || 0}</p>
                </div>
                <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
              </div>

              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Faulty Hardware</p>
                  <p className="text-2xl font-bold text-red-600 mt-1">{summary?.faulty_total || 0}</p>
                </div>
                <div className="w-10 h-10 rounded-xl bg-red-50 text-red-600 flex items-center justify-center">
                  <AlertTriangle className="w-5 h-5" />
                </div>
              </div>

              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Under Repair</p>
                  <p className="text-2xl font-bold text-amber-600 mt-1">{summary?.under_repair_total || 0}</p>
                </div>
                <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
                  <Wrench className="w-5 h-5" />
                </div>
              </div>

              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Low Stock Alerts</p>
                  <p className="text-2xl font-bold text-indigo-600 mt-1">{summary?.low_stock_count || 0}</p>
                </div>
                <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
                  <Boxes className="w-5 h-5" />
                </div>
              </div>
            </div>

            {/* Category Breakdown & Status Charts Section */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Category Counts */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
                <h2 className="text-sm font-bold text-slate-800 border-b pb-3">Assets by Category</h2>
                <div className="space-y-2.5">
                  {Object.entries(summary?.by_category || {}).map(([cat, count]: [string, any]) => (
                    <div key={cat} className="flex items-center justify-between text-xs">
                      <span className="font-medium text-slate-700">{cat.replace(/_/g, ' ')}</span>
                      <span className="px-2.5 py-1 rounded-full bg-slate-100 font-bold text-slate-800">{count}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Status Counts */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
                <h2 className="text-sm font-bold text-slate-800 border-b pb-3">Assets by Status</h2>
                <div className="space-y-2.5">
                  {Object.entries(summary?.by_status || {}).map(([st, count]: [string, any]) => (
                    <div key={st} className="flex items-center justify-between text-xs">
                      <span className="font-medium text-slate-700">{st.replace(/_/g, ' ')}</span>
                      <span className="px-2.5 py-1 rounded-full bg-slate-100 font-bold text-slate-800">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
