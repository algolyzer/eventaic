<template>
  <div class="space-y-6">
    <div>
      <div class="badge">Admin</div>
      <h1 class="text-2xl md:text-3xl font-extrabold tracking-tight mt-1">Admin Overview</h1>
      <p class="text-white/60">System health and controls</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <StatWidget ic="💾" label="Queue depth" :value="sys.queue" :trend="-2" />
      <StatWidget ic="⚙️" label="Workers" :value="sys.workers" :trend="0" />
      <StatWidget ic="🔒" label="Auth errors" :value="sys.authErrors" :trend="-12" />
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <ChartCard title="Requests per minute" subtitle="API traffic" :labels="labels" :series="[{label:'RPM', data: rpm}]" />
      <ChartCard title="Latency (p95)" subtitle="ms" :labels="labels" :series="[{label:'Latency', data: lat}]" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import StatWidget from '@/components/StatWidget.vue'
import ChartCard from '@/components/ChartCard.vue'
import { api } from '@/services/api'

const sys = ref({ queue: 0, workers: 0, authErrors: 0 })
const labels = ref([]), rpm = ref([]), lat = ref([])

onMounted(async () => {
  try {
    const r = await api.get('/api/v1/admin/overview')
    sys.value = r.data.sys
    labels.value = r.data.labels
    rpm.value = r.data.rpm
    lat.value = r.data.lat
  } catch {
    sys.value = { queue: 7, workers: 4, authErrors: 1 }
    labels.value = Array.from({ length: 12 }, (_, i) => `T${i+1}`)
    rpm.value = labels.value.map((_, i) => 40 + Math.sin(i/1.5)*10 + Math.random()*6)
    lat.value = labels.value.map(() => 120 + Math.random()*50)
  }
})
</script>
