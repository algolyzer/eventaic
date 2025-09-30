<template>
  <div>
    <h2 class="text-xl font-bold mb-2">Create your account</h2>
    <p class="text-white/60 mb-6">Start generating event-driven campaigns</p>

    <form @submit.prevent="submit" class="space-y-3">
      <div>
        <input
            v-model="form.full_name"
            type="text"
            class="input"
            placeholder="Your full name"
            required
            autocomplete="name"
            :disabled="loading"
        />
      </div>

      <div>
        <input
            v-model="form.email"
            type="email"
            class="input"
            placeholder="you@company.com"
            required
            autocomplete="email"
            :disabled="loading"
        />
      </div>

      <div>
        <input
            v-model="form.company_name"
            type="text"
            class="input"
            placeholder="Company name"
            required
            :disabled="loading"
        />
      </div>

      <div>
        <input
            v-model="form.password"
            type="password"
            class="input"
            placeholder="Create a password (min 8 characters)"
            required
            autocomplete="new-password"
            :disabled="loading"
        />
        <p class="text-xs text-white/50 mt-1">
          Must contain uppercase, lowercase, number, and special character
        </p>
      </div>

      <button
          type="submit"
          class="btn w-full justify-center"
          :disabled="loading"
      >
        <span v-if="loading">Creating account...</span>
        <span v-else>Create account</span>
      </button>
    </form>

    <div class="mt-4 text-sm">
      Already have an account?
      <RouterLink class="link" to="/auth/login">Log in</RouterLink>
    </div>

    <Toast :show="toast.show" :title="toast.title" :message="toast.msg"/>
  </div>
</template>

<script setup>
import {ref} from 'vue'
import {RouterLink, useRouter} from 'vue-router'
import {api, setAuth} from '@/services/api'
import Toast from '@/components/Toast.vue'

const router = useRouter()

const form = ref({
  full_name: '',
  email: '',
  company_name: '',
  password: ''
})

const loading = ref(false)
const toast = ref({show: false, title: '', msg: ''})

async function submit() {
  // Validate inputs
  if (!form.value.full_name.trim() || !form.value.email.trim() ||
      !form.value.company_name.trim() || !form.value.password) {
    toast.value = {
      show: true,
      title: 'Validation Error',
      msg: 'Please fill in all required fields'
    }
    return
  }

  loading.value = true
  toast.value.show = false

  try {
    console.log('🔐 Attempting registration...')

    // Generate username from email (part before @)
    const username = form.value.email.split('@')[0].toLowerCase().replace(/[^a-z0-9_-]/g, '')

    // Send registration request
    const response = await api.post('/api/v1/auth/register', {
      email: form.value.email.trim(),
      username: username,
      full_name: form.value.full_name.trim(),
      password: form.value.password,
      company_name: form.value.company_name.trim()
    })

    console.log('✅ Registration response:', response.data)

    // Extract data from response
    const {access_token, refresh_token, user} = response.data

    if (!access_token) {
      throw new Error('No access token in response')
    }

    // Create user object with fallbacks
    const userData = user || {}
    const userForStorage = {
      id: userData.id || 'unknown',
      email: userData.email || form.value.email,
      username: userData.username || username,
      full_name: userData.full_name || form.value.full_name,
      name: userData.full_name || form.value.full_name,
      role: userData.role || 'company',
      company_id: userData.company_id || null,
      company_name: userData.company_name || form.value.company_name
    }

    console.log('✅ User data prepared:', userForStorage)

    // Store auth data
    setAuth(access_token, userForStorage)

    // Store refresh token
    if (refresh_token) {
      localStorage.setItem('eventaic:refresh_token', refresh_token)
    }

    // Dispatch events
    window.dispatchEvent(new CustomEvent('user-logged-in', {detail: userForStorage}))
    window.dispatchEvent(new CustomEvent('user-updated', {detail: userForStorage}))

    // Show success
    toast.value = {
      show: true,
      title: 'Success',
      msg: `Welcome to Eventaic, ${userForStorage.name}!`
    }

    // Redirect to dashboard
    setTimeout(() => {
      router.replace('/dashboard')
    }, 500)

  } catch (error) {
    console.error('❌ Registration error:', error)
    console.error('Error details:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status
    })

    // Determine error message
    let errorMessage = 'Registration failed. Please try again.'

    if (error.response) {
      const status = error.response.status
      const detail = error.response.data?.detail

      if (status === 400) {
        if (typeof detail === 'string' && detail.includes('Email')) {
          errorMessage = 'This email is already registered'
        } else if (typeof detail === 'string' && detail.includes('Username')) {
          errorMessage = 'This username is already taken'
        } else {
          errorMessage = detail || 'Invalid registration data'
        }
      } else if (detail) {
        errorMessage = detail
      }
    } else if (error.message) {
      errorMessage = error.message
    }

    toast.value = {
      show: true,
      title: 'Registration Failed',
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
</style>