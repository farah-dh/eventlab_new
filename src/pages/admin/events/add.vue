<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'


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
const isLoadingOptions = ref(true)
const formError = ref<Record<string, string>>({})
const formErrorMsg = ref('')
const successMsg = ref('')

const categories = ref<any[]>([])
const locations = ref<any[]>([])

const form = ref({
  title: '',
  short_description: '',
  description: '',
  category: null as number | null,
  location: null as number | null,
  location_address: '',
  start_date: '',
  end_date: '',
  type: 1, // 1=Payant, 2=Gratuit
  price: 0,
  seats: 100,
  cover_image: '',
  link: '',
  step: 1,
})

// ─── Charger catégories et lieux ───
const loadOptions = async () => {
  isLoadingOptions.value = true
  try {
    const [catsData, locsData] = await Promise.all([
      apiFetch('/events/categories/'),
      apiFetch('/events/locations/'),
    ])
    categories.value = (catsData.results || catsData || []).filter((c: any) => c.status)
    locations.value = (locsData.results || locsData || []).filter((l: any) => l.status)
  }
  catch (err) {
    console.error('Erreur chargement options:', err)
    formErrorMsg.value = '❌ Impossible de charger les catégories ou les lieux.'
  }
  finally {
    isLoadingOptions.value = false
  }
}

const categoryOptions = computed(() =>
  categories.value.map(c => ({ title: c.name, value: c.id })),
)

const locationOptions = computed(() =>
  locations.value.map(l => ({ title: l.name, value: l.id })),
)

// ─── Submit ───
const saveEvent = async () => {
  formError.value = {}
  formErrorMsg.value = ''

  // Validations basiques
  if (!form.value.title) {
    formError.value.title = 'Le titre est obligatoire'
    return
  }
  if (!form.value.category) {
    formError.value.category = 'La catégorie est obligatoire'
    return
  }
  if (!form.value.location) {
    formError.value.location = 'Le lieu est obligatoire'
    return
  }
  if (!form.value.start_date) {
    formError.value.start_date = 'La date de début est obligatoire'
    return
  }
  if (!form.value.end_date) {
    formError.value.end_date = 'La date de fin est obligatoire'
    return
  }
  if (new Date(form.value.end_date) < new Date(form.value.start_date)) {
    formError.value.end_date = 'La date de fin doit être après la date de début'
    return
  }

  isSaving.value = true
  try {
    await apiFetch('/events/', {
      method: 'POST',
      body: JSON.stringify({
        title:             form.value.title,
        short_description: form.value.short_description,
        description:       form.value.description,
        category:          form.value.category,
        location:          form.value.location,
        location_address:  form.value.location_address,
        start_date:        form.value.start_date,
        end_date:          form.value.end_date,
        type:              form.value.type,
        price:             form.value.type === 2 ? 0 : form.value.price,
        seats:             form.value.seats,
        cover_image:       form.value.cover_image,
        link:              form.value.link,
        step:              form.value.step,
      }),
    })

    successMsg.value = '✅ Événement créé avec succès !'
    setTimeout(() => router.push('/admin/events'), 1500)
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

onMounted(loadOptions)
</script>

<template>
  <div>
    <!-- ── Header ── -->
    <div class="d-flex align-center gap-3 mb-6">
      <VBtn icon variant="text" @click="router.push('/admin/events')">
        <VIcon icon="tabler-arrow-left" size="20" />
      </VBtn>
      <div>
        <h4 class="text-h4 font-weight-bold">Ajouter un événement</h4>
        <p class="text-body-1 text-medium-emphasis mt-1">
          Créez un nouvel événement sur la plateforme
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
    <div v-if="isLoadingOptions" class="d-flex flex-column align-center justify-center py-16">
      <VProgressCircular indeterminate color="primary" size="48" />
      <p class="text-body-1 text-medium-emphasis mt-4">Chargement...</p>
    </div>

    <VRow v-else>
      <!-- ── Formulaire principal ── -->
      <VCol cols="12" md="8">

        <!-- Section Infos générales -->
        <VCard class="mb-6">
          <VCardTitle class="pa-6 pb-2">
            <span class="text-h6 font-weight-bold">Informations générales</span>
          </VCardTitle>
          <VCardText class="pa-6">
            <VRow>
              <VCol cols="12">
                <VTextField
                  v-model="form.title"
                  label="Titre de l'événement *"
                  placeholder="Ex: Concert de jazz à Carthage"
                  prepend-inner-icon="tabler-calendar-event"
                  :error-messages="formError.title"
                />
              </VCol>
              <VCol cols="12" md="6">
                <VSelect
                  v-model="form.category"
                  :items="categoryOptions"
                  label="Catégorie *"
                  prepend-inner-icon="tabler-tag"
                  :error-messages="formError.category"
                  no-data-text="Aucune catégorie active — créez-en une d'abord"
                />
              </VCol>
              <VCol cols="12" md="6">
                <VSelect
                  v-model="form.location"
                  :items="locationOptions"
                  label="Lieu *"
                  prepend-inner-icon="tabler-map-pin"
                  :error-messages="formError.location"
                  no-data-text="Aucun lieu actif — créez-en un d'abord"
                />
              </VCol>
              <VCol cols="12">
                <VTextField
                  v-model="form.location_address"
                  label="Adresse complète"
                  placeholder="Ex: Rue Habib Bourguiba, Tunis"
                  prepend-inner-icon="tabler-map"
                  :error-messages="formError.location_address"
                />
              </VCol>
              <VCol cols="12">
                <VTextField
                  v-model="form.short_description"
                  label="Description courte"
                  placeholder="Une phrase accrocheuse..."
                  prepend-inner-icon="tabler-align-left"
                  counter="200"
                  maxlength="200"
                  :error-messages="formError.short_description"
                />
              </VCol>
              <VCol cols="12">
                <VTextarea
                  v-model="form.description"
                  label="Description complète"
                  placeholder="Détails de l'événement, programme, artistes..."
                  prepend-inner-icon="tabler-file-text"
                  rows="5"
                  :error-messages="formError.description"
                />
              </VCol>
            </VRow>
          </VCardText>
        </VCard>

        <!-- Section Dates -->
        <VCard class="mb-6">
          <VCardTitle class="pa-6 pb-2">
            <span class="text-h6 font-weight-bold">Dates</span>
          </VCardTitle>
          <VCardText class="pa-6">
            <VRow>
              <VCol cols="12" md="6">
                <VTextField
                  v-model="form.start_date"
                  label="Date de début *"
                  type="date"
                  prepend-inner-icon="tabler-calendar"
                  :error-messages="formError.start_date"
                />
              </VCol>
              <VCol cols="12" md="6">
                <VTextField
                  v-model="form.end_date"
                  label="Date de fin *"
                  type="date"
                  prepend-inner-icon="tabler-calendar"
                  :error-messages="formError.end_date"
                />
              </VCol>
            </VRow>
          </VCardText>
        </VCard>

        <!-- Section Tarifs & Places -->
        <VCard class="mb-6">
          <VCardTitle class="pa-6 pb-2">
            <span class="text-h6 font-weight-bold">Tarifs & Places</span>
          </VCardTitle>
          <VCardText class="pa-6">
            <VRow>
              <VCol cols="12" md="6">
                <VSelect
                  v-model="form.type"
                  :items="[
                    { title: 'Payant', value: 1 },
                    { title: 'Gratuit', value: 2 },
                  ]"
                  label="Type d'événement *"
                  prepend-inner-icon="tabler-cash"
                  :error-messages="formError.type"
                />
              </VCol>
              <VCol cols="12" md="6">
                <VTextField
                  v-model.number="form.price"
                  label="Prix (DT)"
                  type="number"
                  step="0.001"
                  min="0"
                  :disabled="form.type === 2"
                  prepend-inner-icon="tabler-currency-dollar"
                  :error-messages="formError.price"
                  :hint="form.type === 2 ? 'Gratuit' : ''"
                  persistent-hint
                />
              </VCol>
              <VCol cols="12">
                <VTextField
                  v-model.number="form.seats"
                  label="Nombre de places"
                  type="number"
                  min="1"
                  prepend-inner-icon="tabler-ticket"
                  :error-messages="formError.seats"
                  hint="Laissez vide pour illimité"
                  persistent-hint
                />
              </VCol>
            </VRow>
          </VCardText>
        </VCard>

        <!-- Section Médias & Liens -->
        <VCard>
          <VCardTitle class="pa-6 pb-2">
            <span class="text-h6 font-weight-bold">Médias & Liens</span>
          </VCardTitle>
          <VCardText class="pa-6">
            <VRow>
              <VCol cols="12">
                <VTextField
                  v-model="form.cover_image"
                  label="Image de couverture (URL)"
                  placeholder="https://example.com/image.jpg"
                  prepend-inner-icon="tabler-photo"
                  :error-messages="formError.cover_image"
                />
              </VCol>
              <VCol v-if="form.cover_image" cols="12">
                <img :src="form.cover_image" alt="Aperçu" style="width:100%; max-height:250px; object-fit:cover; border-radius:8px; border:0.5px solid #E5E7EB;">
              </VCol>
              <VCol cols="12">
                <VTextField
                  v-model="form.link"
                  label="Lien externe (optionnel)"
                  placeholder="https://site-de-l-evenement.com"
                  prepend-inner-icon="tabler-link"
                  :error-messages="formError.link"
                />
              </VCol>
            </VRow>
          </VCardText>
        </VCard>
      </VCol>

      <!-- ── Sidebar droite ── -->
      <VCol cols="12" md="4">

        <!-- Récap -->
        <VCard class="mb-6" color="info" variant="tonal">
          <VCardText class="pa-6">
            <div class="d-flex align-center gap-2 mb-3">
              <VIcon icon="tabler-info-circle" size="20" />
              <span class="text-subtitle-2 font-weight-bold">Récapitulatif</span>
            </div>
            <div class="text-caption">
              <p class="mb-2">
                <strong>Titre :</strong> {{ form.title || '—' }}
              </p>
              <p class="mb-2">
                <strong>Type :</strong> {{ form.type === 1 ? 'Payant' : 'Gratuit' }}
              </p>
              <p v-if="form.type === 1" class="mb-2">
                <strong>Prix :</strong> {{ form.price }} DT
              </p>
              <p class="mb-2">
                <strong>Places :</strong> {{ form.seats || 'Illimitées' }}
              </p>
              <p class="mb-0">
                <strong>Du</strong> {{ form.start_date || '—' }}
                <strong>au</strong> {{ form.end_date || '—' }}
              </p>
            </div>
          </VCardText>
        </VCard>

        <!-- Info KYC -->
        <VCard class="mb-6" color="warning" variant="tonal">
          <VCardText class="pa-6">
            <div class="d-flex align-center gap-2 mb-2">
              <VIcon icon="tabler-alert-triangle" size="20" />
              <span class="text-subtitle-2 font-weight-bold">À savoir</span>
            </div>
            <p class="text-caption mb-0">
              L'événement sera créé avec le statut actif par défaut.
              Vous pourrez le modifier, le mettre en vedette ou le désactiver
              depuis la liste.
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
              prepend-icon="tabler-calendar-plus"
              @click="saveEvent"
            >
              Créer l'événement
            </VBtn>
            <VBtn
              variant="outlined"
              color="secondary"
              block
              size="large"
              class="mt-3"
              @click="router.push('/admin/events')"
            >
              Annuler
            </VBtn>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>
  </div>
</template>