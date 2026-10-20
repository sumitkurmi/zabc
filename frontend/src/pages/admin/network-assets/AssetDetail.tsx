// MODULE: Network Asset and Stock Management - this file belongs to the code for this module.
// Detail view page displaying asset parameters, warranty status, maintenance records, and status transition dialogs.

import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  fetchAssetDetail,
  changeAssetStatus,
  changeAssetLocation,
  replaceAsset,
  addMaintenanceRecord,
  fetchLocationsTree
} from '../../../api/networkAssets';
import { NetworkAssetsNav } from '../../../components/network-assets/NetworkAssetsNav';
import {
  ArrowLeft,
  Wrench,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  History,
  ShieldCheck,
  ShieldAlert,
  Edit,
  FolderInput
} from 'lucide-react';

export const AssetDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [asset, setAsset] = useState<any>(null);
  const [locations, setLocations] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [toast, setToast] = useState<string | null>(null);

  // Dialog states
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [newStatus, setNewStatus] = useState('IN_USE');
  const [statusReason, setStatusReason] = useState('');

  const [showMoveModal, setShowMoveModal] = useState(false);
  const [targetLocationId, setTargetLocationId] = useState('');

  const [showReplaceModal, setShowReplaceModal] = useState(false);
  const [newAssetId, setNewAssetId] = useState('');
  const [replaceReason, setReplaceReason] = useState('');

  const [showMaintModal, setShowMaintModal] = useState(false);
  const [maintForm, setMaintForm] = useState({
    date: new Date().toISOString().split('T')[0],
    type: 'REPAIR',
    description: '',
    performed_by: 'MNNIT Technician',
    cost: 0
  });

  const loadData = () => {
    if (!id) return;
    setIsLoading(true);
    fetchAssetDetail(id)
      .then((data) => setAsset(data))
      .catch((err) => alert(err.message))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    loadData();
    fetchLocationsTree().then((data) => {
      const flatten = (nodes: any[]): any[] => {
        let list: any[] = [];
        for (const n of nodes) {
          list.push(n);
          if (n.children && n.children.length > 0) list = list.concat(flatten(n.children));
        }
        return list;
      };
      setLocations(flatten(data));
    });
  }, [id]);

  const handleStatusSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !statusReason.trim()) return alert('Reason is required for status changes');
    try {
      await changeAssetStatus(id, newStatus, statusReason);
      setToast('Status updated successfully');
      setShowStatusModal(false);
      setStatusReason('');
      loadData();
      setTimeout(() => setToast(null), 4000);
    } catch (err: any) {
      alert(err.message || 'Failed to update status');
    }
  };

  const handleMoveSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !targetLocationId) return;
    try {
      await changeAssetLocation(id, targetLocationId);
      setToast('Location updated successfully');
      setShowMoveModal(false);
      loadData();
      setTimeout(() => setToast(null), 4000);
    } catch (err: any) {
      alert(err.message || 'Failed to move location');
    }
  };

  const handleReplaceSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !newAssetId) return;
    try {
      await replaceAsset(id, newAssetId, replaceReason);
      setToast('Asset replaced successfully');
      setShowReplaceModal(false);
      loadData();
      setTimeout(() => setToast(null), 4000);
    } catch (err: any) {
      alert(err.message || 'Failed to replace asset');
    }
  };

  const handleMaintSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !maintForm.description.trim()) return;
    try {
      await addMaintenanceRecord(id, maintForm);
      setToast('Maintenance event added to history');
      setShowMaintModal(false);
      loadData();
      setTimeout(() => setToast(null), 4000);
    } catch (err: any) {
      alert(err.message || 'Failed to add maintenance record');
    }
  };

  if (isLoading || !asset) {
    return <div className="p-12 text-center text-slate-400 text-xs">Loading asset record...</div>;
  }

  const isWarrantyActive = asset.warranty?.is_active;

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="bg-mnnit-blue text-white shadow-md">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/admin/network-assets/list" className="p-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <h1 className="text-lg font-bold">{asset.make} {asset.model}</h1>
              <p className="text-xs text-slate-300 font-mono">Tag: {asset.asset_tag} | SN: {asset.serial_number}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Link
              to={`/admin/network-assets/${asset._id}/edit`}
              className="px-3 py-1.5 bg-white/10 hover:bg-white/20 text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 transition-colors"
            >
              <Edit className="w-4 h-4" />
              <span>Edit Asset</span>
            </Link>
          </div>
        </div>
      </header>

      <NetworkAssetsNav />

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        {toast && (
          <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-3.5 rounded-xl text-xs font-semibold">
            {toast}
          </div>
        )}

        {/* Action Header Card */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-blue-50 text-blue-800 border border-blue-200">
              {asset.category}
            </span>
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-800 border border-slate-200">
              Status: {asset.status}
            </span>
            <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold border ${
              isWarrantyActive ? 'bg-emerald-50 text-emerald-800 border-emerald-200' : 'bg-amber-50 text-amber-800 border-amber-200'
            }`}>
              {isWarrantyActive ? <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> : <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />}
              <span>{isWarrantyActive ? 'Warranty Active' : 'Warranty Expired / None'}</span>
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => setShowStatusModal(true)}
              className="px-3 py-1.5 bg-mnnit-blue hover:bg-blue-800 text-white text-xs font-semibold rounded-xl flex items-center gap-1.5"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Change Status</span>
            </button>
            <button
              onClick={() => setShowMoveModal(true)}
              className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold rounded-xl flex items-center gap-1.5"
            >
              <FolderInput className="w-3.5 h-3.5" />
              <span>Move Location</span>
            </button>
            <button
              onClick={() => setShowReplaceModal(true)}
              className="px-3 py-1.5 bg-purple-50 hover:bg-purple-100 text-purple-800 border border-purple-200 text-xs font-semibold rounded-xl flex items-center gap-1.5"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Replace Hardware</span>
            </button>
            <button
              onClick={() => setShowMaintModal(true)}
              className="px-3 py-1.5 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 text-xs font-semibold rounded-xl flex items-center gap-1.5"
            >
              <Wrench className="w-3.5 h-3.5" />
              <span>Log Maintenance</span>
            </button>
          </div>
        </div>

        {/* Details Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider border-b pb-2">Technical Parameters</h2>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div><span className="text-slate-400">Make:</span> <p className="font-semibold text-slate-800">{asset.make}</p></div>
              <div><span className="text-slate-400">Model:</span> <p className="font-semibold text-slate-800">{asset.model}</p></div>
              <div><span className="text-slate-400">Serial:</span> <p className="font-mono text-slate-800">{asset.serial_number}</p></div>
              <div><span className="text-slate-400">Installation Date:</span> <p className="text-slate-800">{asset.installation_date || 'N/A'}</p></div>
              {asset.ip_address && <div><span className="text-slate-400">IP Address:</span> <p className="font-mono text-slate-800">{asset.ip_address}</p></div>}
              {asset.mac_address && <div><span className="text-slate-400">MAC Address:</span> <p className="font-mono text-slate-800">{asset.mac_address}</p></div>}
              {asset.total_ports && <div><span className="text-slate-400">Total Ports:</span> <p className="text-slate-800">{asset.total_ports}</p></div>}
              {asset.replaced_by_id && <div><span className="text-slate-400">Replaced By ID:</span> <p className="font-mono text-purple-700">{asset.replaced_by_id}</p></div>}
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider border-b pb-2">Warranty Metadata</h2>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div><span className="text-slate-400">Vendor:</span> <p className="font-semibold text-slate-800">{asset.warranty?.vendor || 'N/A'}</p></div>
              <div><span className="text-slate-400">Start Date:</span> <p className="text-slate-800">{asset.warranty?.start_date || 'N/A'}</p></div>
              <div><span className="text-slate-400">End Date:</span> <p className="text-slate-800">{asset.warranty?.end_date || 'N/A'}</p></div>
            </div>
          </div>
        </div>

        {/* Maintenance History */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
          <div className="flex items-center justify-between border-b pb-3">
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              <Wrench className="w-4 h-4 text-amber-600" />
              <span>Maintenance & Repair History</span>
            </h2>
          </div>

          {asset.maintenance_history?.length === 0 ? (
            <p className="text-xs text-slate-400 italic">No maintenance events recorded for this asset.</p>
          ) : (
            <div className="divide-y divide-slate-100">
              {asset.maintenance_history?.map((m: any, idx: number) => (
                <div key={idx} className="py-3 flex flex-col sm:flex-row items-start sm:items-center justify-between text-xs gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-800">{m.type}</span>
                      <span className="text-slate-400">• {m.date}</span>
                      <span className="text-slate-500 font-medium">by {m.performed_by}</span>
                    </div>
                    <p className="text-slate-600 mt-1">{m.description}</p>
                  </div>
                  {m.cost && <span className="font-semibold text-slate-700 bg-slate-100 px-2 py-1 rounded">Cost: ₹{m.cost}</span>}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Status History */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
          <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider border-b pb-3 flex items-center gap-1.5">
            <History className="w-4 h-4 text-blue-600" />
            <span>Lifecycle Status Audit Log</span>
          </h2>
          <div className="space-y-3">
            {asset.status_history?.map((s: any, idx: number) => (
              <div key={idx} className="text-xs border-l-2 border-blue-500 pl-3 py-0.5 space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-blue-900">{s.status}</span>
                  <span className="text-[10px] text-slate-400">{new Date(s.changed_at).toLocaleString()}</span>
                  <span className="text-slate-500 font-medium">by {s.changed_by}</span>
                </div>
                <p className="text-slate-600 italic">"{s.reason}"</p>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Change Status Modal */}
      {showStatusModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <form onSubmit={handleStatusSubmit} className="bg-white rounded-2xl p-6 max-w-md w-full border border-slate-200 space-y-4 shadow-xl">
            <h3 className="text-sm font-bold text-slate-800">Transition Asset Lifecycle Status</h3>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">New Status</label>
              <select
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value)}
                className="w-full p-2.5 text-xs border border-slate-300 rounded-xl bg-white"
              >
                <option value="IN_USE">IN USE</option>
                <option value="SPARE">SPARE</option>
                <option value="FAULTY">FAULTY</option>
                <option value="UNDER_REPAIR">UNDER REPAIR</option>
                <option value="REPLACED">REPLACED</option>
                <option value="RETIRED">RETIRED</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Justification Reason *</label>
              <textarea
                required
                rows={3}
                value={statusReason}
                onChange={(e) => setStatusReason(e.target.value)}
                placeholder="Explain why status is changing..."
                className="w-full p-2.5 text-xs border border-slate-300 rounded-xl"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowStatusModal(false)} className="px-4 py-2 border rounded-xl text-xs font-semibold">Cancel</button>
              <button type="submit" className="px-4 py-2 bg-mnnit-blue text-white rounded-xl text-xs font-semibold">Confirm Status</button>
            </div>
          </form>
        </div>
      )}

      {/* Move Location Modal */}
      {showMoveModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <form onSubmit={handleMoveSubmit} className="bg-white rounded-2xl p-6 max-w-md w-full border border-slate-200 space-y-4 shadow-xl">
            <h3 className="text-sm font-bold text-slate-800">Move Asset to New Location</h3>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Target Location</label>
              <select
                required
                value={targetLocationId}
                onChange={(e) => setTargetLocationId(e.target.value)}
                className="w-full p-2.5 text-xs border border-slate-300 rounded-xl bg-white"
              >
                <option value="">Select target location...</option>
                {locations.map((loc) => (
                  <option key={loc._id} value={loc._id}>{loc.path || loc.name}</option>
                ))}
              </select>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowMoveModal(false)} className="px-4 py-2 border rounded-xl text-xs font-semibold">Cancel</button>
              <button type="submit" className="px-4 py-2 bg-mnnit-blue text-white rounded-xl text-xs font-semibold">Move Asset</button>
            </div>
          </form>
        </div>
      )}

      {/* Replace Asset Modal */}
      {showReplaceModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <form onSubmit={handleReplaceSubmit} className="bg-white rounded-2xl p-6 max-w-md w-full border border-slate-200 space-y-4 shadow-xl">
            <h3 className="text-sm font-bold text-slate-800">Link Replacement Asset</h3>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Replacement Asset ID *</label>
              <input
                type="text"
                required
                value={newAssetId}
                onChange={(e) => setNewAssetId(e.target.value)}
                placeholder="Enter Mongo ID of new asset"
                className="w-full p-2.5 text-xs border border-slate-300 rounded-xl"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Replacement Notes</label>
              <input
                type="text"
                value={replaceReason}
                onChange={(e) => setReplaceReason(e.target.value)}
                placeholder="e.g. Upgraded to Gigabit switch"
                className="w-full p-2.5 text-xs border border-slate-300 rounded-xl"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowReplaceModal(false)} className="px-4 py-2 border rounded-xl text-xs font-semibold">Cancel</button>
              <button type="submit" className="px-4 py-2 bg-purple-700 text-white rounded-xl text-xs font-semibold">Confirm Replacement</button>
            </div>
          </form>
        </div>
      )}

      {/* Add Maintenance Modal */}
      {showMaintModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <form onSubmit={handleMaintSubmit} className="bg-white rounded-2xl p-6 max-w-md w-full border border-slate-200 space-y-4 shadow-xl">
            <h3 className="text-sm font-bold text-slate-800">Log Maintenance Event</h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Date</label>
                <input
                  type="date"
                  required
                  value={maintForm.date}
                  onChange={(e) => setMaintForm({ ...maintForm, date: e.target.value })}
                  className="w-full p-2 text-xs border border-slate-300 rounded-xl"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Type</label>
                <select
                  value={maintForm.type}
                  onChange={(e) => setMaintForm({ ...maintForm, type: e.target.value })}
                  className="w-full p-2 text-xs border border-slate-300 rounded-xl bg-white"
                >
                  <option value="REPAIR">REPAIR</option>
                  <option value="SERVICE">SERVICE</option>
                  <option value="REPLACEMENT">REPLACEMENT</option>
                  <option value="INSPECTION">INSPECTION</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Description *</label>
              <textarea
                required
                rows={3}
                value={maintForm.description}
                onChange={(e) => setMaintForm({ ...maintForm, description: e.target.value })}
                placeholder="Work done..."
                className="w-full p-2 text-xs border border-slate-300 rounded-xl"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Performed By</label>
              <input
                type="text"
                value={maintForm.performed_by}
                onChange={(e) => setMaintForm({ ...maintForm, performed_by: e.target.value })}
                className="w-full p-2 text-xs border border-slate-300 rounded-xl"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowMaintModal(false)} className="px-4 py-2 border rounded-xl text-xs font-semibold">Cancel</button>
              <button type="submit" className="px-4 py-2 bg-amber-600 text-white rounded-xl text-xs font-semibold">Log Maintenance</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
