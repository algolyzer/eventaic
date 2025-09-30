<template>
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
    <div class="lg:col-span-2 card p-5">
      <div class="flex items-center justify-between mb-4">
        <div>
          <div class="text-white/60 text-sm">Company</div>
          <div class="text-xl font-bold">Profile</div>
        </div>
        <button class="btn-ghost border rounded-xl px-4 py-2" @click="load">Refresh</button>
      </div>

      <form @submit.prevent="save" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <input v-model="form.name" class="input" placeholder="Company name" required/>
        <input v-model="form.website" class="input" placeholder="Website"/>
        <input v-model="form.industry" class="input" placeholder="Industry"/>
        <input v-model="form.size" class="input" placeholder="Company size"/>
        <textarea v-model="form.description" class="input h-24 sm:col-span-2" placeholder="Description"></textarea>
        <button class="btn sm:col-span-2 justify-center" :disabled="saving">
          {{ saving ? 'Saving...' : 'Save' }}
        </button>
      </form>

      <div v-if="message" class="mt-3 p-3 rounded-xl" :class="messageClass">
        {{ message }}
      </div>
    </div>

    <div class="card p-5">
      <div class="text-white/60 text-sm">Integrations</div>
      <div class="text-lg font-bold mb-3">Ad Platforms</div>
      <ul class="space-y-2">
        <li class="flex items-center justify-between p-3 rounded-xl border border-white/10">
          <span>Google Ads</span>
          <button class="btn-ghost border rounded-xl px-3 py-1">Connect</button>
        </li>
        <li class="flex items-center justify-between p-3 rounded-xl border border-white/10">
          <span>Meta</span>
          <button class="btn-ghost border rounded-xl px-3 py-1">Connect</button>
        </li>
        <li class="flex items-center justify-between p-3 rounded-xl border border-white/10">
          <span>LinkedIn</span>
          <button class="btn-ghost border rounded-xl px-3 py-1">Connect</button>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import {ref, onMounted} from 'vue'
import {api} from '@/services/api'

const form = ref({
  name: '',
  website: '',
  industry: '',
  size: '',
  description: ''
})
const saving = ref(false)
const message = ref('')
const messageClass = ref('')

async function load() {
  try {
    // Fixed route: removed duplicate "company"
    const r = await api.get('/api/v1/company/profile')
    Object.assign(form.value, {
      name: r.data.name || '',
      website: r.data.website || '',
      industry: r.data.industry || '',
      size: r.data.size || '',
      description: r.data.description || ''
    })
  } catch (error) {
    console.error('Load error:', error)
    // Fill with demo data if API fails
    form.value = {
      name: 'Eventaic Inc.',
      website: 'https://eventaic.com',
      industry: 'AdTech',
      size: '11-50',
      description: 'Event-responsive ad generation platform.'
    }
  }
}

async function save() {
  saving.value = true
  message.value = ''

  try {
    // Fixed route: removed duplicate "company"
    await api.put('/api/v1/company/profile', form.value)

    message.value = 'Company profile saved successfully!'
    messageClass.value = 'bg-green-500/20 border border-green-500/30 text-green-400'

    // Clear message after 3 seconds
    setTimeout(() => {
      message.value = ''
    }, 3000)

    // Refresh to ensure data is in sync
    await load()
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