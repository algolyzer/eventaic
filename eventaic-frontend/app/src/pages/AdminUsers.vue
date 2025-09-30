<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <div class="text-white/60 text-sm">Admin</div>
        <div class="text-xl font-bold">Users Management</div>
        <p class="text-white/60 text-sm mt-1">Total users: {{ users.length }}</p>
      </div>
      <button
          class="btn rounded-xl px-4 py-2"
          @click="showCreateModal = true"
          :disabled="loading"
      >
        ➕ Add User
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="card p-8">
      <div class="flex items-center justify-center gap-3">
        <div class="animate-spin text-2xl">⚙️</div>
        <span class="text-white/60">Loading users...</span>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="loadError" class="card p-5 border-red-500/20 bg-red-500/5">
      <p class="text-red-400 mb-3">{{ loadError }}</p>
      <button @click="load" class="btn">Retry</button>
    </div>

    <!-- Empty State -->
    <div v-else-if="users.length === 0" class="card p-12 text-center">
      <div class="text-6xl mb-4">👥</div>
      <h3 class="text-xl font-bold mb-2">No users yet</h3>
      <p class="text-white/60 mb-4">Create your first user to get started</p>
      <button @click="showCreateModal = true" class="btn">
        Create First User
      </button>
    </div>

    <!-- Users Table -->
    <div v-else class="card overflow-x-auto">
      <table class="min-w-full text-sm">
        <thead class="text-left text-white/60 border-b border-white/10">
        <tr>
          <th class="p-4">Name</th>
          <th class="p-4">Email</th>
          <th class="p-4">Username</th>
          <th class="p-4">Company</th>
          <th class="p-4">Role</th>
          <th class="p-4">Status</th>
          <th class="p-4 text-right">Actions</th>
        </tr>
        </thead>
        <tbody>
        <tr
            v-for="user in users"
            :key="user.id"
            class="border-b border-white/10 hover:bg-white/5 transition"
        >
          <td class="p-4">
            <div class="font-medium">{{ user.full_name || user.name || '—' }}</div>
          </td>
          <td class="p-4">
            <div class="text-white/80">{{ user.email }}</div>
          </td>
          <td class="p-4">
            <div class="text-white/60">{{ user.username || '—' }}</div>
          </td>
          <td class="p-4">
            <div class="text-white/60">{{ user.company || user.company_name || '—' }}</div>
          </td>
          <td class="p-4">
              <span
                  class="badge"
                  :class="user.role === 'super_admin' ? 'bg-purple-500/20 border-purple-500/30' : 'bg-blue-500/20 border-blue-500/30'"
              >
                {{ formatRole(user.role) }}
              </span>
          </td>
          <td class="p-4">
              <span
                  class="badge text-xs"
                  :class="user.is_active ? 'bg-green-500/20 border-green-500/30 text-green-400' : 'bg-red-500/20 border-red-500/30 text-red-400'"
              >
                {{ user.is_active ? '✓ Active' : '✗ Inactive' }}
              </span>
          </td>
          <td class="p-4">
            <div class="flex items-center justify-end gap-2">
              <button
                  class="btn-ghost border rounded-xl px-3 py-1 text-xs"
                  @click="viewUser(user)"
                  title="View details"
              >
                👁️ View
              </button>
              <button
                  v-if="user.is_active"
                  class="btn-ghost border border-yellow-500/30 rounded-xl px-3 py-1 text-xs hover:bg-yellow-500/10"
                  @click="toggleUserStatus(user.id, false)"
                  :disabled="togglingId === user.id"
                  title="Deactivate user"
              >
                {{ togglingId === user.id ? '...' : '🔒' }}
              </button>
              <button
                  v-else
                  class="btn-ghost border border-green-500/30 rounded-xl px-3 py-1 text-xs hover:bg-green-500/10"
                  @click="toggleUserStatus(user.id, true)"
                  :disabled="togglingId === user.id"
                  title="Activate user"
              >
                {{ togglingId === user.id ? '...' : '🔓' }}
              </button>
              <button
                  class="btn-ghost border border-red-500/30 rounded-xl px-3 py-1 text-xs hover:bg-red-500/10"
                  @click="deleteUser(user.id)"
                  :disabled="deletingId === user.id"
                  title="Delete user"
              >
                {{ deletingId === user.id ? '...' : '🗑️' }}
              </button>
            </div>
          </td>
        </tr>
        </tbody>
      </table>
    </div>

    <!-- Create User Modal -->
    <Teleport to="body">
      <div
          v-if="showCreateModal"
          class="fixed inset-0 bg-black/70 z-50 grid place-items-center p-4 overflow-y-auto"
          @click.self="closeModal"
      >
        <div class="card p-6 max-w-md w-full my-8" @click.stop>
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-xl font-bold">Create New User</h3>
            <button
                @click="closeModal"
                class="text-white/60 hover:text-white text-2xl leading-none"
                :disabled="creating"
            >
              ✕
            </button>
          </div>

          <form @submit.prevent="createUser" class="space-y-3">
            <div>
              <label class="block text-sm font-medium mb-1">Full Name *</label>
              <input
                  v-model="newUser.full_name"
                  type="text"
                  class="input"
                  placeholder="John Doe"
                  required
                  :disabled="creating"
              />
            </div>

            <div>
              <label class="block text-sm font-medium mb-1">Email *</label>
              <input
                  v-model="newUser.email"
                  type="email"
                  class="input"
                  placeholder="john@company.com"
                  required
                  :disabled="creating"
              />
            </div>

            <div>
              <label class="block text-sm font-medium mb-1">Username *</label>
              <input
                  v-model="newUser.username"
                  type="text"
                  class="input"
                  placeholder="johndoe"
                  required
                  minlength="3"
                  pattern="[a-zA-Z0-9_-]+"
                  title="Only letters, numbers, underscores and hyphens"
                  :disabled="creating"
              />
              <p class="text-xs text-white/50 mt-1">3-50 characters, alphanumeric only</p>
            </div>

            <div>
              <label class="block text-sm font-medium mb-1">Company Name *</label>
              <input
                  v-model="newUser.company_name"
                  type="text"
                  class="input"
                  placeholder="Acme Inc"
                  required
                  :disabled="creating"
              />
            </div>

            <div>
              <label class="block text-sm font-medium mb-1">Phone (Optional)</label>
              <input
                  v-model="newUser.phone"
                  type="tel"
                  class="input"
                  placeholder="+1234567890"
                  :disabled="creating"
              />
            </div>

            <div>
              <label class="block text-sm font-medium mb-1">Password *</label>
              <input
                  v-model="newUser.password"
                  type="password"
                  class="input"
                  placeholder="••••••••"
                  required
                  minlength="8"
                  :disabled="creating"
              />
              <p class="text-xs text-white/50 mt-1">
                Min 8 chars with uppercase, lowercase, number & special character
              </p>
            </div>

            <div>
              <label class="block text-sm font-medium mb-1">Role *</label>
              <select v-model="newUser.role" class="input" :disabled="creating">
                <option value="company">Company User</option>
                <option value="super_admin">Super Admin</option>
              </select>
            </div>

            <div class="flex gap-2 pt-3">
              <button
                  type="submit"
                  class="btn flex-1 justify-center"
                  :disabled="creating"
              >
                <span v-if="creating">Creating...</span>
                <span v-else>✓ Create User</span>
              </button>
              <button
                  type="button"
                  @click="closeModal"
                  class="btn-ghost border rounded-xl px-4 py-2"
                  :disabled="creating"
              >
                Cancel
              </button>
            </div>
          </form>

          <div v-if="createError"
               class="mt-3 p-3 rounded-xl bg-red-500/20 border border-red-500/30 text-red-400 text-sm">
            {{ createError }}
          </div>

          <div v-if="createSuccess"
               class="mt-3 p-3 rounded-xl bg-green-500/20 border border-green-500/30 text-green-400 text-sm">
            {{ createSuccess }}
          </div>
        </div>
      </div>
    </Teleport>

    <!-- View User Modal -->
    <Teleport to="body">
      <div
          v-if="viewingUser"
          class="fixed inset-0 bg-black/70 z-50 grid place-items-center p-4 overflow-y-auto"
          @click.self="viewingUser = null"
      >
        <div class="card p-6 max-w-lg w-full my-8" @click.stop>
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-xl font-bold">User Details</h3>
            <button
                @click="viewingUser = null"
                class="text-white/60 hover:text-white text-2xl leading-none"
            >
              ✕
            </button>
          </div>

          <div class="space-y-3">
            <div class="grid grid-cols-2 gap-3">
              <div>
                <div class="text-xs text-white/50 mb-1">Full Name</div>
                <div class="font-medium">{{ viewingUser.full_name || '—' }}</div>
              </div>
              <div>
                <div class="text-xs text-white/50 mb-1">Username</div>
                <div class="font-medium">{{ viewingUser.username || '—' }}</div>
              </div>
            </div>

            <div>
              <div class="text-xs text-white/50 mb-1">Email</div>
              <div class="font-medium">{{ viewingUser.email }}</div>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <div class="text-xs text-white/50 mb-1">Role</div>
                <span class="badge">{{ formatRole(viewingUser.role) }}</span>
              </div>
              <div>
                <div class="text-xs text-white/50 mb-1">Status</div>
                <span
                    class="badge text-xs"
                    :class="viewingUser.is_active ? 'bg-green-500/20 border-green-500/30 text-green-400' : 'bg-red-500/20 border-red-500/30 text-red-400'"
                >
                  {{ viewingUser.is_active ? 'Active' : 'Inactive' }}
                </span>
              </div>
            </div>

            <div>
              <div class="text-xs text-white/50 mb-1">Company</div>
              <div class="font-medium">{{ viewingUser.company || viewingUser.company_name || '—' }}</div>
            </div>

            <div>
              <div class="text-xs text-white/50 mb-1">Phone</div>
              <div class="font-medium">{{ viewingUser.phone || '—' }}</div>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <div class="text-xs text-white/50 mb-1">Created</div>
                <div class="text-sm">{{ formatDate(viewingUser.created_at) }}</div>
              </div>
              <div>
                <div class="text-xs text-white/50 mb-1">Last Login</div>
                <div class="text-sm">{{ formatDate(viewingUser.last_login) || 'Never' }}</div>
              </div>
            </div>

            <div>
              <div class="text-xs text-white/50 mb-1">Email Verified</div>
              <span class="badge text-xs">
                {{ viewingUser.is_email_verified ? '✓ Verified' : '✗ Not Verified' }}
              </span>
            </div>
          </div>

          <button
              @click="viewingUser = null"
              class="btn w-full justify-center mt-4"
          >
            Close
          </button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import {ref, onMounted} from 'vue'
import {api} from '@/services/api'

const users = ref([])
const loading = ref(false)
const loadError = ref('')
const showCreateModal = ref(false)
const creating = ref(false)
const createError = ref('')
const createSuccess = ref('')
const deletingId = ref(null)
const togglingId = ref(null)
const viewingUser = ref(null)

const newUser = ref({
  full_name: '',
  email: '',
  username: '',
  company_name: '',
  phone: '',
  password: '',
  role: 'company'
})

function formatRole(role) {
  const roles = {
    'company': 'Company User',
    'super_admin': 'Super Admin',
    'COMPANY': 'Company User',
    'SUPER_ADMIN': 'Super Admin'
  }
  return roles[role] || role
}

function formatDate(dateStr) {
  if (!dateStr) return '—'
  try {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return '—'
  }
}

function viewUser(user) {
  viewingUser.value = user
}

function closeModal() {
  showCreateModal.value = false
  createError.value = ''
  createSuccess.value = ''
  newUser.value = {
    full_name: '',
    email: '',
    username: '',
    company_name: '',
    phone: '',
    password: '',
    role: 'company'
  }
}

async function createUser() {
  creating.value = true
  createError.value = ''
  createSuccess.value = ''

  try {
    // Validate inputs
    if (!newUser.value.email || !newUser.value.username || !newUser.value.full_name || !newUser.value.password) {
      createError.value = 'Please fill in all required fields'
      return
    }

    // Validate password
    const password = newUser.value.password
    if (password.length < 8) {
      createError.value = 'Password must be at least 8 characters'
      return
    }
    if (!/[A-Z]/.test(password)) {
      createError.value = 'Password must contain at least one uppercase letter'
      return
    }
    if (!/[a-z]/.test(password)) {
      createError.value = 'Password must contain at least one lowercase letter'
      return
    }
    if (!/[0-9]/.test(password)) {
      createError.value = 'Password must contain at least one number'
      return
    }
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      createError.value = 'Password must contain at least one special character'
      return
    }

    // Validate username
    if (newUser.value.username.length < 3 || newUser.value.username.length > 50) {
      createError.value = 'Username must be 3-50 characters'
      return
    }
    if (!/^[a-zA-Z0-9_-]+$/.test(newUser.value.username)) {
      createError.value = 'Username can only contain letters, numbers, underscores and hyphens'
      return
    }

    console.log('Creating user with data:', {
      email: newUser.value.email,
      username: newUser.value.username,
      full_name: newUser.value.full_name,
      company_name: newUser.value.company_name || undefined,
      phone: newUser.value.phone || undefined,
      role: newUser.value.role
    })

    const response = await api.post('/api/v1/admin/users', {
      email: newUser.value.email.trim(),
      username: newUser.value.username.trim(),
      full_name: newUser.value.full_name.trim(),
      password: newUser.value.password,
      company_name: newUser.value.company_name.trim() || undefined,
      phone: newUser.value.phone.trim() || undefined,
      role: newUser.value.role
    })

    console.log('User created successfully:', response.data)

    createSuccess.value = 'User created successfully!'

    // Wait a bit to show success message
    setTimeout(async () => {
      // Reload users
      await load()
      // Close modal
      closeModal()
    }, 1500)

  } catch (error) {
    console.error('❌ Create user error:', error)
    console.error('Error response:', error.response?.data)
    console.error('Error status:', error.response?.status)

    const detail = error.response?.data?.detail
    if (typeof detail === 'string') {
      createError.value = detail
    } else if (Array.isArray(detail)) {
      // Pydantic validation errors
      const errors = detail.map(e => {
        const field = e.loc?.join('.') || 'field'
        const msg = e.msg || 'Invalid value'
        return `${field}: ${msg}`
      }).join(', ')
      createError.value = errors
    } else if (error.response?.data?.message) {
      createError.value = error.response.data.message
    } else if (error.message) {
      createError.value = error.message
    } else {
      createError.value = 'Failed to create user. Please try again.'
    }
  } finally {
    creating.value = false
  }
}

async function load() {
  loading.value = true
  loadError.value = ''

  try {
    console.log('Loading users from admin endpoint...')

    const response = await api.get('/api/v1/admin/users', {
      params: {
        page: 1,
        per_page: 100
      }
    })

    console.log('Users API response:', response.data)

    // Handle different response formats
    if (response.data.users) {
      users.value = response.data.users
    } else if (Array.isArray(response.data)) {
      users.value = response.data
    } else {
      users.value = []
    }

    console.log('Loaded users:', users.value)

  } catch (error) {
    console.error('Load users error:', error)
    console.error('Error details:', {
      status: error.response?.status,
      data: error.response?.data,
      message: error.message
    })

    loadError.value = error.response?.data?.detail || 'Failed to load users. Please try again.'
    users.value = []
  } finally {
    loading.value = false
  }
}

async function toggleUserStatus(userId, activate) {
  togglingId.value = userId

  try {
    const endpoint = activate ? 'activate' : 'deactivate'
    await api.post(`/api/v1/admin/users/${userId}/${endpoint}`)

    // Update user in list
    const user = users.value.find(u => u.id === userId)
    if (user) {
      user.is_active = activate
    }

  } catch (error) {
    console.error('Toggle user status error:', error)
    alert(error.response?.data?.detail || 'Failed to update user status')
  } finally {
    togglingId.value = null
  }
}

async function deleteUser(userId) {
  if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
    return
  }

  deletingId.value = userId

  try {
    console.log('Deleting user:', userId)
    await api.delete(`/api/v1/admin/users/${userId}`)
    console.log('User deleted successfully')

    // Remove from list
    users.value = users.value.filter(u => u.id !== userId)

  } catch (error) {
    console.error('Delete user error:', error)
    console.error('Error details:', {
      status: error.response?.status,
      data: error.response?.data
    })

    const errorMessage = error.response?.data?.detail || 'Failed to delete user'
    alert(errorMessage)
  } finally {
    deletingId.value = null
  }
}

onMounted(() => {
  console.log('AdminUsers component mounted')
  load()
})
</script>

<style scoped>
.input:focus {
  outline: none;
  border-color: rgba(124, 92, 255, 0.5);
  box-shadow: 0 0 0 3px rgba(124, 92, 255, 0.1);
}

.input:disabled, .btn:disabled, .btn-ghost:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}

table {
  border-collapse: collapse;
}

tbody tr:hover {
  background: rgba(255, 255, 255, 0.03);
}
</style>