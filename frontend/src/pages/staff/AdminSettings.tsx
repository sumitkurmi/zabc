// MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
// AdminSettings page for managing admin notification preferences.

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchAdminSettings, updateAdminSettings } from '../../api/complaints';
import { adminLogout } from '../../api/admin';
import { Settings, Bell, CheckCircle2, ArrowLeft, LogOut } from 'lucide-react';

export const AdminSettings: React.FC = () => {
  const [notifyNew, setNotifyNew] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchAdminSettings().then((res) => setNotifyNew(res.notify_on_new_complaint || false));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    try {
      await updateAdminSettings(notifyNew);
      setMessage('Settings updated successfully');
      setTimeout(() => setMessage(null), 3000);
    } catch (err: any) {
      alert(err.message || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = () => {
    adminLogout();
    window.location.href = '/login';
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col">
      {/* Header */}
      <header className="bg-mnnit-blue text-white shadow-md">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/admin" className="p-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <h1 className="text-lg font-bold">Admin Settings</h1>
          </div>
          <div className="flex items-center gap-4">
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

      <main className="max-w-7xl mx-auto px-6 py-8 w-full flex-1">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-6 max-w-xl">
      <div className="flex items-center gap-2 border-b border-slate-100 pb-4">
        <Settings className="w-5 h-5 text-blue-600" />
        <h1 className="text-base font-bold text-slate-900">Admin Notification Settings</h1>
      </div>

      {message && (
        <div className="p-3 bg-emerald-50 text-emerald-800 text-xs rounded-xl flex items-center gap-2 border border-emerald-200">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{message}</span>
        </div>
      )}

      <div className="space-y-4 text-xs">
        <div className="flex items-center justify-between p-4 bg-slate-50 rounded-2xl border border-slate-200">
          <div className="space-y-0.5">
            <span className="font-bold text-slate-800 flex items-center gap-1.5">
              <Bell className="w-4 h-4 text-mnnit-gold" />
              Email Alert on New Complaint
            </span>
            <p className="text-slate-500 text-[11px]">
              Receive immediate email notification copies when a student submits and verifies a new complaint ticket.
            </p>
          </div>
          <input
            type="checkbox"
            checked={notifyNew}
            onChange={(e) => setNotifyNew(e.target.checked)}
            className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500 cursor-pointer"
          />
        </div>

        <button
          onClick={handleSave}
          disabled={saving}
          className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl shadow transition-colors"
        >
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>
        </div>
      </main>
    </div>
  );
};
