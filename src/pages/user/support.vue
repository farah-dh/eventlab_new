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
const tickets = ref<any[]>([])
const showNewTicket = ref(false)
const showDetail = ref(false)
const selectedTicket = ref<any>(null)
const replyText = ref('')
const isSending = ref(false)

const newTicket = ref({
  subject: '',
  message: '',
  priority: 'medium',
})

// ─── Fetch ───
const fetchTickets = async () => {
  isLoading.value = true
  try {
    const data = await apiFetch('/support/tickets/')
    const results = data.results || data.data || data || []
    tickets.value = Array.isArray(results) ? results : []
  } catch (err) {
    console.error('Erreur chargement tickets:', err)
    tickets.value = []
  } finally {
    isLoading.value = false
  }
}

// ─── Actions ───
const createTicket = async () => {
  isSending.value = true
  try {
    await apiFetch('/support/tickets/', { method: 'POST', body: JSON.stringify(newTicket.value) })
    showNewTicket.value = false
    newTicket.value = { subject: '', message: '', priority: 'medium' }
    await fetchTickets()
  } catch (err) { console.error('Erreur création ticket:', err) }
  finally { isSending.value = false }
}

const viewTicket = (ticket: any) => {
  selectedTicket.value = ticket
  replyText.value = ''
  showDetail.value = true
}

const replyTicket = async () => {
  if (!replyText.value.trim() || !selectedTicket.value) return
  isSending.value = true
  try {
    await apiFetch(`/support/tickets/${selectedTicket.value.id}/reply/`, {
      method: 'POST',
      body: JSON.stringify({ message: replyText.value }),
    })
    replyText.value = ''
    await fetchTickets()
    // Refresh selected ticket
    const updated = tickets.value.find(t => t.id === selectedTicket.value.id)
    if (updated) selectedTicket.value = updated
  } catch (err) { console.error('Erreur réponse:', err) }
  finally { isSending.value = false }
}

const closeTicket = async (ticket: any) => {
  if (confirm('Fermer ce ticket ?')) {
    try {
      await apiFetch(`/support/tickets/${ticket.id}/close/`, { method: 'POST' })
      await fetchTickets()
      showDetail.value = false
    } catch (err) { console.error('Erreur fermeture:', err) }
  }
}

// ─── Computed ───
const openCount = computed(() => tickets.value.filter(t => t.status !== 'closed').length)
const closedCount = computed(() => tickets.value.filter(t => t.status === 'closed').length)

// ─── Helpers ───
function formatDate(dateString: string | null): string {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function getStatusConfig(status: string) {
  const config: Record<string, { label: string; color: string; icon: string }> = {
    open: { label: 'Ouvert', color: 'info', icon: 'tabler-message-dots' },
    pending: { label: 'En attente', color: 'warning', icon: 'tabler-clock' },
    answered: { label: 'Répondu', color: 'success', icon: 'tabler-message-check' },
    closed: { label: 'Fermé', color: 'default', icon: 'tabler-lock' },
  }
  return config[status] || { label: status || 'Inconnu', color: 'default', icon: 'tabler-help' }
}

function getPriorityConfig(priority: string) {
  const config: Record<string, { label: string; color: string }> = {
    low: { label: 'Basse', color: 'success' },
    medium: { label: 'Moyenne', color: 'warning' },
    high: { label: 'Haute', color: 'error' },
  }
  return config[priority] || { label: priority || '-', color: 'default' }
}

onMounted(() => { fetchTickets() })
</script>

<template>
  <div>
    <!-- Header -->
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h4 class="text-h4 font-weight-bold">Support</h4>
        <p class="text-body-1 text-medium-emphasis mt-1">Besoin d'aide ? Contactez notre équipe</p>
      </div>
      <VBtn color="primary" prepend-icon="tabler-message-plus" @click="showNewTicket = true">
        Nouveau ticket
      </VBtn>
    </div>

    <!-- Stats -->
    <VRow class="mb-6">
      <VCol cols="4">
        <VCard class="text-center pa-4">
          <h5 class="text-h5 font-weight-bold text-primary">{{ tickets.length }}</h5>
          <p class="text-caption text-medium-emphasis mb-0">Total</p>
        </VCard>
      </VCol>
      <VCol cols="4">
        <VCard class="text-center pa-4">
          <h5 class="text-h5 font-weight-bold text-info">{{ openCount }}</h5>
          <p class="text-caption text-medium-emphasis mb-0">Ouverts</p>
        </VCard>
      </VCol>
      <VCol cols="4">
        <VCard class="text-center pa-4">
          <h5 class="text-h5 font-weight-bold text-medium-emphasis">{{ closedCount }}</h5>
          <p class="text-caption text-medium-emphasis mb-0">Fermés</p>
        </VCard>
      </VCol>
    </VRow>

    <!-- Loading -->
    <div v-if="isLoading" class="d-flex flex-column align-center justify-center py-16">
      <VProgressCircular indeterminate color="primary" size="48" />
    </div>

    <template v-else>
      <!-- Tickets List -->
      <div v-if="tickets.length > 0" class="d-flex flex-column gap-3">
        <VCard v-for="ticket in tickets" :key="ticket.id" hover @click="viewTicket(ticket)">
          <VCardText class="d-flex align-center gap-4 pa-4">
            <VAvatar :color="getStatusConfig(ticket.status).color" variant="tonal" size="44">
              <VIcon :icon="getStatusConfig(ticket.status).icon" size="22" />
            </VAvatar>
            <div class="flex-grow-1">
              <div class="d-flex align-center gap-2 mb-1">
                <p class="text-body-1 font-weight-bold mb-0">{{ ticket.subject || ticket.title || 'Ticket #' + ticket.id }}</p>
                <VChip :color="getPriorityConfig(ticket.priority).color" size="x-small" variant="tonal">
                  {{ getPriorityConfig(ticket.priority).label }}
                </VChip>
              </div>
              <p class="text-body-2 text-medium-emphasis mb-0">
                {{ (ticket.message || ticket.body || '').substring(0, 100) }}...
              </p>
              <p class="text-caption text-medium-emphasis mt-1 mb-0">
                <VIcon icon="tabler-clock" size="12" class="me-1" />
                {{ formatDate(ticket.created_at) }}
              </p>
            </div>
            <VChip :color="getStatusConfig(ticket.status).color" size="small" variant="tonal">
              {{ getStatusConfig(ticket.status).label }}
            </VChip>
          </VCardText>
        </VCard>
      </div>

      <!-- Empty -->
      <VCard v-else class="text-center py-16">
        <VAvatar color="info" variant="tonal" size="80" class="mb-4">
          <VIcon icon="tabler-headset" size="40" />
        </VAvatar>
        <h5 class="text-h5 font-weight-bold mb-2">Aucun ticket</h5>
        <p class="text-body-1 text-medium-emphasis mb-4">Vous n'avez pas encore créé de ticket de support</p>
        <VBtn color="primary" prepend-icon="tabler-message-plus" @click="showNewTicket = true">Créer un ticket</VBtn>
      </VCard>
    </template>

    <!-- New Ticket Dialog -->
    <VDialog v-model="showNewTicket" max-width="550" persistent>
      <VCard>
        <VCardTitle class="d-flex justify-space-between align-center pa-6">
          <span class="text-h6 font-weight-bold">Nouveau ticket</span>
          <VBtn icon variant="text" size="small" @click="showNewTicket = false">
            <VIcon icon="tabler-x" />
          </VBtn>
        </VCardTitle>
        <VDivider />
        <VCardText class="pa-6">
          <VTextField v-model="newTicket.subject" label="Sujet *" prepend-inner-icon="tabler-message" class="mb-4" />
          <VSelect
            v-model="newTicket.priority"
            label="Priorité"
            :items="[
              { title: 'Basse', value: 'low' },
              { title: 'Moyenne', value: 'medium' },
              { title: 'Haute', value: 'high' },
            ]"
            class="mb-4"
          />
          <VTextarea v-model="newTicket.message" label="Message *" rows="5" placeholder="Décrivez votre problème..." />
        </VCardText>
        <VDivider />
        <VCardActions class="pa-6">
          <VSpacer />
          <VBtn variant="outlined" @click="showNewTicket = false">Annuler</VBtn>
          <VBtn color="primary" :loading="isSending" prepend-icon="tabler-send" @click="createTicket">Envoyer</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Ticket Detail Dialog -->
    <VDialog v-model="showDetail" max-width="600">
      <VCard v-if="selectedTicket">
        <VCardTitle class="d-flex justify-space-between align-center pa-6">
          <span class="text-h6 font-weight-bold">{{ selectedTicket.subject || 'Ticket #' + selectedTicket.id }}</span>
          <VBtn icon variant="text" size="small" @click="showDetail = false">
            <VIcon icon="tabler-x" />
          </VBtn>
        </VCardTitle>
        <VDivider />
        <VCardText class="pa-6">
          <div class="d-flex gap-2 mb-4">
            <VChip :color="getStatusConfig(selectedTicket.status).color" size="small" variant="tonal">
              {{ getStatusConfig(selectedTicket.status).label }}
            </VChip>
            <VChip :color="getPriorityConfig(selectedTicket.priority).color" size="small" variant="tonal">
              {{ getPriorityConfig(selectedTicket.priority).label }}
            </VChip>
            <VChip size="small" variant="tonal">{{ formatDate(selectedTicket.created_at) }}</VChip>
          </div>

          <VCard variant="tonal" color="default" class="mb-4">
            <VCardText>
              <p class="text-body-1 mb-0">{{ selectedTicket.message || selectedTicket.body || '-' }}</p>
            </VCardText>
          </VCard>

          <!-- Reply -->
          <div v-if="selectedTicket.status !== 'closed'">
            <VTextarea v-model="replyText" label="Votre réponse" rows="3" placeholder="Tapez votre message..." class="mb-3" />
            <div class="d-flex gap-2">
              <VBtn color="primary" :loading="isSending" prepend-icon="tabler-send" @click="replyTicket">Répondre</VBtn>
              <VBtn color="error" variant="tonal" prepend-icon="tabler-lock" @click="closeTicket(selectedTicket)">Fermer le ticket</VBtn>
            </div>
          </div>
          <VAlert v-else type="info" variant="tonal">Ce ticket est fermé.</VAlert>
        </VCardText>
      </VCard>
    </VDialog>
  </div>
</template>