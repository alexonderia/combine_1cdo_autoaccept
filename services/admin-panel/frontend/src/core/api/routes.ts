/**
 * Centralized list of backend endpoints used by the admin panel.
 */
export const API_ROUTES = {
  services: {
    status: '/api/services/status',
  },
  prompts: {
    list: '/api/prompts/list',
    update: '/api/prompts/update',
  },
  config: {
    list: '/api/config/list',
  },
  proxy: '/api/proxy',
} as const;
