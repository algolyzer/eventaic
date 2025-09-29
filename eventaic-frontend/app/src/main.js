import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './assets/tailwind.css'
import routes from './router'
import { useAuthStore } from './stores/auth'

const router = createRouter({
  history: createWebHistory('/app/'),
  routes
})

// Auth guard
router.beforeEach((to, from, next) => {
  const { isAuthenticated } = useAuthStore()

  if (to.meta.requiresAuth && !isAuthenticated.value) {
    next({ name: 'login', query: { redirect: to.fullPath } })
  } else if (to.meta.public && isAuthenticated.value && to.name === 'login') {
    next({ name: 'dashboard' })
  } else {
    next()
  }
})

const app = createApp(App)
app.use(router)
app.mount('#app')