import axios from 'axios'

const BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export const api = axios.create({
  baseURL: BASE,
  withCredentials: true
})

api.interceptors.request.use(config => {
  const t = getToken()
  if (t) config.headers['Authorization'] = `Bearer ${t}`
  return config
})

api.interceptors.response.use(
  r => r,
  err => {
    const msg = err?.response?.data?.detail || err.message || 'Request failed'
    return Promise.reject(new Error(msg))
  }
)

const TOKEN_KEY = 'eventaic:token'
const USER_KEY = 'eventaic:user'

export function setAuth(token, user) {
  localStorage.setItem(TOKEN_KEY, token)
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function getUser() {
  try { return JSON.parse(localStorage.getItem(USER_KEY) || 'null') } catch { return null }
}

// ---- Auth API ----
export async function login(payload) {
  // Expect FastAPI to return { access_token, token_type, user }
  const r = await api.post('/api/v1/auth/login', payload)
  const token = r.data.access_token || r.data.token || r.data.accessToken
  setAuth(token, r.data.user || { email: payload.email })
  return r.data
}

export async function register(payload) {
  const r = await api.post('/api/v1/auth/register', payload)
  const token = r.data.access_token || r.data.token || r.data.accessToken
  setAuth(token, r.data.user || { email: payload.email, name: payload.name })
  return r.data
}

export async function forgotPassword(payload) {
  const r = await api.post('/api/v1/auth/forgot-password', payload)
  return r.data
}
