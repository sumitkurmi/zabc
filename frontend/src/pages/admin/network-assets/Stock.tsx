// MODULE: Network Asset and Stock Management - this file belongs to the code for this module.
// Stock inventory table with low-stock highlighting, Issue/Restock dialogs, and transactions drawer.

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  fetchStockItems,
  createStockItem,
  issueStock,
  restockStock,
  fetchStockTransactions,
  fetchLocationsTree
} from '../../../api/networkAssets';
import { NetworkAssetsNav } from '../../../components/network-assets/NetworkAssetsNav';
import {
  Boxes,
  Plus,
  AlertTriangle,
  ArrowLeft,
  History,
  MinusCircle,
  PlusCircle,
  X
} from 'lucide-react';

export const Stock: React.FC = () => {
  const [items, setItems] = useState<any[]>([]);
  const [locations, setLocations] = useState<any[]>([]);
  const [lowStockOnly, setLowStockOnly] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [toast, setToast] = useState<string | null>(null);

  // Modal dialog states
  const [showAddModal, setShowAddModal] = useState(false);
  const [addForm, setAddForm] = useState({
    item_type: 'LAN Cable Box (305m)',
    make: 'D-Link',
    model: 'Cat6 UTP',
    quantity_available: 10,
    minimum_level: 3,
    store_location_id: ''
  });

  const [issueItem, setIssueItem] = useState<any>(null);
  const [issueQty, setIssueQty] = useState(1);
  const [issueReason, setIssueReason] = useState('Deployment in Hostel Block A');

  const [restockItem, setRestockItem] = useState<any>(null);
  const [restockQty, setRestockQty] = useState(5);

  const [txItem, setTxItem] = useState<any>(null);
  const [transactions, setTransactions] = useState<any[]>([]);

  const loadStock = () => {
    setIsLoading(true);
    fetchStockItems(lowStockOnly)
      .then((data) => setItems(data))
      .catch((err) => console.error(err))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    loadStock();
    fetchLocationsTree().then((data) => {
      const flatten = (nodes: any[]): any[] => {
        let list: any[] = [];
        for (const n of nodes) {
          list.push(n);
          if (n.children && n.children.length > 0) list = list.concat(flatten(n.children));
        }
        return list;
      };
      const flat = flatten(data);
      setLocations(flat);
      if (flat.length > 0 && !addForm.store_location_id) {
        setAddForm((prev) => ({ ...prev, store_location_id: flat[0]._id }));
      }
    });
  }, [lowStockOnly]);

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createStockItem(addForm);
      setToast('Stock item created successfully');
      setShowAddModal(false);
      loadStock();
      setTimeout(() => setToast(null), 4000);
    } catch (err: any) {
      alert(err.message || 'Failed to create stock item');
    }
  };

  const handleIssueSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!issueItem) return;
    try {
      await issueStock(issueItem._id, issueQty, issueReason);
      setToast(`Issued ${issueQty} units of ${issueItem.item_type}`);
      setIssueItem(null);
      loadStock();
      setTimeout(() => setToast(null), 4000);
    } catch (err: any) {
      alert(err.message || 'Failed to issue stock');
    }
  };

  const handleRestockSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!restockItem) return;
    try {
      await restockStock(restockItem._id, restockQty);
      setToast(`Restocked ${restockQty} units of ${restockItem.item_type}`);
      setRestockItem(null);
      loadStock();
      setTimeout(() => setToast(null), 4000);
    } catch (err: any) {
      alert(err.message || 'Failed to restock item');
    }
  };

  const handleViewTransactions = async (item: any) => {
    setTxItem(item);
    try {
      const txs = await fetchStockTransactions(item._id);
      setTransactions(txs);
    } catch (err: any) {
      alert(err.message || 'Failed to load stock movement log');
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
            <h1 className="text-lg font-bold">Stock & Inventory Management</h1>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-3 py-1.5 bg-mnnit-gold hover:bg-amber-400 text-mnnit-blue text-xs font-bold rounded-lg flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Add Stock Item</span>
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

        {/* Filter Toolbar */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm flex items-center justify-between">
          <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-slate-700">
            <input
              type="checkbox"
              checked={lowStockOnly}
              onChange={(e) => setLowStockOnly(e.target.checked)}
              className="rounded text-blue-600 focus:ring-blue-500"
            />
            <span>Show Low Stock Alert Items Only</span>
          </label>
        </div>

        {/* Stock Items Table */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          {isLoading ? (
            <div className="p-12 text-center text-slate-400 text-xs">Loading stock items...</div>
          ) : items.length === 0 ? (
            <div className="p-12 text-center text-slate-500 text-xs">No stock items found.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold">
                    <th className="p-3.5">Item Type</th>
                    <th className="p-3.5">Make / Model</th>
                    <th className="p-3.5">Qty Available</th>
                    <th className="p-3.5">Min Threshold</th>
                    <th className="p-3.5">Stock Status</th>
                    <th className="p-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {items.map((item) => (
                    <tr key={item._id} className={`hover:bg-slate-50 transition-colors ${item.is_low ? 'bg-amber-50/40' : ''}`}>
                      <td className="p-3.5 font-bold text-slate-900">{item.item_type}</td>
                      <td className="p-3.5 text-slate-700">{item.make} {item.model}</td>
                      <td className="p-3.5 font-bold text-base text-slate-900">{item.quantity_available}</td>
                      <td className="p-3.5 text-slate-500">{item.minimum_level}</td>
                      <td className="p-3.5">
                        {item.is_low ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300">
                            <AlertTriangle className="w-3 h-3 text-amber-600" />
                            Low Stock Alert
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            Normal
                          </span>
                        )}
                      </td>
                      <td className="p-3.5 text-right space-x-1.5">
                        <button
                          onClick={() => { setIssueItem(item); setIssueQty(1); }}
                          className="px-2.5 py-1 bg-red-50 hover:bg-red-100 text-red-700 font-semibold rounded-lg text-xs transition-colors border border-red-200"
                        >
                          Issue
                        </button>
                        <button
                          onClick={() => { setRestockItem(item); setRestockQty(5); }}
                          className="px-2.5 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 font-semibold rounded-lg text-xs transition-colors border border-emerald-200"
                        >
                          Restock
                        </button>
                        <button
                          onClick={() => handleViewTransactions(item)}
                          className="p-1 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
                          title="Movement history"
                        >
                          <History className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>

      {/* Add Item Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <form onSubmit={handleAddSubmit} className="bg-white rounded-2xl p-6 max-w-md w-full border border-slate-200 space-y-4 shadow-xl">
            <h3 className="text-sm font-bold text-slate-800">Add Bulk Stock Item</h3>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Item Type *</label>
              <input
                type="text"
                required
                value={addForm.item_type}
                onChange={(e) => setAddForm({ ...addForm, item_type: e.target.value })}
                placeholder="e.g. Cat6 LAN Cable Box or Single-mode SFP"
                className="w-full p-2.5 text-xs border border-slate-300 rounded-xl"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Make</label>
                <input
                  type="text"
                  required
                  value={addForm.make}
                  onChange={(e) => setAddForm({ ...addForm, make: e.target.value })}
                  className="w-full p-2.5 text-xs border border-slate-300 rounded-xl"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Model</label>
                <input
                  type="text"
                  required
                  value={addForm.model}
                  onChange={(e) => setAddForm({ ...addForm, model: e.target.value })}
                  className="w-full p-2.5 text-xs border border-slate-300 rounded-xl"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Initial Qty</label>
                <input
                  type="number"
                  required
                  value={addForm.quantity_available}
                  onChange={(e) => setAddForm({ ...addForm, quantity_available: Number(e.target.value) })}
                  className="w-full p-2.5 text-xs border border-slate-300 rounded-xl"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Min Threshold</label>
                <input
                  type="number"
                  required
                  value={addForm.minimum_level}
                  onChange={(e) => setAddForm({ ...addForm, minimum_level: Number(e.target.value) })}
                  className="w-full p-2.5 text-xs border border-slate-300 rounded-xl"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowAddModal(false)} className="px-4 py-2 border rounded-xl text-xs font-semibold">Cancel</button>
              <button type="submit" className="px-4 py-2 bg-mnnit-blue text-white rounded-xl text-xs font-semibold">Create Item</button>
            </div>
          </form>
        </div>
      )}

      {/* Issue Modal */}
      {issueItem && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <form onSubmit={handleIssueSubmit} className="bg-white rounded-2xl p-6 max-w-md w-full border border-slate-200 space-y-4 shadow-xl">
            <h3 className="text-sm font-bold text-slate-800">Issue Stock: {issueItem.item_type}</h3>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Quantity to Issue (Available: {issueItem.quantity_available})</label>
              <input
                type="number"
                min={1}
                max={issueItem.quantity_available}
                required
                value={issueQty}
                onChange={(e) => setIssueQty(Number(e.target.value))}
                className="w-full p-2.5 text-xs border border-slate-300 rounded-xl"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Deployment Reason *</label>
              <input
                type="text"
                required
                value={issueReason}
                onChange={(e) => setIssueReason(e.target.value)}
                placeholder="Where or why is stock issued?"
                className="w-full p-2.5 text-xs border border-slate-300 rounded-xl"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setIssueItem(null)} className="px-4 py-2 border rounded-xl text-xs font-semibold">Cancel</button>
              <button type="submit" className="px-4 py-2 bg-red-600 text-white rounded-xl text-xs font-semibold">Confirm Issue</button>
            </div>
          </form>
        </div>
      )}

      {/* Restock Modal */}
      {restockItem && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <form onSubmit={handleRestockSubmit} className="bg-white rounded-2xl p-6 max-w-md w-full border border-slate-200 space-y-4 shadow-xl">
            <h3 className="text-sm font-bold text-slate-800">Restock Item: {restockItem.item_type}</h3>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Restock Quantity</label>
              <input
                type="number"
                min={1}
                required
                value={restockQty}
                onChange={(e) => setRestockQty(Number(e.target.value))}
                className="w-full p-2.5 text-xs border border-slate-300 rounded-xl"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setRestockItem(null)} className="px-4 py-2 border rounded-xl text-xs font-semibold">Cancel</button>
              <button type="submit" className="px-4 py-2 bg-emerald-600 text-white rounded-xl text-xs font-semibold">Confirm Restock</button>
            </div>
          </form>
        </div>
      )}

      {/* Transactions Drawer */}
      {txItem && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex justify-end">
          <div className="bg-white max-w-md w-full h-full p-6 space-y-4 overflow-y-auto border-l border-slate-200 shadow-2xl">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-sm font-bold text-slate-800">Stock Movement Audit Log</h3>
              <button onClick={() => setTxItem(null)} className="p-1 text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <p className="text-xs text-slate-500 font-semibold">{txItem.item_type} ({txItem.make} {txItem.model})</p>

            <div className="space-y-3">
              {transactions.length === 0 ? (
                <p className="text-xs text-slate-400 italic">No transactions logged for this item.</p>
              ) : (
                transactions.map((tx) => (
                  <div key={tx._id} className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <span className={`font-bold ${tx.change > 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                        {tx.change > 0 ? `+${tx.change}` : tx.change} units
                      </span>
                      <span className="text-[10px] text-slate-400">{new Date(tx.date).toLocaleString()}</span>
                    </div>
                    <p className="text-slate-700">{tx.reason}</p>
                    <p className="text-[10px] text-slate-400">By {tx.by}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
