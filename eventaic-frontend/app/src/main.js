import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './assets/tailwind.css'
import routes from './router'
import { api, getToken } from './services/api'

const router = createRouter({
  history: createWebHistory('/app/'),
  routes
})

// Auth guard
router.beforeEach((to, from, next) => {
  const authed = !!getToken()
  if (to.meta.requiresAuth && !authed) {
    next({ name: 'login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

createApp(App).use(router).mount('#app')
