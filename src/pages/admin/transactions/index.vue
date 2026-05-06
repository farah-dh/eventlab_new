<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'
const getToken = () => localStorage.getItem('access_token') || localStorage.getItem('token') || ''

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
  if (response.status === 204) return null
  return response.json()
}

// ─── State ───
const isLoading = ref(true)
const orders = ref<any[]>([])
const searchQuery = ref('')
const statusFilter = ref('all')
const paymentFilter = ref('all')
const dateFrom = ref('')
const dateTo = ref('')
const currentPage = ref(1)
const perPage = ref(10)

const successMessage = ref('')
const errorMessage = ref('')
const showSuccess = (m: string) => { successMessage.value = m; setTimeout(() => successMessage.value = '', 4000) }
const showError = (m: string) => { errorMessage.value = m; setTimeout(() => errorMessage.value = '', 5000) }

// Modal
const showModal = ref(false)
const selectedOrder = ref<any>({})

// ─── Status maps (API numeric codes) ───
// Order status: 1=Pending, 2=Confirmed, 3=Cancelled (à ajuster si nécessaire)
const orderStatusMap: Record<number, { label: string; color: string; icon: string }> = {
  1: { label: 'En attente', color: 'warning', icon: 'tabler-clock' },
  2: { label: 'Confirmée', color: 'success', icon: 'tabler-check' },
  3: { label: 'Annulée', color: 'error', icon: 'tabler-x' },
}

// Payment status: 0=Unpaid, 1=Paid, 2=Refunded
const paymentStatusMap: Record<number, { label: string; color: string; icon: string }> = {
  0: { label: 'Non payé', color: 'error', icon: 'tabler-credit-card-off' },
  1: { label: 'Payé', color: 'success', icon: 'tabler-credit-card' },
  2: { label: 'Remboursé', color: 'info', icon: 'tabler-arrow-back' },
}

// ─── Fetch ───
const fetchOrders = async () => {
  isLoading.value = true
  try {
    const data = await apiFetch('/orders/')
    const results = data.results || data.data || data || []
    orders.value = Array.isArray(results) ? results : []
  } catch (err) {
    console.error(err)
    orders.value = []
  } finally {
    isLoading.value = false
  }
}

// ─── Filtering ───
const filteredOrders = computed(() => {
  let result = [...orders.value]
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(o =>
      String(o.id).includes(q)
      || o.event_title?.toLowerCase().includes(q)
      || o.details?.toLowerCase().includes(q),
    )
  }
  if (statusFilter.value !== 'all')
    result = result.filter(o => String(o.status) === statusFilter.value)
  if (paymentFilter.value !== 'all')
    result = result.filter(o => String(o.payment_status) === paymentFilter.value)
  if (dateFrom.value)
    result = result.filter(o => (o.created_at || '') >= dateFrom.value)
  if (dateTo.value)
    result = result.filter(o => (o.created_at || '') <= `${dateTo.value}T23:59:59`)
  return result
})

const paginatedOrders = computed(() => {
  const start = (currentPage.value - 1) * perPage.value
  return filteredOrders.value.slice(start, start + perPage.value)
})

const totalPages = computed(() => Math.ceil(filteredOrders.value.length / perPage.value) || 1)

// ─── Stats ───
const totalOrders = computed(() => orders.value.length)
const paidOrders = computed(() => orders.value.filter(o => o.payment_status === 1).length)
const pendingOrders = computed(() => orders.value.filter(o => o.payment_status === 0).length)
const totalRevenue = computed(() =>
  orders.value.filter(o => o.payment_status === 1).reduce((s, o) => s + Number(o.total_price || 0), 0),
)
const totalCommission = computed(() => totalRevenue.value * 0.1)
const netRevenue = computed(() => totalRevenue.value - totalCommission.value)

const kpiCards = computed(() => [
  { title: 'Total commandes', value: totalOrders.value, icon: 'tabler-receipt', color: 'primary' },
  { title: 'Payées', value: paidOrders.value, icon: 'tabler-credit-card', color: 'success' },
  { title: 'En attente', value: pendingOrders.value, icon: 'tabler-clock', color: 'warning' },
  { title: 'Revenus totaux', value: formatCurrency(totalRevenue.value), icon: 'tabler-currency-dollar', color: 'info' },
  { title: 'Net (90%)', value: formatCurrency(netRevenue.value), icon: 'tabler-building-bank', color: 'secondary' },
])

// ─── Chart ───
const revenueByMonth = computed(() => {
  const now = new Date()
  const months: number[] = []
  for (let i = 5; i >= 0; i--) {
    const target = new Date(now.getFullYear(), now.getMonth() - i, 1)
    const start = new Date(target.getFullYear(), target.getMonth(), 1)
    const end = new Date(target.getFullYear(), target.getMonth() + 1, 0, 23, 59, 59)
    const revenue = orders.value
      .filter(o => {
        if (o.payment_status !== 1) return false
        const d = new Date(o.created_at)
        return d >= start && d <= end
      })
      .reduce((s, o) => s + Number(o.total_price || 0), 0)
    months.push(revenue)
  }
  return months
})

const monthLabels = computed(() => {
  const now = new Date()
  const names = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
  const labels: string[] = []
  for (let i = 5; i >= 0; i--) {
    const t = new Date(now.getFullYear(), now.getMonth() - i, 1)
    labels.push(names[t.getMonth()])
  }
  return labels
})

const chartOptions = computed(() => ({
  chart: { type: 'bar' as const, height: 220, toolbar: { show: false }, parentHeightOffset: 0 },
  colors: ['#7367F0'],
  plotOptions: { bar: { borderRadius: 6, columnWidth: '45%' } },
  xaxis: { categories: monthLabels.value, labels: { style: { fontSize: '12px' } } },
  yaxis: {
    labels: {
      formatter: (val: number) => `${val >= 1000 ? `${(val / 1000).toFixed(1)}K` : val.toFixed(0)} DT`,
      style: { fontSize: '12px' },
    },
  },
  tooltip: { y: { formatter: (val: number) => `${val.toFixed(3)} DT` } },
  dataLabels: { enabled: false },
  grid: { borderColor: '#f1f1f1', strokeDashArray: 5, padding: { bottom: -10 } },
  noData: { text: 'Aucune commande payée', align: 'center' as const, style: { fontSize: '14px', color: '#9e9e9e' } },
}))

const chartSeries = computed(() => [{ name: 'Revenus', data: revenueByMonth.value }])

// ─── Helpers ───
function formatCurrency(a: any): string {
  return `${Number(a || 0).toFixed(3)} DT`
}

function formatDate(d: string | null): string {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function getOrderStatus(s: number) {
  return orderStatusMap[s] || { label: 'Inconnu', color: 'default', icon: 'tabler-help' }
}

function getPaymentStatus(s: number) {
  return paymentStatusMap[s] || { label: 'Inconnu', color: 'default', icon: 'tabler-help' }
}

// ─── Actions ───
const viewOrder = (o: any) => {
  selectedOrder.value = o
  showModal.value = true
}

const markAsPaid = async (o: any) => {
  if (!confirm(`Marquer la commande #${o.id} comme payée ?`)) return
  try {
    await apiFetch(`/orders/${o.id}/mark_paid/`, { method: 'POST' })
    showSuccess(`✅ Commande #${o.id} marquée comme payée.`)
    await fetchOrders()
  } catch (err) { showError('❌ Erreur lors du marquage.'); console.error(err) }
}

const cancelOrder = async (o: any) => {
  if (!confirm(`Annuler la commande #${o.id} ?`)) return
  try {
    await apiFetch(`/orders/${o.id}/cancel/`, { method: 'POST' })
    showSuccess(`✅ Commande #${o.id} annulée.`)
    await fetchOrders()
  } catch (err) { showError('❌ Erreur lors de l\'annulation.'); console.error(err) }
}

const exportCSV = () => {
  const rows = filteredOrders.value.map(o => ({
    ID: o.id,
    Événement: o.event_title || '',
    Quantité: o.quantity || 0,
    'Prix unitaire': Number(o.price || 0).toFixed(3),
    Total: Number(o.total_price || 0).toFixed(3),
    Statut: getOrderStatus(o.status).label,
    Paiement: getPaymentStatus(o.payment_status).label,
    Date: formatDate(o.created_at),
    Détails: o.details || '',
  }))
  if (rows.length === 0) return
  const headers = Object.keys(rows[0])
  const csv = [headers.join(','), ...rows.map(r => headers.map(h => JSON.stringify((r as any)[h] ?? '')).join(','))].join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `commandes_${new Date().toISOString().split('T')[0]}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

const resetFilters = () => {
  searchQuery.value = ''
  statusFilter.value = 'all'
  paymentFilter.value = 'all'
  dateFrom.value = ''
  dateTo.value = ''
  currentPage.value = 1
}

onMounted(fetchOrders)
</script>

<template>
  <div>
    <!-- Header -->
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h4 class="text-h4 font-weight-bold">Toutes les commandes</h4>
        <p class="text-body-1 text-medium-emphasis mt-1">
          Suivez tous les paiements et réservations de la plateforme
        </p>
      </div>
      <div class="d-flex gap-3">
        <VBtn color="success" variant="outlined" prepend-icon="tabler-file-download" @click="exportCSV">
          Exporter CSV
        </VBtn>
        <VBtn color="primary" variant="outlined" prepend-icon="tabler-refresh" @click="fetchOrders">
          Actualiser
        </VBtn>
      </div>
    </div>

    <!-- Notifications -->
    <VAlert v-if="successMessage" type="success" variant="tonal" closable class="mb-4" @click:close="successMessage = ''">
      {{ successMessage }}
    </VAlert>
    <VAlert v-if="errorMessage" type="error" variant="tonal" closable class="mb-4" @click:close="errorMessage = ''">
      {{ errorMessage }}
    </VAlert>

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

    <!-- Chart -->
    <VCard class="mb-6">
      <VCardText>
        <div class="d-flex justify-space-between align-center mb-4">
          <div>
            <h6 class="text-h6 font-weight-bold">Évolution des revenus</h6>
            <p class="text-body-2 text-medium-emphasis mb-0">Commandes payées sur les 6 derniers mois</p>
          </div>
          <VChip color="primary" variant="tonal" size="small">
            Total: {{ formatCurrency(totalRevenue) }}
          </VChip>
        </div>
        <VueApexCharts type="bar" height="220" :options="chartOptions" :series="chartSeries" />
      </VCardText>
    </VCard>

    <!-- Filters -->
    <VCard class="mb-6">
      <VCardText>
        <VRow>
          <VCol cols="12" md="3">
            <VTextField
              v-model="searchQuery"
              placeholder="Rechercher par ID, événement, détails..."
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
                { title: 'En attente', value: '1' },
                { title: 'Confirmée', value: '2' },
                { title: 'Annulée', value: '3' },
              ]"
              density="compact"
            />
          </VCol>
          <VCol cols="12" sm="6" md="2">
            <VSelect
              v-model="paymentFilter"
              :items="[
                { title: 'Tous paiements', value: 'all' },
                { title: 'Payé', value: '1' },
                { title: 'Non payé', value: '0' },
                { title: 'Remboursé', value: '2' },
              ]"
              density="compact"
            />
          </VCol>
          <VCol cols="6" sm="3" md="2">
            <VTextField v-model="dateFrom" type="date" density="compact" label="Du" clearable />
          </VCol>
          <VCol cols="6" sm="3" md="2">
            <VTextField v-model="dateTo" type="date" density="compact" label="Au" clearable />
          </VCol>
          <VCol cols="12" sm="6" md="1">
            <VBtn variant="tonal" color="secondary" block @click="resetFilters">
              <VIcon icon="tabler-refresh" />
            </VBtn>
          </VCol>
        </VRow>
      </VCardText>
    </VCard>

    <!-- Loading -->
    <div v-if="isLoading" class="d-flex flex-column align-center justify-center py-16">
      <VProgressCircular indeterminate color="primary" size="48" />
      <p class="text-body-1 text-medium-emphasis mt-4">Chargement des commandes...</p>
    </div>

    <!-- Table -->
    <VCard v-else>
      <VTable class="text-no-wrap">
        <thead>
          <tr>
            <th>ID</th>
            <th>Événement</th>
            <th>Quantité</th>
            <th>Prix unitaire</th>
            <th>Total</th>
            <th>Paiement</th>
            <th>Statut</th>
            <th>Date</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="o in paginatedOrders" :key="o.id">
            <td><code class="text-caption">#{{ o.id }}</code></td>
            <td>
              <div class="d-flex align-center gap-2 py-2">
                <VAvatar size="36" rounded color="primary" variant="tonal">
                  <VImg v-if="o.event_cover" :src="o.event_cover" />
                  <VIcon v-else icon="tabler-calendar-event" size="18" />
                </VAvatar>
                <p class="text-body-2 font-weight-medium mb-0">{{ o.event_title || '-' }}</p>
              </div>
            </td>
            <td>
              <VChip color="info" size="small" variant="tonal">
                {{ o.quantity || 0 }} billet(s)
              </VChip>
            </td>
            <td>
              <p class="text-body-2 mb-0">{{ formatCurrency(o.price) }}</p>
            </td>
            <td>
              <p class="text-body-2 font-weight-bold mb-0">{{ formatCurrency(o.total_price) }}</p>
            </td>
            <td>
              <VChip :color="getPaymentStatus(o.payment_status).color" size="small" variant="tonal">
                <VIcon :icon="getPaymentStatus(o.payment_status).icon" size="14" start />
                {{ getPaymentStatus(o.payment_status).label }}
              </VChip>
            </td>
            <td>
              <VChip :color="getOrderStatus(o.status).color" size="small" variant="tonal">
                <VIcon :icon="getOrderStatus(o.status).icon" size="14" start />
                {{ getOrderStatus(o.status).label }}
              </VChip>
            </td>
            <td>
              <p class="text-caption mb-0">{{ formatDate(o.created_at) }}</p>
            </td>
            <td>
              <div class="d-flex gap-1">
                <VBtn icon variant="text" size="small" color="primary" @click="viewOrder(o)">
                  <VIcon icon="tabler-eye" size="18" />
                  <VTooltip activator="parent">Voir</VTooltip>
                </VBtn>
                <VBtn
                  v-if="o.payment_status === 0"
                  icon variant="text" size="small" color="success"
                  @click="markAsPaid(o)"
                >
                  <VIcon icon="tabler-check" size="18" />
                  <VTooltip activator="parent">Marquer payé</VTooltip>
                </VBtn>
                <VBtn
                  v-if="o.status !== 3"
                  icon variant="text" size="small" color="error"
                  @click="cancelOrder(o)"
                >
                  <VIcon icon="tabler-ban" size="18" />
                  <VTooltip activator="parent">Annuler</VTooltip>
                </VBtn>
              </div>
            </td>
          </tr>
          <tr v-if="paginatedOrders.length === 0">
            <td colspan="9" class="text-center py-8">
              <VIcon icon="tabler-receipt-off" size="48" color="disabled" class="mb-2" />
              <p class="text-body-1 text-medium-emphasis">Aucune commande trouvée</p>
            </td>
          </tr>
        </tbody>
      </VTable>

      <VDivider />

      <VCardText class="d-flex justify-space-between align-center flex-wrap">
        <p class="text-body-2 text-medium-emphasis mb-0">
          Affichage {{ Math.min((currentPage - 1) * perPage + 1, filteredOrders.length) }}
          à {{ Math.min(currentPage * perPage, filteredOrders.length) }}
          sur {{ filteredOrders.length }} commandes
        </p>
        <div class="d-flex align-center gap-2">
          <VBtn variant="outlined" size="small" :disabled="currentPage <= 1" @click="currentPage--">Précédent</VBtn>
          <VChip size="small" color="primary" variant="tonal">{{ currentPage }} / {{ totalPages }}</VChip>
          <VBtn variant="outlined" size="small" :disabled="currentPage >= totalPages" @click="currentPage++">Suivant</VBtn>
        </div>
      </VCardText>
    </VCard>

    <!-- Modal détail -->
    <VDialog v-model="showModal" max-width="650">
      <VCard>
        <VCardTitle class="d-flex justify-space-between align-center pa-6">
          <span class="text-h6 font-weight-bold">Détail de la commande #{{ selectedOrder.id }}</span>
          <VBtn icon variant="text" size="small" @click="showModal = false">
            <VIcon icon="tabler-x" />
          </VBtn>
        </VCardTitle>
        <VDivider />
        <VCardText class="pa-6">
          <VCard variant="tonal" color="default" class="mb-4">
            <VCardText>
              <VRow>
                <VCol cols="6">
                  <p class="text-caption text-medium-emphasis mb-1">ID</p>
                  <code class="text-body-2">#{{ selectedOrder.id }}</code>
                </VCol>
                <VCol cols="6">
                  <p class="text-caption text-medium-emphasis mb-1">Date</p>
                  <p class="text-body-2 mb-0">{{ formatDate(selectedOrder.created_at) }}</p>
                </VCol>
                <VCol cols="6">
                  <p class="text-caption text-medium-emphasis mb-1">Statut</p>
                  <VChip :color="getOrderStatus(selectedOrder.status).color" size="small" variant="tonal">
                    {{ getOrderStatus(selectedOrder.status).label }}
                  </VChip>
                </VCol>
                <VCol cols="6">
                  <p class="text-caption text-medium-emphasis mb-1">Paiement</p>
                  <VChip :color="getPaymentStatus(selectedOrder.payment_status).color" size="small" variant="tonal">
                    {{ getPaymentStatus(selectedOrder.payment_status).label }}
                  </VChip>
                </VCol>
              </VRow>
            </VCardText>
          </VCard>

          <VCard variant="outlined" class="mb-4">
            <VCardText>
              <h6 class="text-subtitle-1 font-weight-bold mb-3">
                <VIcon icon="tabler-calendar-event" size="18" class="me-1" />
                Événement
              </h6>
              <div class="d-flex align-center gap-3">
                <VAvatar size="56" rounded color="primary" variant="tonal">
                  <VImg v-if="selectedOrder.event_cover" :src="selectedOrder.event_cover" />
                  <VIcon v-else icon="tabler-calendar-event" size="28" />
                </VAvatar>
                <div>
                  <p class="text-body-1 font-weight-medium mb-0">{{ selectedOrder.event_title || '-' }}</p>
                  <p class="text-caption text-medium-emphasis mb-0">Événement ID: {{ selectedOrder.event }}</p>
                </div>
              </div>
            </VCardText>
          </VCard>

          <VCard v-if="selectedOrder.details" variant="outlined" class="mb-4">
            <VCardText>
              <h6 class="text-subtitle-1 font-weight-bold mb-2">
                <VIcon icon="tabler-notes" size="18" class="me-1" />
                Détails
              </h6>
              <p class="text-body-2 mb-0">{{ selectedOrder.details }}</p>
            </VCardText>
          </VCard>

          <VCard color="success" variant="tonal">
            <VCardText>
              <h6 class="text-subtitle-1 font-weight-bold mb-3">
                <VIcon icon="tabler-currency-dollar" size="18" class="me-1" />
                Récapitulatif financier
              </h6>
              <VRow>
                <VCol cols="4" class="text-center">
                  <p class="text-caption text-medium-emphasis mb-1">Prix unitaire</p>
                  <p class="text-h6 font-weight-bold mb-0">{{ formatCurrency(selectedOrder.price) }}</p>
                </VCol>
                <VCol cols="4" class="text-center">
                  <p class="text-caption text-medium-emphasis mb-1">Quantité</p>
                  <p class="text-h6 font-weight-bold mb-0">{{ selectedOrder.quantity || 0 }}</p>
                </VCol>
                <VCol cols="4" class="text-center">
                  <p class="text-caption text-medium-emphasis mb-1">Total</p>
                  <p class="text-h6 font-weight-bold text-success mb-0">{{ formatCurrency(selectedOrder.total_price) }}</p>
                </VCol>
              </VRow>
            </VCardText>
          </VCard>
        </VCardText>
        <VDivider />
        <VCardActions class="pa-6">
          <VSpacer />
          <VBtn variant="outlined" @click="showModal = false">Fermer</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </div>
</template>