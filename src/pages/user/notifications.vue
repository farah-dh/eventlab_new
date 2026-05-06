<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'
const getToken = () => localStorage.getItem('access_token') || localStorage.getItem('token')

const apiFetch = async (endpoint: string, options: RequestInit = {}) => {
  const token = getToken()
  const res = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

// ─── State ───
const isLoading       = ref(true)
const notifications   = ref<any[]>([])
const markingAll      = ref(false)

// ─── Fetch ───
const fetchNotifications = async () => {
  isLoading.value = true
  try {
    const data = await apiFetch('/notifications/logs/')
    const results = data.results || data.data || data || []
    notifications.value = Array.isArray(results) ? results : []
  } catch (err) {
    console.error('Erreur notifications:', err)
    notifications.value = []
  } finally {
    isLoading.value = false
  }
}

// ─── Marquer une notification comme lue ───
const markAsRead = async (notif: any) => {
  if (notif.is_read) return
  try {
    await apiFetch(`/notifications/logs/${notif.id}/mark_read/`, { method: 'POST' })
    notif.is_read = true
  } catch (err) {
    console.error('Erreur mark_read:', err)
  }
}

// ─── Marquer toutes comme lues ───
const markAllAsRead = async () => {
  markingAll.value = true
  try {
    await apiFetch('/notifications/logs/mark_all_read/', { method: 'POST' })
    notifications.value.forEach(n => n.is_read = true)
  } catch (err) {
    console.error('Erreur mark_all_read:', err)
  } finally {
    markingAll.value = false
  }
}

// ─── Computed ───
const unreadCount  = computed(() => notifications.value.filter(n => !n.is_read).length)
const unread       = computed(() => notifications.value.filter(n => !n.is_read))
const read         = computed(() => notifications.value.filter(n => n.is_read))

// ─── Helpers ───
function timeAgo(d: string): string {
  const diff = Math.floor((Date.now() - new Date(d).getTime()) / 1000)
  if (diff < 60)     return "À l'instant"
  if (diff < 3600)   return `Il y a ${Math.floor(diff / 60)} min`
  if (diff < 86400)  return `Il y a ${Math.floor(diff / 3600)}h`
  if (diff < 604800) return `Il y a ${Math.floor(diff / 86400)}j`
  return new Date(d).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })
}

function getNotifIcon(notif: any): string {
  const title = (notif.title || notif.subject || '').toLowerCase()
  if (title.includes('payé') || title.includes('paid') || title.includes('confirm')) return 'tabler-circle-check'
  if (title.includes('annul') || title.includes('cancel'))  return 'tabler-x-circle'
  if (title.includes('billet') || title.includes('ticket')) return 'tabler-ticket'
  if (title.includes('event') || title.includes('événem'))  return 'tabler-calendar-event'
  return 'tabler-bell'
}

function getNotifColor(notif: any): string {
  const title = (notif.title || notif.subject || '').toLowerCase()
  if (title.includes('payé') || title.includes('confirm')) return 'success'
  if (title.includes('annul') || title.includes('cancel')) return 'error'
  return 'primary'
}

onMounted(() => { fetchNotifications() })
</script>

<template>
  <div>
    <!-- Header -->
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h4 class="text-h4 font-weight-bold">Notifications</h4>
        <p class="text-body-1 text-medium-emphasis mt-1">
          {{ unreadCount > 0 ? `${unreadCount} notification(s) non lue(s)` : 'Toutes les notifications sont lues ✅' }}
        </p>
      </div>
      <div class="d-flex gap-3">
        <VBtn
          v-if="unreadCount > 0"
          color="primary"
          variant="tonal"
          prepend-icon="tabler-checks"
          :loading="markingAll"
          @click="markAllAsRead"
        >
          Tout marquer comme lu
        </VBtn>
        <VBtn
          color="primary"
          variant="outlined"
          prepend-icon="tabler-refresh"
          @click="fetchNotifications"
        >
          Actualiser
        </VBtn>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="d-flex flex-column align-center justify-center py-16">
      <VProgressCircular indeterminate color="primary" size="48" />
      <p class="text-body-2 text-medium-emphasis mt-4">Chargement des notifications…</p>
    </div>

    <template v-else>

      <!-- Aucune notification -->
      <VCard v-if="notifications.length === 0" class="text-center py-16">
        <VAvatar color="primary" variant="tonal" size="80" class="mb-4">
          <VIcon icon="tabler-bell-off" size="40" />
        </VAvatar>
        <h5 class="text-h5 font-weight-bold mb-2">Aucune notification</h5>
        <p class="text-body-1 text-medium-emphasis">
          Vous recevrez des notifications lors de vos réservations et paiements.
        </p>
      </VCard>

      <template v-else>

        <!-- ── Non lues ── -->
        <div v-if="unread.length > 0" class="mb-6">
          <div class="d-flex align-center gap-2 mb-3">
            <VIcon icon="tabler-bell-ringing" color="warning" size="20" />
            <h6 class="text-subtitle-1 font-weight-bold">
              Non lues
              <VChip color="error" size="x-small" variant="flat" class="ms-1">{{ unread.length }}</VChip>
            </h6>
          </div>

          <VCard>
            <VList lines="two" class="pa-2">
              <VListItem
                v-for="notif in unread"
                :key="notif.id"
                class="notif-item notif-item--unread rounded-lg mb-1 cursor-pointer"
                @click="markAsRead(notif)"
              >
                <template #prepend>
                  <VAvatar :color="getNotifColor(notif)" variant="tonal" size="44">
                    <VIcon :icon="getNotifIcon(notif)" size="22" />
                  </VAvatar>
                </template>

                <VListItemTitle class="font-weight-bold text-body-2">
                  {{ notif.title || notif.subject || 'Notification' }}
                </VListItemTitle>
                <VListItemSubtitle class="text-caption mt-1">
                  {{ notif.message || notif.body || notif.content || '' }}
                </VListItemSubtitle>

                <template #append>
                  <div class="d-flex flex-column align-end gap-1">
                    <span class="text-caption text-medium-emphasis">{{ timeAgo(notif.created_at) }}</span>
                    <div class="notif-dot"></div>
                  </div>
                </template>
              </VListItem>
            </VList>
          </VCard>
        </div>

        <!-- ── Lues ── -->
        <div v-if="read.length > 0">
          <div class="d-flex align-center gap-2 mb-3">
            <VIcon icon="tabler-bell" color="secondary" size="20" />
            <h6 class="text-subtitle-1 font-weight-bold text-medium-emphasis">
              Déjà lues ({{ read.length }})
            </h6>
          </div>

          <VCard>
            <VList lines="two" class="pa-2">
              <VListItem
                v-for="notif in read"
                :key="notif.id"
                class="notif-item rounded-lg mb-1"
              >
                <template #prepend>
                  <VAvatar color="secondary" variant="tonal" size="44" style="opacity:0.6">
                    <VIcon :icon="getNotifIcon(notif)" size="22" />
                  </VAvatar>
                </template>

                <VListItemTitle class="text-body-2 text-medium-emphasis">
                  {{ notif.title || notif.subject || 'Notification' }}
                </VListItemTitle>
                <VListItemSubtitle class="text-caption mt-1">
                  {{ notif.message || notif.body || notif.content || '' }}
                </VListItemSubtitle>

                <template #append>
                  <span class="text-caption text-disabled">{{ timeAgo(notif.created_at) }}</span>
                </template>
              </VListItem>
            </VList>
          </VCard>
        </div>

      </template>
    </template>
  </div>
</template>

<style scoped>
.notif-item {
  transition: background .15s;
}
.notif-item:hover {
  background: rgba(var(--v-theme-primary), 0.04);
}
.notif-item--unread {
  background: rgba(var(--v-theme-warning), 0.06);
  border-left: 3px solid rgb(var(--v-theme-warning));
}
.notif-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgb(var(--v-theme-error));
}
.cursor-pointer {
  cursor: pointer;
}
</style>