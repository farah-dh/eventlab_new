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

const isSaving   = ref(false)
const formError  = ref<Record<string, string>>({})
const formErrorMsg = ref('')
const successMsg = ref('')

const form = ref({
  email:            '',
  firstname:        '',
  lastname:         '',
  username:         '',
  mobile:           '',
  password:         '',
  password_confirm: '',
  country_name:     '',
  city:             '',
  is_active:        true,
})

const showPassword  = ref(false)
const showPassword2 = ref(false)

const saveUser = async () => {
  formError.value = {}
  formErrorMsg.value = ''
  isSaving.value = true
  try {
    await apiFetch('/auth/register/', {
      method: 'POST',
      body: JSON.stringify({
        email:            form.value.email,
        firstname:        form.value.firstname,
        lastname:         form.value.lastname,
        username:         form.value.username,
        mobile:           form.value.mobile,
        password:         form.value.password,
        password_confirm: form.value.password_confirm,
        country_name:     form.value.country_name,
        city:             form.value.city,
        is_active:        form.value.is_active,
      }),
    })
    successMsg.value = '✅ Utilisateur créé avec succès !'
    setTimeout(() => router.push('/admin/users'), 1500)
  }
  catch (err: any) {
    if (err?.data?.errors && typeof err.data.errors === 'object') {
      const mapped: Record<string, string> = {}
      for (const [field, msg] of Object.entries(err.data.errors)) {
        mapped[field] = Array.isArray(msg) ? (msg as string[]).join(', ') : String(msg)
      }
      formError.value = mapped
    } else {
      formErrorMsg.value = err?.data?.message || '❌ Erreur lors de la création.'
    }
  }
  finally { isSaving.value = false }
}
</script>

<template>
  <div>
    <!-- ── Header ── -->
    <div class="d-flex align-center gap-3 mb-6">
      <VBtn icon variant="text" @click="router.push('/admin/users')">
        <VIcon icon="tabler-arrow-left" size="20" />
      </VBtn>
      <div>
        <h4 class="text-h4 font-weight-bold">Ajouter un utilisateur</h4>
        <p class="text-body-1 text-medium-emphasis mt-1">Créez un nouveau compte utilisateur</p>
      </div>
    </div>

    <!-- ── Notifications ── -->
    <VAlert v-if="successMsg" type="success" variant="tonal" class="mb-4">{{ successMsg }}</VAlert>
    <VAlert v-if="formErrorMsg" type="error" variant="tonal" closable class="mb-4" @click:close="formErrorMsg = ''">{{ formErrorMsg }}</VAlert>

    <VRow>
      <!-- ── Formulaire principal ── -->
      <VCol cols="12" md="8">
        <VCard class="mb-6">
          <VCardTitle class="pa-6 pb-2">
            <span class="text-h6 font-weight-bold">Informations personnelles</span>
          </VCardTitle>
          <VCardText class="pa-6">
            <VRow>
              <VCol cols="12" md="6">
                <VTextField
                  v-model="form.firstname"
                  label="Prénom"
                  prepend-inner-icon="tabler-user"
                  :error-messages="formError.firstname"
                />
              </VCol>
              <VCol cols="12" md="6">
                <VTextField
                  v-model="form.lastname"
                  label="Nom"
                  prepend-inner-icon="tabler-user"
                  :error-messages="formError.lastname"
                />
              </VCol>
              <VCol cols="12">
                <VTextField
                  v-model="form.email"
                  label="Email *"
                  type="email"
                  prepend-inner-icon="tabler-mail"
                  :error-messages="formError.email"
                />
              </VCol>
              <VCol cols="12" md="6">
                <VTextField
                  v-model="form.username"
                  label="Nom d'utilisateur"
                  prepend-inner-icon="tabler-at"
                  :error-messages="formError.username"
                />
              </VCol>
              <VCol cols="12" md="6">
                <VTextField
                  v-model="form.mobile"
                  label="Mobile"
                  prepend-inner-icon="tabler-phone"
                  :error-messages="formError.mobile"
                />
              </VCol>
              <VCol cols="12" md="6">
                <VTextField
                  v-model="form.country_name"
                  label="Pays"
                  prepend-inner-icon="tabler-world"
                  :error-messages="formError.country_name"
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
        <VCard class="mb-6">
          <VCardTitle class="pa-6 pb-2">
            <span class="text-h6 font-weight-bold">Statut du compte</span>
          </VCardTitle>
          <VCardText class="pa-6">
            <div class="d-flex align-center justify-space-between">
              <div>
                <p class="text-body-1 font-weight-medium mb-1">Compte actif</p>
                <p class="text-caption text-medium-emphasis mb-0">
                  {{ form.is_active ? "L'utilisateur peut se connecter" : "L'utilisateur ne peut pas se connecter" }}
                </p>
              </div>
              <VSwitch v-model="form.is_active" color="success" hide-details />
            </div>
          </VCardText>
        </VCard>

        <VCard>
          <VCardText class="pa-6">
            <VBtn
              color="primary"
              block
              size="large"
              :loading="isSaving"
              prepend-icon="tabler-user-plus"
              @click="saveUser"
            >
              Créer l'utilisateur
            </VBtn>
            <VBtn
              variant="outlined"
              color="secondary"
              block
              size="large"
              class="mt-3"
              @click="router.push('/admin/users')"
            >
              Annuler
            </VBtn>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>
  </div>
</template>