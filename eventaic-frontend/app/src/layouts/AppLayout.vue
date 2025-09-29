<script setup>
import {ref} from 'vue'
import Sidebar from '@/components/Sidebar.vue'
import Topbar from '@/components/Topbar.vue'

const sidebarOpen = ref(false)
</script>

<template>
  <div class="min-h-screen flex">
    <Sidebar :open="sidebarOpen" @close="sidebarOpen = false"/>
    <div class="flex-1 flex flex-col md:ml-72">
      <Topbar @toggleSidebar="sidebarOpen = !sidebarOpen"/>
      <main class="flex-1">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 md:px-8 py-8">
          <slot/>
        </div>
      </main>
    </div>
  </div>
</template>