import { API_ROUTES, requestJson } from '../../core/api/client';
import type { ConfigService } from '../../core/types';

/** Retrieves configuration entries grouped by service. */
export function fetchConfigServices(): Promise<ConfigService[]> {
  return requestJson<ConfigService[]>(API_ROUTES.config.list);
}
