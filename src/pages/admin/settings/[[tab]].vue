<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'

const route = useRoute()
const router = useRouter()

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
      ...(options.headers as { [key: string]: string }),
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
const isSaving = ref(false)
const showSnackbar = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref<'success' | 'error' | 'warning' | 'info'>('success')

const showMsg = (msg: string, color: 'success' | 'error' | 'warning' | 'info' = 'success') => {
  snackbarMessage.value = msg
  snackbarColor.value = color
  showSnackbar.value = true
}

const tabs = [
  { id: 'general',       title: 'Général',                 icon: 'tabler-settings'    },
  { id: 'gateways',      title: 'Passerelles paiement',    icon: 'tabler-credit-card' },
  { id: 'notifications', title: 'Notifications',           icon: 'tabler-bell'        },
  { id: 'security',      title: 'Sécurité & Vérification', icon: 'tabler-shield-lock' },
  { id: 'system',        title: 'Système',                 icon: 'tabler-server'      },
]

// ─── Tab actif basé sur le paramètre de route ───
const activeTab = computed(() => {
  const tab = String((route.params as any).tab || 'general')
  return tabs.find(t => t.id === tab) ? tab : 'general'
})

const navigateToTab = (val: unknown) => {
  if (typeof val === 'string')
    router.push({ path: `/admin/settings/${val}` })
}

const settings = ref<any>({})

// ─── Gateways state ───
const gateways = ref<any[]>([])
const isLoadingGateways = ref(false)
const showGatewayModal = ref(false)
const gatewayModalMode = ref<'add' | 'edit'>('add')
const editingGateway = ref<any>(null)
const gatewayFormError = ref('')
const isSavingGateway = ref(false)
const isDeletingGateway = ref(false)
const showDeleteGatewayDialog = ref(false)
const gatewayToDelete = ref<any>(null)

const emptyGateway = () => ({
  code: 0,
  name: '',
  alias: '',
  image: '',
  status: 1,
  crypto: false,
  description: '',
})

const gatewayForm = ref(emptyGateway())

const activeGateways = computed(() => gateways.value.filter(g => g.status === 1).length)
const inactiveGateways = computed(() => gateways.value.filter(g => g.status !== 1).length)

const gatewayTemplates = [
  {
    code: 1,
    name: 'D17',
    alias: 'd17',
    image: 'https://www.poste.tn/images/logo-d17.png',
    description: 'Paiement via D17 - La Poste Tunisienne 🇹🇳',
    crypto: false,
    status: 1,
  },
  {
    code: 2,
    name: 'Stripe',
    alias: 'stripe',
    image: 'https://upload.wikimedia.org/wikipedia/commons/b/ba/Stripe_Logo%2C_revised_2016.svg',
    description: 'Paiement par carte bancaire (Visa, Mastercard, etc.)',
    crypto: false,
    status: 1,
  },
  {
    code: 3,
    name: 'PayPal',
    alias: 'paypal',
    image: 'https://upload.wikimedia.org/wikipedia/commons/b/b5/PayPal.svg',
    description: 'Paiement international via PayPal',
    crypto: false,
    status: 1,
  },
]

// ─── Fetch Settings ───
const fetchSettings = async () => {
  isLoading.value = true
  try {
    const data = await apiFetch('/cms/settings/')
    settings.value = data
  }
  catch (err) {
    console.error('Erreur chargement paramètres:', err)
  }
  finally {
    isLoading.value = false
  }
}

// ─── Save Settings ───
const saveSettings = async () => {
  isSaving.value = true
  try {
    const data = await apiFetch('/cms/settings/', { method: 'PATCH', body: JSON.stringify(settings.value) })
    settings.value = data
    showMsg('✅ Paramètres enregistrés avec succès !', 'success')
  }
  catch (err) {
    console.error('Erreur sauvegarde:', err)
    showMsg('❌ Erreur lors de la sauvegarde', 'error')
  }
  finally {
    isSaving.value = false
  }
}

// ─── Fetch Gateways ───
const fetchGateways = async () => {
  isLoadingGateways.value = true
  try {
    const data = await apiFetch('/payments/gateways/')
    gateways.value = data.results || data || []
  }
  catch (err) {
    console.error('Erreur chargement passerelles:', err)
    gateways.value = []
  }
  finally {
    isLoadingGateways.value = false
  }
}

// ─── Gateway Modal ───
const openAddGateway = () => {
  gatewayModalMode.value = 'add'
  editingGateway.value = null
  gatewayForm.value = emptyGateway()
  gatewayFormError.value = ''
  showGatewayModal.value = true
}

const openEditGateway = (gw: any) => {
  gatewayModalMode.value = 'edit'
  editingGateway.value = gw
  gatewayForm.value = {
    code: gw.code || 0,
    name: gw.name || '',
    alias: gw.alias || '',
    image: gw.image || '',
    status: gw.status ?? 1,
    crypto: gw.crypto ?? false,
    description: gw.description || '',
  }
  gatewayFormError.value = ''
  showGatewayModal.value = true
}

const loadTemplate = (tpl: any) => {
  gatewayForm.value = { ...tpl }
}

const saveGateway = async () => {
  if (!gatewayForm.value.name) { gatewayFormError.value = 'Le nom est obligatoire.'; return }
  if (!gatewayForm.value.alias) { gatewayFormError.value = "L'alias est obligatoire."; return }

  gatewayFormError.value = ''
  isSavingGateway.value = true
  try {
    const payload = { ...gatewayForm.value }
    if (gatewayModalMode.value === 'edit' && editingGateway.value)
      await apiFetch(`/payments/gateways/${editingGateway.value.id}/`, { method: 'PATCH', body: JSON.stringify(payload) })
    else
      await apiFetch('/payments/gateways/', { method: 'POST', body: JSON.stringify(payload) })

    showGatewayModal.value = false
    showMsg(gatewayModalMode.value === 'edit' ? '✅ Passerelle modifiée !' : '✅ Passerelle créée !', 'success')
    await fetchGateways()
  }
  catch (err: any) {
    if (err?.data?.errors) {
      gatewayFormError.value = Object.entries(err.data.errors)
        .map(([f, m]: any) => `• ${f} : ${Array.isArray(m) ? m.join(', ') : m}`)
        .join('\n')
    }
    else if (err?.data && typeof err.data === 'object') {
      gatewayFormError.value = Object.entries(err.data)
        .map(([f, m]: any) => `• ${f} : ${Array.isArray(m) ? m.join(', ') : m}`)
        .join('\n')
    }
    else {
      gatewayFormError.value = err?.data?.message || '❌ Erreur lors de la sauvegarde.'
    }
  }
  finally { isSavingGateway.value = false }
}

// ─── Toggle gateway status ───
const toggleGatewayStatus = async (gw: any) => {
  try {
    const newStatus = gw.status === 1 ? 0 : 1
    await apiFetch(`/payments/gateways/${gw.id}/`, {
      method: 'PATCH',
      body: JSON.stringify({ status: newStatus }),
    })
    showMsg(newStatus === 1 ? '✅ Passerelle activée' : '⚠️ Passerelle désactivée', 'success')
    await fetchGateways()
  }
  catch { showMsg('❌ Erreur lors de la mise à jour', 'error') }
}

// ─── Delete gateway ───
const confirmDeleteGateway = (gw: any) => {
  gatewayToDelete.value = gw
  showDeleteGatewayDialog.value = true
}

const deleteGateway = async () => {
  if (!gatewayToDelete.value) return
  isDeletingGateway.value = true
  try {
    await apiFetch(`/payments/gateways/${gatewayToDelete.value.id}/`, { method: 'DELETE' })
    showDeleteGatewayDialog.value = false
    const name = gatewayToDelete.value.name
    gatewayToDelete.value = null
    showMsg(`🗑️ Passerelle "${name}" supprimée`, 'success')
    await fetchGateways()
  }
  catch {
    showDeleteGatewayDialog.value = false
    showMsg('❌ Erreur lors de la suppression', 'error')
  }
  finally { isDeletingGateway.value = false }
}

// ─── Initialiser les 3 passerelles ───
const initializeGateways = async () => {
  if (!confirm('Créer les 3 passerelles par défaut (D17, Stripe, PayPal) ?')) return
  isLoadingGateways.value = true
  try {
    for (const tpl of gatewayTemplates) {
      const exists = gateways.value.find(g => g.alias === tpl.alias)
      if (!exists)
        await apiFetch('/payments/gateways/', { method: 'POST', body: JSON.stringify(tpl) })
    }
    showMsg('✅ Passerelles initialisées !', 'success')
    await fetchGateways()
  }
  catch { showMsg('❌ Erreur lors de l\'initialisation', 'error') }
  finally { isLoadingGateways.value = false }
}

// ─── Helpers icône/couleur ───
const getGatewayIcon = (alias: string) => {
  const icons: { [key: string]: string } = {
    d17: 'tabler-building-bank',
    stripe: 'tabler-brand-stripe',
    paypal: 'tabler-brand-paypal',
    flouci: 'tabler-wallet',
  }
  return icons[alias?.toLowerCase()] || 'tabler-credit-card'
}

const getGatewayColor = (alias: string) => {
  const colors: { [key: string]: string } = {
    d17: 'primary',
    stripe: 'info',
    paypal: 'warning',
    flouci: 'success',
  }
  return colors[alias?.toLowerCase()] || 'primary'
}

function formatDate(dateString: string | null): string {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('fr-FR', {
    day: '2-digit', month: 'long', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

onMounted(() => {
  fetchSettings()
  fetchGateways()
})
</script>

<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h4 class="text-h4 font-weight-bold">Paramètres</h4>
        <p class="text-body-1 text-medium-emphasis mt-1">Gérez la configuration globale de la plateforme</p>
      </div>
    </div>

    <div v-if="isLoading" class="d-flex flex-column align-center justify-center py-16">
      <VProgressCircular indeterminate color="primary" size="48" />
      <p class="text-body-1 text-medium-emphasis mt-4">Chargement des paramètres...</p>
    </div>

    <template v-else>
      <VTabs
        :model-value="activeTab"
        class="mb-6"
        @update:model-value="(val) => navigateToTab(val)"
      >
        <VTab v-for="tab in tabs" :key="tab.id" :value="tab.id">
          <VIcon :icon="tab.icon" size="20" start />
          {{ tab.title }}
        </VTab>
      </VTabs>

      <VWindow :model-value="activeTab">

        <!-- ═══════ Onglet Général ═══════ -->
        <VWindowItem value="general">
          <VCard>
            <VCardText class="pa-6">
              <div class="d-flex align-center gap-2 mb-6">
                <VIcon icon="tabler-info-circle" color="primary" />
                <h6 class="text-h6 font-weight-bold">Informations générales</h6>
              </div>
              <VRow>
                <VCol cols="12" md="6">
                  <VTextField v-model="settings.site_name" label="Nom de la plateforme" prepend-inner-icon="tabler-building" />
                </VCol>
                <VCol cols="12" md="3">
                  <VTextField v-model="settings.cur_text" label="Code devise" prepend-inner-icon="tabler-currency-dollar" placeholder="TND" />
                </VCol>
                <VCol cols="12" md="3">
                  <VTextField v-model="settings.cur_sym" label="Symbole devise" prepend-inner-icon="tabler-currency-dollar" placeholder="DT" />
                </VCol>
                <VCol cols="12" md="6">
                  <VTextField v-model="settings.base_color" label="Couleur principale" prepend-inner-icon="tabler-palette" type="color" />
                </VCol>
                <VCol cols="12" md="6">
                  <VTextField v-model="settings.secondary_color" label="Couleur secondaire" prepend-inner-icon="tabler-palette" type="color" />
                </VCol>
                <VCol cols="12" md="4">
                  <VTextField v-model.number="settings.cancel_time" label="Délai annulation (heures)" type="number" prepend-inner-icon="tabler-clock" />
                </VCol>
                <VCol cols="12" md="4">
                  <VTextField v-model.number="settings.payment_timeout" label="Timeout paiement (min)" type="number" prepend-inner-icon="tabler-clock" />
                </VCol>
                <VCol cols="12" md="4">
                  <VTextField v-model.number="settings.paginate_number" label="Résultats par page" type="number" prepend-inner-icon="tabler-list-numbers" />
                </VCol>
                <VCol cols="12" md="4">
                  <VTextField v-model.number="settings.max_gallery_images" label="Max images galerie" type="number" prepend-inner-icon="tabler-photo" />
                </VCol>
                <VCol cols="12" md="4">
                  <VTextField v-model.number="settings.currency_format" label="Format devise (0 ou 1)" type="number" prepend-inner-icon="tabler-currency-dollar" />
                </VCol>
                <VCol cols="12" md="4">
                  <VSelect
                    v-model="settings.organizer_registration"
                    label="Inscription organisateur"
                    :items="[
                      { title: 'Désactivée', value: 0 },
                      { title: 'Activée', value: 1 },
                    ]"
                    prepend-inner-icon="tabler-user-plus"
                  />
                </VCol>
              </VRow>

              <div class="d-flex align-center gap-2 mt-6 mb-4">
                <VIcon icon="tabler-toggle-right" color="primary" />
                <h6 class="text-h6 font-weight-bold">Options</h6>
              </div>
              <VRow>
                <VCol cols="12" sm="6" md="4">
                  <VSwitch v-model="settings.registration" label="Inscription utilisateurs" color="success" />
                </VCol>
                <VCol cols="12" sm="6" md="4">
                  <VSwitch v-model="settings.event_verification" label="Vérification événements" color="success" />
                </VCol>
                <VCol cols="12" sm="6" md="4">
                  <VSwitch v-model="settings.multi_language" label="Multi-langues" color="success" />
                </VCol>
                <VCol cols="12" sm="6" md="4">
                  <VSwitch v-model="settings.agree" label="Conditions d'utilisation" color="success" />
                </VCol>
                <VCol cols="12" sm="6" md="4">
                  <VSwitch v-model="settings.maintenance_mode" label="Mode maintenance" color="warning" />
                </VCol>
                <VCol cols="12" sm="6" md="4">
                  <VSwitch v-model="settings.force_ssl" label="Forcer SSL" color="info" />
                </VCol>
              </VRow>
            </VCardText>
            <VDivider />
            <VCardActions class="pa-6">
              <VSpacer />
              <VBtn color="primary" :loading="isSaving" prepend-icon="tabler-device-floppy" @click="saveSettings">
                Enregistrer
              </VBtn>
            </VCardActions>
          </VCard>
        </VWindowItem>

        <!-- ═══════ Onglet Passerelles paiement ═══════ -->
        <VWindowItem value="gateways">
          <div>
            <div class="d-flex justify-space-between align-center mb-6 flex-wrap gap-3">
              <div>
                <h5 class="text-h5 font-weight-bold mb-1">Passerelles de paiement</h5>
                <p class="text-body-2 text-medium-emphasis mb-0">Gérez les méthodes de paiement disponibles pour les utilisateurs</p>
              </div>
              <div class="d-flex gap-2">
                <VBtn
                  v-if="gateways.length === 0"
                  color="success"
                  variant="tonal"
                  prepend-icon="tabler-rocket"
                  @click="initializeGateways"
                >
                  Initialiser D17, Stripe & PayPal
                </VBtn>
                <VBtn color="primary" prepend-icon="tabler-plus" @click="openAddGateway">
                  Ajouter une passerelle
                </VBtn>
              </div>
            </div>

            <VRow class="mb-6">
              <VCol cols="12" sm="4">
                <VCard>
                  <VCardText class="d-flex align-center gap-3">
                    <VAvatar color="primary" variant="tonal" size="44" rounded>
                      <VIcon icon="tabler-credit-card" size="24" />
                    </VAvatar>
                    <div>
                      <p class="text-caption text-medium-emphasis mb-0">Total passerelles</p>
                      <h5 class="text-h6 font-weight-bold">{{ gateways.length }}</h5>
                    </div>
                  </VCardText>
                </VCard>
              </VCol>
              <VCol cols="12" sm="4">
                <VCard>
                  <VCardText class="d-flex align-center gap-3">
                    <VAvatar color="success" variant="tonal" size="44" rounded>
                      <VIcon icon="tabler-check" size="24" />
                    </VAvatar>
                    <div>
                      <p class="text-caption text-medium-emphasis mb-0">Actives</p>
                      <h5 class="text-h6 font-weight-bold">{{ activeGateways }}</h5>
                    </div>
                  </VCardText>
                </VCard>
              </VCol>
              <VCol cols="12" sm="4">
                <VCard>
                  <VCardText class="d-flex align-center gap-3">
                    <VAvatar color="error" variant="tonal" size="44" rounded>
                      <VIcon icon="tabler-x" size="24" />
                    </VAvatar>
                    <div>
                      <p class="text-caption text-medium-emphasis mb-0">Inactives</p>
                      <h5 class="text-h6 font-weight-bold">{{ inactiveGateways }}</h5>
                    </div>
                  </VCardText>
                </VCard>
              </VCol>
            </VRow>

            <div v-if="isLoadingGateways" class="d-flex justify-center py-10">
              <VProgressCircular indeterminate color="primary" size="40" />
            </div>

            <VCard v-else-if="gateways.length === 0" variant="tonal" color="info">
              <VCardText class="text-center pa-12">
                <VIcon icon="tabler-credit-card-off" size="64" class="mb-4" />
                <h5 class="text-h6 font-weight-bold mb-2">Aucune passerelle configurée</h5>
                <p class="text-body-2 mb-4">Cliquez sur "Initialiser D17, Stripe & PayPal" pour créer les 3 passerelles recommandées, ou ajoutez-en une manuellement.</p>
              </VCardText>
            </VCard>

            <VRow v-else>
              <VCol v-for="gw in gateways" :key="gw.id" cols="12" md="6" lg="4">
                <VCard class="gateway-card" :class="{ 'gateway-inactive': gw.status !== 1 }">
                  <VCardText class="pa-6">
                    <div class="d-flex justify-space-between align-start mb-4">
                      <VAvatar :color="getGatewayColor(gw.alias)" variant="tonal" size="56" rounded>
                        <VImg v-if="gw.image" :src="gw.image" contain />
                        <VIcon v-else :icon="getGatewayIcon(gw.alias)" size="28" />
                      </VAvatar>
                      <VSwitch
                        :model-value="gw.status === 1"
                        color="success"
                        hide-details
                        density="compact"
                        @change="toggleGatewayStatus(gw)"
                      />
                    </div>
                    <h6 class="text-h6 font-weight-bold mb-1">{{ gw.name }}</h6>
                    <p class="text-caption text-medium-emphasis mb-3">
                      <code>{{ gw.alias }}</code> • Code: {{ gw.code }}
                    </p>
                    <p class="text-body-2 mb-4" style="min-height: 40px;">
                      {{ gw.description || 'Aucune description' }}
                    </p>
                    <div class="d-flex flex-wrap gap-2 mb-4">
                      <VChip :color="gw.status === 1 ? 'success' : 'error'" size="small" variant="tonal">
                        <VIcon :icon="gw.status === 1 ? 'tabler-check' : 'tabler-x'" size="14" start />
                        {{ gw.status === 1 ? 'Active' : 'Inactive' }}
                      </VChip>
                      <VChip v-if="gw.crypto" color="warning" size="small" variant="tonal">
                        <VIcon icon="tabler-currency-bitcoin" size="14" start />
                        Crypto
                      </VChip>
                    </div>
                  </VCardText>
                  <VDivider />
                  <VCardActions class="pa-3">
                    <VBtn variant="text" color="primary" prepend-icon="tabler-settings" size="small" @click="openEditGateway(gw)">
                      Configurer
                    </VBtn>
                    <VSpacer />
                    <VBtn icon variant="text" color="error" size="small" @click="confirmDeleteGateway(gw)">
                      <VIcon icon="tabler-trash" size="18" />
                      <VTooltip activator="parent">Supprimer</VTooltip>
                    </VBtn>
                  </VCardActions>
                </VCard>
              </VCol>
            </VRow>
          </div>
        </VWindowItem>

        <!-- ═══════ Onglet Notifications ═══════ -->
        <VWindowItem value="notifications">
          <div class="d-flex flex-column gap-6">
            <VCard>
              <VCardText class="pa-6">
                <div class="d-flex align-center gap-2 mb-6">
                  <VIcon icon="tabler-mail" color="primary" />
                  <h6 class="text-h6 font-weight-bold">Email</h6>
                </div>
                <VRow>
                  <VCol cols="12" md="6">
                    <VTextField v-model="settings.email_from" label="Email expéditeur" prepend-inner-icon="tabler-mail" />
                  </VCol>
                  <VCol cols="12" md="6">
                    <VTextField v-model="settings.email_from_name" label="Nom expéditeur" prepend-inner-icon="tabler-user" />
                  </VCol>
                  <VCol cols="12">
                    <VTextarea v-model="settings.email_template" label="Template email de réservation" rows="6" />
                  </VCol>
                </VRow>
              </VCardText>
            </VCard>

            <VCard>
              <VCardText class="pa-6">
                <div class="d-flex align-center gap-2 mb-6">
                  <VIcon icon="tabler-message" color="success" />
                  <h6 class="text-h6 font-weight-bold">SMS</h6>
                </div>
                <VRow>
                  <VCol cols="12" md="6">
                    <VTextField v-model="settings.sms_from" label="Expéditeur SMS" prepend-inner-icon="tabler-message" />
                  </VCol>
                  <VCol cols="12">
                    <VTextarea v-model="settings.sms_template" label="Template SMS" rows="3" />
                  </VCol>
                  <VCol cols="12">
                    <VTextarea v-model="settings.sms_body" label="Corps SMS (billet)" rows="3" />
                  </VCol>
                </VRow>
              </VCardText>
            </VCard>

            <VCard>
              <VCardText class="pa-6">
                <div class="d-flex align-center gap-2 mb-6">
                  <VIcon icon="tabler-bell" color="warning" />
                  <h6 class="text-h6 font-weight-bold">Notifications Push</h6>
                </div>
                <VRow>
                  <VCol cols="12" md="6">
                    <VTextField v-model="settings.push_title" label="Titre push" prepend-inner-icon="tabler-bell" />
                  </VCol>
                  <VCol cols="12">
                    <VTextarea v-model="settings.push_template" label="Template push" rows="2" />
                  </VCol>
                </VRow>
              </VCardText>
            </VCard>

            <VCard>
              <VCardText class="pa-6">
                <div class="d-flex align-center gap-2 mb-6">
                  <VIcon icon="tabler-toggle-right" color="info" />
                  <h6 class="text-h6 font-weight-bold">Canaux actifs</h6>
                </div>
                <VRow>
                  <VCol cols="12" sm="6" md="3">
                    <VSwitch v-model="settings.en" label="Email" color="primary" />
                  </VCol>
                  <VCol cols="12" sm="6" md="3">
                    <VSwitch v-model="settings.sn" label="SMS" color="success" />
                  </VCol>
                  <VCol cols="12" sm="6" md="3">
                    <VSwitch v-model="settings.pn" label="Push" color="warning" />
                  </VCol>
                </VRow>
              </VCardText>
              <VDivider />
              <VCardActions class="pa-6">
                <VSpacer />
                <VBtn color="primary" :loading="isSaving" prepend-icon="tabler-device-floppy" @click="saveSettings">
                  Enregistrer
                </VBtn>
              </VCardActions>
            </VCard>
          </div>
        </VWindowItem>

        <!-- ═══════ Onglet Sécurité ═══════ -->
        <VWindowItem value="security">
          <VCard>
            <VCardText class="pa-6">
              <div class="d-flex align-center gap-2 mb-6">
                <VIcon icon="tabler-shield-check" color="error" />
                <h6 class="text-h6 font-weight-bold">Vérification & Sécurité</h6>
              </div>
              <div class="d-flex flex-column gap-4">
                <div class="d-flex justify-space-between align-center pa-4 rounded-lg" style="border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));">
                  <div class="d-flex align-center gap-3">
                    <VAvatar color="primary" variant="tonal" size="44" rounded>
                      <VIcon icon="tabler-shield-check" size="24" />
                    </VAvatar>
                    <div>
                      <p class="text-body-1 font-weight-medium mb-0">Vérification KYC</p>
                      <p class="text-caption text-medium-emphasis mb-0">Exiger la vérification d'identité</p>
                    </div>
                  </div>
                  <VSwitch v-model="settings.kv" color="primary" />
                </div>
                <div class="d-flex justify-space-between align-center pa-4 rounded-lg" style="border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));">
                  <div class="d-flex align-center gap-3">
                    <VAvatar color="success" variant="tonal" size="44" rounded>
                      <VIcon icon="tabler-mail-check" size="24" />
                    </VAvatar>
                    <div>
                      <p class="text-body-1 font-weight-medium mb-0">Vérification email</p>
                      <p class="text-caption text-medium-emphasis mb-0">Exiger la vérification de l'email à l'inscription</p>
                    </div>
                  </div>
                  <VSwitch v-model="settings.ev" color="success" />
                </div>
                <div class="d-flex justify-space-between align-center pa-4 rounded-lg" style="border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));">
                  <div class="d-flex align-center gap-3">
                    <VAvatar color="info" variant="tonal" size="44" rounded>
                      <VIcon icon="tabler-phone-check" size="24" />
                    </VAvatar>
                    <div>
                      <p class="text-body-1 font-weight-medium mb-0">Vérification SMS</p>
                      <p class="text-caption text-medium-emphasis mb-0">Exiger la vérification du numéro de téléphone</p>
                    </div>
                  </div>
                  <VSwitch v-model="settings.sv" color="info" />
                </div>
                <div class="d-flex justify-space-between align-center pa-4 rounded-lg" style="border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));">
                  <div class="d-flex align-center gap-3">
                    <VAvatar color="warning" variant="tonal" size="44" rounded>
                      <VIcon icon="tabler-lock" size="24" />
                    </VAvatar>
                    <div>
                      <p class="text-body-1 font-weight-medium mb-0">Mot de passe sécurisé</p>
                      <p class="text-caption text-medium-emphasis mb-0">Exiger un mot de passe fort (majuscule, chiffre, symbole)</p>
                    </div>
                  </div>
                  <VSwitch v-model="settings.secure_password" color="warning" />
                </div>
              </div>
            </VCardText>
            <VDivider />
            <VCardActions class="pa-6">
              <VSpacer />
              <VBtn color="primary" :loading="isSaving" prepend-icon="tabler-device-floppy" @click="saveSettings">
                Enregistrer
              </VBtn>
            </VCardActions>
          </VCard>
        </VWindowItem>

        <!-- ═══════ Onglet Système ═══════ -->
        <VWindowItem value="system">
          <VCard>
            <VCardText class="pa-6">
              <div class="d-flex align-center gap-2 mb-6">
                <VIcon icon="tabler-server" color="secondary" />
                <h6 class="text-h6 font-weight-bold">Informations système</h6>
              </div>
              <VRow>
                <VCol cols="12">
                  <VTextarea v-model="settings.system_info" label="Informations système" rows="4" disabled />
                </VCol>
                <VCol cols="12" md="6">
                  <VTextField v-model="settings.available_version" label="Version" prepend-inner-icon="tabler-tag" disabled />
                </VCol>
                <VCol cols="12" md="6">
                  <VTextField :model-value="formatDate(settings.last_cron)" label="Dernier CRON" prepend-inner-icon="tabler-clock" disabled />
                </VCol>
                <VCol cols="12" md="6">
                  <VTextField v-model="settings.active_template" label="Template actif" prepend-inner-icon="tabler-layout" />
                </VCol>
                <VCol cols="12">
                  <VTextarea v-model="settings.global_shortcodes" label="Shortcodes globaux" rows="3" placeholder="Variables disponibles dans les templates" />
                </VCol>
                <VCol cols="12" md="6">
                  <VSwitch v-model="settings.system_customized" label="Système personnalisé" color="primary" />
                </VCol>
              </VRow>
            </VCardText>
            <VDivider />
            <VCardActions class="pa-6">
              <VSpacer />
              <VBtn color="primary" :loading="isSaving" prepend-icon="tabler-device-floppy" @click="saveSettings">
                Enregistrer
              </VBtn>
            </VCardActions>
          </VCard>
        </VWindowItem>

      </VWindow>
    </template>

    <!-- ════ MODAL: Ajouter/Modifier passerelle ════ -->
    <VDialog v-model="showGatewayModal" max-width="600" persistent>
      <VCard>
        <VCardTitle class="d-flex justify-space-between align-center pa-6">
          <span class="text-h6 font-weight-bold">
            {{ gatewayModalMode === 'add' ? 'Ajouter une passerelle' : 'Modifier la passerelle' }}
          </span>
          <VBtn icon variant="text" size="small" @click="showGatewayModal = false">
            <VIcon icon="tabler-x" />
          </VBtn>
        </VCardTitle>
        <VDivider />
        <VCardText class="pa-6">
          <div v-if="gatewayModalMode === 'add'" class="mb-4">
            <p class="text-caption text-medium-emphasis mb-2">Choisir un modèle :</p>
            <div class="d-flex gap-2 flex-wrap">
              <VBtn
                v-for="tpl in gatewayTemplates"
                :key="tpl.alias"
                size="small"
                variant="tonal"
                :color="getGatewayColor(tpl.alias)"
                :prepend-icon="getGatewayIcon(tpl.alias)"
                @click="loadTemplate(tpl)"
              >
                {{ tpl.name }}
              </VBtn>
            </div>
          </div>
          <VAlert v-if="gatewayFormError" type="error" variant="tonal" density="compact" class="mb-4" closable @click:close="gatewayFormError = ''">
            <div style="white-space: pre-line">{{ gatewayFormError }}</div>
          </VAlert>
          <VRow>
            <VCol cols="12" md="8">
              <VTextField v-model="gatewayForm.name" label="Nom *" placeholder="Ex: D17 Poste Tunisienne" prepend-inner-icon="tabler-credit-card" />
            </VCol>
            <VCol cols="12" md="4">
              <VTextField v-model.number="gatewayForm.code" label="Code" type="number" prepend-inner-icon="tabler-hash" />
            </VCol>
            <VCol cols="12">
              <VTextField v-model="gatewayForm.alias" label="Alias *" placeholder="d17, stripe, paypal..." prepend-inner-icon="tabler-at" hint="Identifiant court unique, en minuscules" persistent-hint />
            </VCol>
            <VCol cols="12">
              <VTextField v-model="gatewayForm.image" label="Logo (URL)" placeholder="https://example.com/logo.png" prepend-inner-icon="tabler-photo" />
            </VCol>
            <VCol v-if="gatewayForm.image" cols="12">
              <img :src="gatewayForm.image" alt="Aperçu" style="max-width:100%; max-height:100px; object-fit:contain; border-radius:8px; border:0.5px solid #E5E7EB; padding: 8px; background: #F9FAFB;">
            </VCol>
            <VCol cols="12">
              <VTextarea v-model="gatewayForm.description" label="Description" rows="3" prepend-inner-icon="tabler-file-text" />
            </VCol>
            <VCol cols="12" md="6">
              <VSelect
                v-model="gatewayForm.status"
                :items="[
                  { title: 'Active', value: 1 },
                  { title: 'Inactive', value: 0 },
                ]"
                label="Statut"
                prepend-inner-icon="tabler-toggle-right"
              />
            </VCol>
            <VCol cols="12" md="6">
              <div class="d-flex align-center gap-3 mt-3">
                <span class="text-body-2 text-medium-emphasis">Crypto :</span>
                <VSwitch v-model="gatewayForm.crypto" color="warning" hide-details :label="gatewayForm.crypto ? 'Oui' : 'Non'" />
              </div>
            </VCol>
          </VRow>
        </VCardText>
        <VDivider />
        <VCardActions class="pa-6">
          <VSpacer />
          <VBtn variant="outlined" color="secondary" @click="showGatewayModal = false">Annuler</VBtn>
          <VBtn color="primary" :loading="isSavingGateway" prepend-icon="tabler-device-floppy" @click="saveGateway">
            {{ gatewayModalMode === 'add' ? 'Créer' : 'Enregistrer' }}
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- ════ DIALOG: Supprimer passerelle ════ -->
    <VDialog v-model="showDeleteGatewayDialog" max-width="450">
      <VCard>
        <VCardText class="text-center pa-8">
          <VAvatar color="error" variant="tonal" size="64" class="mb-4">
            <VIcon icon="tabler-alert-triangle" size="32" />
          </VAvatar>
          <h5 class="text-h6 font-weight-bold mb-2">Confirmer la suppression</h5>
          <p class="text-body-1 text-medium-emphasis mb-0">
            Êtes-vous sûr de vouloir supprimer la passerelle<br>
            <strong>{{ gatewayToDelete?.name }}</strong> ?
          </p>
          <p class="text-body-2 text-error mt-2 mb-0">
            ⚠️ Les utilisateurs ne pourront plus payer avec cette méthode.
          </p>
        </VCardText>
        <VDivider />
        <VCardActions class="pa-4 justify-center">
          <VBtn variant="outlined" color="secondary" @click="showDeleteGatewayDialog = false">Annuler</VBtn>
          <VBtn color="error" :loading="isDeletingGateway" prepend-icon="tabler-trash" @click="deleteGateway">Supprimer</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Snackbar -->
    <VSnackbar v-model="showSnackbar" :color="snackbarColor" :timeout="3000" location="bottom end">
      <div class="d-flex align-center gap-2">
        <VIcon :icon="snackbarColor === 'success' ? 'tabler-check' : 'tabler-alert-circle'" />
        {{ snackbarMessage }}
      </div>
    </VSnackbar>
  </div>
</template>

<style scoped>
.gateway-card {
  transition: all 0.3s ease;
  border: 1px solid transparent;
}
.gateway-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}
.gateway-inactive {
  opacity: 0.7;
}
.gateway-inactive:hover {
  opacity: 1;
}
</style>