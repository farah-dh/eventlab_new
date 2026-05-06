<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

// ─── Config API ───
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'

const getToken = () => {
  return localStorage.getItem('access_token') || localStorage.getItem('token')
}

const apiFetch = async (endpoint: string) => {
  const token = getToken()
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  })
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json()
}

// ─── State ───
const isLoading = ref(true)
const hasError = ref(false)
const errorMsg = ref('')
const allUsers = ref<any[]>([])
const allEvents = ref<any[]>([])
const allPayments = ref<any[]>([])

// ─── Fetch Data ───
const fetchDashboardData = async () => {
  isLoading.value = true
  hasError.value = false

  try {
    try {
      const usersData = await apiFetch('/users/')
      const users = usersData.results || usersData.data || usersData || []
      allUsers.value = Array.isArray(users) ? users : []
    }
    catch { allUsers.value = [] }

    try {
      const eventsData = await apiFetch('/events/')
      const events = eventsData.results || eventsData.data || eventsData || []
      allEvents.value = Array.isArray(events) ? events : []
    }
    catch { allEvents.value = [] }

    try {
      const paymentsData = await apiFetch('/orders/transactions/')
      const payments = paymentsData.results || paymentsData.data || paymentsData || []
      allPayments.value = Array.isArray(payments) ? payments : []
    }
    catch { allPayments.value = [] }
  }
  catch (err: any) {
    hasError.value = true
    errorMsg.value = err.message || 'Erreur de connexion au serveur'
  }
  finally {
    isLoading.value = false
  }
}

// ─── Computed Stats ───
const totalUsers = computed(() => allUsers.value.length)
const totalOrganizers = computed(() => allUsers.value.filter(u => u.role === 'organizer' || u.is_organizer).length)
const totalEvents = computed(() => allEvents.value.length)
const activeEvents = computed(() => allEvents.value.filter(e => e.status === 'ongoing' || e.status === 'upcoming').length)
const pendingEventsList = computed(() => allEvents.value.filter(e => e.status === 'pending' || !e.is_approved).slice(0, 5))
const totalRevenue = computed(() => allPayments.value.reduce((sum, p) => sum + (Number(p.amount) || 0), 0))
const ticketsSold = computed(() => allEvents.value.reduce((sum, e) => sum + (e.tickets_sold || 0), 0))

// ─── Calcul des revenus par mois (RÉEL) ───
const revenueByMonth = computed(() => {
  const now = new Date()
  const months: number[] = []

  // Calculer les 6 derniers mois
  for (let i = 5; i >= 0; i--) {
    const targetMonth = new Date(now.getFullYear(), now.getMonth() - i, 1)
    const monthStart = new Date(targetMonth.getFullYear(), targetMonth.getMonth(), 1)
    const monthEnd = new Date(targetMonth.getFullYear(), targetMonth.getMonth() + 1, 0, 23, 59, 59)

    const monthRevenue = allPayments.value
      .filter(p => {
        const paymentDate = new Date(p.created_at || p.date || p.paid_at)
        return paymentDate >= monthStart && paymentDate <= monthEnd
      })
      .reduce((sum, p) => sum + (Number(p.amount) || 0), 0)

    months.push(monthRevenue)
  }

  return months
})

// Noms des 6 derniers mois
const monthLabels = computed(() => {
  const now = new Date()
  const labels: string[] = []
  const monthNames = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']

  for (let i = 5; i >= 0; i--) {
    const targetMonth = new Date(now.getFullYear(), now.getMonth() - i, 1)
    labels.push(monthNames[targetMonth.getMonth()])
  }

  return labels
})

// Pourcentage de croissance réel
const revenueGrowth = computed(() => {
  const data = revenueByMonth.value
  if (data.length < 2) return '0'
  const current = data[data.length - 1]
  const previous = data[data.length - 2]
  if (previous === 0) return current > 0 ? '+100' : '0'
  const growth = ((current - previous) / previous) * 100
  return (growth >= 0 ? '+' : '') + growth.toFixed(1)
})

const recentEvents = computed(() => {
  return [...allEvents.value]
    .sort((a, b) => new Date(b.created_at || b.date).getTime() - new Date(a.created_at || a.date).getTime())
    .slice(0, 6)
})

const recentUsers = computed(() => {
  return [...allUsers.value]
    .sort((a, b) => new Date(b.date_joined || b.created_at).getTime() - new Date(a.date_joined || a.created_at).getTime())
    .slice(0, 5)
})

// ─── KPI Cards ───
const kpiCards = computed(() => [
  {
    title: 'Utilisateurs',
    value: totalUsers.value,
    subtitle: `${totalOrganizers.value} organisateurs`,
    icon: 'tabler-users',
    color: 'primary',
  },
  {
    title: 'Événements',
    value: totalEvents.value,
    subtitle: `${activeEvents.value} actifs`,
    icon: 'tabler-calendar-event',
    color: 'success',
  },
  {
    title: 'Revenus totaux',
    value: formatCurrency(totalRevenue.value),
    subtitle: `${allPayments.value.length} transactions`,
    icon: 'tabler-currency-dollar',
    color: 'warning',
  },
  {
    title: 'Billets vendus',
    value: ticketsSold.value,
    subtitle: `${pendingEventsList.value.length} en attente`,
    icon: 'tabler-ticket',
    color: 'info',
  },
])

// ─── Chart (données RÉELLES) ───
const chartOptions = computed(() => ({
  chart: {
    type: 'area' as const,
    height: 250,
    toolbar: { show: false },
    parentHeightOffset: 0,
  },
  colors: ['#7367F0'],
  fill: {
    type: 'gradient',
    gradient: { shadeIntensity: 1, opacityFrom: 0.4, opacityTo: 0.1, stops: [0, 90, 100] },
  },
  stroke: { curve: 'smooth' as const, width: 3 },
  xaxis: {
    categories: monthLabels.value,
    labels: { style: { fontSize: '12px' } },
  },
  yaxis: {
    labels: {
      formatter: (val: number) => `${val >= 1000 ? `${(val / 1000).toFixed(1)}K` : val.toFixed(0)} DT`,
      style: { fontSize: '12px' },
    },
  },
  tooltip: { y: { formatter: (val: number) => `${val.toFixed(3)} DT` } },
  dataLabels: { enabled: false },
  grid: { borderColor: '#f1f1f1', strokeDashArray: 5, padding: { bottom: -10 } },
  noData: {
    text: 'Aucune transaction pour le moment',
    align: 'center' as const,
    verticalAlign: 'middle' as const,
    style: { fontSize: '14px', color: '#9e9e9e' },
  },
}))

const chartSeries = computed(() => [
  { name: 'Revenus', data: revenueByMonth.value },
])

// ─── Helpers ───
function formatCurrency(amount: number): string {
  if (amount >= 1000000) return `${(amount / 1000000).toFixed(1)}M DT`
  if (amount >= 1000) return `${(amount / 1000).toFixed(1)}K DT`
  return `${amount.toFixed(3)} DT`
}

function formatDate(dateString: string | null): string {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatRelativeDate(dateString: string | null): string {
  if (!dateString) return '-'
  const diff = Date.now() - new Date(dateString).getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 60) return `Il y a ${minutes} min`
  const hours = Math.floor(diff / 3600000)
  if (hours < 24) return `Il y a ${hours}h`
  const days = Math.floor(diff / 86400000)
  if (days < 7) return `Il y a ${days}j`
  return formatDate(dateString)
}

function getEventStatusConfig(status: string) {
  const config: Record<string, { label: string; color: string; icon: string }> = {
    upcoming: { label: 'À venir', color: 'info', icon: 'tabler-clock' },
    ongoing: { label: 'En cours', color: 'success', icon: 'tabler-player-play' },
    completed: { label: 'Terminé', color: 'secondary', icon: 'tabler-check' },
    cancelled: { label: 'Annulé', color: 'error', icon: 'tabler-x' },
    pending: { label: 'En attente', color: 'warning', icon: 'tabler-clock-pause' },
    draft: { label: 'Brouillon', color: 'default', icon: 'tabler-pencil' },
    true: { label: 'Actif', color: 'success', icon: 'tabler-check' },
    false: { label: 'Inactif', color: 'error', icon: 'tabler-x' },
  }
  return config[String(status)] || { label: String(status), color: 'default', icon: 'tabler-help' }
}

function getRoleConfig(role: string) {
  const config: Record<string, { label: string; color: string }> = {
    admin: { label: 'Admin', color: 'error' },
    organizer: { label: 'Organisateur', color: 'primary' },
    user: { label: 'Utilisateur', color: 'info' },
  }
  return config[role] || { label: role || 'Utilisateur', color: 'info' }
}

function getTicketPercentage(sold: number, capacity: number): number {
  if (!capacity) return 0
  return Math.min(Math.round((sold / capacity) * 100), 100)
}

function getTicketColor(pct: number): string {
  if (pct >= 90) return 'error'
  if (pct >= 70) return 'warning'
  if (pct >= 40) return 'primary'
  return 'info'
}

// ─── Actions ───
const approveEvent = async (eventId: number) => {
  try {
    await apiFetch(`/events/${eventId}/approve/`)
    await fetchDashboardData()
  }
  catch (err) { console.error('Erreur approbation:', err) }
}

const rejectEvent = async (eventId: number) => {
  try {
    await apiFetch(`/events/${eventId}/reject/`)
    await fetchDashboardData()
  }
  catch (err) { console.error('Erreur rejet:', err) }
}

onMounted(() => { fetchDashboardData() })
</script>

<template>
  <div>
    <!-- Page Header -->
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h4 class="text-h4 font-weight-bold">
          Tableau de bord
        </h4>
        <p class="text-body-1 text-medium-emphasis mt-1">
          Bienvenue ! Voici un aperçu de votre plateforme EventLab.
        </p>
      </div>
      <VBtn color="primary" variant="outlined" prepend-icon="tabler-download">
        Exporter
      </VBtn>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="d-flex flex-column align-center justify-center py-16">
      <VProgressCircular indeterminate color="primary" size="48" />
      <p class="text-body-1 text-medium-emphasis mt-4">
        Chargement des données...
      </p>
    </div>

    <!-- Error State -->
    <VAlert v-else-if="hasError" type="warning" variant="tonal" class="mb-6">
      <template #title>
        Connexion au serveur impossible
      </template>
      <p class="mb-2">
        {{ errorMsg || 'Le serveur API ne répond pas.' }}
      </p>
      <VBtn size="small" color="warning" variant="outlined" prepend-icon="tabler-refresh" @click="fetchDashboardData">
        Réessayer
      </VBtn>
    </VAlert>

    <template v-if="!isLoading">
      <!-- KPI Cards -->
      <VRow class="mb-6">
        <VCol v-for="(kpi, i) in kpiCards" :key="i" cols="12" sm="6" lg="3">
          <VCard>
            <VCardText class="d-flex align-center gap-4">
              <VAvatar :color="kpi.color" variant="tonal" size="48" rounded>
                <VIcon :icon="kpi.icon" size="28" />
              </VAvatar>
              <div>
                <p class="text-body-2 text-medium-emphasis mb-1">
                  {{ kpi.title }}
                </p>
                <h4 class="text-h5 font-weight-bold">
                  {{ kpi.value }}
                </h4>
                <p class="text-caption text-medium-emphasis mb-0 mt-1">
                  {{ kpi.subtitle }}
                </p>
              </div>
            </VCardText>
          </VCard>
        </VCol>
      </VRow>

      <!-- Charts Row -->
      <VRow class="mb-6">
        <VCol cols="12" md="8">
          <VCard>
            <VCardText>
              <div class="d-flex justify-space-between align-center mb-4">
                <div>
                  <h6 class="text-h6 font-weight-bold">
                    Revenus mensuels
                  </h6>
                  <p class="text-body-2 text-medium-emphasis mb-0">
                    Évolution sur les 6 derniers mois
                  </p>
                </div>
                <VChip
                  :color="revenueGrowth.startsWith('+') ? 'success' : revenueGrowth === '0' ? 'secondary' : 'error'"
                  variant="tonal"
                  size="small"
                >
                  <VIcon
                    :icon="revenueGrowth.startsWith('+') ? 'tabler-trending-up' : revenueGrowth === '0' ? 'tabler-minus' : 'tabler-trending-down'"
                    size="14"
                    start
                  />
                  {{ revenueGrowth }}%
                </VChip>
              </div>
              <VueApexCharts type="area" height="250" :options="chartOptions" :series="chartSeries" />
            </VCardText>
          </VCard>
        </VCol>

        <VCol cols="12" md="4">
          <VCard class="h-100">
            <VCardText>
              <h6 class="text-h6 font-weight-bold mb-6">
                Résumé rapide
              </h6>
              <div class="d-flex flex-column gap-6">
                <div class="d-flex align-center gap-3">
                  <VAvatar color="primary" variant="tonal" size="40" rounded>
                    <VIcon icon="tabler-user-star" size="22" />
                  </VAvatar>
                  <div class="flex-grow-1">
                    <p class="text-body-2 font-weight-medium mb-0">
                      Organisateurs
                    </p>
                    <p class="text-caption text-medium-emphasis mb-0">
                      Comptes actifs
                    </p>
                  </div>
                  <span class="text-h6 font-weight-bold">{{ totalOrganizers }}</span>
                </div>
                <div class="d-flex align-center gap-3">
                  <VAvatar color="success" variant="tonal" size="40" rounded>
                    <VIcon icon="tabler-calendar-check" size="22" />
                  </VAvatar>
                  <div class="flex-grow-1">
                    <p class="text-body-2 font-weight-medium mb-0">
                      Événements actifs
                    </p>
                    <p class="text-caption text-medium-emphasis mb-0">
                      En cours / À venir
                    </p>
                  </div>
                  <span class="text-h6 font-weight-bold">{{ activeEvents }}</span>
                </div>
                <div class="d-flex align-center gap-3">
                  <VAvatar color="warning" variant="tonal" size="40" rounded>
                    <VIcon icon="tabler-clock-pause" size="22" />
                  </VAvatar>
                  <div class="flex-grow-1">
                    <p class="text-body-2 font-weight-medium mb-0">
                      En attente
                    </p>
                    <p class="text-caption text-medium-emphasis mb-0">
                      Approbation requise
                    </p>
                  </div>
                  <VChip color="warning" size="small">
                    {{ pendingEventsList.length }}
                  </VChip>
                </div>
                <div class="d-flex align-center gap-3">
                  <VAvatar color="info" variant="tonal" size="40" rounded>
                    <VIcon icon="tabler-ticket" size="22" />
                  </VAvatar>
                  <div class="flex-grow-1">
                    <p class="text-body-2 font-weight-medium mb-0">
                      Billets vendus
                    </p>
                    <p class="text-caption text-medium-emphasis mb-0">
                      Total cumulé
                    </p>
                  </div>
                  <span class="text-h6 font-weight-bold">{{ ticketsSold }}</span>
                </div>
              </div>
            </VCardText>
          </VCard>
        </VCol>
      </VRow>

      <!-- Pending Events -->
      <VCard v-if="pendingEventsList.length > 0" class="mb-6">
        <VCardText>
          <div class="d-flex align-center gap-2 mb-4">
            <VIcon icon="tabler-alert-circle" color="warning" />
            <h6 class="text-h6 font-weight-bold">
              Événements en attente d'approbation
            </h6>
            <VChip color="warning" size="small">
              {{ pendingEventsList.length }}
            </VChip>
          </div>
          <div class="d-flex flex-column gap-3">
            <div
              v-for="event in pendingEventsList"
              :key="event.id"
              class="d-flex align-center justify-space-between pa-3 rounded-lg"
              style="border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));"
            >
              <div class="d-flex align-center gap-3">
                <VAvatar color="warning" variant="tonal" size="40" rounded>
                  <VIcon icon="tabler-calendar" />
                </VAvatar>
                <div>
                  <p class="text-body-1 font-weight-medium mb-0">
                    {{ event.title }}
                  </p>
                  <p class="text-body-2 text-medium-emphasis mb-0">
                    {{ event.organizer_name || 'Organisateur' }} · {{ formatDate(event.date) }}
                  </p>
                </div>
              </div>
              <div class="d-flex gap-2">
                <VBtn color="success" variant="tonal" size="small" prepend-icon="tabler-check" @click="approveEvent(event.id)">
                  Approuver
                </VBtn>
                <VBtn color="error" variant="tonal" size="small" prepend-icon="tabler-x" @click="rejectEvent(event.id)">
                  Refuser
                </VBtn>
              </div>
            </div>
          </div>
        </VCardText>
      </VCard>

      <!-- Tables Row -->
      <VRow>
        <VCol cols="12" lg="7">
          <VCard>
            <VCardText>
              <div class="d-flex justify-space-between align-center mb-4">
                <h6 class="text-h6 font-weight-bold">
                  Événements récents
                </h6>
                <VBtn variant="text" color="primary" size="small" append-icon="tabler-arrow-right" to="/admin/events">
                  Voir tout
                </VBtn>
              </div>
              <VTable class="text-no-wrap">
                <thead>
                  <tr>
                    <th>Événement</th>
                    <th>Date</th>
                    <th>Billets</th>
                    <th>Statut</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="event in recentEvents" :key="event.id">
                    <td>
                      <div class="d-flex align-center gap-3 py-2">
                        <VAvatar :color="getEventStatusConfig(event.status).color" variant="tonal" size="38" rounded>
                          <VIcon :icon="getEventStatusConfig(event.status).icon" size="20" />
                        </VAvatar>
                        <div>
                          <p class="text-body-1 font-weight-medium mb-0">
                            {{ event.title }}
                          </p>
                          <p class="text-caption text-medium-emphasis mb-0">
                            {{ event.category || 'Général' }}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td>{{ formatDate(event.date) }}</td>
                    <td>
                      <div class="d-flex align-center gap-2">
                        <VProgressLinear
                          :model-value="getTicketPercentage(event.tickets_sold || 0, event.capacity || 1)"
                          :color="getTicketColor(getTicketPercentage(event.tickets_sold || 0, event.capacity || 1))"
                          height="6"
                          rounded
                          style="inline-size: 60px;"
                        />
                        <span class="text-caption text-medium-emphasis">
                          {{ event.tickets_sold || 0 }}/{{ event.capacity || 0 }}
                        </span>
                      </div>
                    </td>
                    <td>
                      <VChip :color="getEventStatusConfig(event.status).color" size="small" variant="tonal">
                        {{ getEventStatusConfig(event.status).label }}
                      </VChip>
                    </td>
                  </tr>
                  <tr v-if="recentEvents.length === 0">
                    <td colspan="4" class="text-center text-medium-emphasis py-8">
                      Aucun événement pour le moment
                    </td>
                  </tr>
                </tbody>
              </VTable>
            </VCardText>
          </VCard>
        </VCol>

        <VCol cols="12" lg="5">
          <VCard>
            <VCardText>
              <div class="d-flex justify-space-between align-center mb-4">
                <h6 class="text-h6 font-weight-bold">
                  Derniers inscrits
                </h6>
                <VBtn variant="text" color="primary" size="small" append-icon="tabler-arrow-right" to="/admin/users">
                  Voir tout
                </VBtn>
              </div>
              <div class="d-flex flex-column gap-4">
                <div v-for="user in recentUsers" :key="user.id" class="d-flex align-center gap-3">
                  <VAvatar :color="getRoleConfig(user.role).color" variant="tonal" size="40">
                    <span class="text-body-1 font-weight-medium">
                      {{ (user.full_name || user.email || '?')[0].toUpperCase() }}
                    </span>
                  </VAvatar>
                  <div class="flex-grow-1">
                    <p class="text-body-2 font-weight-medium mb-0">
                      {{ user.full_name || user.username || user.email }}
                    </p>
                    <p class="text-caption text-medium-emphasis mb-0">
                      {{ user.email }}
                    </p>
                  </div>
                  <div class="text-end">
                    <VChip :color="getRoleConfig(user.role).color" size="x-small" variant="tonal">
                      {{ getRoleConfig(user.role).label }}
                    </VChip>
                    <p class="text-caption text-medium-emphasis mb-0 mt-1">
                      {{ formatRelativeDate(user.date_joined || user.created_at) }}
                    </p>
                  </div>
                </div>
                <div v-if="recentUsers.length === 0" class="text-center text-medium-emphasis py-8">
                  Aucun utilisateur pour le moment
                </div>
              </div>
            </VCardText>
          </VCard>
        </VCol>
      </VRow>
    </template>
  </div>
</template>