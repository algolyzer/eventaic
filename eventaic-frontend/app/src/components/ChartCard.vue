<template>
  <div class="card p-5">
    <div class="flex items-center justify-between mb-3">
      <div>
        <div class="text-white/60 text-sm">{{ subtitle }}</div>
        <div class="text-lg font-bold">{{ title }}</div>
      </div>
      <div v-if="period" class="badge">{{ period }}</div>
    </div>
    <div class="min-h-chart">
      <canvas ref="canvasRef" :height="height"></canvas>
    </div>
  </div>
</template>

<script setup>
import {ref, onMounted, onUnmounted, watch, nextTick} from 'vue'
import {Chart, registerables} from 'chart.js'

// Register Chart.js components
Chart.register(...registerables)

const props = defineProps({
  title: String,
  subtitle: String,
  period: {type: String, default: ''},
  labels: {
    type: Array,
    default: () => [],
    validator: (value) => Array.isArray(value)
  },
  series: {
    type: Array,
    default: () => [],
    validator: (value) => Array.isArray(value)
  },
  type: {
    type: String,
    default: 'line',
    validator: (value) => ['line', 'bar'].includes(value)
  },
  height: {
    type: Number,
    default: 120
  }
})

const canvasRef = ref(null)
let chartInstance = null
let renderTimeout = null

// Function to safely destroy chart
function destroyChart() {
  if (renderTimeout) {
    clearTimeout(renderTimeout)
    renderTimeout = null
  }

  if (chartInstance) {
    try {
      chartInstance.destroy()
      chartInstance = null
    } catch (err) {
      console.warn('Chart destroy error:', err)
      chartInstance = null
    }
  }
}

// Function to create/update chart
function renderChart() {
  // Clear any pending renders
  if (renderTimeout) {
    clearTimeout(renderTimeout)
  }

  // Delay render slightly to batch updates
  renderTimeout = setTimeout(() => {
    // Destroy existing chart
    destroyChart()

    // Check if we have valid data and canvas
    if (!canvasRef.value || !props.labels?.length || !props.series?.length) {
      console.log('Skipping chart render - missing data or canvas')
      return
    }

    try {
      const ctx = canvasRef.value.getContext('2d')

      // Prepare datasets with safe defaults
      const datasets = props.series.map((s, index) => ({
        label: s.label || `Series ${index + 1}`,
        data: Array.isArray(s.data) ? s.data : [],
        tension: props.type === 'line' ? 0.35 : 0,
        fill: props.type === 'line' ? false : true,
        borderWidth: 2,
        pointRadius: props.type === 'line' ? 0 : undefined,
        backgroundColor: index === 0
            ? 'rgba(124, 92, 255, 0.5)'
            : 'rgba(0, 212, 255, 0.5)',
        borderColor: index === 0
            ? 'rgba(124, 92, 255, 1)'
            : 'rgba(0, 212, 255, 1)'
      }))

      // Create new chart
      chartInstance = new Chart(ctx, {
        type: props.type,
        data: {
          labels: props.labels,
          datasets: datasets
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: {
            mode: 'index',
            intersect: false
          },
          plugins: {
            legend: {
              display: props.series.length > 1,
              position: 'top',
              labels: {
                color: '#cfcfff',
                padding: 10,
                font: {
                  size: 11
                }
              }
            },
            tooltip: {
              enabled: true,
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              titleColor: '#fff',
              bodyColor: '#cfcfff',
              borderColor: 'rgba(255, 255, 255, 0.1)',
              borderWidth: 1,
              padding: 8,
              displayColors: true,
              callbacks: {
                label: function (context) {
                  let label = context.dataset.label || '';
                  if (label) {
                    label += ': ';
                  }
                  if (context.parsed.y !== null) {
                    label += context.parsed.y;
                  }
                  return label;
                }
              }
            }
          },
          scales: {
            x: {
              grid: {
                color: 'rgba(255, 255, 255, 0.08)',
                drawBorder: false
              },
              ticks: {
                color: '#cfcfff',
                font: {
                  size: 10
                },
                maxRotation: 45,
                minRotation: 0
              }
            },
            y: {
              grid: {
                color: 'rgba(255, 255, 255, 0.08)',
                drawBorder: false
              },
              ticks: {
                color: '#cfcfff',
                font: {
                  size: 10
                },
                padding: 5
              },
              beginAtZero: true
            }
          }
        }
      })
    } catch (err) {
      console.error('Chart render error:', err)
    }
  }, 100) // Small delay to batch updates
}

// Lifecycle hooks
onMounted(() => {
  nextTick(() => {
    if (props.labels?.length && props.series?.length) {
      renderChart()
    }
  })
})

onUnmounted(() => {
  destroyChart()
})

// Watch for prop changes (with debouncing)
let updateTimeout = null
watch(
    () => [props.labels, props.series, props.type],
    () => {
      if (updateTimeout) {
        clearTimeout(updateTimeout)
      }
      updateTimeout = setTimeout(() => {
        if (props.labels?.length && props.series?.length) {
          renderChart()
        }
      }, 200) // Debounce updates
    },
    {deep: true}
)
</script>

<style scoped>
.min-h-chart {
  min-height: 180px;
  position: relative;
}

.card {
  transition: all 0.3s ease;
}
</style>