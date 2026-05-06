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
const events = ref<any[]>([])
const categories = ref<any[]>([])
const locations = ref<any[]>([])
const searchQuery = ref('')
const statusFilter = ref('all')
const featuredFilter = ref('all')
const categoryFilter = ref('all')
const locationFilter = ref('all')
const typeFilter = ref('all')
const currentPage = ref(1)
const perPage = ref(10)

// Modal
const showViewModal = ref(false)
const selectedEvent = ref<any>(null)

// Delete
const showDeleteDialog = ref(false)
const eventToDelete = ref<any>(null)

// ─── Fetch Data ───
const fetchEvents = async () => {
  isLoading.value = true
  try {
    const data = await apiFetch('/events/')
    const results = data.results || data.data || data || []
    events.value = Array.isArray(results) ? results : []
  }
  catch (err) {
    console.error('Erreur chargement événements:', err)
    events.value = []
  }
  finally {
    isLoading.value = false
  }
}

const fetchCategories = async () => {
  try {
    const data = await apiFetch('/events/categories/')
    categories.value = data.results || data || []
  }
  catch (err) { console.error(err) }
}

const fetchLocations = async () => {
  try {
    const data = await apiFetch('/events/locations/')
    locations.value = data.results || data || []
  }
  catch (err) { console.error(err) }
}

// ─── Computed Stats ───
const totalEvents = computed(() => events.value.length)
const activeCount = computed(() => events.value.filter(e => e.status === true).length)
const inactiveCount = computed(() => events.value.filter(e => e.status === false).length)
const featuredCount = computed(() => events.value.filter(e => e.is_featured === true).length)
const totalSeatsBooked = computed(() => events.value.reduce((sum, e) => sum + (e.seats_booked || 0), 0))

// ─── KPI Cards ───
const kpiCards = computed(() => [
  { title: 'Total événements', value: totalEvents.value, icon: 'tabler-calendar-event', color: 'primary' },
  { title: 'Actifs', value: activeCount.value, icon: 'tabler-check', color: 'success' },
  { title: 'Inactifs', value: inactiveCount.value, icon: 'tabler-x', color: 'error' },
  { title: 'En vedette', value: featuredCount.value, icon: 'tabler-star', color: 'warning' },
  { title: 'Places réservées', value: totalSeatsBooked.value, icon: 'tabler-ticket', color: 'info' },
])

// ─── Filtering ───
const filteredEvents = computed(() => {
  let result = [...events.value]

  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(e =>
      e.title?.toLowerCase().includes(q)
      || e.organizer_name?.toLowerCase().includes(q)
      || e.category_name?.toLowerCase().includes(q)
      || e.location_name?.toLowerCase().includes(q)
      || e.location_address?.toLowerCase().includes(q),
    )
  }

  if (statusFilter.value !== 'all')
    result = result.filter(e => String(e.status) === statusFilter.value)

  if (featuredFilter.value !== 'all')
    result = result.filter(e => String(e.is_featured) === featuredFilter.value)

  if (categoryFilter.value !== 'all')
    result = result.filter(e => e.category_name === categoryFilter.value)

  if (locationFilter.value !== 'all')
    result = result.filter(e => e.location_name === locationFilter.value)

  if (typeFilter.value !== 'all')
    result = result.filter(e => String(e.type) === typeFilter.value)

  return result
})

const paginatedEvents = computed(() => {
  const start = (currentPage.value - 1) * perPage.value
  return filteredEvents.value.slice(start, start + perPage.value)
})

const totalPages = computed(() => Math.ceil(filteredEvents.value.length / perPage.value) || 1)

// ─── Helpers ───
function formatDate(dateString: string | null): string {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatPrice(price: any): string {
  if (price === null || price === undefined) return 'Gratuit'
  return `${Number(price).toFixed(3)} DT`
}

function getTypeLabel(type: number): string {
  if (type === 1) return 'Payant'
  return 'Gratuit'
}

function getStatusConfig(status: any) {
  if (status === true) return { label: 'Actif', color: 'success', icon: 'tabler-check' }
  return { label: 'Inactif', color: 'error', icon: 'tabler-x' }
}

function getSeatsInfo(event: any): string {
  if (event.seats === null) return `${event.seats_booked || 0} réservés`
  return `${event.seats_booked || 0} / ${event.seats}`
}

function getSeatsPercentage(event: any): number {
  if (!event.seats || event.seats === 0) return 0
  return Math.min(Math.round((event.seats_booked / event.seats) * 100), 100)
}

function getSeatsColor(pct: number): string {
  if (pct >= 90) return 'error'
  if (pct >= 70) return 'warning'
  if (pct >= 40) return 'primary'
  return 'info'
}

// ─── CRUD Actions ───
const goToAddPage = () => {
  router.push('/admin/events/add')
}

const goToEditPage = (event: any) => {
  router.push(`/admin/events/${event.id}/edit`)
}

const viewEvent = (event: any) => {
  selectedEvent.value = event
  showViewModal.value = true
}

const featureEvent = async (event: any) => {
  try {
    await apiFetch(`/events/${event.id}/feature/`, { method: 'POST' })
    await fetchEvents()
  }
  catch (err) { console.error('Erreur feature:', err) }
}

const confirmDelete = (event: any) => {
  eventToDelete.value = event
  showDeleteDialog.value = true
}

const deleteEvent = async () => {
  if (!eventToDelete.value) return
  try {
    await apiFetch(`/events/${eventToDelete.value.id}/`, { method: 'DELETE' })
    showDeleteDialog.value = false
    eventToDelete.value = null
    await fetchEvents()
  }
  catch (err) { console.error('Erreur suppression:', err) }
}

const resetFilters = () => {
  searchQuery.value = ''
  statusFilter.value = 'all'
  featuredFilter.value = 'all'
  categoryFilter.value = 'all'
  locationFilter.value = 'all'
  typeFilter.value = 'all'
  currentPage.value = 1
}

// ─── Dropdown items ───
const categoryOptions = computed(() => [
  { title: 'Toutes catégories', value: 'all' },
  ...categories.value.map(c => ({ title: c.name, value: c.name })),
])

const locationOptions = computed(() => [
  { title: 'Tous les lieux', value: 'all' },
  ...locations.value.map(l => ({ title: l.name, value: l.name })),
])

// ─── Init ───
onMounted(() => {
  fetchEvents()
  fetchCategories()
  fetchLocations()
})
</script>

<template>
  <div>
    <!-- Page Header -->
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h4 class="text-h4 font-weight-bold">
          Gestion des Événements
        </h4>
        <p class="text-body-1 text-medium-emphasis mt-1">
          Gérez tous les événements de la plateforme
        </p>
      </div>
      <div class="d-flex gap-2">
        <VBtn color="primary" variant="outlined" prepend-icon="tabler-refresh" @click="fetchEvents">
          Actualiser
        </VBtn>
        <VBtn color="primary" prepend-icon="tabler-calendar-plus" @click="goToAddPage">
          Ajouter un événement
        </VBtn>
      </div>
    </div>

    <!-- KPI Cards -->
    <VRow class="mb-6">
      <VCol v-for="(kpi, i) in kpiCards" :key="i" cols="12" sm="6" md="4" lg>
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

    <!-- Filters -->
    <VCard class="mb-6">
      <VCardText>
        <VRow>
          <VCol cols="12" md="4">
            <VTextField
              v-model="searchQuery"
              placeholder="Rechercher par titre, organisateur, lieu..."
              prepend-inner-icon="tabler-search"
              density="compact"
              clearable
              @update:model-value="currentPage = 1"
            />
          </VCol>
          <VCol cols="12" sm="6" md="2">
            <VSelect
              v-model="statusFilter"
              :items="[
                { title: 'Tous statuts', value: 'all' },
                { title: 'Actifs', value: 'true' },
                { title: 'Inactifs', value: 'false' },
              ]"
              density="compact"
            />
          </VCol>
          <VCol cols="12" sm="6" md="2">
            <VSelect
              v-model="typeFilter"
              :items="[
                { title: 'Tous types', value: 'all' },
                { title: 'Payant', value: '1' },
                { title: 'Gratuit', value: '2' },
              ]"
              density="compact"
            />
          </VCol>
          <VCol cols="12" sm="6" md="2">
            <VSelect
              v-model="categoryFilter"
              :items="categoryOptions"
              density="compact"
            />
          </VCol>
          <VCol cols="12" sm="6" md="2">
            <VSelect
              v-model="locationFilter"
              :items="locationOptions"
              density="compact"
            />
          </VCol>
        </VRow>
        <VRow>
          <VCol cols="12" sm="6" md="3">
            <VSelect
              v-model="featuredFilter"
              :items="[
                { title: 'Tous', value: 'all' },
                { title: 'En vedette', value: 'true' },
                { title: 'Normal', value: 'false' },
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
      <p class="text-body-1 text-medium-emphasis mt-4">Chargement des événements...</p>
    </div>

    <!-- Events Table -->
    <VCard v-else>
      <VTable class="text-no-wrap">
        <thead>
          <tr>
            <th>Événement</th>
            <th>Organisateur</th>
            <th>Catégorie</th>
            <th>Lieu</th>
            <th>Type</th>
            <th>Date début</th>
            <th>Date fin</th>
            <th>Prix</th>
            <th>Places</th>
            <th>Vedette</th>
            <th>Statut</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="event in paginatedEvents" :key="event.id">
            <td>
              <div class="d-flex align-center gap-3 py-2">
                <VAvatar
                  :color="getStatusConfig(event.status).color"
                  variant="tonal"
                  size="40"
                  rounded
                >
                  <VImg v-if="event.cover_image" :src="event.cover_image" />
                  <VIcon v-else icon="tabler-calendar-event" size="20" />
                </VAvatar>
                <div>
                  <p class="text-body-1 font-weight-medium mb-0">{{ event.title }}</p>
                  <p class="text-caption text-medium-emphasis mb-0">{{ event.slug }}</p>
                </div>
              </div>
            </td>
            <td>
              <p class="text-body-2 font-weight-medium mb-0">{{ event.organizer_name || '-' }}</p>
            </td>
            <td>
              <VChip color="primary" size="small" variant="tonal">
                {{ event.category_name || '-' }}
              </VChip>
            </td>
            <td>
              <p class="text-body-2 mb-0">{{ event.location_name || '-' }}</p>
            </td>
            <td>
              <VChip :color="event.type === 1 ? 'warning' : 'success'" size="small" variant="tonal">
                {{ getTypeLabel(event.type) }}
              </VChip>
            </td>
            <td>
              <p class="text-body-2 mb-0">{{ formatDate(event.start_date) }}</p>
            </td>
            <td>
              <p class="text-body-2 mb-0">{{ formatDate(event.end_date) }}</p>
            </td>
            <td>
              <p class="text-body-2 font-weight-medium mb-0">{{ formatPrice(event.price) }}</p>
            </td>
            <td>
              <div v-if="event.seats" class="d-flex align-center gap-2">
                <VProgressLinear
                  :model-value="getSeatsPercentage(event)"
                  :color="getSeatsColor(getSeatsPercentage(event))"
                  height="6"
                  rounded
                  style="inline-size: 50px;"
                />
                <span class="text-caption">{{ getSeatsInfo(event) }}</span>
              </div>
              <span v-else class="text-caption text-medium-emphasis">{{ event.seats_booked || 0 }} réservés</span>
            </td>
            <td>
              <VChip :color="event.is_featured ? 'warning' : 'default'" size="small" variant="tonal">
                <VIcon :icon="event.is_featured ? 'tabler-star-filled' : 'tabler-star'" size="14" start />
                {{ event.is_featured ? 'Oui' : 'Non' }}
              </VChip>
            </td>
            <td>
              <VChip :color="getStatusConfig(event.status).color" size="small" variant="tonal">
                <VIcon :icon="getStatusConfig(event.status).icon" size="14" start />
                {{ getStatusConfig(event.status).label }}
              </VChip>
            </td>
            <td>
              <div class="d-flex gap-1">
                <VBtn icon variant="text" size="small" color="primary" @click="viewEvent(event)">
                  <VIcon icon="tabler-eye" size="18" />
                  <VTooltip activator="parent">Voir</VTooltip>
                </VBtn>
                <VBtn icon variant="text" size="small" color="success" @click="goToEditPage(event)">
                  <VIcon icon="tabler-pencil" size="18" />
                  <VTooltip activator="parent">Modifier</VTooltip>
                </VBtn>
                <VBtn icon variant="text" size="small" color="warning" @click="featureEvent(event)">
                  <VIcon :icon="event.is_featured ? 'tabler-star-off' : 'tabler-star'" size="18" />
                  <VTooltip activator="parent">{{ event.is_featured ? 'Retirer vedette' : 'Mettre en vedette' }}</VTooltip>
                </VBtn>
                <VBtn icon variant="text" size="small" color="error" @click="confirmDelete(event)">
                  <VIcon icon="tabler-trash" size="18" />
                  <VTooltip activator="parent">Supprimer</VTooltip>
                </VBtn>
              </div>
            </td>
          </tr>

          <tr v-if="paginatedEvents.length === 0">
            <td colspan="12" class="text-center py-8">
              <VIcon icon="tabler-calendar-off" size="48" color="disabled" class="mb-2" />
              <p class="text-body-1 text-medium-emphasis">Aucun événement trouvé</p>
            </td>
          </tr>
        </tbody>
      </VTable>

      <VDivider />

      <VCardText class="d-flex justify-space-between align-center flex-wrap">
        <p class="text-body-2 text-medium-emphasis mb-0">
          Affichage {{ Math.min((currentPage - 1) * perPage + 1, filteredEvents.length) }}
          à {{ Math.min(currentPage * perPage, filteredEvents.length) }}
          sur {{ filteredEvents.length }} événements
        </p>
        <div class="d-flex align-center gap-2">
          <VBtn variant="outlined" size="small" :disabled="currentPage <= 1" @click="currentPage--">Précédent</VBtn>
          <VChip size="small" color="primary" variant="tonal">{{ currentPage }} / {{ totalPages }}</VChip>
          <VBtn variant="outlined" size="small" :disabled="currentPage >= totalPages" @click="currentPage++">Suivant</VBtn>
        </div>
      </VCardText>
    </VCard>

    <!-- ═══════ MODAL: Voir détails ═══════ -->
    <VDialog v-model="showViewModal" max-width="650">
      <VCard v-if="selectedEvent">
        <VCardTitle class="d-flex justify-space-between align-center pa-6">
          <span class="text-h6 font-weight-bold">Détails de l'événement</span>
          <VBtn icon variant="text" size="small" @click="showViewModal = false">
            <VIcon icon="tabler-x" />
          </VBtn>
        </VCardTitle>

        <VDivider />

        <VCardText class="pa-6">
          <div class="d-flex align-center gap-4 mb-6">
            <VAvatar :color="getStatusConfig(selectedEvent.status).color" variant="tonal" size="64" rounded>
              <VImg v-if="selectedEvent.cover_image" :src="selectedEvent.cover_image" />
              <VIcon v-else icon="tabler-calendar-event" size="32" />
            </VAvatar>
            <div>
              <h5 class="text-h6 font-weight-bold">{{ selectedEvent.title }}</h5>
              <div class="d-flex gap-2 mt-1">
                <VChip :color="getStatusConfig(selectedEvent.status).color" size="small" variant="tonal">
                  {{ getStatusConfig(selectedEvent.status).label }}
                </VChip>
                <VChip :color="selectedEvent.type === 1 ? 'warning' : 'success'" size="small" variant="tonal">
                  {{ getTypeLabel(selectedEvent.type) }}
                </VChip>
                <VChip v-if="selectedEvent.is_featured" color="warning" size="small" variant="tonal">
                  <VIcon icon="tabler-star-filled" size="12" start />
                  En vedette
                </VChip>
                <VChip v-if="selectedEvent.is_sold_out" color="error" size="small" variant="tonal">
                  Complet
                </VChip>
              </div>
            </div>
          </div>

          <VRow>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Organisateur</p>
              <p class="text-body-2 font-weight-medium">{{ selectedEvent.organizer_name || '-' }}</p>
            </VCol>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Catégorie</p>
              <p class="text-body-2 font-weight-medium">{{ selectedEvent.category_name || '-' }}</p>
            </VCol>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Date début</p>
              <p class="text-body-2 font-weight-medium">{{ formatDate(selectedEvent.start_date) }}</p>
            </VCol>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Date fin</p>
              <p class="text-body-2 font-weight-medium">{{ formatDate(selectedEvent.end_date) }}</p>
            </VCol>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Lieu</p>
              <p class="text-body-2 font-weight-medium">{{ selectedEvent.location_name || '-' }}</p>
            </VCol>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Adresse</p>
              <p class="text-body-2 font-weight-medium">{{ selectedEvent.location_address || '-' }}</p>
            </VCol>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Prix</p>
              <p class="text-body-2 font-weight-medium">{{ formatPrice(selectedEvent.price) }}</p>
            </VCol>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Places</p>
              <p class="text-body-2 font-weight-medium">
                {{ selectedEvent.seats_booked || 0 }} réservées
                <span v-if="selectedEvent.seats"> / {{ selectedEvent.seats }} total</span>
                <span v-if="selectedEvent.seats_available"> ({{ selectedEvent.seats_available }} disponibles)</span>
              </p>
            </VCol>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Slug</p>
              <p class="text-body-2 font-weight-medium">{{ selectedEvent.slug || '-' }}</p>
            </VCol>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Créé le</p>
              <p class="text-body-2 font-weight-medium">{{ formatDate(selectedEvent.created_at) }}</p>
            </VCol>
          </VRow>
        </VCardText>

        <VDivider />

        <VCardActions class="pa-6">
          <VSpacer />
          <VBtn variant="outlined" @click="showViewModal = false">Fermer</VBtn>
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
          <h5 class="text-h6 font-weight-bold mb-2">Confirmer la suppression</h5>
          <p class="text-body-1 text-medium-emphasis mb-0">
            Êtes-vous sûr de vouloir supprimer<br>
            <strong>{{ eventToDelete?.title }}</strong> ?
          </p>
          <p class="text-body-2 text-error mt-2 mb-0">Cette action est irréversible.</p>
        </VCardText>
        <VDivider />
        <VCardActions class="pa-4 justify-center">
          <VBtn variant="outlined" color="secondary" @click="showDeleteDialog = false">Annuler</VBtn>
          <VBtn color="error" prepend-icon="tabler-trash" @click="deleteEvent">Supprimer</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </div>
</template>