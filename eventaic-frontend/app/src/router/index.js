import {createRouter, createWebHistory} from 'vue-router'
import {useAuthStore} from '@/stores/auth'

// Lazy pages (match the actual folders we created)
const Login = () => import('@/pages/auth/Login.vue')
const Register = () => import('@/pages/auth/Register.vue')
const Forgot = () => import('@/pages/auth/Forgot.vue')
const Dashboard = () => import('@/pages/Dashboard.vue')
const Profile = () => import('@/pages/Profile.vue')
const Company = () => import('@/pages/Company.vue')
const AdminOverview = () => import('@/pages/admin/AdminOverview.vue')
const AdminUsers = () => import('@/pages/admin/AdminUsers.vue')
const AdminCompanies = () => import('@/pages/admin/AdminCompanies.vue')

const router = createRouter({
    history: createWebHistory('/app'),
    routes: [
        {path: '/', redirect: '/dashboard'},
        {path: '/auth/login', name: 'login', component: Login, meta: {public: true}},
        {path: '/auth/register', name: 'register', component: Register, meta: {public: true}},
        {path: '/auth/forgot', name: 'forgot', component: Forgot, meta: {public: true}},

        {path: '/dashboard', name: 'dashboard', component: Dashboard},
        {path: '/profile', name: 'profile', component: Profile},
        {path: '/company', name: 'company', component: Company},

        {path: '/admin', name: 'admin', component: AdminOverview},
        {path: '/admin/users', name: 'admin-users', component: AdminUsers},
        {path: '/admin/companies', name: 'admin-companies', component: AdminCompanies},

        {path: '/:pathMatch(.*)*', redirect: '/dashboard'}
    ],
    scrollBehavior() {
        return {top: 0}
    }
})

router.beforeEach((to, _from, next) => {
    const auth = useAuthStore()
    if (!to.meta.public && !auth.isAuthenticated) {
        return next({name: 'login', query: {redirect: to.fullPath}})
    }
    next()
})

export default router
