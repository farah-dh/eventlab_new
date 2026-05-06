<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'

// ─── Layout admin ───

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

// ── State ─────────────────────────────────────────────────────────────────────
const isLoading   = ref(true)
const isSaving    = ref(false)
const isDeleting  = ref(false)
const locations   = ref<any[]>([])
const searchQuery = ref('')
const statusFilter = ref('all')

const successMessage = ref('')
const errorMessage   = ref('')
const showSuccess = (msg: string) => { successMessage.value = msg; setTimeout(() => successMessage.value = '', 4000) }
const showError   = (msg: string) => { errorMessage.value = msg;   setTimeout(() => errorMessage.value = '', 5000) }

const filteredLocations = computed(() => {
  let result = [...locations.value]

  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(l => l.name?.toLowerCase().includes(q))
  }

  if (statusFilter.value !== 'all') {
    if (statusFilter.value === 'active')
      result = result.filter(l => l.status === true)
    else if (statusFilter.value === 'inactive')
      result = result.filter(l => l.status === false)
    else if (statusFilter.value === 'featured')
      result = result.filter(l => l.is_featured === true)
  }

  return result
})

const fetchLocations = async () => {
  isLoading.value = true
  try {
    const data = await apiFetch('/events/locations/')
    locations.value = data.results || data || []
  }
  catch (e) { console.error(e) }
  finally { isLoading.value = false }
}

// ── Modal ─────────────────────────────────────────────────────────────────────
const showModal   = ref(false)
const modalMode   = ref<'add' | 'edit'>('add')
const editingItem = ref<any>(null)
const formError   = ref('')

const emptyForm = () => ({ name: '', image: '', sort_order: 0, status: true, is_featured: false })
const form = ref(emptyForm())

const openAdd = () => {
  modalMode.value = 'add'
  editingItem.value = null
  form.value = emptyForm()
  formError.value = ''
  showModal.value = true
}

const openEdit = (loc: any) => {
  modalMode.value = 'edit'
  editingItem.value = loc
  form.value = {
    name:        loc.name        || '',
    image:       loc.image       || '',
    sort_order:  loc.sort_order  || 0,
    status:      loc.status      ?? true,
    is_featured: loc.is_featured ?? false,
  }
  formError.value = ''
  showModal.value = true
}

const saveLocation = async () => {
  if (!form.value.name) { formError.value = 'Le nom est obligatoire.'; return }
  formError.value = ''
  isSaving.value = true
  try {
    const payload = {
      name:        form.value.name,
      image:       form.value.image || null,
      sort_order:  form.value.sort_order,
      status:      form.value.status,
      is_featured: form.value.is_featured,
    }
    if (modalMode.value === 'edit' && editingItem.value)
      await apiFetch(`/events/locations/${editingItem.value.id}/`, { method: 'PATCH', body: JSON.stringify(payload) })
    else
      await apiFetch('/events/locations/', { method: 'POST', body: JSON.stringify(payload) })

    showModal.value = false
    showSuccess(modalMode.value === 'edit' ? '✅ Lieu modifié avec succès !' : '✅ Lieu créé avec succès !')
    await fetchLocations()
  }
  catch (err: any) {
    if (err?.data?.errors) {
      formError.value = Object.entries(err.data.errors)
        .map(([f, m]: any) => `• ${f} : ${Array.isArray(m) ? m.join(', ') : m}`)
        .join('\n')
    } else if (err?.data && typeof err.data === 'object') {
      formError.value = Object.entries(err.data)
        .map(([f, m]: any) => `• ${f} : ${Array.isArray(m) ? m.join(', ') : m}`)
        .join('\n')
    } else {
      formError.value = err?.data?.message || '❌ Erreur lors de la sauvegarde.'
    }
  }
  finally { isSaving.value = false }
}

// ── Supprimer ─────────────────────────────────────────────────────────────────
const showDeleteDialog = ref(false)
const itemToDelete     = ref<any>(null)

const confirmDelete = (loc: any) => { itemToDelete.value = loc; showDeleteDialog.value = true }

const deleteLocation = async () => {
  if (!itemToDelete.value) return
  isDeleting.value = true
  try {
    await apiFetch(`/events/locations/${itemToDelete.value.id}/`, { method: 'DELETE' })
    showDeleteDialog.value = false
    const name = itemToDelete.value.name
    itemToDelete.value = null
    showSuccess(`🗑️ Lieu "${name}" supprimé.`)
    await fetchLocations()
  }
  catch {
    showDeleteDialog.value = false
    showError('❌ Erreur lors de la suppression.')
  }
  finally { isDeleting.value = false }
}

const toggleStatus = async (loc: any) => {
  try {
    await apiFetch(`/events/locations/${loc.id}/`, {
      method: 'PATCH',
      body: JSON.stringify({ status: !loc.status }),
    })
    showSuccess('✅ Statut mis à jour.')
    await fetchLocations()
  }
  catch { showError('❌ Erreur lors de la mise à jour du statut.') }
}

const toggleFeatured = async (loc: any) => {
  try {
    await apiFetch(`/events/locations/${loc.id}/`, {
      method: 'PATCH',
      body: JSON.stringify({ is_featured: !loc.is_featured }),
    })
    showSuccess(loc.is_featured ? '✅ Lieu retiré des mis en avant.' : '⭐ Lieu mis en avant.')
    await fetchLocations()
  }
  catch { showError('❌ Erreur lors de la mise à jour.') }
}

const formatDate = (d: string) => {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })
}

onMounted(fetchLocations)
</script>

<template>
  <div>
    <!-- ── Header ── -->
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h4 class="text-h4 font-weight-bold">Lieux d'événements</h4>
        <p class="text-body-1 text-medium-emphasis mt-1">
          Gérez les lieux disponibles pour les événements
        </p>
      </div>
      <VBtn color="primary" prepend-icon="tabler-plus" @click="openAdd">
        Ajouter un lieu
      </VBtn>
    </div>

    <!-- ── Notifications ── -->
    <VAlert v-if="successMessage" type="success" variant="tonal" closable class="mb-4" @click:close="successMessage = ''">
      {{ successMessage }}
    </VAlert>
    <VAlert v-if="errorMessage" type="error" variant="tonal" closable class="mb-4" @click:close="errorMessage = ''">
      {{ errorMessage }}
    </VAlert>

    <!-- ── Stats ── -->
    <VRow class="mb-6">
      <VCol cols="12" sm="6" md="3">
        <VCard>
          <VCardText class="d-flex align-center gap-3">
            <VAvatar color="primary" variant="tonal" size="44" rounded>
              <VIcon icon="tabler-map-pin" size="24" />
            </VAvatar>
            <div>
              <p class="text-caption text-medium-emphasis mb-0">Total lieux</p>
              <h5 class="text-h6 font-weight-bold">{{ locations.length }}</h5>
            </div>
          </VCardText>
        </VCard>
      </VCol>
      <VCol cols="12" sm="6" md="3">
        <VCard>
          <VCardText class="d-flex align-center gap-3">
            <VAvatar color="success" variant="tonal" size="44" rounded>
              <VIcon icon="tabler-check" size="24" />
            </VAvatar>
            <div>
              <p class="text-caption text-medium-emphasis mb-0">Actifs</p>
              <h5 class="text-h6 font-weight-bold">{{ locations.filter(l => l.status).length }}</h5>
            </div>
          </VCardText>
        </VCard>
      </VCol>
      <VCol cols="12" sm="6" md="3">
        <VCard>
          <VCardText class="d-flex align-center gap-3">
            <VAvatar color="error" variant="tonal" size="44" rounded>
              <VIcon icon="tabler-x" size="24" />
            </VAvatar>
            <div>
              <p class="text-caption text-medium-emphasis mb-0">Inactifs</p>
              <h5 class="text-h6 font-weight-bold">{{ locations.filter(l => !l.status).length }}</h5>
            </div>
          </VCardText>
        </VCard>
      </VCol>
      <VCol cols="12" sm="6" md="3">
        <VCard>
          <VCardText class="d-flex align-center gap-3">
            <VAvatar color="warning" variant="tonal" size="44" rounded>
              <VIcon icon="tabler-star" size="24" />
            </VAvatar>
            <div>
              <p class="text-caption text-medium-emphasis mb-0">Mis en avant</p>
              <h5 class="text-h6 font-weight-bold">{{ locations.filter(l => l.is_featured).length }}</h5>
            </div>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- ── Table ── -->
    <VCard>
      <VCardText class="pb-0">
        <VRow>
          <VCol cols="12" md="4">
            <VTextField
              v-model="searchQuery"
              placeholder="Rechercher un lieu..."
              prepend-inner-icon="tabler-search"
              density="compact"
              clearable
            />
          </VCol>
          <VCol cols="12" md="4">
            <VSelect
              v-model="statusFilter"
              :items="[
                { title: 'Tous les lieux', value: 'all' },
                { title: 'Actifs', value: 'active' },
                { title: 'Inactifs', value: 'inactive' },
                { title: 'Mis en avant', value: 'featured' },
              ]"
              density="compact"
            />
          </VCol>
          <VCol cols="12" md="4" class="d-flex justify-end align-center">
            <span class="text-body-2 text-medium-emphasis">
              {{ filteredLocations.length }} lieu(x) trouvé(s)
            </span>
          </VCol>
        </VRow>
      </VCardText>

      <div v-if="isLoading" class="d-flex justify-center align-center py-16">
        <VProgressCircular indeterminate color="primary" size="48" />
      </div>

      <VTable v-else class="text-no-wrap">
        <thead>
          <tr>
            <th>Image</th>
            <th>Nom</th>
            <th>Slug</th>
            <th>Ordre</th>
            <th>Mis en avant</th>
            <th>Statut</th>
            <th>Créé le</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="loc in filteredLocations" :key="loc.id">
            <td>
              <VAvatar size="40" rounded color="primary" variant="tonal">
                <VImg v-if="loc.image" :src="loc.image" :alt="loc.name" />
                <VIcon v-else icon="tabler-map-pin" size="20" />
              </VAvatar>
            </td>
            <td>
              <p class="text-body-1 font-weight-medium mb-0">{{ loc.name }}</p>
            </td>
            <td>
              <code class="text-caption">{{ loc.slug || '-' }}</code>
            </td>
            <td>
              <p class="text-body-2 mb-0">{{ loc.sort_order || 0 }}</p>
            </td>
            <td>
              <VBtn
                icon
                variant="text"
                size="small"
                :color="loc.is_featured ? 'warning' : 'default'"
                @click="toggleFeatured(loc)"
              >
                <VIcon :icon="loc.is_featured ? 'tabler-star-filled' : 'tabler-star'" size="20" />
                <VTooltip activator="parent">
                  {{ loc.is_featured ? 'Retirer des mis en avant' : 'Mettre en avant' }}
                </VTooltip>
              </VBtn>
            </td>
            <td>
              <VSwitch
                :model-value="loc.status"
                color="success"
                hide-details
                density="compact"
                @change="toggleStatus(loc)"
              />
            </td>
            <td>
              <p class="text-body-2 mb-0">{{ formatDate(loc.created_at) }}</p>
            </td>
            <td>
              <div class="d-flex gap-1">
                <VBtn icon variant="text" size="small" color="success" @click="openEdit(loc)">
                  <VIcon icon="tabler-pencil" size="18" />
                  <VTooltip activator="parent">Modifier</VTooltip>
                </VBtn>
                <VBtn icon variant="text" size="small" color="error" @click="confirmDelete(loc)">
                  <VIcon icon="tabler-trash" size="18" />
                  <VTooltip activator="parent">Supprimer</VTooltip>
                </VBtn>
              </div>
            </td>
          </tr>
          <tr v-if="filteredLocations.length === 0">
            <td colspan="8" class="text-center py-8">
              <VIcon icon="tabler-map-off" size="48" color="disabled" class="mb-2" />
              <p class="text-body-1 text-medium-emphasis">Aucun lieu trouvé</p>
            </td>
          </tr>
        </tbody>
      </VTable>
    </VCard>

    <!-- ════ MODAL : Ajouter / Modifier ════ -->
    <VDialog v-model="showModal" max-width="540" persistent>
      <VCard>
        <VCardTitle class="d-flex justify-space-between align-center pa-6">
          <span class="text-h6 font-weight-bold">
            {{ modalMode === 'add' ? 'Ajouter un lieu' : 'Modifier le lieu' }}
          </span>
          <VBtn icon variant="text" size="small" @click="showModal = false">
            <VIcon icon="tabler-x" />
          </VBtn>
        </VCardTitle>
        <VDivider />
        <VCardText class="pa-6">
          <VAlert v-if="formError" type="error" variant="tonal" density="compact" class="mb-4" closable @click:close="formError = ''">
            <div style="white-space: pre-line">{{ formError }}</div>
          </VAlert>
          <VRow>
            <VCol cols="12">
              <VTextField v-model="form.name" label="Nom *" placeholder="Ex: Palais des Congrès, Théâtre Municipal..." prepend-inner-icon="tabler-map-pin" />
            </VCol>
            <VCol cols="12">
              <VTextField v-model="form.image" label="Image (URL)" placeholder="https://example.com/image.jpg" prepend-inner-icon="tabler-photo" />
            </VCol>
            <VCol v-if="form.image" cols="12">
              <img :src="form.image" alt="Aperçu" style="width:100%; height:160px; object-fit:cover; border-radius:8px; border:0.5px solid #E5E7EB;">
            </VCol>
            <VCol cols="12" md="6">
              <VTextField v-model.number="form.sort_order" label="Ordre d'affichage" type="number" placeholder="0" prepend-inner-icon="tabler-sort-ascending" />
            </VCol>
            <VCol cols="12" md="6">
              <div class="d-flex align-center gap-3 mt-3">
                <span class="text-body-2 text-medium-emphasis">Statut :</span>
                <VSwitch v-model="form.status" color="success" hide-details :label="form.status ? 'Actif' : 'Inactif'" />
              </div>
            </VCol>
            <VCol cols="12">
              <VDivider class="my-2" />
              <div class="d-flex align-center justify-space-between">
                <div>
                  <p class="text-body-1 font-weight-medium mb-1">
                    <VIcon icon="tabler-star" size="18" class="me-1" />
                    Mis en avant
                  </p>
                  <p class="text-caption text-medium-emphasis mb-0">
                    {{ form.is_featured ? 'Ce lieu sera affiché en vedette' : 'Affichage normal' }}
                  </p>
                </div>
                <VSwitch v-model="form.is_featured" color="warning" hide-details />
              </div>
            </VCol>
          </VRow>
        </VCardText>
        <VDivider />
        <VCardActions class="pa-6">
          <VSpacer />
          <VBtn variant="outlined" color="secondary" @click="showModal = false">Annuler</VBtn>
          <VBtn color="primary" :loading="isSaving" prepend-icon="tabler-device-floppy" @click="saveLocation">
            {{ modalMode === 'add' ? 'Créer' : 'Enregistrer' }}
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- ════ DIALOG : Supprimer ════ -->
    <VDialog v-model="showDeleteDialog" max-width="450">
      <VCard>
        <VCardText class="text-center pa-8">
          <VAvatar color="error" variant="tonal" size="64" class="mb-4">
            <VIcon icon="tabler-alert-triangle" size="32" />
          </VAvatar>
          <h5 class="text-h6 font-weight-bold mb-2">Confirmer la suppression</h5>
          <p class="text-body-1 text-medium-emphasis mb-0">
            Êtes-vous sûr de vouloir supprimer le lieu<br>
            <strong>{{ itemToDelete?.name }}</strong> ?
          </p>
          <p class="text-body-2 text-error mt-2 mb-0">
            ⚠️ Les événements liés à ce lieu seront affectés.
          </p>
        </VCardText>
        <VDivider />
        <VCardActions class="pa-4 justify-center">
          <VBtn variant="outlined" color="secondary" @click="showDeleteDialog = false">Annuler</VBtn>
          <VBtn color="error" :loading="isDeleting" prepend-icon="tabler-trash" @click="deleteLocation">
            Supprimer
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

  </div>
</template>