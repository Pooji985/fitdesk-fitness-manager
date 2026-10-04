import { apiRequest } from './api';

export const memberService = {
  async getMyProfile() {
    return apiRequest('/members/me');
  },

  async updateMyProfile(updates) {
    return apiRequest('/members/me', {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  },

  async getMembers() {
    return apiRequest('/members');
  },

  async updateMember(memberId, updates) {
    return apiRequest(`/members/${memberId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  },
};