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
const categories  = ref<any[]>([])
const searchQuery = ref('')

const successMessage = ref('')
const errorMessage   = ref('')
const showSuccess = (msg: string) => { successMessage.value = msg; setTimeout(() => successMessage.value = '', 4000) }
const showError   = (msg: string) => { errorMessage.value = msg;   setTimeout(() => errorMessage.value = '', 5000) }

const filteredCategories = computed(() => {
  if (!searchQuery.value) return categories.value
  return categories.value.filter(c =>
    c.name?.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const fetchCategories = async () => {
  isLoading.value = true
  try {
    const data = await apiFetch('/events/categories/')
    categories.value = data.results || data || []
  }
  catch (e) { console.error(e) }
  finally { isLoading.value = false }
}

// ── Modal ─────────────────────────────────────────────────────────────────────
const showModal   = ref(false)
const modalMode   = ref<'add' | 'edit'>('add')
const editingItem = ref<any>(null)
const formError   = ref('')

const emptyForm = () => ({ name: '', image: '', sort_order: 0, status: true })
const form = ref(emptyForm())

const openAdd = () => {
  modalMode.value = 'add'
  editingItem.value = null
  form.value = emptyForm()
  formError.value = ''
  showModal.value = true
}

const openEdit = (cat: any) => {
  modalMode.value = 'edit'
  editingItem.value = cat
  form.value = {
    name:       cat.name       || '',
    image:      cat.image      || '',
    sort_order: cat.sort_order || 0,
    status:     cat.status     ?? true,
  }
  formError.value = ''
  showModal.value = true
}

const saveCategory = async () => {
  if (!form.value.name) { formError.value = 'Le nom est obligatoire.'; return }
  formError.value = ''
  isSaving.value = true
  try {
    const payload = {
      name:       form.value.name,
      image:      form.value.image || null,
      sort_order: form.value.sort_order,
      status:     form.value.status,
    }
    if (modalMode.value === 'edit' && editingItem.value)
      await apiFetch(`/events/categories/${editingItem.value.id}/`, { method: 'PATCH', body: JSON.stringify(payload) })
    else
      await apiFetch('/events/categories/', { method: 'POST', body: JSON.stringify(payload) })

    showModal.value = false
    showSuccess(modalMode.value === 'edit' ? '✅ Catégorie modifiée avec succès !' : '✅ Catégorie créée avec succès !')
    await fetchCategories()
  }
  catch (err: any) {
    if (err?.data?.errors) {
      formError.value = Object.entries(err.data.errors)
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

const confirmDelete = (cat: any) => { itemToDelete.value = cat; showDeleteDialog.value = true }

const deleteCategory = async () => {
  if (!itemToDelete.value) return
  isDeleting.value = true
  try {
    await apiFetch(`/events/categories/${itemToDelete.value.id}/`, { method: 'DELETE' })
    showDeleteDialog.value = false
    const name = itemToDelete.value.name
    itemToDelete.value = null
    showSuccess(`🗑️ Catégorie "${name}" supprimée.`)
    await fetchCategories()
  }
  catch {
    showDeleteDialog.value = false
    showError('❌ Erreur lors de la suppression.')
  }
  finally { isDeleting.value = false }
}

const toggleStatus = async (cat: any) => {
  try {
    await apiFetch(`/events/categories/${cat.id}/`, {
      method: 'PATCH',
      body: JSON.stringify({ status: !cat.status }),
    })
    showSuccess('✅ Statut mis à jour.')
    await fetchCategories()
  }
  catch { showError('❌ Erreur lors de la mise à jour du statut.') }
}

const formatDate = (d: string) => {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })
}

onMounted(fetchCategories)
</script>

<template>
  <div>
    <!-- ── Header ── -->
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h4 class="text-h4 font-weight-bold">Catégories d'événements</h4>
        <p class="text-body-1 text-medium-emphasis mt-1">
          Gérez les catégories disponibles pour les événements
        </p>
      </div>
      <VBtn color="primary" prepend-icon="tabler-plus" @click="openAdd">
        Ajouter une catégorie
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
      <VCol cols="12" sm="4">
        <VCard>
          <VCardText class="d-flex align-center gap-3">
            <VAvatar color="primary" variant="tonal" size="44" rounded>
              <VIcon icon="tabler-tag" size="24" />
            </VAvatar>
            <div>
              <p class="text-caption text-medium-emphasis mb-0">Total catégories</p>
              <h5 class="text-h6 font-weight-bold">{{ categories.length }}</h5>
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
              <h5 class="text-h6 font-weight-bold">{{ categories.filter(c => c.status).length }}</h5>
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
              <h5 class="text-h6 font-weight-bold">{{ categories.filter(c => !c.status).length }}</h5>
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
              placeholder="Rechercher une catégorie..."
              prepend-inner-icon="tabler-search"
              density="compact"
              clearable
            />
          </VCol>
          <VCol cols="12" md="8" class="d-flex justify-end align-center">
            <span class="text-body-2 text-medium-emphasis">
              {{ filteredCategories.length }} catégorie(s) trouvée(s)
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
            <th>Événements</th>
            <th>Ordre</th>
            <th>Statut</th>
            <th>Créée le</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="cat in filteredCategories" :key="cat.id">
            <td>
              <VAvatar size="40" rounded color="primary" variant="tonal">
                <VImg v-if="cat.image" :src="cat.image" :alt="cat.name" />
                <VIcon v-else icon="tabler-tag" size="20" />
              </VAvatar>
            </td>
            <td>
              <p class="text-body-1 font-weight-medium mb-0">{{ cat.name }}</p>
            </td>
            <td>
              <code class="text-caption">{{ cat.slug || '-' }}</code>
            </td>
            <td>
              <VChip color="info" size="small" variant="tonal">
                {{ cat.events_count || 0 }} événement(s)
              </VChip>
            </td>
            <td>
              <p class="text-body-2 mb-0">{{ cat.sort_order || 0 }}</p>
            </td>
            <td>
              <VSwitch
                :model-value="cat.status"
                color="success"
                hide-details
                density="compact"
                @change="toggleStatus(cat)"
              />
            </td>
            <td>
              <p class="text-body-2 mb-0">{{ formatDate(cat.created_at) }}</p>
            </td>
            <td>
              <div class="d-flex gap-1">
                <VBtn icon variant="text" size="small" color="success" @click="openEdit(cat)">
                  <VIcon icon="tabler-pencil" size="18" />
                  <VTooltip activator="parent">Modifier</VTooltip>
                </VBtn>
                <VBtn icon variant="text" size="small" color="error" @click="confirmDelete(cat)">
                  <VIcon icon="tabler-trash" size="18" />
                  <VTooltip activator="parent">Supprimer</VTooltip>
                </VBtn>
              </div>
            </td>
          </tr>
          <tr v-if="filteredCategories.length === 0">
            <td colspan="8" class="text-center py-8">
              <VIcon icon="tabler-tag-off" size="48" color="disabled" class="mb-2" />
              <p class="text-body-1 text-medium-emphasis">Aucune catégorie trouvée</p>
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
            {{ modalMode === 'add' ? 'Ajouter une catégorie' : 'Modifier la catégorie' }}
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
              <VTextField v-model="form.name" label="Nom *" placeholder="Ex: Musique, Sport, Théâtre..." prepend-inner-icon="tabler-tag" />
            </VCol>
            <VCol cols="12">
              <VTextField v-model="form.image" label="Image (URL)" placeholder="https://example.com/image.jpg" prepend-inner-icon="tabler-photo" />
            </VCol>
            <VCol v-if="form.image" cols="12">
              <img :src="form.image" alt="Aperçu" style="width:100%; height:120px; object-fit:cover; border-radius:8px; border:0.5px solid #E5E7EB;">
            </VCol>
            <VCol cols="12" md="6">
              <VTextField v-model.number="form.sort_order" label="Ordre d'affichage" type="number" placeholder="0" prepend-inner-icon="tabler-sort-ascending" />
            </VCol>
            <VCol cols="12" md="6">
              <div class="d-flex align-center gap-3 mt-3">
                <span class="text-body-2 text-medium-emphasis">Statut :</span>
                <VSwitch v-model="form.status" color="success" hide-details :label="form.status ? 'Active' : 'Inactive'" />
              </div>
            </VCol>
          </VRow>
        </VCardText>
        <VDivider />
        <VCardActions class="pa-6">
          <VSpacer />
          <VBtn variant="outlined" color="secondary" @click="showModal = false">Annuler</VBtn>
          <VBtn color="primary" :loading="isSaving" prepend-icon="tabler-device-floppy" @click="saveCategory">
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
            Êtes-vous sûr de vouloir supprimer la catégorie<br>
            <strong>{{ itemToDelete?.name }}</strong> ?
          </p>
          <p class="text-body-2 text-error mt-2 mb-0">
            ⚠️ Les événements liés à cette catégorie seront affectés.
          </p>
        </VCardText>
        <VDivider />
        <VCardActions class="pa-4 justify-center">
          <VBtn variant="outlined" color="secondary" @click="showDeleteDialog = false">Annuler</VBtn>
          <VBtn color="error" :loading="isDeleting" prepend-icon="tabler-trash" @click="deleteCategory">
            Supprimer
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

  </div>
</template>