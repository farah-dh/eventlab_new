<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'

definePage({
  meta: {
    layout: 'organizer',
  },
})

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
  if (res.status === 204) return null
  return res.json()
}

const isLoading    = ref(true)
const isSaving     = ref(false)
const isDeleting   = ref(false)
const events       = ref<any[]>([])
const categories   = ref<any[]>([])
const locations    = ref<any[]>([])
const search       = ref('')
const filterStatus = ref<'all' | 'active' | 'inactive'>('all')

const successMessage = ref('')
const errorMessage   = ref('')

const showSuccess = (msg: string) => {
  successMessage.value = msg
  setTimeout(() => successMessage.value = '', 4000)
}
const showError = (msg: string) => {
  errorMessage.value = msg
  setTimeout(() => errorMessage.value = '', 5000)
}

// ✅ CORRECTION : suppression du filtre organizer_name qui bloquait l'affichage
const filteredEvents = computed(() => {
  let list = [...events.value]
  if (search.value)
    list = list.filter(e => e.title?.toLowerCase().includes(search.value.toLowerCase()))
  if (filterStatus.value === 'active')   list = list.filter(e => e.status === true)
  if (filterStatus.value === 'inactive') list = list.filter(e => e.status === false)
  return list
})

const fetchAll = async () => {
  isLoading.value = true
  try {
    const [ev, cats, locs] = await Promise.allSettled([
      apiFetch('/events/'),
      apiFetch('/events/categories/'),
      apiFetch('/events/locations/'),
    ])
    if (ev.status === 'fulfilled')   events.value     = ev.value?.results   || ev.value   || []
    if (cats.status === 'fulfilled') categories.value = cats.value?.results || cats.value || []
    if (locs.status === 'fulfilled') locations.value  = locs.value?.results || locs.value || []
  }
  catch (e) { console.error(e) }
  finally { isLoading.value = false }
}

const showDialog   = ref(false)
const editingEvent = ref<any>(null)
const formError    = ref('')
const activeTab    = ref('info')

const emptyForm = () => ({
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
const form = ref(emptyForm())
const dialogTitle = computed(() => editingEvent.value ? "Modifier l'événement" : 'Créer un événement')

const openCreate = () => {
  editingEvent.value = null
  form.value = emptyForm()
  formError.value = ''
  activeTab.value = 'info'
  showDialog.value = true
}

const openEdit = (event: any) => {
  editingEvent.value = event
  form.value = {
    title:             event.title             || '',
    short_description: event.short_description || '',
    description:       event.description       || '',
    start_date:        event.start_date        || '',
    end_date:          event.end_date          || '',
    location_address:  event.location_address  || '',
    cover_image:       event.cover_image       || '',
    link:              event.link              || '',
    category:          event.category          || null,
    location:          event.location          || null,
    type:              event.type              || 1,
    price:             event.price             || '',
    seats:             event.seats             || '',
    status:            event.status            ?? true,
    step:              event.step              || 0,
  }
  formError.value = ''
  activeTab.value = 'info'
  showDialog.value = true
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

    const isEditing = !!editingEvent.value
    if (isEditing)
      await apiFetch(`/events/${editingEvent.value.id}/`, { method: 'PATCH', body: JSON.stringify(payload) })
    else
      await apiFetch('/events/', { method: 'POST', body: JSON.stringify(payload) })

    showDialog.value = false
    showSuccess(isEditing ? '✅ Événement modifié avec succès !' : '✅ Événement créé avec succès !')
    await fetchAll()
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
      formError.value = "❌ Erreur lors de l'enregistrement. Vérifiez les champs."
    }
  }
  finally { isSaving.value = false }
}

const showDeleteDialog = ref(false)
const eventToDelete    = ref<any>(null)

const confirmDelete = (event: any) => { eventToDelete.value = event; showDeleteDialog.value = true }

const deleteEvent = async () => {
  if (!eventToDelete.value) return
  isDeleting.value = true
  try {
    await apiFetch(`/events/${eventToDelete.value.id}/`, { method: 'DELETE' })
    showDeleteDialog.value = false
    const title = eventToDelete.value.title
    eventToDelete.value = null
    showSuccess(`🗑️ L'événement "${title}" a été supprimé.`)
    await fetchAll()
  }
  catch {
    showDeleteDialog.value = false
    showError('❌ Erreur lors de la suppression. Veuillez réessayer.')
  }
  finally { isDeleting.value = false }
}

const showGalleryDialog  = ref(false)
const galleryEvent       = ref<any>(null)
const galleryImageUrl    = ref('')
const isUploadingGallery = ref(false)
const galleryError       = ref('')

const openGallery = (event: any) => {
  galleryEvent.value = event
  galleryImageUrl.value = ''
  galleryError.value = ''
  showGalleryDialog.value = true
}

const uploadGallery = async () => {
  if (!galleryImageUrl.value.trim()) { galleryError.value = "Saisissez une URL d'image valide."; return }
  isUploadingGallery.value = true; galleryError.value = ''
  try {
    const token = getToken()
    const res = await fetch(`${API}/events/${galleryEvent.value.id}/gallery/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(token && { Authorization: `Bearer ${token}` }) },
      body: JSON.stringify({ image: galleryImageUrl.value.trim() }),
    })
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}))
      galleryError.value = errData?.message || errData?.image?.[0] || "❌ Erreur lors de l'ajout."
      return
    }
    showGalleryDialog.value = false
    galleryImageUrl.value = ''
    showSuccess('✅ Image ajoutée à la galerie avec succès !')
    await fetchAll()
  }
  catch { galleryError.value = "❌ Erreur lors de l'ajout de l'image." }
  finally { isUploadingGallery.value = false }
}

const showScheduleDialog = ref(false)
const scheduleEvent      = ref<any>(null)
const scheduleItems      = ref<any[]>([])
const isLoadingSchedule  = ref(false)
const showAddSchedule    = ref(false)
const isSavingSchedule   = ref(false)
const scheduleError      = ref('')
const scheduleForm       = ref({ title: '', start_time: '', end_time: '', description: '' })

const openSchedule = async (event: any) => {
  scheduleEvent.value = event; scheduleItems.value = []
  showAddSchedule.value = false; scheduleError.value = ''
  showScheduleDialog.value = true; isLoadingSchedule.value = true
  try {
    const data = await apiFetch(`/events/${event.id}/schedule/`)
    scheduleItems.value = data?.results || data || []
  }
  catch { }
  finally { isLoadingSchedule.value = false }
}

const addScheduleItem = async () => {
  if (!scheduleForm.value.title) { scheduleError.value = 'Titre obligatoire.'; return }
  isSavingSchedule.value = true; scheduleError.value = ''
  try {
    await apiFetch(`/events/${scheduleEvent.value.id}/schedule/`, {
      method: 'POST', body: JSON.stringify(scheduleForm.value),
    })
    scheduleForm.value = { title: '', start_time: '', end_time: '', description: '' }
    showAddSchedule.value = false
    const data = await apiFetch(`/events/${scheduleEvent.value.id}/schedule/`)
    scheduleItems.value = data?.results || data || []
  }
  catch { scheduleError.value = "❌ Erreur lors de l'ajout." }
  finally { isSavingSchedule.value = false }
}

const showSpeakersDialog = ref(false)
const speakersEvent      = ref<any>(null)
const speakersList       = ref<any[]>([])
const isLoadingSpeakers  = ref(false)
const showAddSpeaker     = ref(false)
const isSavingSpeaker    = ref(false)
const speakerError       = ref('')
const speakerForm        = ref({ name: '', title: '', bio: '', photo: null as File | null })

const openSpeakers = async (event: any) => {
  speakersEvent.value = event; speakersList.value = []
  showAddSpeaker.value = false; speakerError.value = ''
  showSpeakersDialog.value = true; isLoadingSpeakers.value = true
  try {
    const data = await apiFetch(`/events/${event.id}/speakers/`)
    speakersList.value = data?.results || data || []
  }
  catch { }
  finally { isLoadingSpeakers.value = false }
}

const addSpeaker = async () => {
  if (!speakerForm.value.name) { speakerError.value = 'Nom obligatoire.'; return }
  isSavingSpeaker.value = true; speakerError.value = ''
  try {
    const fd = new FormData()
    fd.append('name', speakerForm.value.name)
    fd.append('title', speakerForm.value.title)
    fd.append('bio', speakerForm.value.bio)
    if (speakerForm.value.photo) fd.append('photo', speakerForm.value.photo)
    const token = getToken()
    const res = await fetch(`${API}/events/${speakersEvent.value.id}/speakers/`, {
      method: 'POST',
      headers: { ...(token && { Authorization: `Bearer ${token}` }) },
      body: fd,
    })
    if (!res.ok) throw new Error()
    speakerForm.value = { name: '', title: '', bio: '', photo: null }
    showAddSpeaker.value = false
    const data = await apiFetch(`/events/${speakersEvent.value.id}/speakers/`)
    speakersList.value = data?.results || data || []
  }
  catch { speakerError.value = "❌ Erreur lors de l'ajout." }
  finally { isSavingSpeaker.value = false }
}

const formatDate     = (d: string) => {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })
}
const getStatusLabel = (s: boolean) => s ? 'Actif' : 'Inactif'
const getTypeLabel   = (t: number)  => t === 1 ? 'Payant' : 'Gratuit'

onMounted(fetchAll)
</script>

<template>
  <div class="events-page">

    <div class="page-header">
      <div>
        <h2 class="page-title">Mes événements</h2>
        <p class="page-sub">Gérez tous vos événements depuis cet espace</p>
      </div>
      <button class="btn-primary" @click="openCreate">
        <VIcon icon="tabler-plus" size="15" /> Créer un événement
      </button>
    </div>

    <VAlert v-if="successMessage" type="success" variant="tonal" closable @click:close="successMessage = ''">
      {{ successMessage }}
    </VAlert>
    <VAlert v-if="errorMessage" type="error" variant="tonal" closable @click:close="errorMessage = ''">
      {{ errorMessage }}
    </VAlert>

    <div class="filters-bar">
      <div class="search-wrap">
        <VIcon icon="tabler-search" size="14" class="si" />
        <input v-model="search" type="text" placeholder="Rechercher un événement..." class="search-input">
      </div>
      <div class="filter-tabs">
        <button :class="['ftab', { active: filterStatus === 'all' }]"      @click="filterStatus = 'all'">Tous</button>
        <button :class="['ftab', { active: filterStatus === 'active' }]"   @click="filterStatus = 'active'">Actifs</button>
        <button :class="['ftab', { active: filterStatus === 'inactive' }]" @click="filterStatus = 'inactive'">Inactifs</button>
      </div>
      <span class="results-count">{{ filteredEvents.length }} événement(s)</span>
    </div>

    <div v-if="isLoading" class="center-pad">
      <VProgressCircular indeterminate color="primary" size="36" />
    </div>

    <div v-else-if="filteredEvents.length === 0" class="empty-state">
      <VIcon icon="tabler-calendar-off" size="56" color="grey-lighten-1" class="mb-4" />
      <p class="empty-title">Aucun événement trouvé</p>
      <p class="empty-sub">{{ search ? 'Essayez un autre terme de recherche' : 'Créez votre premier événement pour commencer' }}</p>
      <button v-if="!search" class="btn-primary mt-4" @click="openCreate">
        <VIcon icon="tabler-plus" size="15" /> Créer un événement
      </button>
    </div>

    <div v-else class="events-grid">
      <div v-for="event in filteredEvents" :key="event.id" class="event-card">
        <div class="event-banner">
          <img v-if="event.cover_image" :src="event.cover_image" :alt="event.title" class="banner-img">
          <div v-else class="banner-placeholder">
            <VIcon icon="tabler-calendar-event" size="32" color="white" />
          </div>
          <div class="banner-badges">
            <span :class="['badge-status', event.status ? 'badge-active' : 'badge-inactive']">{{ getStatusLabel(event.status) }}</span>
            <span :class="['badge-type', event.type === 1 ? 'badge-paid' : 'badge-free']">{{ getTypeLabel(event.type) }}</span>
          </div>
        </div>
        <div class="event-body">
          <h3 class="event-title">{{ event.title }}</h3>
          <div class="event-meta">
            <span class="meta-item"><VIcon icon="tabler-calendar" size="13" />{{ formatDate(event.start_date) }}</span>
            <span class="meta-item"><VIcon icon="tabler-map-pin" size="13" />{{ event.location_name || event.location_address || 'Lieu non défini' }}</span>
            <span class="meta-item"><VIcon icon="tabler-ticket" size="13" />{{ event.seats_booked || 0 }} / {{ event.seats || '∞' }} billets</span>
            <span class="meta-item"><VIcon icon="tabler-coin" size="13" />{{ event.price ? `${event.price} DT` : 'Gratuit' }}</span>
          </div>
        </div>
        <div class="event-actions">
          <button class="action-btn" title="Modifier"     @click="openEdit(event)">    <VIcon icon="tabler-edit"         size="15" /></button>
          <button class="action-btn" title="Programme"    @click="openSchedule(event)"><VIcon icon="tabler-list-details" size="15" /></button>
          <button class="action-btn" title="Intervenants" @click="openSpeakers(event)"><VIcon icon="tabler-users"        size="15" /></button>
          <button class="action-btn" title="Galerie"      @click="openGallery(event)"> <VIcon icon="tabler-photo"        size="15" /></button>
          <button class="action-btn action-btn--danger" title="Supprimer" @click="confirmDelete(event)"><VIcon icon="tabler-trash" size="15" /></button>
        </div>
      </div>
    </div>

    <!-- ════ DIALOG : Créer / Modifier ════ -->
    <VDialog v-model="showDialog" max-width="700" scrollable>
      <VCard>
        <VCardText class="pa-0">
          <div class="dialog-head">
            <div class="dialog-icon"><VIcon icon="tabler-calendar-plus" color="#4F46E5" size="20" /></div>
            <div>
              <h3 class="dialog-title">{{ dialogTitle }}</h3>
              <p class="dialog-sub">Remplissez les informations ci-dessous</p>
            </div>
            <VBtn icon variant="text" size="small" class="ms-auto" @click="showDialog = false">
              <VIcon icon="tabler-x" size="16" />
            </VBtn>
          </div>
          <VDivider />
          <div class="dialog-tabs">
            <button :class="['dtab', { active: activeTab === 'info' }]"    @click="activeTab = 'info'">
              <VIcon icon="tabler-info-circle" size="14" /> Informations
            </button>
            <button :class="['dtab', { active: activeTab === 'details' }]" @click="activeTab = 'details'">
              <VIcon icon="tabler-settings" size="14" /> Détails
            </button>
          </div>
          <VDivider />
          <div class="pa-5">
            <VAlert v-if="formError" type="error" variant="tonal" density="compact" class="mb-4" closable @click:close="formError = ''">
              <div style="white-space: pre-line">{{ formError }}</div>
            </VAlert>
            <VForm @submit.prevent="saveEvent">

              <!-- ── Tab Informations ── -->
              <div v-show="activeTab === 'info'">
                <VRow>
                  <VCol cols="12">
                    <AppTextField v-model="form.title" label="Titre *" placeholder="Ex: Stand-up Comedy Night..." prepend-inner-icon="tabler-text-size" />
                  </VCol>
                  <VCol cols="12" md="6">
                    <AppTextField v-model="form.start_date" label="Date de début *" type="date" prepend-inner-icon="tabler-calendar" />
                  </VCol>
                  <VCol cols="12" md="6">
                    <AppTextField v-model="form.end_date" label="Date de fin" type="date" prepend-inner-icon="tabler-calendar-off" />
                  </VCol>
                  <VCol cols="12" md="6">
                    <VSelect v-model="form.category" label="Catégorie" :items="categories" item-title="name" item-value="id" prepend-inner-icon="tabler-tag" clearable />
                  </VCol>
                  <VCol cols="12" md="6">
                    <VSelect v-model="form.location" label="Lieu" :items="locations" item-title="name" item-value="id" prepend-inner-icon="tabler-map-pin" clearable />
                  </VCol>
                  <VCol cols="12">
                    <AppTextField v-model="form.location_address" label="Adresse *" placeholder="Ex: Théâtre Municipal, Avenue de Paris, Tunis" prepend-inner-icon="tabler-map-pin" />
                  </VCol>
                  <VCol cols="12">
                    <AppTextField v-model="form.short_description" label="Description courte *" placeholder="Ex: Une soirée de rires inoubliable..." prepend-inner-icon="tabler-text" />
                  </VCol>
                  <VCol cols="12">
                    <AppTextField v-model="form.cover_image" label="Image de couverture (URL)" placeholder="https://example.com/cover.jpg" prepend-inner-icon="tabler-photo" />
                  </VCol>
                  <VCol v-if="form.cover_image" cols="12">
                    <img :src="form.cover_image" alt="Aperçu couverture" class="preview-img">
                  </VCol>
                  <VCol cols="12">
                    <AppTextField v-model="form.link" label="Lien externe" placeholder="https://example.com/event" prepend-inner-icon="tabler-link" />
                  </VCol>
                  <VCol cols="12">
                    <VTextarea v-model="form.description" label="Description complète" placeholder="Décrivez votre événement en détail..." rows="4" prepend-inner-icon="tabler-align-left" />
                  </VCol>
                </VRow>
              </div>

              <!-- ── Tab Détails ── -->
              <div v-show="activeTab === 'details'">
                <VRow>
                  <VCol cols="12" md="6">
                    <VSelect
                      v-model="form.type"
                      label="Type d'événement"
                      :items="[{ title: 'Payant', value: 1 }, { title: 'Gratuit', value: 2 }]"
                      item-title="title" item-value="value"
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
                    <AppTextField v-model="form.seats" label="Nombre de places" type="number" placeholder="100" prepend-inner-icon="tabler-armchair" />
                  </VCol>
                  <VCol cols="12" md="6">
                    <div class="d-flex align-center gap-3 mt-3">
                      <span class="text-body-2 text-medium-emphasis">Statut :</span>
                      <VSwitch v-model="form.status" color="success" hide-details :label="form.status ? 'Actif' : 'Inactif'" />
                    </div>
                  </VCol>
                </VRow>
              </div>

              <VDivider class="my-4" />
              <div class="d-flex justify-end gap-3">
                <VBtn variant="outlined" @click="showDialog = false">Annuler</VBtn>
                <VBtn color="primary" type="submit" :loading="isSaving">
                  <VIcon start icon="tabler-check" size="15" />
                  {{ editingEvent ? 'Enregistrer' : 'Créer' }}
                </VBtn>
              </div>
            </VForm>
          </div>
        </VCardText>
      </VCard>
    </VDialog>

    <!-- ════ DIALOG : Supprimer ════ -->
    <VDialog v-model="showDeleteDialog" max-width="400">
      <VCard>
        <VCardText class="text-center pa-8">
          <VAvatar color="error" variant="tonal" size="56" class="mb-4">
            <VIcon icon="tabler-alert-triangle" size="28" />
          </VAvatar>
          <h5 class="text-h6 font-weight-bold mb-2">Confirmer la suppression</h5>
          <p class="text-body-2 text-medium-emphasis">
            Voulez-vous vraiment supprimer<br><strong>{{ eventToDelete?.title }}</strong> ?
          </p>
          <p class="text-caption text-error mt-2">Cette action est irréversible.</p>
        </VCardText>
        <VDivider />
        <VCardActions class="pa-4 justify-center gap-3">
          <VBtn variant="outlined" @click="showDeleteDialog = false">Annuler</VBtn>
          <VBtn color="error" :loading="isDeleting" @click="deleteEvent">
            <VIcon start icon="tabler-trash" size="15" /> Supprimer
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- ════ DIALOG : Galerie ════ -->
    <VDialog v-model="showGalleryDialog" max-width="480">
      <VCard>
        <VCardText class="pa-0">
          <div class="dialog-head">
            <div class="dialog-icon"><VIcon icon="tabler-photo" color="#4F46E5" size="20" /></div>
            <div><h3 class="dialog-title">Galerie photos</h3><p class="dialog-sub">{{ galleryEvent?.title }}</p></div>
            <VBtn icon variant="text" size="small" class="ms-auto" @click="showGalleryDialog = false"><VIcon icon="tabler-x" size="16" /></VBtn>
          </div>
          <VDivider />
          <div class="pa-5">
            <VAlert v-if="galleryError" type="error" variant="tonal" density="compact" class="mb-4" closable @click:close="galleryError = ''">
              {{ galleryError }}
            </VAlert>
            <p class="text-body-2 text-medium-emphasis mb-2">Saisissez l'URL d'une image :</p>
            <AppTextField v-model="galleryImageUrl" label="URL de l'image *" placeholder="https://example.com/image.jpg" prepend-inner-icon="tabler-link" />
            <p class="text-caption text-medium-emphasis mt-1 mb-3">Exemple : https://picsum.photos/800/400</p>
            <div v-if="galleryImageUrl" class="mt-2">
              <img :src="galleryImageUrl" alt="Aperçu" class="preview-img" @error="galleryError = 'URL invalide ou image inaccessible.'">
            </div>
            <div class="d-flex justify-end gap-3 mt-4">
              <VBtn variant="outlined" @click="showGalleryDialog = false">Annuler</VBtn>
              <VBtn color="primary" :loading="isUploadingGallery" @click="uploadGallery">
                <VIcon start icon="tabler-plus" size="15" /> Ajouter
              </VBtn>
            </div>
          </div>
        </VCardText>
      </VCard>
    </VDialog>

    <!-- ════ DIALOG : Programme ════ -->
    <VDialog v-model="showScheduleDialog" max-width="560" scrollable>
      <VCard>
        <VCardText class="pa-0">
          <div class="dialog-head">
            <div class="dialog-icon"><VIcon icon="tabler-list-details" color="#4F46E5" size="20" /></div>
            <div><h3 class="dialog-title">Programme</h3><p class="dialog-sub">{{ scheduleEvent?.title }}</p></div>
            <VBtn icon variant="text" size="small" class="ms-auto" @click="showScheduleDialog = false"><VIcon icon="tabler-x" size="16" /></VBtn>
          </div>
          <VDivider />
          <div class="pa-5">
            <div v-if="isLoadingSchedule" class="center-pad"><VProgressCircular indeterminate color="primary" size="28" /></div>
            <div v-else>
              <div v-if="scheduleItems.length === 0 && !showAddSchedule" class="text-center py-6">
                <VIcon icon="tabler-calendar-time" size="40" color="grey-lighten-1" class="mb-3" />
                <p class="text-medium-emphasis text-body-2">Aucun programme ajouté</p>
              </div>
              <div v-else class="schedule-list mb-4">
                <div v-for="item in scheduleItems" :key="item.id" class="schedule-item">
                  <div class="schedule-time">{{ item.start_time ? item.start_time.slice(0,5) : '--:--' }}<span v-if="item.end_time"> → {{ item.end_time.slice(0,5) }}</span></div>
                  <div class="schedule-info">
                    <p class="schedule-title">{{ item.title }}</p>
                    <p v-if="item.description" class="schedule-desc">{{ item.description }}</p>
                  </div>
                </div>
              </div>
              <div v-if="showAddSchedule" class="add-form">
                <VAlert v-if="scheduleError" type="error" variant="tonal" density="compact" class="mb-3">{{ scheduleError }}</VAlert>
                <VRow>
                  <VCol cols="12"><AppTextField v-model="scheduleForm.title" label="Titre *" placeholder="Ex: Ouverture des portes" /></VCol>
                  <VCol cols="6"><AppTextField v-model="scheduleForm.start_time" label="Heure début" type="time" /></VCol>
                  <VCol cols="6"><AppTextField v-model="scheduleForm.end_time" label="Heure fin" type="time" /></VCol>
                  <VCol cols="12"><AppTextField v-model="scheduleForm.description" label="Description" placeholder="Détails..." /></VCol>
                </VRow>
                <div class="d-flex gap-2 mt-2">
                  <VBtn variant="outlined" size="small" @click="showAddSchedule = false">Annuler</VBtn>
                  <VBtn color="primary" size="small" :loading="isSavingSchedule" @click="addScheduleItem">Ajouter</VBtn>
                </div>
              </div>
              <VBtn v-if="!showAddSchedule" variant="tonal" color="primary" size="small" prepend-icon="tabler-plus" @click="showAddSchedule = true">Ajouter une session</VBtn>
            </div>
          </div>
        </VCardText>
      </VCard>
    </VDialog>

    <!-- ════ DIALOG : Intervenants ════ -->
    <VDialog v-model="showSpeakersDialog" max-width="560" scrollable>
      <VCard>
        <VCardText class="pa-0">
          <div class="dialog-head">
            <div class="dialog-icon"><VIcon icon="tabler-users" color="#4F46E5" size="20" /></div>
            <div><h3 class="dialog-title">Intervenants</h3><p class="dialog-sub">{{ speakersEvent?.title }}</p></div>
            <VBtn icon variant="text" size="small" class="ms-auto" @click="showSpeakersDialog = false"><VIcon icon="tabler-x" size="16" /></VBtn>
          </div>
          <VDivider />
          <div class="pa-5">
            <div v-if="isLoadingSpeakers" class="center-pad"><VProgressCircular indeterminate color="primary" size="28" /></div>
            <div v-else>
              <div v-if="speakersList.length === 0 && !showAddSpeaker" class="text-center py-6">
                <VIcon icon="tabler-user-off" size="40" color="grey-lighten-1" class="mb-3" />
                <p class="text-medium-emphasis text-body-2">Aucun intervenant ajouté</p>
              </div>
              <div v-else class="speakers-list mb-4">
                <div v-for="sp in speakersList" :key="sp.id" class="speaker-item">
                  <VAvatar size="40" color="primary" variant="tonal">
                    <img v-if="sp.photo" :src="sp.photo" :alt="sp.name">
                    <span v-else>{{ sp.name?.[0]?.toUpperCase() }}</span>
                  </VAvatar>
                  <div>
                    <p class="speaker-name">{{ sp.name }}</p>
                    <p class="speaker-title">{{ sp.title || sp.role || '-' }}</p>
                  </div>
                </div>
              </div>
              <div v-if="showAddSpeaker" class="add-form">
                <VAlert v-if="speakerError" type="error" variant="tonal" density="compact" class="mb-3">{{ speakerError }}</VAlert>
                <VRow>
                  <VCol cols="12" md="6"><AppTextField v-model="speakerForm.name" label="Nom *" placeholder="Ex: Ahmed Ben Ali" /></VCol>
                  <VCol cols="12" md="6"><AppTextField v-model="speakerForm.title" label="Titre / Rôle" placeholder="Ex: Comédien, Humoriste..." /></VCol>
                  <VCol cols="12"><VTextarea v-model="speakerForm.bio" label="Biographie" rows="3" placeholder="Courte bio..." /></VCol>
                  <VCol cols="12">
                    <label class="text-body-2 text-medium-emphasis d-block mb-1">Photo</label>
                    <input type="file" accept="image/*" @change="(e) => { const f = (e.target as HTMLInputElement).files?.[0]; if(f) speakerForm.photo = f }">
                  </VCol>
                </VRow>
                <div class="d-flex gap-2 mt-3">
                  <VBtn variant="outlined" size="small" @click="showAddSpeaker = false">Annuler</VBtn>
                  <VBtn color="primary" size="small" :loading="isSavingSpeaker" @click="addSpeaker">Ajouter</VBtn>
                </div>
              </div>
              <VBtn v-if="!showAddSpeaker" variant="tonal" color="primary" size="small" prepend-icon="tabler-plus" @click="showAddSpeaker = true">Ajouter un intervenant</VBtn>
            </div>
          </div>
        </VCardText>
      </VCard>
    </VDialog>

  </div>
</template>

<style scoped lang="scss">
.events-page { display: flex; flex-direction: column; gap: 20px; }
.page-header { display: flex; align-items: flex-start; justify-content: space-between; }
.page-title { font-size: 20px; font-weight: 600; color: #111827; margin: 0 0 4px; }
.page-sub   { font-size: 13px; color: #6B7280; margin: 0; }
.btn-primary {
  display: inline-flex; align-items: center; gap: 7px; padding: 9px 18px;
  background: #4F46E5; color: white; border: none; border-radius: 8px;
  font-size: 13.5px; font-weight: 500; cursor: pointer; transition: background .15s;
  &:hover { background: #4338CA; }
}
.filters-bar { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.search-wrap {
  display: flex; align-items: center; gap: 8px; background: white;
  border: 0.5px solid #E5E7EB; border-radius: 8px; padding: 7px 12px;
  flex: 1; min-width: 200px;
  &:focus-within { border-color: #818CF8; box-shadow: 0 0 0 3px rgba(99,102,241,0.08); }
  .si { color: #9CA3AF; flex-shrink: 0; }
  .search-input { border: none; background: none; outline: none; font-size: 13px; color: #111827; width: 100%; &::placeholder { color: #9CA3AF; } }
}
.filter-tabs { display: flex; background: white; border: 0.5px solid #E5E7EB; border-radius: 8px; overflow: hidden; }
.ftab {
  padding: 7px 14px; border: none; background: none; font-size: 13px; color: #6B7280; cursor: pointer;
  transition: all .15s; border-right: 0.5px solid #E5E7EB;
  &:last-child { border-right: none; }
  &.active { background: #4F46E5; color: white; }
  &:hover:not(.active) { background: #F9FAFB; }
}
.results-count { font-size: 12px; color: #9CA3AF; background: #F3F4F6; padding: 6px 12px; border-radius: 20px; white-space: nowrap; }
.center-pad { display: flex; justify-content: center; padding: 48px; }
.empty-state { text-align: center; padding: 56px 24px; display: flex; flex-direction: column; align-items: center; }
.empty-title { font-size: 15px; font-weight: 500; color: #374151; margin-bottom: 6px; }
.empty-sub   { font-size: 13px; color: #9CA3AF; }
.mt-4        { margin-top: 16px; }
.events-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
.event-card { background: white; border: 0.5px solid #E5E7EB; border-radius: 12px; overflow: hidden; transition: box-shadow .2s; &:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.08); } }
.event-banner { position: relative; height: 140px; background: #F3F4F6; }
.banner-img { width: 100%; height: 100%; object-fit: cover; }
.banner-placeholder { height: 100%; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%); }
.banner-badges { position: absolute; top: 10px; left: 10px; display: flex; gap: 6px; }
.badge-status, .badge-type { padding: 3px 8px; border-radius: 20px; font-size: 11px; font-weight: 600; }
.badge-active   { background: rgba(16,185,129,0.15); color: #059669; }
.badge-inactive { background: rgba(107,114,128,0.15); color: #6B7280; }
.badge-paid     { background: rgba(79,70,229,0.15); color: #4F46E5; }
.badge-free     { background: rgba(16,185,129,0.15); color: #059669; }
.event-body { padding: 14px 16px; }
.event-title { font-size: 14px; font-weight: 600; color: #111827; margin: 0 0 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.event-meta { display: flex; flex-direction: column; gap: 5px; }
.meta-item { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #6B7280; }
.event-actions { display: flex; align-items: center; gap: 4px; padding: 10px 12px; border-top: 0.5px solid #F3F4F6; background: #FAFAFA; }
.action-btn {
  display: flex; align-items: center; justify-content: center; width: 30px; height: 30px;
  border: 0.5px solid #E5E7EB; border-radius: 6px; background: white; cursor: pointer; color: #6B7280; transition: all .15s;
  &:hover { background: #F3F4F6; color: #111827; }
  &--danger:hover { background: #FEF2F2; color: #EF4444; border-color: #FECACA; }
}
.dialog-head { display: flex; align-items: center; gap: 14px; padding: 18px 20px 14px; }
.dialog-icon { width: 38px; height: 38px; background: #EEF2FF; border-radius: 9px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.dialog-title { font-size: 15px; font-weight: 600; color: #111827; margin: 0 0 2px; }
.dialog-sub   { font-size: 12px; color: #9CA3AF; margin: 0; }
.dialog-tabs { display: flex; padding: 0 20px; gap: 0; }
.dtab {
  display: flex; align-items: center; gap: 6px; padding: 10px 16px; border: none; background: none;
  font-size: 13px; color: #6B7280; cursor: pointer; border-bottom: 2px solid transparent; transition: all .15s;
  &.active { color: #4F46E5; border-bottom-color: #4F46E5; }
  &:hover:not(.active) { color: #374151; }
}
.preview-img { width: 100%; height: 160px; object-fit: cover; border-radius: 8px; border: 0.5px solid #E5E7EB; }
.schedule-list { display: flex; flex-direction: column; gap: 8px; }
.schedule-item { display: flex; gap: 14px; align-items: flex-start; padding: 10px 12px; background: #F9FAFB; border-radius: 8px; border-left: 3px solid #4F46E5; }
.schedule-time { font-size: 12px; font-weight: 600; color: #4F46E5; white-space: nowrap; min-width: 80px; }
.schedule-title { font-size: 13px; font-weight: 500; color: #111827; margin: 0 0 2px; }
.schedule-desc  { font-size: 12px; color: #9CA3AF; margin: 0; }
.speakers-list { display: flex; flex-direction: column; gap: 8px; }
.speaker-item { display: flex; align-items: center; gap: 12px; padding: 10px 12px; background: #F9FAFB; border-radius: 8px; }
.speaker-name  { font-size: 13px; font-weight: 500; color: #111827; margin: 0 0 2px; }
.speaker-title { font-size: 12px; color: #9CA3AF; margin: 0; }
.add-form { background: #F9FAFB; border-radius: 10px; padding: 16px; margin-bottom: 12px; border: 0.5px solid #E5E7EB; }
</style>