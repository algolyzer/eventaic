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
        <input v-model="form.company_name" class="input" placeholder="Company name" required />
        <input v-model="form.website" class="input" placeholder="Website" />
        <input v-model="form.industry" class="input" placeholder="Industry" />
        <input v-model="form.size" class="input" placeholder="Company size" />
        <textarea v-model="form.brand_tone" class="input h-24 sm:col-span-2" placeholder="Brand tone"></textarea>
        <button class="btn sm:col-span-2 justify-center">Save</button>
      </form>
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
import { ref, onMounted } from 'vue'
import { api } from '@/services/api'

const form = ref({ company_name: '', website: '', industry: '', size: '', brand_tone: '' })

async function load() {
  try {
    const r = await api.get('/api/v1/company/company/profile')
    Object.assign(form.value, r.data)
  } catch {
    // Fill with demo
    form.value = { company_name: 'Eventaic Inc.', website: 'https://eventaic.com', industry: 'AdTech', size: '11-50', brand_tone: 'Bold, clear, helpful.' }
  }
}

async function save() {
  try {
    await api.put('/api/v1/company/company/profile', form.value)
    alert('Saved company profile!')
  } catch (e) {
    alert('Save failed: ' + (e.message || 'unknown'))
  }
}

onMounted(load)
</script>
