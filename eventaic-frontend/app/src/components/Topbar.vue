<template>
  <header class="sticky top-0 z-30 border-b border-white/10 bg-black/30 backdrop-blur-xl">
    <div class="px-4 md:px-6 h-14 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <button class="md:hidden btn-ghost border rounded-xl px-3 py-2" @click="$emit('toggleSidebar')">☰</button>
        <span class="badge hidden md:inline-flex">⚡ Event-Responsive Ads</span>
      </div>
      <div class="flex items-center gap-2">
        <RouterLink to="/dashboard" class="btn-ghost border rounded-full px-3 py-2">🏠</RouterLink>
        <a href="/" class="btn rounded-full px-4 py-2 hidden sm:inline-flex">Landing</a>
      </div>
    </div>
  </header>
</template>

<script setup>
import { RouterLink } from 'vue-router'
</script>
