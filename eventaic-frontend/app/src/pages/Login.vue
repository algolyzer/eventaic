<template>
  <div>
    <h2 class="text-xl font-bold mb-2">Welcome back</h2>
    <p class="text-white/60 mb-6">Log in to your Eventaic account</p>
    <form @submit.prevent="submit" class="space-y-3">
      <input v-model="email" type="email" class="input" placeholder="you@company.com" required />
      <input v-model="password" type="password" class="input" placeholder="••••••••" required />
      <button class="btn w-full justify-center">Log in</button>
    </form>
    <div class="mt-4 flex justify-between text-sm">
      <RouterLink class="link" to="/auth/forgot">Forgot password?</RouterLink>
      <RouterLink class="link" to="/auth/register">Create account</RouterLink>
    </div>
    <Toast :show="toast.show" :title="toast.title" :message="toast.msg" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { login } from '@/services/api'
import Toast from '@/components/Toast.vue'

const router = useRouter()
const email = ref('')
const password = ref('')
const toast = ref({ show: false, title: '', msg: '' })

async function submit() {
  try {
    await login({ email: email.value, password: password.value })
    router.replace('/dashboard')
  } catch (e) {
    toast.value = { show: true, title: 'Login failed', msg: e.message || 'Please check your credentials.' }
  }
}
</script>
