<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'

const getToken = () => localStorage.getItem('access_token') || localStorage.getItem('token')

const apiFetch = async (endpoint: string, options: RequestInit = {}) => {
  const token = getToken()
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...(options.headers as Record<string, string>),
    },
  })
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw { status: response.status, data: errorData }
  }
  return response.json()
}

const isLoading = ref(true)
const users = ref<any[]>([])
const searchQuery = ref('')
const statusFilter = ref('all')
const kycFilter = ref('all')
const currentPage = ref(1)
const perPage = ref(10)

const showModal = ref(false)
const modalMode = ref<'add' | 'edit' | 'view'>('view')
const currentUser = ref<any>({})
const isSaving = ref(false)
const saveErrors = ref<Record<string, string>>({})
const saveErrorMessage = ref('')

const showDeleteDialog = ref(false)
const userToDelete = ref<any>(null)

const fetchUsers = async () => {
  isLoading.value = true
  try {
    const data = await apiFetch('/users/')
    const results = data.results || data.data || data || []
    users.value = Array.isArray(results) ? results : []
  }
  catch (err) {
    console.error('Erreur chargement:', err)
    users.value = []
  }
  finally {
    isLoading.value = false
  }
}

const totalUsers = computed(() => users.value.length)
const activeCount = computed(() => users.value.filter(u => u.is_active).length)
const inactiveCount = computed(() => users.value.filter(u => !u.is_active).length)
const verifiedCount = computed(() => users.value.filter(u => u.kv === 1).length)
const emailVerifiedCount = computed(() => users.value.filter(u => u.ev === true).length)
const mobileVerifiedCount = computed(() => users.value.filter(u => u.sv === true).length)

const kpiCards = computed(() => [
  { title: 'Total utilisateurs', value: totalUsers.value, icon: 'tabler-users', color: 'primary' },
  { title: 'Actifs', value: activeCount.value, icon: 'tabler-user-check', color: 'success' },
  { title: 'Inactifs', value: inactiveCount.value, icon: 'tabler-user-off', color: 'error' },
  { title: 'Vérifiés (KYC)', value: verifiedCount.value, icon: 'tabler-shield-check', color: 'info' },
])

const filteredUsers = computed(() => {
  let result = [...users.value]
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(u =>
      u.email?.toLowerCase().includes(q)
      || u.full_name?.toLowerCase().includes(q)
      || u.username?.toLowerCase().includes(q)
      || u.firstname?.toLowerCase().includes(q)
      || u.lastname?.toLowerCase().includes(q)
      || u.mobile?.toLowerCase().includes(q),
    )
  }
  if (statusFilter.value !== 'all')
    result = result.filter(u => String(u.is_active) === statusFilter.value)
  if (kycFilter.value !== 'all') {
    if (kycFilter.value === '1') result = result.filter(u => u.kv === 1)
    else if (kycFilter.value === '0') result = result.filter(u => u.kv === 0)
    else if (kycFilter.value === '2') result = result.filter(u => u.kv === 2)
  }
  return result
})

const paginatedUsers = computed(() => {
  const start = (currentPage.value - 1) * perPage.value
  return filteredUsers.value.slice(start, start + perPage.value)
})
const totalPages = computed(() => Math.ceil(filteredUsers.value.length / perPage.value) || 1)

function formatDate(dateString: string | null): string {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })
}

function getUserName(user: any): string {
  if (user.full_name) return user.full_name
  if (user.firstname || user.lastname) return `${user.firstname || ''} ${user.lastname || ''}`.trim()
  return user.username || user.email || '-'
}

function getUserInitials(user: any): string {
  const name = getUserName(user)
  if (name === '-') return '?'
  const parts = name.split(' ')
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return name[0].toUpperCase()
}

function getKycConfig(user: any) {
  if (user.kv === 1) return { label: 'Vérifié', color: 'success', icon: 'tabler-shield-check' }
  if (user.kv === 2) return { label: 'En attente', color: 'warning', icon: 'tabler-clock' }
  return { label: 'Non vérifié', color: 'error', icon: 'tabler-shield-x' }
}

// ─── Parse errors Django ───
// Gère: { status, message, errors: { field: ["msg"] } }
// ET:   { field: ["msg"] }
// ET:   { field: "msg" }
function parseErrors(data: any): Record<string, string> {
  const mapped: Record<string, string> = {}
  const errorsObj = data?.errors || data
  if (!errorsObj || typeof errorsObj !== 'object') return mapped
  for (const [field, msg] of Object.entries(errorsObj)) {
    if (field === 'status' || field === 'message') continue
    if (Array.isArray(msg)) {
      mapped[field] = msg.map((m: any) => {
        if (typeof m === 'string') return m
        if (typeof m === 'object' && m !== null) return Object.values(m).join(', ')
        return String(m)
      }).join(', ')
    }
    else if (typeof msg === 'object' && msg !== null) {
      mapped[field] = Object.entries(msg as Record<string, any>)
        .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
        .join(' | ')
    }
    else {
      mapped[field] = String(msg)
    }
  }
  return mapped
}

const openAddModal = () => {
  modalMode.value = 'add'
  saveErrors.value = {}
  saveErrorMessage.value = ''
  currentUser.value = {
    email: '', firstname: '', lastname: '', username: '',
    mobile: '', password: '', password_confirm: '',
    country_name: '', city: '', is_active: true,
  }
  showModal.value = true
}

const viewUser = (user: any) => {
  modalMode.value = 'view'
  currentUser.value = { ...user }
  showModal.value = true
}

const editUser = (user: any) => {
  modalMode.value = 'edit'
  saveErrors.value = {}
  saveErrorMessage.value = ''
  currentUser.value = { ...user }
  showModal.value = true
}

const saveUser = async () => {
  isSaving.value = true
  saveErrors.value = {}
  saveErrorMessage.value = ''
  try {
    if (modalMode.value === 'add') {
      await apiFetch('/auth/register/', {
        method: 'POST',
        body: JSON.stringify({
          email: currentUser.value.email,
          firstname: currentUser.value.firstname,
          lastname: currentUser.value.lastname,
          username: currentUser.value.username,
          mobile: currentUser.value.mobile,
          password: currentUser.value.password,
          password_confirm: currentUser.value.password_confirm,
          country_name: currentUser.value.country_name,
          city: currentUser.value.city,
          is_active: currentUser.value.is_active,
        }),
      })
    }
    else {
      await apiFetch(`/users/${currentUser.value.id}/`, {
        method: 'PATCH',
        body: JSON.stringify(currentUser.value),
      })
    }
    showModal.value = false
    await fetchUsers()
  }
  catch (err: any) {
    console.error('Erreur complète:', JSON.stringify(err))
    if (err?.data) {
      saveErrorMessage.value = err.data?.message || 'Erreur de validation.'
      saveErrors.value = parseErrors(err.data)
    }
    else {
      saveErrorMessage.value = 'Une erreur est survenue. Veuillez réessayer.'
    }
  }
  finally {
    isSaving.value = false
  }
}

const confirmDelete = (user: any) => { userToDelete.value = user; showDeleteDialog.value = true }

const deleteUser = async () => {
  if (!userToDelete.value) return
  try {
    await apiFetch(`/users/${userToDelete.value.id}/`, { method: 'DELETE' })
    showDeleteDialog.value = false
    userToDelete.value = null
    await fetchUsers()
  }
  catch (err) { console.error('Erreur suppression:', err) }
}

const banUser = async (user: any) => {
  if (confirm(`Bannir l'utilisateur "${user.email}" ?`)) {
    try {
      await apiFetch(`/users/${user.id}/ban/`, { method: 'POST', body: JSON.stringify({ reason: 'Banni par admin' }) })
      await fetchUsers()
    }
    catch (err) { console.error('Erreur ban:', err) }
  }
}

const unbanUser = async (user: any) => {
  if (confirm(`Débannir l'utilisateur "${user.email}" ?`)) {
    try {
      await apiFetch(`/users/${user.id}/unban/`, { method: 'POST' })
      await fetchUsers()
    }
    catch (err) { console.error('Erreur unban:', err) }
  }
}

const resetFilters = () => {
  searchQuery.value = ''
  statusFilter.value = 'all'
  kycFilter.value = 'all'
  currentPage.value = 1
}

onMounted(() => { fetchUsers() })
</script>

<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h4 class="text-h4 font-weight-bold">Gestion des Utilisateurs</h4>
        <p class="text-body-1 text-medium-emphasis mt-1">Gérez tous les comptes utilisateurs de la plateforme</p>
      </div>
      <VBtn color="primary" prepend-icon="tabler-user-plus" @click="openAddModal">Ajouter Un Utilisateur</VBtn>
    </div>

    <VRow class="mb-6">
      <VCol v-for="(kpi, i) in kpiCards" :key="i" cols="12" sm="6" lg="3">
        <VCard>
          <VCardText class="d-flex align-center gap-3">
            <VAvatar :color="kpi.color" variant="tonal" size="44" rounded>
              <VIcon :icon="kpi.icon" size="24" />
            </VAvatar>
            <div>
              <p class="text-caption text-medium-emphasis mb-0">{{ kpi.title }}</p>
              <h5 class="text-h6 font-weight-bold">{{ kpi.value }}</h5>
            </div>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <VCard class="mb-6">
      <VCardText class="d-flex align-center gap-6 flex-wrap">
        <div class="d-flex align-center gap-2">
          <VIcon icon="tabler-mail-check" size="18" color="success" />
          <span class="text-body-2">Email vérifié: <strong>{{ emailVerifiedCount }}</strong></span>
        </div>
        <VDivider vertical class="my-1" />
        <div class="d-flex align-center gap-2">
          <VIcon icon="tabler-phone-check" size="18" color="primary" />
          <span class="text-body-2">Mobile vérifié: <strong>{{ mobileVerifiedCount }}</strong></span>
        </div>
        <VDivider vertical class="my-1" />
        <div class="d-flex align-center gap-2">
          <VIcon icon="tabler-shield-check" size="18" color="info" />
          <span class="text-body-2">KYC vérifié: <strong>{{ verifiedCount }}</strong></span>
        </div>
      </VCardText>
    </VCard>

    <VCard class="mb-6">
      <VCardText>
        <VRow>
          <VCol cols="12" md="4">
            <VTextField v-model="searchQuery" placeholder="Rechercher par nom, email, mobile..." prepend-inner-icon="tabler-search" density="compact" clearable @update:model-value="currentPage = 1" />
          </VCol>
          <VCol cols="12" sm="6" md="3">
            <VSelect v-model="statusFilter" :items="[{ title: 'Tous les statuts', value: 'all' }, { title: 'Actifs', value: 'true' }, { title: 'Inactifs', value: 'false' }]" density="compact" />
          </VCol>
          <VCol cols="12" sm="6" md="3">
            <VSelect v-model="kycFilter" :items="[{ title: 'Tous KYC', value: 'all' }, { title: 'Vérifiés', value: '1' }, { title: 'Non vérifiés', value: '0' }, { title: 'En attente', value: '2' }]" density="compact" />
          </VCol>
          <VCol cols="12" sm="6" md="2">
            <VBtn variant="tonal" color="secondary" block @click="resetFilters">
              <VIcon icon="tabler-refresh" class="me-1" />Réinitialiser
            </VBtn>
          </VCol>
        </VRow>
      </VCardText>
    </VCard>

    <div v-if="isLoading" class="d-flex flex-column align-center justify-center py-16">
      <VProgressCircular indeterminate color="primary" size="48" />
      <p class="text-body-1 text-medium-emphasis mt-4">Chargement des utilisateurs...</p>
    </div>

    <VCard v-else>
      <VTable class="text-no-wrap">
        <thead>
          <tr>
            <th>Utilisateur</th>
            <th>Email / Mobile</th>
            <th>Statut</th>
            <th>KYC</th>
            <th>Email / Mobile vérifié</th>
            <th>Solde</th>
            <th>Inscrit le</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in paginatedUsers" :key="user.id">
            <td>
              <div class="d-flex align-center gap-3 py-2">
                <VAvatar color="primary" variant="tonal" size="38">
                  <VImg v-if="user.profile_image" :src="user.profile_image" />
                  <span v-else class="text-body-1 font-weight-medium">{{ getUserInitials(user) }}</span>
                </VAvatar>
                <div>
                  <p class="text-body-1 font-weight-medium mb-0">{{ getUserName(user) }}</p>
                  <p class="text-caption text-medium-emphasis mb-0">@{{ user.username || 'N/A' }}</p>
                </div>
              </div>
            </td>
            <td>
              <p class="text-body-2 mb-0">{{ user.email }}</p>
              <p class="text-caption text-medium-emphasis mb-0">{{ user.mobile || '-' }}</p>
            </td>
            <td>
              <VChip :color="user.is_active ? 'success' : 'error'" size="small" variant="tonal">
                <VIcon :icon="user.is_active ? 'tabler-check' : 'tabler-ban'" size="14" start />
                {{ user.is_active ? 'Actif' : 'Banni' }}
              </VChip>
            </td>
            <td>
              <VChip :color="getKycConfig(user).color" size="small" variant="tonal">
                <VIcon :icon="getKycConfig(user).icon" size="14" start />
                {{ getKycConfig(user).label }}
              </VChip>
            </td>
            <td>
              <div class="d-flex gap-1">
                <VChip :color="user.ev ? 'success' : 'default'" size="x-small" variant="tonal">
                  <VIcon icon="tabler-mail" size="12" start />{{ user.ev ? '✓' : '✗' }}
                </VChip>
                <VChip :color="user.sv ? 'success' : 'default'" size="x-small" variant="tonal">
                  <VIcon icon="tabler-phone" size="12" start />{{ user.sv ? '✓' : '✗' }}
                </VChip>
              </div>
            </td>
            <td>
              <p class="text-body-2 font-weight-medium mb-0">{{ Number.parseFloat(user.balance || 0).toFixed(3) }} DT</p>
            </td>
            <td>
              <p class="text-body-2 mb-0">{{ formatDate(user.created_at) }}</p>
            </td>
            <td>
              <div class="d-flex gap-1">
                <VBtn icon variant="text" size="small" color="primary" @click="viewUser(user)">
                  <VIcon icon="tabler-eye" size="18" /><VTooltip activator="parent">Voir</VTooltip>
                </VBtn>
                <VBtn icon variant="text" size="small" color="success" @click="editUser(user)">
                  <VIcon icon="tabler-pencil" size="18" /><VTooltip activator="parent">Modifier</VTooltip>
                </VBtn>
                <VBtn v-if="user.is_active" icon variant="text" size="small" color="warning" @click="banUser(user)">
                  <VIcon icon="tabler-ban" size="18" /><VTooltip activator="parent">Bannir</VTooltip>
                </VBtn>
                <VBtn v-else icon variant="text" size="small" color="success" @click="unbanUser(user)">
                  <VIcon icon="tabler-user-check" size="18" /><VTooltip activator="parent">Débannir</VTooltip>
                </VBtn>
                <VBtn icon variant="text" size="small" color="error" @click="confirmDelete(user)">
                  <VIcon icon="tabler-trash" size="18" /><VTooltip activator="parent">Supprimer</VTooltip>
                </VBtn>
              </div>
            </td>
          </tr>
          <tr v-if="paginatedUsers.length === 0">
            <td colspan="8" class="text-center py-8">
              <VIcon icon="tabler-users-minus" size="48" color="disabled" class="mb-2" />
              <p class="text-body-1 text-medium-emphasis">Aucun utilisateur trouvé</p>
            </td>
          </tr>
        </tbody>
      </VTable>
      <VDivider />
      <VCardText class="d-flex justify-space-between align-center flex-wrap">
        <p class="text-body-2 text-medium-emphasis mb-0">
          Affichage {{ Math.min((currentPage - 1) * perPage + 1, filteredUsers.length) }}
          à {{ Math.min(currentPage * perPage, filteredUsers.length) }}
          sur {{ filteredUsers.length }} utilisateurs
        </p>
        <div class="d-flex align-center gap-2">
          <VBtn variant="outlined" size="small" :disabled="currentPage <= 1" @click="currentPage--">Précédent</VBtn>
          <VChip size="small" color="primary" variant="tonal">{{ currentPage }} / {{ totalPages }}</VChip>
          <VBtn variant="outlined" size="small" :disabled="currentPage >= totalPages" @click="currentPage++">Suivant</VBtn>
        </div>
      </VCardText>
    </VCard>

    <!-- ═══════ MODAL ═══════ -->
    <VDialog v-model="showModal" max-width="600" persistent>
      <VCard>
        <VCardTitle class="d-flex justify-space-between align-center pa-6">
          <span class="text-h6 font-weight-bold">
            {{ modalMode === 'add' ? 'Ajouter un utilisateur' : modalMode === 'edit' ? "Modifier l'utilisateur" : "Détails de l'utilisateur" }}
          </span>
          <VBtn icon variant="text" size="small" @click="showModal = false">
            <VIcon icon="tabler-x" />
          </VBtn>
        </VCardTitle>
        <VDivider />
        <VCardText class="pa-6">

          <!-- Bloc erreurs -->
          <VAlert
            v-if="saveErrorMessage || Object.keys(saveErrors).length > 0"
            type="error"
            variant="tonal"
            class="mb-4"
            closable
            @click:close="saveErrorMessage = ''; saveErrors = {}"
          >
            <p v-if="saveErrorMessage" class="mb-1 font-weight-medium">{{ saveErrorMessage }}</p>
            <ul v-if="Object.keys(saveErrors).length > 0" class="mb-0 ps-4">
              <li v-for="(msg, field) in saveErrors" :key="field">
                <strong>{{ field }}</strong> : {{ msg }}
              </li>
            </ul>
          </VAlert>

          <!-- View Mode -->
          <div v-if="modalMode === 'view'">
            <div class="d-flex align-center gap-4 mb-6">
              <VAvatar color="primary" variant="tonal" size="64">
                <VImg v-if="currentUser.profile_image" :src="currentUser.profile_image" />
                <span v-else class="text-h5 font-weight-medium">{{ getUserInitials(currentUser) }}</span>
              </VAvatar>
              <div>
                <h5 class="text-h6 font-weight-bold">{{ getUserName(currentUser) }}</h5>
                <p class="text-body-2 text-medium-emphasis mb-1">{{ currentUser.email }}</p>
                <div class="d-flex gap-2">
                  <VChip :color="currentUser.is_active ? 'success' : 'error'" size="x-small" variant="tonal">
                    {{ currentUser.is_active ? 'Actif' : 'Banni' }}
                  </VChip>
                  <VChip :color="getKycConfig(currentUser).color" size="x-small" variant="tonal">
                    {{ getKycConfig(currentUser).label }}
                  </VChip>
                  <VChip v-if="currentUser.ts" color="primary" size="x-small" variant="tonal">2FA activé</VChip>
                </div>
              </div>
            </div>
            <VRow>
              <VCol cols="6"><p class="text-caption text-medium-emphasis mb-1">Prénom</p><p class="text-body-2 font-weight-medium">{{ currentUser.firstname || '-' }}</p></VCol>
              <VCol cols="6"><p class="text-caption text-medium-emphasis mb-1">Nom</p><p class="text-body-2 font-weight-medium">{{ currentUser.lastname || '-' }}</p></VCol>
              <VCol cols="6"><p class="text-caption text-medium-emphasis mb-1">Username</p><p class="text-body-2 font-weight-medium">{{ currentUser.username || '-' }}</p></VCol>
              <VCol cols="6"><p class="text-caption text-medium-emphasis mb-1">Mobile</p><p class="text-body-2 font-weight-medium">{{ currentUser.dial_code || '' }} {{ currentUser.mobile || '-' }}</p></VCol>
              <VCol cols="6"><p class="text-caption text-medium-emphasis mb-1">Pays</p><p class="text-body-2 font-weight-medium">{{ currentUser.country_name || '-' }}</p></VCol>
              <VCol cols="6"><p class="text-caption text-medium-emphasis mb-1">Ville</p><p class="text-body-2 font-weight-medium">{{ currentUser.city || '-' }}</p></VCol>
              <VCol cols="6"><p class="text-caption text-medium-emphasis mb-1">Solde</p><p class="text-body-2 font-weight-medium">{{ Number.parseFloat(currentUser.balance || 0).toFixed(3) }} DT</p></VCol>
              <VCol cols="6"><p class="text-caption text-medium-emphasis mb-1">Inscrit le</p><p class="text-body-2 font-weight-medium">{{ formatDate(currentUser.created_at) }}</p></VCol>
              <VCol cols="6">
                <p class="text-caption text-medium-emphasis mb-1">Email vérifié</p>
                <VChip :color="currentUser.ev ? 'success' : 'error'" size="x-small" variant="tonal">{{ currentUser.ev ? 'Oui' : 'Non' }}</VChip>
              </VCol>
              <VCol cols="6">
                <p class="text-caption text-medium-emphasis mb-1">Mobile vérifié</p>
                <VChip :color="currentUser.sv ? 'success' : 'error'" size="x-small" variant="tonal">{{ currentUser.sv ? 'Oui' : 'Non' }}</VChip>
              </VCol>
              <VCol v-if="currentUser.address" cols="12"><p class="text-caption text-medium-emphasis mb-1">Adresse</p><p class="text-body-2 font-weight-medium">{{ currentUser.address }}</p></VCol>
            </VRow>
          </div>

          <!-- Add / Edit Mode -->
          <VRow v-else>
            <VCol cols="12">
              <VTextField v-model="currentUser.email" label="Email *" type="email" prepend-inner-icon="tabler-mail" :error-messages="saveErrors.email" />
            </VCol>
            <VCol cols="12" md="6">
              <VTextField v-model="currentUser.firstname" label="Prénom" prepend-inner-icon="tabler-user" :error-messages="saveErrors.firstname" />
            </VCol>
            <VCol cols="12" md="6">
              <VTextField v-model="currentUser.lastname" label="Nom" prepend-inner-icon="tabler-user" :error-messages="saveErrors.lastname" />
            </VCol>
            <VCol cols="12" md="6">
              <VTextField v-model="currentUser.username" label="Username" prepend-inner-icon="tabler-at" :error-messages="saveErrors.username" />
            </VCol>
            <VCol cols="12" md="6">
              <VTextField v-model="currentUser.mobile" label="Mobile" prepend-inner-icon="tabler-phone" :error-messages="saveErrors.mobile" />
            </VCol>
            <VCol v-if="modalMode === 'add'" cols="12" md="6">
              <VTextField v-model="currentUser.password" label="Mot de passe *" type="password" prepend-inner-icon="tabler-lock" :error-messages="saveErrors.password" />
            </VCol>
            <VCol v-if="modalMode === 'add'" cols="12" md="6">
              <VTextField v-model="currentUser.password_confirm" label="Confirmer *" type="password" prepend-inner-icon="tabler-lock" :error-messages="saveErrors.password_confirm" />
            </VCol>
            <VCol cols="12" md="6">
              <VTextField v-model="currentUser.country_name" label="Pays" prepend-inner-icon="tabler-world" :error-messages="saveErrors.country_name" />
            </VCol>
            <VCol cols="12" md="6">
              <VTextField v-model="currentUser.city" label="Ville" prepend-inner-icon="tabler-map-pin" :error-messages="saveErrors.city" />
            </VCol>
            <VCol cols="12">
              <VSwitch v-model="currentUser.is_active" label="Compte actif" color="success" />
            </VCol>
          </VRow>
        </VCardText>
        <VDivider />
        <VCardActions class="pa-6">
          <VSpacer />
          <VBtn variant="outlined" color="secondary" @click="showModal = false">
            {{ modalMode === 'view' ? 'Fermer' : 'Annuler' }}
          </VBtn>
          <VBtn v-if="modalMode === 'view'" color="primary" prepend-icon="tabler-pencil" @click="modalMode = 'edit'">Modifier</VBtn>
          <VBtn v-else color="primary" :loading="isSaving" prepend-icon="tabler-device-floppy" @click="saveUser">Enregistrer</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- ═══════ DIALOG Suppression ═══════ -->
    <VDialog v-model="showDeleteDialog" max-width="450">
      <VCard>
        <VCardText class="text-center pa-8">
          <VAvatar color="error" variant="tonal" size="64" class="mb-4">
            <VIcon icon="tabler-alert-triangle" size="32" />
          </VAvatar>
          <h5 class="text-h6 font-weight-bold mb-2">Confirmer la suppression</h5>
          <p class="text-body-1 text-medium-emphasis mb-0">
            Êtes-vous sûr de vouloir supprimer<br><strong>{{ userToDelete?.email }}</strong> ?
          </p>
          <p class="text-body-2 text-error mt-2 mb-0">Cette action est irréversible.</p>
        </VCardText>
        <VDivider />
        <VCardActions class="pa-4 justify-center">
          <VBtn variant="outlined" color="secondary" @click="showDeleteDialog = false">Annuler</VBtn>
          <VBtn color="error" prepend-icon="tabler-trash" @click="deleteUser">Supprimer</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </div>
</template>