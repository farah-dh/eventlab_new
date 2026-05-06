<script setup lang="ts">
import { onMounted, ref } from 'vue'

const router = useRouter()
const route = useRoute()
const organizerId = (route.params as any).id as string
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
  return response.json()
}

const isLoading = ref(true)
const isSaving = ref(false)
const formError = ref<Record<string, string>>({})
const formErrorMsg = ref('')
const successMsg = ref('')

const form = ref({
  organization_name: '',
  short_description: '',
  long_description: '',
  firstname: '',
  lastname: '',
  username: '',
  email: '',
  dial_code: '+216',
  mobile: '',
  country_code: '',
  city: '',
  title: '',
  status: true,
  is_featured: false,
})

const phoneCodes = [
  { title: '🇹🇳 +216', value: '+216' },
  { title: '🇫🇷 +33', value: '+33' },
  { title: '🇺🇸 +1', value: '+1' },
  { title: '🇬🇧 +44', value: '+44' },
  { title: '🇲🇦 +212', value: '+212' },
  { title: '🇩🇿 +213', value: '+213' },
  { title: '🇪🇬 +20', value: '+20' },
  { title: '🇸🇦 +966', value: '+966' },
  { title: '🇦🇪 +971', value: '+971' },
]

const countries = [
  { title: 'Tunisie', value: 'TN' },
  { title: 'France', value: 'FR' },
  { title: 'Maroc', value: 'MA' },
  { title: 'Algérie', value: 'DZ' },
  { title: 'Égypte', value: 'EG' },
  { title: 'Arabie Saoudite', value: 'SA' },
  { title: 'Émirats Arabes Unis', value: 'AE' },
  { title: 'Belgique', value: 'BE' },
  { title: 'Suisse', value: 'CH' },
  { title: 'Canada', value: 'CA' },
]

// ─── Charger les données de l'organisateur ───
const loadOrganizer = async () => {
  isLoading.value = true
  try {
    const data = await apiFetch(`/organizers/${organizerId}/`)
    form.value = {
      organization_name: data.organization_name || '',
      short_description: data.short_description || '',
      long_description: data.long_description || '',
      firstname: data.firstname || '',
      lastname: data.lastname || '',
      username: data.username || '',
      email: data.email || '',
      dial_code: data.dial_code || '+216',
      mobile: data.mobile || '',
      country_code: data.country_code || '',
      city: data.city || '',
      title: data.title || '',
      status: data.status ?? true,
      is_featured: data.is_featured ?? false,
    }
  }
  catch (err: any) {
    formErrorMsg.value = '❌ Impossible de charger l\'organisateur.'
    console.error(err)
  }
  finally {
    isLoading.value = false
  }
}

// ─── Sauvegarder les modifications ───
const updateOrganizer = async () => {
  formError.value = {}
  formErrorMsg.value = ''
  isSaving.value = true

  try {
    await apiFetch(`/organizers/${organizerId}/`, {
      method: 'PATCH',
      body: JSON.stringify(form.value),
    })
    successMsg.value = '✅ Organisateur mis à jour avec succès !'
    setTimeout(() => router.push('/admin/organizers'), 1500)
  }
  catch (err: any) {
    if (err?.data?.errors && typeof err.data.errors === 'object') {
      const mapped: Record<string, string> = {}
      for (const [field, msg] of Object.entries(err.data.errors))
        mapped[field] = Array.isArray(msg) ? (msg as string[]).join(', ') : String(msg)
      formError.value = mapped
    }
    else if (err?.data && typeof err.data === 'object') {
      const mapped: Record<string, string> = {}
      for (const [field, msg] of Object.entries(err.data))
        mapped[field] = Array.isArray(msg) ? (msg as string[]).join(', ') : String(msg)
      formError.value = mapped
    }
    else {
      formErrorMsg.value = err?.data?.message || '❌ Erreur lors de la mise à jour.'
    }
  }
  finally {
    isSaving.value = false
  }
}

onMounted(() => {
  loadOrganizer()
})
</script>

<template>
  <div>
    <!-- ── Header ── -->
    <div class="d-flex align-center gap-3 mb-6">
      <VBtn icon variant="text" @click="router.push('/admin/organizers')">
        <VIcon icon="tabler-arrow-left" size="20" />
      </VBtn>
      <div>
        <h4 class="text-h4 font-weight-bold">Modifier l'organisateur</h4>
        <p class="text-body-1 text-medium-emphasis mt-1">
          Mettre à jour les informations de l'organisateur
        </p>
      </div>
    </div>

    <!-- ── Notifications ── -->
    <VAlert v-if="successMsg" type="success" variant="tonal" class="mb-4">
      {{ successMsg }}
    </VAlert>
    <VAlert
      v-if="formErrorMsg"
      type="error"
      variant="tonal"
      closable
      class="mb-4"
      @click:close="formErrorMsg = ''"
    >
      {{ formErrorMsg }}
    </VAlert>

    <!-- ── Loading ── -->
    <div v-if="isLoading" class="d-flex flex-column align-center justify-center py-16">
      <VProgressCircular indeterminate color="primary" size="48" />
      <p class="text-body-1 text-medium-emphasis mt-4">Chargement...</p>
    </div>

    <VRow v-else>
      <!-- ── Formulaire principal ── -->
      <VCol cols="12" md="8">

        <!-- Section Organisation -->
        <VCard class="mb-6">
          <VCardTitle class="pa-6 pb-2">
            <span class="text-h6 font-weight-bold">Organisation</span>
          </VCardTitle>
          <VCardText class="pa-6">
            <VRow>
              <VCol cols="12">
                <VTextField
                  v-model="form.organization_name"
                  label="Nom de l'organisation *"
                  prepend-inner-icon="tabler-building"
                  :error-messages="formError.organization_name"
                />
              </VCol>
              <VCol cols="12">
                <VTextField
                  v-model="form.title"
                  label="Titre / Slogan"
                  prepend-inner-icon="tabler-bookmark"
                  :error-messages="formError.title"
                />
              </VCol>
              <VCol cols="12">
                <VTextField
                  v-model="form.short_description"
                  label="Description courte"
                  prepend-inner-icon="tabler-align-left"
                  counter="150"
                  maxlength="150"
                  :error-messages="formError.short_description"
                />
              </VCol>
              <VCol cols="12">
                <VTextarea
                  v-model="form.long_description"
                  label="Description longue"
                  prepend-inner-icon="tabler-file-text"
                  rows="4"
                  :error-messages="formError.long_description"
                />
              </VCol>
            </VRow>
          </VCardText>
        </VCard>

        <!-- Section Informations personnelles -->
        <VCard class="mb-6">
          <VCardTitle class="pa-6 pb-2">
            <span class="text-h6 font-weight-bold">Informations personnelles</span>
          </VCardTitle>
          <VCardText class="pa-6">
            <VRow>
              <VCol cols="12" md="6">
                <VTextField
                  v-model="form.firstname"
                  label="Prénom *"
                  prepend-inner-icon="tabler-user"
                  :error-messages="formError.firstname"
                />
              </VCol>
              <VCol cols="12" md="6">
                <VTextField
                  v-model="form.lastname"
                  label="Nom *"
                  prepend-inner-icon="tabler-user"
                  :error-messages="formError.lastname"
                />
              </VCol>
              <VCol cols="12" md="6">
                <VTextField
                  v-model="form.username"
                  label="Nom d'utilisateur *"
                  prepend-inner-icon="tabler-at"
                  :error-messages="formError.username"
                />
              </VCol>
              <VCol cols="12" md="6">
                <VTextField
                  v-model="form.email"
                  label="Email *"
                  type="email"
                  prepend-inner-icon="tabler-mail"
                  :error-messages="formError.email"
                />
              </VCol>
              <VCol cols="12" md="4">
                <VSelect
                  v-model="form.dial_code"
                  :items="phoneCodes"
                  label="Indicatif"
                  prepend-inner-icon="tabler-world"
                  :error-messages="formError.dial_code"
                />
              </VCol>
              <VCol cols="12" md="8">
                <VTextField
                  v-model="form.mobile"
                  label="Téléphone"
                  prepend-inner-icon="tabler-phone"
                  :error-messages="formError.mobile"
                />
              </VCol>
              <VCol cols="12" md="6">
                <VSelect
                  v-model="form.country_code"
                  :items="countries"
                  label="Pays"
                  prepend-inner-icon="tabler-map"
                  :error-messages="formError.country_code"
                  clearable
                />
              </VCol>
              <VCol cols="12" md="6">
                <VTextField
                  v-model="form.city"
                  label="Ville"
                  prepend-inner-icon="tabler-map-pin"
                  :error-messages="formError.city"
                />
              </VCol>
            </VRow>
          </VCardText>
        </VCard>
      </VCol>

      <!-- ── Sidebar droite ── -->
      <VCol cols="12" md="4">

        <!-- Statut du compte -->
        <VCard class="mb-6">
          <VCardTitle class="pa-6 pb-2">
            <span class="text-h6 font-weight-bold">Statut du compte</span>
          </VCardTitle>
          <VCardText class="pa-6">
            <div class="d-flex align-center justify-space-between mb-4">
              <div>
                <p class="text-body-1 font-weight-medium mb-1">
                  Compte {{ form.status ? 'actif' : 'inactif' }}
                </p>
                <p class="text-caption text-medium-emphasis mb-0">
                  {{ form.status ? "L'organisateur peut se connecter" : 'Accès bloqué' }}
                </p>
              </div>
              <VSwitch v-model="form.status" color="success" hide-details />
            </div>

            <VDivider class="my-4" />

            <div class="d-flex align-center justify-space-between">
              <div>
                <p class="text-body-1 font-weight-medium mb-1">
                  Mis en avant
                </p>
                <p class="text-caption text-medium-emphasis mb-0">
                  {{ form.is_featured ? 'Affiché en vedette' : 'Affichage normal' }}
                </p>
              </div>
              <VSwitch v-model="form.is_featured" color="warning" hide-details />
            </div>
          </VCardText>
        </VCard>

        <!-- Info -->
        <VCard class="mb-6" color="info" variant="tonal">
          <VCardText class="pa-6">
            <div class="d-flex align-center gap-2 mb-2">
              <VIcon icon="tabler-info-circle" size="20" />
              <span class="text-subtitle-2 font-weight-bold">À noter</span>
            </div>
            <p class="text-caption mb-0">
              Le mot de passe ne peut pas être modifié depuis cette page.
              Demandez à l'organisateur d'utiliser la fonction "Mot de passe oublié".
            </p>
          </VCardText>
        </VCard>

        <!-- Actions -->
        <VCard>
          <VCardText class="pa-6">
            <VBtn
              color="primary"
              block
              size="large"
              :loading="isSaving"
              prepend-icon="tabler-device-floppy"
              @click="updateOrganizer"
            >
              Enregistrer les modifications
            </VBtn>
            <VBtn
              variant="outlined"
              color="secondary"
              block
              size="large"
              class="mt-3"
              @click="router.push('/admin/organizers')"
            >
              Annuler
            </VBtn>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>
  </div>
</template>