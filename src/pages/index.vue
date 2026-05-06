<route lang="yaml">
meta:
  layout: blank
  public: true
</route>

<script setup lang="ts">
definePage({ meta: { layout: 'blank', public: true } })
import { ref, computed, onMounted, onUnmounted } from 'vue'
defineOptions({ name: 'HomePage' })

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'
const router = useRouter()

const events           = ref<any[]>([])
const featuredEvents   = ref<any[]>([])
const upcomingEvents   = ref<any[]>([])
const categories       = ref<any[]>([])
const siteSettings     = ref<any>({})
const isLoadingEvents  = ref(false)
const isLoadingCats    = ref(true)
const isLoadingFeat    = ref(true)
const searchQuery      = ref('')
const selectedCity     = ref('')
const selectedCategory = ref<any>(null)
const selectedPrice    = ref('')
const currentPage      = ref(1)
const totalEvents      = ref(0)
const eventsPerPage    = 12
const scrolled         = ref(false)
const heroSlide        = ref(0)
const newsletter       = ref('')
const newsletterMsg    = ref('')
const viewMode         = ref<'home' | 'category' | 'city'>('home')
const stat1 = ref(0); const stat2 = ref(0); const stat3 = ref(0)
const statsAnimated = ref(false)

// ── Apparence (appliqué globalement sur <html>) ──
const showPalette = ref(false)

const themes = [
  { id: 'rose',    label: 'Rose',    p: '#D4215A', pl: '#FF4D7A', pd: '#9B1040', pale: '#FFF0F3', pmuted: '#FCE4EC', rgb: '212,33,90',  drgb: '155,16,64'  },
  { id: 'violet',  label: 'Violet',  p: '#7C3AED', pl: '#9F67FA', pd: '#5B21B6', pale: '#F5F3FF', pmuted: '#EDE9FE', rgb: '124,58,237', drgb: '91,33,182'  },
  { id: 'ocean',   label: 'Océan',   p: '#0369A1', pl: '#0EA5E9', pd: '#075985', pale: '#F0F9FF', pmuted: '#E0F2FE', rgb: '3,105,161',  drgb: '7,89,133'   },
  { id: 'emerald', label: 'Nature',  p: '#059669', pl: '#10B981', pd: '#047857', pale: '#ECFDF5', pmuted: '#D1FAE5', rgb: '5,150,105',  drgb: '4,120,87'   },
  { id: 'sunset',  label: 'Sunset',  p: '#EA580C', pl: '#F97316', pd: '#C2410C', pale: '#FFF7ED', pmuted: '#FFEDD5', rgb: '234,88,12',  drgb: '194,65,12'  },
  { id: 'gold',    label: 'Gold',    p: '#D97706', pl: '#F59E0B', pd: '#B45309', pale: '#FFFBEB', pmuted: '#FEF3C7', rgb: '217,119,6',  drgb: '180,83,9'   },
]
const isDark        = ref(false)
const currentTheme  = ref(themes[0])

// Applique thème + dark sur <html> → toutes les pages en héritent
const applyToDOM = () => {
  const root = document.documentElement
  const t = currentTheme.value
  root.style.setProperty('--accent',      t.p)
  root.style.setProperty('--accent-lt',   t.pl)
  root.style.setProperty('--accent-dk',   t.pd)
  root.style.setProperty('--accent-pale', t.pale)
  root.style.setProperty('--accent-mute', t.pmuted)
  root.style.setProperty('--accent-rgb',  t.rgb)
  root.style.setProperty('--accent-drg',  t.drgb)
  isDark.value ? root.classList.add('dark') : root.classList.remove('dark')
}

const setTheme = (t: typeof themes[0]) => {
  currentTheme.value = t
  localStorage.setItem('el-theme', t.id)
  applyToDOM()
}
const toggleDark = () => {
  isDark.value = !isDark.value
  localStorage.setItem('el-dark', isDark.value ? '1' : '0')
  applyToDOM()
}

const heroSlides = [
  'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=1920&q=90',
  'https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?w=1920&q=90',
  'https://images.unsplash.com/photo-1459749411175-04bf5292ceea?w=1920&q=90',
  'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=1920&q=90',
]

const cities = [
  { name: 'Tunis',    count: 85,  img: 'https://images.unsplash.com/photo-1605216663980-b7ca6e4d11c5?w=800&q=85' },
  { name: 'Sousse',   count: 42,  img: 'https://images.unsplash.com/photo-1568640347023-a616a30bc3bd?w=800&q=85' },
  { name: 'Sfax',     count: 28,  img: 'https://images.unsplash.com/photo-1518730518541-d0843268c287?w=800&q=85' },
  { name: 'Hammamet', count: 36,  img: 'https://images.unsplash.com/photo-1589308078059-be1415eab4c3?w=800&q=85' },
  { name: 'Djerba',   count: 24,  img: 'https://images.unsplash.com/photo-1535359056830-d4badde79747?w=800&q=85' },
  { name: 'Monastir', count: 18,  img: 'https://images.unsplash.com/photo-1562680534-3da4ed25f70c?w=800&q=85' },
]

const siteName = computed(() => siteSettings.value.site_name || 'EventLab')
const totalPages = computed(() => Math.ceil(totalEvents.value / eventsPerPage))
const activeCategoryName = computed(() => selectedCategory.value?.name || '')
const isHomeView = computed(() => viewMode.value === 'home')
const isCategoryView = computed(() => viewMode.value === 'category')

const handleScroll = () => {
  scrolled.value = window.scrollY > 40
  if (!statsAnimated.value) {
    const el = document.querySelector('.el-stats')
    if (el) { const rect = el.getBoundingClientRect(); if (rect.top < window.innerHeight - 80) { animateStats(); statsAnimated.value = true } }
  }
}
const animateStats = () => {
  const go = (r: any, end: number, ms: number) => { let cur = 0; const step = end / (ms / 16); const t = setInterval(() => { cur += step; if (cur >= end) { cur = end; clearInterval(t) } r.value = Math.floor(cur) }, 16) }
  go(stat1, 200, 1400); go(stat2, 50, 1400); go(stat3, 49, 1400)
}
const onClickOutside = (e: MouseEvent) => { const el = document.querySelector('.el-appearance'); if (el && !el.contains(e.target as Node)) showPalette.value = false }

let heroTimer: any = null
const startHero = () => { heroTimer = setInterval(() => { heroSlide.value = (heroSlide.value + 1) % heroSlides.length }, 5000) }

onMounted(() => {
  // Restore preferences and apply on <html>
  isDark.value = localStorage.getItem('el-dark') === '1'
  const saved = localStorage.getItem('el-theme'); if (saved) { const t = themes.find(x => x.id === saved); if (t) currentTheme.value = t }
  applyToDOM() // ← applique sur <html> dès le chargement
  window.addEventListener('scroll', handleScroll)
  document.addEventListener('click', onClickOutside)
  fetchSettings(); fetchCategories(); fetchFeaturedEvents(); fetchUpcomingEvents(); startHero(); setTimeout(handleScroll, 500)
})
onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
  document.removeEventListener('click', onClickOutside)
  if (heroTimer) clearInterval(heroTimer)
})

const fetchSettings = async () => { try { const r = await fetch(`${API_BASE_URL}/cms/settings/`); if (r.ok) siteSettings.value = await r.json() } catch {} }
const fetchCategories = async () => { isLoadingCats.value = true; try { const r = await fetch(`${API_BASE_URL}/events/categories/`); const d = await r.json(); categories.value = d.results || d || [] } catch { categories.value = [] } finally { isLoadingCats.value = false } }
const fetchFeaturedEvents = async () => { isLoadingFeat.value = true; try { const r = await fetch(`${API_BASE_URL}/events/?is_featured=true&page_size=6`); const d = await r.json(); featuredEvents.value = (d.results || d || []).slice(0, 6) } catch { featuredEvents.value = [] } finally { isLoadingFeat.value = false } }
const fetchUpcomingEvents = async () => { try { const r = await fetch(`${API_BASE_URL}/events/?page_size=8`); const d = await r.json(); upcomingEvents.value = (d.results || d || []).slice(0, 8) } catch { upcomingEvents.value = [] } }
const fetchEventsByCategory = async (catId: any) => { isLoadingEvents.value = true; try { const p = new URLSearchParams(); p.append('category', String(catId)); if (searchQuery.value) p.append('search', searchQuery.value); if (selectedPrice.value === 'free') p.append('is_free', 'true'); else if (selectedPrice.value === 'paid') p.append('is_free', 'false'); p.append('page', currentPage.value.toString()); p.append('page_size', eventsPerPage.toString()); const r = await fetch(`${API_BASE_URL}/events/?${p}`); const d = await r.json(); events.value = d.results || d || []; totalEvents.value = d.count || events.value.length } catch { events.value = [] } finally { isLoadingEvents.value = false } }
const fetchEventsByCity = async (city: string) => { isLoadingEvents.value = true; try { const p = new URLSearchParams(); p.append('search', city); p.append('page', currentPage.value.toString()); p.append('page_size', eventsPerPage.toString()); const r = await fetch(`${API_BASE_URL}/events/?${p}`); const d = await r.json(); events.value = d.results || d || []; totalEvents.value = d.count || events.value.length } catch { events.value = [] } finally { isLoadingEvents.value = false } }

const selectCategory = (cat: any) => { selectedCategory.value = cat; selectedCity.value = ''; viewMode.value = 'category'; currentPage.value = 1; fetchEventsByCategory(cat.id); window.scrollTo({ top: 0, behavior: 'smooth' }) }
const selectCity = (c: string) => { selectedCity.value = c; selectedCategory.value = null; viewMode.value = 'city'; currentPage.value = 1; fetchEventsByCity(c); window.scrollTo({ top: 0, behavior: 'smooth' }) }
const goHome = () => { selectedCategory.value = null; selectedCity.value = ''; viewMode.value = 'home'; events.value = []; searchQuery.value = ''; selectedPrice.value = '' }
const goToEvent = (id: number) => router.push(`/events/${id}`)
const goToLogin = () => router.push('/login')
const goToRegister = () => router.push('/register')
const subscribeNewsletter = () => { if (!newsletter.value.includes('@')) { newsletterMsg.value = '⚠️ Email invalide'; return } newsletterMsg.value = '✨ Merci, vous êtes inscrit(e) !'; newsletter.value = ''; setTimeout(() => newsletterMsg.value = '', 4000) }
const formatDate = (d: string) => { if (!d) return ''; return new Date(d).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' }) }
const getDateParts = (d: string) => { if (!d) return { day: '--', month: '---' }; const dt = new Date(d); return { day: dt.getDate().toString().padStart(2, '0'), month: dt.toLocaleDateString('fr-FR', { month: 'short' }).toUpperCase().replace('.', '') } }
const formatPrice = (price: any, isFree?: boolean) => { if (isFree || !price || price === '0.000' || price === 0) return 'Gratuit'; return `${Number(price).toFixed(0)} DT` }
const getEventImage = (e: any) => e.cover_image || e.image || e.banner || e.cover || null
const isPriceFree = (e: any) => !e.price || e.price === '0.000' || e.price === 0 || e.is_free

const catIcons: Record<string, string> = { musique: '🎵', music: '🎵', sport: '⚽', sports: '⚽', technologie: '💻', technology: '💻', 'arts': '🎨', culture: '🎨', food: '🍽️', gastronomie: '🍽️', business: '💼', conférence: '💼', festival: '🎪', cinéma: '🎬', cinema: '🎬', théâtre: '🎭', theatre: '🎭', spectacle: '🎭', comedy: '😂', humour: '😂', mode: '👗', fashion: '👗', gaming: '🎮', santé: '🏥', education: '🎓', voyage: '✈️', science: '🔬', clubbing: '🎧', nightlife: '🎧' }
const getCatIcon = (name: string) => { const n = name.toLowerCase(); for (const [k, v] of Object.entries(catIcons)) { if (n.includes(k)) return v } return '🎯' }
const catImgs: Record<string, string> = { musique: 'https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?w=600', sport: 'https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?w=600', technologie: 'https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=600', 'arts': 'https://images.unsplash.com/photo-1460661419201-fd4cecdf8a8b?w=600', food: 'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=600', business: 'https://images.unsplash.com/photo-1515187029135-18ee286d815b?w=600', festival: 'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=600', cinema: 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=600', theatre: 'https://images.unsplash.com/photo-1503095396549-807759245b35?w=600', comedy: 'https://images.unsplash.com/photo-1527224538127-2104bb71c51b?w=600', spectacle: 'https://images.unsplash.com/photo-1501386761578-eac5c94b800a?w=600', mode: 'https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=600', gaming: 'https://images.unsplash.com/photo-1542751371-adc38448a05e?w=600', clubbing: 'https://images.unsplash.com/photo-1571266028243-e4733b0f0bb0?w=600' }
const getCatImg = (cat: any) => { if (cat.image || cat.cover || cat.banner) return cat.image || cat.cover || cat.banner; const n = cat.name.toLowerCase(); for (const [k, v] of Object.entries(catImgs)) { if (n.includes(k)) return v } return 'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=600' }
const catsRef = ref<HTMLElement | null>(null)
const scrollLeft = () => catsRef.value?.scrollBy({ left: -340, behavior: 'smooth' })
const scrollRight = () => catsRef.value?.scrollBy({ left: 340, behavior: 'smooth' })
</script>

<template>
  <div class="el" :class="{ dark: isDark }">

    <!-- ══ NAV ══ -->
    <nav class="el-nav" :class="{ 'el-nav--solid': scrolled }">
      <div class="el-nav__inner">
        <div class="el-logo" @click="goHome()">
          <div class="el-logo__gem"><span>{{ siteName[0] }}</span></div>
          <div class="el-logo__text">
            <span class="el-logo__name">{{ siteName }}</span>
            <span class="el-logo__tag">Billetterie Tunisie</span>
          </div>
        </div>
        <div class="el-nav__links" v-if="isHomeView">
          <a href="#events">Événements</a>
          <a href="#categories">Catégories</a>
          <a href="#cities">Villes</a>
          <a href="#how">Comment ça marche</a>
        </div>
        <div class="el-nav__crumb" v-else>
          <button @click="goHome()"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15,18 9,12 15,6"/></svg>Accueil</button>
          <span>/</span>
          <span>{{ isCategoryView ? activeCategoryName : selectedCity }}</span>
        </div>
        <div class="el-nav__actions">
          <!-- Bouton mode sombre/clair -->
          <button class="el-dark-btn" @click="toggleDark" :title="isDark ? 'Mode clair' : 'Mode sombre'">
            <transition name="dm" mode="out-in">
              <span v-if="isDark" key="sun">☀️</span>
              <span v-else key="moon">🌙</span>
            </transition>
          </button>
          <button class="el-btn el-btn--ghost" @click="goToLogin()">Connexion</button>
          <button class="el-btn el-btn--primary" @click="goToRegister()">S'inscrire</button>
        </div>
      </div>
    </nav>

    <!-- ══ PALETTE FLOTTANTE ══ -->
    <div class="el-appearance" @click.stop>
      <transition name="el-panel">
        <div v-if="showPalette" class="el-ap-panel">
          <div class="el-ap-section">
            <div class="el-ap-label">🎨 Couleur du thème</div>
            <div class="el-ap-swatches">
              <button
                v-for="t in themes" :key="t.id"
                class="el-ap-swatch"
                :class="{ active: currentTheme.id === t.id }"
                :style="{ '--sw': t.p, '--sw2': t.pd }"
                :title="t.label"
                @click="setTheme(t)"
              >
                <span v-if="currentTheme.id === t.id">✓</span>
              </button>
            </div>
            <div class="el-ap-names">
              <span v-for="t in themes" :key="t.id" :class="{ active: currentTheme.id === t.id }">{{ t.label }}</span>
            </div>
          </div>
          <div class="el-ap-sep"></div>
          <div class="el-ap-section">
            <div class="el-ap-label">💡 Mode d'affichage</div>
            <div class="el-ap-mode" @click="toggleDark">
              <div class="el-ap-mode-opt" :class="{ active: !isDark }"><span>☀️</span> Clair</div>
              <div class="el-ap-mode-opt" :class="{ active: isDark }"><span>🌙</span> Sombre</div>
            </div>
          </div>
        </div>
      </transition>
      <button class="el-ap-fab" @click="showPalette = !showPalette" :title="showPalette ? 'Fermer' : 'Personnaliser'">
        <transition name="dm" mode="out-in">
          <svg v-if="showPalette" key="x" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          <svg v-else key="pal" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10c0 1.657-1.343 3-3 3h-1.5A1.5 1.5 0 0 0 16 16.5V16a4 4 0 1 0-4 4"/><circle cx="7.5" cy="10.5" r="1" fill="currentColor"/><circle cx="12" cy="7.5" r="1" fill="currentColor"/><circle cx="16.5" cy="10.5" r="1" fill="currentColor"/></svg>
        </transition>
      </button>
    </div>

    <!-- ══════ PAGE HOME ══════ -->
    <div v-if="isHomeView">

      <section class="el-hero">
        <div class="el-hero__bg">
          <div v-for="(s, i) in heroSlides" :key="i" class="el-hero__slide" :class="{ active: i === heroSlide }" :style="{ backgroundImage: `url(${s})` }"></div>
          <div class="el-hero__overlay"></div>
          <div class="el-hero__grain"></div>
        </div>
        <div class="el-hero__orb el-orb1"></div>
        <div class="el-hero__orb el-orb2"></div>
        <div class="el-hero__orb el-orb3"></div>
        <div class="el-hero__content">
          <div class="el-hero__kicker"><span class="el-kicker-dot"></span>Plateforme #1 · Tunisie · {{ categories.length || 18 }} catégories</div>
          <h1 class="el-hero__h1">Vivez<br><em class="el-hero__italic">l'extraordinaire</em></h1>
          <p class="el-hero__sub">Concerts, festivals, théâtre, sport — réservez vos billets en quelques clics.</p>
          <div class="el-hero__dots">
            <button v-for="(_, i) in heroSlides" :key="i" :class="{ active: i === heroSlide }" @click="heroSlide = i"></button>
          </div>
        </div>
        <div class="el-hero__scroll-hint"><span>Défiler</span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12l7 7 7-7"/></svg></div>
      </section>

      <div class="el-search-wrap">
        <div class="el-search-pill">
          <div class="el-search-pill__field">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
            <input v-model="searchQuery" placeholder="Concert, festival, spectacle…" />
          </div>
          <div class="el-search-pill__sep"></div>
          <div class="el-search-pill__field el-search-pill__field--loc">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
            <select v-model="selectedCity">
              <option value="">Toute la Tunisie</option>
              <option v-for="c in cities" :key="c.name" :value="c.name">{{ c.name }}</option>
            </select>
          </div>
          <button class="el-search-pill__btn" @click="selectedCity ? selectCity(selectedCity) : (categories.length && selectCategory(categories[0]))">Rechercher</button>
        </div>
        <div class="el-quick-tags">
          <button v-for="cat in categories.slice(0, 6)" :key="cat.id" class="el-tag" @click="selectCategory(cat)">{{ getCatIcon(cat.name) }} {{ cat.name }}</button>
        </div>
      </div>

      <div class="el-stats" id="stats">
        <div class="el-wrap">
          <div class="el-stats__grid">
            <div class="el-stat"><div class="el-stat__num">{{ categories.length || 18 }}<span class="el-stat__plus">+</span></div><div class="el-stat__lbl">Catégories</div></div>
            <div class="el-stat__div"></div>
            <div class="el-stat"><div class="el-stat__num">{{ stat1 }}<span class="el-stat__plus">+</span></div><div class="el-stat__lbl">Événements</div></div>
            <div class="el-stat__div"></div>
            <div class="el-stat"><div class="el-stat__num">{{ stat2 }}K<span class="el-stat__plus">+</span></div><div class="el-stat__lbl">Participants</div></div>
            <div class="el-stat__div"></div>
            <div class="el-stat"><div class="el-stat__num">4.9<span class="el-stat__plus">★</span></div><div class="el-stat__lbl">Note moyenne</div></div>
          </div>
        </div>
      </div>

      <section class="el-sec" id="events" v-if="featuredEvents.length > 0 || isLoadingFeat">
        <div class="el-wrap">
          <div class="el-sec-head">
            <div class="el-sec-head__left"><span class="el-label">🔥 Cette semaine</span><h2 class="el-sec-title">Événements vedettes</h2></div>
            <p class="el-sec-desc">Les plus populaires du moment</p>
          </div>
          <div v-if="isLoadingFeat" class="el-bento"><div v-for="i in 5" :key="i" class="el-bento__skel" :class="i === 1 ? 'el-bento__skel--big' : ''"></div></div>
          <div v-else-if="featuredEvents.length > 0" class="el-bento">
            <div v-for="(ev, i) in featuredEvents.slice(0, 5)" :key="ev.id" class="el-bento__card" :class="i === 0 ? 'el-bento__card--hero' : i <= 2 ? 'el-bento__card--med' : 'el-bento__card--sm'" @click="goToEvent(ev.id)">
              <img v-if="getEventImage(ev)" :src="getEventImage(ev)" :alt="ev.title" />
              <div v-else class="el-bento__ph">{{ getCatIcon('festival') }}</div>
              <div class="el-bento__overlay"></div>
              <div class="el-bento__rank">#{{ i + 1 }}</div>
              <div class="el-bento__price" :class="{ free: isPriceFree(ev) }">{{ formatPrice(ev.price, ev.is_free) }}</div>
              <div class="el-bento__info">
                <p class="el-bento__date">{{ formatDate(ev.start_date) }}</p>
                <h3 class="el-bento__title">{{ ev.title }}</h3>
                <span v-if="ev.location_address" class="el-bento__loc"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>{{ ev.location_address }}</span>
              </div>
              <div class="el-bento__hover">Voir l'événement →</div>
            </div>
          </div>
        </div>
      </section>

      <section class="el-sec el-sec--dark" id="categories">
        <div class="el-wrap">
          <div class="el-sec-head">
            <div class="el-sec-head__left"><span class="el-label el-label--light">Explorer par</span><h2 class="el-sec-title el-sec-title--light">Catégories</h2></div>
            <div class="el-cats-nav">
              <button @click="scrollLeft"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15,18 9,12 15,6"/></svg></button>
              <button @click="scrollRight"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9,18 15,12 9,6"/></svg></button>
            </div>
          </div>
        </div>
        <div class="el-cats-scroll" ref="catsRef">
          <div class="el-cats-track">
            <template v-if="isLoadingCats"><div v-for="i in 6" :key="i" class="el-cat-skel"></div></template>
            <template v-else>
              <button v-for="cat in categories" :key="cat.id" class="el-cat" @click="selectCategory(cat)">
                <img :src="getCatImg(cat)" :alt="cat.name" />
                <div class="el-cat__overlay"></div>
                <div class="el-cat__body">
                  <span class="el-cat__icon">{{ getCatIcon(cat.name) }}</span>
                  <h3 class="el-cat__name">{{ cat.name }}</h3>
                  <span class="el-cat__cta">Explorer →</span>
                </div>
              </button>
            </template>
          </div>
        </div>
      </section>

      <section class="el-sec" id="upcoming" v-if="upcomingEvents.length > 0">
        <div class="el-wrap">
          <div class="el-sec-head">
            <div class="el-sec-head__left"><span class="el-label">📅 À venir</span><h2 class="el-sec-title">Prochains événements</h2></div>
            <p class="el-sec-desc">Réservez avant qu'il soit trop tard</p>
          </div>
          <div class="el-evgrid">
            <div v-for="ev in upcomingEvents" :key="ev.id" class="el-evc" @click="goToEvent(ev.id)">
              <div class="el-evc__img">
                <img v-if="getEventImage(ev)" :src="getEventImage(ev)" :alt="ev.title" /><div v-else class="el-evc__ph">{{ getCatIcon('festival') }}</div>
                <div class="el-evc__date-badge"><span class="el-evc__day">{{ getDateParts(ev.start_date).day }}</span><span class="el-evc__month">{{ getDateParts(ev.start_date).month }}</span></div>
                <div class="el-evc__price-tag" :class="{ free: isPriceFree(ev) }">{{ formatPrice(ev.price, ev.is_free) }}</div>
                <div class="el-evc__shine"></div>
              </div>
              <div class="el-evc__body">
                <h3 class="el-evc__title">{{ ev.title }}</h3>
                <p v-if="ev.location_address" class="el-evc__loc"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>{{ ev.location_address }}</p>
                <div class="el-evc__foot"><button class="el-evc__book" @click.stop="goToEvent(ev.id)">Réserver</button></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="el-sec el-sec--cream" id="cities">
        <div class="el-wrap">
          <div class="el-sec-head">
            <div class="el-sec-head__left"><span class="el-label">📍 Près de chez vous</span><h2 class="el-sec-title">Villes populaires</h2></div>
            <p class="el-sec-desc">Cliquez pour explorer les événements</p>
          </div>
          <div class="el-cities">
            <button v-for="city in cities" :key="city.name" class="el-city" @click="selectCity(city.name)">
              <img :src="city.img" :alt="city.name" /><div class="el-city__overlay"></div>
              <div class="el-city__body"><h3 class="el-city__name">{{ city.name }}</h3><span class="el-city__count">{{ city.count }}+ événements</span></div>
              <div class="el-city__arrow">→</div>
            </button>
          </div>
        </div>
      </section>

      <section class="el-sec" id="how">
        <div class="el-wrap">
          <div class="el-sec-head el-sec-head--center"><span class="el-label">Simple & rapide</span><h2 class="el-sec-title">3 étapes pour réserver</h2></div>
          <div class="el-how">
            <div class="el-how__step"><div class="el-how__num">01</div><div class="el-how__icon">🔍</div><h3>Trouvez</h3><p>Parcourez par catégorie, ville ou mot-clé. Filtrez selon vos préférences.</p></div>
            <div class="el-how__line"></div>
            <div class="el-how__step"><div class="el-how__num">02</div><div class="el-how__icon">💳</div><h3>Réservez</h3><p>Paiement 100% sécurisé, aucun frais caché. Confirmation instantanée.</p></div>
            <div class="el-how__line"></div>
            <div class="el-how__step"><div class="el-how__num">03</div><div class="el-how__icon">🎉</div><h3>Profitez</h3><p>E-billet par email, présentez-le à l'entrée et vivez l'expérience.</p></div>
          </div>
        </div>
      </section>

      <section class="el-cta-sec">
        <div class="el-wrap">
          <div class="el-cta">
            <div class="el-cta__img"><img src="https://images.unsplash.com/photo-1511578314322-379afb476865?w=900&q=85" alt="" /><div class="el-cta__img-mask"></div></div>
            <div class="el-cta__content">
              <span class="el-cta__tag">Pour les organisateurs</span>
              <h2 class="el-cta__title">Créez des<br>expériences mémorables</h2>
              <p class="el-cta__sub">Rejoignez {{ siteName }} et vendez vos billets en ligne dès aujourd'hui.</p>
              <ul class="el-cta__list"><li><span>✓</span> Vente de billets en ligne</li><li><span>✓</span> Dashboard analytics temps réel</li><li><span>✓</span> Paiements 100% sécurisés</li><li><span>✓</span> Support 24h/7j</li></ul>
              <div class="el-cta__btns"><button class="el-btn el-btn--white" @click="goToRegister()">Commencer gratuitement →</button><button class="el-btn el-btn--ghost-w" @click="goToLogin()">Se connecter</button></div>
            </div>
          </div>
        </div>
      </section>

      <section class="el-sec">
        <div class="el-wrap">
          <div class="el-sec-head el-sec-head--center"><span class="el-label">💬 Avis</span><h2 class="el-sec-title">Ils nous font confiance</h2></div>
          <div class="el-testis">
            <div class="el-testi"><div class="el-testi__q">"</div><div class="el-testi__stars">★★★★★</div><p>La meilleure plateforme pour découvrir les événements en Tunisie. Interface élégante et réservation ultra simple.</p><div class="el-testi__author"><div class="el-testi__av">SB</div><div><b>Sarra Ben Ali</b><span>Utilisatrice depuis 2024</span></div></div></div>
            <div class="el-testi el-testi--offset"><div class="el-testi__q">"</div><div class="el-testi__stars">★★★★★</div><p>EventLab m'a permis de tripler mes ventes de billets. Le dashboard est complet et intuitif. Recommandé à 100% !</p><div class="el-testi__author"><div class="el-testi__av">MK</div><div><b>Mohamed Khadri</b><span>Organisateur de festivals</span></div></div></div>
            <div class="el-testi"><div class="el-testi__q">"</div><div class="el-testi__stars">★★★★★</div><p>Je trouve toujours des concerts incroyables grâce à EventLab. L'app est moderne et le support très réactif.</p><div class="el-testi__author"><div class="el-testi__av">AT</div><div><b>Amira Trabelsi</b><span>Mélomane passionnée</span></div></div></div>
          </div>
        </div>
      </section>

      <section class="el-newsletter">
        <div class="el-newsletter__bg"></div>
        <div class="el-wrap">
          <div class="el-newsletter__inner">
            <div class="el-newsletter__left"><span class="el-newsletter__icon">📨</span><h2>Restez informé(e)</h2><p>Recevez chaque semaine les meilleurs événements de Tunisie.</p></div>
            <div class="el-newsletter__right">
              <div class="el-newsletter__form"><input v-model="newsletter" type="email" placeholder="votre@email.com" @keyup.enter="subscribeNewsletter" /><button @click="subscribeNewsletter">S'inscrire →</button></div>
              <p v-if="newsletterMsg" class="el-newsletter__msg">{{ newsletterMsg }}</p>
              <p class="el-newsletter__hint">Pas de spam. Désinscription en 1 clic.</p>
            </div>
          </div>
        </div>
      </section>

      <footer class="el-footer">
        <div class="el-wrap">
          <div class="el-footer__top">
            <div class="el-footer__brand">
              <div class="el-logo el-logo--light" @click="goHome()"><div class="el-logo__gem"><span>{{ siteName[0] }}</span></div><div class="el-logo__text"><span class="el-logo__name" style="color:#fff">{{ siteName }}</span><span class="el-logo__tag" style="color:#7a4d5c">Billetterie Tunisie</span></div></div>
              <p class="el-footer__desc">La plateforme #1 pour découvrir et réserver les meilleurs événements de Tunisie.</p>
              <div class="el-footer__socials"><a href="#" aria-label="Facebook">f</a><a href="#" aria-label="Instagram">ig</a><a href="#" aria-label="Twitter">X</a><a href="#" aria-label="LinkedIn">in</a></div>
            </div>
            <div class="el-footer__cols">
              <div><h4>Catégories</h4><a v-for="cat in categories.slice(0,5)" :key="cat.id" @click="selectCategory(cat)">{{ cat.name }}</a></div>
              <div><h4>Villes</h4><a v-for="c in cities.slice(0,5)" :key="c.name" @click="selectCity(c.name)">{{ c.name }}</a></div>
              <div><h4>Légal</h4><a @click="goToLogin()">Connexion</a><a @click="goToRegister()">S'inscrire</a><a href="#">CGU</a><a href="#">Contact</a></div>
            </div>
          </div>
          <div class="el-footer__bot"><span>© 2026 {{ siteName }}. Tous droits réservés.</span><span>Fait avec 💖 en Tunisie</span></div>
        </div>
      </footer>
    </div>

    <!-- ══ VUE CATÉGORIE / VILLE ══ -->
    <div v-else class="el-subpage">
      <div class="el-banner" :style="{ backgroundImage: `url(${isCategoryView ? getCatImg(selectedCategory) : (cities.find(c => c.name === selectedCity)?.img || '')})` }">
        <div class="el-banner__overlay"></div>
        <div class="el-banner__content">
          <button class="el-back" @click="goHome()"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15,18 9,12 15,6"/></svg>Retour</button>
          <span class="el-banner__icon">{{ isCategoryView ? getCatIcon(selectedCategory.name) : '📍' }}</span>
          <h1 class="el-banner__title">{{ isCategoryView ? selectedCategory.name : selectedCity }}</h1>
          <p class="el-banner__count">{{ totalEvents }} événement{{ totalEvents !== 1 ? 's' : '' }}</p>
        </div>
      </div>
      <div class="el-wrap" style="padding: 48px 48px 80px">
        <div class="el-filters">
          <div class="el-filter-search"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg><input v-model="searchQuery" placeholder="Rechercher…" @keyup.enter="currentPage = 1; isCategoryView ? fetchEventsByCategory(selectedCategory.id) : fetchEventsByCity(selectedCity)" /></div>
          <select v-model="selectedPrice" class="el-filter-sel" @change="currentPage = 1; isCategoryView ? fetchEventsByCategory(selectedCategory.id) : fetchEventsByCity(selectedCity)"><option value="">Tous les prix</option><option value="free">Gratuit</option><option value="paid">Payant</option></select>
          <button class="el-btn el-btn--primary el-btn--sm" @click="currentPage = 1; isCategoryView ? fetchEventsByCategory(selectedCategory.id) : fetchEventsByCity(selectedCity)">Filtrer</button>
        </div>
        <div v-if="isLoadingEvents" class="el-evgrid"><div v-for="i in 8" :key="i" class="el-evc el-evc--skel"><div class="el-evc__img-skel"></div><div class="el-evc__body-skel"></div></div></div>
        <div v-else-if="events.length === 0" class="el-empty"><span>🔍</span><h3>Aucun événement trouvé</h3><button class="el-btn el-btn--primary" @click="selectedPrice = ''; searchQuery = ''; isCategoryView ? fetchEventsByCategory(selectedCategory.id) : fetchEventsByCity(selectedCity)">Voir tous</button></div>
        <div v-else class="el-evgrid">
          <div v-for="ev in events" :key="ev.id" class="el-evc" @click="goToEvent(ev.id)">
            <div class="el-evc__img">
              <img v-if="getEventImage(ev)" :src="getEventImage(ev)" :alt="ev.title" /><div v-else class="el-evc__ph">🎪</div>
              <div class="el-evc__date-badge"><span class="el-evc__day">{{ getDateParts(ev.start_date).day }}</span><span class="el-evc__month">{{ getDateParts(ev.start_date).month }}</span></div>
              <div class="el-evc__price-tag" :class="{ free: isPriceFree(ev) }">{{ formatPrice(ev.price, ev.is_free) }}</div>
              <div class="el-evc__shine"></div>
            </div>
            <div class="el-evc__body">
              <h3 class="el-evc__title">{{ ev.title }}</h3>
              <p v-if="ev.location_address" class="el-evc__loc"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>{{ ev.location_address }}</p>
              <div class="el-evc__foot"><button class="el-evc__book" @click.stop="goToEvent(ev.id)">Réserver</button></div>
            </div>
          </div>
        </div>
        <div v-if="totalPages > 1" class="el-pages">
          <button :disabled="currentPage === 1" @click="currentPage--; isCategoryView ? fetchEventsByCategory(selectedCategory.id) : fetchEventsByCity(selectedCity)">‹</button>
          <button v-for="p in totalPages" :key="p" :class="{ active: p === currentPage }" @click="currentPage = p; isCategoryView ? fetchEventsByCategory(selectedCategory.id) : fetchEventsByCity(selectedCity)">{{ p }}</button>
          <button :disabled="currentPage === totalPages" @click="currentPage++; isCategoryView ? fetchEventsByCategory(selectedCategory.id) : fetchEventsByCity(selectedCity)">›</button>
        </div>
      </div>
      <footer class="el-footer"><div class="el-wrap"><div class="el-footer__bot" style="border:none;padding-top:28px"><span>© 2026 {{ siteName }}. Tous droits réservés.</span><span>Fait avec 💖 en Tunisie</span></div></div></footer>
    </div>

  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400;1,700&family=Jost:wght@300;400;500;600;700&display=swap');

/* Variables GLOBALES sur :root — toutes les pages en héritent */
:root {
  --accent:      #D4215A;
  --accent-lt:   #FF4D7A;
  --accent-dk:   #9B1040;
  --accent-pale: #FFF0F3;
  --accent-mute: #FCE4EC;
  --accent-rgb:  212,33,90;
  --accent-drg:  155,16,64;
  --gold:        #C9956C;
  --gold-lt:     #F0C8A0;
  --bg:          #FFFFFF;
  --bg-alt:      #FDF8F5;
  --card:        #FFFFFF;
  --text:        #1A0A14;
  --muted:       #7A5060;
  --border:      #F0DCE4;
  --dark-bg:     #120810;
  --dark-bg2:    #1E0E18;
}

/* Dark mode — classe ajoutée sur <html> par applyToDOM() */
html.dark {
  --bg:       #0d0709;
  --bg-alt:   #120810;
  --card:     #1a0f13;
  --text:     #f0dde5;
  --muted:    #9a7080;
  --border:   #2d1520;
  --dark-bg:  #080405;
  --dark-bg2: #0f0610;
}
</style>

<style scoped>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}

.el {
  font-family: 'Jost', sans-serif;
  color: var(--text);
  background: var(--bg);
  min-height: 100vh;
  transition: background .3s, color .3s;
}

/* ══════════════════════════════════
   PALETTE FLOTTANTE
══════════════════════════════════ */
.el-appearance {
  position: fixed; bottom: 32px; right: 28px; z-index: 1001;
  display: flex; flex-direction: column; align-items: flex-end; gap: 14px;
}
.el-ap-fab {
  width: 54px; height: 54px; border-radius: 17px;
  background: linear-gradient(135deg, var(--accent-lt), var(--accent));
  border: none; color: #fff; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 8px 32px rgba(var(--accent-rgb), .45);
  transition: all .25s;
}
.el-ap-fab:hover { transform: scale(1.1) rotate(12deg); box-shadow: 0 12px 40px rgba(var(--accent-rgb), .6); }

.el-ap-panel {
  background: var(--card);
  border: 1.5px solid var(--border);
  border-radius: 24px;
  padding: 22px 24px;
  width: 248px;
  box-shadow: 0 28px 64px rgba(0,0,0,.2);
}
.el-ap-section { }
.el-ap-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .1em; color: var(--muted); margin-bottom: 14px; }
.el-ap-sep { height: 1px; background: var(--border); margin: 18px 0; }

.el-ap-swatches { display: flex; gap: 10px; justify-content: space-between; margin-bottom: 8px; }
.el-ap-swatch {
  width: 34px; height: 34px; border-radius: 50%;
  background: linear-gradient(135deg, var(--sw), var(--sw2));
  border: 2.5px solid transparent;
  cursor: pointer; transition: all .2s;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; color: #fff; font-weight: 900; outline: none;
}
.el-ap-swatch:hover { transform: scale(1.15); }
.el-ap-swatch.active { border-color: var(--bg); box-shadow: 0 0 0 3px var(--sw); transform: scale(1.18); }

.el-ap-names { display: flex; justify-content: space-between; }
.el-ap-names span { font-size: 9px; color: var(--muted); text-align: center; flex: 1; transition: color .2s; }
.el-ap-names span.active { color: var(--accent); font-weight: 700; }

.el-ap-mode {
  display: flex; background: var(--bg-alt); border-radius: 12px;
  padding: 4px; border: 1.5px solid var(--border); cursor: pointer;
  transition: border-color .2s;
}
.el-ap-mode:hover { border-color: var(--accent); }
.el-ap-mode-opt {
  flex: 1; padding: 9px 4px; border-radius: 9px;
  font-size: 12px; font-weight: 600; text-align: center;
  display: flex; align-items: center; justify-content: center; gap: 5px;
  color: var(--muted); transition: all .25s;
}
.el-ap-mode-opt.active { background: var(--card); color: var(--accent); box-shadow: 0 2px 10px rgba(var(--accent-rgb), .18); }

.el-panel-enter-active { animation: panIn .3s cubic-bezier(.34,1.56,.64,1); }
.el-panel-leave-active { animation: panOut .2s ease; }
@keyframes panIn  { from { opacity:0; transform:translateY(12px) scale(.95) } to { opacity:1; transform:none } }
@keyframes panOut { from { opacity:1; transform:none } to { opacity:0; transform:translateY(8px) scale(.96) } }

/* ══ DARK TOGGLE BUTTON ══ */
.el-dark-btn {
  width: 40px; height: 40px; border-radius: 11px;
  border: 1.5px solid rgba(255,255,255,.3);
  background: rgba(255,255,255,.12); backdrop-filter: blur(10px);
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  font-size: 18px; transition: all .25s; line-height: 1;
}
.el-dark-btn:hover { transform: scale(1.08); }
.el-nav--solid .el-dark-btn { border-color: var(--accent-mute); background: var(--accent-pale); backdrop-filter: none; }
.el.dark .el-nav--solid .el-dark-btn { background: #1e0d14; border-color: #3d1a28; }

.dm-enter-active,.dm-leave-active { transition: all .2s; }
.dm-enter-from { opacity:0; transform:rotate(-90deg) scale(.5); }
.dm-leave-to  { opacity:0; transform:rotate(90deg) scale(.5); }

/* ══ NAV ══ */
.el-nav { position:fixed; top:0; left:0; right:0; z-index:1000; padding:0 48px; transition:all .4s; }
.el-nav--solid { background:var(--card); backdrop-filter:blur(24px) saturate(180%); box-shadow:0 1px 0 rgba(var(--accent-rgb),.1),0 4px 24px rgba(0,0,0,.06); }
.el-nav__inner { max-width:1360px; margin:0 auto; height:76px; display:flex; align-items:center; justify-content:space-between; gap:32px; }
.el-nav__links { display:flex; gap:32px; flex:1; justify-content:center; }
.el-nav__links a { color:rgba(255,255,255,.9); font-size:14px; font-weight:500; text-decoration:none; cursor:pointer; transition:color .2s; text-shadow:0 1px 6px rgba(0,0,0,.4); }
.el-nav--solid .el-nav__links a { color:var(--muted); text-shadow:none; }
.el-nav__links a:hover { color:var(--accent-lt); }
.el-nav--solid .el-nav__links a:hover { color:var(--accent); }
.el-nav__crumb { display:flex; align-items:center; gap:10px; flex:1; }
.el-nav__crumb button { display:flex; align-items:center; gap:6px; background:rgba(var(--accent-rgb),.1); color:var(--accent); border:none; border-radius:8px; padding:6px 14px; font-size:13px; font-weight:600; cursor:pointer; font-family:'Jost',sans-serif; transition:all .2s; }
.el-nav__crumb button:hover { background:rgba(var(--accent-rgb),.18); }
.el-nav__crumb span:first-of-type { color:var(--muted); }
.el-nav__crumb span:last-child { font-weight:700; color:var(--accent); font-size:13px; }
.el-nav__actions { display:flex; gap:10px; align-items:center; }

/* ══ LOGO ══ */
.el-logo { display:flex; align-items:center; gap:12px; cursor:pointer; }
.el-logo__gem { width:42px; height:42px; border-radius:13px; background:linear-gradient(135deg,var(--accent-lt) 0%,var(--accent) 50%,var(--accent-dk) 100%); display:flex; align-items:center; justify-content:center; box-shadow:0 6px 20px rgba(var(--accent-rgb),.4); position:relative; overflow:hidden; }
.el-logo__gem::before { content:''; position:absolute; top:-50%; left:-50%; width:200%; height:200%; background:linear-gradient(135deg,rgba(255,255,255,.3) 0%,transparent 50%); }
.el-logo__gem span { font-family:'Cormorant Garamond',serif; font-weight:700; font-size:20px; color:#fff; position:relative; z-index:1; }
.el-logo__text { display:flex; flex-direction:column; }
.el-logo__name { font-family:'Cormorant Garamond',serif; font-weight:700; font-size:22px; color:#fff; line-height:1.1; text-shadow:0 1px 6px rgba(0,0,0,.4); }
.el-nav--solid .el-logo__name { color:var(--text); text-shadow:none; }
.el-logo__tag { font-size:10px; font-weight:500; color:rgba(255,255,255,.6); letter-spacing:1.5px; text-transform:uppercase; }
.el-nav--solid .el-logo__tag { color:var(--muted); }

/* ══ BUTTONS ══ */
.el-btn { display:inline-flex; align-items:center; gap:7px; border:none; cursor:pointer; border-radius:10px; font-size:14px; font-weight:600; padding:10px 22px; transition:all .25s; font-family:'Jost',sans-serif; line-height:1; white-space:nowrap; }
.el-btn--sm { padding:9px 18px; font-size:13px; }
.el-btn--primary { background:linear-gradient(135deg,var(--accent-lt),var(--accent)); color:#fff; box-shadow:0 4px 18px rgba(var(--accent-rgb),.35); }
.el-btn--primary:hover { transform:translateY(-2px); box-shadow:0 8px 28px rgba(var(--accent-rgb),.5); }
.el-btn--ghost { background:rgba(255,255,255,.15); color:#fff; border:1.5px solid rgba(255,255,255,.3); backdrop-filter:blur(10px); }
.el-btn--ghost:hover { background:rgba(255,255,255,.25); }
.el-nav--solid .el-btn--ghost { background:transparent; color:var(--accent); border-color:var(--accent-mute); backdrop-filter:none; }
.el-nav--solid .el-btn--ghost:hover { background:var(--accent-pale); }
.el-btn--white { background:#fff; color:var(--accent-dk); font-weight:700; box-shadow:0 4px 16px rgba(0,0,0,.12); }
.el-btn--white:hover { background:var(--accent-pale); transform:translateY(-2px); }
.el-btn--ghost-w { background:rgba(255,255,255,.1); color:#fff; border:1.5px solid rgba(255,255,255,.3); }
.el-btn--ghost-w:hover { background:rgba(255,255,255,.2); }

/* ══ HERO ══ */
.el-hero { height:100vh; min-height:600px; max-height:900px; position:relative; display:flex; align-items:center; justify-content:center; overflow:hidden; }
.el-hero__bg { position:absolute; inset:0; }
.el-hero__slide { position:absolute; inset:0; background-size:cover; background-position:center; opacity:0; transition:opacity 1.8s ease; transform:scale(1.05); animation:hzoom 10s ease-out forwards; }
.el-hero__slide.active { opacity:1; }
@keyframes hzoom { 0%{transform:scale(1.05)} 100%{transform:scale(1)} }
.el-hero__overlay { position:absolute; inset:0; background:linear-gradient(160deg,rgba(18,8,16,.92) 0%,rgba(var(--accent-drg),.75) 45%,rgba(18,8,16,.88) 100%); }
.el-hero__grain { position:absolute; inset:0; opacity:.06; background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 512 512' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='1'/%3E%3C/svg%3E"); }
.el-hero__orb { position:absolute; border-radius:50%; filter:blur(100px); pointer-events:none; opacity:.35; }
.el-orb1 { width:500px; height:500px; background:radial-gradient(circle,var(--accent) 0%,transparent 70%); top:-150px; right:-100px; animation:orb1 8s ease-in-out infinite alternate; }
.el-orb2 { width:350px; height:350px; background:radial-gradient(circle,var(--gold) 0%,transparent 70%); bottom:-100px; left:100px; animation:orb2 10s ease-in-out infinite alternate; }
.el-orb3 { width:250px; height:250px; background:radial-gradient(circle,var(--accent-lt) 0%,transparent 70%); top:40%; left:40%; animation:orb1 12s ease-in-out infinite alternate-reverse; }
@keyframes orb1 { 0%{transform:translate(0,0) scale(1)} 100%{transform:translate(40px,-40px) scale(1.1)} }
@keyframes orb2 { 0%{transform:translate(0,0) scale(1)} 100%{transform:translate(-30px,30px) scale(1.08)} }
.el-hero__content { position:relative; z-index:1; text-align:center; max-width:820px; padding:0 24px 80px; }
.el-hero__kicker { display:inline-flex; align-items:center; gap:10px; background:rgba(255,255,255,.1); border:1px solid rgba(255,255,255,.2); border-radius:100px; padding:8px 22px; font-size:12px; font-weight:500; color:rgba(255,255,255,.85); margin-bottom:32px; backdrop-filter:blur(12px); letter-spacing:1.5px; text-transform:uppercase; }
.el-kicker-dot { width:8px; height:8px; border-radius:50%; background:var(--accent-lt); animation:pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.4;transform:scale(.7)} }
.el-hero__h1 { font-family:'Cormorant Garamond',serif; font-size:clamp(52px,7.5vw,110px); font-weight:700; line-height:.95; color:#fff; margin-bottom:24px; letter-spacing:-2px; }
.el-hero__italic { font-style:italic; color:var(--gold-lt); }
.el-hero__sub { font-size:17px; color:rgba(255,255,255,.75); max-width:520px; margin:0 auto 40px; line-height:1.7; font-weight:300; }
.el-hero__dots { display:flex; gap:8px; justify-content:center; }
.el-hero__dots button { width:32px; height:4px; border-radius:2px; background:rgba(255,255,255,.25); border:none; cursor:pointer; transition:all .3s; padding:0; }
.el-hero__dots button.active { background:#fff; width:48px; }
.el-hero__scroll-hint { position:absolute; bottom:36px; left:50%; transform:translateX(-50%); display:flex; flex-direction:column; align-items:center; gap:6px; color:rgba(255,255,255,.5); font-size:11px; letter-spacing:2px; text-transform:uppercase; animation:bounce 2.5s infinite; }
@keyframes bounce { 0%,100%{transform:translateX(-50%) translateY(0)} 50%{transform:translateX(-50%) translateY(10px)} }

/* ══ SEARCH ══ */
.el-search-wrap { position:relative; margin-top:-52px; z-index:5; padding:0 40px; }
.el-search-pill { display:flex; align-items:center; background:var(--card); border-radius:20px; box-shadow:0 20px 60px rgba(0,0,0,.18),0 0 0 1px rgba(var(--accent-rgb),.08); padding:8px; max-width:860px; margin:0 auto; transition:background .3s; }
.el-search-pill__field { display:flex; align-items:center; gap:10px; flex:1; padding:10px 18px; color:var(--accent); }
.el-search-pill__field--loc { flex:0 0 200px; }
.el-search-pill__field input,.el-search-pill__field select { border:none; outline:none; font-size:15px; color:var(--text); width:100%; background:transparent; font-family:'Jost',sans-serif; font-weight:400; transition:color .3s; }
.el-search-pill__field input::placeholder { color:rgba(var(--accent-rgb),.4); }
.el-search-pill__field select { cursor:pointer; }
.el-search-pill__sep { width:1px; height:32px; background:var(--border); flex-shrink:0; }
.el-search-pill__btn { padding:14px 32px; background:linear-gradient(135deg,var(--accent-lt),var(--accent)); border:none; border-radius:14px; color:#fff; font-family:'Jost',sans-serif; font-size:14px; font-weight:700; cursor:pointer; transition:all .25s; white-space:nowrap; box-shadow:0 4px 18px rgba(var(--accent-rgb),.4); }
.el-search-pill__btn:hover { transform:translateY(-1px); box-shadow:0 8px 28px rgba(var(--accent-rgb),.55); }
.el-quick-tags { display:flex; gap:8px; flex-wrap:wrap; max-width:860px; margin:16px auto 0; padding:0 8px; }
.el-tag { padding:7px 16px; background:var(--card); border:1.5px solid var(--border); border-radius:100px; font-size:13px; font-weight:500; color:var(--muted); cursor:pointer; transition:all .2s; font-family:'Jost',sans-serif; }
.el-tag:hover { border-color:var(--accent); color:var(--accent); background:var(--accent-pale); transform:translateY(-2px); box-shadow:0 4px 14px rgba(var(--accent-rgb),.15); }

/* ══ STATS ══ */
.el-stats { padding:60px 0 0; }
.el-stats__grid { display:grid; grid-template-columns:1fr auto 1fr auto 1fr auto 1fr; align-items:center; padding:36px 0; border-top:1px solid var(--border); border-bottom:1px solid var(--border); transition:border-color .3s; }
.el-stat { text-align:center; padding:0 20px; }
.el-stat__num { font-family:'Cormorant Garamond',serif; font-size:48px; font-weight:700; background:linear-gradient(135deg,var(--accent-lt),var(--accent)); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; line-height:1; }
.el-stat__plus { font-size:32px; }
.el-stat__lbl { font-size:12px; color:var(--muted); font-weight:600; letter-spacing:2px; text-transform:uppercase; margin-top:6px; }
.el-stat__div { width:1px; height:48px; background:var(--border); }

/* ══ SECTIONS ══ */
.el-wrap { max-width:1360px; margin:0 auto; padding:0 48px; }
.el-sec { padding:100px 0; background:var(--bg); transition:background .3s; }
.el-sec--dark { background:var(--dark-bg); padding:80px 0 60px; }
.el-sec--cream { background:var(--bg-alt); transition:background .3s; }
.el-sec-head { display:flex; align-items:flex-end; justify-content:space-between; margin-bottom:56px; gap:20px; flex-wrap:wrap; }
.el-sec-head--center { flex-direction:column; align-items:center; text-align:center; }
.el-sec-head__left { display:flex; flex-direction:column; gap:8px; }
.el-label { font-size:11px; font-weight:700; color:var(--accent); letter-spacing:3px; text-transform:uppercase; }
.el-label--light { color:var(--gold-lt); }
.el-sec-title { font-family:'Cormorant Garamond',serif; font-size:clamp(32px,3.5vw,48px); font-weight:700; color:var(--text); line-height:1.05; transition:color .3s; }
.el-sec-title--light { color:#fff; }
.el-sec-desc { font-size:15px; color:var(--muted); max-width:280px; text-align:right; line-height:1.6; font-weight:300; }

/* ══ BENTO ══ */
.el-bento { display:grid; grid-template-columns:repeat(6,1fr); grid-template-rows:300px 220px; gap:14px; }
.el-bento__card--hero { grid-column:span 3; grid-row:span 2; }
.el-bento__card--med  { grid-column:span 3; }
.el-bento__card--sm   { grid-column:span 2; }
.el-bento__card { position:relative; border-radius:20px; overflow:hidden; cursor:pointer; transition:all .4s; box-shadow:0 4px 24px rgba(0,0,0,.12); }
.el-bento__card:hover { transform:scale(.985); box-shadow:0 20px 60px rgba(0,0,0,.25); }
.el-bento__card img { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; transition:transform .6s; }
.el-bento__card:hover img { transform:scale(1.06); }
.el-bento__ph { position:absolute; inset:0; background:linear-gradient(135deg,var(--accent),var(--accent-dk)); display:flex; align-items:center; justify-content:center; font-size:60px; }
.el-bento__overlay { position:absolute; inset:0; background:linear-gradient(to top,rgba(18,8,16,.95) 0%,rgba(18,8,16,.3) 50%,transparent 100%); }
.el-bento__rank { position:absolute; top:16px; left:16px; background:linear-gradient(135deg,var(--gold-lt),var(--gold)); color:#fff; font-family:'Cormorant Garamond',serif; font-size:18px; font-weight:700; padding:5px 14px; border-radius:10px; }
.el-bento__price { position:absolute; top:16px; right:16px; background:var(--accent); color:#fff; font-size:13px; font-weight:700; padding:6px 14px; border-radius:10px; }
.el-bento__price.free { background:#059669; }
.el-bento__info { position:absolute; left:22px; right:22px; bottom:20px; color:#fff; }
.el-bento__date { font-size:11px; color:rgba(255,255,255,.65); margin-bottom:6px; letter-spacing:1px; text-transform:uppercase; }
.el-bento__title { font-family:'Cormorant Garamond',serif; font-size:22px; font-weight:700; line-height:1.2; margin-bottom:8px; text-shadow:0 2px 8px rgba(0,0,0,.4); }
.el-bento__card--hero .el-bento__title { font-size:34px; }
.el-bento__loc { display:flex; align-items:center; gap:5px; font-size:12px; color:rgba(255,255,255,.75); }
.el-bento__hover { position:absolute; inset:0; background:linear-gradient(135deg,rgba(var(--accent-drg),.85),rgba(var(--accent-rgb),.85)); display:flex; align-items:center; justify-content:center; color:#fff; font-size:16px; font-weight:700; letter-spacing:1px; opacity:0; transition:opacity .3s; font-family:'Cormorant Garamond',serif; }
.el-bento__card:hover .el-bento__hover { opacity:1; }
.el-bento__skel { border-radius:20px; background:linear-gradient(90deg,var(--accent-mute) 25%,var(--accent-pale) 50%,var(--accent-mute) 75%); background-size:200% 100%; animation:shimmer 1.4s infinite; }
.el-bento__skel--big { grid-column:span 3; grid-row:span 2; }
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

/* ══ CATS CAROUSEL ══ */
.el-cats-nav { display:flex; gap:10px; }
.el-cats-nav button { width:42px; height:42px; border-radius:50%; border:1.5px solid rgba(255,255,255,.15); background:rgba(255,255,255,.08); color:rgba(255,255,255,.7); cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all .2s; backdrop-filter:blur(10px); }
.el-cats-nav button:hover { background:var(--accent); border-color:var(--accent); color:#fff; transform:scale(1.1); }
.el-cats-scroll { overflow-x:auto; scrollbar-width:none; padding:4px 0 24px; margin-top:8px; }
.el-cats-scroll::-webkit-scrollbar { display:none; }
.el-cats-track { display:flex; gap:16px; padding:0 48px; }
.el-cat { flex:0 0 260px; height:380px; position:relative; border-radius:20px; overflow:hidden; cursor:pointer; border:none; padding:0; transition:all .4s; box-shadow:0 4px 24px rgba(0,0,0,.2); }
.el-cat:hover { transform:translateY(-10px) scale(1.02); box-shadow:0 30px 60px rgba(0,0,0,.35); }
.el-cat img { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; transition:transform .7s; }
.el-cat:hover img { transform:scale(1.12); }
.el-cat__overlay { position:absolute; inset:0; background:linear-gradient(to top,rgba(18,8,16,.96) 0%,rgba(var(--accent-drg),.6) 50%,rgba(var(--accent-rgb),.15) 100%); transition:all .35s; }
.el-cat:hover .el-cat__overlay { background:linear-gradient(to top,rgba(18,8,16,.98),rgba(var(--accent-rgb),.75)); }
.el-cat__body { position:absolute; inset:0; display:flex; flex-direction:column; justify-content:flex-end; padding:28px; z-index:1; text-align:left; }
.el-cat__icon { font-size:42px; margin-bottom:14px; display:block; }
.el-cat__name { font-family:'Cormorant Garamond',serif; font-size:28px; font-weight:700; color:#fff; margin-bottom:12px; }
.el-cat__cta { font-size:13px; font-weight:600; color:var(--gold-lt); letter-spacing:1.5px; text-transform:uppercase; transition:letter-spacing .25s; }
.el-cat:hover .el-cat__cta { letter-spacing:3px; color:#fff; }
.el-cat-skel { flex:0 0 260px; height:380px; border-radius:20px; background:linear-gradient(90deg,#1E0E18 25%,#2d1520 50%,#1E0E18 75%); background-size:200% 100%; animation:shimmer 1.4s infinite; }

/* ══ EVENT CARDS ══ */
.el-evgrid { display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:24px; }
.el-evc { background:var(--card); border-radius:18px; overflow:hidden; cursor:pointer; border:1.5px solid var(--border); transition:all .35s; box-shadow:0 2px 16px rgba(0,0,0,.04); }
.el-evc:hover { transform:translateY(-8px); box-shadow:0 28px 60px rgba(var(--accent-rgb),.15); border-color:rgba(var(--accent-rgb),.3); }
.el-evc__img { position:relative; height:220px; overflow:hidden; }
.el-evc__img img { width:100%; height:100%; object-fit:cover; transition:transform .5s; }
.el-evc:hover .el-evc__img img { transform:scale(1.07); }
.el-evc__ph { width:100%; height:100%; display:flex; align-items:center; justify-content:center; background:linear-gradient(135deg,var(--accent-mute),var(--accent-pale)); font-size:52px; }
.el-evc__shine { position:absolute; inset:0; background:linear-gradient(135deg,rgba(255,255,255,.2) 0%,transparent 50%,rgba(0,0,0,.1) 100%); opacity:0; transition:opacity .3s; }
.el-evc:hover .el-evc__shine { opacity:1; }
.el-evc__date-badge { position:absolute; top:14px; left:14px; background:rgba(255,255,255,.97); backdrop-filter:blur(12px); border-radius:12px; padding:7px 13px; display:flex; flex-direction:column; align-items:center; min-width:52px; box-shadow:0 4px 16px rgba(0,0,0,.15); }
.el-evc__day { font-family:'Cormorant Garamond',serif; font-size:24px; font-weight:700; color:var(--accent); line-height:1; }
.el-evc__month { font-size:10px; font-weight:700; color:var(--accent-dk); letter-spacing:1px; margin-top:2px; }
.el-evc__price-tag { position:absolute; bottom:14px; right:14px; background:var(--accent); color:#fff; border-radius:8px; padding:5px 13px; font-size:12px; font-weight:700; }
.el-evc__price-tag.free { background:#059669; }
.el-evc__body { padding:18px 20px; }
.el-evc__title { font-family:'Cormorant Garamond',serif; font-size:19px; font-weight:700; color:var(--text); margin-bottom:10px; line-height:1.25; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; transition:color .3s; }
.el-evc__loc { display:flex; align-items:center; gap:5px; font-size:12px; color:var(--muted); margin-bottom:14px; font-weight:300; }
.el-evc__foot { display:flex; justify-content:flex-end; padding-top:12px; border-top:1px solid var(--border); transition:border-color .3s; }
.el-evc__book { padding:9px 20px; background:linear-gradient(135deg,var(--accent-lt),var(--accent)); color:#fff; border:none; border-radius:10px; font-size:13px; font-weight:600; cursor:pointer; font-family:'Jost',sans-serif; transition:all .2s; box-shadow:0 3px 12px rgba(var(--accent-rgb),.25); }
.el-evc__book:hover { transform:translateY(-1px); box-shadow:0 6px 18px rgba(var(--accent-rgb),.45); }
.el-evc--skel .el-evc__img-skel { height:220px; background:linear-gradient(90deg,var(--accent-pale) 25%,var(--accent-mute) 50%,var(--accent-pale) 75%); background-size:200% 100%; animation:shimmer 1.4s infinite; }
.el-evc--skel .el-evc__body-skel { height:100px; background:linear-gradient(90deg,var(--accent-pale) 25%,var(--accent-mute) 50%,var(--accent-pale) 75%); background-size:200% 100%; animation:shimmer 1.4s infinite; margin:12px; border-radius:8px; }

/* ══ CITIES ══ */
.el-cities { display:grid; grid-template-columns:repeat(3,1fr); gap:16px; }
.el-city { position:relative; border-radius:18px; overflow:hidden; height:210px; cursor:pointer; border:none; padding:0; transition:all .4s; box-shadow:0 4px 20px rgba(0,0,0,.1); }
.el-city:hover { transform:translateY(-6px) scale(1.01); box-shadow:0 24px 56px rgba(0,0,0,.22); }
.el-city img { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; transition:transform .6s; }
.el-city:hover img { transform:scale(1.08); }
.el-city__overlay { position:absolute; inset:0; background:linear-gradient(to top,rgba(18,8,16,.9) 0%,rgba(18,8,16,.3) 50%,transparent 100%); }
.el-city__body { position:absolute; left:22px; bottom:18px; color:#fff; z-index:1; }
.el-city__name { font-family:'Cormorant Garamond',serif; font-size:26px; font-weight:700; margin-bottom:4px; }
.el-city__count { font-size:12px; color:rgba(255,255,255,.75); font-weight:500; }
.el-city__arrow { position:absolute; top:16px; right:16px; width:38px; height:38px; border-radius:50%; background:rgba(255,255,255,.15); backdrop-filter:blur(8px); border:1px solid rgba(255,255,255,.25); display:flex; align-items:center; justify-content:center; color:#fff; font-size:18px; transition:all .3s; }
.el-city:hover .el-city__arrow { background:var(--accent); border-color:var(--accent); transform:translateX(4px); }

/* ══ HOW IT WORKS ══ */
.el-how { display:grid; grid-template-columns:1fr auto 1fr auto 1fr; align-items:stretch; max-width:1000px; margin:0 auto; }
.el-how__step { background:var(--card); border:1.5px solid var(--border); border-radius:24px; padding:40px 32px; text-align:center; position:relative; transition:all .35s; box-shadow:0 4px 20px rgba(0,0,0,.04); }
.el-how__step:hover { transform:translateY(-8px); border-color:rgba(var(--accent-rgb),.3); box-shadow:0 20px 50px rgba(var(--accent-rgb),.12); }
.el-how__num { position:absolute; top:-16px; left:50%; transform:translateX(-50%); background:linear-gradient(135deg,var(--accent-lt),var(--accent)); color:#fff; padding:6px 18px; border-radius:100px; font-family:'Cormorant Garamond',serif; font-size:15px; font-weight:700; letter-spacing:1px; box-shadow:0 4px 16px rgba(var(--accent-rgb),.4); }
.el-how__icon { width:80px; height:80px; border-radius:22px; margin:14px auto 22px; background:linear-gradient(135deg,var(--accent-mute),var(--accent-pale)); display:flex; align-items:center; justify-content:center; font-size:38px; }
.el-how__step h3 { font-family:'Cormorant Garamond',serif; font-size:24px; font-weight:700; color:var(--text); margin-bottom:12px; transition:color .3s; }
.el-how__step p { font-size:14px; color:var(--muted); line-height:1.7; font-weight:300; }
.el-how__line { display:flex; align-items:center; padding:0 8px; color:var(--border); font-size:28px; }

/* ══ CTA ORGANIZERS ══ */
.el-cta-sec { padding:100px 0; }
.el-cta { display:grid; grid-template-columns:1fr 1fr; border-radius:28px; overflow:hidden; box-shadow:0 40px 100px rgba(0,0,0,.2); }
.el-cta__img { position:relative; min-height:520px; }
.el-cta__img img { width:100%; height:100%; object-fit:cover; }
.el-cta__img-mask { position:absolute; inset:0; background:linear-gradient(135deg,rgba(var(--accent-drg),.35),rgba(var(--accent-rgb),.2)); }
.el-cta__content { background:linear-gradient(155deg,#1E0E18 0%,#120810 100%); padding:60px 56px; display:flex; flex-direction:column; justify-content:center; position:relative; overflow:hidden; }
.el-cta__content::before { content:''; position:absolute; top:-100px; right:-100px; width:400px; height:400px; border-radius:50%; background:radial-gradient(circle,rgba(var(--accent-rgb),.2) 0%,transparent 70%); pointer-events:none; }
.el-cta__tag { display:inline-block; background:rgba(240,200,160,.15); color:var(--gold-lt); border:1px solid rgba(240,200,160,.25); border-radius:100px; padding:7px 18px; font-size:12px; font-weight:600; margin-bottom:24px; letter-spacing:1.5px; text-transform:uppercase; width:fit-content; }
.el-cta__title { font-family:'Cormorant Garamond',serif; font-size:42px; font-weight:700; color:#fff; line-height:1.1; margin-bottom:18px; }
.el-cta__sub { color:rgba(255,255,255,.6); font-size:15px; line-height:1.7; margin-bottom:28px; font-weight:300; }
.el-cta__list { list-style:none; display:flex; flex-direction:column; gap:12px; margin-bottom:32px; }
.el-cta__list li { display:flex; align-items:center; gap:12px; font-size:14px; color:rgba(255,255,255,.8); }
.el-cta__list li span { width:22px; height:22px; border-radius:50%; background:rgba(240,200,160,.2); color:var(--gold-lt); display:flex; align-items:center; justify-content:center; font-size:11px; font-weight:700; flex-shrink:0; }
.el-cta__btns { display:flex; gap:12px; flex-wrap:wrap; }

/* ══ TESTIMONIALS ══ */
.el-testis { display:grid; grid-template-columns:repeat(3,1fr); gap:24px; align-items:start; }
.el-testi { background:var(--card); border:1.5px solid var(--border); border-radius:20px; padding:36px 28px 28px; position:relative; transition:all .3s; box-shadow:0 4px 20px rgba(0,0,0,.04); }
.el-testi--offset { margin-top:40px; }
.el-testi:hover { transform:translateY(-6px); border-color:rgba(var(--accent-rgb),.3); box-shadow:0 20px 50px rgba(var(--accent-rgb),.12); }
.el-testi__q { position:absolute; top:-22px; left:24px; width:52px; height:52px; border-radius:14px; background:linear-gradient(135deg,var(--accent-lt),var(--accent)); display:flex; align-items:flex-start; justify-content:center; padding-top:4px; color:#fff; font-family:'Cormorant Garamond',serif; font-size:52px; font-weight:700; line-height:.9; box-shadow:0 8px 24px rgba(var(--accent-rgb),.35); }
.el-testi__stars { color:#F59E0B; font-size:15px; letter-spacing:2px; margin-bottom:14px; }
.el-testi p { font-size:14px; line-height:1.75; color:var(--muted); margin-bottom:24px; font-weight:300; }
.el-testi__author { display:flex; align-items:center; gap:12px; padding-top:18px; border-top:1px solid var(--border); transition:border-color .3s; }
.el-testi__av { width:44px; height:44px; border-radius:50%; background:linear-gradient(135deg,var(--accent-lt),var(--accent)); color:#fff; display:flex; align-items:center; justify-content:center; font-size:14px; font-weight:700; flex-shrink:0; }
.el-testi__author b { display:block; font-size:14px; font-weight:700; color:var(--text); transition:color .3s; }
.el-testi__author span { display:block; font-size:12px; color:var(--muted); margin-top:2px; }

/* ══ NEWSLETTER ══ */
.el-newsletter { position:relative; padding:80px 0; overflow:hidden; }
.el-newsletter__bg { position:absolute; inset:0; background:linear-gradient(135deg,var(--accent) 0%,var(--accent-dk) 100%); }
.el-newsletter__bg::before { content:''; position:absolute; inset:0; background-image:radial-gradient(circle at 20% 50%,rgba(255,255,255,.12) 0%,transparent 50%),radial-gradient(circle at 80% 50%,rgba(255,255,255,.08) 0%,transparent 50%); }
.el-newsletter__inner { position:relative; z-index:1; display:grid; grid-template-columns:1fr 1fr; align-items:center; gap:60px; }
.el-newsletter__icon { font-size:48px; display:block; margin-bottom:16px; }
.el-newsletter__left h2 { font-family:'Cormorant Garamond',serif; font-size:38px; font-weight:700; color:#fff; margin-bottom:12px; line-height:1.1; }
.el-newsletter__left p { color:rgba(255,255,255,.75); font-size:15px; line-height:1.6; font-weight:300; }
.el-newsletter__form { display:flex; background:rgba(255,255,255,.12); backdrop-filter:blur(20px); border:1.5px solid rgba(255,255,255,.2); border-radius:16px; overflow:hidden; margin-bottom:14px; }
.el-newsletter__form input { flex:1; background:transparent; border:none; outline:none; padding:16px 22px; font-family:'Jost',sans-serif; font-size:15px; color:#fff; }
.el-newsletter__form input::placeholder { color:rgba(255,255,255,.55); }
.el-newsletter__form button { padding:16px 28px; background:rgba(255,255,255,.2); color:#fff; border:none; border-left:1.5px solid rgba(255,255,255,.15); font-family:'Jost',sans-serif; font-size:14px; font-weight:700; cursor:pointer; transition:all .2s; white-space:nowrap; }
.el-newsletter__form button:hover { background:rgba(255,255,255,.3); }
.el-newsletter__msg { color:rgba(255,255,255,.9); font-size:13px; font-weight:600; margin-bottom:8px; }
.el-newsletter__hint { color:rgba(255,255,255,.5); font-size:12px; }

/* ══ FOOTER ══ */
.el-footer { background:var(--dark-bg); padding:70px 0 0; transition:background .3s; }
.el-footer__top { display:grid; grid-template-columns:1.5fr 2fr; gap:80px; margin-bottom:56px; }
.el-footer__desc { color:#5e3a4a; font-size:14px; line-height:1.7; max-width:280px; margin:16px 0 20px; font-weight:300; }
.el-footer__socials { display:flex; gap:10px; }
.el-footer__socials a { width:38px; height:38px; border:1px solid #2d1520; border-radius:10px; display:flex; align-items:center; justify-content:center; color:#4a2030; font-size:12px; font-weight:700; text-decoration:none; transition:all .2s; }
.el-footer__socials a:hover { border-color:var(--accent); color:var(--accent); background:rgba(var(--accent-rgb),.08); }
.el-footer__cols { display:grid; grid-template-columns:repeat(3,1fr); gap:36px; }
.el-footer__cols h4 { color:var(--gold-lt); font-size:11px; font-weight:700; letter-spacing:2.5px; text-transform:uppercase; margin-bottom:18px; }
.el-footer__cols a { display:block; color:#5e3a4a; font-size:14px; cursor:pointer; text-decoration:none; margin-bottom:10px; transition:color .2s; background:none; border:none; font-family:'Jost',sans-serif; text-align:left; padding:0; font-weight:300; }
.el-footer__cols a:hover { color:var(--accent-lt); }
.el-footer__bot { display:flex; align-items:center; justify-content:space-between; border-top:1px solid #1E0E18; padding:24px 0; font-size:13px; color:#3a1a28; }
.el-footer__bot span:last-child { color:var(--accent); }

/* ══ SUBPAGE ══ */
.el-banner { min-height:420px; background-size:cover; background-position:center; position:relative; display:flex; align-items:flex-end; padding:140px 48px 60px; }
.el-banner__overlay { position:absolute; inset:0; background:linear-gradient(160deg,rgba(18,8,16,.92),rgba(var(--accent-drg),.75),rgba(18,8,16,.9)); }
.el-banner__content { position:relative; z-index:1; }
.el-back { display:inline-flex; align-items:center; gap:7px; background:rgba(255,255,255,.12); backdrop-filter:blur(10px); border:1px solid rgba(255,255,255,.2); color:#fff; border-radius:10px; padding:8px 18px; font-size:13px; font-weight:600; cursor:pointer; font-family:'Jost',sans-serif; margin-bottom:24px; transition:all .2s; }
.el-back:hover { background:rgba(255,255,255,.22); }
.el-banner__icon { font-size:64px; display:block; margin-bottom:16px; }
.el-banner__title { font-family:'Cormorant Garamond',serif; font-size:64px; font-weight:700; color:#fff; margin-bottom:10px; }
.el-banner__count { color:rgba(255,255,255,.7); font-size:16px; font-weight:400; }
.el-filters { display:flex; align-items:center; gap:12px; flex-wrap:wrap; background:var(--card); border:1.5px solid var(--border); border-radius:16px; padding:14px 20px; margin-bottom:36px; transition:background .3s,border-color .3s; }
.el-filter-search { display:flex; align-items:center; gap:10px; flex:1; min-width:200px; color:var(--accent); }
.el-filter-search input { border:none; outline:none; font-size:14px; color:var(--text); width:100%; background:transparent; font-family:'Jost',sans-serif; transition:color .3s; }
.el-filter-sel { background:var(--accent-pale); border:1.5px solid var(--border); border-radius:10px; padding:9px 16px; font-size:14px; color:var(--accent-dk); cursor:pointer; outline:none; font-family:'Jost',sans-serif; font-weight:500; transition:background .3s; }
.el-empty { text-align:center; padding:100px 20px; }
.el-empty span { font-size:60px; display:block; margin-bottom:20px; }
.el-empty h3 { font-family:'Cormorant Garamond',serif; font-size:28px; color:var(--accent-dk); margin-bottom:20px; }
.el-pages { display:flex; align-items:center; justify-content:center; gap:8px; margin-top:56px; }
.el-pages button { width:42px; height:42px; border-radius:11px; border:1.5px solid var(--border); background:var(--card); font-size:14px; font-weight:600; color:var(--accent); cursor:pointer; transition:all .2s; font-family:'Jost',sans-serif; }
.el-pages button.active,.el-pages button:hover:not(:disabled) { background:linear-gradient(135deg,var(--accent-lt),var(--accent)); color:#fff; border-color:var(--accent); }
.el-pages button:disabled { opacity:.3; cursor:not-allowed; }

/* ══ RESPONSIVE ══ */
@media (max-width:1100px) {
  .el-bento{grid-template-columns:repeat(2,1fr);grid-template-rows:auto;height:auto}
  .el-bento__card--hero{grid-column:span 2;height:360px}
  .el-bento__card--med,.el-bento__card--sm{grid-column:span 1;height:260px}
  .el-cta{grid-template-columns:1fr}.el-cta__img{min-height:300px}.el-cta__content{padding:48px 40px}
  .el-footer__top{grid-template-columns:1fr;gap:40px}
  .el-testis{grid-template-columns:1fr}.el-testi--offset{margin-top:0}
  .el-newsletter__inner{grid-template-columns:1fr;gap:40px;text-align:center}
  .el-newsletter__icon{margin:0 auto 16px;display:block}
}
@media (max-width:768px) {
  .el-nav{padding:0 24px}.el-nav__links{display:none}.el-nav__actions .el-btn--ghost{display:none}
  .el-wrap{padding:0 24px}.el-hero__h1{font-size:52px}
  .el-search-wrap{padding:0 24px}.el-search-pill{flex-direction:column;align-items:stretch;padding:12px;gap:4px}
  .el-search-pill__sep{display:none}.el-search-pill__field--loc{flex:auto}.el-search-pill__btn{width:100%;justify-content:center}
  .el-stats__grid{grid-template-columns:repeat(2,1fr);gap:20px}.el-stat__div{display:none}
  .el-sec{padding:72px 0}.el-sec-head{flex-direction:column;align-items:flex-start}.el-sec-desc{text-align:left;max-width:100%}
  .el-bento{grid-template-columns:1fr}.el-bento__card--hero,.el-bento__card--med,.el-bento__card--sm{grid-column:span 1;height:260px}
  .el-cats-track{padding:0 24px}.el-cat{flex:0 0 220px;height:320px}
  .el-evgrid{grid-template-columns:1fr}.el-cities{grid-template-columns:1fr}
  .el-how{grid-template-columns:1fr}.el-how__line{transform:rotate(90deg);padding:8px 0;justify-content:center}
  .el-footer__cols{grid-template-columns:1fr 1fr;gap:24px}.el-footer__bot{flex-direction:column;gap:8px;text-align:center}
  .el-banner{padding:120px 24px 48px}.el-banner__title{font-size:44px}
  .el-cta__content{padding:36px 28px}.el-cta__title{font-size:32px}
  .el-appearance{bottom:20px;right:16px}
}
</style>