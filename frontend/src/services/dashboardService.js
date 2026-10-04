import { apiRequest } from './api';

/**
 * Service for fetching role-tailored dashboard metrics and activity feeds.
 */
export const dashboardService = {
  /**
   * Fetches real-time dashboard statistics and activity history for active persona.
   *
   * @returns {Promise<Object>} Dashboard metrics response from FastAPI
   */
  async getMetrics() {
    return apiRequest('/dashboard/metrics');
  },
};
