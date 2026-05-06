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
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json()
}

const isLoading     = ref(true)
const orders        = ref<any[]>([])
const searchQuery   = ref('')
const statusFilter  = ref('all')
const currentPage   = ref(1)
const perPage       = ref(10)
const showDetail    = ref(false)
const showTicket    = ref(false)
const selectedOrder = ref<any>(null)
const ticketQrUrl   = ref('')

const fetchOrders = async () => {
  isLoading.value = true
  try {
    const data = await apiFetch('/orders/')
    const results = data.results || data.data || data || []
    orders.value = Array.isArray(results) ? results : []
  }
  catch (err) {
    console.error('Erreur chargement réservations:', err)
    orders.value = []
  }
  finally {
    isLoading.value = false
  }
}

const cancelOrder = async (order: any) => {
  if (confirm(`Annuler la réservation #${order.id} ?`)) {
    try {
      await apiFetch(`/orders/${order.id}/cancel/`, { method: 'POST' })
      await fetchOrders()
    }
    catch (err) { console.error('Erreur annulation:', err) }
  }
}

const viewOrder = (order: any) => {
  selectedOrder.value = order
  showDetail.value = true
}

const viewTicket = (order: any) => {
  selectedOrder.value = order

  // Générer le QR code avec les infos de la commande
  const qrText = [
    `Commande #${order.id}`,
    order.event_title || order.event?.title || 'EventLab',
    `Quantite: ${order.quantity || 1} billet(s)`,
    `Montant: ${Number(order.total_price || order.total_amount || 0).toFixed(3)} DT`,
    `Date: ${formatDate(order.created_at)}`,
  ].join(' | ')

  ticketQrUrl.value = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(qrText)}&color=3d2c35&bgcolor=ffffff&margin=10`
  showTicket.value = true
}

const printTicket = () => window.print()

const totalOrders    = computed(() => orders.value.length)
const pendingCount   = computed(() => orders.value.filter(o => Number(o.payment_status) === 0).length)
const confirmedCount = computed(() => orders.value.filter(o => Number(o.payment_status) === 1).length)
const cancelledCount = computed(() => orders.value.filter(o => Number(o.payment_status) === 2).length)

const totalSpent = computed(() =>
  orders.value
    .filter(o => Number(o.payment_status) === 1)
    .reduce((sum, o) => sum + Number(o.total_price || o.total_amount || o.amount || 0), 0),
)

const filteredOrders = computed(() => {
  let result = [...orders.value]
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(o =>
      o.event_title?.toLowerCase().includes(q)
      || o.event?.title?.toLowerCase().includes(q)
      || String(o.id).includes(q),
    )
  }
  if (statusFilter.value !== 'all')
    result = result.filter(o => String(o.payment_status) === statusFilter.value)
  return result
})

const paginatedOrders = computed(() => {
  const start = (currentPage.value - 1) * perPage.value
  return filteredOrders.value.slice(start, start + perPage.value)
})

const totalPages = computed(() => Math.ceil(filteredOrders.value.length / perPage.value) || 1)

function formatDate(dateString: string | null): string {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('fr-FR', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function formatPrice(price: any): string {
  const val = Number(price)
  if (!price || val === 0) return '—'
  return `${val.toFixed(3)} DT`
}

function getStatusConfig(status: any) {
  const config: Record<string, { label: string; color: string; icon: string }> = {
    '0': { label: 'En attente', color: 'warning',   icon: 'tabler-clock' },
    '1': { label: 'Payée ✅',   color: 'success',   icon: 'tabler-check' },
    '2': { label: 'Échouée',    color: 'error',     icon: 'tabler-x' },
    '3': { label: 'Remboursée', color: 'secondary', icon: 'tabler-arrow-back' },
  }
  return config[String(status)] || { label: 'Inconnu', color: 'default', icon: 'tabler-help' }
}

function getEventDate(order: any): { day: string; month: string; year: string } {
  const d = order.event?.start_date || order.event_date || order.created_at
  if (!d) return { day: '--', month: '---', year: '----' }
  const dt = new Date(d)
  return {
    day:   dt.getDate().toString().padStart(2, '0'),
    month: dt.toLocaleDateString('fr-FR', { month: 'short' }).toUpperCase().replace('.', ''),
    year:  dt.getFullYear().toString(),
  }
}

onMounted(() => { fetchOrders() })
</script>

<template>
  <div>
    <!-- Header -->
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h4 class="text-h4 font-weight-bold">Mes réservations</h4>
        <p class="text-body-1 text-medium-emphasis mt-1">Suivez toutes vos réservations d'événements</p>
      </div>
      <VBtn color="primary" variant="outlined" prepend-icon="tabler-refresh" @click="fetchOrders">
        Actualiser
      </VBtn>
    </div>

    <!-- KPI Cards -->
    <VRow class="mb-6">
      <VCol cols="6" md="3">
        <VCard class="text-center pa-4">
          <VAvatar color="primary" variant="tonal" size="44" class="mb-2">
            <VIcon icon="tabler-ticket" size="24" />
          </VAvatar>
          <h5 class="text-h5 font-weight-bold">{{ totalOrders }}</h5>
          <p class="text-caption text-medium-emphasis mb-0">Total</p>
        </VCard>
      </VCol>
      <VCol cols="6" md="3">
        <VCard class="text-center pa-4">
          <VAvatar color="warning" variant="tonal" size="44" class="mb-2">
            <VIcon icon="tabler-clock" size="24" />
          </VAvatar>
          <h5 class="text-h5 font-weight-bold">{{ pendingCount }}</h5>
          <p class="text-caption text-medium-emphasis mb-0">En attente</p>
        </VCard>
      </VCol>
      <VCol cols="6" md="3">
        <VCard class="text-center pa-4">
          <VAvatar color="success" variant="tonal" size="44" class="mb-2">
            <VIcon icon="tabler-check" size="24" />
          </VAvatar>
          <h5 class="text-h5 font-weight-bold">{{ confirmedCount }}</h5>
          <p class="text-caption text-medium-emphasis mb-0">Confirmées</p>
        </VCard>
      </VCol>
      <VCol cols="6" md="3">
        <VCard class="text-center pa-4">
          <VAvatar color="success" variant="tonal" size="44" class="mb-2">
            <VIcon icon="tabler-wallet" size="24" />
          </VAvatar>
          <h5 class="text-h5 font-weight-bold">{{ totalSpent.toFixed(3) }}</h5>
          <p class="text-caption text-medium-emphasis mb-0">DT dépensés</p>
        </VCard>
      </VCol>
    </VRow>

    <!-- Filters -->
    <VCard class="mb-6">
      <VCardText>
        <VRow>
          <VCol cols="12" md="6">
            <VTextField
              v-model="searchQuery"
              placeholder="Rechercher par événement ou référence..."
              prepend-inner-icon="tabler-search"
              density="compact"
              clearable
              @update:model-value="currentPage = 1"
            />
          </VCol>
          <VCol cols="12" md="4">
            <VSelect
              v-model="statusFilter"
              :items="[
                { title: 'Tous les statuts', value: 'all' },
                { title: 'En attente',       value: '0' },
                { title: 'Payées',           value: '1' },
                { title: 'Échouées',         value: '2' },
                { title: 'Remboursées',      value: '3' },
              ]"
              density="compact"
            />
          </VCol>
          <VCol cols="12" md="2">
            <VBtn variant="tonal" color="secondary" block @click="searchQuery = ''; statusFilter = 'all'">
              <VIcon icon="tabler-refresh" />
            </VBtn>
          </VCol>
        </VRow>
      </VCardText>
    </VCard>

    <!-- Loading -->
    <div v-if="isLoading" class="d-flex flex-column align-center justify-center py-16">
      <VProgressCircular indeterminate color="primary" size="48" />
    </div>

    <template v-else>
      <VCard v-if="paginatedOrders.length > 0">
        <VTable class="text-no-wrap">
          <thead>
            <tr>
              <th>Réf.</th>
              <th>Événement</th>
              <th>Date commande</th>
              <th>Montant</th>
              <th>Statut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="order in paginatedOrders" :key="order.id">
              <td>
                <code class="text-caption font-weight-bold">#{{ order.id }}</code>
              </td>
              <td>
                <div class="d-flex align-center gap-3 py-2">
                  <VAvatar color="primary" variant="tonal" size="36" rounded>
                    <VIcon icon="tabler-calendar-event" size="18" />
                  </VAvatar>
                  <p class="text-body-2 font-weight-medium mb-0">
                    {{ order.event_title || order.event?.title || '-' }}
                  </p>
                </div>
              </td>
              <td>
                <p class="text-body-2 mb-0">{{ formatDate(order.created_at) }}</p>
              </td>
              <td>
                <p class="text-body-2 font-weight-bold mb-0">
                  {{ formatPrice(order.total_price || order.total_amount || order.amount) }}
                </p>
              </td>
              <td>
                <VChip
                  :color="getStatusConfig(order.payment_status).color"
                  size="small"
                  variant="tonal"
                >
                  <VIcon :icon="getStatusConfig(order.payment_status).icon" size="14" start />
                  {{ getStatusConfig(order.payment_status).label }}
                </VChip>
              </td>
              <td>
                <div class="d-flex gap-1">
                  <!-- Détails -->
                  <VBtn icon variant="text" size="small" color="primary" @click="viewOrder(order)">
                    <VIcon icon="tabler-eye" size="18" />
                    <VTooltip activator="parent">Détails</VTooltip>
                  </VBtn>
                  <!-- 🎟️ Voir billet (seulement si payée) -->
                  <VBtn
                    v-if="Number(order.payment_status) === 1"
                    icon variant="text" size="small" color="success"
                    @click="viewTicket(order)"
                  >
                    <VIcon icon="tabler-ticket" size="18" />
                    <VTooltip activator="parent">Voir mon billet</VTooltip>
                  </VBtn>
                  <!-- Annuler (seulement si en attente) -->
                  <VBtn
                    v-if="Number(order.payment_status) === 0"
                    icon variant="text" size="small" color="error"
                    @click="cancelOrder(order)"
                  >
                    <VIcon icon="tabler-x" size="18" />
                    <VTooltip activator="parent">Annuler</VTooltip>
                  </VBtn>
                </div>
              </td>
            </tr>
          </tbody>
        </VTable>

        <VDivider />

        <VCardText class="d-flex justify-space-between align-center">
          <p class="text-body-2 text-medium-emphasis mb-0">
            {{ filteredOrders.length }} réservation(s)
          </p>
          <div class="d-flex align-center gap-2">
            <VBtn variant="outlined" size="small" :disabled="currentPage <= 1" @click="currentPage--">Précédent</VBtn>
            <VChip size="small" color="primary" variant="tonal">{{ currentPage }} / {{ totalPages }}</VChip>
            <VBtn variant="outlined" size="small" :disabled="currentPage >= totalPages" @click="currentPage++">Suivant</VBtn>
          </div>
        </VCardText>
      </VCard>

      <!-- Empty -->
      <VCard v-else class="text-center py-16">
        <VAvatar color="primary" variant="tonal" size="80" class="mb-4">
          <VIcon icon="tabler-ticket-off" size="40" />
        </VAvatar>
        <h5 class="text-h5 font-weight-bold mb-2">Aucune réservation</h5>
        <p class="text-body-1 text-medium-emphasis mb-4">Vous n'avez pas encore réservé de billets</p>
        <VBtn color="primary" prepend-icon="tabler-calendar-event" to="/">
          Découvrir les événements
        </VBtn>
      </VCard>
    </template>

    <!-- ── MODALE DÉTAIL ── -->
    <VDialog v-model="showDetail" max-width="550">
      <VCard v-if="selectedOrder">
        <VCardTitle class="d-flex justify-space-between align-center pa-6">
          <span class="text-h6 font-weight-bold">Réservation #{{ selectedOrder.id }}</span>
          <VBtn icon variant="text" size="small" @click="showDetail = false">
            <VIcon icon="tabler-x" />
          </VBtn>
        </VCardTitle>
        <VDivider />
        <VCardText class="pa-6">
          <div class="d-flex align-center gap-3 mb-6">
            <VAvatar color="primary" variant="tonal" size="56" rounded>
              <VIcon icon="tabler-calendar-event" size="28" />
            </VAvatar>
            <div>
              <h6 class="text-h6 font-weight-bold">
                {{ selectedOrder.event_title || selectedOrder.event?.title || '-' }}
              </h6>
              <VChip
                :color="getStatusConfig(selectedOrder.payment_status).color"
                size="small" variant="tonal" class="mt-1"
              >
                <VIcon :icon="getStatusConfig(selectedOrder.payment_status).icon" size="14" start />
                {{ getStatusConfig(selectedOrder.payment_status).label }}
              </VChip>
            </div>
          </div>
          <VRow>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Date commande</p>
              <p class="text-body-2 font-weight-medium">{{ formatDate(selectedOrder.created_at) }}</p>
            </VCol>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Montant</p>
              <p class="text-body-2 font-weight-bold text-primary">
                {{ formatPrice(selectedOrder.total_price || selectedOrder.total_amount || selectedOrder.amount) }}
              </p>
            </VCol>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Quantité</p>
              <p class="text-body-2 font-weight-medium">{{ selectedOrder.quantity || 1 }} billet(s)</p>
            </VCol>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Référence</p>
              <code class="text-body-2">#{{ selectedOrder.id }}</code>
            </VCol>
          </VRow>
        </VCardText>
        <VDivider />
        <VCardActions class="pa-6">
          <VSpacer />
          <VBtn variant="outlined" @click="showDetail = false">Fermer</VBtn>
          <!-- Bouton voir billet si payée -->
          <VBtn
            v-if="Number(selectedOrder.payment_status) === 1"
            color="success" variant="tonal"
            prepend-icon="tabler-ticket"
            @click="showDetail = false; viewTicket(selectedOrder)"
          >
            Voir mon billet
          </VBtn>
          <VBtn
            v-if="Number(selectedOrder.payment_status) === 0"
            color="error" variant="tonal"
            prepend-icon="tabler-x"
            @click="showDetail = false; cancelOrder(selectedOrder)"
          >
            Annuler
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- ── MODALE BILLET QR CODE ── -->
    <VDialog v-model="showTicket" max-width="620">
      <VCard v-if="selectedOrder" class="ticket-modal">
        <VCardTitle class="d-flex justify-space-between align-center pa-5">
          <div class="d-flex align-center gap-2">
            <VIcon icon="tabler-ticket" color="primary" />
            <span class="text-h6 font-weight-bold">Mon Billet</span>
          </div>
          <VBtn icon variant="text" size="small" @click="showTicket = false">
            <VIcon icon="tabler-x" />
          </VBtn>
        </VCardTitle>
        <VDivider />

        <!-- Billet stylisé -->
        <div class="ticket-body" id="ticket-print">
          <div class="ticket-inner">
            <!-- Partie gauche -->
            <div class="ticket-left">
              <!-- Date badge + event -->
              <div class="ticket-event">
                <div class="ticket-date-badge">
                  <span class="ticket-day">{{ getEventDate(selectedOrder).day }}</span>
                  <span class="ticket-month">{{ getEventDate(selectedOrder).month }}</span>
                  <span class="ticket-year">{{ getEventDate(selectedOrder).year }}</span>
                </div>
                <div class="ticket-event-info">
                  <div class="ticket-event-label">ÉVÉNEMENT</div>
                  <div class="ticket-event-name">
                    {{ selectedOrder.event_title || selectedOrder.event?.title || 'Événement' }}
                  </div>
                  <div v-if="selectedOrder.event?.location" class="ticket-event-meta">
                    <VIcon icon="tabler-map-pin" size="12" />
                    {{ selectedOrder.event.location }}
                  </div>
                </div>
              </div>

              <!-- Séparateur -->
              <div class="ticket-divider">
                <div class="ticket-notch ticket-notch-l"></div>
                <div class="ticket-dash"></div>
                <div class="ticket-notch ticket-notch-r"></div>
              </div>

              <!-- Détails -->
              <div class="ticket-details">
                <div class="ticket-detail">
                  <div class="ticket-detail-label">COMMANDE</div>
                  <div class="ticket-detail-value">#{{ selectedOrder.id }}</div>
                </div>
                <div class="ticket-detail">
                  <div class="ticket-detail-label">QUANTITÉ</div>
                  <div class="ticket-detail-value">{{ selectedOrder.quantity || 1 }} billet(s)</div>
                </div>
                <div class="ticket-detail">
                  <div class="ticket-detail-label">MONTANT</div>
                  <div class="ticket-detail-value ticket-detail-pink">
                    {{ formatPrice(selectedOrder.total_price || selectedOrder.total_amount) }}
                  </div>
                </div>
                <div class="ticket-detail">
                  <div class="ticket-detail-label">STATUT</div>
                  <div class="ticket-detail-value" style="color:#059669">✓ Payé</div>
                </div>
              </div>
            </div>

            <!-- Partie droite : QR Code -->
            <div class="ticket-qr-side">
              <div class="ticket-qr-box">
                <img :src="ticketQrUrl" alt="QR Code" class="ticket-qr-img" />
              </div>
              <div class="ticket-qr-label">Scanner à l'entrée</div>
              <div class="ticket-num">
                <div class="ticket-num-label">BILLET</div>
                <div class="ticket-num-value">#{{ String(selectedOrder.id).padStart(3,'0') }}</div>
              </div>
            </div>
          </div>

          <!-- Barcode -->
          <div class="ticket-barcode">
            <div class="ticket-bars">
              <div
                v-for="b in 55" :key="b"
                class="ticket-bar"
                :style="{ height: ((b * 13 % 23) + 12) + 'px', opacity: (b * 7 % 5) * 0.1 + 0.5 }"
              />
            </div>
            <div class="ticket-barcode-text">
              EVL-{{ String(selectedOrder.id).padStart(8,'0') }}-{{ new Date().getFullYear() }}
            </div>
          </div>
        </div>

        <VDivider />
        <VCardActions class="pa-5">
          <p class="text-caption text-medium-emphasis mb-0">
            <VIcon icon="tabler-info-circle" size="14" class="me-1" />
            Présentez ce QR code à l'entrée
          </p>
          <VSpacer />
          <VBtn variant="outlined" @click="showTicket = false">Fermer</VBtn>
          <VBtn color="primary" prepend-icon="tabler-download" @click="printTicket">
            Télécharger
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </div>
</template>

<style scoped>
/* ── TICKET MODAL ── */
.ticket-body {
  background: #fff;
  padding: 0;
}
.ticket-inner {
  display: grid;
  grid-template-columns: 1fr 160px;
  min-height: 210px;
  background: #fff;
}
.ticket-left {
  padding: 24px 24px 20px;
  display: flex;
  flex-direction: column;
}
.ticket-event {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  margin-bottom: 16px;
}
.ticket-date-badge {
  background: linear-gradient(135deg, #e8405a, #c4184a);
  border-radius: 12px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  box-shadow: 0 4px 14px rgba(232,64,90,0.3);
}
.ticket-day   { font-size: 24px; font-weight: 800; color: #fff; line-height: 1; }
.ticket-month { font-size: 10px; font-weight: 700; color: rgba(255,255,255,0.85); letter-spacing: 1px; margin-top: 2px; }
.ticket-year  { font-size: 9px; font-weight: 600; color: rgba(255,255,255,0.6); }
.ticket-event-info { flex: 1; }
.ticket-event-label {
  font-size: 9px;
  font-weight: 700;
  color: #e8405a;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  margin-bottom: 4px;
}
.ticket-event-name {
  font-size: 16px;
  font-weight: 800;
  color: #3d2c35;
  line-height: 1.25;
  margin-bottom: 6px;
}
.ticket-event-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #b08090;
}

/* Divider */
.ticket-divider {
  display: flex;
  align-items: center;
  margin: 12px 0;
}
.ticket-notch {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #f5f5f5;
  border: 1px solid #eee;
  flex-shrink: 0;
}
.ticket-notch-l { margin-left: -35px; }
.ticket-notch-r { margin-right: -35px; }
.ticket-dash {
  flex: 1;
  border-top: 2px dashed #f0e4e9;
  margin: 0 4px;
}

/* Details */
.ticket-details {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}
.ticket-detail-label {
  font-size: 8px;
  font-weight: 700;
  color: #c5a8b5;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 3px;
}
.ticket-detail-value {
  font-size: 11px;
  font-weight: 700;
  color: #3d2c35;
}
.ticket-detail-pink { color: #e8405a; }

/* QR Side */
.ticket-qr-side {
  background: linear-gradient(160deg, #fff8fa, #fef0f4);
  border-left: 2px dashed #f5dce5;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px 14px;
  gap: 8px;
}
.ticket-qr-box {
  background: #fff;
  border-radius: 12px;
  padding: 8px;
  box-shadow: 0 4px 14px rgba(232,64,90,0.1);
  border: 1px solid #f5dce5;
}
.ticket-qr-img { width: 100px; height: 100px; display: block; }
.ticket-qr-label {
  font-size: 9px;
  font-weight: 600;
  color: #c5a8b5;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  text-align: center;
}
.ticket-num { text-align: center; }
.ticket-num-label {
  font-size: 8px;
  font-weight: 700;
  color: #c5a8b5;
  text-transform: uppercase;
  letter-spacing: 1px;
}
.ticket-num-value {
  font-size: 16px;
  font-weight: 700;
  color: #e8405a;
  font-family: monospace;
}

/* Barcode */
.ticket-barcode {
  background: linear-gradient(135deg, #5d3a48, #3d2c35);
  padding: 10px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.ticket-bars { display: flex; align-items: flex-end; gap: 2px; height: 32px; }
.ticket-bar  { width: 2px; background: rgba(255,255,255,0.65); border-radius: 1px; }
.ticket-barcode-text {
  font-size: 9px;
  color: rgba(255,255,255,0.45);
  letter-spacing: 2px;
  text-transform: uppercase;
  font-family: monospace;
}

/* Print */
@media print {
  .v-dialog .v-card-title,
  .v-dialog .v-divider,
  .v-dialog .v-card-actions { display: none !important; }
}

@media (max-width: 500px) {
  .ticket-inner { grid-template-columns: 1fr; }
  .ticket-qr-side { border-left: none; border-top: 2px dashed #f5dce5; flex-direction: row; justify-content: space-around; }
  .ticket-details { grid-template-columns: repeat(2, 1fr); }
}
</style>