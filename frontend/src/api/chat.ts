import { fetchApi } from './client';
import {
  ChatMessageResponse,
  ChatTranscriptResponse,
  SummarizeResponse
} from '../types';

export async function createChat(): Promise<{ chat_id: string }> {
  return fetchApi<{ chat_id: string }>('/chat', {
    method: 'POST',
  });
}

export async function getChatTranscript(chatId: string): Promise<ChatTranscriptResponse> {
  return fetchApi<ChatTranscriptResponse>(`/chat/${chatId}`);
}

export async function sendChatMessage(
  chatId: string,
  content: string
): Promise<ChatMessageResponse> {
  return fetchApi<ChatMessageResponse>(`/chat/${chatId}/message`, {
    method: 'POST',
    body: JSON.stringify({ content }),
  });
}

export async function summarizeChat(chatId: string): Promise<SummarizeResponse> {
  return fetchApi<SummarizeResponse>(`/chat/${chatId}/summarize`, {
    method: 'POST',
  });
}
