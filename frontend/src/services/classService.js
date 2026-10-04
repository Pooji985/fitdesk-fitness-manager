import { apiRequest } from './api';

/**
 * Service for fetching fitness classes, trainer directory, and scheduling classes.
 */
export const classService = {
  /**
   * Retrieves all scheduled fitness classes with optional filtering and weather enrichment.
   *
   * @param {Object} [filters={}] - Optional filters: class_type, category, search, trainer_id, include_weather
   * @returns {Promise<Array>} List of fitness classes
   */
  async getClasses(filters = {}) {
    const params = new URLSearchParams();

    if (filters.class_type && filters.class_type !== 'all') {
      params.append('class_type', filters.class_type);
    }
    if (filters.category && filters.category !== 'all') {
      params.append('category', filters.category);
    }
    if (filters.search && filters.search.trim()) {
      params.append('search', filters.search.trim());
    }
    if (filters.trainer_id) {
      params.append('trainer_id', filters.trainer_id);
    }
    if (filters.upcoming_only !== undefined) {
      params.append('upcoming_only', String(filters.upcoming_only));
    }
    if (filters.include_weather !== undefined) {
      params.append('include_weather', String(filters.include_weather));
    }

    const query = params.toString() ? `?${params.toString()}` : '';
    return apiRequest(`/classes${query}`);
  },

  /**
   * Retrieves a single fitness class by ID with its weather forecast and capacity.
   *
   * @param {number|string} id - Class ID
   * @param {boolean} [includeWeather=true] - Whether to query Open-Meteo for outdoor classes
   * @returns {Promise<Object>} Fitness class detail
   */
  async getClassById(id, includeWeather = true) {
    return apiRequest(`/classes/${id}?include_weather=${includeWeather}`);
  },

  /**
   * Retrieves active trainers and staff eligible to lead classes.
   *
   * @returns {Promise<Array>} List of trainers
   */
  async getTrainers() {
    return apiRequest('/classes/trainers');
  },

  /**
   * Schedules a new fitness class (Admin or Trainer role required).
   *
   * @param {Object} classData - The class payload
   * @returns {Promise<Object>} Created fitness class
   */
  async createClass(classData) {
    return apiRequest('/classes', {
      method: 'POST',
      body: JSON.stringify(classData),
    });
  },

  async updateClass(classId, classData) {
    return apiRequest(`/classes/${classId}`, {
      method: 'PATCH',
      body: JSON.stringify(classData),
    });
  },

  async cancelClass(classId) {
    return apiRequest(`/classes/${classId}/cancel`, { method: 'POST' });
  },
};
