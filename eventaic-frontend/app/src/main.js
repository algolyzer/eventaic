import {createApp} from 'vue'
import {createRouter, createWebHistory} from 'vue-router'
import App from './App.vue'
import './assets/tailwind.css'
import routes from './router'

// Create router
const router = createRouter({
    history: createWebHistory('/app/'),
    routes
})

// Simple auth guard without loops
router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('eventaic:token')
    const isAuthenticated = !!token
    const isAuthRoute = to.path.startsWith('/auth/')

    // If route requires auth and user is not authenticated
    if (to.meta.requiresAuth && !isAuthenticated) {
        // Redirect to login only if not already going there
        if (to.path !== '/auth/login') {
            next({
                path: '/auth/login',
                query: {redirect: to.fullPath}
            })
        } else {
            next()
        }
    }
    // If user is authenticated and tries to access auth pages
    else if (isAuthRoute && isAuthenticated) {
        // Redirect to dashboard
        next({path: '/dashboard'})
    }
    // Otherwise, proceed normally
    else {
        next()
    }
})

// Handle router errors
router.onError((error) => {
    console.error('Router error:', error)
    // If there's a navigation error, try to go to dashboard
    if (error.name === 'NavigationDuplicated') {
        // Ignore duplicate navigation
        return
    }
    // For other errors, redirect to dashboard as fallback
    router.push('/dashboard').catch(() => {
        // If dashboard also fails, go to login
        router.push('/auth/login').catch(() => {
            console.error('Critical routing error')
        })
    })
})

// Create and mount app
const app = createApp(App)
app.use(router)

// Global error handler
app.config.errorHandler = (err, instance, info) => {
    console.error('Vue error:', err, info)
    // Don't let errors crash the app
}

// Mount app
app.mount('#app')

// Prevent unhandled promise rejections from crashing the app
window.addEventListener('unhandledrejection', event => {
    console.error('Unhandled promise rejection:', event.reason)
    event.preventDefault()
})