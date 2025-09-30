const routes = [
    {path: '/', redirect: '/dashboard'},

    // Auth routes
    {
        path: '/auth/login',
        name: 'login',
        component: () => import('@/pages/Login.vue'),
        meta: {layout: 'auth', public: true}
    },
    {
        path: '/auth/register',
        name: 'register',
        component: () => import('@/pages/Register.vue'),
        meta: {layout: 'auth', public: true}
    },
    {
        path: '/auth/forgot',
        name: 'forgot',
        component: () => import('@/pages/Forgot.vue'),
        meta: {layout: 'auth', public: true}
    },

    // App routes
    {
        path: '/dashboard',
        name: 'dashboard',
        component: () => import('@/pages/Dashboard.vue'),
        meta: {requiresAuth: true}
    },
    {
        path: '/profile',
        name: 'profile',
        component: () => import('@/pages/Profile.vue'),
        meta: {requiresAuth: true}
    },
    {
        path: '/company',
        name: 'company',
        component: () => import('@/pages/CompanyProfile.vue'),
        meta: {requiresAuth: true}
    },

    // Ads routes
    {
        path: '/ads',
        name: 'ads',
        component: () => import('@/pages/AdsList.vue'),
        meta: {requiresAuth: true}
    },
    {
        path: '/ads/generate',
        name: 'generate-ad',
        component: () => import('@/pages/GenerateAd.vue'),
        meta: {requiresAuth: true}
    },
    {
        path: '/ads/:id',
        name: 'ad-detail',
        component: () => import('@/pages/AdDetail.vue'),
        meta: {requiresAuth: true}
    },

    // Admin routes
    {
        path: '/admin',
        name: 'admin',
        component: () => import('@/pages/Admin.vue'),
        meta: {requiresAuth: true}
    },
    {
        path: '/admin/users',
        name: 'admin-users',
        component: () => import('@/pages/AdminUsers.vue'),
        meta: {requiresAuth: true}
    },
    {
        path: '/admin/companies',
        name: 'admin-companies',
        component: () => import('@/pages/AdminCompanies.vue'),
        meta: {requiresAuth: true}
    },

    {path: '/:pathMatch(.*)*', redirect: '/dashboard'}
]

export default routes