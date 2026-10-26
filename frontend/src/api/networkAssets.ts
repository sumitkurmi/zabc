// MODULE: Network Asset and Stock Management - this file belongs to the code for this module.
// REST API client functions for Network Asset and Stock Management endpoints.

import { fetchApi } from './client';

const API_BASE = '/admin/network-assets';

export async function fetchAssetSummary() {
  return fetchApi(`${API_BASE}/reports/summary`);
}

export async function fetchAssets(params: {
  category?: string;
  status?: string;
  location_id?: string;
  q?: string;
  warranty_expiring_days?: number;
  page?: number;
  limit?: number;
}): Promise<{ assets: any[]; total: number; page: number; pages: number }> {
  const query = new URLSearchParams();
  if (params.category) query.set('category', params.category);
  if (params.status) query.set('status', params.status);
  if (params.location_id) query.set('location_id', params.location_id);
  if (params.q) query.set('q', params.q);
  if (params.warranty_expiring_days) query.set('warranty_expiring_days', String(params.warranty_expiring_days));
  if (params.page) query.set('page', String(params.page));
  if (params.limit) query.set('limit', String(params.limit));

  return fetchApi<{ assets: any[]; total: number; page: number; pages: number }>(`${API_BASE}/assets?${query.toString()}`);
}

export async function createAsset(data: any) {
  return fetchApi(`${API_BASE}/assets`, {
    method: 'POST',
    body: JSON.stringify(data)
  });
}

export async function fetchAssetDetail(id: string): Promise<any> {
  return fetchApi<any>(`${API_BASE}/assets/${id}`);
}

export async function updateAsset(id: string, data: any) {
  return fetchApi(`${API_BASE}/assets/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data)
  });
}

export async function deleteAsset(id: string): Promise<{ action: string; message: string }> {
  return fetchApi(`${API_BASE}/assets/${id}`, {
    method: 'DELETE'
  });
}

export async function changeAssetStatus(id: string, status: string, reason: string) {
  return fetchApi(`${API_BASE}/assets/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status, reason })
  });
}

export async function changeAssetLocation(id: string, location_id: string) {
  return fetchApi(`${API_BASE}/assets/${id}/location`, {
    method: 'PATCH',
    body: JSON.stringify({ location_id })
  });
}

export async function replaceAsset(id: string, new_asset_id: string, reason?: string) {
  return fetchApi(`${API_BASE}/assets/${id}/replace`, {
    method: 'POST',
    body: JSON.stringify({ new_asset_id, reason })
  });
}

export async function addMaintenanceRecord(id: string, record: any) {
  return fetchApi(`${API_BASE}/assets/${id}/maintenance`, {
    method: 'POST',
    body: JSON.stringify(record)
  });
}

// Locations
export async function fetchLocationsTree(): Promise<any[]> {
  return fetchApi(`${API_BASE}/locations`);
}

export async function createLocation(data: any) {
  return fetchApi(`${API_BASE}/locations`, {
    method: 'POST',
    body: JSON.stringify(data)
  });
}

export async function fetchLocationDetail(id: string) {
  return fetchApi(`${API_BASE}/locations/${id}`);
}

export async function deleteLocation(id: string): Promise<{ message: string }> {
  return fetchApi(`${API_BASE}/locations/${id}`, {
    method: 'DELETE'
  });
}

// Ports
export async function bulkCreatePorts(switchId: string, start_port: number, end_port: number, vlan?: number) {
  return fetchApi(`${API_BASE}/switches/${switchId}/ports`, {
    method: 'POST',
    body: JSON.stringify({ start_port, end_port, vlan })
  });
}

export async function fetchSwitchPorts(switchId: string): Promise<any[]> {
  return fetchApi(`${API_BASE}/switches/${switchId}/ports`);
}

export async function updatePort(portId: string, data: any) {
  return fetchApi(`${API_BASE}/ports/${portId}`, {
    method: 'PUT',
    body: JSON.stringify(data)
  });
}

// Stock
export async function fetchStockItems(lowStockOnly = false): Promise<any[]> {
  return fetchApi(`${API_BASE}/stock?low_stock=${lowStockOnly}`);
}

export async function createStockItem(data: any) {
  return fetchApi(`${API_BASE}/stock`, {
    method: 'POST',
    body: JSON.stringify(data)
  });
}

export async function issueStock(id: string, quantity: number, reason: string) {
  return fetchApi(`${API_BASE}/stock/${id}/issue`, {
    method: 'POST',
    body: JSON.stringify({ quantity, reason })
  });
}

export async function restockStock(id: string, quantity: number) {
  return fetchApi(`${API_BASE}/stock/${id}/restock`, {
    method: 'POST',
    body: JSON.stringify({ quantity })
  });
}

export async function fetchStockTransactions(id: string): Promise<any[]> {
  return fetchApi(`${API_BASE}/stock/${id}/transactions`);
}
