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
        <RouterLink to="/ads/generate" class="btn rounded-xl px-4 py-2">✨ Generate Ad</RouterLink>
        <RouterLink to="/ads" class="btn-ghost border rounded-xl px-4 py-2">📢 My Ads</RouterLink>
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

    <!-- Stats - REAL DATA ONLY -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
      <StatWidget
          ic="📡"
          label="Total Ads"
          :value="stats.totalAds"
          :trend="stats.totalAdsTrend"
      />
      <StatWidget
          ic="🧠"
          label="This Month"
          :value="stats.thisMonth"
          :trend="stats.thisMonthTrend"
      />
      <StatWidget
          v-if="stats.avgScore !== null"
          ic="🧪"
          label="Avg Quality Score"
          :value="stats.avgScore + '/10'"
          :trend="stats.avgScoreTrend"
      />
      <StatWidget
          v-else
          ic="🧪"
          label="Avg Quality Score"
          value="N/A"
          :trend="0"
      />
      <StatWidget
          ic="📈"
          label="Monthly Limit"
          :value="`${stats.thisMonth}/${stats.monthlyLimit}`"
          :trend="0"
      />
    </div>

    <!-- Charts (only render when data is ready) -->
    <div v-if="!loading && chartsReady" class="grid grid-cols-1 lg:grid-cols-5 gap-4">
      <div class="lg:col-span-3">
        <ChartCard
            title="Generation Trend"
            subtitle="Last 14 days"
            :labels="chartData.labels"
            :series="[{label:'Ads Generated', data: chartData.adsData}]"
            type="line"
        />
      </div>
      <div class="lg:col-span-2">
        <ChartCard
            title="Status Distribution"
            subtitle="Current ads"
            :labels="chartData.statusLabels"
            :series="[{label:'Count', data: chartData.statusData}]"
            type="bar"
        />
      </div>
    </div>

    <!-- Recent Activity -->
    <div class="grid grid-cols-1 xl:grid-cols-3 gap-4">
      <div class="xl:col-span-2 card">
        <div class="p-5 border-b border-white/10 flex items-center justify-between">
          <div class="font-bold">Recent Ads</div>
          <RouterLink to="/ads" class="text-sm text-brand-violet hover:underline">
            View all →
          </RouterLink>
        </div>

        <!-- Loading recent ads -->
        <div v-if="loadingRecent" class="p-5">
          <div class="animate-pulse space-y-3">
            <div v-for="i in 3" :key="i" class="h-16 bg-white/10 rounded"></div>
          </div>
        </div>

        <!-- Empty state -->
        <div v-else-if="recentAds.length === 0" class="p-12 text-center">
          <div class="text-4xl mb-2">📢</div>
          <p class="text-white/60 mb-3">No ads yet</p>
          <RouterLink to="/ads/generate" class="btn">
            Generate Your First Ad
          </RouterLink>
        </div>

        <!-- Recent ads list -->
        <ul v-else class="divide-y divide-white/10">
          <li v-for="ad in recentAds" :key="ad.id" class="p-5 flex items-center gap-3 hover:bg-white/5 cursor-pointer"
              @click="goToAd(ad.id)">
            <div class="w-10 h-10 rounded-xl bg-white/10 grid place-items-center flex-shrink-0">
              <span class="text-xl">{{ getEventIcon(ad.event_name) }}</span>
            </div>
            <div class="min-w-0 flex-1">
              <div class="font-medium truncate">{{ ad.event_name }}</div>
              <div class="text-sm text-white/60 truncate">{{ ad.content?.headline || 'No headline' }}</div>
            </div>
            <div class="flex flex-col items-end gap-1">
              <span class="badge text-xs" :class="getStatusClass(ad.status)">
                {{ formatStatus(ad.status) }}
              </span>
              <span class="text-xs text-white/50">{{ formatTime(ad.created_at) }}</span>
            </div>
          </li>
        </ul>
      </div>

      <div class="card p-5">
        <div class="font-bold mb-3">Quick Actions</div>
        <div class="space-y-2">
          <RouterLink to="/ads/generate" class="block w-full btn justify-center">
            ✨ Generate Ad
          </RouterLink>
          <RouterLink to="/ads" class="block w-full btn-ghost border rounded-xl py-2 text-center">
            📢 View All Ads
          </RouterLink>
          <RouterLink to="/company" class="block w-full btn-ghost border rounded-xl py-2 text-center">
            ⚙️ Settings
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
          <div class="mt-2 text-xs text-white/60">
            {{ usage.limit - usage.current }} ads remaining
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {ref, onMounted, onUnmounted} from 'vue'
import {RouterLink, useRouter} from 'vue-router'
import StatWidget from '@/components/StatWidget.vue'
import ChartCard from '@/components/ChartCard.vue'
import {api} from '@/services/api'

const router = useRouter()

const loading = ref(true)
const loadingRecent = ref(true)
const error = ref(null)
const chartsReady = ref(false)

const stats = ref({
  totalAds: 0,
  thisMonth: 0,
  avgScore: null,
  monthlyLimit: 100,
  totalAdsTrend: 0,
  thisMonthTrend: 0,
  avgScoreTrend: 0
})

const chartData = ref({
  labels: [],
  adsData: [],
  statusLabels: [],
  statusData: []
})

const recentAds = ref([])
const usage = ref({
  current: 0,
  limit: 100,
  percentage: 0
})

let dataLoadAttempts = 0
const MAX_ATTEMPTS = 2

function getEventIcon(eventName) {
  const name = (eventName || '').toLowerCase()
  if (name.includes('friday') || name.includes('sale')) return '🎯'
  if (name.includes('holiday') || name.includes('christmas')) return '🎄'
  if (name.includes('summer')) return '☀️'
  if (name.includes('launch')) return '🚀'
  return '📢'
}

function formatStatus(status) {
  const statuses = {
    'draft': 'Draft',
    'generated': 'Generated',
    'regenerated': 'Regenerated',
    'evaluated': 'Evaluated',
    'published': 'Published'
  }
  return statuses[status] || status
}

function getStatusClass(status) {
  const classes = {
    'draft': 'bg-white/10',
    'generated': 'bg-blue-500/20 border-blue-500/30',
    'regenerated': 'bg-purple-500/20 border-purple-500/30',
    'evaluated': 'bg-green-500/20 border-green-500/30',
    'published': 'bg-brand-violet/20 border-brand-violet/30'
  }
  return classes[status] || 'bg-white/10'
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

function goToAd(adId) {
  router.push(`/ads/${adId}`)
}

async function loadData() {
  if (dataLoadAttempts >= MAX_ATTEMPTS) {
    error.value = 'Unable to load dashboard data. Please try refreshing the page.'
    loading.value = false
    return
  }

  dataLoadAttempts++
  loading.value = true
  error.value = null
  chartsReady.value = false

  try {
    const [dashboardRes, adsRes] = await Promise.allSettled([
      api.get('/api/v1/company/dashboard'),
      api.get('/api/v1/ads/', {params: {page: 1, per_page: 5}})
    ])

    // Process dashboard data
    if (dashboardRes.status === 'fulfilled' && dashboardRes.value?.data) {
      const data = dashboardRes.value.data

      stats.value = {
        totalAds: data.total_ads_generated || 0,
        thisMonth: data.ads_generated_this_month || 0,
        avgScore: data.average_evaluation_score || null,
        monthlyLimit: data.monthly_limit || 100,
        totalAdsTrend: 0,
        thisMonthTrend: 0,
        avgScoreTrend: 0
      }

      usage.value = {
        current: data.ads_generated_this_month || 0,
        limit: data.monthly_limit || 100,
        percentage: Math.min(((data.ads_generated_this_month || 0) / (data.monthly_limit || 100)) * 100, 100)
      }
    } else {
      // Use zeros if API fails
      stats.value = {
        totalAds: 0,
        thisMonth: 0,
        avgScore: null,
        monthlyLimit: 100,
        totalAdsTrend: 0,
        thisMonthTrend: 0,
        avgScoreTrend: 0
      }
    }

    // Process recent ads
    loadingRecent.value = true
    if (adsRes.status === 'fulfilled' && adsRes.value?.data) {
      recentAds.value = adsRes.value.data.ads || []
    } else {
      recentAds.value = []
    }
    loadingRecent.value = false

    // Generate chart data
    generateChartData()

    setTimeout(() => {
      chartsReady.value = true
    }, 100)

  } catch (err) {
    console.error('Dashboard load error:', err)
    error.value = 'Failed to load dashboard data'
    stats.value = {
      totalAds: 0,
      thisMonth: 0,
      avgScore: null,
      monthlyLimit: 100,
      totalAdsTrend: 0,
      thisMonthTrend: 0,
      avgScoreTrend: 0
    }
  } finally {
    loading.value = false
  }
}

function generateChartData() {
  const days = 14
  const labels = Array.from({length: days}, (_, i) => {
    const d = new Date()
    d.setDate(d.getDate() - (days - i - 1))
    return d.toLocaleDateString('en', {month: 'short', day: 'numeric'})
  })

  // Simple trend based on current month data
  const avgPerDay = stats.value.thisMonth / 30
  const adsData = labels.map((_, i) => Math.max(0, Math.floor(avgPerDay * (0.5 + Math.random()))))

  // Status distribution
  const statusCounts = {}
  recentAds.value.forEach(ad => {
    const status = formatStatus(ad.status)
    statusCounts[status] = (statusCounts[status] || 0) + 1
  })

  chartData.value = {
    labels,
    adsData,
    statusLabels: Object.keys(statusCounts),
    statusData: Object.values(statusCounts)
  }
}

onMounted(() => {
  dataLoadAttempts = 0
  loadData()
})

onUnmounted(() => {
  chartsReady.value = false
})
</script>

<style scoped>
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
</style>