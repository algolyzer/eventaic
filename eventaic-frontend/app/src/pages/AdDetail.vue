<template>
  <div class="max-w-5xl mx-auto space-y-6">
    <!-- Back Button -->
    <div>
      <button @click="$router.back()" class="btn-ghost border rounded-xl px-4 py-2 mb-2">
        ← Back
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="card p-8 animate-pulse">
      <div class="h-8 bg-white/10 rounded w-1/2 mb-4"></div>
      <div class="h-4 bg-white/10 rounded w-full mb-2"></div>
      <div class="h-4 bg-white/10 rounded w-3/4"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="card p-5 border-red-500/20 bg-red-500/5">
      <p class="text-red-400">{{ error }}</p>
      <button @click="loadAd" class="btn mt-3">Retry</button>
    </div>

    <!-- Success Message -->
    <div v-if="successMessage" class="card p-5 border-green-500/20 bg-green-500/5">
      <p class="text-green-400">✅ {{ successMessage }}</p>
    </div>

    <!-- Ad Content -->
    <div v-else-if="ad" class="space-y-6">
      <!-- Header -->
      <div class="card p-6">
        <div class="flex justify-between items-start mb-4">
          <div class="flex-1">
            <div class="flex items-center gap-3 mb-2">
              <h1 class="text-2xl font-bold">{{ ad.event_name }}</h1>
              <span class="badge" :class="getStatusClass(ad.status)">
                {{ formatStatus(ad.status) }}
              </span>
            </div>
            <p class="text-white/60">
              Created {{ formatDate(ad.created_at) }}
              <span v-if="ad.company_name"> • {{ ad.company_name }}</span>
            </p>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex flex-wrap gap-2">
          <button @click="evaluateAd" class="btn" :disabled="evaluating">
            {{ evaluating ? 'Evaluating...' : '🧪 Evaluate' }}
          </button>
          <button @click="regenerateAd" class="btn-ghost border rounded-xl px-4 py-2" :disabled="regenerating">
            {{ regenerating ? 'Regenerating...' : '🔄 Regenerate' }}
          </button>
          <button @click="regenerateImage" class="btn-ghost border rounded-xl px-4 py-2" :disabled="regeneratingImage">
            {{ regeneratingImage ? 'Regenerating Image...' : '🖼️ New Image' }}
          </button>
          <button @click="deleteAd" class="btn-ghost border border-red-500/30 rounded-xl px-4 py-2 hover:bg-red-500/10">
            🗑️ Delete
          </button>
        </div>
      </div>

      <!-- Ad Image (if exists) -->
      <div v-if="ad.content?.image_url" class="card p-6">
        <h2 class="text-xl font-bold mb-4">Ad Image</h2>
        <div class="rounded-xl overflow-hidden border border-white/10">
          <img
              :src="getImageUrl(ad.content.image_url)"
              :alt="ad.content?.headline || 'Ad image'"
              class="w-full h-auto"
              @error="handleImageError"
          />
        </div>
        <p class="text-sm text-white/50 mt-2">
          {{ ad.content?.image_prompt || 'No image prompt available' }}
        </p>
      </div>

      <!-- Evaluation Score -->
      <div v-if="ad.evaluation_score" class="card p-6">
        <h2 class="text-xl font-bold mb-4">Quality Evaluation</h2>
        <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div class="text-center">
            <div class="text-3xl font-bold" :class="getScoreClass(ad.evaluation_details?.relevance_score || 0)">
              {{ (ad.evaluation_details?.relevance_score || 0).toFixed(1) }}
            </div>
            <div class="text-sm text-white/60">Relevance</div>
          </div>
          <div class="text-center">
            <div class="text-3xl font-bold" :class="getScoreClass(ad.evaluation_details?.clarity_score || 0)">
              {{ (ad.evaluation_details?.clarity_score || 0).toFixed(1) }}
            </div>
            <div class="text-sm text-white/60">Clarity</div>
          </div>
          <div class="text-center">
            <div class="text-3xl font-bold" :class="getScoreClass(ad.evaluation_details?.persuasiveness_score || 0)">
              {{ (ad.evaluation_details?.persuasiveness_score || 0).toFixed(1) }}
            </div>
            <div class="text-sm text-white/60">Persuasion</div>
          </div>
          <div class="text-center">
            <div class="text-3xl font-bold" :class="getScoreClass(ad.evaluation_details?.brand_safety_score || 0)">
              {{ (ad.evaluation_details?.brand_safety_score || 0).toFixed(1) }}
            </div>
            <div class="text-sm text-white/60">Safety</div>
          </div>
          <div class="text-center">
            <div class="text-3xl font-bold" :class="getScoreClass(ad.evaluation_score)">
              {{ ad.evaluation_score.toFixed(1) }}
            </div>
            <div class="text-sm text-white/60">Overall</div>
          </div>
        </div>

        <div v-if="ad.evaluation_details?.feedback" class="mt-4 p-4 rounded-xl bg-white/5">
          <div class="text-sm font-medium mb-1">Feedback</div>
          <p class="text-white/70 text-sm">{{ ad.evaluation_details.feedback }}</p>
        </div>
      </div>

      <!-- Ad Content -->
      <div class="card p-6">
        <h2 class="text-xl font-bold mb-4">Ad Content</h2>

        <div class="space-y-4">
          <div>
            <div class="text-sm text-white/60 mb-1">Headline</div>
            <div class="text-xl font-bold">{{ ad.content?.headline }}</div>
          </div>

          <div>
            <div class="text-sm text-white/60 mb-1">Description</div>
            <div class="text-white/90">{{ ad.content?.description }}</div>
          </div>

          <div>
            <div class="text-sm text-white/60 mb-1">Slogan</div>
            <div class="font-semibold text-lg">{{ ad.content?.slogan }}</div>
          </div>

          <div>
            <div class="text-sm text-white/60 mb-1">Call to Action</div>
            <button class="btn">
              {{ ad.content?.cta_text }}
            </button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div class="text-sm text-white/60 mb-2">Keywords</div>
              <div class="flex flex-wrap gap-2">
                <span v-for="kw in ad.content?.keywords" :key="kw" class="badge">
                  {{ kw }}
                </span>
              </div>
            </div>
            <div>
              <div class="text-sm text-white/60 mb-2">Hashtags</div>
              <div class="flex flex-wrap gap-2">
                <span v-for="tag in ad.content?.hashtags" :key="tag" class="badge">
                  {{ tag }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Platform Details -->
      <div class="card p-6">
        <h2 class="text-xl font-bold mb-4">Platform Recommendations</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div v-for="platform in ad.platforms" :key="platform"
               class="p-4 rounded-xl border border-white/10 bg-white/5">
            <div class="font-bold mb-1">{{ formatPlatform(platform) }}</div>
            <div v-if="ad.platform_details && ad.platform_details[platform]" class="text-sm text-white/60">
              Priority: {{ ad.platform_details[platform].priority || 'N/A' }}<br>
              Budget: {{ ad.platform_details[platform].budget_percentage || 0 }}%
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {ref, onMounted} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {api} from '@/services/api'

const route = useRoute()
const router = useRouter()

const ad = ref(null)
const loading = ref(true)
const error = ref('')
const successMessage = ref('')
const evaluating = ref(false)
const regenerating = ref(false)
const regeneratingImage = ref(false)

function formatPlatform(platform) {
  const platforms = {
    'google_ads': 'Google Ads',
    'meta_ads': 'Meta Ads',
    'linkedin': 'LinkedIn',
    'twitter': 'Twitter/X',
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
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return 'Recently'
  }
}

function getImageUrl(url) {
  // If URL is already absolute, return as is
  if (url && (url.startsWith('http://') || url.startsWith('https://'))) {
    return url
  }
  // Otherwise, prepend the API base URL
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
  return `${baseUrl}${url}`
}

function handleImageError(event) {
  console.error('Failed to load image:', event.target.src)
  event.target.style.display = 'none'
}

async function loadAd() {
  loading.value = true
  error.value = ''
  successMessage.value = ''

  try {
    const response = await api.get(`/api/v1/ads/${route.params.id}`)
    ad.value = response.data
    console.log('✅ Ad loaded:', ad.value)
  } catch (err) {
    console.error('❌ Load ad error:', err)
    error.value = err.response?.data?.detail || 'Failed to load ad'
  } finally {
    loading.value = false
  }
}

async function evaluateAd() {
  evaluating.value = true
  error.value = ''
  successMessage.value = ''

  try {
    console.log('🧪 Evaluating ad...')
    await api.post('/api/v1/ads/evaluate', {
      ad_id: route.params.id
    })

    successMessage.value = 'Ad evaluated successfully!'

    // Reload ad to show evaluation results
    await loadAd()
  } catch (err) {
    console.error('❌ Evaluation error:', err)
    error.value = err.response?.data?.detail || 'Failed to evaluate ad'
  } finally {
    evaluating.value = false
  }
}

async function regenerateAd() {
  if (!confirm('This will create a new version of this ad. Continue?')) return

  regenerating.value = true
  error.value = ''
  successMessage.value = ''

  try {
    console.log('🔄 Regenerating ad...')
    const response = await api.post('/api/v1/ads/regenerate', {
      ad_id: route.params.id,
      regenerate_image: false
    })

    successMessage.value = 'Ad regenerated successfully!'

    // Navigate to the new ad
    setTimeout(() => {
      router.push(`/ads/${response.data.id}`)
    }, 1000)
  } catch (err) {
    console.error('❌ Regeneration error:', err)
    error.value = err.response?.data?.detail || 'Failed to regenerate ad'
  } finally {
    regenerating.value = false
  }
}

async function regenerateImage() {
  if (!confirm('This will generate a new image for this ad. Continue?')) return

  regeneratingImage.value = true
  error.value = ''
  successMessage.value = ''

  try {
    console.log('🖼️ Regenerating image...')

    const response = await api.post('/api/v1/ads/regenerate', {
      ad_id: route.params.id,
      regenerate_image: true
    })

    console.log('✅ Image regeneration response:', response.data)

    successMessage.value = 'Image regenerated successfully!'

    // Reload ad to show new image
    await loadAd()

    // Clear success message after 3 seconds
    setTimeout(() => {
      successMessage.value = ''
    }, 3000)

  } catch (err) {
    console.error('❌ Image regeneration error:', err)
    console.error('Error details:', {
      status: err.response?.status,
      data: err.response?.data,
      message: err.message
    })
    error.value = err.response?.data?.detail || err.message || 'Failed to regenerate image'
  } finally {
    regeneratingImage.value = false
  }
}

async function deleteAd() {
  if (!confirm('Are you sure you want to delete this ad? This action cannot be undone.')) return

  try {
    console.log('🗑️ Deleting ad...')
    await api.delete(`/api/v1/ads/${route.params.id}`)

    successMessage.value = 'Ad deleted successfully!'

    // Navigate back to ads list after brief delay
    setTimeout(() => {
      router.push('/ads')
    }, 1000)
  } catch (err) {
    console.error('❌ Delete error:', err)
    error.value = err.response?.data?.detail || 'Failed to delete ad'
  }
}

onMounted(() => {
  loadAd()
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

img {
  max-width: 100%;
  height: auto;
  display: block;
}
</style>