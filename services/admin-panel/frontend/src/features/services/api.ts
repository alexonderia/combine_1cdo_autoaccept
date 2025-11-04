import { API_ROUTES, requestJson } from '../../core/api/client';
import type { Service } from '../../core/types';

/** Loads the current service status list. */
export function fetchServiceStatus(): Promise<Service[]> {
  return requestJson<Service[]>(API_ROUTES.services.status);
}
