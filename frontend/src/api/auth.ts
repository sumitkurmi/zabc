// MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
// API client methods for staff user authentication and current user profile retrieval.

import { fetchApi } from './client';

export async function loginStaff(data: { username: string; password: string }) {
  return fetchApi<{ token: string; role: string; full_name: string; expires_at: string }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(data)
  });
}

export async function fetchCurrentStaff() {
  return fetchApi<any>('/auth/me');
}
