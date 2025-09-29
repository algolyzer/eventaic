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
                username: credentials.email,
                password: credentials.password
            })
            const token = response.data.access_token
            state.token = token
            state.user = response.data.user || {email: credentials.email}
            setAuth(token, state.user)
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
            state.token = token
            state.user = response.data.user || {email: data.email}
            setAuth(token, state.user)
            return response.data
        } catch (err) {
            state.error = err.message
            throw err
        } finally {
            state.loading = false
        }
    }

    const logout = () => {
        state.user = null
        state.token = null
        clearAuth()
    }

    return {
        isAuthenticated,
        currentUser,
        loading,
        error,
        login,
        register,
        logout
    }
}