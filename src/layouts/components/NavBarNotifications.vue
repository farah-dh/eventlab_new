<script lang="ts" setup>
import type { Notification } from '@layouts/types'

// ── API ──────────────────────────────────────────────────────────
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'
const getToken     = () => localStorage.getItem('access_token') || localStorage.getItem('token')

const apiFetch = async (endpoint: string, options: RequestInit = {}) => {
  const token = getToken()
  const res = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    ...options,
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

// ── STATE ─────────────────────────────────────────────────────────
const notifications = ref<Notification[]>([])
const isLoading     = ref(false)

// ── UNREAD COUNT (badge) ──────────────────────────────────────────
const unreadCount = computed(() =>
  notifications.value.filter(n => !n.isSeen).length
)

// Expose pour le badge dans le layout parent
defineExpose({ unreadCount })

// ── FETCH depuis l'API ────────────────────────────────────────────
const fetchNotifications = async () => {
  isLoading.value = true
  try {
    const data = await apiFetch('/notifications/logs/')
    const list = Array.isArray(data.results || data) ? (data.results || data) : []

    notifications.value = list.map((n: any) => ({
      id:       n.id,
      title:    n.title || n.subject || 'Notification',
      subtitle: n.message || n.body || '',
      time:     formatTime(n.created_at || n.date),
      isSeen:   n.is_read ?? n.isSeen ?? false,
      text:     n.sender_name || '',
      img:      n.image || null,
      color:    n.type === 'error' ? 'error' : n.type === 'success' ? 'success' : 'primary',
    }))
  } catch {
    // Si l'API échoue, garder la liste vide
    notifications.value = []
  } finally {
    isLoading.value = false
  }
}

const formatTime = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now  = new Date()
  const diff = Math.floor((now.getTime() - date.getTime()) / 1000)

  if (diff < 60)     return 'À l\'instant'
  if (diff < 3600)   return `Il y a ${Math.floor(diff / 60)} min`
  if (diff < 86400)  return `Il y a ${Math.floor(diff / 3600)}h`
  if (diff < 172800) return 'Hier'
  return date.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })
}

// ── ACTIONS ───────────────────────────────────────────────────────
const removeNotification = async (notificationId: number) => {
  notifications.value = notifications.value.filter(n => n.id !== notificationId)
}

const markRead = async (notificationIds: number[]) => {
  for (const id of notificationIds) {
    try {
      await apiFetch(`/notifications/logs/${id}/mark_read/`, { method: 'POST' })
    } catch {}
    const n = notifications.value.find(n => n.id === id)
    if (n) n.isSeen = true
  }
}

const markUnRead = (notificationIds: number[]) => {
  notifications.value.forEach(item => {
    if (notificationIds.includes(item.id))
      item.isSeen = false
  })
}

const markAllRead = async () => {
  try {
    await apiFetch('/notifications/logs/mark_all_read/', { method: 'POST' })
    notifications.value.forEach(n => n.isSeen = true)
  } catch {}
}

const handleNotificationClick = (notification: Notification) => {
  if (!notification.isSeen)
    markRead([notification.id])
}

// ── POLLING : rafraîchir toutes les 30s ──────────────────────────
onMounted(() => {
  fetchNotifications()
  const interval = setInterval(fetchNotifications, 30000)
  onUnmounted(() => clearInterval(interval))
})
</script>

<template>
  <div class="notif-wrapper">
    <!-- Badge sur l'icône cloche -->
    <div v-if="isLoading" class="notif-loading">
      <div class="notif-spinner"></div>
    </div>

    <Notifications
      :notifications="notifications"
      @remove="removeNotification"
      @read="markRead"
      @unread="markUnRead"
      @click:notification="handleNotificationClick"
    >
      <!-- Slot pour ajouter "Tout marquer comme lu" -->
      <template #before-list>
        <div v-if="unreadCount > 0" class="notif-header-action">
          <span class="notif-badge">{{ unreadCount }}</span>
          <span class="notif-unread-txt">non lue{{ unreadCount > 1 ? 's' : '' }}</span>
          <button class="notif-mark-all" @click="markAllRead">
            Tout marquer comme lu
          </button>
        </div>
      </template>
    </Notifications>
  </div>
</template>

<style scoped>
.notif-wrapper { position: relative; }

.notif-loading {
  position: absolute;
  top: -4px; right: -4px;
  z-index: 10;
}
.notif-spinner {
  width: 10px; height: 10px;
  border: 2px solid #f5dce5;
  border-top-color: #e8405a;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.notif-header-action {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: #fff5f7;
  border-bottom: 1px solid #f5dce5;
}
.notif-badge {
  background: #e8405a;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 20px;
  min-width: 20px;
  text-align: center;
}
.notif-unread-txt {
  font-size: 12px;
  color: #b08090;
  flex: 1;
}
.notif-mark-all {
  font-size: 11px;
  font-weight: 600;
  color: #e8405a;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.2s;
}
.notif-mark-all:hover { background: #ffd6de; }
</style>