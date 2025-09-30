<template>
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
    <div class="lg:col-span-2 card p-5">
      <div class="flex items-center justify-between mb-4">
        <div>
          <div class="text-white/60 text-sm">Profile</div>
          <div class="text-xl font-bold">Your info</div>
        </div>
        <button class="btn-ghost border rounded-xl px-4 py-2" @click="load">Refresh</button>
      </div>

      <form @submit.prevent="save" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <input v-model="form.full_name" class="input" placeholder="Name"/>
        <input v-model="form.email" type="email" class="input" placeholder="Email"/>
        <input v-model="form.username" class="input" placeholder="Username"/>
        <input v-model="form.phone" class="input" placeholder="Phone"/>
        <button class="btn sm:col-span-2 justify-center" :disabled="saving">
          {{ saving ? 'Saving...' : 'Save changes' }}
        </button>
      </form>

      <div v-if="message" class="mt-3 p-3 rounded-xl" :class="messageClass">
        {{ message }}
      </div>
    </div>

    <div class="card p-5">
      <div class="text-white/60 text-sm">Security</div>
      <div class="text-lg font-bold mb-3">API token</div>
      <code class="block rounded-xl bg-black/40 p-3 border border-white/10 break-all text-xs">
        {{ token || '—' }}
      </code>
    </div>
  </div>
</template>

<script setup>
import {ref, onMounted} from 'vue'
import {api, getToken} from '@/services/api'
import {useAuthStore} from '@/stores/auth'

const token = getToken()
const authStore = useAuthStore()

const form = ref({
  full_name: '',
  email: '',
  username: '',
  phone: ''
})
const saving = ref(false)
const message = ref('')
const messageClass = ref('')

async function load() {
  try {
    // Fixed route: removed duplicate "users"
    const r = await api.get('/api/v1/users/profile')
    form.value = {
      full_name: r.data.full_name || '',
      email: r.data.email || '',
      username: r.data.username || '',
      phone: r.data.phone || ''
    }

    // Update auth store with latest user data
    if (authStore && authStore.updateUser) {
      authStore.updateUser(r.data)
    }
  } catch (error) {
    console.error('Load error:', error)
    // fallback demo identity
    form.value = {
      full_name: 'Alex Doe',
      email: 'alex@example.com',
      username: 'alexdoe',
      phone: ''
    }
  }
}

async function save() {
  saving.value = true
  message.value = ''

  try {
    // Fixed route: removed duplicate "users"
    const response = await api.put('/api/v1/users/profile', form.value)

    message.value = 'Profile updated successfully!'
    messageClass.value = 'bg-green-500/20 border border-green-500/30 text-green-400'

    // Update auth store to refresh sidebar
    if (authStore && authStore.updateUser) {
      authStore.updateUser(response.data)
    }

    // Update localStorage user data
    const currentUser = JSON.parse(localStorage.getItem('eventaic:user') || '{}')
    const updatedUser = {
      ...currentUser,
      full_name: response.data.full_name,
      email: response.data.email,
      username: response.data.username,
      phone: response.data.phone
    }
    localStorage.setItem('eventaic:user', JSON.stringify(updatedUser))

    // Trigger a custom event to notify sidebar of changes
    window.dispatchEvent(new CustomEvent('user-updated', {detail: updatedUser}))

    // Clear message after 3 seconds
    setTimeout(() => {
      message.value = ''
    }, 3000)

  } catch (error) {
    console.error('Save error:', error)
    message.value = error.response?.data?.detail || 'Failed to save. Please try again.'
    messageClass.value = 'bg-red-500/20 border border-red-500/30 text-red-400'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>