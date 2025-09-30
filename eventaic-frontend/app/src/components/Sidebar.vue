<template>
  <!-- Mobile overlay -->
  <div v-if="open" class="fixed inset-0 bg-black/40 z-40 md:hidden" @click="$emit('close')"></div>

  <aside :class="[open ? 'translate-x-0' : '-translate-x-full md:translate-x-0']"
         class="fixed md:static z-50 h-full w-72 border-r border-white/10 bg-black/40 backdrop-blur-xl transition-transform flex flex-col">

    <!-- Header -->
    <div class="p-4 flex items-center gap-3 border-b border-white/10 flex-shrink-0">
      <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-violet to-brand-cyan flex-shrink-0"></div>
      <div class="font-extrabold text-xl">Eventaic</div>
    </div>

    <!-- Navigation -->
    <nav class="p-3 space-y-1 flex-1 overflow-y-auto">
      <RouterLink v-for="item in navItems" :key="item.to" :to="item.to"
                  class="flex items-center gap-3 px-3 py-2.5 rounded-xl border border-transparent hover:bg-white/5 transition-colors"
                  :class="{'bg-white/10 border-white/20': $route.path === item.to}">
        <span class="text-xl flex-shrink-0">{{ item.icon }}</span>
        <span class="font-medium">{{ item.label }}</span>
      </RouterLink>

      <div v-if="isAdmin" class="mt-6 pt-4 border-t border-white/10">
        <div class="px-3 mb-2 text-xs uppercase tracking-wide text-white/40">Admin</div>
        <RouterLink v-for="item in adminItems" :key="item.to" :to="item.to"
                    class="flex items-center gap-3 px-3 py-2.5 rounded-xl border border-transparent hover:bg-white/5 transition-colors"
                    :class="{'bg-white/10 border-white/20': $route.path === item.to}">
          <span class="text-xl flex-shrink-0">{{ item.icon }}</span>
          <span class="font-medium">{{ item.label }}</span>
        </RouterLink>
      </div>
    </nav>

    <!-- User Profile Section - Fixed -->
    <div class="p-3 border-t border-white/10 flex-shrink-0">
      <RouterLink to="/profile" class="block card p-3 hover:bg-white/10 transition rounded-xl">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-white/10 grid place-items-center flex-shrink-0">
            <span class="text-xl">👤</span>
          </div>
          <div class="min-w-0 flex-1">
            <div class="font-semibold truncate text-sm">{{ displayName }}</div>
            <div class="text-xs text-white/50 truncate">{{ displayEmail }}</div>
          </div>
        </div>
      </RouterLink>
      <button @click="handleLogout"
              class="mt-2 w-full btn-ghost border rounded-xl py-2.5 hover:bg-white/10 transition text-sm">
        Sign Out
      </button>
    </div>
  </aside>
</template>

<script setup>
import {ref, computed, onMounted, onUnmounted, watch} from 'vue'
import {RouterLink, useRouter, useRoute} from 'vue-router'
import {useAuthStore} from '@/stores/auth'
import {getUser} from '@/services/api'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const props = defineProps({
  open: {type: Boolean, default: false}
})

const emit = defineEmits(['close'])

const userData = ref({
  name: 'Loading...',
  email: 'loading@example.com',
  role: 'company'
})

const isLoading = ref(true)

// Computed properties for display
const displayName = computed(() => {
  if (isLoading.value) return 'Loading...'
  return userData.value.name || 'User'
})

const displayEmail = computed(() => {
  if (isLoading.value) return 'loading...'
  return userData.value.email || 'user@example.com'
})

const isAdmin = computed(() => userData.value.role === 'super_admin')

const navItems = [
  {to: '/dashboard', label: 'Dashboard', icon: '📊'},
  {to: '/ads/generate', label: 'Generate Ad', icon: '✨'},
  {to: '/ads', label: 'My Ads', icon: '📢'},
  {to: '/company', label: 'Company', icon: '🏢'},
  {to: '/profile', label: 'Profile', icon: '⚙️'}
]

const adminItems = [
  {to: '/admin', label: 'Overview', icon: '🛠️'},
  {to: '/admin/users', label: 'Users', icon: '👥'},
  {to: '/admin/companies', label: 'Companies', icon: '🏢'}
]

function loadUserData() {
  isLoading.value = true

  try {
    // Priority 1: Get from auth store
    if (authStore?.currentUser?.value) {
      const user = authStore.currentUser.value
      userData.value = {
        name: user.full_name || user.name || user.username || 'User',
        email: user.email || 'user@example.com',
        role: user.role || 'company'
      }
      isLoading.value = false
      console.log('✅ Loaded user from auth store:', userData.value)
      return
    }

    // Priority 2: Get from localStorage
    const storedUser = localStorage.getItem('eventaic:user')
    if (storedUser) {
      try {
        const user = JSON.parse(storedUser)
        userData.value = {
          name: user.full_name || user.name || user.username || 'User',
          email: user.email || 'user@example.com',
          role: user.role || 'company'
        }
        isLoading.value = false
        console.log('✅ Loaded user from localStorage:', userData.value)
        return
      } catch (parseError) {
        console.error('❌ Error parsing stored user:', parseError)
      }
    }

    // Priority 3: Get from API
    const currentUser = getUser()
    if (currentUser) {
      userData.value = {
        name: currentUser.full_name || currentUser.name || currentUser.username || 'User',
        email: currentUser.email || 'user@example.com',
        role: currentUser.role || 'company'
      }
      isLoading.value = false
      console.log('✅ Loaded user from API helper:', userData.value)
      return
    }

  } catch (error) {
    console.error('❌ Error loading user data:', error)
  } finally {
    isLoading.value = false
  }

  // Fallback: Set default values
  console.warn('⚠️ Using default user data')
  userData.value = {
    name: 'User',
    email: 'user@example.com',
    role: 'company'
  }
}

function handleUserUpdate(event) {
  console.log('🔄 User update event received:', event.detail)

  if (event.detail) {
    userData.value = {
      name: event.detail.full_name || event.detail.name || event.detail.username || 'User',
      email: event.detail.email || 'user@example.com',
      role: event.detail.role || 'company'
    }

    // Also update auth store
    if (authStore && authStore.updateUser) {
      authStore.updateUser(event.detail)
    }

    console.log('✅ User data updated:', userData.value)
  } else {
    loadUserData()
  }
}

function handleStorageChange(e) {
  if (e.key === 'eventaic:user' && e.newValue) {
    console.log('🔄 Storage changed, reloading user data')
    loadUserData()
  }
}

function handleLogout() {
  console.log('🚪 Logging out...')
  authStore.logout()

  // Clear all user data
  userData.value = {
    name: 'User',
    email: 'user@example.com',
    role: 'company'
  }

  router.push('/auth/login')
}

// Watch for auth store changes
watch(
    () => authStore?.currentUser?.value,
    (newUser) => {
      if (newUser) {
        console.log('🔄 Auth store user changed:', newUser)
        userData.value = {
          name: newUser.full_name || newUser.name || newUser.username || 'User',
          email: newUser.email || 'user@example.com',
          role: newUser.role || 'company'
        }
      }
    },
    {deep: true}
)

// Watch for route changes (in case we need to reload)
watch(
    () => route.path,
    () => {
      // Reload user data on certain routes
      if (route.path === '/profile' || route.path === '/dashboard') {
        loadUserData()
      }
    }
)

onMounted(() => {
  console.log('🚀 Sidebar mounted, loading user data...')

  // Load user data immediately
  loadUserData()

  // Set up event listeners
  window.addEventListener('user-updated', handleUserUpdate)
  window.addEventListener('storage', handleStorageChange)

  // Also listen for login events
  window.addEventListener('user-logged-in', loadUserData)
})

onUnmounted(() => {
  console.log('👋 Sidebar unmounting, cleaning up listeners')
  window.removeEventListener('user-updated', handleUserUpdate)
  window.removeEventListener('storage', handleStorageChange)
  window.removeEventListener('user-logged-in', loadUserData)
})
</script>

<style scoped>
aside {
  transition: transform 0.3s ease;
}

.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Ensure proper flexbox layout */
aside {
  display: flex;
  flex-direction: column;
}

/* Prevent text overlap */
nav {
  overflow-y: auto;
  overflow-x: hidden;
}

/* Better responsive text */
@media (max-width: 768px) {
  .font-semibold {
    font-size: 0.875rem;
  }

  .text-xs {
    font-size: 0.75rem;
  }
}

/* Loading animation */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.loading {
  animation: pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>