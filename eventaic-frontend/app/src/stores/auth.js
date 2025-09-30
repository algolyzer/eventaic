import {reactive, computed} from 'vue'
import {api, setAuth, clearAuth} from '@/services/api'

const state = reactive({
    user: null,
    token: localStorage.getItem('eventaic:token'),
    loading: false,
    error: null
})

export const useAuthStore = () => {
    const isAuthenticated = computed(() => !!state.token)
    const currentUser = computed(() => state.user)
    const loading = computed(() => state.loading)
    const error = computed(() => state.error)

    const login = async (credentials) => {
        state.loading = true
        state.error = null
        try {
            const response = await api.post('/api/v1/auth/login', {
                username: credentials.email || credentials.username,
                password: credentials.password
            })
            const token = response.data.access_token
            const user = response.data.user || {email: credentials.email}

            state.token = token
            state.user = user
            setAuth(token, user)

            return response.data
        } catch (err) {
            state.error = err.message
            throw err
        } finally {
            state.loading = false
        }
    }

    const register = async (data) => {
        state.loading = true
        state.error = null
        try {
            const response = await api.post('/api/v1/auth/register', data)
            const token = response.data.access_token
            const user = response.data.user || {email: data.email}

            state.token = token
            state.user = user
            setAuth(token, user)

            return response.data
        } catch (err) {
            state.error = err.message
            throw err
        } finally {
            state.loading = false
        }
    }

    const updateUser = (userData) => {
        // Update state
        state.user = {
            ...state.user,
            ...userData
        }

        // Update localStorage
        try {
            const currentUser = JSON.parse(localStorage.getItem('eventaic:user') || '{}')
            const updatedUser = {
                ...currentUser,
                ...userData
            }
            localStorage.setItem('eventaic:user', JSON.stringify(updatedUser))
        } catch (error) {
            console.error('Error updating user in localStorage:', error)
        }
    }

    const logout = () => {
        state.user = null
        state.token = null
        clearAuth()
    }

    // Load user from localStorage on init
    const loadUser = () => {
        try {
            const userStr = localStorage.getItem('eventaic:user')
            if (userStr) {
                state.user = JSON.parse(userStr)
            }
        } catch (error) {
            console.error('Error loading user from localStorage:', error)
        }
    }

    // Initialize user data
    loadUser()

    return {
        isAuthenticated,
        currentUser,
        loading,
        error,
        login,
        register,
        logout,
        updateUser,
        loadUser
    }
}