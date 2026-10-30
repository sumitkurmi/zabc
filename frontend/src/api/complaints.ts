// MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
// API client functions for student OTP verification, manager/technician/admin complaint operations, and leaderboard.

import { fetchApi } from './client';
import { ConfigResponse } from '../types';

export { fetchStockItems } from './networkAssets';

export async function getConfig(): Promise<ConfigResponse> {
  return fetchApi<ConfigResponse>('/config');
}

// Public OTP Complaint Registration
export async function requestOTP(data: any) {
  return fetchApi<{ pending_id: string; message: string; expires_in_seconds: number; resend_cooldown_seconds: number }>(
    '/complaints/otp/request',
    {
      method: 'POST',
      body: JSON.stringify(data)
    }
  );
}

export async function verifyOTP(pending_id: string, otp: string) {
  return fetchApi<{ ticket_id: string; message: string }>('/complaints/otp/verify', {
    method: 'POST',
    body: JSON.stringify({ pending_id, otp })
  });
}

export async function resendOTP(pending_id: string) {
  return fetchApi<{ pending_id: string; message: string; expires_in_seconds: number; resend_cooldown_seconds: number }>(
    '/complaints/otp/resend',
    {
      method: 'POST',
      body: JSON.stringify({ pending_id })
    }
  );
}

// Student Action Links
export async function fetchTokenInfo(token: string) {
  return fetchApi<any>(`/student-actions/${token}`);
}

export async function confirmResolution(token: string, solved: boolean, comment?: string) {
  return fetchApi<{ message: string; ticket_id: string }>(`/student-actions/${token}/confirm`, {
    method: 'POST',
    body: JSON.stringify({ solved, comment })
  });
}

export async function submitRating(token: string, rating: number, feedback?: string) {
  return fetchApi<{ message: string; ticket_id: string }>(`/student-actions/${token}/rate`, {
    method: 'POST',
    body: JSON.stringify({ rating, feedback })
  });
}

// Manager Operations
export async function fetchManagerSummary() {
  return fetchApi<any>('/manager/summary');
}

export async function fetchManagerComplaints(params: {
  view?: string;
  status?: string;
  priority?: string;
  problem_type?: string;
  location?: string;
  technician_id?: string;
  sort?: string;
  q?: string;
  page?: number;
  limit?: number;
}) {
  const query = new URLSearchParams();
  if (params.view) query.set('view', params.view);
  if (params.status) query.set('status', params.status);
  if (params.priority) query.set('priority', params.priority);
  if (params.problem_type) query.set('problem_type', params.problem_type);
  if (params.location) query.set('location', params.location);
  if (params.technician_id) query.set('technician_id', params.technician_id);
  if (params.sort) query.set('sort', params.sort);
  if (params.q) query.set('q', params.q);
  if (params.page) query.set('page', String(params.page));
  if (params.limit) query.set('limit', String(params.limit));

  return fetchApi<{ complaints: any[]; total: number; page: number; pages: number }>(`/manager/complaints?${query.toString()}`);
}

export async function runAgentPipeline(ticket_id: string) {
  return fetchApi<{ message: string; ticket_id: string; job_id: string }>(`/manager/complaints/${ticket_id}/agent/run`, {
    method: 'POST'
  });
}

export async function acceptAgentSuggestion(ticket_id: string) {
  return fetchApi<{ message: string; ticket_id: string }>(`/manager/complaints/${ticket_id}/agent/accept-suggestion`, {
    method: 'POST'
  });
}

export async function fetchAgentStatus() {
  return fetchApi<{
    enabled: boolean;
    mode: string;
    pending_jobs: number;
    failed_jobs: number;
    last_successful_run: string | null;
  }>('/admin/agent/status');
}

export async function fetchComplaintDetail(ticket_id: string) {
  return fetchApi<any>(`/manager/complaints/${ticket_id}`);
}

export async function assignComplaint(ticket_id: string, technician_id: string, reason?: string) {
  return fetchApi(`/manager/complaints/${ticket_id}/assign`, {
    method: 'POST',
    body: JSON.stringify({ technician_id, reason })
  });
}

export async function fetchTechnicians() {
  return fetchApi<any[]>('/manager/technicians');
}

export async function toggleTechnicianAvailability(id: string, availability: string, confirm = false) {
  return fetchApi(`/manager/technicians/${id}/availability`, {
    method: 'PATCH',
    body: JSON.stringify({ availability, confirm })
  });
}

export async function fetchManagerReports(range = 'today') {
  return fetchApi<any>(`/manager/reports?range=${range}`);
}

// Shared Leaderboard
export async function fetchLeaderboard(sort = 'score') {
  return fetchApi<any[]>(`/leaderboard?sort=${sort}`);
}

// Technician Operations
export async function fetchTechnicianComplaints(tab = 'open', page = 1, limit = 20) {
  return fetchApi<{ complaints: any[]; total: number; page: number; pages: number }>(`/technician/complaints?tab=${tab}&page=${page}&limit=${limit}`);
}

export async function fetchTechnicianComplaintDetail(ticket_id: string) {
  return fetchApi<any>(`/technician/complaints/${ticket_id}`);
}

export async function resolveComplaint(ticket_id: string, payload: {
  diagnosis: string;
  solution: string;
  items_used?: any[];
  asset_actions?: any[];
}) {
  return fetchApi(`/technician/complaints/${ticket_id}/resolve`, {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export async function fetchMyRatings() {
  return fetchApi<any>('/technician/my-ratings');
}

// Admin Operations
export async function fetchStaffUsers() {
  return fetchApi<any[]>('/admin/staff');
}

export async function createStaffUser(data: any) {
  return fetchApi('/admin/staff', {
    method: 'POST',
    body: JSON.stringify(data)
  });
}

export async function updateStaffUser(id: string, data: any) {
  return fetchApi(`/admin/staff/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data)
  });
}

export async function resetStaffPassword(id: string, new_password: string) {
  return fetchApi(`/admin/staff/${id}/reset-password`, {
    method: 'POST',
    body: JSON.stringify({ new_password })
  });
}

export async function deactivateStaffUser(id: string) {
  return fetchApi(`/admin/staff/${id}/deactivate`, {
    method: 'POST'
  });
}

export async function reactivateStaffUser(id: string) {
  return fetchApi(`/admin/staff/${id}/reactivate`, {
    method: 'POST'
  });
}

export async function fetchAdminSettings() {
  return fetchApi<any>('/admin/me/settings');
}

export async function updateAdminSettings(notify_on_new_complaint: boolean) {
  return fetchApi('/admin/me/settings', {
    method: 'PUT',
    body: JSON.stringify({ notify_on_new_complaint })
  });
}

// Junk Operations
export async function markJunk(ticket_id: string, reason?: string) {
  return fetchApi(`/admin/complaints/${ticket_id}/mark-junk`, {
    method: 'POST',
    body: JSON.stringify({ reason })
  });
}

export async function restoreJunk(ticket_id: string) {
  return fetchApi(`/admin/complaints/${ticket_id}/restore`, {
    method: 'POST'
  });
}

export async function fetchJunkComplaints(page = 1, limit = 20) {
  return fetchApi<{ complaints: any[]; total: number; page: number; pages: number }>(`/admin/junk?page=${page}&limit=${limit}`);
}

export async function clearAllJunk(confirm = true) {
  return fetchApi(`/admin/junk?confirm=${confirm}`, {
    method: 'DELETE'
  });
}
