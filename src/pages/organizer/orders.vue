<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'

definePage({
  meta: {
    layout: 'organizer',
  },
})

// ── Config API ────────────────────────────────────────────────────────────────
const API = 'http://127.0.0.1:8001/api/v1'
const getToken = () => localStorage.getItem('organizer_token') || ''

const apiFetch = async (endpoint: string, options: RequestInit = {}) => {
  const token = getToken()
  const res = await fetch(`${API}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Token ${token}` }),
      ...options.headers,
    },
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  if (res.status === 204) return null
  return res.json()
}

const organizer = computed(() => {
  try { return JSON.parse(localStorage.getItem('organizer') || '{}') }
  catch { return {} }
})

// ── State ─────────────────────────────────────────────────────────────────────
const isLoading     = ref(true)
const orders        = ref<any[]>([])
const search        = ref('')
const filterStatus  = ref('all')
const selectedOrder = ref<any>(null)
const showDetail    = ref(false)
const isCancelling  = ref(false)
const isMarkingPaid = ref(false)
const actionError   = ref('')

// ── Stats ─────────────────────────────────────────────────────────────────────
const totalOrders   = computed(() => orders.value.length)
const paidOrders    = computed(() => orders.value.filter(o => o.status === 'paid' || o.payment_status === 'paid').length)
const pendingOrders = computed(() => orders.value.filter(o => o.status === 'pending' || o.payment_status === 'pending').length)
const totalRevenue  = computed(() =>
  orders.value
    .filter(o => o.status === 'paid' || o.payment_status === 'paid')
    .reduce((sum, o) => sum + parseFloat(o.total_amount || o.amount || 0), 0)
    .toFixed(2)
)

// ── Filtered ──────────────────────────────────────────────────────────────────
const filteredOrders = computed(() => {
  let list = orders.value
  if (search.value)
    list = list.filter(o =>
      o.event_title?.toLowerCase().includes(search.value.toLowerCase()) ||
      o.user_name?.toLowerCase().includes(search.value.toLowerCase()) ||
      String(o.id).includes(search.value)
    )
  if (filterStatus.value !== 'all')
    list = list.filter(o => (o.status || o.payment_status) === filterStatus.value)
  return list
})

// ── Fetch ─────────────────────────────────────────────────────────────────────
const fetchOrders = async () => {
  isLoading.value = true
  try {
    const data = await apiFetch('/orders/')
    orders.value = data?.results || data || []
  }
  catch (e) { console.error(e) }
  finally { isLoading.value = false }
}

// ── Detail ────────────────────────────────────────────────────────────────────
const openDetail = (order: any) => {
  selectedOrder.value = order
  actionError.value = ''
  showDetail.value = true
}

// ── Cancel ────────────────────────────────────────────────────────────────────
const cancelOrder = async () => {
  if (!selectedOrder.value) return
  isCancelling.value = true
  actionError.value = ''
  try {
    await apiFetch(`/orders/${selectedOrder.value.id}/cancel/`, { method: 'POST' })
    showDetail.value = false
    await fetchOrders()
  }
  catch { actionError.value = "Erreur lors de l'annulation." }
  finally { isCancelling.value = false }
}

// ── Mark paid ─────────────────────────────────────────────────────────────────
const markPaid = async () => {
  if (!selectedOrder.value) return
  isMarkingPaid.value = true
  actionError.value = ''
  try {
    await apiFetch(`/orders/${selectedOrder.value.id}/mark_paid/`, { method: 'POST' })
    showDetail.value = false
    await fetchOrders()
  }
  catch { actionError.value = 'Erreur lors du marquage.' }
  finally { isMarkingPaid.value = false }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
const formatDate = (d: string) => {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('fr-FR', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    paid: 'Payé', confirmed: 'Confirmé',
    pending: 'En attente',
    cancelled: 'Annulé', canceled: 'Annulé',
    refunded: 'Remboursé',
  }
  return map[status] || status || '-'
}

const getStatusBadgeClass = (status: string) => {
  const map: Record<string, string> = {
    paid: 'badge-paid', confirmed: 'badge-paid',
    pending: 'badge-pending',
    cancelled: 'badge-cancelled', canceled: 'badge-cancelled',
    refunded: 'badge-refunded',
  }
  return map[status] || 'badge-default'
}

const orderStatus = (o: any) => o.status || o.payment_status || 'pending'

onMounted(fetchOrders)
</script>

<template>
  <div class="orders-page">

    <!-- Header -->
    <div class="page-header">
      <div>
        <h2 class="page-title">Réservations</h2>
        <p class="page-sub">Suivez toutes les réservations de vos événements</p>
      </div>
      <button class="btn-refresh" @click="fetchOrders">
        <VIcon icon="tabler-refresh" size="15" />
        Actualiser
      </button>
    </div>

    <!-- Stats -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon si-blue"><VIcon icon="tabler-shopping-cart" size="18" /></div>
        <div>
          <p class="stat-label">Total réservations</p>
          <p class="stat-value">{{ totalOrders }}</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon si-green"><VIcon icon="tabler-circle-check" size="18" /></div>
        <div>
          <p class="stat-label">Payées</p>
          <p class="stat-value">{{ paidOrders }}</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon si-amber"><VIcon icon="tabler-clock" size="18" /></div>
        <div>
          <p class="stat-label">En attente</p>
          <p class="stat-value">{{ pendingOrders }}</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon si-violet"><VIcon icon="tabler-coin" size="18" /></div>
        <div>
          <p class="stat-label">Revenus</p>
          <p class="stat-value">{{ totalRevenue }} DT</p>
        </div>
      </div>
    </div>

    <!-- Filtres -->
    <div class="filters-bar">
      <div class="search-wrap">
        <VIcon icon="tabler-search" size="14" class="si" />
        <input
          v-model="search"
          type="text"
          placeholder="Rechercher par événement, client ou N° commande..."
          class="search-input"
        >
      </div>
      <div class="filter-tabs">
        <button :class="['ftab', { active: filterStatus === 'all' }]"       @click="filterStatus = 'all'">Tous</button>
        <button :class="['ftab', { active: filterStatus === 'paid' }]"      @click="filterStatus = 'paid'">Payés</button>
        <button :class="['ftab', { active: filterStatus === 'pending' }]"   @click="filterStatus = 'pending'">En attente</button>
        <button :class="['ftab', { active: filterStatus === 'cancelled' }]" @click="filterStatus = 'cancelled'">Annulés</button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="center-pad">
      <VProgressCircular indeterminate color="primary" size="36" />
    </div>

    <!-- Empty -->
    <div v-else-if="filteredOrders.length === 0" class="empty-state">
      <VIcon icon="tabler-shopping-cart-off" size="56" color="grey-lighten-1" class="mb-4" />
      <p class="empty-title">Aucune réservation trouvée</p>
      <p class="empty-sub">
        {{ search ? 'Essayez un autre terme de recherche' : 'Les réservations apparaîtront ici une fois créées' }}
      </p>
    </div>

    <!-- Table -->
    <div v-else class="table-card">
      <div class="table-head">
        <span class="table-title">Liste des réservations</span>
        <span class="count-badge">{{ filteredOrders.length }} résultat(s)</span>
      </div>
      <div class="table-wrap">
        <table class="orders-table">
          <thead>
            <tr>
              <th>N° Commande</th>
              <th>Événement</th>
              <th>Client</th>
              <th>Billets</th>
              <th>Montant</th>
              <th>Date</th>
              <th>Statut</th>
              <th class="text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="order in filteredOrders" :key="order.id" class="order-row">
              <td><span class="order-id">#{{ order.id }}</span></td>
              <td><span class="event-name">{{ order.event_title || order.event?.title || '-' }}</span></td>
              <td>
                <div class="client-cell">
                  <div class="client-avatar">
                    {{ (order.user_name || order.user?.name || 'U')[0]?.toUpperCase() }}
                  </div>
                  <div>
                    <p class="client-name">{{ order.user_name || order.user?.name || '-' }}</p>
                    <p class="client-email">{{ order.user_email || order.user?.email || '' }}</p>
                  </div>
                </div>
              </td>
              <td><span class="ticket-count">{{ order.quantity || order.tickets || 1 }} billet(s)</span></td>
              <td><span class="amount">{{ parseFloat(order.total_amount || order.amount || 0).toFixed(2) }} DT</span></td>
              <td><span class="date-cell">{{ formatDate(order.created_at || order.date) }}</span></td>
              <td>
                <span :class="['status-badge', getStatusBadgeClass(orderStatus(order))]">
                  {{ getStatusLabel(orderStatus(order)) }}
                </span>
              </td>
              <td class="text-center">
                <button class="action-btn" title="Voir détails" @click="openDetail(order)">
                  <VIcon icon="tabler-eye" size="15" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Dialog Détail -->
    <VDialog v-model="showDetail" max-width="520">
      <VCard v-if="selectedOrder">
        <VCardText class="pa-0">
          <div class="dialog-head">
            <div class="dialog-icon">
              <VIcon icon="tabler-receipt" color="#4F46E5" size="20" />
            </div>
            <div>
              <h3 class="dialog-title">Commande #{{ selectedOrder.id }}</h3>
              <p class="dialog-sub">{{ formatDate(selectedOrder.created_at || selectedOrder.date) }}</p>
            </div>
            <VBtn icon variant="text" size="small" class="ms-auto" @click="showDetail = false">
              <VIcon icon="tabler-x" size="16" />
            </VBtn>
          </div>
          <VDivider />
          <div class="pa-5">
            <VAlert v-if="actionError" type="error" variant="tonal" density="compact" class="mb-4">
              {{ actionError }}
            </VAlert>

            <div class="detail-row highlight-row">
              <span class="detail-label">Statut</span>
              <span :class="['status-badge', getStatusBadgeClass(orderStatus(selectedOrder))]">
                {{ getStatusLabel(orderStatus(selectedOrder)) }}
              </span>
            </div>

            <div class="detail-section">
              <p class="section-title">Événement</p>
              <div class="detail-row">
                <span class="detail-label">Titre</span>
                <span class="detail-value">{{ selectedOrder.event_title || selectedOrder.event?.title || '-' }}</span>
              </div>
            </div>

            <div class="detail-section">
              <p class="section-title">Client</p>
              <div class="detail-row">
                <span class="detail-label">Nom</span>
                <span class="detail-value">{{ selectedOrder.user_name || selectedOrder.user?.name || '-' }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Email</span>
                <span class="detail-value">{{ selectedOrder.user_email || selectedOrder.user?.email || '-' }}</span>
              </div>
            </div>

            <div class="detail-section">
              <p class="section-title">Détails commande</p>
              <div class="detail-row">
                <span class="detail-label">Billets</span>
                <span class="detail-value">{{ selectedOrder.quantity || selectedOrder.tickets || 1 }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Montant total</span>
                <span class="detail-value amount-lg">
                  {{ parseFloat(selectedOrder.total_amount || selectedOrder.amount || 0).toFixed(2) }} DT
                </span>
              </div>
              <div v-if="selectedOrder.payment_method" class="detail-row">
                <span class="detail-label">Méthode paiement</span>
                <span class="detail-value">{{ selectedOrder.payment_method }}</span>
              </div>
              <div v-if="selectedOrder.reference || selectedOrder.transaction_id" class="detail-row">
                <span class="detail-label">Référence</span>
                <span class="detail-value mono">{{ selectedOrder.reference || selectedOrder.transaction_id }}</span>
              </div>
            </div>

            <VDivider class="my-4" />
            <div class="d-flex gap-3 justify-end flex-wrap">
              <VBtn variant="outlined" size="small" @click="showDetail = false">Fermer</VBtn>
              <VBtn
                v-if="orderStatus(selectedOrder) === 'pending'"
                color="success"
                size="small"
                :loading="isMarkingPaid"
                @click="markPaid"
              >
                <VIcon start icon="tabler-check" size="14" />
                Marquer payé
              </VBtn>
              <VBtn
                v-if="!['cancelled', 'canceled', 'refunded'].includes(orderStatus(selectedOrder))"
                color="error"
                variant="outlined"
                size="small"
                :loading="isCancelling"
                @click="cancelOrder"
              >
                <VIcon start icon="tabler-x" size="14" />
                Annuler
              </VBtn>
            </div>
          </div>
        </VCardText>
      </VCard>
    </VDialog>

  </div>
</template>

<style scoped lang="scss">
.orders-page { display: flex; flex-direction: column; gap: 20px; }

.page-header { display: flex; align-items: flex-start; justify-content: space-between; }
.page-title  { font-size: 20px; font-weight: 600; color: #111827; margin: 0 0 4px; }
.page-sub    { font-size: 13px; color: #6B7280; margin: 0; }

.btn-refresh {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 8px 16px; background: white; color: #374151;
  border: 0.5px solid #E5E7EB; border-radius: 8px;
  font-size: 13px; font-weight: 500; cursor: pointer; transition: all .15s;
  &:hover { background: #F9FAFB; }
}

.stats-row {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;
  @media (max-width: 900px) { grid-template-columns: repeat(2, 1fr); }
  @media (max-width: 500px) { grid-template-columns: 1fr; }
}
.stat-card {
  background: white; border: 0.5px solid #E5E7EB;
  border-radius: 12px; padding: 18px 20px;
  display: flex; align-items: center; gap: 14px;
}
.stat-icon {
  width: 40px; height: 40px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  &.si-blue   { background: #EFF6FF; color: #3B82F6; }
  &.si-green  { background: #ECFDF5; color: #10B981; }
  &.si-amber  { background: #FFFBEB; color: #F59E0B; }
  &.si-violet { background: #EEF2FF; color: #6366F1; }
}
.stat-label { font-size: 12px; color: #6B7280; margin: 0 0 4px; }
.stat-value { font-size: 20px; font-weight: 600; color: #111827; margin: 0; }

.filters-bar { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.search-wrap {
  display: flex; align-items: center; gap: 8px;
  background: white; border: 0.5px solid #E5E7EB;
  border-radius: 8px; padding: 7px 12px; flex: 1; min-width: 200px;
  &:focus-within { border-color: #818CF8; box-shadow: 0 0 0 3px rgba(99,102,241,0.08); }
  .si { color: #9CA3AF; flex-shrink: 0; }
  .search-input {
    border: none; background: none; outline: none;
    font-size: 13px; color: #111827; width: 100%;
    &::placeholder { color: #9CA3AF; }
  }
}
.filter-tabs {
  display: flex; background: white;
  border: 0.5px solid #E5E7EB; border-radius: 8px; overflow: hidden;
}
.ftab {
  padding: 7px 14px; border: none; background: none;
  font-size: 13px; color: #6B7280; cursor: pointer;
  transition: all .15s; border-right: 0.5px solid #E5E7EB;
  &:last-child { border-right: none; }
  &.active { background: #4F46E5; color: white; }
  &:hover:not(.active) { background: #F9FAFB; }
}

.center-pad  { display: flex; justify-content: center; padding: 48px; }
.empty-state { text-align: center; padding: 56px 24px; display: flex; flex-direction: column; align-items: center; }
.empty-title { font-size: 15px; font-weight: 500; color: #374151; margin-bottom: 6px; }
.empty-sub   { font-size: 13px; color: #9CA3AF; margin: 0; }

.table-card { background: white; border: 0.5px solid #E5E7EB; border-radius: 12px; overflow: hidden; }
.table-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; border-bottom: 0.5px solid #F3F4F6;
}
.table-title { font-size: 14px; font-weight: 600; color: #111827; }
.count-badge { padding: 3px 10px; background: #EEF2FF; color: #4F46E5; border-radius: 20px; font-size: 11px; font-weight: 500; }
.table-wrap  { overflow-x: auto; }

.orders-table {
  width: 100%; border-collapse: collapse;
  th {
    padding: 11px 16px; text-align: left;
    font-size: 11px; font-weight: 600; color: #6B7280;
    text-transform: uppercase; letter-spacing: .5px;
    background: #FAFAFA; border-bottom: 0.5px solid #F3F4F6; white-space: nowrap;
  }
  td { padding: 13px 16px; border-bottom: 0.5px solid #F9FAFB; vertical-align: middle; }
  .order-row:last-child td { border-bottom: none; }
  .order-row:hover td { background: #FAFAFA; }
}

.order-id     { font-size: 13px; font-weight: 600; color: #4F46E5; font-family: monospace; }
.event-name   { font-size: 13px; font-weight: 500; color: #111827; }
.ticket-count { font-size: 13px; color: #374151; }
.amount       { font-size: 13px; font-weight: 600; color: #111827; }
.date-cell    { font-size: 12px; color: #6B7280; white-space: nowrap; }

.client-cell  { display: flex; align-items: center; gap: 10px; }
.client-avatar {
  width: 30px; height: 30px; border-radius: 50%;
  background: #EEF2FF; color: #4F46E5;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 600; flex-shrink: 0;
}
.client-name  { font-size: 13px; font-weight: 500; color: #111827; margin: 0; }
.client-email { font-size: 11px; color: #9CA3AF; margin: 0; }

.status-badge {
  display: inline-flex; align-items: center;
  padding: 3px 10px; border-radius: 20px;
  font-size: 11px; font-weight: 600; white-space: nowrap;
}
.badge-paid      { background: #ECFDF5; color: #059669; }
.badge-pending   { background: #FFFBEB; color: #D97706; }
.badge-cancelled { background: #FEF2F2; color: #DC2626; }
.badge-refunded  { background: #EFF6FF; color: #2563EB; }
.badge-default   { background: #F3F4F6; color: #6B7280; }

.action-btn {
  display: inline-flex; align-items: center; justify-content: center;
  width: 30px; height: 30px; border: 0.5px solid #E5E7EB;
  border-radius: 6px; background: white; cursor: pointer;
  color: #6B7280; transition: all .15s;
  &:hover { background: #EEF2FF; color: #4F46E5; border-color: #C7D2FE; }
}

.dialog-head {
  display: flex; align-items: center; gap: 14px; padding: 18px 20px 14px;
}
.dialog-icon {
  width: 38px; height: 38px; background: #EEF2FF;
  border-radius: 9px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.dialog-title { font-size: 15px; font-weight: 600; color: #111827; margin: 0 0 2px; }
.dialog-sub   { font-size: 12px; color: #9CA3AF; margin: 0; }

.detail-section { margin-bottom: 16px; }
.section-title  { font-size: 11px; font-weight: 600; color: #9CA3AF; text-transform: uppercase; letter-spacing: .6px; margin: 0 0 8px; }
.detail-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 7px 0; border-bottom: 0.5px solid #F9FAFB;
  &:last-child { border-bottom: none; }
  &.highlight-row { background: #F9FAFB; padding: 8px 12px; border-radius: 8px; margin-bottom: 16px; border-bottom: none; }
}
.detail-label { font-size: 12px; color: #9CA3AF; }
.detail-value { font-size: 13px; font-weight: 500; color: #111827; text-align: right; }
.amount-lg    { font-size: 16px; font-weight: 700; color: #111827; }
.mono         { font-family: monospace; font-size: 12px; }

.mb-4 { margin-bottom: 16px; }
.my-4 { margin: 16px 0; }
</style>