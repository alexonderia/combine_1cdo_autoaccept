// В дальнейшем переменные можно переопределять через .env
export const CONTRACT_EXTRACTOR_URL = import.meta.env.VITE_CONTRACT_EXTRACTOR_URL || 'http://localhost:18080';
export const GLOBAS_API_URL = import.meta.env.VITE_GLOBAS_API_URL || 'http://localhost:18090';
export const LEGAL_AI_URL = import.meta.env.VITE_LEGAL_AI_URL || 'http://localhost:18100';
