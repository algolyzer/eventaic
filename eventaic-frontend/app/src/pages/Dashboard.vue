<template>
  <div class="space-y-6">
    <!-- Headline -->
    <div class="flex flex-col sm:flex-row sm:items-end gap-3">
      <div>
        <div class="badge">Live</div>
        <h1 class="text-2xl md:text-3xl font-extrabold tracking-tight mt-1">Dashboard</h1>
        <p class="text-white/60">From signal → spend. Your system at a glance.</p>
      </div>
      <div class="sm:ml-auto flex gap-2">
        <RouterLink to="/company" class="btn-ghost border rounded-xl px-4 py-2">Company</RouterLink>
        <a href="/" class="btn rounded-xl px-4 py-2">Landing</a>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
      <StatWidget ic="📡" label="Events processed" :value="stats.events" :trend="12" />
      <StatWidget ic="🧠" label="Creatives generated" :value="stats.creatives" :trend="8" />
      <StatWidget ic="🧪" label="Avg quality score" :value="stats.quality + '/10'" :trend="4" />
      <StatWidget ic="📈" label="Predicted CTR" :value="stats.ctr + '%'" :trend="3" />
    </div>

    <!-- Charts -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-4">
      <ChartCard class="lg:col-span-3" title="CTR over time" subtitle="Predicted %" :labels="labels" :series="[{label:'CTR %', data: ctrData}]" type="line" />
      <ChartCard class="lg:col-span-2" title="Quality components" subtitle="Avg by day" :labels="labels"
        :series="[
          {label:'Relevance', data: relData},
          {label:'Clarity', data: clrData},
          {label:'Persuasion', data: psuData},
        ]" type="bar" />
    </div>

    <!-- Recent Activity -->
    <div class="grid grid-cols-1 xl:grid-cols-3 gap-4">
      <div class="xl:col-span-2 card">
        <div class="p-5 border-b border-white/10 flex items-center justify-between">
          <div class="font-bold">Recent events</div>
          <div class="text-sm text-white/60">Last 24h</div>
        </div>
        <ul class="divide-y divide-white/10">
          <li v-for="e in events" :key="e.id" class="p-5 flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-white/10 grid place-items-center">⚡</div>
            <div class="min-w-0">
              <div class="font-medium truncate">{{ e.title }}</div>
              <div class="text-sm text-white/60 truncate">{{ e.desc }}</div>
            </div>
            <div class="ml-auto text-sm text-white/50">{{ e.time }}</div>
          </li>
        </ul>
      </div>

      <div class="card p-5">
        <div class="font-bold mb-3">Tasks</div>
        <ul class="space-y-2">
          <li v-for="t in tasks" :key="t.id" class="flex items-center gap-3 p-3 rounded-xl border border-white/10">
            <input type="checkbox" class="accent-brand-violet" v-model="t.done" />
            <div class="min-w-0">
              <div class="font-medium" :class="t.done ? 'line-through text-white/50' : ''">{{ t.title }}</div>
              <div class="text-xs text-white/50">{{ t.note }}</div>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import StatWidget from '@/components/StatWidget.vue'
import ChartCard from '@/components/ChartCard.vue'
import { api } from '@/services/api'

const stats = ref({ events: 0, creatives: 0, quality: 0, ctr: 0 })
const labels = ref([])
const ctrData = ref([])
const relData = ref([])
const clrData = ref([])
const psuData = ref([])
const events = ref([])
const tasks = ref([
  { id: 1, title: 'Wire Meta Ads account', note: 'Connect OAuth in settings', done: false },
  { id: 2, title: 'Define event thresholds', note: 'Black Friday + NYC weather', done: true },
  { id: 3, title: 'Publish first creative', note: 'Use auto-evaluate loop', done: false },
])

onMounted(async () => {
  // Try fetching metrics; fallback to demo if API not ready
  try {
    const r = await api.get('/api/v1/metrics/dashboard')
    Object.assign(stats.value, r.data.stats)
    labels.value = r.data.labels
    ctrData.value = r.data.ctr
    relData.value = r.data.rel
    clrData.value = r.data.clr
    psuData.value = r.data.psu
    events.value = r.data.events
  } catch {
    // Demo data
    stats.value = { events: 120, creatives: 48, quality: 8.9, ctr: 4.7 }
    labels.value = Array.from({ length: 14 }, (_, i) => `D${i+1}`)
    ctrData.value = labels.value.map((_, i) => 3.6 + Math.sin(i/2)*.6 + Math.random()*0.3)
    relData.value = labels.value.map(() => 8.5 + Math.random()*0.6)
    clrData.value = labels.value.map(() => 8.1 + Math.random()*0.6)
    psuData.value = labels.value.map(() => 8.8 + Math.random()*0.6)
    events.value = [
      { id: 1, title: 'Black Friday: Electronics', desc: 'NYC surge detected', time: '4m ago' },
      { id: 2, title: 'Rain in SF', desc: 'Context switch to umbrellas creative', time: '18m ago' },
      { id: 3, title: 'Viral tweet detected', desc: 'Auto-matching hashtag appended', time: '1h ago' },
      { id: 4, title: 'Holiday: Diwali', desc: 'Localized creatives queued', time: '3h ago' },
    ]
  }
})
</script>
