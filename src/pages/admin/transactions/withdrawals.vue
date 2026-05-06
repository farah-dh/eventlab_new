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
const withdrawals = ref<any[]>([])
const searchQuery = ref('')
const statusFilter = ref('all')
const currentPage = ref(1)
const perPage = ref(10)

const successMessage = ref('')
const errorMessage = ref('')
const showSuccess = (m: string) => { successMessage.value = m; setTimeout(() => successMessage.value = '', 4000) }
const showError = (m: string) => { errorMessage.value = m; setTimeout(() => errorMessage.value = '', 5000) }

// Modals
const showModal = ref(false)
const selectedWithdrawal = ref<any>({})
const showApproveDialog = ref(false)
const showRejectDialog = ref(false)
const itemToProcess = ref<any>(null)
const adminFeedback = ref('')
const isProcessing = ref(false)

// Status: 1=Pending, 2=Approved, 3=Rejected (à ajuster si besoin)
const statusMap: Record<number, { label: string; color: string; icon: string }> = {
  1: { label: 'En attente', color: 'warning', icon: 'tabler-clock' },
  2: { label: 'Approuvé', color: 'success', icon: 'tabler-check' },
  3: { label: 'Rejeté', color: 'error', icon: 'tabler-x' },
}

// ─── Fetch ───
const fetchWithdrawals = async () => {
  isLoading.value = true
  try {
    const data = await apiFetch('/orders/withdrawals/')
    const results = data.results || data.data || data || []
    withdrawals.value = Array.isArray(results) ? results : []
  } catch (err) {
    console.error(err)
    withdrawals.value = []
  } finally {
    isLoading.value = false
  }
}

// ─── Filtering ───
const filteredWithdrawals = computed(() => {
  let result = [...withdrawals.value]
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(w =>
      String(w.id).includes(q)
      || w.method_name?.toLowerCase().includes(q)
      || w.trx?.toLowerCase().includes(q)
      || w.withdraw_information?.toLowerCase().includes(q),
    )
  }
  if (statusFilter.value !== 'all')
    result = result.filter(w => String(w.status) === statusFilter.value)
  return result
})

const paginatedWithdrawals = computed(() => {
  const start = (currentPage.value - 1) * perPage.value
  return filteredWithdrawals.value.slice(start, start + perPage.value)
})

const totalPages = computed(() => Math.ceil(filteredWithdrawals.value.length / perPage.value) || 1)

// ─── Stats ───
const pendingCount = computed(() => withdrawals.value.filter(w => w.status === 1).length)
const approvedCount = computed(() => withdrawals.value.filter(w => w.status === 2).length)
const rejectedCount = computed(() => withdrawals.value.filter(w => w.status === 3).length)
const totalAmount = computed(() => withdrawals.value.reduce((s, w) => s + Math.abs(Number(w.amount || 0)), 0))
const pendingAmount = computed(() =>
  withdrawals.value.filter(w => w.status === 1).reduce((s, w) => s + Math.abs(Number(w.amount || 0)), 0),
)

const kpiCards = computed(() => [
  { title: 'Total retraits', value: withdrawals.value.length, icon: 'tabler-cash', color: 'primary' },
  { title: 'En attente', value: pendingCount.value, icon: 'tabler-clock', color: 'warning' },
  { title: 'Approuvés', value: approvedCount.value, icon: 'tabler-check', color: 'success' },
  { title: 'Rejetés', value: rejectedCount.value, icon: 'tabler-x', color: 'error' },
  { title: 'Montant en attente', value: formatCurrency(pendingAmount.value), icon: 'tabler-currency-dollar', color: 'info' },
])

// ─── Helpers ───
function formatCurrency(a: any): string {
  return `${Math.abs(Number(a || 0)).toFixed(3)} DT`
}

function formatDate(d: string | null): string {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function getStatus(s: number) {
  return statusMap[s] || { label: 'Inconnu', color: 'default', icon: 'tabler-help' }
}

// ─── Actions ───
const viewWithdrawal = (w: any) => {
  selectedWithdrawal.value = w
  showModal.value = true
}

const askApprove = (w: any) => {
  itemToProcess.value = w
  adminFeedback.value = ''
  showApproveDialog.value = true
}

const askReject = (w: any) => {
  itemToProcess.value = w
  adminFeedback.value = ''
  showRejectDialog.value = true
}

const approveWithdrawal = async () => {
  if (!itemToProcess.value) return
  isProcessing.value = true
  try {
    await apiFetch(`/orders/withdrawals/${itemToProcess.value.id}/approve/`, {
      method: 'POST',
      body: JSON.stringify({ admin_feedback: adminFeedback.value }),
    })
    showApproveDialog.value = false
    showSuccess(`✅ Retrait #${itemToProcess.value.id} approuvé.`)
    itemToProcess.value = null
    await fetchWithdrawals()
  } catch (err) { showError('❌ Erreur lors de l\'approbation.'); console.error(err) }
  finally { isProcessing.value = false }
}

const rejectWithdrawal = async () => {
  if (!itemToProcess.value) return
  if (!adminFeedback.value) {
    showError('Veuillez indiquer un motif de rejet.')
    return
  }
  isProcessing.value = true
  try {
    await apiFetch(`/orders/withdrawals/${itemToProcess.value.id}/reject/`, {
      method: 'POST',
      body: JSON.stringify({ admin_feedback: adminFeedback.value }),
    })
    showRejectDialog.value = false
    showSuccess(`❌ Retrait #${itemToProcess.value.id} rejeté.`)
    itemToProcess.value = null
    await fetchWithdrawals()
  } catch (err) { showError('❌ Erreur lors du rejet.'); console.error(err) }
  finally { isProcessing.value = false }
}

const resetFilters = () => {
  searchQuery.value = ''
  statusFilter.value = 'all'
  currentPage.value = 1
}

onMounted(fetchWithdrawals)
</script>

<template>
  <div>
    <!-- Header -->
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h4 class="text-h4 font-weight-bold">Retraits</h4>
        <p class="text-body-1 text-medium-emphasis mt-1">
          Gérez les demandes de retrait des organisateurs
        </p>
      </div>
      <VBtn color="primary" variant="outlined" prepend-icon="tabler-refresh" @click="fetchWithdrawals">
        Actualiser
      </VBtn>
    </div>

    <!-- Notifications -->
    <VAlert v-if="successMessage" type="success" variant="tonal" closable class="mb-4" @click:close="successMessage = ''">
      {{ successMessage }}
    </VAlert>
    <VAlert v-if="errorMessage" type="error" variant="tonal" closable class="mb-4" @click:close="errorMessage = ''">
      {{ errorMessage }}
    </VAlert>

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
              placeholder="Rechercher par ID, méthode, TRX..."
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
                { title: 'Tous statuts', value: 'all' },
                { title: 'En attente', value: '1' },
                { title: 'Approuvés', value: '2' },
                { title: 'Rejetés', value: '3' },
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
      <p class="text-body-1 text-medium-emphasis mt-4">Chargement des retraits...</p>
    </div>

    <!-- Table -->
    <VCard v-else>
      <VTable class="text-no-wrap">
        <thead>
          <tr>
            <th>ID</th>
            <th>Méthode</th>
            <th>Montant</th>
            <th>Frais</th>
            <th>Montant final</th>
            <th>TRX</th>
            <th>Statut</th>
            <th>Date</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="w in paginatedWithdrawals" :key="w.id">
            <td><code class="text-caption">#{{ w.id }}</code></td>
            <td>
              <p class="text-body-2 font-weight-medium mb-0">{{ w.method_name || '-' }}</p>
            </td>
            <td>
              <p class="text-body-2 font-weight-bold mb-0">{{ formatCurrency(w.amount) }} {{ w.currency || '' }}</p>
            </td>
            <td>
              <p class="text-body-2 text-warning mb-0">{{ formatCurrency(w.charge) }}</p>
            </td>
            <td>
              <p class="text-body-2 text-success font-weight-bold mb-0">{{ formatCurrency(w.final_amount) }}</p>
            </td>
            <td>
              <code class="text-caption">{{ w.trx || '-' }}</code>
            </td>
            <td>
              <VChip :color="getStatus(w.status).color" size="small" variant="tonal">
                <VIcon :icon="getStatus(w.status).icon" size="14" start />
                {{ getStatus(w.status).label }}
              </VChip>
            </td>
            <td>
              <p class="text-caption mb-0">{{ formatDate(w.created_at) }}</p>
            </td>
            <td>
              <div class="d-flex gap-1">
                <VBtn icon variant="text" size="small" color="primary" @click="viewWithdrawal(w)">
                  <VIcon icon="tabler-eye" size="18" />
                  <VTooltip activator="parent">Voir</VTooltip>
                </VBtn>
                <VBtn
                  v-if="w.status === 1"
                  icon variant="text" size="small" color="success"
                  @click="askApprove(w)"
                >
                  <VIcon icon="tabler-check" size="18" />
                  <VTooltip activator="parent">Approuver</VTooltip>
                </VBtn>
                <VBtn
                  v-if="w.status === 1"
                  icon variant="text" size="small" color="error"
                  @click="askReject(w)"
                >
                  <VIcon icon="tabler-x" size="18" />
                  <VTooltip activator="parent">Rejeter</VTooltip>
                </VBtn>
              </div>
            </td>
          </tr>
          <tr v-if="paginatedWithdrawals.length === 0">
            <td colspan="9" class="text-center py-8">
              <VIcon icon="tabler-cash-off" size="48" color="disabled" class="mb-2" />
              <p class="text-body-1 text-medium-emphasis">Aucun retrait trouvé</p>
            </td>
          </tr>
        </tbody>
      </VTable>

      <VDivider />

      <VCardText class="d-flex justify-space-between align-center flex-wrap">
        <p class="text-body-2 text-medium-emphasis mb-0">
          Affichage {{ Math.min((currentPage - 1) * perPage + 1, filteredWithdrawals.length) }}
          à {{ Math.min(currentPage * perPage, filteredWithdrawals.length) }}
          sur {{ filteredWithdrawals.length }} retraits
        </p>
        <div class="d-flex align-center gap-2">
          <VBtn variant="outlined" size="small" :disabled="currentPage <= 1" @click="currentPage--">Précédent</VBtn>
          <VChip size="small" color="primary" variant="tonal">{{ currentPage }} / {{ totalPages }}</VChip>
          <VBtn variant="outlined" size="small" :disabled="currentPage >= totalPages" @click="currentPage++">Suivant</VBtn>
        </div>
      </VCardText>
    </VCard>

    <!-- Modal détails -->
    <VDialog v-model="showModal" max-width="600">
      <VCard>
        <VCardTitle class="d-flex justify-space-between align-center pa-6">
          <span class="text-h6 font-weight-bold">Détail du retrait #{{ selectedWithdrawal.id }}</span>
          <VBtn icon variant="text" size="small" @click="showModal = false">
            <VIcon icon="tabler-x" />
          </VBtn>
        </VCardTitle>
        <VDivider />
        <VCardText class="pa-6">
          <VRow>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Méthode</p>
              <p class="text-body-2 font-weight-medium">{{ selectedWithdrawal.method_name || '-' }}</p>
            </VCol>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Statut</p>
              <VChip :color="getStatus(selectedWithdrawal.status).color" size="small" variant="tonal">
                {{ getStatus(selectedWithdrawal.status).label }}
              </VChip>
            </VCol>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">TRX</p>
              <code class="text-body-2">{{ selectedWithdrawal.trx || '-' }}</code>
            </VCol>
            <VCol cols="6">
              <p class="text-caption text-medium-emphasis mb-1">Date</p>
              <p class="text-body-2">{{ formatDate(selectedWithdrawal.created_at) }}</p>
            </VCol>
            <VCol cols="12">
              <p class="text-caption text-medium-emphasis mb-1">Informations de retrait</p>
              <div class="pa-3" style="background: rgba(0,0,0,0.03); border-radius: 6px;">
                <p class="text-body-2 mb-0" style="white-space: pre-wrap">{{ selectedWithdrawal.withdraw_information || '-' }}</p>
              </div>
            </VCol>
            <VCol v-if="selectedWithdrawal.admin_feedback" cols="12">
              <p class="text-caption text-medium-emphasis mb-1">Commentaire admin</p>
              <div class="pa-3" style="background: rgba(0,0,0,0.03); border-radius: 6px;">
                <p class="text-body-2 mb-0">{{ selectedWithdrawal.admin_feedback }}</p>
              </div>
            </VCol>
          </VRow>

          <VDivider class="my-4" />

          <VCard color="info" variant="tonal">
            <VCardText>
              <h6 class="text-subtitle-1 font-weight-bold mb-3">
                <VIcon icon="tabler-currency-dollar" size="18" class="me-1" />
                Récapitulatif financier
              </h6>
              <VRow>
                <VCol cols="4" class="text-center">
                  <p class="text-caption text-medium-emphasis mb-1">Montant demandé</p>
                  <p class="text-h6 font-weight-bold mb-0">{{ formatCurrency(selectedWithdrawal.amount) }}</p>
                </VCol>
                <VCol cols="4" class="text-center">
                  <p class="text-caption text-medium-emphasis mb-1">Frais</p>
                  <p class="text-h6 font-weight-bold text-warning mb-0">{{ formatCurrency(selectedWithdrawal.charge) }}</p>
                </VCol>
                <VCol cols="4" class="text-center">
                  <p class="text-caption text-medium-emphasis mb-1">Final</p>
                  <p class="text-h6 font-weight-bold text-success mb-0">{{ formatCurrency(selectedWithdrawal.final_amount) }}</p>
                </VCol>
              </VRow>
            </VCardText>
          </VCard>
        </VCardText>
        <VDivider />
        <VCardActions class="pa-6">
          <VSpacer />
          <VBtn variant="outlined" @click="showModal = false">Fermer</VBtn>
          <VBtn v-if="selectedWithdrawal.status === 1" color="success" prepend-icon="tabler-check" @click="showModal = false; askApprove(selectedWithdrawal)">
            Approuver
          </VBtn>
          <VBtn v-if="selectedWithdrawal.status === 1" color="error" prepend-icon="tabler-x" @click="showModal = false; askReject(selectedWithdrawal)">
            Rejeter
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Dialog approuver -->
    <VDialog v-model="showApproveDialog" max-width="500" persistent>
      <VCard>
        <VCardText class="pa-6">
          <div class="d-flex align-center gap-3 mb-4">
            <VAvatar color="success" variant="tonal" size="48">
              <VIcon icon="tabler-check" size="24" />
            </VAvatar>
            <div>
              <h5 class="text-h6 font-weight-bold mb-0">Approuver le retrait</h5>
              <p class="text-caption text-medium-emphasis mb-0">Retrait #{{ itemToProcess?.id }} — {{ formatCurrency(itemToProcess?.amount) }}</p>
            </div>
          </div>
          <VTextarea
            v-model="adminFeedback"
            label="Commentaire (optionnel)"
            placeholder="Ex: Virement effectué le 17/04/2026"
            rows="3"
          />
        </VCardText>
        <VDivider />
        <VCardActions class="pa-4">
          <VSpacer />
          <VBtn variant="outlined" @click="showApproveDialog = false">Annuler</VBtn>
          <VBtn color="success" :loading="isProcessing" prepend-icon="tabler-check" @click="approveWithdrawal">
            Approuver
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Dialog rejeter -->
    <VDialog v-model="showRejectDialog" max-width="500" persistent>
      <VCard>
        <VCardText class="pa-6">
          <div class="d-flex align-center gap-3 mb-4">
            <VAvatar color="error" variant="tonal" size="48">
              <VIcon icon="tabler-x" size="24" />
            </VAvatar>
            <div>
              <h5 class="text-h6 font-weight-bold mb-0">Rejeter le retrait</h5>
              <p class="text-caption text-medium-emphasis mb-0">Retrait #{{ itemToProcess?.id }} — {{ formatCurrency(itemToProcess?.amount) }}</p>
            </div>
          </div>
          <VTextarea
            v-model="adminFeedback"
            label="Motif du rejet *"
            placeholder="Ex: Informations bancaires incorrectes"
            rows="3"
            :error-messages="!adminFeedback && isProcessing ? 'Obligatoire' : ''"
          />
        </VCardText>
        <VDivider />
        <VCardActions class="pa-4">
          <VSpacer />
          <VBtn variant="outlined" @click="showRejectDialog = false">Annuler</VBtn>
          <VBtn color="error" :loading="isProcessing" prepend-icon="tabler-x" @click="rejectWithdrawal">
            Rejeter
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </div>
</template>