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
            <div class="font-semibold truncate text-sm">{{ userData.name }}</div>
            <div class="text-xs text-white/50 truncate">{{ userData.email }}</div>
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
import {ref, computed, onMounted, onUnmounted} from 'vue'
import {RouterLink, useRouter} from 'vue-router'
import {useAuthStore} from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const props = defineProps({
  open: {type: Boolean, default: false}
})

const emit = defineEmits(['close'])

const userData = ref({
  name: 'User',
  email: 'user@example.com',
  role: 'company'
})

function loadUserData() {
  if (authStore.currentUser?.value) {
    userData.value = {
      name: authStore.currentUser.value.full_name || authStore.currentUser.value.name || 'User',
      email: authStore.currentUser.value.email || 'user@example.com',
      role: authStore.currentUser.value.role || 'company'
    }
    return
  }

  try {
    const storedUser = localStorage.getItem('eventaic:user')
    if (storedUser) {
      const user = JSON.parse(storedUser)
      userData.value = {
        name: user.full_name || user.name || 'User',
        email: user.email || 'user@example.com',
        role: user.role || 'company'
      }
      return
    }
  } catch (error) {
    console.error('Error loading user data:', error)
  }

  userData.value = {
    name: 'User',
    email: 'user@example.com',
    role: 'company'
  }
}

function handleUserUpdate(event) {
  if (event.detail) {
    userData.value = {
      name: event.detail.full_name || event.detail.name || 'User',
      email: event.detail.email || 'user@example.com',
      role: event.detail.role || 'company'
    }
  } else {
    loadUserData()
  }
}

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

function handleLogout() {
  authStore.logout()
  router.push('/auth/login')
}

onMounted(() => {
  loadUserData()
  window.addEventListener('user-updated', handleUserUpdate)
  window.addEventListener('storage', (e) => {
    if (e.key === 'eventaic:user') {
      loadUserData()
    }
  })
})

onUnmounted(() => {
  window.removeEventListener('user-updated', handleUserUpdate)
  window.removeEventListener('storage', loadUserData)
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
</style>