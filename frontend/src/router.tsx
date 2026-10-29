// MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
// Application router configuration wiring public student pages, staff authentication, role guards, and dashboards.

import React from 'react';
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { Home } from './pages/Home';
import { Success } from './pages/Success';
import { Login as StaffLogin } from './pages/public/Login';
import { ConfirmComplaint } from './pages/public/ConfirmComplaint';
import { RateComplaint } from './pages/public/RateComplaint';

import { ManagerDashboard } from './pages/staff/ManagerDashboard';
import { TechnicianDashboard } from './pages/staff/TechnicianDashboard';
import { StaffManagement } from './pages/staff/StaffManagement';
import { JunkComplaints } from './pages/staff/JunkComplaints';
import { AdminSettings } from './pages/staff/AdminSettings';

import { Dashboard as AdminDashboard } from './pages/admin/Dashboard';
import { AllChats } from './pages/admin/AllChats';
import { ChatDetail } from './pages/admin/ChatDetail';
import { ReferenceHome } from './pages/admin/ReferenceHome';
import { CategoryPage } from './pages/admin/CategoryPage';
import { RequireRole } from './components/RequireRole';

import { Overview } from './pages/admin/network-assets/Overview';
import { AssetList } from './pages/admin/network-assets/AssetList';
import { AssetForm } from './pages/admin/network-assets/AssetForm';
import { AssetDetail } from './pages/admin/network-assets/AssetDetail';
import { Locations } from './pages/admin/network-assets/Locations';
import { SwitchPorts } from './pages/admin/network-assets/SwitchPorts';
import { Stock } from './pages/admin/network-assets/Stock';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const router = createBrowserRouter([
  // Public Student Pages
  { path: '/', element: <Home /> },
  { path: '/success/:complaintId', element: <Success /> },
  { path: '/confirm/:token', element: <ConfirmComplaint /> },
  { path: '/rate/:token', element: <RateComplaint /> },
  { path: '/login', element: <StaffLogin /> },
  { path: '/admin/login', element: <Navigate to="/login" replace /> },

  // Admin Workspace
  {
    element: <RequireRole allowedRoles={['ADMIN']} />,
    children: [
      { path: '/admin', element: <AdminDashboard /> },
      { path: '/admin/staff', element: <StaffManagement /> },
      { path: '/admin/junk', element: <JunkComplaints /> },
      { path: '/admin/settings', element: <AdminSettings /> },
      { path: '/admin/chats', element: <AllChats /> },
      { path: '/admin/chats/:id', element: <ChatDetail /> },
      { path: '/admin/reference', element: <ReferenceHome /> },
      { path: '/admin/reference/:categoryId', element: <CategoryPage /> },
    ],
  },

  // Manager Workspace (Admin + Manager)
  {
    element: <RequireRole allowedRoles={['ADMIN', 'MANAGER']} />,
    children: [{ path: '/manager', element: <ManagerDashboard /> }],
  },

  // Technician Workspace (Technician)
  {
    element: <RequireRole allowedRoles={['TECHNICIAN']} />,
    children: [{ path: '/technician', element: <TechnicianDashboard /> }],
  },

  // Shared Read-Only / Write Network Assets
  {
    element: <RequireRole allowedRoles={['ADMIN', 'MANAGER', 'TECHNICIAN']} />,
    children: [
      { path: '/admin/network-assets', element: <Overview /> },
      { path: '/admin/network-assets/list', element: <AssetList /> },
      { path: '/admin/network-assets/new', element: <AssetForm /> },
      { path: '/admin/network-assets/:id/edit', element: <AssetForm /> },
      { path: '/admin/network-assets/:id', element: <AssetDetail /> },
      { path: '/admin/network-assets/locations', element: <Locations /> },
      { path: '/admin/network-assets/switches/:id/ports', element: <SwitchPorts /> },
      { path: '/admin/network-assets/stock', element: <Stock /> },
    ],
  },
]);

export const AppRouter: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
};
