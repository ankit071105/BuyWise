import axios from 'axios'

// ⚠️ CHANGE THIS: Update to your backend URL if different
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('buywise_token')
    if (token) config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Auto-logout on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('buywise_token')
      localStorage.removeItem('buywise_user')
      window.location.href = '/auth/login'
    }
    return Promise.reject(err)
  }
)

// Auth
export const authApi = {
  register: (data: { email: string; name: string; password: string }) =>
    api.post('/api/auth/register', data),
  login: (email: string, password: string) =>
    api.post('/api/auth/login', new URLSearchParams({ username: email, password }),
      { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }),
  me: () => api.get('/api/auth/me'),
}

// Products
export const productsApi = {
  analyze: (payload: { url?: string; query?: string }) =>
    api.post('/api/products/analyze', payload),
  track: (productId: number, targetPrice?: number) =>
    api.post('/api/products/track', { product_id: productId, target_price: targetPrice }),
  untrack: (trackedId: number) =>
    api.delete(`/api/products/track/${trackedId}`),
  getTracked: () => api.get('/api/products/tracked'),
  getProduct: (id: number) => api.get(`/api/products/${id}`),
}

// Chat
export const chatApi = {
  send: (message: string) => api.post('/api/chat/message', { message }),
  getHistory: () => api.get('/api/chat/history'),
  clearHistory: () => api.delete('/api/chat/history'),
}

// Search history
export const historyApi = {
  get: () => api.get('/api/history/'),
  clear: () => api.delete('/api/history/'),
}

// Alerts
export const alertsApi = {
  create: (data: { product_id: number; alert_type: string; threshold?: number; channel: string }) =>
    api.post('/api/alerts/', data),
  get: () => api.get('/api/alerts/'),
  delete: (id: number) => api.delete(`/api/alerts/${id}`),
}
