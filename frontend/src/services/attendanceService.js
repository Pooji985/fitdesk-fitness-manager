import { apiRequest } from './api';

export const attendanceService = {
  async getClassAttendance(classId) {
    return apiRequest(`/attendance/classes/${classId}`);
  },

  async updateBookingAttendance(bookingId, attendanceStatus) {
    return apiRequest(`/attendance/bookings/${bookingId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status: attendanceStatus }),
    });
  },
};