// API Configuration
const getApiUrl = () => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  
  // Default URLs based on environment
  if (import.meta.env.MODE === 'production') {
    return 'https://api.streamapi.dev';
  }
  
  return 'http://localhost:8000';
};

const getWebSocketUrl = () => {
  const apiUrl = getApiUrl();
  if (apiUrl.startsWith('https://')) {
    return apiUrl.replace('https://', 'wss://');
  }
  return apiUrl.replace('http://', 'ws://');
};

export const API_CONFIG = {
  BASE_URL: getApiUrl(),
  WS_URL: getWebSocketUrl(),
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
};

export const API_ENDPOINTS = {
  // Auth
  LOGIN: '/api/auth/login',
  REGISTER: '/api/auth/register',
  REFRESH: '/api/auth/refresh',
  LOGOUT: '/api/auth/logout',
  
  // Projects
  PROJECTS: '/api/projects',
  PROJECT_STATS: '/api/projects/stats/overview',
  
  // V5.0 Features
  NATURAL_LANGUAGE: '/api/v5/natural-language',
  VISUALIZATION: '/api/v5/visualization',
  VARIABLES: '/api/v5/variables',
  PRIVACY_AI: '/api/v5/privacy-ai',
  OFFLINE: '/api/v5/offline',
  VIRTUALIZATION: '/api/v5/virtualization',
  VSCODE: '/api/v5/vscode',
  
  // WebSocket
  WS_ENDPOINT: '/ws',
};

export default API_CONFIG;