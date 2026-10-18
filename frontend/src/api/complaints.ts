import { fetchApi } from './client';
import { ComplaintCreateRequest, ComplaintCreateResponse, ConfigResponse } from '../types';

export async function getConfig(): Promise<ConfigResponse> {
  return fetchApi<ConfigResponse>('/config');
}

export async function submitComplaint(data: ComplaintCreateRequest): Promise<ComplaintCreateResponse> {
  return fetchApi<ComplaintCreateResponse>('/complaints', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
