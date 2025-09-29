<template>
  <div class="card p-5 flex items-start gap-4">
    <div class="text-2xl">{{ ic }}</div>
    <div class="min-w-0">
      <div class="text-white/60 text-sm">{{ label }}</div>
      <div class="text-2xl font-extrabold tracking-tight">{{ value }}</div>
    </div>
    <div class="ml-auto text-right">
      <div class="text-sm" :class="trend >= 0 ? 'text-green-400' : 'text-red-400'">
        {{ trend >= 0 ? '▲' : '▼' }} {{ Math.abs(trend) }}%
      </div>
      <div class="text-xs text-white/50">vs last period</div>
    </div>
  </div>
</template>
<script setup>
defineProps({
  ic: String,
  label: String,
  value: [String, Number],
  trend: { type: Number, default: 0 }
})
</script>
