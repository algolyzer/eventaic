<template>
  <div>
    <h2 class="text-xl font-bold mb-2">Reset your password</h2>
    <p class="text-white/60 mb-6">We’ll email you a reset link</p>
    <form @submit.prevent="submit" class="space-y-3">
      <input v-model="email" type="email" class="input" placeholder="you@company.com" required />
      <button class="btn w-full justify-center">Send reset link</button>
    </form>
    <div class="mt-4 text-sm">
      <RouterLink class="link" to="/auth/login">Back to login</RouterLink>
    </div>
    <Toast :show="toast.show" :title="toast.title" :message="toast.msg" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { forgotPassword } from '@/services/api'
import Toast from '@/components/Toast.vue'

const email = ref('')
const toast = ref({ show: false, title: '', msg: '' })

async function submit() {
  try {
    await forgotPassword({ email: email.value })
    toast.value = { show: true, title: 'Email sent', msg: 'Check your inbox for the reset link.' }
  } catch (e) {
    toast.value = { show: true, title: 'Error', msg: e.message || 'Could not send email.' }
  }
}
</script>
