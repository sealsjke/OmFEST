import type { DeviceType, Endpoint, Instructions, LabState } from '../types';

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, { ...init, headers: { ...(init?.body ? { 'Content-Type': 'application/json' } : {}), ...init?.headers } });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error((data as { error?: string }).error ?? `Request failed (${response.status})`);
  return data as T;
}

const base = '/api';
export const api = {
  createSession: () => request<LabState>(`${base}/session`, { method: 'POST' }),
  instructions: () => request<Instructions>(`${base}/challenge`),
  state: (id: string) => request<LabState>(`${base}/session/${id}/state`),
  addDevice: (id: string, body: { type: DeviceType; x: number; y: number }) => request<LabState>(`${base}/session/${id}/device`, { method: 'POST', body: JSON.stringify(body) }),
  moveDevice: (id: string, deviceId: string, x: number, y: number) => request<LabState>(`${base}/session/${id}/device/${deviceId}`, { method: 'PATCH', body: JSON.stringify({ x, y }) }),
  deleteDevice: (id: string, deviceId: string) => request<LabState>(`${base}/session/${id}/device/${deviceId}`, { method: 'DELETE' }),
  addLink: (id: string, a: Endpoint, b: Endpoint) => request<LabState>(`${base}/session/${id}/link`, { method: 'POST', body: JSON.stringify({ a, b }) }),
  deleteLink: (id: string, linkId: string) => request<LabState>(`${base}/session/${id}/link/${linkId}`, { method: 'DELETE' }),
  configurePc: (id: string, deviceId: string, body: { ip: string; mask: string; gateway: string }) => request<LabState>(`${base}/session/${id}/pc/${deviceId}/config`, { method: 'POST', body: JSON.stringify(body) }),
  command: (id: string, deviceId: string, command: string) => request<{ output: string; prompt: string; clear: boolean; exited: boolean; state: LabState }>(`${base}/session/${id}/device/${deviceId}/command`, { method: 'POST', body: JSON.stringify({ command }) }),
  reset: (id: string) => request<LabState>(`${base}/session/${id}/reset`, { method: 'POST' }),
};
