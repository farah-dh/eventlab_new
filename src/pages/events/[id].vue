<route lang="yaml">
meta:
  layout: blank
  public: true
</route>

<script setup lang="ts">
definePage({ meta: { layout: 'blank', public: true } })
import { ref, computed, onMounted } from 'vue'
import { useCartStore } from '@/stores/cart'

const router = useRouter()
const route = useRoute()
const cart = useCartStore()
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'

const event       = ref<any>(null)
const isLoading   = ref(true)
const error       = ref('')
const quantity    = ref(1)
const siteSettings = ref<any>({})
const showToast   = ref(false)

const eventId = computed(() => {
  const params = route.params as any
  return params.id || params.slug || ''
})
const siteName = computed(() => siteSettings.value.site_name || 'EventLab')

onMounted(async () => {
  fetchEvent()
  fetchSettings()
})

const fetchSettings = async () => {
  try { const r = await fetch(`${API_BASE_URL}/cms/settings/`); if (r.ok) siteSettings.value = await r.json() } catch {}
}

const fetchEvent = async () => {
  isLoading.value = true
  error.value = ''
  try {
    const r = await fetch(`${API_BASE_URL}/events/${eventId.value}/`)
    if (!r.ok) {
      error.value = 'Événement introuvable'
      return
    }
    const d = await r.json()
    event.value = d.data || d
  } catch {
    error.value = 'Erreur de chargement'
  } finally {
    isLoading.value = false
  }
}

const formatDate = (d: string) => {
  if (!d) return ''
  return new Date(d).toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
}
const formatTime = (d: string) => {
  if (!d) return '20:00'
  return new Date(d).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}
const getDateParts = (d: string) => {
  if (!d) return { day: '--', month: '---', year: '----' }
  const date = new Date(d)
  return {
    day: date.getDate().toString().padStart(2, '0'),
    month: date.toLocaleDateString('fr-FR', { month: 'short' }).toUpperCase().replace('.', ''),
    year: date.getFullYear(),
  }
}
const formatPrice = (price: any) => {
  if (!price || price === 0) return 'Gratuit'
  return Number(price).toFixed(2)
}
const isPriceFree = computed(() => !event.value?.price || event.value?.price === 0)
const totalPrice = computed(() => {
  if (!event.value || isPriceFree.value) return '0.00'
  return (Number(event.value.price) * quantity.value).toFixed(2)
})

const daysUntil = computed(() => {
  if (!event.value?.start_date) return null
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const eventDate = new Date(event.value.start_date)
  eventDate.setHours(0, 0, 0, 0)
  const diff = Math.ceil((eventDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
  return diff
})
const daysLabel = computed(() => {
  const d = daysUntil.value
  if (d === null) return ''
  if (d < 0) return 'Événement passé'
  if (d === 0) return "Aujourd'hui !"
  if (d === 1) return 'Demain !'
  if (d <= 7) return `Dans ${d} jours`
  return `J − ${d}`
})

const locationDisplay = computed(() => {
  if (!event.value) return '—'
  const name = event.value.location_name
  const addr = event.value.location_address
  if (name && addr && addr !== '123 Event Street') return `${name}, ${addr}`
  if (name) return name
  if (addr && addr !== '123 Event Street') return addr
  return 'Lieu à confirmer'
})

const catConfigs = [
  { emoji: '🎵', img: 'https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?w=1600&q=85', keywords: ['music','musique','concert'] },
  { emoji: '⚽', img: 'https://images.unsplash.com/photo-1508098682722-e99c643e7f0b?w=1600&q=85', keywords: ['sport','sports','football'] },
  { emoji: '💻', img: 'https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=1600&q=85', keywords: ['tech','technology','it'] },
  { emoji: '🎨', img: 'https://images.unsplash.com/photo-1460661419201-fd4cecdf8a8b?w=1600&q=85', keywords: ['art','arts','culture'] },
  { emoji: '🍽️', img: 'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=1600&q=85', keywords: ['food','nourriture'] },
  { emoji: '💼', img: 'https://images.unsplash.com/photo-1515187029135-18ee286d815b?w=1600&q=85', keywords: ['business','affaires'] },
  { emoji: '🎪', img: 'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=1600&q=85', keywords: ['festival'] },
  { emoji: '🎬', img: 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=1600&q=85', keywords: ['cinema','cinéma','film'] },
  { emoji: '🎭', img: 'https://images.unsplash.com/photo-1503095396549-807759245b35?w=1600&q=85', keywords: ['theatre','théâtre'] },
  { emoji: '😂', img: 'https://images.unsplash.com/photo-1527224538127-2104bb71c51b?w=1600&q=85', keywords: ['comedy','comédie','comedie','humour'] },
  { emoji: '👗', img: 'https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=1600&q=85', keywords: ['fashion','mode'] },
  { emoji: '🎮', img: 'https://images.unsplash.com/photo-1542751371-adc38448a05e?w=1600&q=85', keywords: ['gaming','game','jeu'] },
  { emoji: '🏥', img: 'https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=1600&q=85', keywords: ['health','santé'] },
  { emoji: '🎓', img: 'https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=1600&q=85', keywords: ['education','éducation'] },
  { emoji: '✈️', img: 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=1600&q=85', keywords: ['travel','voyage'] },
  { emoji: '🔬', img: 'https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=1600&q=85', keywords: ['science'] },
  { emoji: '💃', img: 'https://images.unsplash.com/photo-1535525153412-5a42439a210d?w=1600&q=85', keywords: ['danse','dance'] },
]
const getCatCfg = (name: string) => {
  const n = (name || '').toLowerCase()
  return catConfigs.find(c => c.keywords.some(k => n.includes(k))) || {
    emoji: '🎯',
    img: 'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=1600&q=85',
  }
}
const heroImage = computed(() => event.value?.cover_image || event.value?.image || event.value?.banner || getCatCfg(event.value?.category_name || '').img)

const goHome = () => router.push('/')
const goToLogin = () => router.push('/login')
const goToRegister = () => router.push('/register')
const goToCart = () => router.push('/cart')

const incQty = () => {
  if (event.value && quantity.value < (event.value.seats_available || 10)) quantity.value++
}
const decQty = () => {
  if (quantity.value > 1) quantity.value--
}

// ✨ AJOUTER AU PANIER
const addToCart = () => {
  if (!event.value || event.value.is_sold_out) return

  cart.addItem({
    eventId: event.value.id,
    title: event.value.title,
    image: heroImage.value,
    price: Number(event.value.price) || 0,
    quantity: quantity.value,
    date: event.value.start_date,
    location: locationDisplay.value,
    category: event.value.category_name || '',
  })

  // Toast
  showToast.value = true
  setTimeout(() => {
    showToast.value = false
    // Redirige vers le panier après 1.2s
    router.push('/cart')
  }, 1200)
}

const availabilityLevel = computed(() => {
  if (!event.value) return 'high'
  const ratio = (event.value.seats_available || 0) / (event.value.seats || 1)
  if (event.value.is_sold_out) return 'sold'
  if (ratio < 0.15) return 'critical'
  if (ratio < 0.4) return 'low'
  return 'high'
})

const planSeats = computed(() => {
  const rows = []
  const eventNum = parseInt(String(event.value?.id || 1))
  for (let row = 0; row < 5; row++) {
    const seats = []
    for (let col = 0; col < 18; col++) {
      if (col === 5 || col === 12) { seats.push({ type: 'gap' }); continue }
      const reserved = ((row + 1) * (col + 1) + eventNum) % 7 < 2
      seats.push({ type: 'seat', reserved })
    }
    rows.push(seats)
  }
  return rows
})
</script>

<template>
  <div class="ev">

    <!-- ════ NAVBAR avec icône panier ════ -->
    <nav class="ev-nav">
      <div class="ev-nav__inner">
        <div class="ev-logo" @click="goHome()">
          <div class="ev-logo__mark">{{ siteName[0] }}</div>
          <span class="ev-logo__name">{{ siteName }}</span>
        </div>

        <div class="ev-nav__crumb">
          <button class="ev-crumb-btn" @click="goHome()">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15,18 9,12 15,6"/></svg>
            Accueil
          </button>
          <span class="ev-crumb-sep">/</span>
          <span class="ev-crumb-cur">{{ event?.category_name || 'Événement' }}</span>
        </div>

        <div class="ev-nav__actions">
          <!-- 🛒 ICONE PANIER -->
          <button class="ev-cart-btn" @click="goToCart()" aria-label="Panier">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/>
              <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>
            </svg>
            <span v-if="cart.totalItems > 0" class="ev-cart-badge">{{ cart.totalItems }}</span>
          </button>
          <button class="ev-btn ev-ghost" @click="goToLogin()">Connexion</button>
          <button class="ev-btn ev-primary" @click="goToRegister()">S'inscrire</button>
        </div>
      </div>
    </nav>

    <!-- 🎉 TOAST DE CONFIRMATION -->
    <Transition name="toast">
      <div v-if="showToast" class="ev-toast">
        <span class="ev-toast__icon">✓</span>
        <div>
          <div class="ev-toast__title">Ajouté au panier !</div>
          <div class="ev-toast__sub">{{ quantity }} billet{{ quantity > 1 ? 's' : '' }} pour {{ event?.title }}</div>
        </div>
      </div>
    </Transition>

    <!-- LOADING -->
    <div v-if="isLoading" class="ev-loading">
      <div class="ev-spinner"></div>
      <p>Chargement de l'événement…</p>
    </div>

    <!-- ERROR -->
    <div v-else-if="error" class="ev-error">
      <span>😕</span>
      <h2>{{ error }}</h2>
      <button class="ev-btn ev-primary" @click="goHome()">Retour à l'accueil</button>
    </div>

    <!-- EVENT DETAIL -->
    <template v-else-if="event">

      <!-- HERO -->
      <section class="ev-hero">
        <div class="ev-hero__bg" :style="{ backgroundImage: `url(${heroImage})` }"></div>
        <div class="ev-hero__overlay"></div>
        <div class="ev-hero__glow"></div>

        <div class="ev-wrap">
          <div class="ev-hero__content">
            <div class="ev-hero__cat-badge">
              <span class="ev-hero__cat-emoji">{{ getCatCfg(event.category_name).emoji }}</span>
              <span class="ev-hero__cat-name">{{ event.category_name }}</span>
            </div>

            <div class="ev-hero__countdown" v-if="daysUntil !== null && daysUntil >= 0">
              <span class="ev-hero__countdown-icon">⏳</span>
              {{ daysLabel }}
            </div>

            <h1 class="ev-hero__title">{{ event.title }}</h1>

            <div class="ev-hero__metas">
              <div class="ev-hero__meta">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                {{ locationDisplay }}
              </div>
              <div class="ev-hero__meta">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                {{ formatDate(event.start_date) }}
              </div>
              <div class="ev-hero__meta">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
                Par <strong>{{ event.organizer_name }}</strong>
              </div>
            </div>

            <div class="ev-hero__price-box" v-if="!isPriceFree">
              <span class="ev-hero__price-lbl">À partir de</span>
              <span class="ev-hero__price">{{ formatPrice(event.price) }} <small>DT</small></span>
            </div>
            <div class="ev-hero__price-box ev-hero__price-box--free" v-else>
              <span class="ev-hero__price">🎁 Gratuit</span>
            </div>
          </div>
        </div>
      </section>

      <!-- MAIN -->
      <div class="ev-main">
        <div class="ev-wrap">
          <div class="ev-grid">

            <!-- SIDEBAR -->
            <aside class="ev-side">
              <div class="ev-card">
                <div class="ev-card__head">
                  <span class="ev-card__head-icon">🎟️</span>
                  BILLETS
                </div>
                <div class="ev-card__body">
                  <div class="ev-tline">
                    <div class="ev-tline__item">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                      {{ getDateParts(event.start_date).day }}/{{ getDateParts(event.start_date).month }}/{{ getDateParts(event.start_date).year }}
                    </div>
                    <div class="ev-tline__item">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><polyline points="12,6 12,12 16,14"/></svg>
                      {{ formatTime(event.start_date) }}
                    </div>
                  </div>

                  <div class="ev-ticket">
                    <div class="ev-ticket__name">
                      <div class="ev-ticket__icon">🎟️</div>
                      <div>
                        <div class="ev-ticket__title">Billet standard</div>
                        <div class="ev-ticket__sub" v-if="!isPriceFree">{{ formatPrice(event.price) }} DT par billet</div>
                        <div class="ev-ticket__sub" v-else>Entrée gratuite</div>
                      </div>
                    </div>
                    <div class="ev-ticket__qty">
                      <button @click="decQty" :disabled="quantity <= 1">−</button>
                      <span>{{ quantity }}</span>
                      <button @click="incQty" :disabled="event.is_sold_out || quantity >= (event.seats_available || 10)">+</button>
                    </div>
                  </div>

                  <div class="ev-avail" :class="`ev-avail--${availabilityLevel}`">
                    <span v-if="availabilityLevel === 'sold'">🚫 Complet</span>
                    <span v-else-if="availabilityLevel === 'critical'">🔥 Plus que {{ event.seats_available }} places !</span>
                    <span v-else-if="availabilityLevel === 'low'">⚡ {{ event.seats_available }} places restantes</span>
                    <span v-else>✅ {{ event.seats_available }} places disponibles</span>
                  </div>

                  <div class="ev-total" v-if="!isPriceFree">
                    <span>Total</span>
                    <span class="ev-total__amount">{{ totalPrice }} <small>DT</small></span>
                  </div>

                  <button class="ev-reserve" @click="addToCart" :disabled="event.is_sold_out">
                    <svg v-if="!event.is_sold_out" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                      <circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/>
                      <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>
                    </svg>
                    {{ event.is_sold_out ? 'Complet' : 'Ajouter au panier' }}
                  </button>

                  <div class="ev-secure">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                    Paiement 100% sécurisé
                  </div>
                </div>
              </div>

              <div class="ev-card">
                <div class="ev-card__head">
                  <span class="ev-card__head-icon">🗺️</span>
                  PLAN DE SALLE
                </div>
                <div class="ev-card__body">
                  <div class="ev-plan">
                    <div class="ev-plan__stage"><span>🎤 SCÈNE</span></div>
                    <div class="ev-plan__rows">
                      <div class="ev-plan__row" v-for="(row, ri) in planSeats" :key="ri">
                        <span class="ev-plan__rowlbl">{{ String.fromCharCode(65 + ri) }}</span>
                        <div class="ev-plan__seats">
                          <div
                            v-for="(seat, si) in row"
                            :key="si"
                            :class="seat.type === 'gap' ? 'ev-plan__gap' : seat.reserved ? 'ev-plan__seat ev-plan__seat--off' : 'ev-plan__seat ev-plan__seat--on'"
                          ></div>
                        </div>
                        <span class="ev-plan__rowlbl">{{ String.fromCharCode(65 + ri) }}</span>
                      </div>
                    </div>
                    <div class="ev-plan__entry">
                      <span>← Entrée</span>
                      <span>Entrée →</span>
                    </div>
                  </div>
                  <div class="ev-plan__legend">
                    <div><span class="ev-dot ev-dot--on"></span> Disponible</div>
                    <div><span class="ev-dot ev-dot--off"></span> Réservé</div>
                  </div>
                </div>
              </div>
            </aside>

            <!-- CONTENT -->
            <main class="ev-content">
              <div class="ev-info-grid">
                <div class="ev-info">
                  <div class="ev-info__icon">📅</div>
                  <div class="ev-info__lbl">Date</div>
                  <div class="ev-info__val">{{ getDateParts(event.start_date).day }} {{ getDateParts(event.start_date).month }}</div>
                </div>
                <div class="ev-info">
                  <div class="ev-info__icon">⏰</div>
                  <div class="ev-info__lbl">Heure</div>
                  <div class="ev-info__val">{{ formatTime(event.start_date) }}</div>
                </div>
                <div class="ev-info">
                  <div class="ev-info__icon">📍</div>
                  <div class="ev-info__lbl">Lieu</div>
                  <div class="ev-info__val">{{ event.location_name || '—' }}</div>
                </div>
                <div class="ev-info">
                  <div class="ev-info__icon">👥</div>
                  <div class="ev-info__lbl">Places</div>
                  <div class="ev-info__val">{{ event.seats_available }}/{{ event.seats }}</div>
                </div>
              </div>

              <div class="ev-bigimg">
                <img :src="heroImage" :alt="event.title" />
                <span class="ev-badge" v-if="event.is_featured">⭐ Vedette</span>
              </div>

              <div class="ev-desc">
                <h2 class="ev-desc__title">À propos de l'événement</h2>
                <div class="ev-desc__text">
                  <p>
                    <strong>{{ event.title }}</strong> est un événement {{ event.category_name?.toLowerCase() }} qui aura lieu à <strong>{{ event.location_name }}</strong> le {{ formatDate(event.start_date) }}.
                  </p>
                  <p>
                    Organisé par <strong>{{ event.organizer_name }}</strong>, cet événement promet d'être un moment inoubliable. Réservez vos billets dès maintenant pour profiter de cette expérience unique.
                  </p>
                  <ul class="ev-list">
                    <li><strong>Date :</strong> {{ formatDate(event.start_date) }}</li>
                    <li v-if="event.end_date && event.end_date !== event.start_date"><strong>Fin :</strong> {{ formatDate(event.end_date) }}</li>
                    <li><strong>Lieu :</strong> {{ locationDisplay }}</li>
                    <li><strong>Heure de début :</strong> {{ formatTime(event.start_date) }}</li>
                    <li><strong>Catégorie :</strong> {{ event.category_name }}</li>
                    <li><strong>Organisateur :</strong> {{ event.organizer_name }}</li>
                  </ul>
                </div>
              </div>

              <div class="ev-org">
                <div class="ev-org__avatar">{{ event.organizer_name?.[0]?.toUpperCase() }}</div>
                <div class="ev-org__info">
                  <div class="ev-org__lbl">Organisé par</div>
                  <div class="ev-org__name">{{ event.organizer_name }}</div>
                </div>
                <button class="ev-btn ev-ghost ev-btn--sm">Voir le profil</button>
              </div>
            </main>
          </div>
        </div>
      </div>
    </template>

    <footer class="ev-footer">
      <div class="ev-wrap">
        <div class="ev-footer__bot">
          <span>© 2026 {{ siteName }}. Tous droits réservés.</span>
          <span class="ev-footer__made">Fait avec 💖 en Tunisie</span>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;0,800;1,700&family=Outfit:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
.ev { font-family: 'Outfit', sans-serif; background: #FFF5F7; color: #1a0a12; min-height: 100vh; }

/* NAV */
.ev-nav { position: fixed; top: 0; left: 0; right: 0; z-index: 999; padding: 0 40px; background: rgba(255,255,255,.96); backdrop-filter: blur(20px); box-shadow: 0 1px 0 rgba(233,30,140,.1); }
.ev-nav__inner { max-width: 1280px; margin: 0 auto; height: 70px; display: flex; align-items: center; justify-content: space-between; gap: 30px; }
.ev-nav__crumb { display: flex; align-items: center; gap: 8px; font-size: 14px; flex: 1; }
.ev-crumb-btn { display: flex; align-items: center; gap: 5px; background: #FCE4EC; color: #E91E8C; border: none; border-radius: 8px; padding: 6px 14px; font-size: 13px; font-weight: 600; cursor: pointer; font-family: 'Outfit', sans-serif; transition: all .2s; }
.ev-crumb-btn:hover { background: #F8BBD0; }
.ev-crumb-sep { color: #F48FB1; }
.ev-crumb-cur { font-weight: 700; color: #E91E8C; font-size: 13px; }
.ev-nav__actions { display: flex; gap: 10px; align-items: center; }

.ev-logo { display: flex; align-items: center; gap: 10px; cursor: pointer; }
.ev-logo__mark { width: 38px; height: 38px; border-radius: 11px; background: linear-gradient(135deg, #E91E8C, #AD1457); display: flex; align-items: center; justify-content: center; color: #fff; font-family: 'Playfair Display', serif; font-weight: 700; font-size: 18px; flex-shrink: 0; box-shadow: 0 4px 14px rgba(233,30,140,.35); }
.ev-logo__name { font-family: 'Playfair Display', serif; font-weight: 700; font-size: 21px; color: #880E4F; }

/* 🛒 PANIER */
.ev-cart-btn {
  position: relative;
  width: 42px; height: 42px;
  border-radius: 50%;
  border: 1.5px solid #FCE4EC;
  background: #fff;
  color: #E91E8C;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all .2s;
}
.ev-cart-btn:hover { background: #FCE4EC; border-color: #E91E8C; transform: scale(1.05); }
.ev-cart-badge {
  position: absolute; top: -4px; right: -4px;
  min-width: 20px; height: 20px;
  border-radius: 10px;
  background: linear-gradient(135deg, #E91E8C, #AD1457);
  color: #fff;
  font-size: 11px; font-weight: 800;
  display: flex; align-items: center; justify-content: center;
  padding: 0 5px;
  box-shadow: 0 4px 10px rgba(233,30,140,.4);
  border: 2px solid #fff;
}

.ev-btn { display: inline-flex; align-items: center; gap: 6px; border: none; cursor: pointer; border-radius: 10px; font-size: 14px; font-weight: 600; padding: 10px 22px; transition: all .25s; font-family: 'Outfit', sans-serif; line-height: 1; white-space: nowrap; }
.ev-btn--sm { padding: 8px 16px; font-size: 13px; }
.ev-primary { background: linear-gradient(135deg, #E91E8C, #AD1457); color: #fff; box-shadow: 0 4px 16px rgba(233,30,140,.35); }
.ev-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(233,30,140,.45); }
.ev-ghost { background: transparent; color: #E91E8C; border: 1.5px solid #F8BBD0; }
.ev-ghost:hover { background: #FFF5F7; border-color: #F48FB1; }

/* 🎉 TOAST */
.ev-toast {
  position: fixed; top: 90px; right: 30px; z-index: 9999;
  display: flex; align-items: center; gap: 14px;
  background: #fff;
  border-radius: 14px;
  padding: 16px 22px;
  box-shadow: 0 16px 48px rgba(173,20,87,.25);
  border: 1.5px solid #ecfdf5;
  min-width: 280px;
}
.ev-toast__icon {
  width: 36px; height: 36px; border-radius: 50%;
  background: linear-gradient(135deg, #10B981, #059669);
  color: #fff;
  font-size: 18px; font-weight: 800;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 14px rgba(16,185,129,.35);
}
.ev-toast__title { font-size: 14px; font-weight: 700; color: #1a0a12; }
.ev-toast__sub { font-size: 12px; color: #9e6878; margin-top: 2px; }

.toast-enter-active, .toast-leave-active { transition: all .35s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateX(40px); }

/* LOADING / ERROR */
.ev-loading, .ev-error { padding-top: 200px; text-align: center; min-height: 100vh; }
.ev-spinner { width: 40px; height: 40px; border: 3px solid #FCE4EC; border-top-color: #E91E8C; border-radius: 50%; margin: 0 auto 18px; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.ev-loading p { color: #9e6878; font-size: 14px; }
.ev-error span { font-size: 60px; }
.ev-error h2 { font-family: 'Playfair Display', serif; font-size: 26px; color: #880E4F; margin: 18px 0 24px; }

/* HERO */
.ev-hero { margin-top: 70px; padding: 90px 40px 70px; position: relative; min-height: 460px; display: flex; align-items: flex-end; overflow: hidden; }
.ev-hero__bg { position: absolute; inset: 0; background-size: cover; background-position: center; filter: blur(2px); transform: scale(1.05); }
.ev-hero__overlay { position: absolute; inset: 0; background: linear-gradient(135deg, rgba(74,10,46,.93) 0%, rgba(136,14,79,.85) 50%, rgba(173,20,87,.92) 100%); }
.ev-hero__glow { position: absolute; top: -100px; right: -100px; width: 500px; height: 500px; background: radial-gradient(circle, rgba(255,179,209,.4) 0%, transparent 70%); filter: blur(40px); pointer-events: none; }
.ev-wrap { max-width: 1280px; margin: 0 auto; padding: 0 40px; position: relative; z-index: 1; width: 100%; }
.ev-hero__content { color: #fff; }
.ev-hero__cat-badge { display: inline-flex; align-items: center; gap: 10px; background: linear-gradient(135deg, #FFB300, #F57C00); color: #fff; border-radius: 100px; padding: 8px 20px; font-size: 13px; font-weight: 700; margin-bottom: 22px; text-transform: uppercase; letter-spacing: 1.5px; box-shadow: 0 6px 20px rgba(245,124,0,.5); }
.ev-hero__cat-emoji { font-size: 18px; }
.ev-hero__countdown { display: inline-flex; align-items: center; gap: 8px; background: rgba(255,255,255,.18); border: 1px solid rgba(255,255,255,.4); border-radius: 100px; padding: 6px 16px; font-size: 13px; font-weight: 700; color: #fff; margin-left: 10px; margin-bottom: 22px; backdrop-filter: blur(10px); vertical-align: top; }
.ev-hero__countdown-icon { font-size: 14px; }
.ev-hero__title { font-family: 'Playfair Display', serif; font-size: clamp(38px, 5.5vw, 64px); font-weight: 800; line-height: 1.05; margin-bottom: 22px; letter-spacing: -.5px; color: #fff !important; text-shadow: 0 4px 20px rgba(0,0,0,.5), 0 2px 8px rgba(0,0,0,.4); }
.ev-hero__metas { display: flex; flex-wrap: wrap; gap: 24px; margin-bottom: 26px; }
.ev-hero__meta { display: flex; align-items: center; gap: 8px; font-size: 14px; color: rgba(255,255,255,.95); font-weight: 500; }
.ev-hero__meta strong { color: #FFB3D1; font-weight: 700; }
.ev-hero__price-box { display: inline-flex; align-items: center; gap: 14px; background: rgba(255,255,255,.18); backdrop-filter: blur(10px); border: 1.5px solid rgba(255,255,255,.3); padding: 14px 26px; border-radius: 16px; font-size: 13px; color: rgba(255,255,255,.85); font-weight: 500; }
.ev-hero__price-lbl { text-transform: uppercase; letter-spacing: 1.5px; font-size: 11px; }
.ev-hero__price { font-family: 'Playfair Display', serif; font-size: 36px; font-weight: 800; color: #FFB3D1; line-height: 1; }
.ev-hero__price small { font-size: 16px; font-weight: 600; }
.ev-hero__price-box--free .ev-hero__price { color: #6EE7B7; }

/* MAIN */
.ev-main { padding: 50px 40px 60px; background: #FFF5F7; }
.ev-grid { display: grid; grid-template-columns: 380px 1fr; gap: 36px; align-items: flex-start; }

.ev-side { display: flex; flex-direction: column; gap: 24px; position: sticky; top: 90px; }
.ev-card { background: #fff; border-radius: 18px; overflow: hidden; border: 1.5px solid #FCE4EC; box-shadow: 0 4px 24px rgba(233,30,140,.08); }
.ev-card__head { background: linear-gradient(135deg, #4a0a2e, #1a0a12); color: #fff; padding: 16px 24px; text-align: center; font-size: 13px; font-weight: 700; letter-spacing: 4px; text-transform: uppercase; display: flex; align-items: center; justify-content: center; gap: 10px; }
.ev-card__head-icon { font-size: 18px; letter-spacing: 0; }
.ev-card__body { padding: 22px; }

.ev-tline { display: flex; gap: 18px; background: linear-gradient(135deg, #FFF5F7, #FCE4EC); border-radius: 12px; padding: 12px 16px; margin-bottom: 18px; }
.ev-tline__item { display: flex; align-items: center; gap: 7px; font-size: 13px; color: #AD1457; font-weight: 700; }

.ev-ticket { display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #FFF5F7, #FCE4EC); border: 1.5px dashed #F8BBD0; border-radius: 14px; padding: 16px; margin-bottom: 14px; }
.ev-ticket__name { display: flex; align-items: center; gap: 12px; }
.ev-ticket__icon { width: 42px; height: 42px; border-radius: 11px; background: linear-gradient(135deg, #E91E8C, #AD1457); display: flex; align-items: center; justify-content: center; font-size: 20px; box-shadow: 0 4px 14px rgba(233,30,140,.35); }
.ev-ticket__title { font-size: 14px; font-weight: 700; color: #1a0a12; }
.ev-ticket__sub { font-size: 12px; color: #9e6878; margin-top: 2px; }
.ev-ticket__qty { display: flex; align-items: center; gap: 4px; background: #fff; border: 1.5px solid #FCE4EC; border-radius: 10px; padding: 3px; }
.ev-ticket__qty button { width: 28px; height: 28px; border: none; background: transparent; color: #E91E8C; font-size: 18px; font-weight: 700; cursor: pointer; border-radius: 7px; transition: all .2s; }
.ev-ticket__qty button:hover:not(:disabled) { background: #FCE4EC; }
.ev-ticket__qty button:disabled { opacity: .3; cursor: not-allowed; }
.ev-ticket__qty span { min-width: 28px; text-align: center; font-size: 14px; font-weight: 700; color: #1a0a12; }

.ev-avail { text-align: center; border-radius: 10px; padding: 9px 14px; font-size: 12px; font-weight: 700; margin-bottom: 14px; }
.ev-avail--high { background: #ecfdf5; color: #047857; }
.ev-avail--low { background: #fef3c7; color: #b45309; }
.ev-avail--critical { background: #fee2e2; color: #b91c1c; animation: pulse 1.5s infinite; }
.ev-avail--sold { background: #1f2937; color: #fff; }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .65; } }

.ev-total { display: flex; justify-content: space-between; align-items: center; padding: 14px 0; border-top: 1.5px dashed #FCE4EC; border-bottom: 1.5px dashed #FCE4EC; margin-bottom: 16px; font-size: 14px; font-weight: 600; color: #4a0a2e; }
.ev-total__amount { font-family: 'Playfair Display', serif; font-size: 24px; font-weight: 800; color: #E91E8C; }
.ev-total__amount small { font-size: 13px; font-weight: 600; }

.ev-reserve { width: 100%; display: flex; align-items: center; justify-content: center; gap: 8px; padding: 14px; background: linear-gradient(135deg, #E91E8C, #AD1457); border: none; border-radius: 12px; color: #fff; font-family: 'Outfit', sans-serif; font-size: 15px; font-weight: 700; cursor: pointer; transition: all .25s; box-shadow: 0 6px 20px rgba(233,30,140,.35); }
.ev-reserve:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 10px 28px rgba(233,30,140,.5); }
.ev-reserve:disabled { opacity: .5; cursor: not-allowed; }
.ev-secure { display: flex; align-items: center; justify-content: center; gap: 6px; margin-top: 12px; font-size: 11px; color: #9e6878; }

/* PLAN */
.ev-plan { background: linear-gradient(180deg, #fff 0%, #FFF5F7 100%); border-radius: 14px; padding: 22px 16px; border: 1px solid #FCE4EC; }
.ev-plan__stage { background: linear-gradient(135deg, #1a0a12, #4a0a2e); color: #fff; padding: 12px 0; border-radius: 10px; text-align: center; font-weight: 700; font-size: 12px; letter-spacing: 4px; margin-bottom: 22px; box-shadow: 0 4px 14px rgba(26,10,18,.3); }
.ev-plan__rows { display: flex; flex-direction: column; gap: 7px; }
.ev-plan__row { display: flex; align-items: center; gap: 8px; justify-content: center; }
.ev-plan__rowlbl { font-size: 10px; font-weight: 700; color: #b07a8e; width: 14px; text-align: center; }
.ev-plan__seats { display: flex; gap: 3px; flex: 1; justify-content: center; }
.ev-plan__seat { width: 11px; height: 11px; border-radius: 3px; transition: all .2s; }
.ev-plan__seat--on { background: linear-gradient(135deg, #F06292, #E91E8C); box-shadow: 0 1px 3px rgba(233,30,140,.3); }
.ev-plan__seat--off { background: #d8d8d8; }
.ev-plan__gap { width: 11px; height: 11px; }
.ev-plan__entry { display: flex; justify-content: space-between; margin-top: 18px; padding: 0 12px; font-size: 10px; font-weight: 700; color: #b07a8e; text-transform: uppercase; letter-spacing: 1px; }
.ev-plan__legend { display: flex; gap: 20px; justify-content: center; margin-top: 16px; padding-top: 16px; border-top: 1px solid #FCE4EC; font-size: 11px; color: #4a0a2e; font-weight: 600; }
.ev-plan__legend > div { display: flex; align-items: center; gap: 6px; }
.ev-dot { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }
.ev-dot--on { background: linear-gradient(135deg, #F06292, #E91E8C); }
.ev-dot--off { background: #d8d8d8; }

/* RIGHT */
.ev-content { display: flex; flex-direction: column; gap: 28px; }
.ev-info-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
.ev-info { background: #fff; border: 1.5px solid #FCE4EC; border-radius: 14px; padding: 22px 16px; text-align: center; transition: all .3s; }
.ev-info:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(233,30,140,.12); border-color: #F48FB1; }
.ev-info__icon { font-size: 28px; margin-bottom: 10px; }
.ev-info__lbl { font-size: 11px; color: #9e6878; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 6px; }
.ev-info__val { font-family: 'Playfair Display', serif; font-size: 17px; font-weight: 700; color: #1a0a12; }

.ev-bigimg { position: relative; border-radius: 18px; overflow: hidden; box-shadow: 0 8px 32px rgba(173,20,87,.15); }
.ev-bigimg img { width: 100%; display: block; max-height: 460px; object-fit: cover; }
.ev-badge { position: absolute; top: 16px; left: 16px; background: linear-gradient(135deg, #FFB300, #F57C00); color: #fff; padding: 6px 14px; border-radius: 100px; font-size: 12px; font-weight: 700; box-shadow: 0 4px 14px rgba(245,124,0,.4); }

.ev-desc { background: #fff; border: 1.5px solid #FCE4EC; border-radius: 18px; padding: 32px; }
.ev-desc__title { font-family: 'Playfair Display', serif; font-size: 24px; font-weight: 800; color: #1a0a12; margin-bottom: 18px; }
.ev-desc__text p { font-size: 15px; line-height: 1.8; color: #4a0a2e; margin-bottom: 14px; }
.ev-desc__text strong { color: #1a0a12; }
.ev-list { list-style: none; padding: 0; margin-top: 18px; }
.ev-list li { padding: 10px 0; border-bottom: 1px solid #FCE4EC; font-size: 14px; color: #4a0a2e; }
.ev-list li:last-child { border: none; }

.ev-org { display: flex; align-items: center; gap: 16px; background: #fff; border: 1.5px solid #FCE4EC; border-radius: 14px; padding: 18px 22px; }
.ev-org__avatar { width: 52px; height: 52px; border-radius: 50%; background: linear-gradient(135deg, #F06292, #E91E8C); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: 700; box-shadow: 0 4px 14px rgba(233,30,140,.35); flex-shrink: 0; }
.ev-org__info { flex: 1; }
.ev-org__lbl { font-size: 11px; color: #9e6878; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
.ev-org__name { font-family: 'Playfair Display', serif; font-size: 18px; font-weight: 700; color: #1a0a12; margin-top: 2px; }

.ev-footer { background: #1a0a12; padding: 24px 0; }
.ev-footer__bot { display: flex; justify-content: space-between; align-items: center; font-size: 13px; color: #5e2b3d; }
.ev-footer__made { color: #F48FB1; }

@media (max-width: 1024px) {
  .ev-grid { grid-template-columns: 1fr; }
  .ev-side { position: static; }
  .ev-info-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
  .ev-nav { padding: 0 16px; }
  .ev-nav__crumb { display: none; }
  .ev-wrap { padding: 0 20px; }
  .ev-hero { padding: 60px 20px 40px; min-height: 380px; }
  .ev-hero__title { font-size: 30px; }
  .ev-hero__metas { gap: 14px; }
  .ev-hero__countdown { margin-left: 0; }
  .ev-main { padding: 32px 20px 40px; }
  .ev-info-grid { grid-template-columns: 1fr 1fr; }
  .ev-desc { padding: 22px; }
  .ev-toast { right: 16px; left: 16px; min-width: auto; }
  .ev-footer__bot { flex-direction: column; gap: 6px; text-align: center; }
}
</style>