<template>
  <div class="max-w-4xl mx-auto space-y-6">
    <div>
      <div class="badge">✨ AI-Powered</div>
      <h1 class="text-2xl md:text-3xl font-extrabold tracking-tight mt-1">Generate Ad</h1>
      <p class="text-white/60">Create event-responsive ad campaigns instantly</p>
    </div>

    <div class="card p-6">
      <form @submit.prevent="generateAd" class="space-y-4">
        <!-- Event Name -->
        <div>
          <label class="block text-sm font-medium mb-2">Event Name *</label>
          <input
              v-model="form.event_name"
              type="text"
              class="input"
              placeholder="Black Friday, Summer Sale, Product Launch..."
              required
          />
        </div>

        <!-- Product Name -->
        <div>
          <label class="block text-sm font-medium mb-2">Product Name (Optional)</label>
          <input
              v-model="form.product_name"
              type="text"
              class="input"
              placeholder="iPhone 15, Tesla Model 3..."
          />
        </div>

        <!-- Product Categories -->
        <div>
          <label class="block text-sm font-medium mb-2">Product Categories * (comma-separated)</label>
          <input
              v-model="categoriesInput"
              type="text"
              class="input"
              placeholder="Electronics, Smartphones, Accessories"
              required
          />
          <p class="text-xs text-white/50 mt-1">Separate categories with commas</p>
        </div>

        <!-- Location -->
        <div>
          <label class="block text-sm font-medium mb-2">Location (Optional)</label>
          <input
              v-model="form.location"
              type="text"
              class="input"
              placeholder="New York, Los Angeles, Global..."
          />
        </div>

        <!-- Company Name -->
        <div>
          <label class="block text-sm font-medium mb-2">Company Name (Optional)</label>
          <input
              v-model="form.company_name"
              type="text"
              class="input"
              placeholder="Your company name"
          />
        </div>

        <!-- Submit Button -->
        <div class="flex gap-3">
          <button
              type="submit"
              class="btn flex-1 justify-center"
              :disabled="loading"
          >
            <span v-if="loading">⏳ Generating (this may take up to 60 seconds)...</span>
            <span v-else>✨ Generate Ad</span>
          </button>
          <button
              type="button"
              class="btn-ghost border rounded-xl px-6"
              @click="resetForm"
              :disabled="loading"
          >
            Reset
          </button>
        </div>
      </form>

      <!-- Loading Indicator -->
      <div v-if="loading" class="mt-4 p-4 rounded-xl bg-white/5 border border-white/10">
        <div class="flex items-center gap-3">
          <div class="animate-spin text-2xl">⚙️</div>
          <div>
            <div class="font-medium">Generating your ad...</div>
            <div class="text-sm text-white/60">Creating content and image. This typically takes 20-40 seconds.</div>
          </div>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="error" class="mt-4 p-4 rounded-xl bg-red-500/20 border border-red-500/30 text-red-400">
        {{ error }}
      </div>

      <!-- Success Message -->
      <div v-if="success" class="mt-4 p-4 rounded-xl bg-green-500/20 border border-green-500/30 text-green-400">
        {{ success }}
        <RouterLink :to="`/ads/${generatedAdId}`" class="block mt-2 underline">
          View generated ad →
        </RouterLink>
      </div>
    </div>

    <!-- Generated Ad Preview -->
    <div v-if="generatedAd" class="card p-6">
      <h2 class="text-xl font-bold mb-4">Generated Ad Preview</h2>

      <div class="space-y-4">
        <!-- Image Preview -->
        <div v-if="generatedAd.content?.image_url" class="rounded-xl overflow-hidden border border-white/10">
          <img
              :src="getImageUrl(generatedAd.content.image_url)"
              :alt="generatedAd.content?.headline || 'Generated ad image'"
              class="w-full h-auto"
              @error="handleImageError"
          />
        </div>

        <!-- Headline -->
        <div>
          <div class="text-sm text-white/60 mb-1">Headline</div>
          <div class="font-bold text-lg">{{ generatedAd.content?.headline }}</div>
        </div>

        <!-- Description -->
        <div>
          <div class="text-sm text-white/60 mb-1">Description</div>
          <div class="text-white/80">{{ generatedAd.content?.description }}</div>
        </div>

        <!-- Slogan -->
        <div>
          <div class="text-sm text-white/60 mb-1">Slogan</div>
          <div class="font-semibold">{{ generatedAd.content?.slogan }}</div>
        </div>

        <!-- CTA -->
        <div>
          <div class="text-sm text-white/60 mb-1">Call to Action</div>
          <button class="btn-ghost border rounded-xl px-4 py-2">
            {{ generatedAd.content?.cta_text }}
          </button>
        </div>

        <!-- Keywords & Hashtags -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div class="text-sm text-white/60 mb-2">Keywords</div>
            <div class="flex flex-wrap gap-2">
              <span v-for="kw in generatedAd.content?.keywords" :key="kw" class="badge">
                {{ kw }}
              </span>
            </div>
          </div>
          <div>
            <div class="text-sm text-white/60 mb-2">Hashtags</div>
            <div class="flex flex-wrap gap-2">
              <span v-for="tag in generatedAd.content?.hashtags" :key="tag" class="badge">
                {{ tag }}
              </span>
            </div>
          </div>
        </div>

        <!-- Platforms -->
        <div>
          <div class="text-sm text-white/60 mb-2">Recommended Platforms</div>
          <div class="flex flex-wrap gap-2">
            <span v-for="platform in generatedAd.platforms" :key="platform" class="badge">
              {{ formatPlatform(platform) }}
            </span>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex gap-3 pt-4 border-t border-white/10">
          <button @click="evaluateAd" class="btn" :disabled="evaluating">
            {{ evaluating ? 'Evaluating...' : '🧪 Evaluate Quality' }}
          </button>
          <button @click="regenerateAd" class="btn-ghost border rounded-xl px-4 py-2" :disabled="regenerating">
            {{ regenerating ? 'Regenerating...' : '🔄 Regenerate' }}
          </button>
          <RouterLink to="/ads" class="btn-ghost border rounded-xl px-4 py-2">
            View All Ads
          </RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {ref} from 'vue'
import {RouterLink, useRouter} from 'vue-router'
import {api, apiLongRunning} from '@/services/api'

const router = useRouter()

const form = ref({
  event_name: '',
  product_name: '',
  product_categories: [],
  location: '',
  company_name: ''
})

const categoriesInput = ref('')
const loading = ref(false)
const evaluating = ref(false)
const regenerating = ref(false)
const error = ref('')
const success = ref('')
const generatedAd = ref(null)
const generatedAdId = ref(null)

function resetForm() {
  form.value = {
    event_name: '',
    product_name: '',
    product_categories: [],
    location: '',
    company_name: ''
  }
  categoriesInput.value = ''
  error.value = ''
  success.value = ''
  generatedAd.value = null
  generatedAdId.value = null
}

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

function getImageUrl(url) {
  if (url && (url.startsWith('http://') || url.startsWith('https://'))) {
    return url
  }
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
  return `${baseUrl}${url}`
}

function handleImageError(event) {
  console.error('Failed to load image:', event.target.src)
  event.target.style.display = 'none'
}

async function generateAd() {
  loading.value = true
  error.value = ''
  success.value = ''
  generatedAd.value = null

  try {
    // Parse categories
    const categories = categoriesInput.value
        .split(',')
        .map(c => c.trim())
        .filter(c => c.length > 0)

    if (categories.length === 0) {
      error.value = 'Please enter at least one product category'
      return
    }

    const payload = {
      event_name: form.value.event_name,
      product_categories: categories
    }

    if (form.value.product_name) payload.product_name = form.value.product_name
    if (form.value.location) payload.location = form.value.location
    if (form.value.company_name) payload.company_name = form.value.company_name

    console.log('🚀 Generating ad...')
    console.log('⏱️ This may take 20-40 seconds...')

    // Use apiLongRunning for ad generation with image (2 minute timeout)
    const response = await apiLongRunning.post('/api/v1/ads/generate', payload)

    generatedAd.value = response.data
    generatedAdId.value = response.data.id
    success.value = 'Ad generated successfully!'

    console.log('✅ Ad generated:', generatedAd.value)

    // Scroll to preview
    setTimeout(() => {
      window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})
    }, 100)

  } catch (err) {
    console.error('❌ Generation error:', err)
    error.value = err.response?.data?.detail || err.message || 'Failed to generate ad'
  } finally {
    loading.value = false
  }
}

async function evaluateAd() {
  if (!generatedAdId.value) return

  evaluating.value = true
  error.value = ''

  try {
    console.log('🧪 Evaluating ad...')
    const response = await api.post('/api/v1/ads/evaluate', {
      ad_id: generatedAdId.value
    })

    // Update ad with evaluation
    if (generatedAd.value) {
      generatedAd.value.evaluation_score = response.data.overall_score
      generatedAd.value.evaluation_details = response.data
    }

    success.value = `Ad evaluated! Overall score: ${response.data.overall_score}/10`

    console.log('✅ Evaluation complete:', response.data)
  } catch (err) {
    console.error('❌ Evaluation error:', err)
    error.value = err.response?.data?.detail || 'Failed to evaluate ad'
  } finally {
    evaluating.value = false
  }
}

async function regenerateAd() {
  if (!generatedAdId.value) return

  regenerating.value = true
  error.value = ''

  try {
    console.log('🔄 Regenerating ad...')
    console.log('⏱️ This may take 20-40 seconds...')

    // Use apiLongRunning for regeneration with image
    const response = await apiLongRunning.post('/api/v1/ads/regenerate', {
      ad_id: generatedAdId.value,
      regenerate_image: false
    })

    generatedAd.value = response.data
    generatedAdId.value = response.data.id
    success.value = 'Ad regenerated successfully!'

    console.log('✅ Ad regenerated:', generatedAd.value)

  } catch (err) {
    console.error('❌ Regeneration error:', err)
    error.value = err.response?.data?.detail || 'Failed to regenerate ad'
  } finally {
    regenerating.value = false
  }
}
</script>

<style scoped>
.input:focus {
  outline: none;
  border-color: rgba(124, 92, 255, 0.5);
  box-shadow: 0 0 0 3px rgba(124, 92, 255, 0.1);
}

.btn:disabled,
.btn-ghost:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}

img {
  max-width: 100%;
  height: auto;
  display: block;
}
</style>