<template>
  <div class="min-h-screen grid place-items-center px-4 py-10">
    <div class="w-full max-w-md card p-6">
      <div class="flex items-center justify-center gap-3 mb-6">
        <div class="w-10 h-10 rounded-xl" style="background: conic-gradient(from 220deg,#7c5cff,#00d4ff)"></div>
        <h1 class="text-2xl font-extrabold tracking-tight">Eventaic</h1>
      </div>
      <slot />
      <p class="mt-6 text-center text-white/50">
        © {{ new Date().getFullYear() }} Eventaic
      </p>
    </div>
  </div>
</template>

<script setup>
</script>
