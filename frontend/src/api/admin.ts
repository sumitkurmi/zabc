import { fetchApi } from './client';
import {
  AdminLoginResponse,
  AdminStatsResponse,
  CategoryDetailResponse,
  CategorySummary,
  ChatListResponse,
  ChatTranscriptResponse,
  DocumentResponse
} from '../types';

export async function adminLogin(username: string, password: string): Promise<AdminLoginResponse> {
  const res = await fetchApi<AdminLoginResponse>('/admin/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  sessionStorage.setItem('admin_token', res.token);
  return res;
}

export async function adminLogout(): Promise<void> {
  try {
    await fetchApi('/admin/logout', { method: 'POST' });
  } catch (e) {
    // Ignore error
  }
  sessionStorage.removeItem('admin_token');
}

export async function getAdminStats(): Promise<AdminStatsResponse> {
  return fetchApi<AdminStatsResponse>('/admin/stats');
}

export async function getAdminChats(
  status = 'UNASSIGNED',
  page = 1,
  q?: string,
  category?: string
): Promise<ChatListResponse> {
  const params = new URLSearchParams({ status, page: String(page) });
  if (q) params.append('q', q);
  if (category) params.append('category', category);
  return fetchApi<ChatListResponse>(`/admin/chats?${params.toString()}`);
}

export async function getAdminChatDetail(chatId: string): Promise<ChatTranscriptResponse> {
  return fetchApi<ChatTranscriptResponse>(`/admin/chats/${chatId}`);
}

export async function moveChatToReference(chatId: string, categorySlug: string): Promise<{ message: string }> {
  return fetchApi<{ message: string }>(`/admin/chats/${chatId}/move`, {
    method: 'POST',
    body: JSON.stringify({ category_slug: categorySlug }),
  });
}

export async function unassignChatFromReference(chatId: string): Promise<{ message: string }> {
  return fetchApi<{ message: string }>(`/admin/chats/${chatId}/unassign`, {
    method: 'POST',
  });
}

export async function deleteChat(chatId: string): Promise<{ message: string }> {
  return fetchApi<{ message: string }>(`/admin/chats/${chatId}`, {
    method: 'DELETE',
  });
}

export async function getReferenceCategories(): Promise<CategorySummary[]> {
  return fetchApi<CategorySummary[]>('/admin/categories');
}

export async function getCategoryDetail(slug: string): Promise<CategoryDetailResponse> {
  return fetchApi<CategoryDetailResponse>(`/admin/categories/${slug}`);
}

export async function uploadDocument(slug: string, file: File): Promise<DocumentResponse> {
  const token = sessionStorage.getItem('admin_token');
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`/api/admin/categories/${slug}/documents`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Upload failed');
  }

  return res.json();
}

export async function deleteDocument(docId: string): Promise<{ message: string }> {
  return fetchApi<{ message: string }>(`/admin/documents/${docId}`, {
    method: 'DELETE',
  });
}
