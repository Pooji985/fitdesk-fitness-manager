/**
 * Base API client using fetch and routed through the Vite dev proxy to the FastAPI backend.
 */

const API_BASE_URL = `${import.meta.env.VITE_API_URL || ''}/api/v1`;
export const AUTH_TOKEN_STORAGE_KEY = 'fitdesk.access_token';

export async function apiRequest(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const defaultHeaders = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };
  const token = typeof localStorage !== 'undefined'
    ? localStorage.getItem(AUTH_TOKEN_STORAGE_KEY)
    : null;

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const error = new Error(errorData.detail || errorData.message || `Request failed with status ${response.status}`);
      error.status = response.status;
      error.data = errorData;
      throw error;
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error on [${options.method || 'GET'} ${url}]:`, error);
    throw error;
  }
}
