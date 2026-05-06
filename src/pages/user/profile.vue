<script setup lang="ts">
import { onMounted, ref } from 'vue'
import TwoFASettings from '@/components/TwoFASettings.vue'

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

const isLoading          = ref(true)
const isSaving           = ref(false)
const isChangingPassword = ref(false)
const successMsg         = ref('')
const errorMsg           = ref('')
const pwdSuccess         = ref('')
const pwdError           = ref('')
const user               = ref<any>({})
const passwordForm       = ref({ old_password: '', new_password: '', new_password_confirm: '' })

const fetchProfile = async () => {
  isLoading.value = true
  try {
    const data = await apiFetch('/users/me/')
    user.value = data.data || data
    localStorage.setItem('user', JSON.stringify(user.value))
  } catch {
    try { user.value = JSON.parse(localStorage.getItem('user') || '{}') } catch {}
  } finally {
    isLoading.value = false
  }
}

const updateProfile = async () => {
  isSaving.value = true
  successMsg.value = ''
  errorMsg.value = ''
  try {
    const data = await apiFetch('/users/me/', {
      method: 'PATCH',
      body: JSON.stringify({
        firstname:    user.value.firstname,
        lastname:     user.value.lastname,
        username:     user.value.username,
        mobile:       user.value.mobile,
        dial_code:    user.value.dial_code,
        country_name: user.value.country_name,
        city:         user.value.city,
        state:        user.value.state,
        zip:          user.value.zip,
        address:      user.value.address,
      }),
    })
    user.value = data.data || data
    localStorage.setItem('user', JSON.stringify(user.value))
    successMsg.value = 'Profil mis à jour !'
  } catch {
    errorMsg.value = 'Erreur lors de la mise à jour'
  } finally {
    isSaving.value = false
    setTimeout(() => { successMsg.value = ''; errorMsg.value = '' }, 3000)
  }
}

const changePassword = async () => {
  isChangingPassword.value = true
  pwdSuccess.value = ''
  pwdError.value = ''
  if (passwordForm.value.new_password !== passwordForm.value.new_password_confirm) {
    pwdError.value = 'Les mots de passe ne correspondent pas'
    isChangingPassword.value = false
    return
  }
  try {
    await apiFetch('/users/change_password/', {
      method: 'POST',
      body: JSON.stringify(passwordForm.value),
    })
    pwdSuccess.value = 'Mot de passe modifié !'
    passwordForm.value = { old_password: '', new_password: '', new_password_confirm: '' }
  } catch {
    pwdError.value = 'Erreur : vérifiez votre ancien mot de passe'
  } finally {
    isChangingPassword.value = false
    setTimeout(() => { pwdSuccess.value = ''; pwdError.value = '' }, 3000)
  }
}

function formatDate(d: string | null): string {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('fr-FR', { day: '2-digit', month: 'long', year: 'numeric' })
}

function getInitials(): string {
  const name = `${user.value.firstname || ''} ${user.value.lastname || ''}`.trim()
  if (!name) return user.value.email?.[0]?.toUpperCase() || 'U'
  const parts = name.split(' ')
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return name[0].toUpperCase()
}

onMounted(() => { fetchProfile() })
</script>

<template>
  <div>
    <div class="mb-6">
      <h4 class="text-h4 font-weight-bold">Mon Profil</h4>
      <p class="text-body-1 text-medium-emphasis mt-1">Gérez vos informations personnelles</p>
    </div>

    <div v-if="isLoading" class="d-flex justify-center py-16">
      <VProgressCircular indeterminate color="primary" size="48" />
    </div>

    <template v-else>
      <!-- Profile Header -->
      <VCard class="mb-6">
        <VCardText class="d-flex align-center gap-6 pa-6">
          <VAvatar color="primary" variant="tonal" size="80">
            <VImg v-if="user.profile_image" :src="user.profile_image" />
            <span v-else class="text-h4 font-weight-medium">{{ getInitials() }}</span>
          </VAvatar>
          <div>
            <h5 class="text-h5 font-weight-bold">
              {{ user.full_name || `${user.firstname || ''} ${user.lastname || ''}`.trim() || user.email }}
            </h5>
            <p class="text-body-1 text-medium-emphasis mb-2">{{ user.email }}</p>
            <div class="d-flex gap-2">
              <VChip :color="user.ev ? 'success' : 'warning'" size="small" variant="tonal">
                {{ user.ev ? 'Email vérifié' : 'Email non vérifié' }}
              </VChip>
              <VChip :color="user.sv ? 'success' : 'warning'" size="small" variant="tonal">
                {{ user.sv ? 'Mobile vérifié' : 'Mobile non vérifié' }}
              </VChip>
            </div>
          </div>
        </VCardText>
      </VCard>

      <VRow>
        <!-- Edit Profile -->
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
              <VAlert v-if="successMsg" type="success" variant="tonal" class="mb-4">{{ successMsg }}</VAlert>
              <VAlert v-if="errorMsg"   type="error"   variant="tonal" class="mb-4">{{ errorMsg }}</VAlert>
              <VRow>
                <VCol cols="12" md="6">
                  <VTextField v-model="user.firstname"    label="Prénom"    prepend-inner-icon="tabler-user" />
                </VCol>
                <VCol cols="12" md="6">
                  <VTextField v-model="user.lastname"     label="Nom"       prepend-inner-icon="tabler-user" />
                </VCol>
                <VCol cols="12" md="6">
                  <VTextField v-model="user.username"     label="Username"  prepend-inner-icon="tabler-at" />
                </VCol>
                <VCol cols="12" md="6">
                  <VTextField v-model="user.mobile"       label="Mobile"    prepend-inner-icon="tabler-phone" />
                </VCol>
                <VCol cols="12" md="6">
                  <VTextField v-model="user.country_name" label="Pays"      prepend-inner-icon="tabler-world" />
                </VCol>
                <VCol cols="12" md="6">
                  <VTextField v-model="user.city"         label="Ville"     prepend-inner-icon="tabler-map-pin" />
                </VCol>
                <VCol cols="12">
                  <VTextarea v-model="user.address" label="Adresse" rows="2" prepend-inner-icon="tabler-home" />
                </VCol>
              </VRow>
            </VCardText>
            <VDivider />
            <VCardActions class="pa-6">
              <VSpacer />
              <VBtn color="primary" :loading="isSaving" prepend-icon="tabler-device-floppy" @click="updateProfile">
                Enregistrer
              </VBtn>
            </VCardActions>
          </VCard>
        </VCol>

        <!-- Side -->
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
                  <p class="text-caption text-medium-emphasis mb-1">Solde</p>
                  <p class="text-body-2 font-weight-bold text-primary">{{ Number(user.balance || 0).toFixed(3) }} DT</p>
                </div>
                <div>
                  <p class="text-caption text-medium-emphasis mb-1">Inscrit le</p>
                  <p class="text-body-2 font-weight-medium">{{ formatDate(user.created_at) }}</p>
                </div>
              </div>
            </VCardText>
          </VCard>

          <!-- Change Password -->
          <VCard class="mb-6">
            <VCardTitle class="pa-6">
              <div class="d-flex align-center gap-2">
                <VIcon icon="tabler-lock" size="24" />
                <span class="text-h6 font-weight-bold">Mot de passe</span>
              </div>
            </VCardTitle>
            <VDivider />
            <VCardText class="pa-6">
              <VAlert v-if="pwdSuccess" type="success" variant="tonal" class="mb-4">{{ pwdSuccess }}</VAlert>
              <VAlert v-if="pwdError"   type="error"   variant="tonal" class="mb-4">{{ pwdError }}</VAlert>
              <VTextField v-model="passwordForm.old_password"          label="Ancien mot de passe" type="password" prepend-inner-icon="tabler-lock"       class="mb-4" />
              <VTextField v-model="passwordForm.new_password"          label="Nouveau mot de passe" type="password" prepend-inner-icon="tabler-lock-plus"  class="mb-4" />
              <VTextField v-model="passwordForm.new_password_confirm"  label="Confirmer"            type="password" prepend-inner-icon="tabler-lock-check" class="mb-4" />
              <VBtn color="warning" block :loading="isChangingPassword" prepend-icon="tabler-key" @click="changePassword">
                Changer le mot de passe
              </VBtn>
            </VCardText>
          </VCard>

          <!-- 2FA -->
          <VCard>
            <VCardTitle class="pa-6">
              <div class="d-flex align-center gap-2">
                <VIcon icon="tabler-shield-lock" size="24" />
                <span class="text-h6 font-weight-bold">Double authentification</span>
              </div>
            </VCardTitle>
            <VDivider />
            <VCardText class="pa-4">
              <TwoFASettings />
            </VCardText>
          </VCard>

        </VCol>
      </VRow>
    </template>
  </div>
</template>