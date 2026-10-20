// MODULE: Network Asset and Stock Management - this file belongs to the code for this module.
// Switch port grid display and mapping edit form page.

import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  fetchSwitchPorts,
  bulkCreatePorts,
  updatePort,
  fetchAssetDetail,
  fetchLocationsTree
} from '../../../api/networkAssets';
import { NetworkAssetsNav } from '../../../components/network-assets/NetworkAssetsNav';
import { ArrowLeft, Network, Edit, Plus, Check, X } from 'lucide-react';

export const SwitchPorts: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [switchAsset, setSwitchAsset] = useState<any>(null);
  const [ports, setPorts] = useState<any[]>([]);
  const [locations, setLocations] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [toast, setToast] = useState<string | null>(null);

  // Bulk create state
  const [showBulkModal, setShowBulkModal] = useState(false);
  const [bulkStart, setBulkStart] = useState(1);
  const [bulkEnd, setBulkEnd] = useState(24);
  const [bulkVlan, setBulkVlan] = useState(1);

  // Edit port state
  const [editingPort, setEditingPort] = useState<any>(null);
  const [portForm, setPortForm] = useState({
    status: 'ACTIVE',
    vlan: 1,
    location_id: '',
    patch_panel_id: '',
    patch_panel_port: '',
    notes: ''
  });

  const loadData = () => {
    if (!id) return;
    setIsLoading(true);
    Promise.all([fetchAssetDetail(id), fetchSwitchPorts(id)])
      .then(([sw, pts]) => {
        setSwitchAsset(sw);
        setPorts(pts);
      })
      .catch((err) => console.error(err))
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

  const handleBulkSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    try {
      await bulkCreatePorts(id, bulkStart, bulkEnd, bulkVlan);
      setToast('Switch ports initialized successfully');
      setShowBulkModal(false);
      loadData();
      setTimeout(() => setToast(null), 4000);
    } catch (err: any) {
      alert(err.message || 'Failed to create switch ports');
    }
  };

  const handleEditPort = (port: any) => {
    setEditingPort(port);
    setPortForm({
      status: port.status || 'ACTIVE',
      vlan: port.vlan || 1,
      location_id: port.location_id || '',
      patch_panel_id: port.patch_panel_id || '',
      patch_panel_port: port.patch_panel_port ? String(port.patch_panel_port) : '',
      notes: port.notes || ''
    });
  };

  const handlePortFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingPort) return;
    try {
      await updatePort(editingPort._id, {
        ...portForm,
        patch_panel_port: portForm.patch_panel_port ? Number(portForm.patch_panel_port) : null,
        location_id: portForm.location_id || null
      });
      setToast(`Port #${editingPort.port_number} updated`);
      setEditingPort(null);
      loadData();
      setTimeout(() => setToast(null), 4000);
    } catch (err: any) {
      alert(err.message || 'Failed to update port');
    }
  };

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="bg-mnnit-blue text-white shadow-md">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/admin/network-assets/locations" className="p-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <h1 className="text-lg font-bold">Port Map: {switchAsset?.make} {switchAsset?.model}</h1>
              <p className="text-xs text-slate-300 font-mono">Tag: {switchAsset?.asset_tag} | Total Ports: {switchAsset?.total_ports || 24}</p>
            </div>
          </div>
          <button
            onClick={() => setShowBulkModal(true)}
            className="px-3 py-1.5 bg-mnnit-gold hover:bg-amber-400 text-mnnit-blue text-xs font-bold rounded-lg flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Initialize Ports</span>
          </button>
        </div>
      </header>

      <NetworkAssetsNav />

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        {toast && (
          <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-3.5 rounded-xl text-xs font-semibold">
            {toast}
          </div>
        )}

        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
          <div className="flex items-center justify-between border-b pb-3">
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              <Network className="w-4 h-4 text-blue-600" />
              <span>Switch Port Grid ({ports.length} ports mapped)</span>
            </h2>
          </div>

          {isLoading ? (
            <div className="p-12 text-center text-slate-400 text-xs">Loading port map...</div>
          ) : ports.length === 0 ? (
            <div className="p-12 text-center text-slate-500 text-xs">
              No switch ports created yet. Click "Initialize Ports" to bulk create ports 1 to {switchAsset?.total_ports || 24}.
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
              {ports.map((p) => {
                const isFree = p.status === 'FREE';
                const isFaulty = p.status === 'FAULTY';
                return (
                  <div
                    key={p._id}
                    onClick={() => handleEditPort(p)}
                    className={`p-3 rounded-xl border cursor-pointer transition-all hover:shadow-md ${
                      isFaulty
                        ? 'bg-red-50 border-red-200 text-red-900'
                        : isFree
                        ? 'bg-slate-50 border-slate-200 text-slate-700'
                        : 'bg-emerald-50 border-emerald-200 text-emerald-900'
                    }`}
                  >
                    <div className="flex items-center justify-between font-bold text-xs">
                      <span>Port {p.port_number}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                        isFaulty ? 'bg-red-200 text-red-900' : isFree ? 'bg-slate-200 text-slate-700' : 'bg-emerald-200 text-emerald-900'
                      }`}>
                        {p.status}
                      </span>
                    </div>
                    <div className="text-[11px] mt-2 space-y-0.5 opacity-90">
                      <p>VLAN {p.vlan}</p>
                      {p.notes && <p className="truncate italic">{p.notes}</p>}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>

      {/* Edit Port Modal */}
      {editingPort && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <form onSubmit={handlePortFormSubmit} className="bg-white rounded-2xl p-6 max-w-md w-full border border-slate-200 space-y-4 shadow-xl">
            <h3 className="text-sm font-bold text-slate-800">Edit Port #{editingPort.port_number}</h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Status</label>
                <select
                  value={portForm.status}
                  onChange={(e) => setPortForm({ ...portForm, status: e.target.value })}
                  className="w-full p-2 text-xs border border-slate-300 rounded-xl bg-white"
                >
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="FREE">FREE</option>
                  <option value="FAULTY">FAULTY</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">VLAN ID</label>
                <input
                  type="number"
                  value={portForm.vlan}
                  onChange={(e) => setPortForm({ ...portForm, vlan: Number(e.target.value) })}
                  className="w-full p-2 text-xs border border-slate-300 rounded-xl"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Room Served</label>
              <select
                value={portForm.location_id}
                onChange={(e) => setPortForm({ ...portForm, location_id: e.target.value })}
                className="w-full p-2 text-xs border border-slate-300 rounded-xl bg-white"
              >
                <option value="">Unassigned</option>
                {locations.map((loc) => (
                  <option key={loc._id} value={loc._id}>{loc.path || loc.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Notes</label>
              <input
                type="text"
                value={portForm.notes}
                onChange={(e) => setPortForm({ ...portForm, notes: e.target.value })}
                placeholder="e.g. Connected to Wall Socket #3"
                className="w-full p-2 text-xs border border-slate-300 rounded-xl"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setEditingPort(null)} className="px-4 py-2 border rounded-xl text-xs font-semibold">Cancel</button>
              <button type="submit" className="px-4 py-2 bg-mnnit-blue text-white rounded-xl text-xs font-semibold">Save Changes</button>
            </div>
          </form>
        </div>
      )}

      {/* Bulk Create Modal */}
      {showBulkModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <form onSubmit={handleBulkSubmit} className="bg-white rounded-2xl p-6 max-w-md w-full border border-slate-200 space-y-4 shadow-xl">
            <h3 className="text-sm font-bold text-slate-800">Initialize Switch Ports</h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Start Port</label>
                <input
                  type="number"
                  value={bulkStart}
                  onChange={(e) => setBulkStart(Number(e.target.value))}
                  className="w-full p-2 text-xs border border-slate-300 rounded-xl"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">End Port</label>
                <input
                  type="number"
                  value={bulkEnd}
                  onChange={(e) => setBulkEnd(Number(e.target.value))}
                  className="w-full p-2 text-xs border border-slate-300 rounded-xl"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Default VLAN</label>
              <input
                type="number"
                value={bulkVlan}
                onChange={(e) => setBulkVlan(Number(e.target.value))}
                className="w-full p-2 text-xs border border-slate-300 rounded-xl"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowBulkModal(false)} className="px-4 py-2 border rounded-xl text-xs font-semibold">Cancel</button>
              <button type="submit" className="px-4 py-2 bg-mnnit-blue text-white rounded-xl text-xs font-semibold">Bulk Create</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
