<template>
  <transition name="fade">
    <div v-if="open" class="fixed bottom-4 right-4 card p-4 max-w-sm">
      <div class="font-semibold mb-1">{{ title }}</div>
      <div class="text-white/70">{{ message }}</div>
    </div>
  </transition>
</template>

<script setup>
import { ref, watchEffect } from 'vue'
const props = defineProps({ title: String, message: String, duration: { type: Number, default: 1800 }, show: Boolean })
const open = ref(false)
watchEffect(() => {
  if (props.show) {
    open.value = true
    setTimeout(() => open.value = false, props.duration)
  }
})
</script>

<style>
.fade-enter-active,.fade-leave-active{transition:opacity .2s ease}
.fade-enter-from,.fade-leave-to{opacity:0}
</style>
