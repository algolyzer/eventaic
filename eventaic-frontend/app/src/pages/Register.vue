<template>
  <div>
    <h2 class="text-xl font-bold mb-2">Create your account</h2>
    <p class="text-white/60 mb-6">Start generating event-driven campaigns</p>
    <form @submit.prevent="submit" class="space-y-3">
      <input v-model="name" class="input" placeholder="Your name" required />
      <input v-model="email" type="email" class="input" placeholder="you@company.com" required />
      <input v-model="password" type="password" class="input" placeholder="Create a password" required />
      <button class="btn w-full justify-center">Create account</button>
    </form>
    <div class="mt-4 text-sm">
      Already have an account? <RouterLink class="link" to="/auth/login">Log in</RouterLink>
    </div>
    <Toast :show="toast.show" :title="toast.title" :message="toast.msg" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { register as apiRegister } from '@/services/api'
import Toast from '@/components/Toast.vue'

const router = useRouter()
const name = ref('')
const email = ref('')
const password = ref('')
const toast = ref({ show: false, title: '', msg: '' })

async function submit() {
  try {
    await apiRegister({ name: name.value, email: email.value, password: password.value })
    router.replace('/dashboard')
  } catch (e) {
    toast.value = { show: true, title: 'Registration failed', msg: e.message || 'Try again.' }
  }
}
</script>
