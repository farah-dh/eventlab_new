<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

definePage({ meta: { layout: 'organizer' } })

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'
const getToken = () => localStorage.getItem('organizer_token') || ''

// ✅ Décoder le token JWT pour avoir l'ID de l'organisateur
const getOrganizerId = (): number | null => {
  try {
    const token = getToken()
    if (!token) return null
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.organizer_id || null
  } catch { return null }
}

const apiFetch = async (endpoint: string, options: RequestInit = {}) => {
  const token = getToken()
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...(options.headers || {}),
    },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.message || err.detail || `Erreur ${res.status}`)
  }
  return res.json()
}

const loading         = ref(true)
const withdrawLoading = ref(false)
const balance         = ref('0.00')
const methods         = ref<any[]>([])
const withdrawals     = ref<any[]>([])
const snackbar        = ref({ show: false, msg: '', color: 'success' })
const form            = ref({ amount: '', method_id: null as number | null, account_number: '', account_name: '', note: '' })
const formErrors      = ref<Record<string, string>>({})
const showForm        = ref(false)

const fetchAll = async () => {
  loading.value = true
  try {
    // ✅ CORRECTION : bon endpoint /organizers/{id}/
    const orgId = getOrganizerId()
    if (orgId) {
      try {
        const profile = await apiFetch(`/organizers/${orgId}/`)
        balance.value = profile?.data?.balance ?? profile?.balance ?? '0.00'
        console.log('💰 Balance:', balance.value, '| Profile:', profile)
      } catch (e) {
        console.error('Balance fetch error:', e)
        balance.value = '0.00'
      }
    }

    // Méthodes de retrait
    try {
      const mData = await apiFetch('/orders/withdraw-methods/')
      methods.value = Array.isArray(mData) ? mData : (mData.results || mData.data || [])
    } catch { methods.value = [] }

    // Historique des retraits
    try {
      const wData = await apiFetch('/orders/withdrawals/')
      withdrawals.value = Array.isArray(wData) ? wData : (wData.results || wData.data || [])
    } catch { withdrawals.value = [] }

  } finally {
    loading.value = false
  }
}

const validateForm = () => {
  formErrors.value = {}
  const amt = parseFloat(form.value.amount)
  if (!form.value.amount || isNaN(amt) || amt <= 0)
    formErrors.value.amount = 'Montant invalide'
  else if (amt < 10)
    formErrors.value.amount = 'Montant minimum : 10 DT'
  else if (amt > parseFloat(balance.value))
    formErrors.value.amount = `Solde insuffisant (max ${balance.value} DT)`
  if (!form.value.method_id)
    formErrors.value.method_id = 'Choisissez une méthode'
  return Object.keys(formErrors.value).length === 0
}

const submitWithdrawal = async () => {
  if (!validateForm()) return
  withdrawLoading.value = true
  try {
    await apiFetch('/orders/withdrawals/', {
      method: 'POST',
      body: JSON.stringify({
        amount:          parseFloat(form.value.amount),
        withdraw_method: form.value.method_id,
        account_number:  form.value.account_number || '',
        account_name:    form.value.account_name   || '',
        note:            form.value.note           || '',
      }),
    })
    snackbar.value = { show: true, msg: '✅ Demande envoyée avec succès !', color: 'success' }
    form.value = { amount: '', method_id: null, account_number: '', account_name: '', note: '' }
    showForm.value = false
    await fetchAll()
  } catch (err: any) {
    snackbar.value = { show: true, msg: err.message || '❌ Erreur lors de la demande', color: 'error' }
  } finally {
    withdrawLoading.value = false
  }
}

const statusConfig = (status: string | number) => {
  const s = String(status).toLowerCase()
  if (['approved', '2', 'approuvé'].includes(s)) return { label: 'Approuvé', color: 'success', icon: 'tabler-circle-check' }
  if (['rejected', '3', 'refusé'].includes(s))   return { label: 'Refusé',   color: 'error',   icon: 'tabler-circle-x' }
  return { label: 'En attente', color: 'warning', icon: 'tabler-clock' }
}

const formatDate   = (d: string) => d ? new Date(d).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' }) : '-'
const formatAmount = (v: any)    => { const n = parseFloat(v); return isNaN(n) ? '0.00' : n.toFixed(2) }

const pendingCount = computed(() =>
  withdrawals.value.filter(w => {
    const s = String(w.status || w.state || '').toLowerCase()
    return ['pending', '1', 'en attente'].includes(s)
  }).length
)

const approvedTotal = computed(() =>
  withdrawals.value
    .filter(w => ['approved', '2', 'approuvé'].includes(String(w.status || w.state || '').toLowerCase()))
    .reduce((sum, w) => sum + parseFloat(w.amount || 0), 0)
    .toFixed(2)
)

const selectedMethodName = computed(() => {
  const m = methods.value.find(m => m.id === form.value.method_id)
  return m?.name || m?.type || ''
})

onMounted(fetchAll)
</script>

<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h4 class="text-h4 font-weight-bold">Retrait d'argent</h4>
        <p class="text-body-1 text-medium-emphasis mt-1">Demandez un virement de vos revenus</p>
      </div>
      <VBtn color="primary" prepend-icon="tabler-plus" @click="showForm = !showForm">
        Nouvelle demande
      </VBtn>
    </div>

    <!-- Cartes stats -->
    <VRow class="mb-6">
      <VCol cols="12" sm="4">
        <VCard>
          <VCardText class="d-flex align-center gap-3 pa-5">
            <VAvatar color="success" variant="tonal" size="52" rounded>
              <VIcon icon="tabler-wallet" size="26" />
            </VAvatar>
            <div>
              <p class="text-caption text-medium-emphasis mb-0">Solde disponible</p>
              <h4 class="text-h4 font-weight-bold text-success">
                {{ loading ? '...' : formatAmount(balance) }}
                <span class="text-body-2 font-weight-regular">DT</span>
              </h4>
            </div>
          </VCardText>
        </VCard>
      </VCol>
      <VCol cols="12" sm="4">
        <VCard>
          <VCardText class="d-flex align-center gap-3 pa-5">
            <VAvatar color="warning" variant="tonal" size="52" rounded>
              <VIcon icon="tabler-clock" size="26" />
            </VAvatar>
            <div>
              <p class="text-caption text-medium-emphasis mb-0">Demandes en attente</p>
              <h4 class="text-h4 font-weight-bold">{{ loading ? '...' : pendingCount }}</h4>
            </div>
          </VCardText>
        </VCard>
      </VCol>
      <VCol cols="12" sm="4">
        <VCard>
          <VCardText class="d-flex align-center gap-3 pa-5">
            <VAvatar color="primary" variant="tonal" size="52" rounded>
              <VIcon icon="tabler-cash" size="26" />
            </VAvatar>
            <div>
              <p class="text-caption text-medium-emphasis mb-0">Total retiré (approuvé)</p>
              <h4 class="text-h4 font-weight-bold">
                {{ loading ? '...' : approvedTotal }}
                <span class="text-body-2 font-weight-regular">DT</span>
              </h4>
            </div>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- Formulaire -->
    <VExpandTransition>
      <VCard v-if="showForm" class="mb-6">
        <VCardTitle class="d-flex align-center gap-2 pa-5 pb-3">
          <VIcon icon="tabler-arrow-bar-to-down" color="primary" size="20" />
          Nouvelle demande de retrait
        </VCardTitle>
        <VDivider />
        <VCardText v-if="parseFloat(balance) < 10" class="pt-4 pb-0">
          <VAlert type="warning" variant="tonal" icon="tabler-alert-triangle" class="mb-2">
            Solde (<strong>{{ formatAmount(balance) }} DT</strong>) insuffisant. Minimum : 10 DT.
          </VAlert>
        </VCardText>
        <VCardText class="pa-5 pt-4">
          <VRow>
            <VCol cols="12" md="6">
              <VTextField
                v-model="form.amount" label="Montant à retirer (DT) *"
                placeholder="Ex : 50.00" type="number"
                prepend-inner-icon="tabler-currency-dollar"
                :error-messages="formErrors.amount"
                :hint="`Solde : ${formatAmount(balance)} DT | Min : 10 DT`"
                persistent-hint @input="formErrors.amount = ''"
              />
            </VCol>
            <VCol cols="12" md="6">
              <VSelect
                v-model="form.method_id"
                :items="methods"
                :item-title="(m: any) => m.name || m.type || m.label"
                item-value="id" label="Méthode de retrait *"
                prepend-inner-icon="tabler-credit-card"
                :error-messages="formErrors.method_id"
                no-data-text="Aucune méthode configurée"
                @update:model-value="formErrors.method_id = ''"
              />
            </VCol>
            <VCol cols="12" md="6">
              <VTextField
                v-model="form.account_number"
                :label="selectedMethodName.toLowerCase().includes('d17') || selectedMethodName.toLowerCase().includes('flouci') ? 'Numéro de téléphone' : 'Numéro RIB / IBAN'"
                :placeholder="selectedMethodName.toLowerCase().includes('d17') || selectedMethodName.toLowerCase().includes('flouci') ? 'Ex : 0021622XXXXXX' : 'Ex : TN59 0702 0000 0070 0654 9187'"
                prepend-inner-icon="tabler-hash"
                :error-messages="formErrors.account_number"
                @input="formErrors.account_number = ''"
              />
            </VCol>
            <VCol cols="12" md="6">
              <VTextField
                v-model="form.account_name" label="Nom du bénéficiaire"
                placeholder="Ex : Mohamed Ben Ali" prepend-inner-icon="tabler-user"
              />
            </VCol>
            <VCol cols="12">
              <VTextarea
                v-model="form.note" label="Note (optionnel)"
                placeholder="Informations supplémentaires..." rows="2"
                prepend-inner-icon="tabler-notes"
              />
            </VCol>
          </VRow>
        </VCardText>
        <VDivider />
        <VCardActions class="pa-5 gap-3">
          <VSpacer />
          <VBtn variant="outlined" @click="showForm = false; formErrors = {}">Annuler</VBtn>
          <VBtn color="primary" prepend-icon="tabler-send" :loading="withdrawLoading" @click="submitWithdrawal">
            Soumettre La Demande
          </VBtn>
        </VCardActions>
      </VCard>
    </VExpandTransition>

    <!-- Historique -->
    <VCard>
      <VCardTitle class="d-flex align-center justify-space-between pa-5 pb-3">
        <div class="d-flex align-center gap-2">
          <VIcon icon="tabler-history" color="primary" size="20" />
          Historique des retraits
        </div>
        <VBtn variant="text" size="small" prepend-icon="tabler-refresh" :loading="loading" @click="fetchAll">Actualiser</VBtn>
      </VCardTitle>
      <VDivider />

      <VCardText v-if="loading" class="d-flex justify-center pa-10">
        <VProgressCircular indeterminate color="primary" size="40" />
      </VCardText>

      <VCardText v-else-if="withdrawals.length === 0" class="text-center pa-10">
        <VIcon icon="tabler-cash-off" size="52" color="secondary" class="mb-3" />
        <p class="text-h6 text-medium-emphasis mb-1">Aucun retrait effectué</p>
        <p class="text-body-2 text-medium-emphasis">Votre historique apparaîtra ici.</p>
        <VBtn color="primary" variant="tonal" class="mt-4" prepend-icon="tabler-plus" @click="showForm = true">
          Faire une demande
        </VBtn>
      </VCardText>

      <template v-else>
        <VTable>
          <thead>
            <tr>
              <th>Date</th><th>Montant</th><th>Méthode</th>
              <th>Compte</th><th>Statut</th><th>Note admin</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="w in withdrawals" :key="w.id">
              <td>{{ formatDate(w.created_at) }}</td>
              <td><strong class="text-primary">{{ formatAmount(w.amount) }} DT</strong></td>
              <td>{{ w.method_name || w.withdraw_method_name || w.method?.name || '-' }}</td>
              <td class="text-medium-emphasis">{{ w.account_number || w.account || '-' }}</td>
              <td>
                <VChip :color="statusConfig(w.status || w.state).color" :prepend-icon="statusConfig(w.status || w.state).icon" size="small" variant="tonal">
                  {{ statusConfig(w.status || w.state).label }}
                </VChip>
              </td>
              <td class="text-medium-emphasis">{{ w.admin_note || w.rejection_reason || '-' }}</td>
            </tr>
          </tbody>
        </VTable>
      </template>
    </VCard>

    <VSnackbar v-model="snackbar.show" :color="snackbar.color" location="bottom right" timeout="4000">
      <div class="d-flex align-center gap-2">
        <VIcon :icon="snackbar.color === 'success' ? 'tabler-circle-check' : 'tabler-alert-circle'" />
        {{ snackbar.msg }}
      </div>
    </VSnackbar>
  </div>
</template>