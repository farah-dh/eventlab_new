<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'

definePage({
  meta: { layout: 'organizer' },
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
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

const organizer = computed(() => {
  try { return JSON.parse(localStorage.getItem('organizer') || localStorage.getItem('user') || '{}') }
  catch { return {} }
})

const isLoading = ref(true)
const events    = ref<any[]>([])
const orders    = ref<any[]>([])

// ── Notifications ──────────────────────────────────────────────
const notifications      = ref<any[]>([])
const unreadCount        = ref(0)
const showNotifications  = ref(false)
const isLoadingNotifs    = ref(false)

const fetchNotifications = async () => {
  isLoadingNotifs.value = true
  try {
    const data = await apiFetch('/notifications/logs/')
    notifications.value = data.results || data.data || data || []
    unreadCount.value   = notifications.value.filter((n: any) => !n.is_read).length
  } catch { notifications.value = [] }
  finally { isLoadingNotifs.value = false }
}

const markAllRead = async () => {
  try {
    await apiFetch('/notifications/logs/mark_all_read/', { method: 'POST' })
    notifications.value = notifications.value.map(n => ({ ...n, is_read: true }))
    unreadCount.value = 0
  } catch { }
}

const markOneRead = async (notif: any) => {
  if (notif.is_read) return
  try {
    await apiFetch(`/notifications/logs/${notif.id}/mark_read/`, { method: 'POST' })
    notif.is_read = true
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  } catch { }
}

const notifIcon = (type: string) => {
  if (!type) return 'tabler-bell'
  const t = type.toLowerCase()
  if (t.includes('order') || t.includes('reservation')) return 'tabler-shopping-cart'
  if (t.includes('pay') || t.includes('payment'))       return 'tabler-credit-card'
  if (t.includes('withdraw'))                           return 'tabler-cash'
  if (t.includes('event'))                              return 'tabler-calendar'
  return 'tabler-bell'
}

const notifColor = (type: string) => {
  if (!type) return 'primary'
  const t = type.toLowerCase()
  if (t.includes('order') || t.includes('reservation')) return 'success'
  if (t.includes('pay'))                                 return 'info'
  if (t.includes('withdraw'))                           return 'warning'
  return 'primary'
}

const formatNotifDate = (d: string) => {
  if (!d) return ''
  const date = new Date(d)
  const now  = new Date()
  const diff = Math.floor((now.getTime() - date.getTime()) / 60000)
  if (diff < 1)   return 'À l\'instant'
  if (diff < 60)  return `Il y a ${diff} min`
  if (diff < 1440) return `Il y a ${Math.floor(diff/60)}h`
  return date.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })
}

// ── Fetch principal ────────────────────────────────────────────
const fetchData = async () => {
  isLoading.value = true
  try {
    const [evData, ordData] = await Promise.allSettled([
      apiFetch('/events/'),
      apiFetch('/orders/?limit=200'),
    ])
    if (evData.status === 'fulfilled')
      events.value = evData.value.results || evData.value || []
    if (ordData.status === 'fulfilled') {
      const raw = ordData.value
      orders.value = raw.results || raw.data?.results || raw.data || []
    }
  } catch (e) { console.error(e) }
  finally { isLoading.value = false }
}

// ── Stats événements ───────────────────────────────────────────
const totalEvents    = computed(() => events.value.length)
const activeEvents   = computed(() => events.value.filter(e => e.status === true).length)
const inactiveEvents = computed(() => events.value.filter(e => e.status === false).length)
const soldOutEvents  = computed(() => events.value.filter(e => e.is_sold_out).length)
const totalSeats     = computed(() => events.value.reduce((s, e) => s + (e.seats || 0), 0))
const totalBooked    = computed(() => events.value.reduce((s, e) => s + (e.seats_booked || 0), 0))
const freeEvents     = computed(() => events.value.filter(e => e.type === 2).length)
const paidEvents     = computed(() => events.value.filter(e => e.type === 1).length)

// ✅ Gère status numérique (1 = payé) ET textuel
const isPaid = (o: any) => {
  if (o.payment_status === 1 || o.status === 1) return true
  const s = String(o.payment_status ?? o.status ?? '').toLowerCase()
  return ['paid', 'completed', 'confirmed', 'success', 'approved'].includes(s)
}

const totalRevenue    = computed(() => orders.value.filter(isPaid).reduce((s, o) => s + parseFloat(o.total_price || o.amount || 0), 0))
const paidOrdersCount = computed(() => orders.value.filter(isPaid).length)
const fillRate        = computed(() => totalSeats.value ? Math.round((totalBooked.value / totalSeats.value) * 100) : 0)

const topEvents = computed(() =>
  [...events.value].sort((a, b) => (b.seats_booked || 0) - (a.seats_booked || 0)).slice(0, 5)
)

const upcomingEvents = computed(() => {
  const today = new Date()
  return [...events.value]
    .filter(e => new Date(e.start_date) >= today && e.status)
    .sort((a, b) => new Date(a.start_date).getTime() - new Date(b.start_date).getTime())
    .slice(0, 4)
})

const seatsEvents = computed(() =>
  [...events.value]
    .filter(e => e.seats && e.seats > 0)
    .map(e => ({
      ...e,
      remaining: (e.seats || 0) - (e.seats_booked || 0),
      pct: Math.min(100, Math.round(((e.seats_booked || 0) / (e.seats || 1)) * 100)),
    }))
    .sort((a, b) => a.remaining - b.remaining)
)

// ── Helpers ────────────────────────────────────────────────────
const formatDate    = (d: string) => d ? new Date(d).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' }) : '-'
const formatRevenue = (n: number) => n.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const getInitials   = (name: string) => name?.split(' ').map((w: string) => w[0]).join('').slice(0, 2).toUpperCase() || 'O'
const getTypeLabel  = (t: number) => t === 1 ? 'Payant' : 'Gratuit'
const barWidth      = (booked: number, seats: number) => seats ? Math.min(100, Math.round((booked / seats) * 100)) : 0

const getSeatColor = (pct: number) => pct >= 90 ? '#EF4444' : pct >= 60 ? '#F59E0B' : '#10B981'
const getSeatBg    = (pct: number) => pct >= 90 ? '#FEF2F2' : pct >= 60 ? '#FFFBEB' : '#ECFDF5'

const greeting = computed(() => {
  const h = new Date().getHours()
  return h < 12 ? 'Bonjour' : h < 18 ? 'Bon après-midi' : 'Bonsoir'
})

const donutCircumference = 2 * Math.PI * 48
const paidOffset = computed(() => totalEvents.value
  ? donutCircumference * (1 - paidEvents.value / totalEvents.value)
  : donutCircumference
)

onMounted(async () => {
  await Promise.all([fetchData(), fetchNotifications()])
})
</script>

<template>
  <div class="od">

    <!-- ══ HEADER ══ -->
    <div class="od-header">
      <div class="od-header__glow"></div>
      <div class="od-header__left">
        <div class="od-avatar">{{ getInitials(organizer.organization_name || 'O') }}</div>
        <div>
          <p class="od-greeting">{{ greeting }}, <strong>{{ organizer.firstname || organizer.organization_name || 'Organisateur' }}</strong> 👋</p>
          <p class="od-sub">Voici un aperçu de votre activité sur <strong>EventLab</strong></p>
        </div>
      </div>
      <div class="od-header__right">
        <div class="od-date">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
          {{ new Date().toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }) }}
        </div>
        <div class="od-header-actions">
          <!-- 🔔 Cloche notifications -->
          <button class="od-bell" @click="showNotifications = !showNotifications">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
            <span v-if="unreadCount > 0" class="od-bell__badge">{{ unreadCount > 9 ? '9+' : unreadCount }}</span>
          </button>
          <button class="od-refresh" @click="fetchData(); fetchNotifications()">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M1 4v6h6"/><path d="M23 20v-6h-6"/><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/></svg>
            Actualiser
          </button>
        </div>
      </div>
    </div>

    <!-- ══ PANEL NOTIFICATIONS ══ -->
    <transition name="notif-slide">
      <div v-if="showNotifications" class="od-notif-panel">
        <div class="od-notif-panel__head">
          <div>
            <h3 class="od-notif-panel__title">🔔 Notifications</h3>
            <p class="od-notif-panel__sub">{{ unreadCount }} non lue(s)</p>
          </div>
          <div class="od-notif-panel__actions">
            <button v-if="unreadCount > 0" class="od-notif-panel__btn" @click="markAllRead">Tout marquer lu</button>
            <button class="od-notif-panel__close" @click="showNotifications = false">✕</button>
          </div>
        </div>

        <div v-if="isLoadingNotifs" class="od-notif-panel__loading">
          <div class="od-spinner"></div>
        </div>

        <div v-else-if="notifications.length === 0" class="od-notif-panel__empty">
          <span>🔕</span>
          <p>Aucune notification</p>
        </div>

        <div v-else class="od-notif-list">
          <div
            v-for="notif in notifications"
            :key="notif.id"
            class="od-notif-item"
            :class="{ 'od-notif-item--unread': !notif.is_read }"
            @click="markOneRead(notif)"
          >
            <div class="od-notif-item__icon" :style="`background: var(--${notifColor(notif.type)}-pale, #EEF2FF)`">
              <VIcon :icon="notifIcon(notif.type)" size="16" />
            </div>
            <div class="od-notif-item__body">
              <p class="od-notif-item__title">{{ notif.title || notif.message || 'Notification' }}</p>
              <p v-if="notif.body || notif.description" class="od-notif-item__msg">{{ notif.body || notif.description }}</p>
              <p class="od-notif-item__time">{{ formatNotifDate(notif.created_at) }}</p>
            </div>
            <span v-if="!notif.is_read" class="od-notif-item__dot"></span>
          </div>
        </div>
      </div>
    </transition>

    <!-- ══ LOADING ══ -->
    <div v-if="isLoading" class="od-loading">
      <div class="od-spinner"></div>
      <p>Chargement des données…</p>
    </div>

    <template v-else>

      <!-- ══ KPI CARDS ══ -->
      <div class="od-kpis">
        <div class="od-kpi od-kpi--rose">
          <div class="od-kpi__bg"></div>
          <div class="od-kpi__icon">🎪</div>
          <div class="od-kpi__body">
            <span class="od-kpi__val">{{ totalEvents }}</span>
            <span class="od-kpi__label">Événements créés</span>
            <span class="od-kpi__hint">{{ activeEvents }} actifs · {{ inactiveEvents }} inactifs</span>
          </div>
          <div class="od-kpi__trend">+{{ activeEvents }}</div>
        </div>

        <div class="od-kpi od-kpi--violet">
          <div class="od-kpi__bg"></div>
          <div class="od-kpi__icon">🎫</div>
          <div class="od-kpi__body">
            <span class="od-kpi__val">{{ totalBooked }}</span>
            <span class="od-kpi__label">Billets vendus</span>
            <span class="od-kpi__hint">sur {{ totalSeats }} places</span>
          </div>
          <div class="od-kpi__trend">{{ fillRate }}%</div>
        </div>

        <div class="od-kpi od-kpi--emerald">
          <div class="od-kpi__bg"></div>
          <div class="od-kpi__icon">💰</div>
          <div class="od-kpi__body">
            <span class="od-kpi__val">{{ formatRevenue(totalRevenue) }}</span>
            <span class="od-kpi__label">Revenu total (DT)</span>
            <span class="od-kpi__hint">{{ paidOrdersCount }} commande(s) payée(s)</span>
          </div>
          <div class="od-kpi__trend">DT</div>
        </div>

        <div class="od-kpi od-kpi--amber">
          <div class="od-kpi__bg"></div>
          <div class="od-kpi__icon">📊</div>
          <div class="od-kpi__body">
            <span class="od-kpi__val">{{ fillRate }}%</span>
            <span class="od-kpi__label">Taux de remplissage</span>
            <span class="od-kpi__hint">{{ soldOutEvents }} complet(s)</span>
          </div>
          <div class="od-kpi__trend od-kpi__trend--bar">
            <div class="od-kpi__mini-bar" :style="`width:${fillRate}%`"></div>
          </div>
        </div>
      </div>

      <!-- ══ MAIN GRID ══ -->
      <div class="od-main-grid">

        <!-- PLACES RESTANTES -->
        <div class="od-card od-card--full">
          <div class="od-card__head">
            <div class="od-card__head-left">
              <div class="od-card__icon-wrap">🎟️</div>
              <div>
                <h3 class="od-card__title">Places restantes par événement</h3>
                <p class="od-card__sub">Suivi en temps réel du remplissage</p>
              </div>
              <span class="od-badge">{{ seatsEvents.length }}</span>
            </div>
            <div class="od-legend">
              <span class="od-legend__item"><span class="od-dot od-dot--green"></span>Disponible</span>
              <span class="od-legend__item"><span class="od-dot od-dot--amber"></span>À surveiller</span>
              <span class="od-legend__item"><span class="od-dot od-dot--red"></span>Critique</span>
            </div>
          </div>
          <div v-if="seatsEvents.length === 0" class="od-empty">
            <span class="od-empty__icon">🎟️</span>
            <p>Aucun événement avec des places définies</p>
          </div>
          <div v-else class="od-seats-list">
            <div v-for="ev in seatsEvents" :key="ev.id" class="od-seat-row" :style="`--bar-color: ${getSeatColor(ev.pct)}`">
              <div class="od-seat-row__accent" :style="`background: ${getSeatColor(ev.pct)}`"></div>
              <div class="od-seat-row__info">
                <p class="od-seat-row__title">{{ ev.title }}</p>
                <p class="od-seat-row__date">{{ formatDate(ev.start_date) }}</p>
              </div>
              <div class="od-seat-row__progress">
                <div class="od-progress">
                  <div class="od-progress__fill" :style="`width:${ev.pct}%;background:${getSeatColor(ev.pct)}`"></div>
                </div>
                <span class="od-progress__pct" :style="`color:${getSeatColor(ev.pct)}`">{{ ev.pct }}%</span>
              </div>
              <div class="od-seat-row__nums">
                <div class="od-num" :style="`background:${getSeatBg(ev.pct)};color:${getSeatColor(ev.pct)}`">
                  <span class="od-num__v">{{ ev.remaining }}</span>
                  <span class="od-num__l">restantes</span>
                </div>
                <div class="od-num od-num--gray">
                  <span class="od-num__v">{{ ev.seats_booked || 0 }}</span>
                  <span class="od-num__l">réservées</span>
                </div>
                <div class="od-num od-num--total">
                  <span class="od-num__v">{{ ev.seats }}</span>
                  <span class="od-num__l">total</span>
                </div>
              </div>
              <div class="od-seat-row__status">
                <span v-if="ev.remaining === 0" class="od-pill od-pill--sold">COMPLET</span>
                <span v-else-if="ev.pct >= 90"  class="od-pill od-pill--red">🔥 Critique</span>
                <span v-else-if="ev.pct >= 60"  class="od-pill od-pill--amber">⚠️ À surveiller</span>
                <span v-else                     class="od-pill od-pill--green">✅ Disponible</span>
              </div>
            </div>
          </div>
        </div>

        <!-- RÉPARTITION + PROCHAINS -->
        <div class="od-row2">
          <div class="od-card">
            <div class="od-card__head">
              <div class="od-card__head-left">
                <div class="od-card__icon-wrap">📈</div>
                <h3 class="od-card__title">Répartition</h3>
              </div>
            </div>
            <div class="od-card__body">
              <div class="od-donut-wrap">
                <svg viewBox="0 0 120 120" class="od-donut">
                  <circle cx="60" cy="60" r="48" fill="none" stroke="#F8E4EC" stroke-width="16"/>
                  <circle cx="60" cy="60" r="48" fill="none" stroke="url(#roseGrad)" stroke-width="16"
                    :stroke-dasharray="donutCircumference" :stroke-dashoffset="paidOffset"
                    transform="rotate(-90 60 60)" stroke-linecap="round"/>
                  <defs>
                    <linearGradient id="roseGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stop-color="#FF4D7A"/><stop offset="100%" stop-color="#D4215A"/>
                    </linearGradient>
                  </defs>
                </svg>
                <div class="od-donut__center">
                  <span class="od-donut__val">{{ totalEvents }}</span>
                  <span class="od-donut__sub">total</span>
                </div>
              </div>
              <div class="od-donut-legend">
                <div class="od-dl-item"><span class="od-dl-dot" style="background:linear-gradient(135deg,#FF4D7A,#D4215A)"></span><span class="od-dl-label">Payants</span><span class="od-dl-val">{{ paidEvents }}</span></div>
                <div class="od-dl-item"><span class="od-dl-dot" style="background:#10B981"></span><span class="od-dl-label">Gratuits</span><span class="od-dl-val">{{ freeEvents }}</span></div>
                <div class="od-dl-item"><span class="od-dl-dot" style="background:#F59E0B"></span><span class="od-dl-label">Actifs</span><span class="od-dl-val">{{ activeEvents }}</span></div>
                <div class="od-dl-item"><span class="od-dl-dot" style="background:#9CA3AF"></span><span class="od-dl-label">Inactifs</span><span class="od-dl-val">{{ inactiveEvents }}</span></div>
                <div class="od-dl-item"><span class="od-dl-dot" style="background:#EF4444"></span><span class="od-dl-label">Complets</span><span class="od-dl-val">{{ soldOutEvents }}</span></div>
              </div>
            </div>
          </div>

          <div class="od-card">
            <div class="od-card__head">
              <div class="od-card__head-left">
                <div class="od-card__icon-wrap">📅</div>
                <div>
                  <h3 class="od-card__title">Prochains événements</h3>
                  <p class="od-card__sub">{{ upcomingEvents.length }} à venir</p>
                </div>
              </div>
            </div>
            <div class="od-card__body">
              <div v-if="upcomingEvents.length === 0" class="od-empty">
                <span class="od-empty__icon">📅</span><p>Aucun événement à venir</p>
              </div>
              <div v-else class="od-upcoming">
                <div v-for="ev in upcomingEvents" :key="ev.id" class="od-up-item">
                  <div class="od-up-item__thumb" :style="ev.cover_image ? `background-image:url(${ev.cover_image});background-size:cover;background-position:center` : ''">
                    <span v-if="!ev.cover_image">🎪</span>
                  </div>
                  <div class="od-up-item__info">
                    <p class="od-up-item__title">{{ ev.title }}</p>
                    <p class="od-up-item__meta">{{ formatDate(ev.start_date) }}</p>
                  </div>
                  <div class="od-up-item__right">
                    <span class="od-pill" :class="ev.type === 1 ? 'od-pill--violet' : 'od-pill--green'">{{ getTypeLabel(ev.type) }}</span>
                    <span class="od-up-item__price">{{ ev.price ? `${ev.price} DT` : 'Gratuit' }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- TOP ÉVÉNEMENTS -->
        <div class="od-card od-card--full">
          <div class="od-card__head">
            <div class="od-card__head-left">
              <div class="od-card__icon-wrap">🏆</div>
              <div>
                <h3 class="od-card__title">Top événements par billets vendus</h3>
                <p class="od-card__sub">Classement de performance</p>
              </div>
            </div>
          </div>
          <div class="od-card__body">
            <div v-if="topEvents.length === 0" class="od-empty">
              <span class="od-empty__icon">🏆</span><p>Aucun billet vendu pour le moment</p>
            </div>
            <div v-else class="od-top-list">
              <div v-for="(ev, i) in topEvents" :key="ev.id" class="od-top-item">
                <div class="od-top-item__rank" :class="`od-rank--${i+1}`">
                  <span v-if="i===0">🥇</span><span v-else-if="i===1">🥈</span><span v-else-if="i===2">🥉</span><span v-else>{{ i+1 }}</span>
                </div>
                <div class="od-top-item__info">
                  <div class="od-top-item__titlerow">
                    <span class="od-top-item__title">{{ ev.title }}</span>
                    <span class="od-pill od-pill--sm" :class="ev.type===1?'od-pill--violet':'od-pill--green'">{{ getTypeLabel(ev.type) }}</span>
                  </div>
                  <div class="od-top-item__barwrap">
                    <div class="od-top-bar"><div class="od-top-bar__fill" :style="`width:${barWidth(ev.seats_booked||0,ev.seats||0)}%;background:${ev.type===1?'#D4215A':'#10B981'}`"></div></div>
                    <span class="od-top-bar__pct">{{ barWidth(ev.seats_booked||0,ev.seats||0) }}%</span>
                  </div>
                </div>
                <div class="od-top-item__stats">
                  <span class="od-top-item__booked">{{ ev.seats_booked||0 }} / {{ ev.seats||'∞' }}</span>
                  <span class="od-top-item__revenue">{{ ev.price&&ev.seats_booked ? formatRevenue(parseFloat(ev.price)*ev.seats_booked)+' DT' : '—' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- PROFIL -->
        <div class="od-card od-card--full od-card--profile">
          <div class="od-card__head">
            <div class="od-card__head-left">
              <div class="od-card__icon-wrap">👤</div>
              <div><h3 class="od-card__title">Profil organisateur</h3><p class="od-card__sub">Informations de votre compte</p></div>
            </div>
            <span v-if="organizer.kv===1" class="od-pill od-pill--green">✅ KYC Vérifié</span>
            <span v-else class="od-pill od-pill--amber">⏳ KYC En attente</span>
          </div>
          <div class="od-profile-grid">
            <div class="od-profile-item"><span class="od-profile-label">Organisation</span><span class="od-profile-val">{{ organizer.organization_name||'-' }}</span></div>
            <div class="od-profile-item"><span class="od-profile-label">Nom complet</span><span class="od-profile-val">{{ organizer.full_name||`${organizer.firstname||''} ${organizer.lastname||''}`.trim()||'-' }}</span></div>
            <div class="od-profile-item"><span class="od-profile-label">Email</span><span class="od-profile-val">{{ organizer.email||'-' }}</span></div>
            <div class="od-profile-item"><span class="od-profile-label">Téléphone</span><span class="od-profile-val">{{ organizer.dial_code||'' }} {{ organizer.mobile||'-' }}</span></div>
            <div class="od-profile-item"><span class="od-profile-label">Pays</span><span class="od-profile-val">{{ organizer.country_code||'-' }}</span></div>
            <div class="od-profile-item"><span class="od-profile-label">Solde disponible</span><span class="od-profile-val od-profile-val--rose">{{ parseFloat(organizer.balance||0).toFixed(3) }} DT</span></div>
            <div class="od-profile-item"><span class="od-profile-label">Abonnés</span><span class="od-profile-val">{{ organizer.followers_count||0 }}</span></div>
            <div class="od-profile-item"><span class="od-profile-label">Statut KYC</span><span class="od-profile-val" :style="organizer.kv===1?'color:#10B981;font-weight:700':'color:#F59E0B;font-weight:700'">{{ organizer.kv===1?'✅ Vérifié':'⏳ En attente' }}</span></div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.od {
  --rose:#D4215A;--rose-light:#FF4D7A;--rose-dark:#9B1040;
  --rose-pale:#FFF0F3;--rose-muted:#FCE4EC;
  --violet:#7C3AED;--violet-pale:#EDE9FE;
  --emerald:#059669;--emerald-pale:#ECFDF5;
  --amber:#D97706;--amber-pale:#FFFBEB;
  --text:#111827;--muted:#6B7280;--border:#F3F4F6;--white:#FFFFFF;
  display:flex;flex-direction:column;gap:20px;
  font-family:'Segoe UI',system-ui,sans-serif;color:var(--text);padding-bottom:32px;
  position:relative;
}

/* ══ HEADER ══ */
.od-header{position:relative;background:linear-gradient(135deg,#9B1040 0%,#D4215A 50%,#FF4D7A 100%);border-radius:20px;padding:28px 32px;display:flex;align-items:center;justify-content:space-between;overflow:hidden;box-shadow:0 8px 32px rgba(212,33,90,.3);flex-wrap:wrap;gap:16px;}
.od-header__glow{position:absolute;width:300px;height:300px;border-radius:50%;background:radial-gradient(circle,rgba(255,255,255,.15) 0%,transparent 70%);top:-100px;right:-50px;pointer-events:none;}
.od-header__left{display:flex;align-items:center;gap:16px;position:relative;z-index:1;}
.od-avatar{width:56px;height:56px;border-radius:16px;background:rgba(255,255,255,.2);border:2px solid rgba(255,255,255,.35);backdrop-filter:blur(10px);color:#fff;font-size:20px;font-weight:800;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.od-greeting{font-size:20px;font-weight:300;color:rgba(255,255,255,.9);margin:0 0 4px;}
.od-greeting strong{font-weight:800;}
.od-sub{font-size:13px;color:rgba(255,255,255,.65);margin:0;}
.od-header__right{display:flex;flex-direction:column;align-items:flex-end;gap:10px;position:relative;z-index:1;}
.od-date{display:flex;align-items:center;gap:7px;font-size:12px;color:rgba(255,255,255,.7);text-transform:capitalize;}
.od-header-actions{display:flex;align-items:center;gap:10px;}

/* 🔔 Bell */
.od-bell{position:relative;width:38px;height:38px;border-radius:10px;background:rgba(255,255,255,.18);border:1.5px solid rgba(255,255,255,.3);color:#fff;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .2s;}
.od-bell:hover{background:rgba(255,255,255,.28);}
.od-bell__badge{position:absolute;top:-4px;right:-4px;min-width:18px;height:18px;background:#EF4444;color:#fff;font-size:10px;font-weight:800;border-radius:20px;display:flex;align-items:center;justify-content:center;padding:0 4px;border:2px solid #D4215A;}

.od-refresh{display:inline-flex;align-items:center;gap:7px;padding:8px 16px;background:rgba(255,255,255,.18);border:1.5px solid rgba(255,255,255,.3);border-radius:10px;color:#fff;font-size:13px;font-weight:600;cursor:pointer;backdrop-filter:blur(10px);transition:all .2s;font-family:'Segoe UI',sans-serif;}
.od-refresh:hover{background:rgba(255,255,255,.28);transform:translateY(-1px);}

/* ══ NOTIFICATIONS PANEL ══ */
.od-notif-panel{background:#fff;border:1px solid #EAECF0;border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,.12);overflow:hidden;margin-bottom:4px;}
.od-notif-panel__head{display:flex;align-items:center;justify-content:space-between;padding:16px 20px;border-bottom:1px solid var(--border);}
.od-notif-panel__title{font-size:15px;font-weight:700;color:var(--text);margin:0 0 2px;}
.od-notif-panel__sub{font-size:12px;color:var(--muted);margin:0;}
.od-notif-panel__actions{display:flex;align-items:center;gap:10px;}
.od-notif-panel__btn{font-size:12px;color:var(--rose);font-weight:600;background:none;border:none;cursor:pointer;padding:4px 8px;border-radius:6px;transition:background .15s;}
.od-notif-panel__btn:hover{background:var(--rose-pale);}
.od-notif-panel__close{width:28px;height:28px;border-radius:8px;background:#F3F4F6;border:none;cursor:pointer;font-size:14px;color:var(--muted);display:flex;align-items:center;justify-content:center;}
.od-notif-panel__loading{display:flex;justify-content:center;padding:32px;}
.od-notif-panel__empty{display:flex;flex-direction:column;align-items:center;gap:8px;padding:40px;color:var(--muted);font-size:14px;}
.od-notif-panel__empty span{font-size:36px;}

.od-notif-list{max-height:360px;overflow-y:auto;}
.od-notif-item{display:flex;align-items:flex-start;gap:12px;padding:14px 20px;border-bottom:1px solid var(--border);cursor:pointer;transition:background .15s;position:relative;}
.od-notif-item:last-child{border-bottom:none;}
.od-notif-item:hover{background:#FAFAFA;}
.od-notif-item--unread{background:#FFF8FA;}
.od-notif-item--unread:hover{background:#FFF0F3;}
.od-notif-item__icon{width:36px;height:36px;border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.od-notif-item__body{flex:1;min-width:0;}
.od-notif-item__title{font-size:13px;font-weight:600;color:var(--text);margin:0 0 3px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.od-notif-item__msg{font-size:12px;color:var(--muted);margin:0 0 4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.od-notif-item__time{font-size:11px;color:#9CA3AF;margin:0;}
.od-notif-item__dot{width:8px;height:8px;border-radius:50%;background:var(--rose);flex-shrink:0;margin-top:4px;}

/* Transition */
.notif-slide-enter-active,.notif-slide-leave-active{transition:all .25s ease;}
.notif-slide-enter-from,.notif-slide-leave-to{opacity:0;transform:translateY(-10px);}

/* ══ LOADING ══ */
.od-loading{display:flex;flex-direction:column;align-items:center;gap:14px;padding:80px;color:var(--muted);}
.od-spinner{width:40px;height:40px;border:3px solid var(--rose-muted);border-top-color:var(--rose);border-radius:50%;animation:spin .8s linear infinite;}
@keyframes spin{to{transform:rotate(360deg);}}

/* ══ KPIs ══ */
.od-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;}
.od-kpi{border-radius:18px;padding:22px 20px;display:flex;align-items:flex-start;gap:14px;position:relative;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.06);transition:all .25s;}
.od-kpi:hover{transform:translateY(-3px);box-shadow:0 8px 28px rgba(0,0,0,.12);}
.od-kpi--rose{background:linear-gradient(135deg,#FFF0F3,#FFE4EC);border:1px solid #FECDD3;}
.od-kpi--violet{background:linear-gradient(135deg,#F5F3FF,#EDE9FE);border:1px solid #DDD6FE;}
.od-kpi--emerald{background:linear-gradient(135deg,#F0FDF4,#DCFCE7);border:1px solid #BBF7D0;}
.od-kpi--amber{background:linear-gradient(135deg,#FFFBEB,#FEF3C7);border:1px solid #FDE68A;}
.od-kpi__bg{position:absolute;right:-30px;top:-30px;width:110px;height:110px;border-radius:50%;opacity:.12;}
.od-kpi--rose .od-kpi__bg{background:var(--rose);}
.od-kpi--violet .od-kpi__bg{background:var(--violet);}
.od-kpi--emerald .od-kpi__bg{background:var(--emerald);}
.od-kpi--amber .od-kpi__bg{background:var(--amber);}
.od-kpi__icon{font-size:30px;flex-shrink:0;position:relative;z-index:1;}
.od-kpi__body{display:flex;flex-direction:column;gap:3px;flex:1;min-width:0;position:relative;z-index:1;}
.od-kpi__val{font-size:26px;font-weight:800;color:var(--text);line-height:1.1;}
.od-kpi__label{font-size:12px;font-weight:600;color:#374151;}
.od-kpi__hint{font-size:11px;color:var(--muted);}
.od-kpi__trend{position:absolute;top:14px;right:16px;font-size:12px;font-weight:800;opacity:.45;}
.od-kpi--rose .od-kpi__trend{color:var(--rose);}
.od-kpi--violet .od-kpi__trend{color:var(--violet);}
.od-kpi--emerald .od-kpi__trend{color:var(--emerald);}
.od-kpi--amber .od-kpi__trend{color:var(--amber);}
.od-kpi__trend--bar{top:auto;bottom:14px;right:16px;left:16px;height:4px;background:rgba(0,0,0,.08);border-radius:2px;overflow:hidden;}
.od-kpi__mini-bar{height:100%;background:var(--amber);border-radius:2px;transition:width 1s ease;}

/* ══ GRID & CARDS ══ */
.od-main-grid{display:flex;flex-direction:column;gap:16px;}
.od-card{background:var(--white);border:1px solid #EAECF0;border-radius:18px;overflow:hidden;box-shadow:0 1px 8px rgba(0,0,0,.04);transition:box-shadow .2s;}
.od-card:hover{box-shadow:0 4px 20px rgba(0,0,0,.08);}
.od-card--full{width:100%;}
.od-card--profile{border-top:3px solid var(--rose);}
.od-card__head{display:flex;align-items:center;justify-content:space-between;padding:18px 22px;border-bottom:1px solid var(--border);flex-wrap:wrap;gap:10px;}
.od-card__head-left{display:flex;align-items:center;gap:12px;}
.od-card__icon-wrap{width:38px;height:38px;border-radius:10px;background:var(--rose-pale);display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;}
.od-card__title{font-size:14px;font-weight:700;color:var(--text);margin:0;}
.od-card__sub{font-size:12px;color:var(--muted);margin:2px 0 0;}
.od-card__body{padding:18px 22px;}

.od-badge{background:var(--rose-muted);color:var(--rose);padding:3px 12px;border-radius:20px;font-size:11px;font-weight:700;}
.od-pill{display:inline-flex;align-items:center;gap:4px;padding:4px 12px;border-radius:20px;font-size:11px;font-weight:700;white-space:nowrap;}
.od-pill--sm{padding:2px 8px;font-size:10px;}
.od-pill--green{background:var(--emerald-pale);color:var(--emerald);}
.od-pill--amber{background:var(--amber-pale);color:var(--amber);}
.od-pill--red{background:#FEF2F2;color:#DC2626;}
.od-pill--sold{background:#DC2626;color:#fff;}
.od-pill--violet{background:var(--violet-pale);color:var(--violet);}
.od-pill--rose{background:var(--rose-muted);color:var(--rose);}

.od-legend{display:flex;align-items:center;gap:14px;flex-wrap:wrap;}
.od-legend__item{display:flex;align-items:center;gap:5px;font-size:12px;color:var(--muted);}
.od-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;}
.od-dot--green{background:#10B981;}
.od-dot--amber{background:#F59E0B;}
.od-dot--red{background:#EF4444;}

.od-seats-list{display:flex;flex-direction:column;gap:8px;padding:14px 18px;}
.od-seat-row{display:grid;grid-template-columns:1fr 180px 220px 130px;align-items:center;gap:16px;padding:13px 16px 13px 20px;background:#FAFAFA;border-radius:12px;border:1px solid var(--border);position:relative;overflow:hidden;transition:all .2s;}
.od-seat-row:hover{background:#F8F9FA;box-shadow:0 2px 12px rgba(0,0,0,.06);}
.od-seat-row__accent{position:absolute;left:0;top:0;bottom:0;width:4px;}
.od-seat-row__info{min-width:0;}
.od-seat-row__title{font-size:13px;font-weight:600;color:var(--text);margin:0 0 3px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.od-seat-row__date{font-size:11px;color:var(--muted);margin:0;}
.od-progress{flex:1;height:8px;background:#E5E7EB;border-radius:4px;overflow:hidden;}
.od-progress__fill{height:100%;border-radius:4px;transition:width .8s ease;}
.od-seat-row__progress{display:flex;align-items:center;gap:8px;}
.od-progress__pct{font-size:12px;font-weight:700;width:36px;text-align:right;flex-shrink:0;}
.od-seat-row__nums{display:flex;align-items:center;gap:8px;}
.od-num{display:flex;flex-direction:column;align-items:center;padding:5px 10px;border-radius:8px;min-width:55px;}
.od-num--gray{background:#F3F4F6;color:#6B7280;}
.od-num--total{background:var(--rose-muted);color:var(--rose);}
.od-num__v{font-size:15px;font-weight:800;line-height:1;}
.od-num__l{font-size:9px;font-weight:600;margin-top:2px;text-transform:uppercase;letter-spacing:.6px;}

.od-row2{display:grid;grid-template-columns:300px 1fr;gap:16px;}
.od-donut-wrap{position:relative;width:120px;height:120px;margin:0 auto 20px;}
.od-donut{width:120px;height:120px;}
.od-donut__center{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;}
.od-donut__val{font-size:26px;font-weight:800;color:var(--text);line-height:1;}
.od-donut__sub{font-size:11px;color:var(--muted);}
.od-donut-legend{display:flex;flex-direction:column;gap:9px;}
.od-dl-item{display:flex;align-items:center;gap:8px;}
.od-dl-dot{width:10px;height:10px;border-radius:3px;flex-shrink:0;}
.od-dl-label{font-size:12px;color:var(--muted);flex:1;}
.od-dl-val{font-size:12px;font-weight:700;color:var(--text);}

.od-upcoming{display:flex;flex-direction:column;gap:10px;}
.od-up-item{display:flex;align-items:center;gap:12px;padding:10px 12px;background:#FAFAFA;border-radius:12px;border:1px solid var(--border);transition:all .2s;}
.od-up-item:hover{background:var(--rose-pale);border-color:var(--rose-muted);}
.od-up-item__thumb{width:46px;height:46px;border-radius:10px;flex-shrink:0;background:linear-gradient(135deg,var(--rose-light),var(--rose));display:flex;align-items:center;justify-content:center;font-size:20px;background-size:cover;background-position:center;}
.od-up-item__info{flex:1;min-width:0;}
.od-up-item__title{font-size:13px;font-weight:600;color:var(--text);margin:0 0 2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.od-up-item__meta{font-size:11px;color:var(--muted);margin:0;}
.od-up-item__right{display:flex;flex-direction:column;align-items:flex-end;gap:4px;}
.od-up-item__price{font-size:12px;font-weight:700;color:var(--text);}

.od-top-list{display:flex;flex-direction:column;gap:14px;}
.od-top-item{display:flex;align-items:center;gap:14px;}
.od-top-item__rank{width:32px;height:32px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0;background:#F9FAFB;border:1px solid var(--border);}
.od-rank--1{background:#FEF3C7;border-color:#FDE68A;}
.od-rank--2{background:#F3F4F6;border-color:#E5E7EB;}
.od-rank--3{background:#FEE2E2;border-color:#FECACA;}
.od-top-item__info{flex:1;min-width:0;}
.od-top-item__titlerow{display:flex;align-items:center;gap:8px;margin-bottom:7px;}
.od-top-item__title{font-size:13px;font-weight:600;color:var(--text);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.od-top-item__barwrap{display:flex;align-items:center;gap:8px;}
.od-top-bar{flex:1;height:7px;background:#F3F4F6;border-radius:4px;overflow:hidden;}
.od-top-bar__fill{height:100%;border-radius:4px;transition:width .8s ease;}
.od-top-bar__pct{font-size:11px;color:var(--muted);width:34px;text-align:right;}
.od-top-item__stats{display:flex;flex-direction:column;align-items:flex-end;flex-shrink:0;}
.od-top-item__booked{font-size:13px;font-weight:700;color:var(--text);}
.od-top-item__revenue{font-size:12px;color:var(--emerald);font-weight:600;}

.od-profile-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;padding:18px 22px;}
.od-profile-item{display:flex;flex-direction:column;gap:5px;}
.od-profile-label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;font-weight:600;}
.od-profile-val{font-size:13px;font-weight:600;color:var(--text);}
.od-profile-val--rose{color:var(--rose);font-weight:800;}

.od-empty{display:flex;flex-direction:column;align-items:center;gap:10px;padding:32px;color:var(--muted);text-align:center;}
.od-empty__icon{font-size:40px;}
.od-empty p{font-size:13px;margin:0;}

@media(max-width:1100px){.od-kpis{grid-template-columns:repeat(2,1fr);}.od-row2{grid-template-columns:1fr;}.od-seat-row{grid-template-columns:1fr auto;grid-template-rows:auto auto;gap:10px;}}
@media(max-width:700px){.od-kpis{grid-template-columns:1fr;}.od-header{padding:20px 18px;}.od-profile-grid{grid-template-columns:repeat(2,1fr);}.od-seat-row{grid-template-columns:1fr;}}
</style>