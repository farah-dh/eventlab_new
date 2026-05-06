<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

const router = useRouter()

// ─── Config API ───
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'

const getToken = () => {
  return localStorage.getItem('access_token') || localStorage.getItem('token')
}

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
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json()
}

// ─── State ───
const isLoading = ref(true)
const organizers = ref<any[]>([])
const searchQuery = ref('')
const statusFilter = ref('all')
const kycFilter = ref('all')
const currentPage = ref(1)
const perPage = ref(10)

// Modal (view only)
const showModal = ref(false)
const currentOrganizer = ref<any>({})

// Delete
const showDeleteDialog = ref(false)
const organizerToDelete = ref<any>(null)

// ─── Fetch Data ───
const fetchOrganizers = async () => {
  isLoading.value = true
  try {
    const data = await apiFetch('/organizers/')
    const allOrganizers = data.results || data.data || data || []
    organizers.value = Array.isArray(allOrganizers) ? allOrganizers : []
  }
  catch (err) {
    console.error('Erreur chargement organisateurs:', err)
    organizers.value = []
  }
  finally {
    isLoading.value = false
  }
}

// ─── Computed Stats ───
const totalOrganizers = computed(() => organizers.value.length)
const approvedCount = computed(() => organizers.value.filter(o => o.status === true).length)
const pendingCount = computed(() => totalOrganizers.value - approvedCount.value)
const verifiedCount = computed(() => organizers.value.filter(o => o.kv === 1).length)

// ─── KPI Cards ───
const kpiCards = computed(() => [
  { title: 'Total organisateurs', value: totalOrganizers.value, icon: 'tabler-user-star', color: 'primary' },
  { title: 'Actifs', value: approvedCount.value, icon: 'tabler-user-check', color: 'success' },
  { title: 'Inactifs', value: pendingCount.value, icon: 'tabler-clock', color: 'warning' },
  { title: 'Vérifiés (KYC)', value: verifiedCount.value, icon: 'tabler-shield-check', color: 'info' },
])

// ─── Filtering ───
const filteredOrganizers = computed(() => {
  let result = [...organizers.value]

  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(o =>
      o.email?.toLowerCase().includes(q)
      || o.organization_name?.toLowerCase().includes(q)
      || o.full_name?.toLowerCase().includes(q)
      || o.username?.toLowerCase().includes(q)
      || o.firstname?.toLowerCase().includes(q)
      || o.lastname?.toLowerCase().includes(q),
    )
  }

  if (statusFilter.value !== 'all') {
    if (statusFilter.value === 'approved')
      result = result.filter(o => o.status === true)
    else
      result = result.filter(o => o.status === false)
  }

  if (kycFilter.value !== 'all') {
    if (kycFilter.value === '1')
      result = result.filter(o => o.kv === 1)
    else
      result = result.filter(o => o.kv !== 1)
  }

  return result
})

const paginatedOrganizers = computed(() => {
  const start = (currentPage.value - 1) * perPage.value
  return filteredOrganizers.value.slice(start, start + perPage.value)
})

const totalPages = computed(() => Math.ceil(filteredOrganizers.value.length / perPage.value) || 1)

// ─── Helpers ───
function formatDate(dateString: string | null): string {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })
}

function getOrgName(org: any): string {
  if (org.organization_name) return org.organization_name
  if (org.full_name) return org.full_name
  if (org.firstname || org.lastname) return `${org.firstname || ''} ${org.lastname || ''}`.trim()
  return org.username || org.email || '-'
}

function getOrgInitials(org: any): string {
  const name = getOrgName(org)
  if (name === '-') return '?'
  const parts = name.split(' ')
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return name[0].toUpperCase()
}

function getStatusConfig(org: any) {
  if (org.status === true) return { label: 'Actif', color: 'success', icon: 'tabler-check' }
  return { label: 'Banni', color: 'error', icon: 'tabler-ban' }
}

function getKycConfig(org: any) {
  const kv = org.kv
  if (kv === 1) return { label: 'Vérifié', color: 'success', icon: 'tabler-shield-check' }
  if (kv === 2) return { label: 'En attente', color: 'warning', icon: 'tabler-clock' }
  return { label: 'Non vérifié', color: 'error', icon: 'tabler-shield-x' }
}

// ─── CRUD Actions ───
const viewOrganizer = (org: any) => {
  currentOrganizer.value = { ...org }
  showModal.value = true
}

const goToAddPage = () => {
  router.push('/admin/organizers/add')
}

const goToEditPage = (org: any) => {
  router.push(`/admin/organizers/${org.id}/edit`)
}

const approveKyc = async (org: any) => {
  if (confirm(`Approuver le KYC de ${getOrgName(org)} ?`)) {
    try {
      await apiFetch(`/organizers/${org.id}/approve_kyc/`, { method: 'POST' })
      await fetchOrganizers()
    }
    catch (err) { console.error('Erreur approbation KYC:', err) }
  }
}

const banOrganizer = async (org: any) => {
  if (confirm(`Bannir ${getOrgName(org)} ?`)) {
    try {
      await apiFetch(`/organizers/${org.id}/ban/`, { method: 'POST', body: JSON.stringify({ reason: 'Banni par admin' }) })
      await fetchOrganizers()
    }
    catch (err) { console.error('Erreur ban:', err) }
  }
}

const confirmDelete = (org: any) => {
  organizerToDelete.value = org
  showDeleteDialog.value = true
}

const deleteOrganizer = async () => {
  if (!organizerToDelete.value) return
  try {
    await apiFetch(`/organizers/${organizerToDelete.value.id}/`, { method: 'DELETE' })
    showDeleteDialog.value = false
    organizerToDelete.value = null
    await fetchOrganizers()
  }
  catch (err) { console.error('Erreur suppression:', err) }
}

const resetFilters = () => {
  searchQuery.value = ''
  statusFilter.value = 'all'
  kycFilter.value = 'all'
  currentPage.value = 1
}

// ─── Init ───
onMounted(() => { fetchOrganizers() })
</script>

<template>
  <div>
    <!-- Page Header -->
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h4 class="text-h4 font-weight-bold">
          Gestion des Organisateurs
        </h4>
        <p class="text-body-1 text-medium-emphasis mt-1">
          Gérez les comptes organisateurs de la plateforme
        </p>
      </div>
      <VBtn color="primary" prepend-icon="tabler-user-plus" @click="goToAddPage">
        Ajouter un organisateur
      </VBtn>
    </div>

    <!-- KPI Cards -->
    <VRow class="mb-6">
      <VCol v-for="(kpi, i) in kpiCards" :key="i" cols="12" sm="6" lg="3">
        <VCard>
          <VCardText class="d-flex align-center gap-3">
            <VAvatar :color="kpi.color" variant="tonal" size="44" rounded>
              <VIcon :icon="kpi.icon" size="24" />
            </VAvatar>
            <div>
              <p class="text-caption text-medium-emphasis mb-0">
                {{ kpi.title }}
              </p>
              <h5 class="text-h6 font-weight-bold">
                {{ kpi.value }}
              </h5>
            </div>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- Filters -->
    <VCard class="mb-6">
      <VCardText>
        <VRow>
          <VCol cols="12" md="4">
            <VTextField
              v-model="searchQuery"
              placeholder="Rechercher par nom, email..."
              prepend-inner-icon="tabler-search"
              density="compact"
              clearable
              @update:model-value="currentPage = 1"
            />
          </VCol>
          <VCol cols="12" sm="6" md="3">
            <VSelect
              v-model="statusFilter"
              :items="[
                { title: 'Tous les statuts', value: 'all' },
                { title: 'Actifs', value: 'approved' },
                { title: 'Bannis', value: 'pending' },
              ]"
              density="compact"
            />
          </VCol>
          <VCol cols="12" sm="6" md="3">
            <VSelect
              v-model="kycFilter"
              :items="[
                { title: 'Tous KYC', value: 'all' },
                { title: 'Vérifiés', value: '1' },
                { title: 'Non vérifiés', value: '0' },
              ]"
              density="compact"
            />
          </VCol>
          <VCol cols="12" sm="6" md="2">
            <VBtn variant="tonal" color="secondary" block @click="resetFilters">
              <VIcon icon="tabler-refresh" class="me-1" />
              Réinitialiser
            </VBtn>
          </VCol>
        </VRow>
      </VCardText>
    </VCard>

    <!-- Loading -->
    <div v-if="isLoading" class="d-flex flex-column align-center justify-center py-16">
      <VProgressCircular indeterminate color="primary" size="48" />
      <p class="text-body-1 text-medium-emphasis mt-4">
        Chargement des organisateurs...
      </p>
    </div>

    <!-- Organizers Table -->
    <VCard v-else>
      <VTable class="text-no-wrap">
        <thead>
          <tr>
            <th>Organisateur</th>
            <th>Email</th>
            <th>Téléphone</th>
            <th>Statut</th>
            <th>KYC</th>
            <th>Followers</th>
            <th>Inscrit le</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="org in paginatedOrganizers" :key="org.id">
            <td>
              <div class="d-flex align-center gap-3 py-2">
                <VAvatar color="primary" variant="tonal" size="38">
                  <VImg v-if="org.profile_image" :src="org.profile_image" />
                  <span v-else class="text-body-1 font-weight-medium">{{ getOrgInitials(org) }}</span>
                </VAvatar>
                <div>
                  <p class="text-body-1 font-weight-medium mb-0">
                    {{ getOrgName(org) }}
                  </p>
                  <p class="text-caption text-medium-emphasis mb-0">
                    @{{ org.username }}
                  </p>
                </div>
              </div>
            </td>
            <td>
              <p class="text-body-2 mb-0">
                {{ org.email }}
              </p>
            </td>
            <td>
              <p class="text-body-2 mb-0">
                {{ org.mobile || '-' }}
              </p>
            </td>
            <td>
              <VChip :color="getStatusConfig(org).color" size="small" variant="tonal">
                <VIcon :icon="getStatusConfig(org).icon" size="14" start />
                {{ getStatusConfig(org).label }}
              </VChip>
            </td>
            <td>
              <VChip :color="getKycConfig(org).color" size="small" variant="tonal">
                <VIcon :icon="getKycConfig(org).icon" size="14" start />
                {{ getKycConfig(org).label }}
              </VChip>
            </td>
            <td>
              <VChip color="primary" variant="tonal" size="small">
                {{ org.followers_count || 0 }}
              </VChip>
            </td>
            <td>
              <p class="text-body-2 mb-0">
                {{ formatDate(org.created_at) }}
              </p>
            </td>
            <td>
              <div class="d-flex gap-1">
                <VBtn icon variant="text" size="small" color="primary" @click="viewOrganizer(org)">
                  <VIcon icon="tabler-eye" size="18" />
                  <VTooltip activator="parent">Voir</VTooltip>
                </VBtn>
                <VBtn icon variant="text" size="small" color="success" @click="goToEditPage(org)">
                  <VIcon icon="tabler-pencil" size="18" />
                  <VTooltip activator="parent">Modifier</VTooltip>
                </VBtn>
                <VBtn v-if="org.kv !== 1" icon variant="text" size="small" color="warning" @click="approveKyc(org)">
                  <VIcon icon="tabler-shield-check" size="18" />
                  <VTooltip activator="parent">Approuver KYC</VTooltip>
                </VBtn>
                <VBtn v-if="org.status" icon variant="text" size="small" color="orange" @click="banOrganizer(org)">
                  <VIcon icon="tabler-ban" size="18" />
                  <VTooltip activator="parent">Bannir</VTooltip>
                </VBtn>
                <VBtn icon variant="text" size="small" color="error" @click="confirmDelete(org)">
                  <VIcon icon="tabler-trash" size="18" />
                  <VTooltip activator="parent">Supprimer</VTooltip>
                </VBtn>
              </div>
            </td>
          </tr>
          <tr v-if="paginatedOrganizers.length === 0">
            <td colspan="8" class="text-center py-8">
              <VIcon icon="tabler-users-minus" size="48" color="disabled" class="mb-2" />
              <p class="text-body-1 text-medium-emphasis">
                Aucun organisateur trouvé
              </p>
            </td>
          </tr>
        </tbody>
      </VTable>

      <VDivider />

      <VCardText class="d-flex justify-space-between align-center flex-wrap">
        <p class="text-body-2 text-medium-emphasis mb-0">
          Affichage {{ Math.min((currentPage - 1) * perPage + 1, filteredOrganizers.length) }}
          à {{ Math.min(currentPage * perPage, filteredOrganizers.length) }}
          sur {{ filteredOrganizers.length }} organisateurs
        </p>
        <div class="d-flex align-center gap-2">
          <VBtn variant="outlined" size="small" :disabled="currentPage <= 1" @click="currentPage--">
            Précédent
          </VBtn>
          <VChip size="small" color="primary" variant="tonal">
            {{ currentPage }} / {{ totalPages }}
          </VChip>
          <VBtn variant="outlined" size="small" :disabled="currentPage >= totalPages" @click="currentPage++">
            Suivant
          </VBtn>
        </div>
      </VCardText>
    </VCard>

    <!-- ═══════ MODAL: Voir les détails ═══════ -->
    <VDialog v-model="showModal" max-width="600">
      <VCard>
        <VCardTitle class="d-flex justify-space-between align-center pa-6">
          <span class="text-h6 font-weight-bold">
            Détails de l'organisateur
          </span>
          <VBtn icon variant="text" size="small" @click="showModal = false">
            <VIcon icon="tabler-x" />
          </VBtn>
        </VCardTitle>

        <VDivider />

        <VCardText class="pa-6">
          <div class="d-flex align-center gap-4 mb-6">
            <VAvatar color="primary" variant="tonal" size="64">
              <span class="text-h5 font-weight-medium">{{ getOrgInitials(currentOrganizer) }}</span>
            </VAvatar>
            <div>
              <h5 class="text-h6 font-weight-bold">
                {{ getOrgName(currentOrganizer) }}
              </h5>
              <p class="text-body-2 text-medium-emphasis mb-1">
                {{ currentOrganizer.email }}
              </p>
              <div class="d-flex gap-2">
                <VChip :color="getStatusConfig(currentOrganizer).color" size="x-small" variant="tonal">
                  {{ getStatusConfig(currentOrganizer).label }}
                </VChip>
                <VChip :color="getKycConfig(currentOrganizer).color" size="x-small" variant="tonal">
                  {{ getKycConfig(currentOrganizer).label }}
                </VChip>
              </div>
            </div>
          </div>

          <VRow>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Username</p>
              <p class="text-body-2 font-weight-medium">{{ currentOrganizer.username || '-' }}</p>
            </VCol>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Téléphone</p>
              <p class="text-body-2 font-weight-medium">{{ currentOrganizer.mobile || '-' }}</p>
            </VCol>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Ville</p>
              <p class="text-body-2 font-weight-medium">{{ currentOrganizer.city || '-' }}</p>
            </VCol>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Pays</p>
              <p class="text-body-2 font-weight-medium">{{ currentOrganizer.country_name || '-' }}</p>
            </VCol>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Followers</p>
              <p class="text-body-2 font-weight-medium">{{ currentOrganizer.followers_count || 0 }}</p>
            </VCol>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Solde</p>
              <p class="text-body-2 font-weight-medium">{{ Number.parseFloat(currentOrganizer.balance || 0).toFixed(3) }} DT</p>
            </VCol>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Inscrit le</p>
              <p class="text-body-2 font-weight-medium">{{ formatDate(currentOrganizer.created_at) }}</p>
            </VCol>
            <VCol cols="12">
              <p class="text-caption text-medium-emphasis mb-1">Description</p>
              <p class="text-body-2 font-weight-medium">{{ currentOrganizer.short_description || '-' }}</p>
            </VCol>
          </VRow>
        </VCardText>

        <VDivider />

        <VCardActions class="pa-6">
          <VSpacer />
          <VBtn variant="outlined" color="secondary" @click="showModal = false">
            Fermer
          </VBtn>
          <VBtn
            color="primary"
            prepend-icon="tabler-pencil"
            @click="showModal = false; goToEditPage(currentOrganizer)"
          >
            Modifier
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- ═══════ DIALOG: Confirmation suppression ═══════ -->
    <VDialog v-model="showDeleteDialog" max-width="450">
      <VCard>
        <VCardText class="text-center pa-8">
          <VAvatar color="error" variant="tonal" size="64" class="mb-4">
            <VIcon icon="tabler-alert-triangle" size="32" />
          </VAvatar>
          <h5 class="text-h6 font-weight-bold mb-2">
            Confirmer la suppression
          </h5>
          <p class="text-body-1 text-medium-emphasis mb-0">
            Êtes-vous sûr de vouloir supprimer<br>
            <strong>{{ organizerToDelete ? getOrgName(organizerToDelete) : '' }}</strong> ?
          </p>
          <p class="text-body-2 text-error mt-2 mb-0">
            Cette action est irréversible.
          </p>
        </VCardText>
        <VDivider />
        <VCardActions class="pa-4 justify-center">
          <VBtn variant="outlined" color="secondary" @click="showDeleteDialog = false">
            Annuler
          </VBtn>
          <VBtn color="error" prepend-icon="tabler-trash" @click="deleteOrganizer">
            Supprimer
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </div>
</template>