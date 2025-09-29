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
        <input v-model="form.name" class="input" placeholder="Name" />
        <input v-model="form.email" type="email" class="input" placeholder="Email" />
        <input v-model="form.title" class="input sm:col-span-2" placeholder="Title (e.g., Growth Lead)" />
        <button class="btn sm:col-span-2 justify-center">Save changes</button>
      </form>
    </div>

    <div class="card p-5">
      <div class="text-white/60 text-sm">Security</div>
      <div class="text-lg font-bold mb-3">API token</div>
      <code class="block rounded-xl bg-black/40 p-3 border border-white/10 break-all">{{ token || '—' }}</code>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api, getToken } from '@/services/api'

const token = getToken()
const form = ref({ name: '', email: '', title: '' })

async function load() {
  try {
    const r = await api.get('/api/v1/users/users/profile')
    form.value = { name: r.data.name, email: r.data.email, title: r.data.title ?? '' }
  } catch {
    // fallback demo identity
    form.value = { name: 'Alex Doe', email: 'alex@example.com', title: 'Growth Lead' }
  }
}

async function save() {
  try {
    await api.put('/api/v1/users/users/profile', form.value)
    alert('Saved!')
  } catch (e) {
    alert('Save failed: ' + (e.message || 'unknown'))
  }
}

onMounted(load)
</script>
