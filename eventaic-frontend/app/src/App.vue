<template>
  <component :is="layout">
    <router-view />
  </component>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from './layouts/AppLayout.vue'
import AuthLayout from './layouts/AuthLayout.vue'

const route = useRoute()
const layout = computed(() => route.meta.layout === 'auth' ? AuthLayout : AppLayout)
</script>
