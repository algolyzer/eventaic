import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export const api = axios.create({
    baseURL: BASE_URL,
    headers: {
        'Content-Type': 'application/json'
    }
})

// Request interceptor
api.interceptors.request.use(
    (config) => {
        const token = getToken()
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`
        }
        return config
    },
    (error) => Promise.reject(error)
)

// Response interceptor
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config

        // Handle 401 errors (unauthorized)
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true

            // Try to refresh token
            const refreshToken = localStorage.getItem('eventaic:refresh_token')
            if (refreshToken) {
                try {
                    const response = await api.post('/api/v1/auth/refresh', {
                        refresh_token: refreshToken
                    })
                    const {access_token, user} = response.data
                    setAuth(access_token, user)

                    // Retry original request with new token
                    originalRequest.headers['Authorization'] = `Bearer ${access_token}`
                    return api(originalRequest)
                } catch (refreshError) {
                    // Refresh failed, redirect to login
                    clearAuth()
                    window.location.href = '/app/auth/login?message=Session expired. Please login again.'
                    return Promise.reject(refreshError)
                }
            } else {
                // No refresh token, redirect to login
                clearAuth()
                window.location.href = '/app/auth/login'
            }
        }

        const message = error.response?.data?.detail || error.message || 'Request failed'
        return Promise.reject(new Error(message))
    }
)

// Local storage helpers
const TOKEN_KEY = 'eventaic:token'
const USER_KEY = 'eventaic:user'
const REFRESH_TOKEN_KEY = 'eventaic:refresh_token'

export function setAuth(token, user) {
    if (token) {
        localStorage.setItem(TOKEN_KEY, token)
    }
    if (user) {
        localStorage.setItem(USER_KEY, JSON.stringify(user))
    }
}

export function clearAuth() {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
}

export function getToken() {
    return localStorage.getItem(TOKEN_KEY)
}

export function getUser() {
    try {
        const userStr = localStorage.getItem(USER_KEY)
        return userStr ? JSON.parse(userStr) : null
    } catch {
        return null
    }
}

// Auth API methods
export async function login(credentials) {
    try {
        // Backend expects 'username' field which can be email or username
        const payload = {
            username: credentials.email || credentials.username,
            password: credentials.password
        }

        const response = await api.post('/api/v1/auth/login', payload)
        const {access_token, refresh_token, user} = response.data

        // Store tokens and user data
        setAuth(access_token, user)
        if (refresh_token) {
            localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token)
        }

        return response.data
    } catch (error) {
        console.error('Login error:', error)
        throw error
    }
}

export async function register(data) {
    try {
        const response = await api.post('/api/v1/auth/register', data)
        const {access_token, refresh_token, user} = response.data

        // Store tokens and user data
        setAuth(access_token, user)
        if (refresh_token) {
            localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token)
        }

        return response.data
    } catch (error) {
        console.error('Register error:', error)
        throw error
    }
}

export async function logout() {
    try {
        await api.post('/api/v1/auth/logout')
    } catch (error) {
        // Even if logout fails, clear local storage
        console.error('Logout error:', error)
    } finally {
        clearAuth()
    }
}

export async function forgotPassword(data) {
    return await api.post('/api/v1/auth/password-reset/request', data)
}

export async function resetPassword(token, newPassword) {
    return await api.post('/api/v1/auth/password-reset/confirm', {
        token,
        new_password: newPassword
    })
}

export async function verifyEmail(token) {
    return await api.post('/api/v1/auth/verify-email', {token})
}

export async function getCurrentUser() {
    try {
        const response = await api.get('/api/v1/auth/me')
        return response.data
    } catch (error) {
        console.error('Get current user error:', error)
        throw error
    }
}