<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
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

const notifications = ref<any[]>([])
const loading       = ref(false)
let   pollInterval  = null as any

const fetchNotifications = async () => {
  loading.value = true
  try {
    const data = await apiFetch('/notifications/logs/')
    const results = data.results || data.data || data || []
    notifications.value = Array.isArray(results) ? results : []
  }
  catch { }
  finally { loading.value = false }
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
  try {
    await apiFetch('/notifications/logs/mark_all_read/', { method: 'POST' })
    notifications.value.forEach(n => (n.is_read = true))
  }
  catch { }
}

const unreadCount  = computed(() => notifications.value.filter(n => !n.is_read).length)
const recentNotifs = computed(() => notifications.value.slice(0, 5))

const notifIcon = (type: string = '') => {
  const t = (type || '').toLowerCase()
  if (t.includes('reserv') || t.includes('ticket')) return { icon: 'tabler-ticket', color: 'primary' }
  if (t.includes('pay') || t.includes('paiement'))  return { icon: 'tabler-cash', color: 'success' }
  if (t.includes('cancel') || t.includes('annul'))  return { icon: 'tabler-x', color: 'error' }
  if (t.includes('withdraw') || t.includes('retrait')) return { icon: 'tabler-arrow-bar-to-down', color: 'warning' }
  return { icon: 'tabler-bell', color: 'secondary' }
}

const timeAgo = (dateStr: string) => {
  if (!dateStr) return ''
  const diff = Date.now() - new Date(dateStr).getTime()
  const min = Math.floor(diff / 60000)
  const hr  = Math.floor(min / 60)
  if (min < 1)  return "À l'instant"
  if (min < 60) return `${min}min`
  if (hr  < 24) return `${hr}h`
  return `${Math.floor(hr / 24)}j`
}

const notifTitle = (n: any) => n.title || n.subject || n.notification_type || 'Notification'
const notifBody  = (n: any) => n.message || n.body || n.content || n.description || ''

onMounted(() => {
  fetchNotifications()
  pollInterval = setInterval(fetchNotifications, 30000)
})
onUnmounted(() => { if (pollInterval) clearInterval(pollInterval) })
</script>

<template>
  <VMenu offset="14" :close-on-content-click="false" max-width="380">
    <template #activator="{ props }">
      <VBtn icon variant="text" v-bind="props">
        <VBadge v-if="unreadCount > 0" :content="unreadCount > 99 ? '99+' : unreadCount" color="error" floating offset-x="2" offset-y="2">
          <VIcon icon="tabler-bell" size="22" />
        </VBadge>
        <VIcon v-else icon="tabler-bell" size="22" />
      </VBtn>
    </template>

    <VCard min-width="340" max-width="380">
      <VCardTitle class="d-flex align-center justify-space-between pa-4 pb-2">
        <div class="d-flex align-center gap-2">
          <VIcon icon="tabler-bell" size="18" color="primary" />
          <span class="text-body-1 font-weight-bold">Notifications</span>
          <VChip v-if="unreadCount > 0" color="primary" size="x-small" variant="tonal">{{ unreadCount }}</VChip>
        </div>
        <VBtn v-if="unreadCount > 0" variant="text" size="x-small" color="primary" @click="markAllRead">Tout lire</VBtn>
      </VCardTitle>

      <VDivider />

      <VCardText v-if="loading" class="d-flex justify-center pa-6">
        <VProgressCircular indeterminate color="primary" size="28" />
      </VCardText>

      <VCardText v-else-if="recentNotifs.length === 0" class="text-center pa-8">
        <VIcon icon="tabler-bell-check" size="36" color="secondary" class="mb-2" />
        <p class="text-body-2 text-medium-emphasis mb-0">Aucune notification</p>
      </VCardText>

      <VList v-else lines="two" class="pa-0" density="compact">
        <template v-for="(notif, i) in recentNotifs" :key="notif.id">
          <VDivider v-if="i > 0" />
          <VListItem :class="{ 'bg-primary-subtle': !notif.is_read }" class="px-4 py-3" style="cursor:pointer" @click="markRead(notif)">
            <template #prepend>
              <VAvatar :color="notifIcon(notif.notification_type || notif.type).color" variant="tonal" size="36" class="me-1">
                <VIcon :icon="notifIcon(notif.notification_type || notif.type).icon" size="18" />
              </VAvatar>
            </template>
            <VListItemTitle>
              <span :class="notif.is_read ? 'text-body-2' : 'text-body-2 font-weight-bold'">{{ notifTitle(notif) }}</span>
            </VListItemTitle>
            <VListItemSubtitle v-if="notifBody(notif)" class="text-caption mt-1" style="white-space:normal;line-height:1.4">
              {{ notifBody(notif).substring(0, 80) }}{{ notifBody(notif).length > 80 ? '…' : '' }}
            </VListItemSubtitle>
            <template #append>
              <div class="d-flex flex-column align-end gap-1">
                <span class="text-caption text-medium-emphasis">{{ timeAgo(notif.created_at) }}</span>
                <span v-if="!notif.is_read" style="width:7px;height:7px;border-radius:50%;background:rgb(var(--v-theme-primary));display:inline-block" />
              </div>
            </template>
          </VListItem>
        </template>
      </VList>

      <VDivider />

      <VCardActions class="pa-3 justify-center">
        <VBtn variant="text" color="primary" size="small" prepend-icon="tabler-list" @click="router.push('/organizer/notifications')">
          Voir toutes les notifications
        </VBtn>
      </VCardActions>
    </VCard>
  </VMenu>
</template>

<style scoped>
.bg-primary-subtle { background-color: rgba(var(--v-theme-primary), 0.06) !important; }
</style>
