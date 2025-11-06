import { API_ROUTES, requestJson } from '../../core/api/client';

export interface ProxyJsonRequest {
  service: string;
  method: 'GET' | 'POST';
  endpoint: string;
  params?: Record<string, unknown>;
  body?: unknown;
  contentType?: string;
}

export type ProxyResponse = {
  status_code: number;
  url: string;
  headers?: Record<string, string>;
  body?: unknown;
  [key: string]: unknown;
};

/** Sends a JSON payload through the proxy endpoint. */
export function sendProxyJsonRequest(request: ProxyJsonRequest): Promise<ProxyResponse> {
  return requestJson<ProxyResponse>(API_ROUTES.proxy, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
}
