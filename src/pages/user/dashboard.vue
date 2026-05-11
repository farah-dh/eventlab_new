<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useCartStore } from '@/stores/cart'
import type { CartItem } from '@/stores/cart'

// ✅ FIX 1 : layout utilisateur
definePage({
  meta: { layout: 'default' },
})

const router    = useRouter()
const cartStore = useCartStore()

// ✅ FIX 2 : port 8000 au lieu de 8001
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const getToken = () => localStorage.getItem('access_token') || localStorage.getItem('token')

const apiFetch = async (endpoint: string) => {
  const token = getToken()
  const res = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: { 'Content-Type': 'application/json', ...(token && { Authorization: `Bearer ${token}` }) },
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

const isLoading       = ref(true)
const user            = ref<any>({})
const orders          = ref<any[]>([])
const savedEvents     = ref<any[]>([])
const events          = ref<any[]>([])
const notifications   = ref<any[]>([])
const tickets         = ref<any[]>([])
const currentTime     = ref('')
const promoCode       = ref('')
const promoMessage    = ref('')
const promoSuccess    = ref(false)
const discount        = ref(0)
const showClearDialog = ref(false)

const fetchAll = async () => {
  isLoading.value = true
  try {
    try { const d = await apiFetch('/users/me/'); user.value = d.data || d; localStorage.setItem('user', JSON.stringify(user.value)) }
    catch { user.value = JSON.parse(localStorage.getItem('user') || '{}') }
    try { const d = await apiFetch('/orders/'); orders.value = Array.isArray(d.results || d) ? (d.results || d) : [] } catch { orders.value = [] }
    try { const d = await apiFetch('/events/saved/'); savedEvents.value = Array.isArray(d.results || d) ? (d.results || d) : [] } catch { savedEvents.value = [] }
    try { const d = await apiFetch('/events/'); const all = Array.isArray(d.results || d) ? (d.results || d) : []; events.value = all.filter((e: any) => e.status === true).slice(0, 6) } catch { events.value = [] }
    try { const d = await apiFetch('/notifications/logs/'); notifications.value = Array.isArray(d.results || d) ? (d.results || d) : [] } catch { notifications.value = [] }
    try { const d = await apiFetch('/support/tickets/'); tickets.value = Array.isArray(d.results || d) ? (d.results || d) : [] } catch { tickets.value = [] }
  } finally { isLoading.value = false }
}

const userName = computed(() => {
  if (user.value.full_name) return user.value.full_name
  if (user.value.firstname || user.value.lastname) return `${user.value.firstname || ''} ${user.value.lastname || ''}`.trim()
  return user.value.username || 'Utilisateur'
})
const userInitials = computed(() => {
  const p = userName.value.split(' ')
  return p.length >= 2 ? (p[0][0] + p[1][0]).toUpperCase() : userName.value[0]?.toUpperCase() || 'U'
})
const greeting = computed(() => {
  const h = new Date().getHours()
  return h < 12 ? 'Bonjour' : h < 18 ? 'Bon après-midi' : 'Bonsoir'
})
const totalOrders         = computed(() => orders.value.length)
const pendingOrders       = computed(() => orders.value.filter((o: any) => o.status === 'pending').length)
const totalSaved          = computed(() => savedEvents.value.length)
const unreadNotifications = computed(() => notifications.value.filter((n: any) => !n.is_read).length)
const openTickets         = computed(() => tickets.value.filter((t: any) => t.status !== 'closed').length)
const totalSpent          = computed(() => orders.value.reduce((s, o) => s + Number(o.total_price || o.total_amount || o.amount || 0), 0))
const recentOrders        = computed(() => orders.value.slice(0, 5))
const upcomingEvents      = computed(() => events.value.slice(0, 5))

const cartItems    = computed((): CartItem[] => cartStore.items)
const cartCount    = computed(() => cartStore.totalItems)
const cartSubtotal = computed(() => cartStore.totalPrice)
const cartTotal    = computed(() => Math.max(0, cartSubtotal.value - discount.value))

const removeItem  = (id: number)     => cartStore.removeItem(id)
const increaseQty = (item: CartItem) => cartStore.increment(item.id)
const decreaseQty = (item: CartItem) => cartStore.decrement(item.id)
const clearCart   = ()               => { cartStore.clearCart(); showClearDialog.value = false }

const applyPromo = () => {
  const code = promoCode.value.trim().toUpperCase()
  if (code === 'EVENTLAB10')   { discount.value = cartSubtotal.value * 0.1; promoSuccess.value = true; promoMessage.value = '🎉 -10% appliqué !' }
  else if (code === 'WELCOME') { discount.value = 5; promoSuccess.value = true; promoMessage.value = '🎉 -5 DT appliqué !' }
  else                         { discount.value = 0; promoSuccess.value = false; promoMessage.value = '❌ Code invalide' }
}

const quickActions = [
  { title: 'Explorer',     icon: 'tabler-calendar-event', color: '#E91E8C', bg: '#fce4ec', to: '/user/events' },
  { title: 'Réservations', icon: 'tabler-ticket',         color: '#4CAF50', bg: '#e8f5e9', to: '/user/orders' },
  { title: 'Sauvegardés',  icon: 'tabler-heart',          color: '#FF5722', bg: '#fbe9e7', to: '/user/saved' },
  { title: 'Support',      icon: 'tabler-headset',        color: '#2196F3', bg: '#e3f2fd', to: '/user/support' },
]

const kpis = computed(() => [
  { label: 'Réservations',  value: totalOrders.value,                   icon: 'tabler-ticket',  color: '#E91E8C', bg: 'rgba(233,30,140,0.08)', sub: pendingOrders.value > 0 ? `${pendingOrders.value} en attente` : 'Aucune en attente' },
  { label: 'Sauvegardés',   value: totalSaved.value,                    icon: 'tabler-heart',   color: '#FF5722', bg: 'rgba(255,87,34,0.08)',  sub: 'Événements favoris' },
  { label: 'Notifications', value: unreadNotifications.value,           icon: 'tabler-bell',    color: '#FF9800', bg: 'rgba(255,152,0,0.08)',  sub: unreadNotifications.value > 0 ? 'Non lues' : 'Tout lu' },
  { label: 'Dépensé',       value: `${totalSpent.value.toFixed(0)} DT`, icon: 'tabler-wallet',  color: '#4CAF50', bg: 'rgba(76,175,80,0.08)',  sub: 'Total cumulé' },
])

function formatDate(d: string | null) {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })
}
function formatPrice(p: any) {
  return (p === null || p === undefined) ? 'Gratuit' : `${Number(p).toFixed(3)} DT`
}
function getOrderStatus(status: any) {
  const c: Record<string, any> = {
    '0':         { label: 'En attente', color: 'warning', icon: 'tabler-clock' },
    '1':         { label: 'Payée ✅',   color: 'success', icon: 'tabler-check' },
    '2':         { label: 'Échouée',    color: 'error',   icon: 'tabler-x' },
    '3':         { label: 'Remboursée', color: 'info',    icon: 'tabler-refresh' },
    'pending':   { label: 'En attente', color: 'warning', icon: 'tabler-clock' },
    'paid':      { label: 'Payée ✅',   color: 'success', icon: 'tabler-check' },
    'confirmed': { label: 'Confirmée',  color: 'success', icon: 'tabler-circle-check' },
    'cancelled': { label: 'Annulée',    color: 'error',   icon: 'tabler-x' },
  }
  return c[String(status)] || { label: 'Inconnu', color: 'default', icon: 'tabler-help' }
}
function timeAgo(d: string) {
  const diff = Math.floor((Date.now() - new Date(d).getTime()) / 1000)
  if (diff < 60) return "À l'instant"
  if (diff < 3600) return `Il y a ${Math.floor(diff / 60)} min`
  if (diff < 86400) return `Il y a ${Math.floor(diff / 3600)}h`
  return `Il y a ${Math.floor(diff / 86400)}j`
}
const updateTime = () => {
  currentTime.value = new Date().toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
}
onMounted(() => { fetchAll(); updateTime(); setInterval(updateTime, 60000) })
</script>

<template>
  <div class="db-root">

    <div v-if="isLoading" class="db-loading">
      <div class="db-loading__spinner"></div>
      <p>Chargement de votre espace…</p>
    </div>

    <template v-else>

      <!-- HERO -->
      <div class="db-hero">
        <div class="db-hero__glow g1"></div>
        <div class="db-hero__glow g2"></div>
        <div class="db-hero__left">
          <div class="db-hero__avatar">{{ userInitials }}</div>
          <div>
            <p class="db-hero__greeting">{{ greeting }}, <strong>{{ userName }}</strong> 👋</p>
            <p class="db-hero__date">{{ currentTime }}</p>
            <p class="db-hero__sub">Bienvenue sur votre espace EventLab. Explorez et gérez vos réservations.</p>
          </div>
        </div>
        <div class="db-hero__right">
          <button class="db-hero__btn db-hero__btn--solid" @click="router.push('/user/events')">
            <VIcon icon="tabler-calendar-event" size="15" /> Explorer
          </button>
          <button class="db-hero__btn db-hero__btn--outline" @click="router.push('/user/profile')">
            <VIcon icon="tabler-user" size="15" /> Mon profil
          </button>
        </div>
      </div>

      <!-- ALERTE PANIER -->
      <div v-if="cartCount > 0" class="db-cart-alert">
        <div class="db-cart-alert__left">
          <div class="db-cart-alert__icon">🛒</div>
          <div>
            <strong>{{ cartCount }} article{{ cartCount > 1 ? 's' : '' }} dans votre panier</strong>
            <span>Total estimé : {{ cartTotal.toFixed(2) }} DT — Finalisez avant expiration !</span>
          </div>
        </div>
        <button class="db-cart-alert__btn" @click="router.push('/checkout')">
          <VIcon icon="tabler-lock" size="14" /> Passer au paiement
        </button>
      </div>

      <!-- KPIs -->
      <div class="db-kpis">
        <div v-for="kpi in kpis" :key="kpi.label" class="db-kpi" :style="`--kpi-color:${kpi.color};--kpi-bg:${kpi.bg}`">
          <div class="db-kpi__icon"><VIcon :icon="kpi.icon" size="22" :style="`color:${kpi.color}`" /></div>
          <div class="db-kpi__body">
            <span class="db-kpi__value">{{ kpi.value }}</span>
            <span class="db-kpi__label">{{ kpi.label }}</span>
            <span class="db-kpi__sub">{{ kpi.sub }}</span>
          </div>
          <div class="db-kpi__bar"></div>
        </div>
      </div>

      <!-- QUICK ACTIONS -->
      <div class="db-section-title"><VIcon icon="tabler-bolt" size="18" color="#FF9800" /> Actions rapides</div>
      <div class="db-actions">
        <div v-for="a in quickActions" :key="a.title" class="db-action" :style="`--ac:${a.color};--abg:${a.bg}`" @click="router.push(a.to)">
          <div class="db-action__icon"><VIcon :icon="a.icon" size="26" :style="`color:${a.color}`" /></div>
          <span class="db-action__label">{{ a.title }}</span>
        </div>
      </div>

      <!-- MON PANIER -->
      <div id="cart-section" class="db-card db-card--cart">
        <div class="db-card__header">
          <div class="db-card__header-left">
            <VIcon icon="tabler-shopping-cart" size="20" color="#E91E8C" />
            <span>Mon panier</span>
            <span v-if="cartCount > 0" class="db-badge db-badge--pink">{{ cartCount }}</span>
          </div>
          <button v-if="cartItems.length > 0" class="db-btn-ghost db-btn-ghost--danger" @click="showClearDialog = true">
            <VIcon icon="tabler-trash" size="15" /> Vider
          </button>
        </div>

        <div v-if="cartItems.length === 0" class="db-empty">
          <div class="db-empty__icon">🛒</div>
          <h3>Votre panier est vide</h3>
          <p>Parcourez les événements et ajoutez vos favoris !</p>
          <button class="db-btn-primary" @click="router.push('/user/events')">
            <VIcon icon="tabler-calendar-event" size="15" /> Découvrir les événements
          </button>
        </div>

        <div v-else class="db-cart-layout">
          <div class="db-cart-items">
            <div v-for="item in cartItems" :key="item.id" class="db-cart-item">
              <div class="db-cart-item__thumb">
                <img v-if="item.image" :src="item.image" :alt="item.title" />
                <VIcon v-else icon="tabler-calendar-event" size="28" color="#E91E8C" />
              </div>
              <div class="db-cart-item__body">
                <div class="db-cart-item__top">
                  <h4 class="db-cart-item__name">{{ item.title }}</h4>
                  <button class="db-remove-btn" @click="removeItem(item.id)">
                    <VIcon icon="tabler-x" size="14" />
                  </button>
                </div>
                <div class="db-cart-item__chips">
                  <span class="db-chip db-chip--date">
                    <VIcon icon="tabler-calendar" size="11" />
                    {{ item.date ? new Date(item.date).toLocaleDateString('fr-FR') : 'Date TBD' }}
                  </span>
                  <span class="db-chip db-chip--loc">
                    <VIcon icon="tabler-map-pin" size="11" />
                    {{ item.location || 'Lieu TBD' }}
                  </span>
                  <span v-if="item.category" class="db-chip db-chip--ticket">
                    <VIcon icon="tabler-tag" size="11" />
                    {{ item.category }}
                  </span>
                </div>
                <div class="db-cart-item__footer">
                  <div class="db-qty">
                    <button class="db-qty__btn" :disabled="item.quantity <= 1" @click="decreaseQty(item)">−</button>
                    <span class="db-qty__val">{{ item.quantity }}</span>
                    <button class="db-qty__btn" @click="increaseQty(item)">+</button>
                    <span class="db-qty__unit">billet{{ item.quantity > 1 ? 's' : '' }}</span>
                  </div>
                  <div class="db-cart-item__price">
                    <span>{{ Number(item.price).toFixed(2) }} DT × {{ item.quantity }}</span>
                    <strong>{{ (item.price * item.quantity).toFixed(2) }} DT</strong>
                  </div>
                </div>
              </div>
            </div>
            <button class="db-btn-ghost" @click="router.push('/user/events')">
              <VIcon icon="tabler-arrow-left" size="14" /> Continuer mes achats
            </button>
          </div>

          <div class="db-cart-recap">
            <h4 class="db-cart-recap__title">Récapitulatif</h4>
            <div class="db-recap-lines">
              <div v-for="item in cartItems" :key="item.id" class="db-recap-line">
                <span class="db-recap-line__name">{{ item.title }} × {{ item.quantity }}</span>
                <span class="db-recap-line__price">{{ (item.price * item.quantity).toFixed(2) }} DT</span>
              </div>
            </div>
            <div class="db-recap-divider"></div>
            <div class="db-recap-row"><span>Sous-total</span><span>{{ cartSubtotal.toFixed(2) }} DT</span></div>
            <div class="db-recap-row db-recap-row--free"><span>Frais de service</span><span class="db-free-tag">🎁 Offerts</span></div>
            <div class="db-promo">
              <input v-model="promoCode" placeholder="Code promo" class="db-promo__input" @keyup.enter="applyPromo" />
              <button class="db-promo__btn" @click="applyPromo">OK</button>
            </div>
            <p v-if="promoMessage" class="db-promo__msg" :class="promoSuccess ? 'db-promo__msg--ok' : 'db-promo__msg--err'">{{ promoMessage }}</p>
            <div class="db-recap-divider"></div>
            <div class="db-recap-total"><span>Total</span><strong>{{ cartTotal.toFixed(2) }} DT</strong></div>
            <button class="db-checkout-btn" @click="router.push('/checkout')">
              <VIcon icon="tabler-lock" size="17" /> Passer au paiement <VIcon icon="tabler-arrow-right" size="15" />
            </button>
            <div class="db-security"><span>🔒 SSL</span><span>✅ 3D Secure</span><span>🛡️ PCI DSS</span></div>
            <div class="db-cart-infos">
              <p>🎟️ Billets électroniques par e-mail</p>
              <p>🔄 Annulation jusqu'à 48h avant</p>
              <p>💬 Support disponible 7j/7</p>
            </div>
          </div>
        </div>
      </div>

      <!-- MAIN GRID -->
      <div class="db-main-grid">
        <div class="db-card">
          <div class="db-card__header">
            <div class="db-card__header-left">
              <VIcon icon="tabler-ticket" size="20" color="#E91E8C" />
              <span>Mes réservations récentes</span>
            </div>
            <a v-if="orders.length > 0" class="db-link" @click="router.push('/user/orders')">
              Voir tout <VIcon icon="tabler-arrow-right" size="14" />
            </a>
          </div>
          <div v-if="recentOrders.length === 0" class="db-empty db-empty--sm">
            <div class="db-empty__icon">🎟️</div>
            <h3>Aucune réservation</h3>
            <p>Explorez et réservez vos premiers billets !</p>
            <button class="db-btn-primary" @click="router.push('/user/events')">
              <VIcon icon="tabler-calendar-event" size="14" /> Découvrir
            </button>
          </div>
          <div v-else class="db-orders-list">
            <div v-for="order in recentOrders" :key="order.id" class="db-order-row">
              <div class="db-order-row__event">
                <div class="db-order-row__icon"><VIcon icon="tabler-calendar-event" size="18" color="#E91E8C" /></div>
                <div>
                  <p class="db-order-row__title">{{ order.event_title || order.event?.title || '-' }}</p>
                  <p class="db-order-row__ref">Réf: #{{ order.id }}</p>
                </div>
              </div>
              <p class="db-order-row__date">{{ formatDate(order.created_at) }}</p>
              <p class="db-order-row__amount">{{ formatPrice(order.total_price || order.total_amount || order.amount) }}</p>
              <span class="db-status" :class="`db-status--${getOrderStatus(order.payment_status ?? order.status).color}`">
                <VIcon :icon="getOrderStatus(order.payment_status ?? order.status).icon" size="12" />
                {{ getOrderStatus(order.payment_status ?? order.status).label }}
              </span>
            </div>
          </div>
        </div>

        <div class="db-sidebar">
          <!-- Profil -->
          <div class="db-card db-card--profile">
            <div class="db-profile">
              <div class="db-profile__avatar">{{ userInitials }}</div>
              <h3 class="db-profile__name">{{ userName }}</h3>
              <p class="db-profile__email">{{ user.email }}</p>
              <span class="db-profile__badge" :class="user.ev ? 'db-profile__badge--ok' : 'db-profile__badge--warn'">
                <VIcon :icon="user.ev ? 'tabler-mail-check' : 'tabler-mail-x'" size="12" />
                {{ user.ev ? 'Email vérifié' : 'Non vérifié' }}
              </span>
            </div>
            <div class="db-profile__stats">
              <div class="db-profile__stat"><strong>{{ totalOrders }}</strong><span>Réservations</span></div>
              <div class="db-profile__divider"></div>
              <div class="db-profile__stat"><strong>{{ totalSaved }}</strong><span>Sauvegardés</span></div>
              <div class="db-profile__divider"></div>
              <div class="db-profile__stat"><strong>{{ Number(user.balance || 0).toFixed(0) }}</strong><span>DT Solde</span></div>
            </div>
          </div>

          <!-- Événements populaires -->
          <div class="db-card">
            <div class="db-card__header">
              <div class="db-card__header-left">
                <VIcon icon="tabler-flame" size="18" color="#FF5722" /><span>Événements populaires</span>
              </div>
            </div>
            <div v-if="upcomingEvents.length === 0" class="db-empty db-empty--xs">
              <VIcon icon="tabler-calendar-off" size="28" color="#ccc" /><p>Aucun événement disponible</p>
            </div>
            <div v-else class="db-event-list">
              <div v-for="event in upcomingEvents" :key="event.id" class="db-event-item" @click="router.push(`/user/events/${event.id}`)">
                <div class="db-event-item__icon" :class="event.is_featured ? 'db-event-item__icon--gold' : ''">
                  <VIcon :icon="event.is_featured ? 'tabler-star' : 'tabler-calendar'" size="16" />
                </div>
                <div class="db-event-item__body">
                  <p class="db-event-item__title">{{ event.title }}</p>
                  <p class="db-event-item__meta">{{ formatDate(event.start_date) }}<span v-if="event.location_name"> · {{ event.location_name }}</span></p>
                </div>
                <span class="db-price-tag" :class="event.price ? 'db-price-tag--paid' : 'db-price-tag--free'">
                  {{ event.price ? `${Number(event.price).toFixed(0)} DT` : 'Gratuit' }}
                </span>
              </div>
            </div>
          </div>

          <!-- Notifications -->
          <div class="db-card">
            <div class="db-card__header">
              <div class="db-card__header-left">
                <VIcon icon="tabler-bell-ringing" size="18" color="#FF9800" /><span>Notifications</span>
              </div>
              <span v-if="unreadNotifications > 0" class="db-badge db-badge--red">{{ unreadNotifications }}</span>
            </div>
            <div v-if="notifications.length === 0" class="db-empty db-empty--xs">
              <VIcon icon="tabler-bell-off" size="28" color="#ccc" /><p>Aucune notification</p>
            </div>
            <div v-else class="db-notif-list">
              <div v-for="n in notifications.slice(0, 4)" :key="n.id" class="db-notif-item" :class="{ 'db-notif-item--unread': !n.is_read }">
                <div class="db-notif-item__dot" :class="{ 'db-notif-item__dot--active': !n.is_read }"></div>
                <div class="db-notif-item__body">
                  <p class="db-notif-item__title">{{ n.title || n.subject || 'Notification' }}</p>
                  <p class="db-notif-item__time">{{ timeAgo(n.created_at) }}</p>
                </div>
              </div>
            </div>
            <a v-if="notifications.length > 0" class="db-link db-link--center" @click="router.push('/user/notifications')">
              Voir toutes les notifications
            </a>
          </div>

          <!-- Support -->
          <div class="db-card db-card--support">
            <div class="db-support">
              <div class="db-support__icon">🎧</div>
              <div>
                <h4>Besoin d'aide ?</h4>
                <p>{{ openTickets > 0 ? `${openTickets} ticket(s) ouvert(s)` : 'Notre équipe est disponible' }}</p>
              </div>
            </div>
            <button class="db-btn-support" @click="router.push('/user/support')">
              <VIcon icon="tabler-message-plus" size="15" /> Contacter le support
            </button>
          </div>
        </div>
      </div>
    </template>

    <VDialog v-model="showClearDialog" max-width="360">
      <VCard style="border-radius:20px;padding:8px">
        <VCardTitle class="pa-6 pb-2" style="font-size:17px;font-weight:700">Vider le panier ?</VCardTitle>
        <VCardText class="px-6 pb-2 text-body-2" style="color:#7c6070">Cette action supprimera tous les articles de votre panier.</VCardText>
        <VCardActions class="pa-6 pt-2 gap-2">
          <VSpacer />
          <VBtn variant="text" @click="showClearDialog = false">Annuler</VBtn>
          <VBtn color="error" variant="flat" style="border-radius:10px" @click="clearCart">Confirmer</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </div>
</template>

<style scoped>
.db-root{--pink:#E91E8C;--pink-dark:#AD1457;--pink-pale:#fdf0f6;--pink-light:#fce4ec;--text:#1a0a14;--muted:#7c6070;--border:#f0e0ea;--white:#ffffff;--radius:18px;font-family:'Segoe UI',system-ui,sans-serif;color:var(--text);padding-bottom:40px}
.db-loading{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:50vh;gap:16px;color:var(--muted)}
.db-loading__spinner{width:44px;height:44px;border:3px solid var(--pink-light);border-top-color:var(--pink);border-radius:50%;animation:spin .8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.db-hero{position:relative;background:linear-gradient(135deg,#880E4F 0%,#AD1457 45%,#E91E8C 100%);border-radius:var(--radius);padding:32px 36px;display:flex;align-items:center;justify-content:space-between;overflow:hidden;margin-bottom:20px;box-shadow:0 8px 32px rgba(233,30,140,.3)}
.db-hero__glow{position:absolute;border-radius:50%;filter:blur(80px);pointer-events:none}
.db-hero__glow.g1{width:300px;height:300px;background:rgba(255,180,220,.3);top:-120px;right:80px}
.db-hero__glow.g2{width:200px;height:200px;background:rgba(255,100,180,.2);bottom:-80px;left:200px}
.db-hero__left{display:flex;align-items:center;gap:20px;position:relative;z-index:1}
.db-hero__avatar{width:60px;height:60px;background:rgba(255,255,255,.2);border:2px solid rgba(255,255,255,.4);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:800;color:#fff;flex-shrink:0;backdrop-filter:blur(10px)}
.db-hero__greeting{font-size:22px;font-weight:300;color:rgba(255,255,255,.9);margin:0 0 2px}
.db-hero__greeting strong{font-weight:800}
.db-hero__date{font-size:12px;color:rgba(255,255,255,.65);margin:0 0 6px;text-transform:capitalize}
.db-hero__sub{font-size:13px;color:rgba(255,255,255,.7);margin:0;max-width:500px}
.db-hero__right{display:flex;gap:10px;position:relative;z-index:1;flex-shrink:0}
.db-hero__btn{display:inline-flex;align-items:center;gap:7px;padding:10px 18px;border-radius:12px;font-size:13px;font-weight:700;cursor:pointer;transition:all .2s;border:none}
.db-hero__btn--solid{background:#fff;color:var(--pink-dark)}
.db-hero__btn--solid:hover{background:rgba(255,255,255,.9);transform:translateY(-2px)}
.db-hero__btn--outline{background:rgba(255,255,255,.12);color:#fff;border:1.5px solid rgba(255,255,255,.3)!important;backdrop-filter:blur(8px)}
.db-hero__btn--outline:hover{background:rgba(255,255,255,.2);transform:translateY(-2px)}
.db-cart-alert{display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,#fff8e1,#fff3e0);border:1.5px solid #ffe082;border-radius:14px;padding:14px 20px;margin-bottom:20px;gap:16px;transition:all .2s}
.db-cart-alert:hover{box-shadow:0 4px 18px rgba(255,215,0,.2);transform:translateY(-1px)}
.db-cart-alert__left{display:flex;align-items:center;gap:14px}
.db-cart-alert__icon{font-size:26px}
.db-cart-alert__left strong{display:block;font-size:14px;color:var(--text)}
.db-cart-alert__left span{font-size:12px;color:var(--muted)}
.db-cart-alert__btn{display:inline-flex;align-items:center;gap:6px;background:#FF9800;color:#fff;border:none;border-radius:10px;padding:9px 16px;font-size:13px;font-weight:700;cursor:pointer;white-space:nowrap;transition:all .2s}
.db-cart-alert__btn:hover{background:#F57C00;transform:translateY(-1px)}
.db-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px}
.db-kpi{background:var(--white);border:1px solid var(--border);border-radius:var(--radius);padding:20px;display:flex;align-items:center;gap:14px;position:relative;overflow:hidden;transition:all .2s;box-shadow:0 2px 10px rgba(0,0,0,.04)}
.db-kpi:hover{transform:translateY(-3px);box-shadow:0 6px 24px rgba(0,0,0,.08)}
.db-kpi__icon{width:48px;height:48px;background:var(--kpi-bg);border-radius:14px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.db-kpi__body{display:flex;flex-direction:column;gap:2px;flex:1;min-width:0}
.db-kpi__value{font-size:22px;font-weight:800;color:var(--text);line-height:1}
.db-kpi__label{font-size:12px;font-weight:600;color:var(--muted)}
.db-kpi__sub{font-size:11px;color:#b0a0aa}
.db-kpi__bar{position:absolute;bottom:0;left:0;right:0;height:3px;background:var(--kpi-color);opacity:0;transition:opacity .2s}
.db-kpi:hover .db-kpi__bar{opacity:1}
.db-section-title{display:flex;align-items:center;gap:8px;font-size:14px;font-weight:700;color:var(--text);margin:4px 0 12px}
.db-actions{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px}
.db-action{background:var(--white);border:1.5px solid var(--border);border-radius:var(--radius);padding:18px 12px;text-align:center;cursor:pointer;transition:all .2s;box-shadow:0 2px 8px rgba(0,0,0,.03)}
.db-action:hover{border-color:var(--ac);background:var(--abg);transform:translateY(-3px);box-shadow:0 6px 20px rgba(0,0,0,.08)}
.db-action__icon{width:48px;height:48px;background:var(--abg);border-radius:14px;display:flex;align-items:center;justify-content:center;margin:0 auto 10px;transition:background .2s}
.db-action:hover .db-action__icon{background:rgba(255,255,255,.8)}
.db-action__label{font-size:12px;font-weight:600;color:var(--text)}
.db-card{background:var(--white);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;box-shadow:0 2px 12px rgba(233,30,140,.05);margin-bottom:16px}
.db-card__header{display:flex;align-items:center;justify-content:space-between;padding:18px 22px;border-bottom:1px solid var(--border)}
.db-card__header-left{display:flex;align-items:center;gap:8px;font-size:15px;font-weight:700;color:var(--text)}
.db-cart-layout{display:grid;grid-template-columns:1fr 300px;gap:0}
.db-cart-items{padding:16px 20px;display:flex;flex-direction:column;gap:12px;border-right:1px solid var(--border)}
.db-cart-item{display:flex;gap:14px;background:#fdf5f9;border:1px solid var(--border);border-radius:14px;overflow:hidden;transition:all .2s}
.db-cart-item:hover{border-color:var(--pink);box-shadow:0 3px 14px rgba(233,30,140,.1)}
.db-cart-item__thumb{width:90px;flex-shrink:0;background:var(--pink-light);display:flex;align-items:center;justify-content:center;min-height:100px}
.db-cart-item__thumb img{width:100%;height:100%;object-fit:cover}
.db-cart-item__body{flex:1;padding:12px 14px 12px 0;display:flex;flex-direction:column;gap:8px}
.db-cart-item__top{display:flex;align-items:flex-start;justify-content:space-between;gap:8px}
.db-cart-item__name{font-size:14px;font-weight:700;color:var(--text);margin:0;flex:1}
.db-remove-btn{width:24px;height:24px;background:none;border:1px solid var(--border);border-radius:6px;cursor:pointer;color:var(--muted);display:flex;align-items:center;justify-content:center;transition:all .15s;flex-shrink:0}
.db-remove-btn:hover{background:#fee2e2;border-color:#ef4444;color:#ef4444}
.db-cart-item__chips{display:flex;flex-wrap:wrap;gap:6px}
.db-chip{display:inline-flex;align-items:center;gap:4px;padding:3px 8px;border-radius:20px;font-size:10px;font-weight:500;border:1px solid transparent}
.db-chip--date{background:#e3f2fd;color:#1565c0;border-color:#bbdefb}
.db-chip--loc{background:#fce4ec;color:#c2185b;border-color:#f8bbd0}
.db-chip--ticket{background:#fff8e1;color:#f57f17;border-color:#ffe082}
.db-cart-item__footer{display:flex;align-items:center;justify-content:space-between;gap:12px}
.db-qty{display:flex;align-items:center;gap:6px}
.db-qty__btn{width:26px;height:26px;background:var(--white);border:1.5px solid var(--border);border-radius:7px;cursor:pointer;font-size:15px;font-weight:700;display:flex;align-items:center;justify-content:center;transition:all .15s}
.db-qty__btn:hover:not(:disabled){background:var(--pink);color:#fff;border-color:var(--pink)}
.db-qty__btn:disabled{opacity:.35;cursor:not-allowed}
.db-qty__val{font-size:15px;font-weight:800;min-width:24px;text-align:center}
.db-qty__unit{font-size:11px;color:var(--muted)}
.db-cart-item__price{text-align:right}
.db-cart-item__price span{display:block;font-size:11px;color:var(--muted)}
.db-cart-item__price strong{font-size:16px;font-weight:800;color:var(--pink)}
.db-cart-recap{padding:20px;background:#fdf5f9;display:flex;flex-direction:column;gap:10px}
.db-cart-recap__title{font-size:15px;font-weight:700;color:var(--text);margin:0 0 4px}
.db-recap-lines{display:flex;flex-direction:column;gap:6px}
.db-recap-line{display:flex;justify-content:space-between;align-items:center;gap:8px}
.db-recap-line__name{font-size:12px;color:var(--muted);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.db-recap-line__price{font-size:12px;font-weight:600;color:var(--text);white-space:nowrap}
.db-recap-divider{height:1px;background:var(--border)}
.db-recap-row{display:flex;justify-content:space-between;font-size:13px;color:var(--muted)}
.db-free-tag{background:#dcfce7;color:#166534;font-size:11px;font-weight:700;padding:2px 8px;border-radius:20px}
.db-promo{display:flex;gap:6px}
.db-promo__input{flex:1;padding:8px 12px;border:1.5px solid var(--border);border-radius:8px;font-size:13px;outline:none;background:var(--white);transition:border-color .2s}
.db-promo__input:focus{border-color:var(--pink)}
.db-promo__btn{padding:8px 14px;background:var(--pink);color:#fff;border:none;border-radius:8px;font-weight:700;font-size:13px;cursor:pointer}
.db-promo__msg{font-size:11px;margin:0}
.db-promo__msg--ok{color:#166534}
.db-promo__msg--err{color:#dc2626}
.db-recap-total{display:flex;justify-content:space-between;align-items:center;font-size:14px}
.db-recap-total strong{font-size:20px;font-weight:800;color:var(--pink)}
.db-checkout-btn{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;padding:13px;background:linear-gradient(135deg,var(--pink-dark),var(--pink));color:#fff;border:none;border-radius:12px;font-size:14px;font-weight:700;cursor:pointer;box-shadow:0 4px 18px rgba(233,30,140,.35);transition:all .2s}
.db-checkout-btn:hover{transform:translateY(-2px);box-shadow:0 8px 26px rgba(233,30,140,.45)}
.db-security{display:flex;justify-content:center;gap:12px;font-size:10px;color:var(--muted)}
.db-cart-infos{background:var(--white);border-radius:10px;padding:10px 12px}
.db-cart-infos p{font-size:11px;color:var(--muted);margin:0 0 4px}
.db-cart-infos p:last-child{margin-bottom:0}
.db-main-grid{display:grid;grid-template-columns:1fr 300px;gap:16px}
.db-orders-list{display:flex;flex-direction:column}
.db-order-row{display:grid;grid-template-columns:1fr auto auto auto;align-items:center;gap:12px;padding:14px 22px;border-bottom:1px solid var(--border);transition:background .15s}
.db-order-row:last-child{border-bottom:none}
.db-order-row:hover{background:#fdf5f9}
.db-order-row__event{display:flex;align-items:center;gap:10px}
.db-order-row__icon{width:36px;height:36px;background:var(--pink-light);border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.db-order-row__title{font-size:13px;font-weight:600;color:var(--text);margin:0 0 2px}
.db-order-row__ref{font-size:11px;color:var(--muted);margin:0}
.db-order-row__date{font-size:12px;color:var(--muted);white-space:nowrap}
.db-order-row__amount{font-size:13px;font-weight:700;color:var(--text);white-space:nowrap}
.db-status{display:inline-flex;align-items:center;gap:4px;padding:4px 10px;border-radius:20px;font-size:11px;font-weight:700;white-space:nowrap}
.db-status--warning{background:#fff8e1;color:#f57c00}
.db-status--success{background:#e8f5e9;color:#2e7d32}
.db-status--error{background:#fef2f2;color:#b91c1c}
.db-status--info{background:#e3f2fd;color:#1565c0}
.db-status--default{background:#f5f5f5;color:#757575}
.db-sidebar{display:flex;flex-direction:column}
.db-profile{padding:24px;text-align:center;border-bottom:1px solid var(--border)}
.db-profile__avatar{width:72px;height:72px;background:linear-gradient(135deg,var(--pink-dark),var(--pink));border-radius:50%;margin:0 auto 12px;display:flex;align-items:center;justify-content:center;font-size:26px;font-weight:800;color:#fff;box-shadow:0 6px 20px rgba(233,30,140,.3)}
.db-profile__name{font-size:16px;font-weight:700;color:var(--text);margin:0 0 4px}
.db-profile__email{font-size:12px;color:var(--muted);margin:0 0 10px}
.db-profile__badge{display:inline-flex;align-items:center;gap:5px;padding:4px 10px;border-radius:20px;font-size:11px;font-weight:700}
.db-profile__badge--ok{background:#e8f5e9;color:#2e7d32}
.db-profile__badge--warn{background:#fff8e1;color:#f57c00}
.db-profile__stats{display:flex;align-items:center;padding:16px 20px}
.db-profile__stat{flex:1;text-align:center}
.db-profile__stat strong{display:block;font-size:18px;font-weight:800;color:var(--text)}
.db-profile__stat span{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}
.db-profile__divider{width:1px;height:30px;background:var(--border)}
.db-event-list{padding:8px 12px 12px;display:flex;flex-direction:column;gap:6px}
.db-event-item{display:flex;align-items:center;gap:10px;padding:10px;border-radius:12px;cursor:pointer;transition:all .15s}
.db-event-item:hover{background:var(--pink-pale)}
.db-event-item__icon{width:34px;height:34px;background:var(--pink-light);border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0;color:var(--pink)}
.db-event-item__icon--gold{background:#fff8e1;color:#F57C00}
.db-event-item__body{flex:1;min-width:0}
.db-event-item__title{font-size:12px;font-weight:600;color:var(--text);margin:0 0 2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.db-event-item__meta{font-size:10px;color:var(--muted);margin:0}
.db-price-tag{font-size:10px;font-weight:800;padding:3px 8px;border-radius:20px;white-space:nowrap}
.db-price-tag--paid{background:#fff8e1;color:#f57c00}
.db-price-tag--free{background:#e8f5e9;color:#2e7d32}
.db-notif-list{padding:8px 12px 4px;display:flex;flex-direction:column;gap:4px}
.db-notif-item{display:flex;align-items:flex-start;gap:10px;padding:10px;border-radius:12px;transition:background .15s}
.db-notif-item--unread{background:#fff8e1}
.db-notif-item__dot{width:8px;height:8px;border-radius:50%;background:var(--border);margin-top:5px;flex-shrink:0}
.db-notif-item__dot--active{background:var(--pink)}
.db-notif-item__title{font-size:12px;font-weight:600;color:var(--text);margin:0 0 2px}
.db-notif-item__time{font-size:10px;color:var(--muted);margin:0}
.db-card--support{background:linear-gradient(135deg,#fdf0f6,#fce4ec);border-color:#f8bbd0}
.db-support{display:flex;align-items:center;gap:12px;padding:18px 20px 12px}
.db-support__icon{font-size:32px}
.db-support h4{font-size:14px;font-weight:700;color:var(--text);margin:0 0 2px}
.db-support p{font-size:12px;color:var(--muted);margin:0}
.db-btn-support{display:flex;align-items:center;justify-content:center;gap:7px;width:calc(100% - 32px);margin:0 16px 16px;padding:10px;background:var(--white);border:1.5px solid var(--border);border-radius:10px;color:var(--pink-dark);font-size:13px;font-weight:700;cursor:pointer;transition:all .2s}
.db-btn-support:hover{background:var(--pink);color:#fff;border-color:var(--pink)}
.db-empty{padding:48px 20px;text-align:center;display:flex;flex-direction:column;align-items:center;gap:10px}
.db-empty--sm{padding:32px 20px}
.db-empty--xs{padding:18px 14px}
.db-empty__icon{font-size:48px}
.db-empty--sm .db-empty__icon,.db-empty--xs .db-empty__icon{font-size:32px}
.db-empty h3{font-size:16px;font-weight:700;color:var(--text);margin:0}
.db-empty--sm h3{font-size:14px}
.db-empty p{font-size:13px;color:var(--muted);margin:0}
.db-empty--xs p{font-size:11px}
.db-btn-primary{display:inline-flex;align-items:center;gap:7px;padding:10px 20px;background:linear-gradient(135deg,var(--pink-dark),var(--pink));color:#fff;border:none;border-radius:10px;font-size:13px;font-weight:700;cursor:pointer;box-shadow:0 3px 14px rgba(233,30,140,.3);transition:all .2s}
.db-btn-primary:hover{transform:translateY(-2px);box-shadow:0 6px 20px rgba(233,30,140,.4)}
.db-btn-ghost{display:inline-flex;align-items:center;gap:6px;background:none;border:none;color:var(--pink);font-size:13px;font-weight:600;cursor:pointer;padding:6px 2px;transition:opacity .2s}
.db-btn-ghost:hover{opacity:.7}
.db-btn-ghost--danger{color:#dc2626}
.db-badge{font-size:11px;font-weight:800;padding:2px 8px;border-radius:20px}
.db-badge--pink{background:var(--pink);color:#fff}
.db-badge--red{background:#dc2626;color:#fff}
.db-link{display:inline-flex;align-items:center;gap:4px;font-size:12px;font-weight:600;color:var(--pink);cursor:pointer;transition:opacity .2s}
.db-link:hover{opacity:.7}
.db-link--center{display:flex;justify-content:center;padding:10px;border-top:1px solid var(--border);margin-top:4px}
@media(max-width:1100px){.db-cart-layout{grid-template-columns:1fr}.db-cart-recap{border-top:1px solid var(--border)}.db-main-grid{grid-template-columns:1fr}}
@media(max-width:900px){.db-kpis{grid-template-columns:repeat(2,1fr)}.db-actions{grid-template-columns:repeat(2,1fr)}.db-hero{flex-direction:column;align-items:flex-start;gap:16px;padding:24px}.db-order-row{grid-template-columns:1fr auto}.db-order-row__date,.db-order-row__amount{display:none}}
@media(max-width:600px){.db-kpis{grid-template-columns:repeat(2,1fr);gap:10px}.db-hero__right{flex-wrap:wrap}}
</style>