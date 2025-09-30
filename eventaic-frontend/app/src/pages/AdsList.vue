<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl md:text-3xl font-extrabold tracking-tight">My Ads</h1>
        <p class="text-white/60">View and manage your generated ads</p>
      </div>
      <RouterLink to="/ads/generate" class="btn">
        ✨ Generate New Ad
      </RouterLink>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <div v-for="i in 6" :key="i" class="card p-5 animate-pulse">
        <div class="h-6 bg-white/10 rounded w-3/4 mb-3"></div>
        <div class="h-4 bg-white/10 rounded w-full mb-2"></div>
        <div class="h-4 bg-white/10 rounded w-2/3"></div>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="card p-5 border-red-500/20 bg-red-500/5">
      <p class="text-red-400">{{ error }}</p>
      <button @click="loadAds" class="btn mt-3">Retry</button>
    </div>

    <!-- Empty State -->
    <div v-else-if="ads.length === 0" class="card p-12 text-center">
      <div class="text-6xl mb-4">📢</div>
      <h3 class="text-xl font-bold mb-2">No ads yet</h3>
      <p class="text-white/60 mb-4">Create your first AI-powered ad campaign</p>
      <RouterLink to="/ads/generate" class="btn">
        Generate Your First Ad
      </RouterLink>
    </div>

    <!-- Ads Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <div v-for="ad in ads" :key="ad.id" class="card p-5 hover:bg-white/10 transition cursor-pointer"
           @click="viewAd(ad.id)">
        <!-- Header -->
        <div class="flex justify-between items-start mb-3">
          <div class="flex-1 min-w-0">
            <h3 class="font-bold text-lg truncate">{{ ad.event_name }}</h3>
            <p class="text-sm text-white/60 truncate">{{ ad.content?.headline }}</p>
          </div>
          <span class="badge ml-2 flex-shrink-0" :class="getStatusClass(ad.status)">
            {{ formatStatus(ad.status) }}
          </span>
        </div>

        <!-- Description -->
        <p class="text-white/70 text-sm line-clamp-2 mb-3">
          {{ ad.content?.description }}
        </p>

        <!-- Platforms -->
        <div class="flex flex-wrap gap-1 mb-3">
          <span v-for="platform in ad.platforms?.slice(0, 3)" :key="platform"
                class="text-xs px-2 py-1 rounded-full bg-white/5 border border-white/10">
            {{ formatPlatform(platform) }}
          </span>
          <span v-if="ad.platforms?.length > 3"
                class="text-xs px-2 py-1 rounded-full bg-white/5 border border-white/10">
            +{{ ad.platforms.length - 3 }}
          </span>
        </div>

        <!-- Footer -->
        <div class="flex justify-between items-center pt-3 border-t border-white/10 text-sm">
          <div class="text-white/50">
            {{ formatDate(ad.created_at) }}
          </div>
          <div v-if="ad.evaluation_score" class="flex items-center gap-2">
            <span class="text-white/60">Score:</span>
            <span class="font-bold" :class="getScoreClass(ad.evaluation_score)">
              {{ ad.evaluation_score.toFixed(1) }}/10
            </span>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex gap-2 mt-3">
          <button @click.stop="evaluateAdQuick(ad.id)"
                  class="flex-1 btn-ghost border rounded-xl py-2 text-sm"
                  :disabled="evaluatingId === ad.id">
            {{ evaluatingId === ad.id ? 'Evaluating...' : '🧪 Evaluate' }}
          </button>
          <button @click.stop="deleteAd(ad.id)"
                  class="btn-ghost border border-red-500/30 rounded-xl px-3 py-2 text-sm hover:bg-red-500/10"
                  :disabled="deletingId === ad.id">
            🗑️
          </button>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex justify-center gap-2">
      <button
          @click="changePage(page - 1)"
          :disabled="page === 1"
          class="btn-ghost border rounded-xl px-4 py-2"
      >
        Previous
      </button>
      <span class="px-4 py-2 text-white/60">
        Page {{ page }} of {{ totalPages }}
      </span>
      <button
          @click="changePage(page + 1)"
          :disabled="page === totalPages"
          class="btn-ghost border rounded-xl px-4 py-2"
      >
        Next
      </button>
    </div>
  </div>
</template>

<script setup>
import {ref, onMounted} from 'vue'
import {RouterLink, useRouter} from 'vue-router'
import {api} from '@/services/api'

const router = useRouter()

const ads = ref([])
const loading = ref(false)
const error = ref('')
const page = ref(1)
const perPage = ref(12)
const totalPages = ref(1)
const evaluatingId = ref(null)
const deletingId = ref(null)

function formatPlatform(platform) {
  const platforms = {
    'google_ads': 'Google',
    'meta_ads': 'Meta',
    'linkedin': 'LinkedIn',
    'twitter': 'X',
    'instagram': 'Instagram',
    'tiktok': 'TikTok'
  }
  return platforms[platform] || platform
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

function getScoreClass(score) {
  if (score >= 8) return 'text-green-400'
  if (score >= 6) return 'text-yellow-400'
  return 'text-red-400'
}

function formatDate(dateStr) {
  if (!dateStr) return 'Recently'

  try {
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now - date
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)

    if (minutes < 60) return `${minutes}m ago`
    if (hours < 24) return `${hours}h ago`
    if (days < 30) return `${days}d ago`
    return date.toLocaleDateString()
  } catch {
    return 'Recently'
  }
}

async function loadAds() {
  loading.value = true
  error.value = ''

  try {
    const response = await api.get('/api/v1/ads/', {
      params: {
        page: page.value,
        per_page: perPage.value
      }
    })

    ads.value = response.data.ads || []
    totalPages.value = Math.ceil((response.data.total || 0) / perPage.value)

  } catch (err) {
    console.error('Load ads error:', err)
    error.value = err.response?.data?.detail || 'Failed to load ads'
  } finally {
    loading.value = false
  }
}

async function evaluateAdQuick(adId) {
  evaluatingId.value = adId

  try {
    await api.post('/api/v1/ads/evaluate', {ad_id: adId})
    await loadAds() // Reload to show updated score
  } catch (err) {
    console.error('Evaluate error:', err)
  } finally {
    evaluatingId.value = null
  }
}

async function deleteAd(adId) {
  if (!confirm('Are you sure you want to delete this ad?')) return

  deletingId.value = adId

  try {
    await api.delete(`/api/v1/ads/${adId}`)
    ads.value = ads.value.filter(ad => ad.id !== adId)
  } catch (err) {
    console.error('Delete error:', err)
    alert('Failed to delete ad')
  } finally {
    deletingId.value = null
  }
}

function viewAd(adId) {
  router.push(`/ads/${adId}`)
}

function changePage(newPage) {
  if (newPage < 1 || newPage > totalPages.value) return
  page.value = newPage
  loadAds()
}

onMounted(() => {
  loadAds()
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

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