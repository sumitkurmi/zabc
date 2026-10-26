// MODULE: Network Asset and Stock Management - this file belongs to the code for this module.
// Dynamic form component for creating or editing network assets based on category selection.

import React, { useEffect, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { createAsset, fetchAssetDetail, updateAsset, fetchLocationsTree } from '../../../api/networkAssets';
import { NetworkAssetsNav } from '../../../components/network-assets/NetworkAssetsNav';
import { ArrowLeft, Save } from 'lucide-react';

export const AssetForm: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const isEdit = Boolean(id);
  const navigate = useNavigate();

  const [locations, setLocations] = useState<any[]>([]);
  const [category, setCategory] = useState<string>('SWITCH');
  const [formData, setFormData] = useState<any>({
    asset_tag: '',
    make: '',
    model: '',
    serial_number: '',
    location_id: '',
    installation_date: new Date().toISOString().split('T')[0],
    installed_by: 'Admin',
    status: 'SPARE',
    warranty: { start_date: '', end_date: '', vendor: '' },
    ip_address: '',
    mac_address: '',
    firmware_version: '',
    total_ports: 24,
    ssid_list: '',
    coverage_area: '',
    device_type: 'MEDIA_CONVERTER',
    cable_type: 'LAN',
    length_m: 1.0,
    speed: '1Gbps',
    wavelength: '850nm',
    units: 42,
    port_count: 24,
    capacity_va: 1000
  });

  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetchLocationsTree()
      .then((data) => {
        const flatten = (nodes: any[]): any[] => {
          let list: any[] = [];
          for (const n of nodes) {
            list.push(n);
            if (n.children && n.children.length > 0) {
              list = list.concat(flatten(n.children));
            }
          }
          return list;
        };
        const flat = flatten(data);
        setLocations(flat);
        if (flat.length > 0 && !formData.location_id) {
          setFormData((prev: any) => ({ ...prev, location_id: flat[0]._id }));
        }
      })
      .catch((err) => console.error(err));

    if (isEdit && id) {
      setIsLoading(true);
      fetchAssetDetail(id)
        .then((data) => {
          setCategory(data.category);
          setFormData({
            ...data,
            ssid_list: Array.isArray(data.ssid_list) ? data.ssid_list.join(', ') : data.ssid_list || '',
            warranty: data.warranty || { start_date: '', end_date: '', vendor: '' }
          });
        })
        .catch((err) => alert(err.message))
        .finally(() => setIsLoading(false));
    }
  }, [id, isEdit]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    if (name.startsWith('warranty.')) {
      const field = name.split('.')[1];
      setFormData((prev: any) => ({
        ...prev,
        warranty: { ...prev.warranty, [field]: value }
      }));
    } else {
      setFormData((prev: any) => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsLoading(true);
      const payload = {
        ...formData,
        category,
        ssid_list: typeof formData.ssid_list === 'string'
          ? formData.ssid_list.split(',').map((s: string) => s.trim()).filter(Boolean)
          : formData.ssid_list
      };

      if (isEdit && id) {
        await updateAsset(id, payload);
      } else {
        await createAsset(payload);
      }
      navigate('/admin/network-assets/list');
    } catch (err: any) {
      alert(err.message || 'Error saving asset');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="bg-mnnit-blue text-white shadow-md">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/admin/network-assets/list" className="p-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <h1 className="text-lg font-bold">{isEdit ? 'Edit Asset' : 'Add New Network Asset'}</h1>
          </div>
        </div>
      </header>

      <NetworkAssetsNav />

      <main className="max-w-4xl mx-auto px-6 py-8">
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Category Select */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Asset Category</label>
              <select
                disabled={isEdit}
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full p-2.5 text-xs border border-slate-300 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 font-semibold"
              >
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
            </div>

            {/* Common Required Fields */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 border-t pt-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Asset Tag *</label>
                <input
                  type="text"
                  name="asset_tag"
                  required
                  value={formData.asset_tag}
                  onChange={handleChange}
                  placeholder="e.g. MNNIT-SW-001"
                  className="w-full p-2.5 text-xs border border-slate-300 rounded-xl"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Serial Number *</label>
                <input
                  type="text"
                  name="serial_number"
                  required
                  value={formData.serial_number}
                  onChange={handleChange}
                  placeholder="e.g. SN-987654321"
                  className="w-full p-2.5 text-xs border border-slate-300 rounded-xl"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Make / Brand *</label>
                <input
                  type="text"
                  name="make"
                  required
                  value={formData.make}
                  onChange={handleChange}
                  placeholder="e.g. Cisco / Aruba / D-Link"
                  className="w-full p-2.5 text-xs border border-slate-300 rounded-xl"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Model *</label>
                <input
                  type="text"
                  name="model"
                  required
                  value={formData.model}
                  onChange={handleChange}
                  placeholder="e.g. Catalyst 2960"
                  className="w-full p-2.5 text-xs border border-slate-300 rounded-xl"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Installation Location *</label>
                <select
                  name="location_id"
                  required
                  value={formData.location_id}
                  onChange={handleChange}
                  className="w-full p-2.5 text-xs border border-slate-300 rounded-xl bg-white"
                >
                  {locations.map((loc) => (
                    <option key={loc._id} value={loc._id}>
                      {loc.path || loc.name} ({loc.type})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Status</label>
                <select
                  name="status"
                  value={formData.status}
                  onChange={handleChange}
                  className="w-full p-2.5 text-xs border border-slate-300 rounded-xl bg-white"
                >
                  <option value="SPARE">SPARE</option>
                  <option value="IN_USE">IN USE</option>
                  <option value="FAULTY">FAULTY</option>
                  <option value="UNDER_REPAIR">UNDER REPAIR</option>
                  <option value="REPLACED">REPLACED</option>
                  <option value="RETIRED">RETIRED</option>
                </select>
              </div>
            </div>

            {/* Category Specific Extra Fields */}
            {['SWITCH', 'ROUTER', 'ACCESS_POINT', 'FIREWALL', 'OPTICAL_DEVICE'].includes(category) && (
              <div className="border-t pt-4 space-y-4">
                <h3 className="text-xs font-bold text-slate-800">Network Attributes</h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">IP Address</label>
                    <input
                      type="text"
                      name="ip_address"
                      value={formData.ip_address}
                      onChange={handleChange}
                      placeholder="172.16.x.x"
                      className="w-full p-2.5 text-xs border border-slate-300 rounded-xl"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">MAC Address</label>
                    <input
                      type="text"
                      name="mac_address"
                      value={formData.mac_address}
                      onChange={handleChange}
                      placeholder="AA:BB:CC:DD:EE:FF"
                      className="w-full p-2.5 text-xs border border-slate-300 rounded-xl"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Firmware Version</label>
                    <input
                      type="text"
                      name="firmware_version"
                      value={formData.firmware_version}
                      onChange={handleChange}
                      placeholder="v15.2(4)E"
                      className="w-full p-2.5 text-xs border border-slate-300 rounded-xl"
                    />
                  </div>
                </div>
              </div>
            )}

            {category === 'SWITCH' && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Total Switch Ports</label>
                  <input
                    type="number"
                    name="total_ports"
                    value={formData.total_ports}
                    onChange={handleChange}
                    className="w-full p-2.5 text-xs border border-slate-300 rounded-xl"
                  />
                </div>
              </div>
            )}

            {category === 'ACCESS_POINT' && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">SSIDs (comma separated)</label>
                  <input
                    type="text"
                    name="ssid_list"
                    value={formData.ssid_list}
                    onChange={handleChange}
                    placeholder="MNNIT-WiFi, MNNIT-Faculty"
                    className="w-full p-2.5 text-xs border border-slate-300 rounded-xl"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Coverage Area</label>
                  <input
                    type="text"
                    name="coverage_area"
                    value={formData.coverage_area}
                    onChange={handleChange}
                    placeholder="Hostel Block A 2nd Floor"
                    className="w-full p-2.5 text-xs border border-slate-300 rounded-xl"
                  />
                </div>
              </div>
            )}

            {/* Warranty Info */}
            <div className="border-t pt-4">
              <h3 className="text-xs font-bold text-slate-800 mb-3">Warranty Metadata</h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Start Date</label>
                  <input
                    type="date"
                    name="warranty.start_date"
                    value={formData.warranty?.start_date || ''}
                    onChange={handleChange}
                    className="w-full p-2.5 text-xs border border-slate-300 rounded-xl"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">End Date</label>
                  <input
                    type="date"
                    name="warranty.end_date"
                    value={formData.warranty?.end_date || ''}
                    onChange={handleChange}
                    className="w-full p-2.5 text-xs border border-slate-300 rounded-xl"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Vendor</label>
                  <input
                    type="text"
                    name="warranty.vendor"
                    value={formData.warranty?.vendor || ''}
                    onChange={handleChange}
                    placeholder="e.g. Cisco India Ltd"
                    className="w-full p-2.5 text-xs border border-slate-300 rounded-xl"
                  />
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <div className="border-t pt-6 flex justify-end gap-3">
              <Link
                to="/admin/network-assets/list"
                className="px-4 py-2 border border-slate-300 text-slate-700 font-semibold text-xs rounded-xl hover:bg-slate-50"
              >
                Cancel
              </Link>
              <button
                type="submit"
                disabled={isLoading}
                className="px-6 py-2 bg-mnnit-blue hover:bg-blue-800 text-white font-semibold text-xs rounded-xl shadow-md flex items-center gap-1.5 transition-colors disabled:opacity-50"
              >
                <Save className="w-4 h-4" />
                <span>{isEdit ? 'Update Asset' : 'Create Asset'}</span>
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
};
