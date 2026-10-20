import React from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { Home } from './pages/Home';
import { Success } from './pages/Success';
import { Login } from './pages/admin/Login';
import { Dashboard } from './pages/admin/Dashboard';
import { AllChats } from './pages/admin/AllChats';
import { ChatDetail } from './pages/admin/ChatDetail';
import { ReferenceHome } from './pages/admin/ReferenceHome';
import { CategoryPage } from './pages/admin/CategoryPage';
import { ProtectedRoute } from './components/admin/ProtectedRoute';

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
  { path: '/', element: <Home /> },
  { path: '/success/:complaintId', element: <Success /> },
  { path: '/admin/login', element: <Login /> },
  {
    path: '/admin',
    element: (
      <ProtectedRoute>
        <Dashboard />
      </ProtectedRoute>
    ),
  },
  {
    path: '/admin/network-assets',
    element: (
      <ProtectedRoute>
        <Overview />
      </ProtectedRoute>
    ),
  },
  {
    path: '/admin/network-assets/list',
    element: (
      <ProtectedRoute>
        <AssetList />
      </ProtectedRoute>
    ),
  },
  {
    path: '/admin/network-assets/new',
    element: (
      <ProtectedRoute>
        <AssetForm />
      </ProtectedRoute>
    ),
  },
  {
    path: '/admin/network-assets/:id/edit',
    element: (
      <ProtectedRoute>
        <AssetForm />
      </ProtectedRoute>
    ),
  },
  {
    path: '/admin/network-assets/:id',
    element: (
      <ProtectedRoute>
        <AssetDetail />
      </ProtectedRoute>
    ),
  },
  {
    path: '/admin/network-assets/locations',
    element: (
      <ProtectedRoute>
        <Locations />
      </ProtectedRoute>
    ),
  },
  {
    path: '/admin/network-assets/switches/:id/ports',
    element: (
      <ProtectedRoute>
        <SwitchPorts />
      </ProtectedRoute>
    ),
  },
  {
    path: '/admin/network-assets/stock',
    element: (
      <ProtectedRoute>
        <Stock />
      </ProtectedRoute>
    ),
  },
  {
    path: '/admin/chats',
    element: (
      <ProtectedRoute>
        <AllChats />
      </ProtectedRoute>
    ),
  },
  {
    path: '/admin/chats/:id',
    element: (
      <ProtectedRoute>
        <ChatDetail />
      </ProtectedRoute>
    ),
  },
  {
    path: '/admin/reference',
    element: (
      <ProtectedRoute>
        <ReferenceHome />
      </ProtectedRoute>
    ),
  },
  {
    path: '/admin/reference/:categoryId',
    element: (
      <ProtectedRoute>
        <CategoryPage />
      </ProtectedRoute>
    ),
  },
]);

export const AppRouter: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
};
