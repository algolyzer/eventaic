<template>
  <!-- Mobile overlay -->
  <div v-if="open" class="fixed inset-0 bg-black/40 z-40 md:hidden" @click="$emit('close')"></div>

  <aside :class="[open ? 'translate-x-0' : '-translate-x-full md:translate-x-0']"
         class="fixed md:static z-50 h-full w-72 border-r border-white/10 bg-black/40 backdrop-blur-xl transition-transform">

    <div class="p-4 flex items-center gap-3 border-b border-white/10">
      <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-violet to-brand-cyan"></div>
      <div class="font-extrabold text-xl">Eventaic</div>
    </div>

    <nav class="p-3 space-y-1">
      <RouterLink v-for="item in navItems" :key="item.to" :to="item.to"
                  class="flex items-center gap-3 px-3 py-2.5 rounded-xl border border-transparent hover:bg-white/5 transition-colors"
                  :class="{'bg-white/10 border-white/20': $route.path === item.to}">
        <span class="text-xl">{{ item.icon }}</span>
        <span class="font-medium">{{ item.label }}</span>
      </RouterLink>

      <div v-if="isAdmin" class="mt-6 pt-4 border-t border-white/10">
        <div class="px-3 mb-2 text-xs uppercase tracking-wide text-white/40">Admin</div>
        <RouterLink v-for="item in adminItems" :key="item.to" :to="item.to"
                    class="flex items-center gap-3 px-3 py-2.5 rounded-xl border border-transparent hover:bg-white/5 transition-colors"
                    :class="{'bg-white/10 border-white/20': $route.path === item.to}">
          <span class="text-xl">{{ item.icon }}</span>
          <span class="font-medium">{{ item.label }}</span>
        </RouterLink>
      </div>
    </nav>

    <div class="absolute bottom-0 left-0 right-0 p-3">
      <RouterLink to="/profile" class="block card p-3 hover:bg-white/10 transition">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-white/10 grid place-items-center">
            <span class="text-xl">👤</span>
          </div>
          <div class="min-w-0">
            <div class="font-semibold truncate">{{ userName }}</div>
            <div class="text-sm text-white/50 truncate">{{ userEmail }}</div>
          </div>
        </div>
      </RouterLink>
      <button @click="handleLogout" class="mt-2 w-full btn-ghost rounded-xl py-2.5 hover:bg-white/10 transition">
        Sign Out
      </button>
    </div>
  </aside>
</template>

<script setup>
import {computed} from 'vue'
import {RouterLink, useRouter} from 'vue-router'
import {useAuthStore} from '@/stores/auth'

const router = useRouter()
const {currentUser, logout} = useAuthStore()

const props = defineProps({
  open: {type: Boolean, default: false}
})

const emit = defineEmits(['close'])

const userName = computed(() => currentUser.value?.name || 'User')
const userEmail = computed(() => currentUser.value?.email || 'user@example.com')
const isAdmin = computed(() => currentUser.value?.role === 'admin' || true) // Show admin for demo

const navItems = [
  {to: '/dashboard', label: 'Dashboard', icon: '📊'},
  {to: '/company', label: 'Company', icon: '🏢'},
  {to: '/profile', label: 'Profile', icon: '⚙️'}
]

const adminItems = [
  {to: '/admin', label: 'Overview', icon: '🛠️'},
  {to: '/admin/users', label: 'Users', icon: '👥'},
  {to: '/admin/companies', label: 'Companies', icon: '🏢'}
]

function handleLogout() {
  logout()
  router.push('/auth/login')
}
</script>