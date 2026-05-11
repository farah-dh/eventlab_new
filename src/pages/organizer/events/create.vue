<script setup lang="ts">
import { ref } from 'vue'
definePage({
  meta: {
    layout: 'organizer',
  },
})

const router = useRouter()

const API = 'http://127.0.0.1:8001/api/v1'
const getToken = () => localStorage.getItem('organizer_token') || ''

const apiFetch = async (endpoint: string, options: RequestInit = {}) => {
  const token = getToken()
  const res = await fetch(`${API}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
  })
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}))
    throw { status: res.status, data: errorData }
  }
  return res.json()
}

const isSaving  = ref(false)
const formError = ref('')
const activeTab = ref('info')

const form = ref({
  title:             '',
  short_description: '',
  description:       '',
  start_date:        '',
  end_date:          '',
  location_address:  '',
  cover_image:       '',
  link:              '',
  category:          null as number | null,
  location:          null as number | null,
  type:              1,
  price:             '',
  seats:             '',
  status:            true,
  step:              0,
})

const categories = ref<any[]>([])
const locations  = ref<any[]>([])

const fetchMeta = async () => {
  const [cats, locs] = await Promise.allSettled([
    apiFetch('/events/categories/'),
    apiFetch('/events/locations/'),
  ])
  if (cats.status === 'fulfilled') categories.value = cats.value?.results || cats.value || []
  if (locs.status === 'fulfilled') locations.value  = locs.value?.results || locs.value || []
}

const toDateOnly = (val: string) => val ? val.split('T')[0] : ''

const saveEvent = async () => {
  if (!form.value.title)             { formError.value = 'Le titre est obligatoire.'; return }
  if (!form.value.start_date)        { formError.value = 'La date de début est obligatoire.'; return }
  if (!form.value.short_description) { formError.value = 'La description courte est obligatoire.'; return }
  if (!form.value.location_address)  { formError.value = "L'adresse est obligatoire."; return }
  formError.value = ''
  isSaving.value = true
  try {
    const payload: any = {
      title:             form.value.title,
      short_description: form.value.short_description,
      description:       form.value.description,
      start_date:        toDateOnly(form.value.start_date),
      end_date:          toDateOnly(form.value.end_date),
      location_address:  form.value.location_address,
      type:              form.value.type,
      status:            form.value.status,
      step:              form.value.step || 0,
    }
    if (form.value.cover_image) payload.cover_image = form.value.cover_image
    if (form.value.link)        payload.link        = form.value.link
    if (form.value.category)    payload.category    = form.value.category
    if (form.value.location)    payload.location    = form.value.location
    if (form.value.price)       payload.price       = form.value.price
    if (form.value.seats)       payload.seats       = form.value.seats

    await apiFetch('/events/', { method: 'POST', body: JSON.stringify(payload) })
    router.push('/organizer/events')
  }
  catch (err: any) {
    if (err?.data?.errors && typeof err.data.errors === 'object') {
      const labels: Record<string, string> = {
        title: 'Titre', start_date: 'Date de début', end_date: 'Date de fin',
        short_description: 'Description courte', location_address: 'Adresse',
        cover_image: 'Image de couverture', link: 'Lien',
        price: 'Prix', seats: 'Places', category: 'Catégorie', location: 'Lieu',
      }
      formError.value = Object.entries(err.data.errors)
        .map(([f, m]: any) => `• ${labels[f] || f} : ${Array.isArray(m) ? m.join(', ') : m}`)
        .join('\n')
    }
    else if (err?.data?.message) {
      formError.value = `❌ ${err.data.message}`
    }
    else {
      formError.value = "❌ Erreur lors de la création. Vérifiez les champs."
    }
  }
  finally { isSaving.value = false }
}

fetchMeta()
</script>

<template>
  <div class="create-page">

    <!-- En-tête -->
    <div class="page-header">
      <div class="header-left">
        <button class="btn-back" @click="router.push('/organizer/events')">
          <VIcon icon="tabler-arrow-left" size="16" /> Retour
        </button>
        <div>
          <h2 class="page-title">Créer un événement</h2>
          <p class="page-sub">Remplissez les informations pour publier votre événement</p>
        </div>
      </div>
    </div>

    <!-- Alerte erreur -->
    <VAlert v-if="formError" type="error" variant="tonal" density="compact" class="mb-4" closable @click:close="formError = ''">
      <div style="white-space: pre-line">{{ formError }}</div>
    </VAlert>

    <!-- Carte principale -->
    <div class="form-card">

      <!-- Onglets -->
      <div class="form-tabs">
        <button :class="['ftab', { active: activeTab === 'info' }]" @click="activeTab = 'info'">
          <VIcon icon="tabler-info-circle" size="14" /> Informations générales
        </button>
        <button :class="['ftab', { active: activeTab === 'details' }]" @click="activeTab = 'details'">
          <VIcon icon="tabler-settings" size="14" /> Détails & options
        </button>
      </div>

      <VDivider />

      <div class="form-body">
        <VForm @submit.prevent="saveEvent">

          <!-- ── Onglet Informations ── -->
          <div v-show="activeTab === 'info'">
            <VRow>
              <VCol cols="12">
                <AppTextField
                  v-model="form.title"
                  label="Titre de l'événement *"
                  placeholder="Ex: Stand-up Comedy Night, Conférence Tech 2026..."
                  prepend-inner-icon="tabler-text-size"
                />
              </VCol>

              <VCol cols="12" md="6">
                <AppTextField
                  v-model="form.start_date"
                  label="Date de début *"
                  type="date"
                  prepend-inner-icon="tabler-calendar"
                />
              </VCol>
              <VCol cols="12" md="6">
                <AppTextField
                  v-model="form.end_date"
                  label="Date de fin"
                  type="date"
                  prepend-inner-icon="tabler-calendar-off"
                />
              </VCol>

              <VCol cols="12" md="6">
                <VSelect
                  v-model="form.category"
                  label="Catégorie"
                  :items="categories"
                  item-title="name"
                  item-value="id"
                  prepend-inner-icon="tabler-tag"
                  clearable
                />
              </VCol>
              <VCol cols="12" md="6">
                <VSelect
                  v-model="form.location"
                  label="Lieu"
                  :items="locations"
                  item-title="name"
                  item-value="id"
                  prepend-inner-icon="tabler-map-pin"
                  clearable
                />
              </VCol>

              <VCol cols="12">
                <AppTextField
                  v-model="form.location_address"
                  label="Adresse *"
                  placeholder="Ex: Théâtre Municipal, Avenue de Paris, Tunis"
                  prepend-inner-icon="tabler-map-pin"
                />
              </VCol>

              <VCol cols="12">
                <AppTextField
                  v-model="form.short_description"
                  label="Description courte *"
                  placeholder="Ex: Une soirée de rires inoubliable..."
                  prepend-inner-icon="tabler-text"
                />
              </VCol>

              <VCol cols="12">
                <AppTextField
                  v-model="form.cover_image"
                  label="Image de couverture (URL)"
                  placeholder="https://example.com/cover.jpg"
                  prepend-inner-icon="tabler-photo"
                />
              </VCol>

              <VCol v-if="form.cover_image" cols="12">
                <img :src="form.cover_image" alt="Aperçu" class="preview-img">
              </VCol>

              <VCol cols="12">
                <AppTextField
                  v-model="form.link"
                  label="Lien externe"
                  placeholder="https://example.com/event"
                  prepend-inner-icon="tabler-link"
                />
              </VCol>

              <VCol cols="12">
                <VTextarea
                  v-model="form.description"
                  label="Description complète"
                  placeholder="Décrivez votre événement en détail..."
                  rows="5"
                  prepend-inner-icon="tabler-align-left"
                />
              </VCol>
            </VRow>
          </div>

          <!-- ── Onglet Détails ── -->
          <div v-show="activeTab === 'details'">
            <VRow>
              <VCol cols="12" md="6">
                <VSelect
                  v-model="form.type"
                  label="Type d'événement"
                  :items="[{ title: 'Payant', value: 1 }, { title: 'Gratuit', value: 2 }]"
                  item-title="title"
                  item-value="value"
                  prepend-inner-icon="tabler-coin"
                />
              </VCol>
              <VCol cols="12" md="6">
                <AppTextField
                  v-model="form.price"
                  label="Prix (DT)"
                  type="number"
                  placeholder="0.00"
                  prepend-inner-icon="tabler-currency-dollar"
                  :disabled="form.type === 2"
                />
              </VCol>
              <VCol cols="12" md="6">
                <AppTextField
                  v-model="form.seats"
                  label="Nombre de places"
                  type="number"
                  placeholder="100"
                  prepend-inner-icon="tabler-armchair"
                />
              </VCol>
              <VCol cols="12" md="6">
                <div class="d-flex align-center gap-3 mt-3">
                  <span class="text-body-2 text-medium-emphasis">Statut :</span>
                  <VSwitch
                    v-model="form.status"
                    color="success"
                    hide-details
                    :label="form.status ? 'Actif' : 'Inactif'"
                  />
                </div>
              </VCol>
            </VRow>
          </div>

          <!-- Boutons -->
          <VDivider class="my-5" />
          <div class="form-actions">
            <VBtn variant="outlined" @click="router.push('/organizer/events')">
              <VIcon start icon="tabler-x" size="15" /> Annuler
            </VBtn>
            <VBtn color="primary" type="submit" :loading="isSaving" size="large">
              <VIcon start icon="tabler-check" size="15" />
              Créer l'événement
            </VBtn>
          </div>

        </VForm>
      </div>
    </div>

  </div>
</template>

<style scoped lang="scss">
.create-page { display: flex; flex-direction: column; gap: 20px; }

.page-header { display: flex; align-items: flex-start; justify-content: space-between; }
.header-left { display: flex; align-items: center; gap: 16px; }

.btn-back {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 14px; background: white; color: #6B7280;
  border: 0.5px solid #E5E7EB; border-radius: 8px;
  font-size: 13px; cursor: pointer; transition: all .15s;
  &:hover { background: #F9FAFB; color: #111827; }
}

.page-title { font-size: 20px; font-weight: 600; color: #111827; margin: 0 0 4px; }
.page-sub   { font-size: 13px; color: #6B7280; margin: 0; }

.form-card {
  background: white;
  border: 0.5px solid #E5E7EB;
  border-radius: 12px;
  overflow: hidden;
}

.form-tabs {
  display: flex;
  padding: 0 20px;
  background: #FAFAFA;
  border-bottom: none;
}

.ftab {
  display: flex; align-items: center; gap: 6px;
  padding: 14px 18px; border: none; background: none;
  font-size: 13px; color: #6B7280; cursor: pointer;
  border-bottom: 2px solid transparent; transition: all .15s;
  &.active { color: #4F46E5; border-bottom-color: #4F46E5; font-weight: 500; }
  &:hover:not(.active) { color: #374151; }
}

.form-body { padding: 28px 24px; }

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.preview-img {
  width: 100%; height: 180px;
  object-fit: cover;
  border-radius: 8px;
  border: 0.5px solid #E5E7EB;
}
</style>