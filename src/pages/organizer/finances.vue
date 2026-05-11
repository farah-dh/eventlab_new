<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'

definePage({ meta: { layout: 'organizer' } })

const API      = 'http://127.0.0.1:8001/api/v1'
// ✅ CORRECTION : bonne clé du token
const getToken = () => localStorage.getItem('organizer_token') || ''

const organizer = computed(() => {
  try { return JSON.parse(localStorage.getItem('organizer') || '{}') }
  catch { return {} }
})

// ── State ─────────────────────────────────────────────────────────────────────
const isLoading = ref(true)
const stats     = ref({
  total_revenue:   0,
  total_orders:    0,
  total_tickets:   0,
  pending_revenue: 0,
  paid_revenue:    0,
  this_month:      0,
})
const recentOrders = ref<any[]>([])

// ✅ CORRECTION : gère 1 = payé, 0 = en attente (valeurs numériques de l'API)
const isPaid = (o: any) => {
  if (o.payment_status === 1 || o.status === 1) return true
  const s = String(o.payment_status ?? o.status ?? '').toLowerCase()
  return ['paid', 'completed', 'confirmed', 'success', 'approved'].includes(s)
}

const isPending = (o: any) => {
  if (o.payment_status === 0 || o.status === 0) return true
  const s = String(o.payment_status ?? o.status ?? '').toLowerCase()
  return ['pending', 'waiting', 'processing', 'en_attente'].includes(s)
}

// ── Fetch ─────────────────────────────────────────────────────────────────────
const fetchStats = async () => {
  isLoading.value = true
  try {
    // ✅ CORRECTION : pas besoin de orgId, le token identifie l'organisateur
    const res = await fetch(`${API}/orders/?limit=200`, {
      headers: { Authorization: `Bearer ${getToken()}` },
    })
    if (!res.ok) throw new Error()
    const json = await res.json()
    // ✅ CORRECTION : votre API retourne directement json.results
    const orders: any[] = json.results || json.data?.results || json.data || []

    const total   = orders.reduce((s: number, o: any) => s + parseFloat(o.total_price || o.amount || 0), 0)
    const paid    = orders.filter(isPaid)
    const pending = orders.filter(isPending)

    const now       = new Date()
    const thisMonth = orders.filter((o: any) => {
      const d = new Date(o.created_at)
      return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear()
    })

    stats.value = {
      total_revenue:   total,
      total_orders:    orders.length,
      total_tickets:   orders.reduce((s: number, o: any) => s + (o.quantity || 1), 0),
      paid_revenue:    paid.reduce((s: number, o: any) => s + parseFloat(o.total_price || o.amount || 0), 0),
      pending_revenue: pending.reduce((s: number, o: any) => s + parseFloat(o.total_price || o.amount || 0), 0),
      this_month:      thisMonth.reduce((s: number, o: any) => s + parseFloat(o.total_price || o.amount || 0), 0),
    }

    recentOrders.value = orders.slice(0, 10)

    // DEBUG : voir les statuts réels
    console.log('📦 Statuts des commandes:', orders.map(o => o.status || o.payment_status))

  } catch (e) {
    console.error(e)
  } finally {
    isLoading.value = false
  }
}

const fmt = (n: number) => n.toFixed(2)

const statusColor = (s: any) => {
  if (s === 1) return 'status-paid'
  if (s === 0) return 'status-pending'
  const v = String(s).toLowerCase()
  if (['paid', 'completed', 'confirmed', 'success'].includes(v)) return 'status-paid'
  if (['pending', 'waiting', 'processing'].includes(v)) return 'status-pending'
  return 'status-other'
}

const statusLabel = (s: any) => {
  if (s === 1) return 'Payé'
  if (s === 0) return 'En attente'
  const v = String(s).toLowerCase()
  if (['paid', 'completed', 'confirmed', 'success'].includes(v)) return 'Payé'
  if (['pending', 'waiting', 'processing'].includes(v)) return 'En attente'
  if (['cancelled', 'canceled', 'refunded'].includes(v)) return 'Annulé'
  return String(s) || 'N/A'
}

onMounted(fetchStats)
</script>

<template>
  <div class="finances-page">

    <!-- Header -->
    <div class="page-header">
      <div>
        <h2 class="page-title">Total des ventes</h2>
        <p class="page-sub">Aperçu de vos revenus et transactions</p>
      </div>
      <VBtn color="primary" variant="tonal" size="small" :loading="isLoading" @click="fetchStats">
        <VIcon start icon="tabler-refresh" size="14" />
        Actualiser
      </VBtn>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="center-pad">
      <VProgressCircular indeterminate color="primary" size="36" />
    </div>

    <template v-else>

      <!-- Stats cards -->
      <div class="stats-grid">

        <div class="stat-card stat-card--pink">
          <div class="stat-icon"><VIcon icon="tabler-currency-dollar" size="22" /></div>
          <div class="stat-body">
            <span class="stat-label">Revenu total</span>
            <span class="stat-value">{{ fmt(stats.total_revenue) }} DT</span>
          </div>
        </div>

        <div class="stat-card stat-card--green">
          <div class="stat-icon"><VIcon icon="tabler-circle-check" size="22" /></div>
          <div class="stat-body">
            <span class="stat-label">Paiements reçus</span>
            <span class="stat-value">{{ fmt(stats.paid_revenue) }} DT</span>
          </div>
        </div>

        <div class="stat-card stat-card--orange">
          <div class="stat-icon"><VIcon icon="tabler-clock" size="22" /></div>
          <div class="stat-body">
            <span class="stat-label">En attente</span>
            <span class="stat-value">{{ fmt(stats.pending_revenue) }} DT</span>
          </div>
        </div>

        <div class="stat-card stat-card--blue">
          <div class="stat-icon"><VIcon icon="tabler-calendar-stats" size="22" /></div>
          <div class="stat-body">
            <span class="stat-label">Ce mois-ci</span>
            <span class="stat-value">{{ fmt(stats.this_month) }} DT</span>
          </div>
        </div>

        <div class="stat-card stat-card--purple">
          <div class="stat-icon"><VIcon icon="tabler-receipt" size="22" /></div>
          <div class="stat-body">
            <span class="stat-label">Commandes totales</span>
            <span class="stat-value">{{ stats.total_orders }}</span>
          </div>
        </div>

        <div class="stat-card stat-card--teal">
          <div class="stat-icon"><VIcon icon="tabler-ticket" size="22" /></div>
          <div class="stat-body">
            <span class="stat-label">Billets vendus</span>
            <span class="stat-value">{{ stats.total_tickets }}</span>
          </div>
        </div>

      </div>

      <!-- Recent transactions -->
      <div class="table-card">
        <div class="table-head">
          <div>
            <h3 class="table-title">Transactions récentes</h3>
            <p class="table-sub">Les 10 dernières commandes</p>
          </div>
        </div>

        <div v-if="recentOrders.length === 0" class="empty-state">
          <VIcon icon="tabler-receipt-off" size="40" color="grey-lighten-2" />
          <p>Aucune transaction pour le moment</p>
        </div>

        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Commande</th>
                <th>Événement</th>
                <th>Client</th>
                <th>Montant</th>
                <th>Statut</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in recentOrders" :key="order.id">
                <td><span class="order-id">#{{ order.id }}</span></td>
                <td>{{ order.event?.title || order.event_title || 'N/A' }}</td>
                <td>{{ order.user?.email || order.buyer_email || 'N/A' }}</td>
                <td><strong>{{ fmt(parseFloat(order.total_price || order.amount || 0)) }} DT</strong></td>
                <td>
                  <span :class="['status-badge', statusColor(order.status || order.payment_status)]">
                    {{ statusLabel(order.status || order.payment_status) }}
                  </span>
                </td>
                <td>{{ order.created_at ? new Date(order.created_at).toLocaleDateString('fr-FR') : 'N/A' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </template>
  </div>
</template>

<style scoped lang="scss">
$pink: #C8365F;

.finances-page { display: flex; flex-direction: column; gap: 24px; }
.page-header   { display: flex; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; gap: 12px; }
.page-title    { font-size: 20px; font-weight: 700; color: #1A0510; margin: 0 0 4px; }
.page-sub      { font-size: 13px; color: #9CA3AF; margin: 0; }
.center-pad    { display: flex; justify-content: center; padding: 48px; }

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  @media (max-width: 900px) { grid-template-columns: repeat(2, 1fr); }
  @media (max-width: 600px) { grid-template-columns: 1fr; }
}

.stat-card {
  background: white; border-radius: 14px; padding: 20px;
  border: 0.5px solid #F3D6E0;
  display: flex; align-items: center; gap: 16px;
  position: relative; overflow: hidden;
  transition: transform .15s, box-shadow .15s;
  &:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(200,54,95,0.1); }
}

.stat-icon {
  width: 48px; height: 48px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; color: white;
}

.stat-body   { flex: 1; }
.stat-label  { display: block; font-size: 12px; color: #9CA3AF; margin-bottom: 4px; }
.stat-value  { display: block; font-size: 22px; font-weight: 700; color: #1A0510; }

.stat-card--pink   .stat-icon { background: linear-gradient(135deg, #C8365F, #A82248); }
.stat-card--green  .stat-icon { background: linear-gradient(135deg, #059669, #10B981); }
.stat-card--orange .stat-icon { background: linear-gradient(135deg, #D97706, #F59E0B); }
.stat-card--blue   .stat-icon { background: linear-gradient(135deg, #2563EB, #3B82F6); }
.stat-card--purple .stat-icon { background: linear-gradient(135deg, #7C3AED, #8B5CF6); }
.stat-card--teal   .stat-icon { background: linear-gradient(135deg, #0891B2, #06B6D4); }

.table-card {
  background: white; border-radius: 14px;
  border: 0.5px solid #F3D6E0; overflow: hidden;
}
.table-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 20px 24px; border-bottom: 0.5px solid #F3D6E0;
}
.table-title { font-size: 15px; font-weight: 600; color: #1A0510; margin: 0 0 3px; }
.table-sub   { font-size: 12px; color: #9CA3AF; margin: 0; }

.empty-state {
  display: flex; flex-direction: column; align-items: center;
  gap: 12px; padding: 48px; color: #9CA3AF; font-size: 14px;
}

.table-wrap { overflow-x: auto; }

.data-table {
  width: 100%; border-collapse: collapse;
  th {
    padding: 12px 16px; text-align: left;
    font-size: 11px; font-weight: 700; color: #9CA3AF;
    text-transform: uppercase; letter-spacing: .5px;
    background: #FFF8FA; border-bottom: 0.5px solid #F3D6E0;
  }
  td {
    padding: 14px 16px; font-size: 13.5px; color: #374151;
    border-bottom: 0.5px solid #F9F0F4;
  }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: #FFF8FA; }
}

.order-id { font-weight: 600; color: $pink; font-family: monospace; font-size: 13px; }

.status-badge {
  display: inline-flex; align-items: center;
  padding: 3px 10px; border-radius: 20px;
  font-size: 11.5px; font-weight: 600;
  &.status-paid    { background: #ECFDF5; color: #059669; }
  &.status-pending { background: #FFFBEB; color: #D97706; }
  &.status-other   { background: #F3F4F6; color: #6B7280; }
}
</style>