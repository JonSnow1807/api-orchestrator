// API Configuration
// In production, use relative URLs (same origin)
// In development, use localhost:8000

const isDevelopment = import.meta.env.MODE === 'development';
const isProduction = import.meta.env.MODE === 'production';

// Use environment variables if available, otherwise use defaults
export const API_BASE_URL = import.meta.env.VITE_API_URL || 
  (isProduction ? '' : 'http://localhost:8000');

export const WS_BASE_URL = import.meta.env.VITE_WS_URL || 
  (isProduction ? `ws://${window.location.host}` : 'ws://localhost:8000');

// For WebSocket with SSL in production
export const getWebSocketURL = () => {
  if (isProduction) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}/ws`;
  }
  return 'ws://localhost:8000/ws';
};

// Helper to get full API URL
export const getApiUrl = (path) => {
  if (path.startsWith('/')) {
    return `${API_BASE_URL}${path}`;
  }
  return `${API_BASE_URL}/${path}`;
};

export default {
  API_BASE_URL,
  WS_BASE_URL,
  getWebSocketURL,
  getApiUrl,
  isDevelopment,
  isProduction
};