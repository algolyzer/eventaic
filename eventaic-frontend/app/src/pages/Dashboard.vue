<template>
  <div class="space-y-6">
    <!-- Headline -->
    <div class="flex flex-col sm:flex-row sm:items-end gap-3">
      <div>
        <div class="badge">Live</div>
        <h1 class="text-2xl md:text-3xl font-extrabold tracking-tight mt-1">Dashboard</h1>
        <p class="text-white/60">Your event-responsive ad platform at a glance</p>
      </div>
      <div class="sm:ml-auto flex gap-2">
        <RouterLink to="/company" class="btn-ghost border rounded-xl px-4 py-2">Company</RouterLink>
        <a href="/" class="btn rounded-xl px-4 py-2">Landing</a>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
      <div v-for="i in 4" :key="i" class="card p-5 animate-pulse">
        <div class="h-8 bg-white/10 rounded w-20 mb-2"></div>
        <div class="h-10 bg-white/10 rounded w-32"></div>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="card p-5 border-red-500/20 bg-red-500/5">
      <p class="text-red-400">{{ error }}</p>
      <button @click="loadData" class="btn mt-3">Retry</button>
    </div>

    <!-- Stats (with demo data) -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
      <StatWidget
          ic="📡"
          label="Events processed"
          :value="stats.events"
          :trend="12"
      />
      <StatWidget
          ic="🧠"
          label="Ads generated"
          :value="stats.creatives"
          :trend="8"
      />
      <StatWidget
          ic="🧪"
          label="Avg quality score"
          :value="stats.quality + '/10'"
          :trend="4"
      />
      <StatWidget
          ic="📈"
          label="Predicted CTR"
          :value="stats.ctr + '%'"
          :trend="3"
      />
    </div>

    <!-- Charts (only render when data is ready) -->
    <div v-if="!loading && chartsReady" class="grid grid-cols-1 lg:grid-cols-5 gap-4">
      <div class="lg:col-span-3">
        <ChartCard
            title="Performance Trend"
            subtitle="Last 14 days"
            :labels="chartData.labels"
            :series="[{label:'CTR %', data: chartData.ctrData}]"
            type="line"
        />
      </div>
      <div class="lg:col-span-2">
        <ChartCard
            title="Quality Metrics"
            subtitle="Average scores"
            :labels="chartData.labels.slice(0, 5)"
            :series="[
            {label:'Relevance', data: chartData.relData.slice(0, 5)},
            {label:'Clarity', data: chartData.clrData.slice(0, 5)}
          ]"
            type="bar"
        />
      </div>
    </div>

    <!-- Recent Activity -->
    <div class="grid grid-cols-1 xl:grid-cols-3 gap-4">
      <div class="xl:col-span-2 card">
        <div class="p-5 border-b border-white/10 flex items-center justify-between">
          <div class="font-bold">Recent Activity</div>
          <div class="text-sm text-white/60">Last 24h</div>
        </div>
        <ul class="divide-y divide-white/10">
          <li v-for="event in events" :key="event.id" class="p-5 flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-white/10 grid place-items-center">
              <span class="text-xl">{{ event.icon }}</span>
            </div>
            <div class="min-w-0 flex-1">
              <div class="font-medium truncate">{{ event.title }}</div>
              <div class="text-sm text-white/60 truncate">{{ event.desc }}</div>
            </div>
            <div class="text-sm text-white/50">{{ event.time }}</div>
          </li>
        </ul>
      </div>

      <div class="card p-5">
        <div class="font-bold mb-3">Quick Actions</div>
        <div class="space-y-2">
          <RouterLink to="/ads/generate" class="block w-full btn justify-center">
            🚀 Generate Ad
          </RouterLink>
          <RouterLink to="/company" class="block w-full btn-ghost border rounded-xl py-2 text-center">
            ⚙️ Settings
          </RouterLink>
          <RouterLink to="/profile" class="block w-full btn-ghost border rounded-xl py-2 text-center">
            👤 Profile
          </RouterLink>
        </div>
        <div class="mt-4 pt-4 border-t border-white/10">
          <div class="text-sm text-white/60 mb-1">Monthly Usage</div>
          <div class="flex items-center justify-between mb-2">
            <span class="text-2xl font-bold">{{ usage.current }}</span>
            <span class="text-sm text-white/60">/ {{ usage.limit }}</span>
          </div>
          <div class="w-full bg-white/10 rounded-full h-2">
            <div
                class="bg-gradient-to-r from-brand-violet to-brand-cyan rounded-full h-2 transition-all"
                :style="`width: ${usage.percentage}%`"
            ></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {ref, onMounted, onUnmounted} from 'vue'
import {RouterLink} from 'vue-router'
import StatWidget from '@/components/StatWidget.vue'
import ChartCard from '@/components/ChartCard.vue'
import {api} from '@/services/api'

// State
const loading = ref(false)
const error = ref(null)
const chartsReady = ref(false)

// Data
const stats = ref({
  events: 0,
  creatives: 0,
  quality: 0,
  ctr: 0
})

const chartData = ref({
  labels: [],
  ctrData: [],
  relData: [],
  clrData: []
})

const events = ref([])
const usage = ref({
  current: 0,
  limit: 100,
  percentage: 0
})

// Prevent infinite loops
let dataLoadAttempts = 0
const MAX_ATTEMPTS = 3

async function loadData() {
  // Prevent infinite retry loops
  if (dataLoadAttempts >= MAX_ATTEMPTS) {
    console.log('Max load attempts reached, using demo data')
    loadDemoData()
    return
  }

  dataLoadAttempts++
  loading.value = true
  error.value = null
  chartsReady.value = false

  try {
    // Try to load real data from backend
    const [dashboardRes, usageRes] = await Promise.allSettled([
      api.get('/api/v1/company/dashboard').catch(err => {
        console.log('Dashboard API not available, using demo data')
        return null
      }),
      api.get('/api/v1/company/usage').catch(err => {
        console.log('Usage API not available, using demo data')
        return null
      })
    ])

    // Process dashboard data
    if (dashboardRes.status === 'fulfilled' && dashboardRes.value?.data) {
      const data = dashboardRes.value.data
      stats.value = {
        events: data.total_ads_generated || 0,
        creatives: data.ads_generated_this_month || 0,
        quality: data.average_evaluation_score || 8.9,
        ctr: 4.7 // Demo value as this isn't in the backend yet
      }

      // Process recent activity
      if (data.recent_ads && Array.isArray(data.recent_ads)) {
        events.value = data.recent_ads.map((ad, index) => ({
          id: ad.id || index,
          icon: '⚡',
          title: ad.headline || ad.event_name || 'Ad Generated',
          desc: ad.status || 'Ready',
          time: formatTime(ad.created_at)
        }))
      }
    } else {
      // Use demo data if API fails
      loadDemoData()
    }

    // Process usage data
    if (usageRes.status === 'fulfilled' && usageRes.value?.data) {
      const data = usageRes.value.data
      usage.value = {
        current: data.total_generated || 0,
        limit: data.remaining_monthly_limit + data.total_generated || 100,
        percentage: Math.min(((data.total_generated || 0) / 100) * 100, 100)
      }
    } else {
      // Demo usage data
      usage.value = {
        current: 48,
        limit: 100,
        percentage: 48
      }
    }

    // Generate chart data (demo for now)
    generateChartData()

    // Small delay to ensure smooth rendering
    setTimeout(() => {
      chartsReady.value = true
    }, 100)

  } catch (err) {
    console.error('Dashboard load error:', err)
    error.value = 'Failed to load dashboard data. Using demo mode.'
    loadDemoData()
  } finally {
    loading.value = false
  }
}

function loadDemoData() {
  // Safe demo data that won't cause issues
  stats.value = {
    events: 120,
    creatives: 48,
    quality: 8.9,
    ctr: 4.7
  }

  events.value = [
    {
      id: 1,
      icon: '🎯',
      title: 'Black Friday Campaign',
      desc: 'Generated successfully',
      time: '4m ago'
    },
    {
      id: 2,
      icon: '📊',
      title: 'Performance Report',
      desc: 'CTR increased by 12%',
      time: '1h ago'
    },
    {
      id: 3,
      icon: '🚀',
      title: 'New Ad Created',
      desc: 'Holiday season theme',
      time: '3h ago'
    }
  ]

  usage.value = {
    current: 48,
    limit: 100,
    percentage: 48
  }

  generateChartData()

  // Ensure charts render after data is ready
  setTimeout(() => {
    chartsReady.value = true
  }, 100)
}

function generateChartData() {
  // Generate safe chart data
  const days = 14
  const labels = Array.from({length: days}, (_, i) => {
    const d = new Date()
    d.setDate(d.getDate() - (days - i - 1))
    return d.toLocaleDateString('en', {month: 'short', day: 'numeric'})
  })

  chartData.value = {
    labels,
    ctrData: labels.map((_, i) => (3.6 + Math.sin(i / 2) * 0.6 + Math.random() * 0.3).toFixed(1)),
    relData: labels.map(() => (8.5 + Math.random() * 0.6).toFixed(1)),
    clrData: labels.map(() => (8.1 + Math.random() * 0.6).toFixed(1))
  }
}

function formatTime(dateStr) {
  if (!dateStr) return 'Just now'

  try {
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now - date
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)

    if (minutes < 60) return `${minutes}m ago`
    if (hours < 24) return `${hours}h ago`
    return `${days}d ago`
  } catch {
    return 'Recently'
  }
}

// Lifecycle
onMounted(() => {
  // Reset attempts counter
  dataLoadAttempts = 0
  loadData()
})

// Cleanup on unmount to prevent memory leaks
onUnmounted(() => {
  chartsReady.value = false
})
</script>

<style scoped>
/* Smooth animations */
.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: .5;
  }
}

/* Prevent layout shift */
.min-h-chart {
  min-height: 200px;
}
</style>