<template>
  <div>
    <h2 class="text-xl font-bold mb-2">Welcome back</h2>
    <p class="text-white/60 mb-6">Log in to your Eventaic account</p>

    <form @submit.prevent="submit" class="space-y-3">
      <div>
        <input
            v-model="credentials.username"
            type="text"
            class="input"
            placeholder="Email or username"
            required
            autocomplete="username"
            :disabled="loading"
        />
      </div>

      <div>
        <input
            v-model="credentials.password"
            type="password"
            class="input"
            placeholder="Password"
            required
            autocomplete="current-password"
            :disabled="loading"
        />
      </div>

      <div class="flex items-center justify-between">
        <label class="flex items-center text-sm">
          <input
              v-model="rememberMe"
              type="checkbox"
              class="mr-2 rounded border-white/20"
              :disabled="loading"
          />
          <span class="text-white/70">Remember me</span>
        </label>
      </div>

      <button
          type="submit"
          class="btn w-full justify-center"
          :disabled="loading"
      >
        <span v-if="loading">Logging in...</span>
        <span v-else>Log in</span>
      </button>
    </form>

    <div class="mt-4 flex justify-between text-sm">
      <RouterLink class="link" to="/auth/forgot">Forgot password?</RouterLink>
      <RouterLink class="link" to="/auth/register">Create account</RouterLink>
    </div>

    <Toast :show="toast.show" :title="toast.title" :message="toast.msg"/>
  </div>
</template>

<script setup>
import {ref, onMounted} from 'vue'
import {useRouter, useRoute, RouterLink} from 'vue-router'
import Toast from '@/components/Toast.vue'
import {api, setAuth} from '@/services/api'
import {useAuthStore} from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const credentials = ref({
  username: '',
  password: ''
})
const rememberMe = ref(false)
const loading = ref(false)
const toast = ref({show: false, title: '', msg: ''})

onMounted(() => {
  if (route.query.message) {
    toast.value = {
      show: true,
      title: 'Info',
      msg: route.query.message
    }
  }
})

async function submit() {
  // Validate inputs
  if (!credentials.value.username.trim() || !credentials.value.password) {
    toast.value = {
      show: true,
      title: 'Validation Error',
      msg: 'Please enter both username/email and password'
    }
    return
  }

  loading.value = true
  toast.value.show = false

  try {
    console.log('🔐 Attempting login...')

    // Send login request
    const response = await api.post('/api/v1/auth/login', {
      username: credentials.value.username.trim(),
      password: credentials.value.password
    })

    console.log('✅ Login response:', response.data)

    // Extract data from response
    const {access_token, refresh_token, user} = response.data

    // Basic validation
    if (!access_token) {
      throw new Error('No access token in response')
    }

    // Create user object with fallbacks
    const userData = user || {}
    const userForStorage = {
      id: userData.id || 'unknown',
      email: userData.email || credentials.value.username,
      username: userData.username || credentials.value.username,
      full_name: userData.full_name || userData.name || userData.username || 'User',
      name: userData.full_name || userData.name || userData.username || 'User',
      role: userData.role || 'company',
      company_id: userData.company_id || null,
      company_name: userData.company_name || null
    }

    console.log('✅ User data prepared:', userForStorage)

    // Store auth data
    setAuth(access_token, userForStorage)
    console.log('✅ Auth stored')

    // Store refresh token if remember me
    if (rememberMe.value && refresh_token) {
      localStorage.setItem('eventaic:refresh_token', refresh_token)
      console.log('✅ Refresh token stored')
    }

    // Update auth store
    if (authStore && authStore.updateUser) {
      authStore.updateUser(userForStorage)
      console.log('✅ Auth store updated')
    }

    // Dispatch events for components
    window.dispatchEvent(new CustomEvent('user-logged-in', {
      detail: userForStorage
    }))
    console.log('✅ Login event dispatched')

    window.dispatchEvent(new CustomEvent('user-updated', {
      detail: userForStorage
    }))
    console.log('✅ User update event dispatched')

    // Show success
    toast.value = {
      show: true,
      title: 'Success',
      msg: `Welcome back, ${userForStorage.name}!`
    }

    // Redirect
    setTimeout(() => {
      const redirectTo = route.query.redirect || '/dashboard'
      console.log('🚀 Redirecting to:', redirectTo)
      router.replace(redirectTo)
    }, 500)

  } catch (error) {
    console.error('❌ Login error:', error)
    console.error('Error details:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status
    })

    // Determine error message
    let errorMessage = 'Login failed. Please try again.'

    if (error.response) {
      const status = error.response.status
      const detail = error.response.data?.detail

      if (status === 401) {
        errorMessage = detail || 'Incorrect username/email or password'
      } else if (status === 403) {
        errorMessage = detail || 'Access denied. Please verify your email.'
      } else if (status === 429) {
        errorMessage = 'Too many login attempts. Please try again later.'
      } else if (detail) {
        errorMessage = detail
      }
    } else if (error.message) {
      errorMessage = error.message
    }

    toast.value = {
      show: true,
      title: 'Login Failed',
      msg: errorMessage
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.input:focus {
  outline: none;
  border-color: rgba(124, 92, 255, 0.5);
  box-shadow: 0 0 0 3px rgba(124, 92, 255, 0.1);
}

.input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

input[type="checkbox"] {
  width: 1rem;
  height: 1rem;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 3px;
  cursor: pointer;
}

input[type="checkbox"]:checked {
  background: linear-gradient(135deg, #7c5cff, #00d4ff);
  border-color: transparent;
}

input[type="checkbox"]:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.link {
  transition: opacity 0.2s;
}

.link:hover {
  opacity: 0.8;
}
</style>