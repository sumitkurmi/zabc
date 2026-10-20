// MODULE: Network Asset and Stock Management - this file belongs to the code for this module.
// Sub-navigation header bar for Network Asset and Stock Management sub-routes.

import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Server, Network, Boxes } from 'lucide-react';

export const NetworkAssetsNav: React.FC = () => {
  const navItems = [
    { to: '/admin/network-assets', label: 'Overview', icon: LayoutDashboard, end: true },
    { to: '/admin/network-assets/list', label: 'Assets', icon: Server, end: false },
    { to: '/admin/network-assets/locations', label: 'Locations & Ports', icon: Network, end: false },
    { to: '/admin/network-assets/stock', label: 'Stock Inventory', icon: Boxes, end: false }
  ];

  return (
    <div className="bg-white border-b border-slate-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-6 flex items-center gap-2 overflow-x-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex items-center gap-2 px-4 py-3 text-xs font-semibold border-b-2 transition-colors whitespace-nowrap ${
                  isActive
                    ? 'border-blue-600 text-blue-600 bg-blue-50/50'
                    : 'border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </div>
    </div>
  );
};
