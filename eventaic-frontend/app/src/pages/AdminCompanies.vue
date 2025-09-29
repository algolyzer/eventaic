<template>
  <div class="space-y-4">
    <div>
      <div class="text-white/60 text-sm">Admin</div>
      <div class="text-xl font-bold">Companies</div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <div v-for="c in companies" :key="c.id" class="card p-5">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-white/10 grid place-items-center">🏢</div>
          <div class="min-w-0">
            <div class="font-semibold truncate">{{ c.name }}</div>
            <div class="text-sm text-white/60 truncate">{{ c.domain }}</div>
          </div>
          <span class="ml-auto badge">{{ c.plan }}</span>
        </div>
        <div class="mt-3 text-sm text-white/60">{{ c.note }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/services/api'

const companies = ref([])

onMounted(async () => {
  try {
    const r = await api.get('/api/v1/admin/companies')
    companies.value = r.data.companies
  } catch {
    companies.value = [
      { id: 1, name: 'Eventaic Inc.', domain: 'eventaic.com', plan: 'Scale', note: 'High throughput' },
      { id: 2, name: 'Northwind', domain: 'northwind.test', plan: 'Launch', note: 'Evaluating beta' },
      { id: 3, name: 'Contoso', domain: 'contoso.test', plan: 'Custom', note: 'SSO + SLAs' },
    ]
  }
})
</script>
