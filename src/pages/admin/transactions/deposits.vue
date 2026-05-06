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
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json()
}

const isLoading = ref(true)
const transactions = ref<any[]>([])
const searchQuery = ref('')
const typeFilter = ref('+')
const currentPage = ref(1)
const perPage = ref(10)

const showModal = ref(false)
const selectedTx = ref<any>({})

const fetchTransactions = async () => {
  isLoading.value = true
  try {
    const data = await apiFetch('/orders/transactions/')
    const results = data.results || data.data || data || []
    transactions.value = Array.isArray(results) ? results : []
  } catch (err) {
    console.error(err)
    transactions.value = []
  } finally {
    isLoading.value = false
  }
}

const filteredTransactions = computed(() => {
  let result = [...transactions.value]
  if (typeFilter.value !== 'all')
    result = result.filter(t => t.trx_type === typeFilter.value)
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(t =>
      t.trx?.toLowerCase().includes(q)
      || t.details?.toLowerCase().includes(q)
      || t.remark?.toLowerCase().includes(q),
    )
  }
  return result
})

const paginatedTransactions = computed(() => {
  const start = (currentPage.value - 1) * perPage.value
  return filteredTransactions.value.slice(start, start + perPage.value)
})

const totalPages = computed(() => Math.ceil(filteredTransactions.value.length / perPage.value) || 1)

// Stats
const depositsCount = computed(() => transactions.value.filter(t => t.trx_type === '+').length)
const debitsCount = computed(() => transactions.value.filter(t => t.trx_type === '-').length)
const totalDeposits = computed(() =>
  transactions.value.filter(t => t.trx_type === '+').reduce((s, t) => s + Math.abs(Number(t.amount || 0)), 0),
)
const totalDebits = computed(() =>
  transactions.value.filter(t => t.trx_type === '-').reduce((s, t) => s + Math.abs(Number(t.amount || 0)), 0),
)
const totalCharges = computed(() =>
  transactions.value.reduce((s, t) => s + Math.abs(Number(t.charge || 0)), 0),
)

const kpiCards = computed(() => [
  { title: 'Total mouvements', value: transactions.value.length, icon: 'tabler-list', color: 'primary' },
  { title: 'Crédits (+)', value: depositsCount.value, icon: 'tabler-arrow-down-circle', color: 'success' },
  { title: 'Débits (-)', value: debitsCount.value, icon: 'tabler-arrow-up-circle', color: 'error' },
  { title: 'Total crédits', value: formatCurrency(totalDeposits.value), icon: 'tabler-currency-dollar', color: 'info' },
  { title: 'Total frais', value: formatCurrency(totalCharges.value), icon: 'tabler-percentage', color: 'warning' },
])

function formatCurrency(a: any): string {
  return `${Math.abs(Number(a || 0)).toFixed(3)} DT`
}

function formatDate(d: string | null): string {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const viewTx = (t: any) => {
  selectedTx.value = t
  showModal.value = true
}

const resetFilters = () => {
  searchQuery.value = ''
  typeFilter.value = '+'
  currentPage.value = 1
}

onMounted(fetchTransactions)
</script>

<template>
  <div>
    <!-- Header -->
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h4 class="text-h4 font-weight-bold">Dépôts & Mouvements</h4>
        <p class="text-body-1 text-medium-emphasis mt-1">
          Historique des mouvements financiers sur la plateforme
        </p>
      </div>
      <VBtn color="primary" variant="outlined" prepend-icon="tabler-refresh" @click="fetchTransactions">
        Actualiser
      </VBtn>
    </div>

    <!-- KPI -->
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
          <VCol cols="12" md="5">
            <VTextField
              v-model="searchQuery"
              placeholder="Rechercher par TRX, détails, remarque..."
              prepend-inner-icon="tabler-search"
              density="compact"
              clearable
              @update:model-value="currentPage = 1"
            />
          </VCol>
          <VCol cols="12" md="4">
            <VSelect
              v-model="typeFilter"
              :items="[
                { title: 'Tous', value: 'all' },
                { title: 'Crédits (+)', value: '+' },
                { title: 'Débits (-)', value: '-' },
              ]"
              density="compact"
            />
          </VCol>
          <VCol cols="12" md="3">
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
      <p class="text-body-1 text-medium-emphasis mt-4">Chargement...</p>
    </div>

    <!-- Table -->
    <VCard v-else>
      <VTable class="text-no-wrap">
        <thead>
          <tr>
            <th>ID</th>
            <th>Type</th>
            <th>Montant</th>
            <th>Frais</th>
            <th>Solde après</th>
            <th>TRX</th>
            <th>Détails</th>
            <th>Date</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in paginatedTransactions" :key="t.id">
            <td><code class="text-caption">#{{ t.id }}</code></td>
            <td>
              <VChip :color="t.trx_type === '+' ? 'success' : 'error'" size="small" variant="tonal">
                <VIcon :icon="t.trx_type === '+' ? 'tabler-arrow-down' : 'tabler-arrow-up'" size="14" start />
                {{ t.trx_type === '+' ? 'Crédit' : 'Débit' }}
              </VChip>
            </td>
            <td>
              <p :class="['text-body-2', 'font-weight-bold', 'mb-0', t.trx_type === '+' ? 'text-success' : 'text-error']">
                {{ t.trx_type }}{{ formatCurrency(t.amount) }}
              </p>
            </td>
            <td>
              <p class="text-body-2 text-warning mb-0">{{ formatCurrency(t.charge) }}</p>
            </td>
            <td>
              <p class="text-body-2 font-weight-medium mb-0">{{ formatCurrency(t.post_balance) }}</p>
            </td>
            <td>
              <code class="text-caption">{{ t.trx || '-' }}</code>
            </td>
            <td>
              <p class="text-body-2 mb-0" style="max-inline-size: 200px; overflow: hidden; text-overflow: ellipsis;">
                {{ t.details || '-' }}
              </p>
            </td>
            <td>
              <p class="text-caption mb-0">{{ formatDate(t.created_at) }}</p>
            </td>
            <td>
              <VBtn icon variant="text" size="small" color="primary" @click="viewTx(t)">
                <VIcon icon="tabler-eye" size="18" />
                <VTooltip activator="parent">Voir</VTooltip>
              </VBtn>
            </td>
          </tr>
          <tr v-if="paginatedTransactions.length === 0">
            <td colspan="9" class="text-center py-8">
              <VIcon icon="tabler-receipt-off" size="48" color="disabled" class="mb-2" />
              <p class="text-body-1 text-medium-emphasis">Aucun mouvement trouvé</p>
            </td>
          </tr>
        </tbody>
      </VTable>

      <VDivider />

      <VCardText class="d-flex justify-space-between align-center flex-wrap">
        <p class="text-body-2 text-medium-emphasis mb-0">
          Affichage {{ Math.min((currentPage - 1) * perPage + 1, filteredTransactions.length) }}
          à {{ Math.min(currentPage * perPage, filteredTransactions.length) }}
          sur {{ filteredTransactions.length }} mouvements
        </p>
        <div class="d-flex align-center gap-2">
          <VBtn variant="outlined" size="small" :disabled="currentPage <= 1" @click="currentPage--">Précédent</VBtn>
          <VChip size="small" color="primary" variant="tonal">{{ currentPage }} / {{ totalPages }}</VChip>
          <VBtn variant="outlined" size="small" :disabled="currentPage >= totalPages" @click="currentPage++">Suivant</VBtn>
        </div>
      </VCardText>
    </VCard>

    <!-- Modal détails -->
    <VDialog v-model="showModal" max-width="550">
      <VCard>
        <VCardTitle class="d-flex justify-space-between align-center pa-6">
          <span class="text-h6 font-weight-bold">Détail du mouvement #{{ selectedTx.id }}</span>
          <VBtn icon variant="text" size="small" @click="showModal = false">
            <VIcon icon="tabler-x" />
          </VBtn>
        </VCardTitle>
        <VDivider />
        <VCardText class="pa-6">
          <VRow>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Type</p>
              <VChip :color="selectedTx.trx_type === '+' ? 'success' : 'error'" size="small" variant="tonal">
                {{ selectedTx.trx_type === '+' ? 'Crédit' : 'Débit' }}
              </VChip>
            </VCol>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">TRX</p>
              <code class="text-body-2">{{ selectedTx.trx || '-' }}</code>
            </VCol>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Montant</p>
              <p class="text-body-2 font-weight-bold">{{ selectedTx.trx_type }}{{ formatCurrency(selectedTx.amount) }}</p>
            </VCol>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Frais</p>
              <p class="text-body-2 text-warning">{{ formatCurrency(selectedTx.charge) }}</p>
            </VCol>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Solde après</p>
              <p class="text-body-2 font-weight-bold">{{ formatCurrency(selectedTx.post_balance) }}</p>
            </VCol>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Date</p>
              <p class="text-body-2">{{ formatDate(selectedTx.created_at) }}</p>
            </VCol>
            <VCol v-if="selectedTx.details" cols="12">
              <p class="text-caption text-medium-emphasis mb-1">Détails</p>
              <div class="pa-3" style="background: rgba(0,0,0,0.03); border-radius: 6px;">
                <p class="text-body-2 mb-0">{{ selectedTx.details }}</p>
              </div>
            </VCol>
            <VCol v-if="selectedTx.remark" cols="12">
              <p class="text-caption text-medium-emphasis mb-1">Remarque</p>
              <div class="pa-3" style="background: rgba(0,0,0,0.03); border-radius: 6px;">
                <p class="text-body-2 mb-0">{{ selectedTx.remark }}</p>
              </div>
            </VCol>
          </VRow>
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