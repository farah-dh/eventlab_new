<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

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

// ─── State ───
const isLoading = ref(true)
const savedEvents = ref<any[]>([])
const removingId = ref<number | null>(null)

// ─── Fetch ───
const fetchSaved = async () => {
  isLoading.value = true
  try {
    const data = await apiFetch('/events/saved/')
    const results = data.results || data.data || data || []
    savedEvents.value = Array.isArray(results) ? results : []
  } catch (err) {
    console.error('Erreur chargement sauvegardés:', err)
    savedEvents.value = []
  } finally {
    isLoading.value = false
  }
}

// ─── Actions ───
const unsaveEvent = async (event: any) => {
  removingId.value = event.id
  try {
    await apiFetch(`/events/${event.id}/unsave_event/`, { method: 'DELETE' })
    savedEvents.value = savedEvents.value.filter(e => e.id !== event.id)
  } catch (err) { console.error('Erreur suppression:', err) }
  finally { removingId.value = null }
}

// ─── Helpers ───
function formatDate(dateString: string | null): string {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatPrice(price: any): string {
  if (price === null || price === undefined || price === 0) return 'Gratuit'
  return `${Number(price).toFixed(3)} DT`
}

onMounted(() => { fetchSaved() })
</script>

<template>
  <div>
    <!-- Header -->
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h4 class="text-h4 font-weight-bold">Événements sauvegardés</h4>
        <p class="text-body-1 text-medium-emphasis mt-1">Retrouvez les événements que vous avez mis de côté</p>
      </div>
      <VChip color="error" variant="tonal">
        <VIcon icon="tabler-heart" size="16" start />
        {{ savedEvents.length }} sauvegardé(s)
      </VChip>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="d-flex flex-column align-center justify-center py-16">
      <VProgressCircular indeterminate color="primary" size="48" />
    </div>

    <template v-else>
      <!-- Grid -->
      <VRow v-if="savedEvents.length > 0">
        <VCol v-for="event in savedEvents" :key="event.id" cols="12" sm="6" lg="4">
          <VCard hover class="h-100 d-flex flex-column">
            <!-- Image -->
            <div class="position-relative" style="height: 160px; overflow: hidden;">
              <VImg v-if="event.cover_image" :src="event.cover_image" height="160" cover />
              <div v-else class="d-flex align-center justify-center h-100" style="background: linear-gradient(135deg, rgb(var(--v-theme-error)), rgb(var(--v-theme-warning)));">
                <VIcon icon="tabler-heart" size="48" color="white" />
              </div>
              <div class="position-absolute" style="top: 8px; left: 8px;">
                <VChip :color="event.price ? 'warning' : 'success'" size="small" variant="elevated">
                  {{ formatPrice(event.price) }}
                </VChip>
              </div>
            </div>

            <!-- Content -->
            <VCardText class="pa-4 flex-grow-1 d-flex flex-column">
              <VChip v-if="event.category_name" color="primary" size="x-small" variant="tonal" class="mb-2" style="width: fit-content;">
                {{ event.category_name }}
              </VChip>

              <h6 class="text-subtitle-1 font-weight-bold mb-2">{{ event.title }}</h6>

              <div class="d-flex flex-column gap-1 mb-3 flex-grow-1">
                <div class="d-flex align-center gap-2 text-caption text-medium-emphasis">
                  <VIcon icon="tabler-user" size="14" />
                  {{ event.organizer_name || '-' }}
                </div>
                <div class="d-flex align-center gap-2 text-caption text-medium-emphasis">
                  <VIcon icon="tabler-calendar" size="14" />
                  {{ formatDate(event.start_date) }}
                </div>
                <div v-if="event.location_name" class="d-flex align-center gap-2 text-caption text-medium-emphasis">
                  <VIcon icon="tabler-map-pin" size="14" />
                  {{ event.location_name }}
                </div>
              </div>

              <!-- Actions -->
              <div class="d-flex gap-2 mt-auto pt-3" style="border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));">
                <VBtn color="error" variant="tonal" size="small" prepend-icon="tabler-heart-off" :loading="removingId === event.id" @click="unsaveEvent(event)">
                  Retirer
                </VBtn>
              </div>
            </VCardText>
          </VCard>
        </VCol>
      </VRow>

      <!-- Empty -->
      <VCard v-else class="text-center py-16">
        <VAvatar color="error" variant="tonal" size="80" class="mb-4">
          <VIcon icon="tabler-heart-off" size="40" />
        </VAvatar>
        <h5 class="text-h5 font-weight-bold mb-2">Aucun événement sauvegardé</h5>
        <p class="text-body-1 text-medium-emphasis mb-4">Explorez les événements et sauvegardez vos favoris</p>
        <VBtn color="primary" prepend-icon="tabler-calendar-event" to="/user/events">Découvrir les événements</VBtn>
      </VCard>
    </template>
  </div>
</template>