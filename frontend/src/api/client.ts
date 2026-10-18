/**
 * Central HTTP fetch client wrapper for REST API communication.
 * Section 1: Strict frontend/backend separation using REST API.
 */

const API_BASE = '/api';

export async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = sessionStorage.getItem('admin_token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401 && endpoint.startsWith('/admin') && endpoint !== '/admin/login') {
    sessionStorage.removeItem('admin_token');
    window.location.href = '/admin/login';
    throw new Error('Unauthorized access. Redirecting to login.');
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const message = errorData.detail || errorData.message || 'An error occurred';
    throw new Error(message);
  }

  return response.json();
}
