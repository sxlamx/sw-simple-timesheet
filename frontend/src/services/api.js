import axios from 'axios';
import offlineService from './offlineService';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8095';

// Create axios instance with default config
const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors and offline scenarios
api.interceptors.response.use(
  (response) => {
    // Cache successful API responses
    if (response.status === 200 && response.config.method === 'get') {
      offlineService.cacheAPIResponse(response.config.url, response.data);
    }
    return response;
  },
  async (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/';
      return Promise.reject(error);
    }
    
    // Handle network errors (offline)
    if (!navigator.onLine || error.code === 'NETWORK_ERROR') {
      // Try to get cached response for GET requests
      if (error.config.method === 'get') {
        try {
          const cachedData = await offlineService.getCachedAPIResponse(error.config.url);
          if (cachedData) {
            return { data: cachedData, status: 200, fromCache: true };
          }
        } catch (cacheError) {
          console.error('Cache read error:', cacheError);
        }
      }
      
      // For POST/PUT/DELETE requests, store for offline sync
      if (['post', 'put', 'delete'].includes(error.config.method)) {
        await handleOfflineAction(error.config);
      }
    }
    
    return Promise.reject(error);
  }
);

// Handle offline actions
async function handleOfflineAction(config) {
  try {
    let actionType = 'UNKNOWN';
    
    // Determine action type based on URL and method
    if (config.url.includes('/timesheets/create')) {
      actionType = 'CREATE_TIMESHEET';
    } else if (config.url.includes('/submit') && config.method === 'post') {
      actionType = 'SUBMIT_TIMESHEET';
    } else if (config.method === 'put') {
      actionType = 'UPDATE_TIMESHEET';
    }
    
    await offlineService.storeOfflineAction(
      actionType,
      config.data ? JSON.parse(config.data) : null,
      config.url
    );
    
    console.log(`Stored offline action: ${actionType}`);
  } catch (error) {
    console.error('Failed to store offline action:', error);
  }
}

// Auth API
export const authAPI = {
  loginWithGoogle: (token) => api.post('/auth/google', { token }),
  getCurrentUser: () => api.get('/users/me'),
};

// Users API
export const usersAPI = {
  getCurrentUser: () => api.get('/users/me'),
  updateCurrentUser: (userData) => api.put('/users/me', userData),
  getUsers: (skip = 0, limit = 100) => api.get(`/users?skip=${skip}&limit=${limit}`),
  getStaffMembers: () => api.get('/users/staff'),
  getUser: (userId) => api.get(`/users/${userId}`),
  updateUser: (userId, userData) => api.put(`/users/${userId}`, userData),
};

// Timesheets API
export const timesheetsAPI = {
  createTimesheet: (year, month) => api.post('/timesheets/create', { year, month }),
  getUserTimesheets: (skip = 0, limit = 100) => api.get(`/timesheets?skip=${skip}&limit=${limit}`),
  getTimesheet: (timesheetId) => api.get(`/timesheets/${timesheetId}`),
  getTimesheetData: (timesheetId) => api.get(`/timesheets/data/${timesheetId}`),
  submitTimesheet: (timesheetId) => api.post(`/timesheets/${timesheetId}/submit`),
  approveTimesheet: (timesheetId, reviewNotes) => api.post(`/timesheets/${timesheetId}/approve`, { review_notes: reviewNotes }),
  rejectTimesheet: (timesheetId, reviewNotes) => api.post(`/timesheets/${timesheetId}/reject`, { review_notes: reviewNotes }),
  getPendingTimesheets: () => api.get('/timesheets/pending/review'),
  getAllTeamTimesheets: (status = null, skip = 0, limit = 100) => {
    const params = new URLSearchParams({ skip: skip.toString(), limit: limit.toString() });
    if (status) params.append('status', status);
    return api.get(`/timesheets/team/all?${params}`);
  },
  getTeamStatistics: () => api.get('/timesheets/team/statistics'),
  getMonthlyAnalytics: (months = 6) => api.get(`/timesheets/analytics/monthly?months=${months}`),
  getTeamMonthlyAnalytics: (months = 6) => api.get(`/timesheets/analytics/team-monthly?months=${months}`),
  getStaffBreakdownAnalytics: () => api.get('/timesheets/analytics/staff-breakdown'),
  exportTimesheet: (timesheetId) => api.get(`/timesheets/${timesheetId}/export`, { responseType: 'blob' }),
  exportTeamTimesheets: () => api.get('/timesheets/export/team', { responseType: 'blob' }),
};

// Notifications API
export const notificationsAPI = {
  sendReminders: () => api.post('/notifications/send-reminders'),
  testEmail: (toEmail) => api.post(`/notifications/test-email?to_email=${encodeURIComponent(toEmail)}`),
};

// Feedback API
export const feedbackAPI = {
  createFeedback: (feedbackData) => api.post('/feedback', feedbackData),
  getFeedbackList: (params = {}) => {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        queryParams.append(key, value);
      }
    });
    return api.get(`/feedback?${queryParams}`);
  },
  getFeedback: (feedbackId) => api.get(`/feedback/${feedbackId}`),
  updateFeedback: (feedbackId, updateData) => api.put(`/feedback/${feedbackId}`, updateData),
  deleteFeedback: (feedbackId) => api.delete(`/feedback/${feedbackId}`),
  addResponse: (feedbackId, responseData) => api.post(`/feedback/${feedbackId}/responses`, responseData),
  getResponses: (feedbackId) => api.get(`/feedback/${feedbackId}/responses`),
  getStats: (myStats = false) => api.get(`/feedback/stats/overview?my_stats=${myStats}`),
};

export default api;