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
        />
      </div>

      <div class="flex items-center justify-between">
        <label class="flex items-center text-sm">
          <input
              v-model="rememberMe"
              type="checkbox"
              class="mr-2 rounded border-white/20"
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

const router = useRouter()
const route = useRoute()

const credentials = ref({
  username: '',  // This field accepts email or username
  password: ''
})
const rememberMe = ref(false)
const loading = ref(false)
const toast = ref({show: false, title: '', msg: ''})

// Check if user was redirected here
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
  loading.value = true
  toast.value.show = false

  try {
    // Send login request
    // Backend expects 'username' field which can contain email or username
    const response = await api.post('/api/v1/auth/login', {
      username: credentials.value.username.trim(),
      password: credentials.value.password
    })

    // Extract tokens and user data
    const {access_token, refresh_token, user} = response.data

    // Store auth data
    setAuth(access_token, user)

    // Store refresh token if remember me is checked
    if (rememberMe.value && refresh_token) {
      localStorage.setItem('eventaic:refresh_token', refresh_token)
    }

    // Show success message
    toast.value = {
      show: true,
      title: 'Success',
      msg: 'Login successful! Redirecting...'
    }

    // Redirect after a brief delay
    setTimeout(() => {
      const redirectTo = route.query.redirect || '/dashboard'
      router.replace(redirectTo)
    }, 1000)

  } catch (error) {
    console.error('Login error:', error)

    // Show error message
    toast.value = {
      show: true,
      title: 'Login failed',
      msg: error.response?.data?.detail || error.message || 'Invalid credentials. Please try again.'
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

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Checkbox styling */
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
</style>