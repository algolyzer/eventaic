<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <div class="text-white/60 text-sm">Admin</div>
        <div class="text-xl font-bold">Users</div>
      </div>
      <button class="btn rounded-xl px-4 py-2" @click="createDemo">Add user</button>
    </div>

    <div class="card overflow-x-auto">
      <table class="min-w-full text-sm">
        <thead class="text-left text-white/60 border-b border-white/10">
          <tr>
            <th class="p-4">Name</th>
            <th class="p-4">Email</th>
            <th class="p-4">Role</th>
            <th class="p-4">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id" class="border-b border-white/10">
            <td class="p-4">{{ u.name }}</td>
            <td class="p-4">{{ u.email }}</td>
            <td class="p-4">
              <span class="badge">{{ u.role }}</span>
            </td>
            <td class="p-4">
              <button class="btn-ghost border rounded-xl px-3 py-1" @click="remove(u.id)">Remove</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/services/api'

const users = ref([])

function createDemo() {
  const id = Math.random().toString(36).slice(2,8)
  users.value.unshift({ id, name: 'New User', email: `new${id}@eventaic.com`, role: 'member' })
}

async function load() {
  try {
    const r = await api.get('/api/v1/admin/users')
    users.value = r.data.users
  } catch {
    users.value = [
      { id: 1, name: 'Alex Doe', email: 'alex@example.com', role: 'owner' },
      { id: 2, name: 'Sam Park', email: 'sam@example.com', role: 'admin' },
      { id: 3, name: 'Riya K', email: 'riya@example.com', role: 'member' },
    ]
  }
}

async function remove(id) {
  try {
    await api.delete(`/api/v1/admin/users/${id}`)
    users.value = users.value.filter(u => u.id !== id)
  } catch {
    users.value = users.value.filter(u => u.id !== id)
  }
}

onMounted(load)
</script>
