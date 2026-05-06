<script setup lang="ts">
import { onMounted, ref } from 'vue'

// ─── Config API ───
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'

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
      ...(options.headers as Record<string, string>),
    },
  })
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json()
}

// ─── State ───
const isLoading = ref(true)
const isSaving = ref(false)
const isChangingPassword = ref(false)
const successMessage = ref('')
const errorMessage = ref('')
const passwordSuccess = ref('')
const passwordError = ref('')

const user = ref<any>({})
const passwordForm = ref({
  old_password: '',
  new_password: '',
  new_password_confirm: '',
})

// ─── Fetch Profile ───
const fetchProfile = async () => {
  isLoading.value = true
  try {
    const data = await apiFetch('/users/me/')
    // L'API retourne { status: true, data: {...} } ou directement les données
    user.value = data.data || data
    // Mettre à jour le localStorage
    localStorage.setItem('user', JSON.stringify(user.value))
  }
  catch (err) {
    console.error('Erreur chargement profil:', err)
    // Fallback sur le localStorage
    try {
      const stored = localStorage.getItem('user')
      if (stored) user.value = JSON.parse(stored)
    } catch {}
  }
  finally {
    isLoading.value = false
  }
}

// ─── Update Profile ───
const updateProfile = async () => {
  isSaving.value = true
  successMessage.value = ''
  errorMessage.value = ''
  try {
    const payload = {
      firstname: user.value.firstname,
      lastname: user.value.lastname,
      username: user.value.username,
      mobile: user.value.mobile,
      dial_code: user.value.dial_code,
      country_name: user.value.country_name,
      city: user.value.city,
      state: user.value.state,
      zip: user.value.zip,
      address: user.value.address,
      country_code: user.value.country_code,
    }
    const data = await apiFetch('/users/me/', { method: 'PATCH', body: JSON.stringify(payload) })
    user.value = data.data || data
    localStorage.setItem('user', JSON.stringify(user.value))
    successMessage.value = 'Profil mis à jour avec succès !'
  }
  catch (err) {
    errorMessage.value = 'Erreur lors de la mise à jour du profil'
    console.error(err)
  }
  finally {
    isSaving.value = false
    setTimeout(() => { successMessage.value = ''; errorMessage.value = '' }, 3000)
  }
}

// ─── Change Password ───
const changePassword = async () => {
  isChangingPassword.value = true
  passwordSuccess.value = ''
  passwordError.value = ''

  if (passwordForm.value.new_password !== passwordForm.value.new_password_confirm) {
    passwordError.value = 'Les mots de passe ne correspondent pas'
    isChangingPassword.value = false
    return
  }

  if (passwordForm.value.new_password.length < 8) {
    passwordError.value = 'Le mot de passe doit contenir au moins 8 caractères'
    isChangingPassword.value = false
    return
  }

  try {
    await apiFetch('/users/change_password/', {
      method: 'POST',
      body: JSON.stringify(passwordForm.value),
    })
    passwordSuccess.value = 'Mot de passe modifié avec succès !'
    passwordForm.value = { old_password: '', new_password: '', new_password_confirm: '' }
  }
  catch (err) {
    passwordError.value = 'Erreur : vérifiez votre ancien mot de passe'
    console.error(err)
  }
  finally {
    isChangingPassword.value = false
    setTimeout(() => { passwordSuccess.value = ''; passwordError.value = '' }, 3000)
  }
}

// ─── Helpers ───
function formatDate(dateString: string | null): string {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('fr-FR', { day: '2-digit', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function getUserInitials(): string {
  const name = `${user.value.firstname || ''} ${user.value.lastname || ''}`.trim()
  if (!name) return user.value.email?.[0]?.toUpperCase() || 'A'
  const parts = name.split(' ')
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return name[0].toUpperCase()
}

// ─── Init ───
onMounted(() => { fetchProfile() })
</script>

<template>
  <div>
    <!-- Page Header -->
    <div class="mb-6">
      <h4 class="text-h4 font-weight-bold">Mon Profil</h4>
      <p class="text-body-1 text-medium-emphasis mt-1">Gérez vos informations personnelles</p>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="d-flex flex-column align-center justify-center py-16">
      <VProgressCircular indeterminate color="primary" size="48" />
      <p class="text-body-1 text-medium-emphasis mt-4">Chargement du profil...</p>
    </div>

    <template v-else>
      <!-- Profile Card -->
      <VCard class="mb-6">
        <VCardText class="d-flex align-center gap-6 pa-6">
          <VAvatar color="primary" variant="tonal" size="80">
            <VImg v-if="user.profile_image" :src="user.profile_image" />
            <span v-else class="text-h4 font-weight-medium">{{ getUserInitials() }}</span>
          </VAvatar>
          <div>
            <h5 class="text-h5 font-weight-bold">
              {{ user.full_name || `${user.firstname || ''} ${user.lastname || ''}`.trim() || user.email }}
            </h5>
            <p class="text-body-1 text-medium-emphasis mb-1">{{ user.email }}</p>
            <div class="d-flex gap-2">
              <VChip color="primary" size="small" variant="tonal">
                <VIcon icon="tabler-shield-star" size="14" start />
                Administrateur
              </VChip>
              <VChip :color="user.is_active ? 'success' : 'error'" size="small" variant="tonal">
                {{ user.is_active ? 'Actif' : 'Inactif' }}
              </VChip>
              <VChip :color="user.ev ? 'success' : 'warning'" size="small" variant="tonal">
                <VIcon :icon="user.ev ? 'tabler-mail-check' : 'tabler-mail-x'" size="14" start />
                {{ user.ev ? 'Email vérifié' : 'Email non vérifié' }}
              </VChip>
            </div>
          </div>
        </VCardText>
      </VCard>

      <!-- Account Info -->
      <VRow>
        <!-- Info Card -->
        <VCol cols="12" md="8">
          <VCard>
            <VCardTitle class="pa-6">
              <div class="d-flex align-center gap-2">
                <VIcon icon="tabler-user-edit" size="24" />
                <span class="text-h6 font-weight-bold">Informations personnelles</span>
              </div>
            </VCardTitle>

            <VDivider />

            <VCardText class="pa-6">
              <VAlert v-if="successMessage" type="success" variant="tonal" class="mb-4">{{ successMessage }}</VAlert>
              <VAlert v-if="errorMessage" type="error" variant="tonal" class="mb-4">{{ errorMessage }}</VAlert>

              <VRow>
                <VCol cols="12" md="6">
                  <VTextField v-model="user.firstname" label="Prénom" prepend-inner-icon="tabler-user" />
                </VCol>
                <VCol cols="12" md="6">
                  <VTextField v-model="user.lastname" label="Nom" prepend-inner-icon="tabler-user" />
                </VCol>
                <VCol cols="12" md="6">
                  <VTextField v-model="user.email" label="Email" prepend-inner-icon="tabler-mail" disabled />
                </VCol>
                <VCol cols="12" md="6">
                  <VTextField v-model="user.username" label="Username" prepend-inner-icon="tabler-at" />
                </VCol>
                <VCol cols="12" md="4">
                  <VTextField v-model="user.dial_code" label="Indicatif" prepend-inner-icon="tabler-phone" placeholder="+216" />
                </VCol>
                <VCol cols="12" md="8">
                  <VTextField v-model="user.mobile" label="Mobile" prepend-inner-icon="tabler-phone" />
                </VCol>
                <VCol cols="12" md="6">
                  <VTextField v-model="user.country_name" label="Pays" prepend-inner-icon="tabler-world" />
                </VCol>
                <VCol cols="12" md="6">
                  <VTextField v-model="user.city" label="Ville" prepend-inner-icon="tabler-map-pin" />
                </VCol>
                <VCol cols="12" md="4">
                  <VTextField v-model="user.state" label="État / Région" />
                </VCol>
                <VCol cols="12" md="4">
                  <VTextField v-model="user.zip" label="Code postal" />
                </VCol>
                <VCol cols="12" md="4">
                  <VTextField v-model="user.country_code" label="Code pays" placeholder="TN" />
                </VCol>
                <VCol cols="12">
                  <VTextarea v-model="user.address" label="Adresse complète" rows="2" prepend-inner-icon="tabler-home" />
                </VCol>
              </VRow>
            </VCardText>

            <VDivider />

            <VCardActions class="pa-6">
              <VSpacer />
              <VBtn color="primary" :loading="isSaving" prepend-icon="tabler-device-floppy" @click="updateProfile">
                Enregistrer les modifications
              </VBtn>
            </VCardActions>
          </VCard>
        </VCol>

        <!-- Side Cards -->
        <VCol cols="12" md="4">
          <!-- Account Details -->
          <VCard class="mb-6">
            <VCardTitle class="pa-6">
              <div class="d-flex align-center gap-2">
                <VIcon icon="tabler-info-circle" size="24" />
                <span class="text-h6 font-weight-bold">Détails du compte</span>
              </div>
            </VCardTitle>

            <VDivider />

            <VCardText class="pa-6">
              <div class="d-flex flex-column gap-4">
                <div>
                  <p class="text-caption text-medium-emphasis mb-1">ID</p>
                  <p class="text-body-2 font-weight-medium">{{ user.id }}</p>
                </div>
                <div>
                  <p class="text-caption text-medium-emphasis mb-1">Solde</p>
                  <p class="text-body-2 font-weight-medium">{{ Number.parseFloat(user.balance || 0).toFixed(3) }} DT</p>
                </div>
                <div>
                  <p class="text-caption text-medium-emphasis mb-1">Profil complet</p>
                  <VChip :color="user.profile_complete ? 'success' : 'warning'" size="small" variant="tonal">
                    {{ user.profile_complete ? 'Oui' : 'Non' }}
                  </VChip>
                </div>
                <div>
                  <p class="text-caption text-medium-emphasis mb-1">2FA</p>
                  <VChip :color="user.ts ? 'success' : 'default'" size="small" variant="tonal">
                    {{ user.ts ? 'Activé' : 'Désactivé' }}
                  </VChip>
                </div>
                <div>
                  <p class="text-caption text-medium-emphasis mb-1">Inscrit le</p>
                  <p class="text-body-2 font-weight-medium">{{ formatDate(user.created_at) }}</p>
                </div>
                <div>
                  <p class="text-caption text-medium-emphasis mb-1">Dernière modification</p>
                  <p class="text-body-2 font-weight-medium">{{ formatDate(user.updated_at) }}</p>
                </div>
              </div>
            </VCardText>
          </VCard>

          <!-- Change Password -->
          <VCard>
            <VCardTitle class="pa-6">
              <div class="d-flex align-center gap-2">
                <VIcon icon="tabler-lock" size="24" />
                <span class="text-h6 font-weight-bold">Changer le mot de passe</span>
              </div>
            </VCardTitle>

            <VDivider />

            <VCardText class="pa-6">
              <VAlert v-if="passwordSuccess" type="success" variant="tonal" class="mb-4">{{ passwordSuccess }}</VAlert>
              <VAlert v-if="passwordError" type="error" variant="tonal" class="mb-4">{{ passwordError }}</VAlert>

              <VTextField
                v-model="passwordForm.old_password"
                label="Ancien mot de passe"
                type="password"
                prepend-inner-icon="tabler-lock"
                class="mb-4"
              />
              <VTextField
                v-model="passwordForm.new_password"
                label="Nouveau mot de passe"
                type="password"
                prepend-inner-icon="tabler-lock-plus"
                class="mb-4"
              />
              <VTextField
                v-model="passwordForm.new_password_confirm"
                label="Confirmer le mot de passe"
                type="password"
                prepend-inner-icon="tabler-lock-check"
                class="mb-4"
              />
              <VBtn
                color="warning"
                block
                :loading="isChangingPassword"
                prepend-icon="tabler-key"
                @click="changePassword"
              >
                Changer le mot de passe
              </VBtn>
            </VCardText>
          </VCard>
        </VCol>
      </VRow>
    </template>
  </div>
</template>