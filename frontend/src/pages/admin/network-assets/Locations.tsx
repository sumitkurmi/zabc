// MODULE: Network Asset and Stock Management - this file belongs to the code for this module.
// Location hierarchy tree and room switch port serving mapping page.

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  fetchLocationsTree,
  createLocation,
  deleteLocation,
  fetchLocationDetail
} from '../../../api/networkAssets';
import { NetworkAssetsNav } from '../../../components/network-assets/NetworkAssetsNav';
import {
  Folder,
  Home,
  Plus,
  Trash2,
  ArrowLeft,
  ChevronRight,
  Server,
  Network
} from 'lucide-react';

export const Locations: React.FC = () => {
  const [tree, setTree] = useState<any[]>([]);
  const [selectedLoc, setSelectedLoc] = useState<any>(null);
  const [locDetail, setLocDetail] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [toast, setToast] = useState<string | null>(null);

  // New location modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [addForm, setAddForm] = useState({
    name: '',
    code: '',
    type: 'HOSTEL',
    parent_id: ''
  });

  const loadTree = () => {
    setIsLoading(true);
    fetchLocationsTree()
      .then((data) => setTree(data))
      .catch((err) => console.error(err))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    loadTree();
  }, []);

  const handleSelectLocation = async (node: any) => {
    setSelectedLoc(node);
    try {
      const detail = await fetchLocationDetail(node._id);
      setLocDetail(detail);
    } catch (err: any) {
      alert(err.message || 'Failed to load location details');
    }
  };

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createLocation({
        ...addForm,
        parent_id: addForm.parent_id || null
      });
      setToast('Location created successfully');
      setShowAddModal(false);
      setAddForm({ name: '', code: '', type: 'HOSTEL', parent_id: '' });
      loadTree();
      setTimeout(() => setToast(null), 4000);
    } catch (err: any) {
      alert(err.message || 'Failed to create location');
    }
  };

  const handleDeleteLoc = async (locId: string) => {
    if (!window.confirm('Delete this location?')) return;
    try {
      await deleteLocation(locId);
      setToast('Location deleted successfully');
      setSelectedLoc(null);
      setLocDetail(null);
      loadTree();
      setTimeout(() => setToast(null), 4000);
    } catch (err: any) {
      alert(err.message || 'Failed to delete location');
    }
  };

  const renderTreeNodes = (nodes: any[]) => {
    return (
      <div className="space-y-1 pl-2">
        {nodes.map((node) => (
          <div key={node._id} className="space-y-1">
            <div
              onClick={() => handleSelectLocation(node)}
              className={`flex items-center justify-between p-2 rounded-xl text-xs cursor-pointer transition-colors ${
                selectedLoc?._id === node._id
                  ? 'bg-blue-600 text-white font-semibold'
                  : 'hover:bg-slate-100 text-slate-800'
              }`}
            >
              <div className="flex items-center gap-2">
                {node.type === 'ROOM' ? <Home className="w-3.5 h-3.5" /> : <Folder className="w-3.5 h-3.5" />}
                <span>{node.name}</span>
                <span className="font-mono text-[10px] opacity-75">({node.code})</span>
              </div>
              <span className="text-[10px] uppercase font-bold opacity-80">{node.type}</span>
            </div>

            {node.children && node.children.length > 0 && (
              <div className="border-l-2 border-slate-200 ml-3 pl-2">
                {renderTreeNodes(node.children)}
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="bg-mnnit-blue text-white shadow-md">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/admin" className="p-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <h1 className="text-lg font-bold">Location Hierarchy & Port Serving Map</h1>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-3 py-1.5 bg-mnnit-gold hover:bg-amber-400 text-mnnit-blue text-xs font-bold rounded-lg flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Add Location</span>
          </button>
        </div>
      </header>

      <NetworkAssetsNav />

      <main className="max-w-7xl mx-auto px-6 py-8">
        {toast && (
          <div className="mb-6 bg-emerald-50 border border-emerald-200 text-emerald-800 p-3.5 rounded-xl text-xs font-semibold">
            {toast}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Location Tree Panel */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 space-y-3 h-fit">
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider border-b pb-2">Campus Hierarchy Tree</h2>
            {isLoading ? (
              <div className="p-4 text-xs text-slate-400">Loading locations...</div>
            ) : tree.length === 0 ? (
              <div className="p-4 text-xs text-slate-400">No locations added yet.</div>
            ) : (
              renderTreeNodes(tree)
            )}
          </div>

          {/* Location Details & Assets / Ports Served Panel */}
          <div className="md:col-span-2 space-y-6">
            {!selectedLoc ? (
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-12 text-center text-slate-400 text-xs">
                Select a location from the hierarchy tree to inspect installed assets and serving switch ports.
              </div>
            ) : (
              <div className="space-y-6">
                {/* Location Header Info */}
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
                  <div>
                    <h2 className="text-base font-bold text-slate-900">{locDetail?.location?.name}</h2>
                    <p className="text-xs text-slate-500">{locDetail?.location?.path} | Code: <span className="font-mono text-slate-800">{locDetail?.location?.code}</span></p>
                  </div>
                  <button
                    onClick={() => handleDeleteLoc(selectedLoc._id)}
                    className="px-3 py-1.5 text-xs bg-red-50 hover:bg-red-100 text-red-700 font-semibold rounded-xl flex items-center gap-1 border border-red-200 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Delete Location</span>
                  </button>
                </div>

                {/* Installed Assets */}
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
                  <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5 border-b pb-2">
                    <Server className="w-4 h-4 text-blue-600" />
                    <span>Installed Hardware Assets ({locDetail?.assets?.length || 0})</span>
                  </h3>
                  {locDetail?.assets?.length === 0 ? (
                    <p className="text-xs text-slate-400 italic">No assets currently installed in this location.</p>
                  ) : (
                    <div className="divide-y divide-slate-100">
                      {locDetail?.assets?.map((a: any) => (
                        <div key={a._id} className="py-2.5 flex items-center justify-between text-xs">
                          <div>
                            <Link to={`/admin/network-assets/${a._id}`} className="font-bold text-blue-600 hover:underline">
                              {a.make} {a.model}
                            </Link>
                            <span className="text-slate-400 ml-2">({a.category})</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-slate-500">Tag: {a.asset_tag}</span>
                            {a.category === 'SWITCH' && (
                              <Link
                                to={`/admin/network-assets/switches/${a._id}/ports`}
                                className="px-2 py-0.5 bg-blue-50 text-blue-700 font-semibold rounded text-[10px] border border-blue-200"
                              >
                                View Port Map
                              </Link>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Switch Ports Serving this Location */}
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
                  <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5 border-b pb-2">
                    <Network className="w-4 h-4 text-emerald-600" />
                    <span>Switch Ports Serving this Location ({locDetail?.ports?.length || 0})</span>
                  </h3>
                  {locDetail?.ports?.length === 0 ? (
                    <p className="text-xs text-slate-400 italic">No switch ports currently mapped to serve this location.</p>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {locDetail?.ports?.map((p: any) => (
                        <div key={p._id} className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-1">
                          <div className="flex items-center justify-between font-bold text-slate-800">
                            <span>Port #{p.port_number}</span>
                            <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-emerald-100 text-emerald-800">{p.status}</span>
                          </div>
                          <p className="text-slate-500">VLAN {p.vlan} {p.notes ? `• ${p.notes}` : ''}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Add Location Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <form onSubmit={handleAddSubmit} className="bg-white rounded-2xl p-6 max-w-md w-full border border-slate-200 space-y-4 shadow-xl">
            <h3 className="text-sm font-bold text-slate-800">Add New Campus Location</h3>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Location Name *</label>
              <input
                type="text"
                required
                value={addForm.name}
                onChange={(e) => setAddForm({ ...addForm, name: e.target.value })}
                placeholder="e.g. Room 214 or Hostel Block A"
                className="w-full p-2.5 text-xs border border-slate-300 rounded-xl"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Unique Location Code *</label>
              <input
                type="text"
                required
                value={addForm.code}
                onChange={(e) => setAddForm({ ...addForm, code: e.target.value })}
                placeholder="e.g. HBA-R214"
                className="w-full p-2.5 text-xs border border-slate-300 rounded-xl"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Type</label>
                <select
                  value={addForm.type}
                  onChange={(e) => setAddForm({ ...addForm, type: e.target.value })}
                  className="w-full p-2.5 text-xs border border-slate-300 rounded-xl bg-white"
                >
                  <option value="HOSTEL">HOSTEL</option>
                  <option value="BUILDING">BUILDING</option>
                  <option value="LAB">LAB</option>
                  <option value="ROOM">ROOM</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Parent Location</label>
                <select
                  value={addForm.parent_id}
                  onChange={(e) => setAddForm({ ...addForm, parent_id: e.target.value })}
                  className="w-full p-2.5 text-xs border border-slate-300 rounded-xl bg-white"
                >
                  <option value="">None (Top Level)</option>
                  {tree.map((loc) => (
                    <option key={loc._id} value={loc._id}>{loc.name} ({loc.code})</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowAddModal(false)} className="px-4 py-2 border rounded-xl text-xs font-semibold">Cancel</button>
              <button type="submit" className="px-4 py-2 bg-mnnit-blue text-white rounded-xl text-xs font-semibold">Create Location</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
