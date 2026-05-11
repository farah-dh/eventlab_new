<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'

const getToken = () =>
  localStorage.getItem('organizer_access_token') ||
  localStorage.getItem('access_token') ||
  localStorage.getItem('token')

const apiFetch = async (endpoint: string, options: RequestInit = {}) => {
  const token = getToken()
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  })
  if (!res.ok) throw new Error(`Erreur ${res.status}`)
  return res.json()
}

const loading       = ref(true)
const markingAll    = ref(false)
const notifications = ref<any[]>([])
const filter        = ref<'all' | 'unread'>('all')
const snackbar      = ref({ show: false, msg: '', color: 'success' })
let   pollInterval  = null as any

const fetchNotifications = async (silent = false) => {
  if (!silent) loading.value = true
  try {
    const data = await apiFetch('/notifications/logs/')
    const results = data.results || data.data || data || []
    notifications.value = Array.isArray(results) ? results : []
  }
  catch { }
  finally { if (!silent) loading.value = false }
}

const markRead = async (notif: any) => {
  if (notif.is_read) return
  try {
    await apiFetch(`/notifications/logs/${notif.id}/mark_read/`, { method: 'POST' })
    notif.is_read = true
  }
  catch { }
}

const markAllRead = async () => {
  markingAll.value = true
  try {
    await apiFetch('/notifications/logs/mark_all_read/', { method: 'POST' })
    notifications.value.forEach(n => (n.is_read = true))
    snackbar.value = { show: true, msg: 'Toutes les notifications marquées comme lues', color: 'success' }
  }
  catch {
    snackbar.value = { show: true, msg: 'Erreur lors de la mise à jour', color: 'error' }
  }
  finally { markingAll.value = false }
}

const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length)
const filtered = computed(() =>
  filter.value === 'unread' ? notifications.value.filter(n => !n.is_read) : notifications.value,
)

const notifIcon = (type: string = '') => {
  const t = (type || '').toLowerCase()
  if (t.includes('reserv') || t.includes('booking') || t.includes('ticket')) return { icon: 'tabler-ticket', color: 'primary' }
  if (t.includes('pay') || t.includes('paiement')) return { icon: 'tabler-cash', color: 'success' }
  if (t.includes('cancel') || t.includes('annul')) return { icon: 'tabler-x', color: 'error' }
  if (t.includes('withdraw') || t.includes('retrait')) return { icon: 'tabler-arrow-bar-to-down', color: 'warning' }
  return { icon: 'tabler-bell', color: 'secondary' }
}

const timeAgo = (dateStr: string) => {
  if (!dateStr) return ''
  const diff = Date.now() - new Date(dateStr).getTime()
  const min = Math.floor(diff / 60000)
  const hr  = Math.floor(min / 60)
  const day = Math.floor(hr / 24)
  if (min < 1)  return "À l'instant"
  if (min < 60) return `Il y a ${min} min`
  if (hr  < 24) return `Il y a ${hr}h`
  if (day < 7)  return `Il y a ${day}j`
  return new Date(dateStr).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })
}

const notifTitle = (n: any) => n.title || n.subject || n.notification_type || 'Notification'
const notifBody  = (n: any) => n.message || n.body || n.content || n.description || ''

onMounted(() => {
  fetchNotifications()
  pollInterval = setInterval(() => fetchNotifications(true), 30000)
})
onUnmounted(() => { if (pollInterval) clearInterval(pollInterval) })
</script>

<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h4 class="text-h4 font-weight-bold">Notifications</h4>
        <p class="text-body-1 text-medium-emphasis mt-1">Suivez l'activité de vos événements en temps réel</p>
      </div>
      <div class="d-flex gap-3 align-center">
        <VChip v-if="unreadCount > 0" color="primary" variant="tonal" prepend-icon="tabler-bell-ringing" size="small">
          {{ unreadCount }} non lue{{ unreadCount > 1 ? 's' : '' }}
        </VChip>
        <VBtn v-if="unreadCount > 0" variant="outlined" size="small" prepend-icon="tabler-checks" :loading="markingAll" @click="markAllRead">
          Tout marquer lu
        </VBtn>
        <VBtn icon variant="text" size="small" :loading="loading" @click="fetchNotifications()">
          <VIcon icon="tabler-refresh" size="18" />
        </VBtn>
      </div>
    </div>

    <VCard class="mb-4">
      <VCardText class="pa-3">
        <VBtnToggle v-model="filter" mandatory variant="outlined" color="primary" density="compact">
          <VBtn value="all" size="small">
            <VIcon icon="tabler-list" size="16" class="me-1" />
            Toutes
            <VChip class="ms-2" size="x-small" color="secondary" variant="tonal">{{ notifications.length }}</VChip>
          </VBtn>
          <VBtn value="unread" size="small">
            <VIcon icon="tabler-bell" size="16" class="me-1" />
            Non lues
            <VChip class="ms-2" size="x-small" color="primary" variant="tonal">{{ unreadCount }}</VChip>
          </VBtn>
        </VBtnToggle>
      </VCardText>
    </VCard>

    <VCard v-if="loading">
      <VCardText class="d-flex justify-center pa-12">
        <VProgressCircular indeterminate color="primary" size="44" />
      </VCardText>
    </VCard>

    <VCard v-else-if="filtered.length === 0">
      <VCardText class="text-center pa-12">
        <VIcon :icon="filter === 'unread' ? 'tabler-bell-check' : 'tabler-bell-off'" size="60" color="secondary" class="mb-4" />
        <p class="text-h6 text-medium-emphasis mb-1">
          {{ filter === 'unread' ? 'Aucune notification non lue' : 'Aucune notification' }}
        </p>
        <p class="text-body-2 text-medium-emphasis">
          {{ filter === 'unread' ? 'Vous êtes à jour !' : 'Les notifications apparaîtront ici.' }}
        </p>
        <VBtn v-if="filter === 'unread'" variant="text" class="mt-3" @click="filter = 'all'">Voir toutes</VBtn>
      </VCardText>
    </VCard>

    <VCard v-else>
      <VList lines="two" class="pa-0">
        <template v-for="(notif, index) in filtered" :key="notif.id">
          <VDivider v-if="index > 0" />
          <VListItem :class="{ 'bg-primary-subtle': !notif.is_read }" class="py-4 px-5" style="cursor:pointer" @click="markRead(notif)">
            <template #prepend>
              <VAvatar :color="notifIcon(notif.notification_type || notif.type).color" variant="tonal" size="44" class="me-1">
                <VIcon :icon="notifIcon(notif.notification_type || notif.type).icon" size="22" />
              </VAvatar>
            </template>
            <VListItemTitle class="d-flex align-center justify-space-between mb-1">
              <span :class="notif.is_read ? 'text-body-1' : 'text-body-1 font-weight-bold'">{{ notifTitle(notif) }}</span>
              <div class="d-flex align-center gap-2">
                <span class="text-caption text-medium-emphasis">{{ timeAgo(notif.created_at) }}</span>
                <span v-if="!notif.is_read" style="width:8px;height:8px;border-radius:50%;background:rgb(var(--v-theme-primary));display:inline-block;flex-shrink:0" />
              </div>
            </VListItemTitle>
            <VListItemSubtitle v-if="notifBody(notif)" class="text-body-2 text-medium-emphasis mt-1" style="white-space:normal">
              {{ notifBody(notif) }}
            </VListItemSubtitle>
            <template #append>
              <VBtn v-if="!notif.is_read" icon variant="text" size="x-small" color="primary" @click.stop="markRead(notif)">
                <VIcon icon="tabler-check" size="16" />
              </VBtn>
            </template>
          </VListItem>
        </template>
      </VList>
    </VCard>

    <p class="text-caption text-medium-emphasis text-center mt-4">
      <VIcon icon="tabler-refresh" size="12" class="me-1" />
      Actualisation automatique toutes les 30 secondes
    </p>

    <VSnackbar v-model="snackbar.show" :color="snackbar.color" location="bottom right" timeout="3000">
      {{ snackbar.msg }}
    </VSnackbar>
  </div>
</template>

<style scoped>
.bg-primary-subtle { background-color: rgba(var(--v-theme-primary), 0.05) !important; }
</style>
