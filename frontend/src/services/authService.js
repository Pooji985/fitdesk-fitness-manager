import { apiRequest } from './api';

export const authService = {
  async register(account) {
    return apiRequest('/auth/register', {
      method: 'POST',
      body: JSON.stringify(account),
    });
  },

  async login(credentials) {
    return apiRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  },

  async getCurrentUser() {
    return apiRequest('/auth/me');
  },
};