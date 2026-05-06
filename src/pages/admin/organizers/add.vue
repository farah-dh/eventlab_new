<script setup lang="ts">
import { ref } from 'vue'

const router = useRouter()

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

const isSaving = ref(false)
const formError = ref<Record<string, string>>({})
const formErrorMsg = ref('')
const successMsg = ref('')

const showPassword = ref(false)
const showPassword2 = ref(false)

const form = ref({
  organization_name: '',
  short_description: '',
  long_description: '',
  first_name: '',
  last_name: '',
  username: '',
  email: '',
  dial_code: '+216',
  phone: '',
  country_code: '',
  city: '',
  password: '',
  password_confirm: '',
  is_active: true,
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

const saveOrganizer = async () => {
  formError.value = {}
  formErrorMsg.value = ''

  if (form.value.password !== form.value.password_confirm) {
    formError.value.password_confirm = 'Les mots de passe ne correspondent pas'
    return
  }

  isSaving.value = true
  try {
    // 1) Création de l'organisateur (champs de base acceptés par l'API POST)
    const created = await apiFetch('/organizers/', {
      method: 'POST',
      body: JSON.stringify({
        organization_name: form.value.organization_name,
        firstname:         form.value.first_name,
        lastname:          form.value.last_name,
        username:          form.value.username,
        email:             form.value.email,
        mobile:            form.value.phone,
        dial_code:         form.value.dial_code,
        country_code:      form.value.country_code,
        password:          form.value.password,
        password_confirm:  form.value.password_confirm,
      }),
    })

    // 2) Mise à jour des champs supplémentaires via PATCH
    if (created?.id) {
      try {
        await apiFetch(`/organizers/${created.id}/`, {
          method: 'PATCH',
          body: JSON.stringify({
            short_description: form.value.short_description,
            long_description:  form.value.long_description,
            city:              form.value.city,
            status:            form.value.is_active,
          }),
        })
      }
      catch (patchErr) {
        console.warn('PATCH infos supplémentaires a échoué :', patchErr)
      }
    }

    successMsg.value = '✅ Organisateur créé avec succès !'
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
      formErrorMsg.value = err?.data?.message || '❌ Erreur lors de la création.'
    }
  }
  finally {
    isSaving.value = false
  }
}
</script>

<template>
  <div>
    <!-- ── Header ── -->
    <div class="d-flex align-center gap-3 mb-6">
      <VBtn icon variant="text" @click="router.push('/admin/organizers')">
        <VIcon icon="tabler-arrow-left" size="20" />
      </VBtn>
      <div>
        <h4 class="text-h4 font-weight-bold">Ajouter un organisateur</h4>
        <p class="text-body-1 text-medium-emphasis mt-1">Créez un nouveau compte organisateur</p>
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

    <VRow>
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
                  v-model="form.first_name"
                  label="Prénom *"
                  prepend-inner-icon="tabler-user"
                  :error-messages="formError.firstname"
                />
              </VCol>
              <VCol cols="12" md="6">
                <VTextField
                  v-model="form.last_name"
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
                  v-model="form.phone"
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

        <!-- Section Mot de passe -->
        <VCard>
          <VCardTitle class="pa-6 pb-2">
            <span class="text-h6 font-weight-bold">Mot de passe</span>
          </VCardTitle>
          <VCardText class="pa-6">
            <VRow>
              <VCol cols="12" md="6">
                <VTextField
                  v-model="form.password"
                  label="Mot de passe *"
                  :type="showPassword ? 'text' : 'password'"
                  prepend-inner-icon="tabler-lock"
                  :append-inner-icon="showPassword ? 'tabler-eye-off' : 'tabler-eye'"
                  :error-messages="formError.password"
                  @click:append-inner="showPassword = !showPassword"
                />
              </VCol>
              <VCol cols="12" md="6">
                <VTextField
                  v-model="form.password_confirm"
                  label="Confirmer *"
                  :type="showPassword2 ? 'text' : 'password'"
                  prepend-inner-icon="tabler-lock-check"
                  :append-inner-icon="showPassword2 ? 'tabler-eye-off' : 'tabler-eye'"
                  :error-messages="formError.password_confirm"
                  @click:append-inner="showPassword2 = !showPassword2"
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
            <div class="d-flex align-center justify-space-between">
              <div>
                <p class="text-body-1 font-weight-medium mb-1">
                  Compte {{ form.is_active ? 'actif' : 'inactif' }}
                </p>
                <p class="text-caption text-medium-emphasis mb-0">
                  {{ form.is_active ? "L'organisateur peut se connecter" : 'Accès bloqué' }}
                </p>
              </div>
              <VSwitch v-model="form.is_active" color="success" hide-details />
            </div>
          </VCardText>
        </VCard>

        <!-- KYC info -->
        <VCard class="mb-6" color="warning" variant="tonal">
          <VCardText class="pa-6">
            <div class="d-flex align-center gap-2 mb-2">
              <VIcon icon="tabler-shield-check" size="20" />
              <span class="text-subtitle-2 font-weight-bold">Vérification KYC</span>
            </div>
            <p class="text-caption mb-3">
              Après la création, l'organisateur devra soumettre ses documents d'identité
              pour la vérification KYC avant de pouvoir publier des événements.
            </p>
            <VChip size="small" color="warning" variant="flat">
              En attente après création
            </VChip>
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
              prepend-icon="tabler-plus"
              @click="saveOrganizer"
            >
              Créer l'organisateur
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