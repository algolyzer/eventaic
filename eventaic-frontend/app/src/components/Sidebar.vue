<template>
  <!-- Mobile overlay -->
  <div v-if="open" class="fixed inset-0 bg-black/40 z-40 md:hidden" @click="$emit('close')"></div>

  <aside :class="[open ? 'translate-x-0' : '-translate-x-full md:translate-x-0']"
         class="fixed md:static z-50 h-full w-72 md:w-72 border-r border-white/10 bg-black/40 backdrop-blur-xl transition-transform">
    <div class="p-4 flex items-center gap-3 border-b border-white/10">
      <div class="w-9 h-9 rounded-xl" style="background: conic-gradient(from 220deg,#7c5cff,#00d4ff)"></div>
      <div class="font-extrabold tracking-tight">Eventaic</div>
    </div>

    <nav class="p-3 space-y-1">
      <RouterLink v-for="i in primary" :key="i.to" :to="i.to"
                  class="flex items-center gap-3 px-3 py-2 rounded-xl border border-transparent hover:bg-white/5"
                  :class="{'nav-active': $route.path===i.to}">
        <span class="text-xl">{{ i.ic }}</span>
        <span class="font-medium">{{ i.label }}</span>
      </RouterLink>

      <div class="mt-4 px-3 text-xs uppercase tracking-wide text-white/40">Admin</div>
      <RouterLink v-for="i in admin" :key="i.to" :to="i.to"
                  class="flex items-center gap-3 px-3 py-2 rounded-xl border border-transparent hover:bg-white/5"
                  :class="{'nav-active': $route.path===i.to}">
        <span class="text-xl">{{ i.ic }}</span>
        <span class="font-medium">{{ i.label }}</span>
      </RouterLink>
    </nav>

    <div class="absolute bottom-0 left-0 right-0 p-3">
      <RouterLink to='/profile' class="block card p-3 hover:bg-white/10 transition">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-white/10 grid place-items-center">👤</div>
          <div class="min-w-0">
            <div class="font-semibold truncate">My Account</div>
            <div class="text-sm text-white/50 truncate">{{ email || 'you@company.com' }}</div>
          </div>
        </div>
      </RouterLink>
      <button @click="logout" class="mt-2 w-full btn-ghost rounded-xl py-2">Log out</button>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { getUser, clearAuth } from '@/services/api'

const router = useRouter()
const email = computed(() => getUser()?.email)

const primary = [
  { to: '/dashboard', label: 'Dashboard', ic: '📊' },
  { to: '/company', label: 'Company', ic: '🏢' },
]

const admin = [
  { to: '/admin', label: 'Overview', ic: '🛠️' },
  { to: '/admin/users', label: 'Users', ic: '👥' },
  { to: '/admin/companies', label: 'Companies', ic: '🏢' },
]

defineProps({ open: { type: Boolean, default: false } })
const emit = defineEmits(['close'])

function logout() {
  clearAuth()
  router.push({ name: 'login' })
}
</script>
