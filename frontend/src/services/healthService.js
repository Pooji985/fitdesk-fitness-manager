import { apiRequest } from './api';

/**
 * Health check service communicating with FastAPI backend
 */
export const healthService = {
  /**
   * Fetches API & SQLite database status from GET /api/v1/health
   */
  async getHealth() {
    return apiRequest('/health');
  },

  /**
   * Fetches root API welcome and documentation links
   */
  async getRootInfo() {
    // Hits FastAPI root '/' via proxy
    const response = await fetch('/');
    if (!response.ok) {
      throw new Error(`Failed to reach root API: ${response.status}`);
    }
    return response.json();
  },
};
