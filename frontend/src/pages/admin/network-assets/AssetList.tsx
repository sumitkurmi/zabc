// MODULE: Network Asset and Stock Management - this file belongs to the code for this module.
// List page for searching, filtering, and managing network assets.

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchAssets, deleteAsset } from '../../../api/networkAssets';
import { NetworkAssetsNav } from '../../../components/network-assets/NetworkAssetsNav';
import {
  Search,
  Plus,
  Eye,
  Trash2,
  ChevronLeft,
  ChevronRight,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  Wrench,
  XCircle,
  Archive
} from 'lucide-react';

const STATUS_BADGES: Record<string, { label: string; className: string; icon: any }> = {
  IN_USE: { label: 'In Use', className: 'bg-emerald-50 text-emerald-700 border-emerald-200', icon: CheckCircle2 },
  SPARE: { label: 'Spare', className: 'bg-blue-50 text-blue-700 border-blue-200', icon: CheckCircle2 },
  FAULTY: { label: 'Faulty', className: 'bg-red-50 text-red-700 border-red-200', icon: AlertTriangle },
  UNDER_REPAIR: { label: 'Under Repair', className: 'bg-amber-50 text-amber-700 border-amber-200', icon: Wrench },
  REPLACED: { label: 'Replaced', className: 'bg-purple-50 text-purple-700 border-purple-200', icon: XCircle },
  RETIRED: { label: 'Retired', className: 'bg-slate-100 text-slate-600 border-slate-200', icon: Archive }
};

export const AssetList: React.FC = () => {
  const [assets, setAssets] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [category, setCategory] = useState('');
  const [status, setStatus] = useState('');
  const [q, setQ] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [toast, setToast] = useState<string | null>(null);

  const loadData = () => {
    setIsLoading(true);
    fetchAssets({ category, status, q, page, limit: 15 })
      .then((data) => {
        setAssets(data.assets);
        setTotal(data.total);
        setPages(data.pages);
      })
      .catch((err) => console.error(err))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    loadData();
  }, [page, category, status]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadData();
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete or retire this asset?')) return;
    try {
      const res = await deleteAsset(id);
      setToast(res.message || 'Asset processed successfully');
      loadData();
      setTimeout(() => setToast(null), 4000);
    } catch (err: any) {
      alert(err.message || 'Failed to delete asset');
    }
  };

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="bg-mnnit-blue text-white shadow-md">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/admin" className="p-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <h1 className="text-lg font-bold">Network Assets Directory</h1>
          </div>
          <Link
            to="/admin/network-assets/new"
            className="px-3 py-1.5 bg-mnnit-gold hover:bg-amber-400 text-mnnit-blue text-xs font-bold rounded-lg flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Add New Asset</span>
          </Link>
        </div>
      </header>

      <NetworkAssetsNav />

      <main className="max-w-7xl mx-auto px-6 py-8">
        {toast && (
          <div className="mb-6 bg-emerald-50 border border-emerald-200 text-emerald-800 p-3.5 rounded-xl text-xs font-semibold shadow-sm">
            {toast}
          </div>
        )}

        {/* Filters */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-4 mb-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <form onSubmit={handleSearch} className="flex-1 w-full flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Search serial, tag, make, or model..."
                className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-600"
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2 bg-mnnit-blue hover:bg-blue-800 text-white rounded-xl text-xs font-semibold shrink-0"
            >
              Search
            </button>
          </form>

          <div className="w-full sm:w-auto flex items-center gap-3">
            <select
              value={category}
              onChange={(e) => { setCategory(e.target.value); setPage(1); }}
              className="p-2 text-xs border border-slate-300 rounded-xl bg-white"
            >
              <option value="">All Categories</option>
              <option value="SWITCH">SWITCH</option>
              <option value="ROUTER">ROUTER</option>
              <option value="ACCESS_POINT">ACCESS POINT</option>
              <option value="FIREWALL">FIREWALL</option>
              <option value="OPTICAL_DEVICE">OPTICAL DEVICE</option>
              <option value="CABLE">CABLE</option>
              <option value="SFP_MODULE">SFP MODULE</option>
              <option value="RACK">RACK</option>
              <option value="PATCH_PANEL">PATCH PANEL</option>
              <option value="UPS">UPS</option>
            </select>

            <select
              value={status}
              onChange={(e) => { setStatus(e.target.value); setPage(1); }}
              className="p-2 text-xs border border-slate-300 rounded-xl bg-white"
            >
              <option value="">All Statuses</option>
              <option value="IN_USE">IN USE</option>
              <option value="SPARE">SPARE</option>
              <option value="FAULTY">FAULTY</option>
              <option value="UNDER_REPAIR">UNDER REPAIR</option>
              <option value="REPLACED">REPLACED</option>
              <option value="RETIRED">RETIRED</option>
            </select>
          </div>
        </div>

        {/* Assets Table */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          {isLoading ? (
            <div className="p-12 text-center text-slate-400 text-xs">Loading assets...</div>
          ) : assets.length === 0 ? (
            <div className="p-12 text-center text-slate-500 text-xs">No assets found.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold">
                    <th className="p-3.5">Asset Tag</th>
                    <th className="p-3.5">Category</th>
                    <th className="p-3.5">Make / Model</th>
                    <th className="p-3.5">Serial Number</th>
                    <th className="p-3.5">Status</th>
                    <th className="p-3.5">Installation Date</th>
                    <th className="p-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {assets.map((asset) => {
                    const badge = STATUS_BADGES[asset.status] || STATUS_BADGES.SPARE;
                    const BadgeIcon = badge.icon;
                    return (
                      <tr key={asset._id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="p-3.5 font-mono font-bold text-slate-900">{asset.asset_tag}</td>
                        <td className="p-3.5 font-semibold text-slate-700">{asset.category}</td>
                        <td className="p-3.5 text-slate-800">{asset.make} {asset.model}</td>
                        <td className="p-3.5 font-mono text-slate-500">{asset.serial_number}</td>
                        <td className="p-3.5">
                          <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full border text-[10px] font-bold ${badge.className}`}>
                            <BadgeIcon className="w-3 h-3" />
                            {badge.label}
                          </span>
                        </td>
                        <td className="p-3.5 text-slate-500">{asset.installation_date || 'N/A'}</td>
                        <td className="p-3.5 text-right space-x-2">
                          <Link
                            to={`/admin/network-assets/${asset._id}`}
                            className="inline-flex items-center gap-1 px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-semibold transition-colors"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            <span>View</span>
                          </Link>
                          <button
                            onClick={() => handleDelete(asset._id)}
                            className="p-1 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="Delete or Retire asset"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          <div className="p-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
            <span>Showing {assets.length} of {total} assets</span>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="p-1 border rounded-lg disabled:opacity-30 hover:bg-white"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span>Page {page} of {pages}</span>
              <button
                disabled={page >= pages}
                onClick={() => setPage((p) => p + 1)}
                className="p-1 border rounded-lg disabled:opacity-30 hover:bg-white"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};
