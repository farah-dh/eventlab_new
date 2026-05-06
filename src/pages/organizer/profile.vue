<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'

definePage({
  meta: {
    layout: 'organizer',
  },
})

// ── Config API ────────────────────────────────────────────────────────────────
const API = 'http://127.0.0.1:8001/api/v1'
const getToken = () => localStorage.getItem('organizer_token') || ''

const apiFetch = async (endpoint: string, options: RequestInit = {}) => {
  const token = getToken()
  const res = await fetch(`${API}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Token ${token}` }),
      ...options.headers,
    },
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  if (res.status === 204) return null
  return res.json()
}

const organizerLocal = computed(() => {
  try { return JSON.parse(localStorage.getItem('organizer') || '{}') }
  catch { return {} }
})

// ── State ─────────────────────────────────────────────────────────────────────
const isLoading      = ref(true)
const isSaving       = ref(false)
const isChangingPwd  = ref(false)
const activeTab      = ref('info')
const successMsg     = ref('')
const errorMsg       = ref('')
const pwdSuccess     = ref('')
const pwdError       = ref('')

// ── Profile data ──────────────────────────────────────────────────────────────
const profile = ref<any>({})

const form = ref({
  firstname:         '',
  lastname:          '',
  organization_name: '',
  email:             '',
  phone:             '',
  bio:               '',
  website:           '',
  address:           '',
})

const pwdForm = ref({
  old_password:  '',
  new_password:  '',
  confirm:       '',
})

const showOldPwd  = ref(false)
const showNewPwd  = ref(false)
const showConfPwd = ref(false)

// ── Avatar upload ─────────────────────────────────────────────────────────────
const avatarFile     = ref<File | null>(null)
const avatarPreview  = ref<string | null>(null)
const isUploadAvatar = ref(false)

const userInitials = computed(() => {
  const f = form.value.firstname
  const l = form.value.lastname
  const o = form.value.organization_name
  if (f && l) return `${f[0]}${l[0]}`.toUpperCase()
  if (o) return o[0].toUpperCase()
  return 'O'
})

// ── Fetch profile ─────────────────────────────────────────────────────────────
const fetchProfile = async () => {
  isLoading.value = true
  try {
    const id = organizerLocal.value.id
    if (!id) throw new Error('No organizer id')
    const data = await apiFetch(`/organizers/${id}/`)
    profile.value = data
    form.value = {
      firstname:         data.firstname         || data.first_name  || '',
      lastname:          data.lastname          || data.last_name   || '',
      organization_name: data.organization_name || '',
      email:             data.email             || '',
      phone:             data.phone             || data.phone_number || '',
      bio:               data.bio               || data.description  || '',
      website:           data.website           || '',
      address:           data.address           || '',
    }
    if (data.avatar || data.logo || data.profile_picture)
      avatarPreview.value = data.avatar || data.logo || data.profile_picture
  }
  catch (e) { console.error(e) }
  finally { isLoading.value = false }
}

// ── Save profile ──────────────────────────────────────────────────────────────
const saveProfile = async () => {
  isSaving.value = true
  successMsg.value = ''
  errorMsg.value = ''
  try {
    const id = organizerLocal.value.id
    const data = await apiFetch(`/organizers/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(form.value),
    })
    // Update localStorage
    const stored = JSON.parse(localStorage.getItem('organizer') || '{}')
    localStorage.setItem('organizer', JSON.stringify({ ...stored, ...data }))
    successMsg.value = 'Profil mis à jour avec succès !'
    setTimeout(() => successMsg.value = '', 4000)
  }
  catch { errorMsg.value = 'Erreur lors de la mise à jour.' }
  finally { isSaving.value = false }
}

// ── Upload avatar ─────────────────────────────────────────────────────────────
const handleAvatarChange = (e: Event) => {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  avatarFile.value = file
  avatarPreview.value = URL.createObjectURL(file)
}

const uploadAvatar = async () => {
  if (!avatarFile.value) return
  isUploadAvatar.value = true
  try {
    const id = organizerLocal.value.id
    const fd = new FormData()
    fd.append('avatar', avatarFile.value)
    const token = getToken()
    const res = await fetch(`${API}/organizers/${id}/`, {
      method: 'PATCH',
      headers: { ...(token && { Authorization: `Token ${token}` }) },
      body: fd,
    })
    if (!res.ok) throw new Error()
    successMsg.value = 'Photo de profil mise à jour !'
    setTimeout(() => successMsg.value = '', 4000)
    avatarFile.value = null
  }
  catch { errorMsg.value = "Erreur lors de l'upload de la photo." }
  finally { isUploadAvatar.value = false }
}

// ── Change password ───────────────────────────────────────────────────────────
const changePassword = async () => {
  pwdError.value = ''
  pwdSuccess.value = ''
  if (!pwdForm.value.old_password) { pwdError.value = 'Entrez votre mot de passe actuel.'; return }
  if (pwdForm.value.new_password.length < 8) { pwdError.value = 'Le nouveau mot de passe doit contenir au moins 8 caractères.'; return }
  if (pwdForm.value.new_password !== pwdForm.value.confirm) { pwdError.value = 'Les mots de passe ne correspondent pas.'; return }

  isChangingPwd.value = true
  try {
    await apiFetch('/users/change_password/', {
      method: 'POST',
      body: JSON.stringify({
        old_password: pwdForm.value.old_password,
        new_password: pwdForm.value.new_password,
      }),
    })
    pwdForm.value = { old_password: '', new_password: '', confirm: '' }
    pwdSuccess.value = 'Mot de passe modifié avec succès !'
    setTimeout(() => pwdSuccess.value = '', 4000)
  }
  catch { pwdError.value = 'Mot de passe actuel incorrect ou erreur serveur.' }
  finally { isChangingPwd.value = false }
}

const pwdStrength = computed(() => {
  const p = pwdForm.value.new_password
  if (!p) return 0
  let score = 0
  if (p.length >= 8) score++
  if (/[A-Z]/.test(p)) score++
  if (/[0-9]/.test(p)) score++
  if (/[^A-Za-z0-9]/.test(p)) score++
  return score
})

const pwdStrengthLabel = computed(() => {
  const labels = ['', 'Faible', 'Moyen', 'Bon', 'Fort']
  return labels[pwdStrength.value] || ''
})

const pwdStrengthColor = computed(() => {
  const colors = ['', '#EF4444', '#F59E0B', '#10B981', '#059669']
  return colors[pwdStrength.value] || ''
})

onMounted(fetchProfile)
</script>

<template>
  <div class="profile-page">

    <!-- ── Header ─────────────────────────────────────────────────────────── -->
    <div class="page-header">
      <div>
        <h2 class="page-title">Mon profil</h2>
        <p class="page-sub">Gérez vos informations personnelles et paramètres</p>
      </div>
    </div>

    <!-- ── Loading ────────────────────────────────────────────────────────── -->
    <div v-if="isLoading" class="center-pad">
      <VProgressCircular indeterminate color="primary" size="36" />
    </div>

    <div v-else class="profile-layout">

      <!-- ── Colonne gauche : Avatar + infos rapides ─────────────────────── -->
      <div class="sidebar-col">
        <div class="avatar-card">
          <div class="avatar-wrap">
            <div class="avatar-circle">
              <img v-if="avatarPreview" :src="avatarPreview" alt="avatar" class="avatar-img">
              <span v-else class="avatar-initials">{{ userInitials }}</span>
            </div>
            <label class="avatar-edit-btn" title="Changer la photo">
              <VIcon icon="tabler-camera" size="14" color="white" />
              <input type="file" accept="image/*" class="d-none" @change="handleAvatarChange">
            </label>
          </div>

          <h3 class="avatar-name">{{ form.firstname }} {{ form.lastname }}</h3>
          <p class="avatar-org">{{ form.organization_name }}</p>
          <p class="avatar-email">{{ form.email }}</p>

          <div v-if="avatarFile" class="mt-3">
            <VBtn
              color="primary"
              size="small"
              block
              :loading="isUploadAvatar"
              @click="uploadAvatar"
            >
              <VIcon start icon="tabler-upload" size="14" />
              Enregistrer la photo
            </VBtn>
          </div>

          <!-- KYC status -->
          <div class="kyc-badge" :class="profile.kyc_status === 'approved' ? 'kyc-approved' : profile.kyc_status === 'pending' ? 'kyc-pending' : 'kyc-none'">
            <VIcon
              :icon="profile.kyc_status === 'approved' ? 'tabler-shield-check' : profile.kyc_status === 'pending' ? 'tabler-shield-half' : 'tabler-shield-x'"
              size="14"
            />
            KYC :
            {{ profile.kyc_status === 'approved' ? 'Approuvé' : profile.kyc_status === 'pending' ? 'En attente' : 'Non soumis' }}
          </div>
        </div>

        <!-- Navigation tabs verticale -->
        <div class="side-nav">
          <button :class="['snav-item', { active: activeTab === 'info' }]" @click="activeTab = 'info'">
            <VIcon icon="tabler-user" size="15" />
            Informations
          </button>
          <button :class="['snav-item', { active: activeTab === 'org' }]" @click="activeTab = 'org'">
            <VIcon icon="tabler-building" size="15" />
            Organisation
          </button>
          <button :class="['snav-item', { active: activeTab === 'security' }]" @click="activeTab = 'security'">
            <VIcon icon="tabler-lock" size="15" />
            Sécurité
          </button>
        </div>
      </div>

      <!-- ── Colonne droite : Formulaires ───────────────────────────────── -->
      <div class="content-col">

        <!-- Alertes globales -->
        <VAlert v-if="successMsg" type="success" variant="tonal" density="compact" class="mb-4" closable @click:close="successMsg = ''">
          {{ successMsg }}
        </VAlert>
        <VAlert v-if="errorMsg" type="error" variant="tonal" density="compact" class="mb-4" closable @click:close="errorMsg = ''">
          {{ errorMsg }}
        </VAlert>

        <!-- ── Tab: Informations personnelles ─────────────────────────── -->
        <div v-show="activeTab === 'info'" class="form-card">
          <div class="form-card-head">
            <VIcon icon="tabler-user" size="18" color="#4F46E5" />
            <div>
              <h3 class="form-card-title">Informations personnelles</h3>
              <p class="form-card-sub">Vos coordonnées de contact</p>
            </div>
          </div>
          <VDivider class="mb-5" />

          <VRow>
            <VCol cols="12" md="6">
              <AppTextField
                v-model="form.firstname"
                label="Prénom"
                placeholder="Ahmed"
                prepend-inner-icon="tabler-user"
              />
            </VCol>
            <VCol cols="12" md="6">
              <AppTextField
                v-model="form.lastname"
                label="Nom"
                placeholder="Ben Ali"
                prepend-inner-icon="tabler-user"
              />
            </VCol>
            <VCol cols="12" md="6">
              <AppTextField
                v-model="form.email"
                label="Email"
                type="email"
                placeholder="ahmed@eventlab.tn"
                prepend-inner-icon="tabler-mail"
              />
            </VCol>
            <VCol cols="12" md="6">
              <AppTextField
                v-model="form.phone"
                label="Téléphone"
                placeholder="+216 XX XXX XXX"
                prepend-inner-icon="tabler-phone"
              />
            </VCol>
            <VCol cols="12">
              <AppTextField
                v-model="form.address"
                label="Adresse"
                placeholder="Rue, Ville, Pays"
                prepend-inner-icon="tabler-map-pin"
              />
            </VCol>
          </VRow>

          <div class="d-flex justify-end mt-4">
            <VBtn color="primary" :loading="isSaving" @click="saveProfile">
              <VIcon start icon="tabler-device-floppy" size="15" />
              Enregistrer
            </VBtn>
          </div>
        </div>

        <!-- ── Tab: Organisation ──────────────────────────────────────── -->
        <div v-show="activeTab === 'org'" class="form-card">
          <div class="form-card-head">
            <VIcon icon="tabler-building" size="18" color="#4F46E5" />
            <div>
              <h3 class="form-card-title">Mon organisation</h3>
              <p class="form-card-sub">Informations de votre structure</p>
            </div>
          </div>
          <VDivider class="mb-5" />

          <VRow>
            <VCol cols="12">
              <AppTextField
                v-model="form.organization_name"
                label="Nom de l'organisation"
                placeholder="EventLab Tunisia"
                prepend-inner-icon="tabler-building"
              />
            </VCol>
            <VCol cols="12" md="6">
              <AppTextField
                v-model="form.website"
                label="Site web"
                placeholder="https://monsite.tn"
                prepend-inner-icon="tabler-world"
              />
            </VCol>
            <VCol cols="12" md="6">
              <AppTextField
                v-model="form.phone"
                label="Téléphone professionnel"
                placeholder="+216 XX XXX XXX"
                prepend-inner-icon="tabler-phone"
              />
            </VCol>
            <VCol cols="12">
              <VTextarea
                v-model="form.bio"
                label="Description / Bio"
                placeholder="Décrivez votre organisation..."
                rows="4"
                prepend-inner-icon="tabler-align-left"
              />
            </VCol>
          </VRow>

          <div class="d-flex justify-end mt-4">
            <VBtn color="primary" :loading="isSaving" @click="saveProfile">
              <VIcon start icon="tabler-device-floppy" size="15" />
              Enregistrer
            </VBtn>
          </div>
        </div>

        <!-- ── Tab: Sécurité ──────────────────────────────────────────── -->
        <div v-show="activeTab === 'security'" class="form-card">
          <div class="form-card-head">
            <VIcon icon="tabler-lock" size="18" color="#4F46E5" />
            <div>
              <h3 class="form-card-title">Changer le mot de passe</h3>
              <p class="form-card-sub">Assurez-vous d'utiliser un mot de passe fort</p>
            </div>
          </div>
          <VDivider class="mb-5" />

          <VAlert v-if="pwdSuccess" type="success" variant="tonal" density="compact" class="mb-4">
            {{ pwdSuccess }}
          </VAlert>
          <VAlert v-if="pwdError" type="error" variant="tonal" density="compact" class="mb-4">
            {{ pwdError }}
          </VAlert>

          <VRow>
            <VCol cols="12">
              <AppTextField
                v-model="pwdForm.old_password"
                label="Mot de passe actuel"
                :type="showOldPwd ? 'text' : 'password'"
                prepend-inner-icon="tabler-lock"
                :append-inner-icon="showOldPwd ? 'tabler-eye-off' : 'tabler-eye'"
                @click:append-inner="showOldPwd = !showOldPwd"
              />
            </VCol>
            <VCol cols="12">
              <AppTextField
                v-model="pwdForm.new_password"
                label="Nouveau mot de passe"
                :type="showNewPwd ? 'text' : 'password'"
                prepend-inner-icon="tabler-lock-plus"
                :append-inner-icon="showNewPwd ? 'tabler-eye-off' : 'tabler-eye'"
                @click:append-inner="showNewPwd = !showNewPwd"
              />
              <!-- Force du mot de passe -->
              <div v-if="pwdForm.new_password" class="pwd-strength">
                <div class="strength-bars">
                  <div
                    v-for="i in 4"
                    :key="i"
                    class="bar"
                    :style="{ background: i <= pwdStrength ? pwdStrengthColor : '#E5E7EB' }"
                  />
                </div>
                <span class="strength-label" :style="{ color: pwdStrengthColor }">
                  {{ pwdStrengthLabel }}
                </span>
              </div>
            </VCol>
            <VCol cols="12">
              <AppTextField
                v-model="pwdForm.confirm"
                label="Confirmer le nouveau mot de passe"
                :type="showConfPwd ? 'text' : 'password'"
                prepend-inner-icon="tabler-lock-check"
                :append-inner-icon="showConfPwd ? 'tabler-eye-off' : 'tabler-eye'"
                @click:append-inner="showConfPwd = !showConfPwd"
              />
              <p
                v-if="pwdForm.confirm && pwdForm.new_password !== pwdForm.confirm"
                class="text-caption text-error mt-1"
              >
                Les mots de passe ne correspondent pas
              </p>
            </VCol>
          </VRow>

          <!-- Règles -->
          <div class="pwd-rules">
            <p class="rules-title">Règles du mot de passe :</p>
            <div class="rules-list">
              <span :class="['rule', { 'rule-ok': pwdForm.new_password.length >= 8 }]">
                <VIcon :icon="pwdForm.new_password.length >= 8 ? 'tabler-check' : 'tabler-x'" size="12" />
                Minimum 8 caractères
              </span>
              <span :class="['rule', { 'rule-ok': /[A-Z]/.test(pwdForm.new_password) }]">
                <VIcon :icon="/[A-Z]/.test(pwdForm.new_password) ? 'tabler-check' : 'tabler-x'" size="12" />
                Une majuscule
              </span>
              <span :class="['rule', { 'rule-ok': /[0-9]/.test(pwdForm.new_password) }]">
                <VIcon :icon="/[0-9]/.test(pwdForm.new_password) ? 'tabler-check' : 'tabler-x'" size="12" />
                Un chiffre
              </span>
              <span :class="['rule', { 'rule-ok': /[^A-Za-z0-9]/.test(pwdForm.new_password) }]">
                <VIcon :icon="/[^A-Za-z0-9]/.test(pwdForm.new_password) ? 'tabler-check' : 'tabler-x'" size="12" />
                Un caractère spécial
              </span>
            </div>
          </div>

          <div class="d-flex justify-end mt-4">
            <VBtn color="primary" :loading="isChangingPwd" @click="changePassword">
              <VIcon start icon="tabler-lock" size="15" />
              Changer le mot de passe
            </VBtn>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.profile-page { display: flex; flex-direction: column; gap: 20px; }

.page-header { display: flex; align-items: flex-start; justify-content: space-between; }
.page-title  { font-size: 20px; font-weight: 600; color: #111827; margin: 0 0 4px; }
.page-sub    { font-size: 13px; color: #6B7280; margin: 0; }

.center-pad  { display: flex; justify-content: center; padding: 48px; }

// ── Layout ────────────────────────────────────────────────────────────────────
.profile-layout {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 20px;
  align-items: start;
  @media (max-width: 768px) { grid-template-columns: 1fr; }
}

// ── Sidebar col ───────────────────────────────────────────────────────────────
.sidebar-col { display: flex; flex-direction: column; gap: 12px; }

.avatar-card {
  background: white; border: 0.5px solid #E5E7EB;
  border-radius: 12px; padding: 24px 20px;
  display: flex; flex-direction: column; align-items: center; text-align: center;
}

.avatar-wrap { position: relative; margin-bottom: 14px; }
.avatar-circle {
  width: 80px; height: 80px; border-radius: 50%;
  background: #4F46E5;
  display: flex; align-items: center; justify-content: center;
  overflow: hidden;
}
.avatar-img      { width: 100%; height: 100%; object-fit: cover; }
.avatar-initials { font-size: 28px; font-weight: 700; color: white; }

.avatar-edit-btn {
  position: absolute; bottom: 0; right: 0;
  width: 26px; height: 26px; border-radius: 50%;
  background: #4F46E5; border: 2px solid white;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: background .15s;
  &:hover { background: #4338CA; }
}

.avatar-name  { font-size: 15px; font-weight: 600; color: #111827; margin: 0 0 3px; }
.avatar-org   { font-size: 13px; color: #6B7280; margin: 0 0 2px; }
.avatar-email { font-size: 12px; color: #9CA3AF; margin: 0; }

.kyc-badge {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 4px 12px; border-radius: 20px;
  font-size: 11px; font-weight: 600; margin-top: 12px;
  &.kyc-approved { background: #ECFDF5; color: #059669; }
  &.kyc-pending  { background: #FFFBEB; color: #D97706; }
  &.kyc-none     { background: #F3F4F6; color: #6B7280; }
}

.side-nav {
  background: white; border: 0.5px solid #E5E7EB;
  border-radius: 12px; padding: 8px; display: flex; flex-direction: column; gap: 2px;
}
.snav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 12px; border: none; background: none;
  border-radius: 8px; cursor: pointer;
  font-size: 13.5px; color: #6B7280; transition: all .15s; text-align: left;
  &:hover  { background: #F9FAFB; color: #374151; }
  &.active { background: #EEF2FF; color: #4F46E5; font-weight: 500; }
}

// ── Content col ───────────────────────────────────────────────────────────────
.content-col { display: flex; flex-direction: column; gap: 0; }

.form-card {
  background: white; border: 0.5px solid #E5E7EB;
  border-radius: 12px; padding: 24px;
}
.form-card-head {
  display: flex; align-items: flex-start; gap: 12px; margin-bottom: 16px;
}
.form-card-title { font-size: 15px; font-weight: 600; color: #111827; margin: 0 0 3px; }
.form-card-sub   { font-size: 12px; color: #9CA3AF; margin: 0; }

// ── Password strength ─────────────────────────────────────────────────────────
.pwd-strength {
  display: flex; align-items: center; gap: 10px; margin-top: 8px;
}
.strength-bars {
  display: flex; gap: 4px; flex: 1;
}
.bar {
  height: 4px; flex: 1; border-radius: 2px;
  transition: background .3s;
}
.strength-label { font-size: 11px; font-weight: 600; min-width: 40px; }

// ── Password rules ────────────────────────────────────────────────────────────
.pwd-rules {
  background: #F9FAFB; border-radius: 10px;
  padding: 14px 16px; margin-top: 16px;
  border: 0.5px solid #E5E7EB;
}
.rules-title { font-size: 12px; font-weight: 600; color: #374151; margin: 0 0 10px; }
.rules-list  { display: flex; flex-wrap: wrap; gap: 8px; }
.rule {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 12px; color: #9CA3AF; transition: color .2s;
  &.rule-ok { color: #059669; }
}

.mt-3 { margin-top: 12px; }
.mt-4 { margin-top: 16px; }
.mb-4 { margin-bottom: 16px; }
.mb-5 { margin-bottom: 20px; }
</style>