import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export const api = axios.create({
    baseURL: BASE_URL,
    timeout: 10000, // 10 second timeout
    headers: {
        'Content-Type': 'application/json'
    }
})

// Track retry attempts to prevent infinite loops
const retryTracker = new Map()

// Request interceptor
api.interceptors.request.use(
    (config) => {
        const token = getToken()
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`
        }

        // Add request ID for tracking
        config.requestId = `${config.url}_${Date.now()}`

        return config
    },
    (error) => {
        console.error('Request error:', error)
        return Promise.reject(error)
    }
)

// Response interceptor with retry limit
api.interceptors.response.use(
    (response) => {
        // Clear retry count on success
        if (response.config.requestId) {
            retryTracker.delete(response.config.requestId)
        }
        return response
    },
    async (error) => {
        const originalRequest = error.config

        // If no config, just reject
        if (!originalRequest) {
            return Promise.reject(error)
        }

        // Track retry attempts
        const requestId = originalRequest.requestId || 'unknown'
        const retryCount = retryTracker.get(requestId) || 0

        // Max 2 retry attempts
        if (retryCount >= 2) {
            retryTracker.delete(requestId)
            console.error('Max retries reached for:', originalRequest.url)
            return Promise.reject(error)
        }

        // Handle 401 errors (unauthorized)
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true
            retryTracker.set(requestId, retryCount + 1)

            // Try to refresh token only once
            const refreshToken = localStorage.getItem('eventaic:refresh_token')
            if (refreshToken && retryCount === 0) {
                try {
                    const response = await axios.post(
                        `${BASE_URL}/api/v1/auth/refresh`,
                        {refresh_token: refreshToken},
                        {timeout: 5000}
                    )

                    const {access_token, user} = response.data
                    setAuth(access_token, user)

                    // Retry original request with new token
                    originalRequest.headers['Authorization'] = `Bearer ${access_token}`
                    return api(originalRequest)
                } catch (refreshError) {
                    console.error('Token refresh failed:', refreshError)
                    clearAuth()

                    // Only redirect if not already on login page
                    if (!window.location.pathname.includes('/auth/login')) {
                        window.location.href = '/app/auth/login?message=Session expired'
                    }
                    return Promise.reject(refreshError)
                }
            } else {
                // No refresh token or already retried
                clearAuth()

                // Only redirect if not already on login page
                if (!window.location.pathname.includes('/auth/login')) {
                    window.location.href = '/app/auth/login'
                }
                return Promise.reject(error)
            }
        }

        // Handle network errors
        if (!error.response) {
            console.error('Network error:', error.message)
            return Promise.reject(new Error('Network error. Please check your connection.'))
        }

        // Handle other errors
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
    // Clear retry tracker
    retryTracker.clear()
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

// Auth API methods with timeout
export async function login(credentials) {
    try {
        const payload = {
            username: credentials.email || credentials.username,
            password: credentials.password
        }

        const response = await api.post('/api/v1/auth/login', payload, {
            timeout: 10000 // 10 second timeout
        })

        const {access_token, refresh_token, user} = response.data

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
        const response = await api.post('/api/v1/auth/register', data, {
            timeout: 10000
        })

        const {access_token, refresh_token, user} = response.data

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
        await api.post('/api/v1/auth/logout', {}, {timeout: 5000})
    } catch (error) {
        // Even if logout fails, clear local storage
        console.error('Logout error:', error)
    } finally {
        clearAuth()
    }
}

export async function forgotPassword(data) {
    return await api.post('/api/v1/auth/password-reset/request', data, {
        timeout: 10000
    })
}

export async function resetPassword(token, newPassword) {
    return await api.post('/api/v1/auth/password-reset/confirm', {
        token,
        new_password: newPassword
    }, {
        timeout: 10000
    })
}

export async function verifyEmail(token) {
    return await api.post('/api/v1/auth/verify-email', {token}, {
        timeout: 10000
    })
}

export async function getCurrentUser() {
    try {
        const response = await api.get('/api/v1/auth/me', {
            timeout: 5000
        })
        return response.data
    } catch (error) {
        console.error('Get current user error:', error)
        throw error
    }
}