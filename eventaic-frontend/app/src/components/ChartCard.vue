<template>
  <div class="card p-5">
    <div class="flex items-center justify-between mb-3">
      <div>
        <div class="text-white/60 text-sm">{{ subtitle }}</div>
        <div class="text-lg font-bold">{{ title }}</div>
      </div>
      <div class="badge">{{ period }}</div>
    </div>
    <canvas ref="canvas" height="120"></canvas>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { Chart, LineController, LineElement, PointElement, LinearScale, CategoryScale, BarController, BarElement, Filler, Tooltip, Legend } from 'chart.js'

Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, BarController, BarElement, Filler, Tooltip, Legend)

const props = defineProps({
  title: String,
  subtitle: String,
  period: { type: String, default: 'Last 14d' },
  labels: { type: Array, default: () => [] },
  series: { type: Array, default: () => [] }, // e.g. [{label:'CTR %', data:[...]}]
  type: { type: String, default: 'line' } // 'line' | 'bar'
})

const canvas = ref(null)
let chart

function render() {
  if (chart) chart.destroy()
  chart = new Chart(canvas.value, {
    type: props.type,
    data: {
      labels: props.labels,
      datasets: props.series.map((s, i) => ({
        label: s.label,
        data: s.data,
        tension: 0.35,
        fill: props.type === 'line',
        borderWidth: 2,
        pointRadius: 0,
      }))
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: true } },
      scales: {
        x: { ticks: { color: '#cfcfff' }, grid: { color: 'rgba(255,255,255,.08)' } },
        y: { ticks: { color: '#cfcfff' }, grid: { color: 'rgba(255,255,255,.08)' } },
      }
    }
  })
}

onMounted(render)
watch(() => [props.labels, props.series, props.type], render, { deep: true })
</script>
