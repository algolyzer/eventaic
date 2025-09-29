<script setup>
import {ref} from 'vue'
import Sidebar from '@/components/layout/Sidebar.vue'
import Topbar from '@/components/layout/Topbar.vue'

const open = ref(false)
</script>

<template>
  <div class="min-h-screen grid grid-cols-1 lg:grid-cols-[18rem_1fr]">
    <Sidebar :open="open" @logout="$emit('logout')"/>
    <div class="lg:ml-72">
      <Topbar @toggle="open = !open"/>
      <main class="max-w-7xl mx-auto px-4 py-6">
        <slot/>
      </main>
    </div>
  </div>
</template>
