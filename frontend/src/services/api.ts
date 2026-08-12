import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const chatAPI = {
  sendMessage: (message: string, sessionId?: string, context?: Record<string, unknown>) =>
    api.post('/chat/', { message, session_id: sessionId, context }),
  getSessionHistory: (sessionId: string) => api.get(`/chat/sessions/${sessionId}/history`),
};

export const authAPI = {
  login: (email: string, password: string) => api.post('/auth/login', { email, password }),
  register: (email: string, password: string, display_name: string) =>
    api.post('/auth/register', { email, password, display_name }),
  getMe: () => api.get('/auth/me'),
  refreshToken: (refreshToken: string) => api.post('/auth/refresh', { refresh_token: refreshToken }),
};

export const accessAPI = {
  createRequest: (data: { resource_type: string; resource_identifier: string; access_type: string; justification: string; share_with_emails?: string }) =>
    api.post('/access/request', data),
  getPending: () => api.get('/access/pending'),
  approve: (approvalId: string, decision: string, comments: string) =>
    api.post(`/access/approve/${approvalId}`, { decision, comments }),
};

export const driveAPI = {
  getAuthUrl: () => api.get('/drive/auth-url'),
  getStatus: () => api.get('/drive/status'),
  disconnect: () => api.post('/drive/disconnect'),
};

export const healthAPI = {
  check: () => api.get('/health'),
  tools: () => api.get('/tools'),
  toolsHealth: () => api.get('/tools/health'),
};

export default api;
