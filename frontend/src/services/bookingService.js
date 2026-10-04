import { apiRequest } from './api';

export const bookingService = {
  async getMyBookings() {
    return apiRequest('/bookings');
  },

  async createBooking(classId) {
    return apiRequest('/bookings', {
      method: 'POST',
      body: JSON.stringify({ class_id: classId }),
    });
  },

  async cancelBooking(bookingId) {
    return apiRequest(`/bookings/${bookingId}/cancel`, { method: 'POST' });
  },

  async getAttendanceRoster(classId) {
    return apiRequest(`/attendance/classes/${classId}`);
  },

  async updateAttendance(bookingId, status) {
    return apiRequest(`/attendance/bookings/${bookingId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  },
};