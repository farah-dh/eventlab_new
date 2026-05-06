<route lang="yaml">
meta:
  layout: blank
  public: true
</route>

<script setup lang="ts">
definePage({ meta: { layout: 'blank', public: true } })
import { ref, computed, onMounted, onUnmounted } from 'vue'
import LoginModal from '@/components/LoginModal.vue'
defineOptions({ name: 'HomePage' })

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'
const router = useRouter()

const showLoginModal = ref(false)
const events           = ref<any[]>([])
const featuredEvents   = ref<any[]>([])
const upcomingEvents   = ref<any[]>([])
const categories       = ref<any[]>([])
const siteSettings     = ref<any>({})
const isLoadingEvents  = ref(false)
const isLoadingCats    = ref(true)
const isLoadingFeat    = ref(true)
const searchQuery      = ref('')
const selectedCategory = ref<any>(null)
const selectedPrice    = ref('')
const currentPage      = ref(1)
const totalEvents      = ref(0)
const eventsPerPage    = 12
const scrolled         = ref(false)
const heroSlide        = ref(0)
const newsletter       = ref('')
const newsletterMsg    = ref('')

// ── Apparence ──
const isDark      = ref(false)
const showPalette = ref(false)

const themes = [
  { id: 'rose',    label: 'Rose',    primary: '#E91E8C', dk: '#AD1457', dkr: '#880E4F', lt: '#FCE4EC', lt2: '#F8BBD0', md: '#F48FB1', xlt: '#FFF5F7', rgb: '233,30,140',  dkRgb: '173,20,87'  },
  { id: 'violet',  label: 'Violet',  primary: '#8B5CF6', dk: '#6D28D9', dkr: '#4C1D95', lt: '#EDE9FE', lt2: '#DDD6FE', md: '#A78BFA', xlt: '#F5F3FF', rgb: '139,92,246',  dkRgb: '109,40,217' },
  { id: 'ocean',   label: 'Océan',   primary: '#0EA5E9', dk: '#0369A1', dkr: '#075985', lt: '#E0F2FE', lt2: '#BAE6FD', md: '#38BDF8', xlt: '#F0F9FF', rgb: '14,165,233',  dkRgb: '3,105,161'  },
  { id: 'emerald', label: 'Nature',  primary: '#10B981', dk: '#059669', dkr: '#047857', lt: '#D1FAE5', lt2: '#A7F3D0', md: '#34D399', xlt: '#ECFDF5', rgb: '16,185,129',  dkRgb: '5,150,105'  },
  { id: 'sunset',  label: 'Sunset',  primary: '#F97316', dk: '#EA580C', dkr: '#C2410C', lt: '#FFEDD5', lt2: '#FED7AA', md: '#FB923C', xlt: '#FFF7ED', rgb: '249,115,22',  dkRgb: '234,88,12'  },
  { id: 'gold',    label: 'Gold',    primary: '#F59E0B', dk: '#D97706', dkr: '#B45309', lt: '#FEF3C7', lt2: '#FDE68A', md: '#FCD34D', xlt: '#FFFBEB', rgb: '245,158,11',  dkRgb: '217,119,6'  },
]

const currentTheme = ref(themes[0])

const themeStyle = computed(() => {
  const t = currentTheme.value
  return {
    '--accent':    t.primary,
    '--accent-dk': t.dk,
    '--accent-dkr':t.dkr,
    '--accent-lt': t.lt,
    '--accent-lt2':t.lt2,
    '--accent-md': t.md,
    '--accent-xlt':t.xlt,
    '--accent-rgb':t.rgb,
    '--accent-dk-rgb':t.dkRgb,
  }
})

const setTheme = (t: typeof themes[0]) => {
  currentTheme.value = t
  localStorage.setItem('vp-theme', t.id)
}

const toggleDark = () => {
  isDark.value = !isDark.value
  localStorage.setItem('vp-dark', isDark.value ? '1' : '0')
}

const heroSlides = [
  'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=1920&q=85',
  'https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?w=1920&q=85',
  'https://images.unsplash.com/photo-1459749411175-04bf5292ceea?w=1920&q=85',
  'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=1920&q=85',
]

const siteName   = computed(() => siteSettings.value.site_name || 'EventLab')
const totalPages = computed(() => Math.ceil(totalEvents.value / eventsPerPage))
const activeCategoryName = computed(() => selectedCategory.value?.name || '')
const handleScroll = () => { scrolled.value = window.scrollY > 30 }

let heroInterval: any = null
const startHeroSlider = () => {
  heroInterval = setInterval(() => { heroSlide.value = (heroSlide.value + 1) % heroSlides.length }, 5000)
}

onMounted(() => {
  isDark.value = localStorage.getItem('vp-dark') === '1'
  const savedTheme = localStorage.getItem('vp-theme')
  if (savedTheme) { const t = themes.find(x => x.id === savedTheme); if (t) currentTheme.value = t }
  window.addEventListener('scroll', handleScroll)
  document.addEventListener('click', onClickOutside)
  fetchSettings(); fetchCategories(); fetchFeaturedEvents(); fetchUpcomingEvents(); startHeroSlider()
})
onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
  document.removeEventListener('click', onClickOutside)
  if (heroInterval) clearInterval(heroInterval)
})

const onClickOutside = (e: MouseEvent) => {
  const el = document.querySelector('.vp-appearance-wrap')
  if (el && !el.contains(e.target as Node)) showPalette.value = false
}

const fetchSettings = async () => {
  try { const r = await fetch(`${API_BASE_URL}/cms/settings/`); if (r.ok) siteSettings.value = await r.json() } catch {}
}
const fetchCategories = async () => {
  isLoadingCats.value = true
  try { const r = await fetch(`${API_BASE_URL}/events/categories/`); const d = await r.json(); categories.value = d.results || d || [] }
  catch { categories.value = [] } finally { isLoadingCats.value = false }
}
const fetchFeaturedEvents = async () => {
  isLoadingFeat.value = true
  try { const r = await fetch(`${API_BASE_URL}/events/?is_featured=true&page_size=6`); const d = await r.json(); featuredEvents.value = (d.results || d || []).slice(0, 6) }
  catch { featuredEvents.value = [] } finally { isLoadingFeat.value = false }
}
const fetchUpcomingEvents = async () => {
  try { const r = await fetch(`${API_BASE_URL}/events/?page_size=6`); const d = await r.json(); upcomingEvents.value = (d.results || d || []).slice(0, 6) }
  catch { upcomingEvents.value = [] }
}
const fetchEventsByCategory = async (catId: string | number) => {
  isLoadingEvents.value = true
  try {
    const p = new URLSearchParams()
    p.append('category', String(catId))
    if (searchQuery.value) p.append('search', searchQuery.value)
    if (selectedPrice.value === 'free') p.append('is_free', 'true')
    if (selectedPrice.value === 'paid') p.append('is_free', 'false')
    p.append('page', currentPage.value.toString())
    p.append('page_size', eventsPerPage.toString())
    const r = await fetch(`${API_BASE_URL}/events/?${p}`)
    const d = await r.json()
    events.value = d.results || d || []
    totalEvents.value = d.count || events.value.length
  } catch { events.value = [] } finally { isLoadingEvents.value = false }
}

const selectCategory = (cat: any) => { selectedCategory.value = cat; currentPage.value = 1; fetchEventsByCategory(cat.id); window.scrollTo({ top: 0, behavior: 'smooth' }) }
const backToCategories = () => { selectedCategory.value = null; events.value = []; searchQuery.value = ''; selectedPrice.value = '' }
const goToEvent    = (id: number) => router.push(`/events/${id}`)
const goToLogin    = () => { showLoginModal.value = true }
const goToRegister = () => router.push('/register')

const subscribeNewsletter = () => {
  if (!newsletter.value || !newsletter.value.includes('@')) { newsletterMsg.value = 'Email invalide'; return }
  newsletterMsg.value = '✨ Merci ! Vous êtes inscrit(e) à notre newsletter'
  newsletter.value = ''
  setTimeout(() => newsletterMsg.value = '', 4000)
}

const formatDate  = (d: string) => { if (!d) return ''; return new Date(d).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' }) }
const formatPrice = (price: any, isFree?: boolean) => { if (isFree || !price || price === '0.000' || price === 0) return 'Gratuit'; return `${Number(price).toFixed(0)} DT` }
const getEventImage = (e: any) => e.image || e.banner || e.cover || null
const isPriceFree   = (e: any) => !e.price || e.price === '0.000' || e.price === 0 || e.is_free

const catConfigs = [
  { emoji: '🎵', img: 'https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?w=800&q=85', keywords: ['music','musique','concert'] },
  { emoji: '⚽', img: 'https://images.unsplash.com/photo-1508098682722-e99c643e7f0b?w=800&q=85', keywords: ['sport','sports','football'] },
  { emoji: '💻', img: 'https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800&q=85', keywords: ['tech','technology','it','informatique'] },
  { emoji: '🎨', img: 'https://images.unsplash.com/photo-1460661419201-fd4cecdf8a8b?w=800&q=85', keywords: ['art','arts','culture','expo','peinture'] },
  { emoji: '🍽️', img: 'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=800&q=85', keywords: ['food','nourriture','gastronomie','drink','boisson'] },
  { emoji: '💼', img: 'https://images.unsplash.com/photo-1515187029135-18ee286d815b?w=800&q=85', keywords: ['business','affaires','entreprise'] },
  { emoji: '🎪', img: 'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=800&q=85', keywords: ['festival'] },
  { emoji: '🎬', img: 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=800&q=85', keywords: ['cinema','cinéma','film'] },
  { emoji: '🎭', img: 'https://images.unsplash.com/photo-1503095396549-807759245b35?w=800&q=85', keywords: ['theatre','théâtre','spectacle','show'] },
  { emoji: '😂', img: 'https://images.unsplash.com/photo-1527224538127-2104bb71c51b?w=800&q=85', keywords: ['comedy','comédie','comedie','humour','humor'] },
  { emoji: '👗', img: 'https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=800&q=85', keywords: ['fashion','mode','vêtement'] },
  { emoji: '🎮', img: 'https://images.unsplash.com/photo-1542751371-adc38448a05e?w=800&q=85', keywords: ['gaming','game','jeu','esport','jeux'] },
  { emoji: '🏥', img: 'https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=800&q=85', keywords: ['health','santé','bien-être','wellness'] },
  { emoji: '🎓', img: 'https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=800&q=85', keywords: ['education','éducation','formation','school'] },
  { emoji: '✈️', img: 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800&q=85', keywords: ['travel','voyage','tourisme'] },
  { emoji: '🔬', img: 'https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=800&q=85', keywords: ['science','recherche'] },
  { emoji: '📚', img: 'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=800&q=85', keywords: ['livre','lecture','book','littérature'] },
  { emoji: '💃', img: 'https://images.unsplash.com/photo-1535525153412-5a42439a210d?w=800&q=85', keywords: ['danse','dance'] },
]
const getCatCfg   = (name: string) => { const n = (name||'').toLowerCase(); return catConfigs.find(c=>c.keywords.some(k=>n.includes(k)))||{emoji:'🎯',img:'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=800&q=85'} }
const getCatImage = (cat: any) => cat.image||cat.cover||cat.banner||getCatCfg(cat.name).img
</script>

<template>
  <div class="vp" :class="{ dark: isDark }" :style="themeStyle">

    <!-- ══ NAV ══ -->
    <nav class="vp-nav" :class="{ scrolled }">
      <div class="vp-nav__inner">
        <div class="vp-logo" @click="backToCategories()">
          <div class="vp-logo__mark">{{ siteName[0] }}</div>
          <span class="vp-logo__name">{{ siteName }}</span>
        </div>
        <div class="vp-nav__links" v-if="!selectedCategory">
          <a href="#featured">Vedettes</a>
          <a href="#categories">Catégories</a>
          <a href="#upcoming">Événements</a>
          <a href="#organizers">Organisateurs</a>
        </div>
        <div class="vp-nav__crumb" v-if="selectedCategory">
          <button class="vp-crumb-btn" @click="backToCategories()">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15,18 9,12 15,6"/></svg>
            Accueil
          </button>
          <span class="vp-crumb-sep">/</span>
          <span class="vp-crumb-cur">{{ activeCategoryName }}</span>
        </div>
        <div class="vp-nav__actions">
          <!-- Bouton mode sombre/clair -->
          <button class="vp-dark-toggle" @click="toggleDark" :title="isDark ? 'Mode clair' : 'Mode sombre'">
            <transition name="dm-icon" mode="out-in">
              <span v-if="isDark" key="sun">☀️</span>
              <span v-else key="moon">🌙</span>
            </transition>
          </button>
          <button class="vp-btn vp-ghost" @click="goToLogin()">Connexion</button>
          <button class="vp-btn vp-primary" @click="goToRegister()">S'inscrire</button>
        </div>
      </div>
    </nav>

    <!-- ══ PALETTE FLOTTANTE ══ -->
    <div class="vp-appearance-wrap">
      <transition name="vp-panel">
        <div v-if="showPalette" class="vp-appearance-panel">
          <div class="vp-ap-section">
            <div class="vp-ap-label">🎨 Couleur du thème</div>
            <div class="vp-swatches">
              <button
                v-for="t in themes"
                :key="t.id"
                class="vp-swatch"
                :class="{ active: currentTheme.id === t.id }"
                :style="{ '--sw': t.primary, '--sw2': t.dk }"
                :title="t.label"
                @click="setTheme(t)"
              >
                <span class="vp-swatch__check" v-if="currentTheme.id === t.id">✓</span>
              </button>
            </div>
            <div class="vp-theme-labels">
              <span v-for="t in themes" :key="t.id" :class="{ active: currentTheme.id === t.id }">{{ t.label }}</span>
            </div>
          </div>
          <div class="vp-ap-divider"></div>
          <div class="vp-ap-section">
            <div class="vp-ap-label">💡 Mode d'affichage</div>
            <div class="vp-mode-toggle" @click="toggleDark">
              <div class="vp-mode-option" :class="{ active: !isDark }">
                <span>☀️</span> Clair
              </div>
              <div class="vp-mode-slider" :class="{ dark: isDark }"></div>
              <div class="vp-mode-option" :class="{ active: isDark }">
                <span>🌙</span> Sombre
              </div>
            </div>
          </div>
        </div>
      </transition>
      <button class="vp-appearance-btn" @click.stop="showPalette = !showPalette" :title="showPalette ? 'Fermer' : 'Personnaliser'">
        <transition name="dm-icon" mode="out-in">
          <svg v-if="showPalette" key="x" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          <svg v-else key="pal" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="8" cy="10" r="1.5" fill="currentColor"/><circle cx="12" cy="7" r="1.5" fill="currentColor"/><circle cx="16" cy="10" r="1.5" fill="currentColor"/><path d="M8 16c0-2.2 1.8-4 4-4s4 1.8 4 4" stroke-linecap="round"/></svg>
        </transition>
      </button>
    </div>

    <!-- ══ CONTENU PRINCIPAL ══ -->
    <div v-if="!selectedCategory">

      <section class="vp-hero">
        <div class="vp-hero__slides">
          <div v-for="(slide, i) in heroSlides" :key="i" class="vp-hero__slide" :class="{ active: i === heroSlide }" :style="{ backgroundImage: `url(${slide})` }"></div>
        </div>
        <div class="vp-hero__overlay"></div>
        <div class="vp-hero__content">
          <div class="vp-hero__pill"><span class="vp-dot-anim"></span>Plateforme #1 de billetterie en Tunisie</div>
          <h1 class="vp-hero__h1">Vivez des moments<br><em>inoubliables</em></h1>
          <p class="vp-hero__p">Concerts, festivals, conférences… Découvrez et réservez les meilleurs événements de Tunisie en quelques clics.</p>
          <div class="vp-searchbar">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
            <input v-model="searchQuery" placeholder="Concert, théâtre, sport, festival…" />
            <button class="vp-search-btn" @click="categories.length > 0 && selectCategory(categories[0])">Rechercher</button>
          </div>
          <div class="vp-hero__stats">
            <div class="vp-hstat"><span class="vp-hstat__num">{{ categories.length || 8 }}+</span><span class="vp-hstat__lbl">Catégories</span></div>
            <div class="vp-hstat__sep"></div>
            <div class="vp-hstat"><span class="vp-hstat__num">200+</span><span class="vp-hstat__lbl">Événements</span></div>
            <div class="vp-hstat__sep"></div>
            <div class="vp-hstat"><span class="vp-hstat__num">50K+</span><span class="vp-hstat__lbl">Participants</span></div>
            <div class="vp-hstat__sep"></div>
            <div class="vp-hstat"><span class="vp-hstat__num">4.9★</span><span class="vp-hstat__lbl">Note moyenne</span></div>
          </div>
          <div class="vp-hero__dots">
            <button v-for="(_, i) in heroSlides" :key="i" :class="{ active: i === heroSlide }" @click="heroSlide = i"></button>
          </div>
        </div>
        <div class="vp-hero__scroll"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12l7 7 7-7"/></svg></div>
      </section>

      <section class="vp-sec" id="featured" v-if="featuredEvents.length > 0 || isLoadingFeat">
        <div class="vp-wrap">
          <div class="vp-sec-top">
            <div><p class="vp-eyebrow">⭐ Coup de cœur</p><h2 class="vp-sec-title">Événements vedettes</h2></div>
            <p class="vp-sec-sub">Les événements les plus attendus du moment</p>
          </div>
          <div v-if="isLoadingFeat" class="vp-feat-grid"><div v-for="i in 3" :key="i" class="vp-feat-skel"></div></div>
          <div v-else-if="featuredEvents.length > 0" class="vp-feat-grid">
            <div v-for="(ev, i) in featuredEvents.slice(0, 3)" :key="ev.id" class="vp-feat" :class="{ 'vp-feat--big': i === 0 }" @click="goToEvent(ev.id)">
              <div class="vp-feat__img">
                <img v-if="getEventImage(ev)" :src="getEventImage(ev)" :alt="ev.title" />
                <div v-else class="vp-feat__ph"><span>🎪</span></div>
                <div class="vp-feat__overlay"></div>
                <span class="vp-feat__badge">⭐ Vedette</span>
                <span class="vp-feat__price" :class="{ free: isPriceFree(ev) }">{{ formatPrice(ev.price, ev.is_free) }}</span>
                <div class="vp-feat__info">
                  <h3 class="vp-feat__title">{{ ev.title }}</h3>
                  <div class="vp-feat__metas">
                    <span class="vp-feat__meta"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>{{ formatDate(ev.start_date) }}</span>
                    <span v-if="ev.location_name" class="vp-feat__meta"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>{{ ev.location_name }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="vp-sec vp-sec--alt" id="categories">
        <div class="vp-wrap">
          <div class="vp-sec-top">
            <div><p class="vp-eyebrow">🎯 Explorer par</p><h2 class="vp-sec-title">Catégories</h2></div>
            <p class="vp-sec-sub">Choisissez votre univers et découvrez tous les événements</p>
          </div>
          <div v-if="isLoadingCats" class="vp-cats-grid"><div v-for="i in 8" :key="i" class="vp-cat-skel"></div></div>
          <div v-else class="vp-cats-grid">
            <button v-for="cat in categories" :key="cat.id" class="vp-cat" @click="selectCategory(cat)">
              <img :src="getCatImage(cat)" :alt="cat.name" class="vp-cat__img" />
              <div class="vp-cat__overlay"></div>
              <div class="vp-cat__body">
                <span class="vp-cat__emoji">{{ getCatCfg(cat.name).emoji }}</span>
                <h3 class="vp-cat__name">{{ cat.name }}</h3>
                <div class="vp-cat__cta"><span>Explorer</span><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9,18 15,12 9,6"/></svg></div>
              </div>
            </button>
          </div>
        </div>
      </section>

      <section class="vp-sec" id="upcoming" v-if="upcomingEvents.length > 0">
        <div class="vp-wrap">
          <div class="vp-sec-top">
            <div><p class="vp-eyebrow">📅 Ne manquez pas</p><h2 class="vp-sec-title">Prochains événements</h2></div>
            <p class="vp-sec-sub">Les derniers ajoutés sur la plateforme</p>
          </div>
          <div class="vp-evgrid">
            <div v-for="ev in upcomingEvents" :key="ev.id" class="vp-evc" @click="goToEvent(ev.id)">
              <div class="vp-evc__img">
                <img v-if="getEventImage(ev)" :src="getEventImage(ev)" :alt="ev.title" /><div v-else class="vp-evc__ph"><span>🎪</span></div>
                <span class="vp-evc__price" :class="{ free: isPriceFree(ev) }">{{ formatPrice(ev.price, ev.is_free) }}</span>
                <span v-if="ev.is_featured" class="vp-evc__star">⭐</span>
                <div class="vp-evc__hov">Voir →</div>
              </div>
              <div class="vp-evc__body">
                <h3 class="vp-evc__title">{{ ev.title }}</h3>
                <div class="vp-evc__metas">
                  <span class="vp-evc__meta"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>{{ formatDate(ev.start_date) }}</span>
                  <span v-if="ev.location_name" class="vp-evc__meta"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>{{ ev.location_name }}</span>
                </div>
                <div class="vp-evc__foot">
                  <div class="vp-evc__org" v-if="ev.organizer_name"><div class="vp-evc__av">{{ ev.organizer_name?.[0]?.toUpperCase() }}</div><span>{{ ev.organizer_name }}</span></div>
                  <button class="vp-evc__book">Réserver</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="vp-sec vp-sec--alt" id="organizers">
        <div class="vp-wrap">
          <div class="vp-cta-box">
            <div class="vp-cta-box__img"><img src="https://images.unsplash.com/photo-1511578314322-379afb476865?w=900&q=85" alt="Organisateur" /><div class="vp-cta-box__img-overlay"></div></div>
            <div class="vp-cta-box__content">
              <span class="vp-cta-tag">Pour les organisateurs</span>
              <h2 class="vp-cta-title">Créez et gérez<br>vos événements</h2>
              <p class="vp-cta-sub">Rejoignez des centaines d'organisateurs qui font confiance à {{ siteName }}.</p>
              <div class="vp-cta-features">
                <div class="vp-feat-item"><span class="vp-feat-item__icon">✓</span> Vente de billets en ligne</div>
                <div class="vp-feat-item"><span class="vp-feat-item__icon">✓</span> Dashboard analytics complet</div>
                <div class="vp-feat-item"><span class="vp-feat-item__icon">✓</span> Paiements sécurisés</div>
                <div class="vp-feat-item"><span class="vp-feat-item__icon">✓</span> Support 24/7</div>
              </div>
              <div class="vp-cta-btns">
                <button class="vp-btn vp-white" @click="goToRegister()">Commencer gratuitement →</button>
                <button class="vp-btn vp-ghost-w" @click="goToLogin()">Se connecter</button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="vp-sec">
        <div class="vp-wrap">
          <div class="vp-sec-top vp-sec-top--center"><div><p class="vp-eyebrow">💬 Témoignages</p><h2 class="vp-sec-title">Ils nous font confiance</h2></div></div>
          <div class="vp-testi-grid">
            <div class="vp-testi"><div class="vp-testi__stars">★★★★★</div><p class="vp-testi__text">"La meilleure plateforme pour découvrir les événements en Tunisie. Interface élégante et réservation ultra simple."</p><div class="vp-testi__author"><div class="vp-testi__av">SB</div><div><div class="vp-testi__name">Sarra Ben Ali</div><div class="vp-testi__role">Utilisatrice depuis 2024</div></div></div></div>
            <div class="vp-testi"><div class="vp-testi__stars">★★★★★</div><p class="vp-testi__text">"En tant qu'organisateur, EventLab m'a permis de tripler mes ventes de billets. Recommandé à 100% !"</p><div class="vp-testi__author"><div class="vp-testi__av">MK</div><div><div class="vp-testi__name">Mohamed Khadri</div><div class="vp-testi__role">Organisateur de festivals</div></div></div></div>
            <div class="vp-testi"><div class="vp-testi__stars">★★★★★</div><p class="vp-testi__text">"Je trouve toujours des concerts incroyables grâce à EventLab. L'app est moderne et le support très réactif."</p><div class="vp-testi__author"><div class="vp-testi__av">AT</div><div><div class="vp-testi__name">Amira Trabelsi</div><div class="vp-testi__role">Mélomane passionnée</div></div></div></div>
          </div>
        </div>
      </section>

      <section class="vp-sec">
        <div class="vp-wrap">
          <div class="vp-news">
            <div class="vp-news__bg"></div>
            <div class="vp-news__content">
              <span class="vp-news__icon">📨</span>
              <h2 class="vp-news__title">Restez informé(e)</h2>
              <p class="vp-news__sub">Recevez chaque semaine les meilleurs événements de Tunisie dans votre boîte mail</p>
              <div class="vp-news__form"><input v-model="newsletter" type="email" placeholder="votre@email.com" @keyup.enter="subscribeNewsletter" /><button @click="subscribeNewsletter">S'inscrire</button></div>
              <p v-if="newsletterMsg" class="vp-news__msg">{{ newsletterMsg }}</p>
              <p class="vp-news__hint">Pas de spam. Désinscription en 1 clic.</p>
            </div>
          </div>
        </div>
      </section>

      <footer class="vp-footer">
        <div class="vp-wrap">
          <div class="vp-footer__top">
            <div class="vp-footer__brand">
              <div class="vp-logo" style="margin-bottom:14px"><div class="vp-logo__mark">{{ siteName[0] }}</div><span class="vp-logo__name" style="color:#fff">{{ siteName }}</span></div>
              <p class="vp-footer__desc">La plateforme de billetterie #1 en Tunisie. Vivez des expériences inoubliables avec EventLab.</p>
              <div class="vp-footer__socials"><a class="vp-social" href="#">f</a><a class="vp-social" href="#">ig</a><a class="vp-social" href="#">X</a><a class="vp-social" href="#">in</a></div>
            </div>
            <div class="vp-footer__cols">
              <div><h4 class="vp-footer__h">Catégories</h4><a v-for="cat in categories.slice(0,5)" :key="cat.id" class="vp-footer__a" @click="selectCategory(cat)">{{ cat.name }}</a></div>
              <div><h4 class="vp-footer__h">Compte</h4><a class="vp-footer__a" @click="goToLogin()">Se connecter</a><a class="vp-footer__a" @click="goToRegister()">S'inscrire</a><a class="vp-footer__a" @click="goToRegister()">Espace organisateur</a></div>
              <div><h4 class="vp-footer__h">Légal</h4><a href="#" class="vp-footer__a">CGU</a><a href="#" class="vp-footer__a">Confidentialité</a><a href="#" class="vp-footer__a">Cookies</a><a href="#" class="vp-footer__a">Contact</a></div>
            </div>
          </div>
          <div class="vp-footer__bot"><span>© 2026 {{ siteName }}. Tous droits réservés.</span><span class="vp-footer__made">Fait avec 💖 en Tunisie</span></div>
        </div>
      </footer>
    </div>

    <!-- ══ PAGE CATÉGORIE ══ -->
    <div v-else class="vp-evpage">
      <div class="vp-banner" :style="{ backgroundImage: `url(${getCatImage(selectedCategory)})` }">
        <div class="vp-banner__overlay"></div>
        <div class="vp-banner__body">
          <button class="vp-back" @click="backToCategories()"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15,18 9,12 15,6"/></svg>Retour à l'accueil</button>
          <span class="vp-banner__emoji">{{ getCatCfg(selectedCategory.name).emoji }}</span>
          <h1 class="vp-banner__title">{{ selectedCategory.name }}</h1>
          <p class="vp-banner__count">{{ totalEvents }} événement{{ totalEvents !== 1 ? 's' : '' }} disponible{{ totalEvents !== 1 ? 's' : '' }}</p>
        </div>
      </div>
      <div class="vp-wrap" style="padding-top:48px;padding-bottom:80px">
        <div class="vp-filterbar">
          <div class="vp-fsearch"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg><input v-model="searchQuery" placeholder="Rechercher un événement…" @keyup.enter="currentPage = 1; fetchEventsByCategory(selectedCategory.id)" /></div>
          <select v-model="selectedPrice" class="vp-fsel" @change="currentPage = 1; fetchEventsByCategory(selectedCategory.id)"><option value="">Tous les prix</option><option value="free">Gratuit</option><option value="paid">Payant</option></select>
          <button class="vp-btn vp-primary vp-btn--sm" @click="currentPage = 1; fetchEventsByCategory(selectedCategory.id)">Filtrer</button>
        </div>
        <div v-if="isLoadingEvents" class="vp-evgrid"><div v-for="i in 9" :key="i" class="vp-ev-skel"><div class="vp-ev-skel__img"></div><div class="vp-ev-skel__body"><div class="vp-ev-skel__l w70"></div><div class="vp-ev-skel__l w100"></div><div class="vp-ev-skel__l w50"></div></div></div></div>
        <div v-else-if="events.length === 0" class="vp-empty"><span class="vp-empty__emoji">🔍</span><h3>Aucun événement trouvé</h3><p>Essayez de modifier vos filtres</p><button class="vp-btn vp-primary" @click="selectedPrice = ''; searchQuery = ''; fetchEventsByCategory(selectedCategory.id)">Voir tous</button></div>
        <div v-else class="vp-evgrid">
          <div v-for="ev in events" :key="ev.id" class="vp-evc" @click="goToEvent(ev.id)">
            <div class="vp-evc__img">
              <img v-if="getEventImage(ev)" :src="getEventImage(ev)" :alt="ev.title" /><div v-else class="vp-evc__ph"><span>{{ getCatCfg(selectedCategory.name).emoji }}</span></div>
              <span class="vp-evc__price" :class="{ free: isPriceFree(ev) }">{{ formatPrice(ev.price, ev.is_free) }}</span>
              <span v-if="ev.is_featured" class="vp-evc__star">⭐</span>
              <div class="vp-evc__hov">Voir →</div>
            </div>
            <div class="vp-evc__body">
              <h3 class="vp-evc__title">{{ ev.title }}</h3>
              <div class="vp-evc__metas">
                <span class="vp-evc__meta"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>{{ formatDate(ev.start_date) }}</span>
                <span v-if="ev.location_name" class="vp-evc__meta"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>{{ ev.location_name }}</span>
              </div>
              <div class="vp-evc__foot">
                <div class="vp-evc__org" v-if="ev.organizer_name"><div class="vp-evc__av">{{ ev.organizer_name?.[0]?.toUpperCase() }}</div><span>{{ ev.organizer_name }}</span></div>
                <button class="vp-evc__book">Réserver</button>
              </div>
            </div>
          </div>
        </div>
        <div v-if="totalPages > 1" class="vp-pages">
          <button class="vp-pgbtn" :disabled="currentPage === 1" @click="currentPage--; fetchEventsByCategory(selectedCategory.id)"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15,18 9,12 15,6"/></svg></button>
          <button v-for="p in totalPages" :key="p" class="vp-pgnum" :class="{ act: p === currentPage }" @click="currentPage = p; fetchEventsByCategory(selectedCategory.id)">{{ p }}</button>
          <button class="vp-pgbtn" :disabled="currentPage === totalPages" @click="currentPage++; fetchEventsByCategory(selectedCategory.id)"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9,18 15,12 9,6"/></svg></button>
        </div>
      </div>
      <footer class="vp-footer"><div class="vp-wrap"><div class="vp-footer__bot" style="border:none;padding-top:32px">© 2026 {{ siteName }}. Tous droits réservés.</div></div></footer>
    </div>

    <LoginModal v-if="showLoginModal" @close="showLoginModal = false" />
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;0,800;1,700&family=Outfit:wght@300;400;500;600;700;800&display=swap');

/* ══════════════════════════════════
   VARIABLES — LIGHT MODE (défaut)
══════════════════════════════════ */
.vp {
  /* accent injectés via :style (thème dynamique) */
  --bg:          #ffffff;
  --bg-alt:      #f9f4f6;
  --text:        #1a0a12;
  --text-sec:    #9e6878;
  --card-bg:     #ffffff;
  --card-border: var(--accent-lt);
  --card-bh:     var(--accent-md);
  --nav-bg:      rgba(255,255,255,0.96);
  --nav-text:    #4a0a2e;
  --filter-bg:   #ffffff;
  --skel-a:      var(--accent-lt);
  --skel-b:      var(--accent-lt2);
  --footer-bg:   #1a0a12;
  --footer-text: #7a4d5c;
  --footer-sep:  #2d1520;
}

/* ══════════════════════════════════
   VARIABLES — DARK MODE
══════════════════════════════════ */
.vp.dark {
  --bg:          #0d0709;
  --bg-alt:      #120810;
  --text:        #f0dde5;
  --text-sec:    #7a5566;
  --card-bg:     #1a0f13;
  --card-border: #2d1520;
  --card-bh:     var(--accent);
  --nav-bg:      rgba(13,7,9,0.96);
  --nav-text:    #f0dde5;
  --filter-bg:   #1a0f13;
  --skel-a:      #1e0d14;
  --skel-b:      #2d1520;
  --footer-bg:   #080405;
  --footer-text: #4a2535;
  --footer-sep:  #1e0d14;
}

/* ══════════════════════════════════
   RESET & BASE
══════════════════════════════════ */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
.vp { font-family:'Outfit',sans-serif; background:var(--bg); color:var(--text); min-height:100vh; transition:background .3s,color .3s; }

/* ══════════════════════════════════
   PALETTE FLOTTANTE
══════════════════════════════════ */
.vp-appearance-wrap {
  position: fixed;
  bottom: 32px;
  right: 28px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12px;
}

.vp-appearance-btn {
  width: 52px; height: 52px;
  border-radius: 16px;
  background: var(--accent);
  border: none;
  color: #fff;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 8px 28px rgba(var(--accent-rgb), 0.45);
  transition: all .25s;
  flex-shrink: 0;
}
.vp-appearance-btn:hover { transform: scale(1.08) rotate(12deg); box-shadow: 0 12px 36px rgba(var(--accent-rgb), 0.55); }

.vp-appearance-panel {
  background: var(--card-bg);
  border: 1.5px solid var(--card-border);
  border-radius: 22px;
  padding: 20px 22px;
  width: 240px;
  box-shadow: 0 24px 60px rgba(0,0,0,.18);
  backdrop-filter: blur(20px);
}

.vp-ap-section { margin-bottom: 0; }
.vp-ap-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .1em; color: var(--text-sec); margin-bottom: 14px; }
.vp-ap-divider { height: 1px; background: var(--card-border); margin: 18px 0; }

/* Swatches */
.vp-swatches { display: flex; gap: 10px; justify-content: space-between; margin-bottom: 8px; }
.vp-swatch {
  width: 34px; height: 34px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--sw), var(--sw2));
  border: 2.5px solid transparent;
  cursor: pointer;
  transition: all .2s;
  display: flex; align-items: center; justify-content: center;
  position: relative;
  outline: none;
}
.vp-swatch:hover { transform: scale(1.15); }
.vp-swatch.active {
  border-color: var(--bg);
  box-shadow: 0 0 0 3px var(--sw);
  transform: scale(1.18);
}
.vp-swatch__check { color: #fff; font-size: 12px; font-weight: 900; line-height: 1; text-shadow: 0 1px 3px rgba(0,0,0,.4); }

.vp-theme-labels { display: flex; justify-content: space-between; gap: 4px; }
.vp-theme-labels span { font-size: 9px; color: var(--text-sec); text-align: center; flex: 1; transition: color .2s; }
.vp-theme-labels span.active { color: var(--accent); font-weight: 700; }

/* Mode toggle */
.vp-mode-toggle {
  display: flex;
  align-items: center;
  gap: 0;
  background: var(--bg-alt);
  border-radius: 12px;
  padding: 4px;
  cursor: pointer;
  border: 1.5px solid var(--card-border);
  transition: all .2s;
}
.vp-mode-toggle:hover { border-color: var(--accent); }
.vp-mode-option {
  flex: 1; padding: 8px 4px; border-radius: 9px;
  font-size: 12px; font-weight: 600; text-align: center;
  display: flex; align-items: center; justify-content: center; gap: 5px;
  color: var(--text-sec); transition: all .25s;
}
.vp-mode-option.active {
  background: var(--card-bg);
  color: var(--accent);
  box-shadow: 0 2px 10px rgba(var(--accent-rgb), 0.2);
}
.vp-mode-slider { display: none; }

/* Transitions palette */
.vp-panel-enter-active { animation: panelIn .3s cubic-bezier(0.34, 1.56, 0.64, 1); }
.vp-panel-leave-active { animation: panelOut .2s ease; }
@keyframes panelIn { from { opacity:0; transform:translateY(12px) scale(.95); } to { opacity:1; transform:none; } }
@keyframes panelOut { from { opacity:1; transform:none; } to { opacity:0; transform:translateY(8px) scale(.96); } }

/* ══════════════════════════════════
   NAV
══════════════════════════════════ */
.vp-nav { position:fixed; top:0; left:0; right:0; z-index:999; padding:0 40px; transition:all .3s; }
.vp-nav.scrolled { background:var(--nav-bg); backdrop-filter:blur(20px); box-shadow:0 1px 0 rgba(var(--accent-rgb),.12); }
.vp-nav__inner { max-width:1280px; margin:0 auto; height:72px; display:flex; align-items:center; justify-content:space-between; gap:30px; }
.vp-nav__links { display:flex; gap:28px; flex:1; justify-content:center; }
.vp-nav__links a { color:#fff; font-size:14px; font-weight:500; text-decoration:none; transition:color .2s; text-shadow:0 1px 4px rgba(0,0,0,.3); cursor:pointer; }
.vp-nav.scrolled .vp-nav__links a { color:var(--nav-text); text-shadow:none; }
.vp-nav__links a:hover { color:var(--accent); }
.vp-nav__crumb { display:flex; align-items:center; gap:8px; font-size:14px; flex:1; }
.vp-crumb-btn { display:flex; align-items:center; gap:5px; background:var(--accent-lt); color:var(--accent); border:none; border-radius:8px; padding:6px 14px; font-size:13px; font-weight:600; cursor:pointer; font-family:'Outfit',sans-serif; transition:all .2s; }
.vp-crumb-sep { color:var(--accent-md); }
.vp-crumb-cur { font-weight:700; color:var(--accent); font-size:13px; }
.vp-nav__actions { display:flex; gap:10px; align-items:center; }

.vp-dark-toggle {
  width:40px; height:40px; border-radius:11px;
  border:1.5px solid rgba(255,255,255,.3);
  background:rgba(255,255,255,.12); backdrop-filter:blur(10px);
  cursor:pointer; display:flex; align-items:center; justify-content:center;
  font-size:18px; transition:all .25s; flex-shrink:0; line-height:1;
}
.vp-dark-toggle:hover { transform:scale(1.08); background:rgba(255,255,255,.22); }
.vp-nav.scrolled .vp-dark-toggle { border-color:var(--accent-lt2); background:var(--accent-xlt); backdrop-filter:none; }
.vp-nav.scrolled .vp-dark-toggle:hover { background:var(--accent-lt); }
.dark .vp-nav.scrolled .vp-dark-toggle { background:#1e0d14; border-color:#3d1a28; }

.dm-icon-enter-active,.dm-icon-leave-active{transition:all .2s}
.dm-icon-enter-from{opacity:0;transform:rotate(-90deg) scale(.5)}
.dm-icon-leave-to{opacity:0;transform:rotate(90deg) scale(.5)}

.vp-logo { display:flex; align-items:center; gap:10px; cursor:pointer; }
.vp-logo__mark { width:38px; height:38px; border-radius:11px; background:linear-gradient(135deg,var(--accent),var(--accent-dk)); display:flex; align-items:center; justify-content:center; color:#fff; font-family:'Playfair Display',serif; font-weight:700; font-size:18px; flex-shrink:0; box-shadow:0 4px 14px rgba(var(--accent-rgb),.35); }
.vp-logo__name { font-family:'Playfair Display',serif; font-weight:700; font-size:21px; color:#fff; text-shadow:0 1px 4px rgba(0,0,0,.3); }
.vp-nav.scrolled .vp-logo__name { color:var(--accent-dkr); text-shadow:none; }

.vp-btn { display:inline-flex; align-items:center; gap:6px; border:none; cursor:pointer; border-radius:10px; font-size:14px; font-weight:600; padding:10px 22px; transition:all .25s; font-family:'Outfit',sans-serif; line-height:1; white-space:nowrap; }
.vp-btn--sm { padding:9px 18px; font-size:13px; }
.vp-primary { background:linear-gradient(135deg,var(--accent),var(--accent-dk)); color:#fff; box-shadow:0 4px 16px rgba(var(--accent-rgb),.35); }
.vp-primary:hover { transform:translateY(-2px); box-shadow:0 8px 24px rgba(var(--accent-rgb),.45); }
.vp-ghost { background:rgba(255,255,255,.15); color:#fff; border:1.5px solid rgba(255,255,255,.3); backdrop-filter:blur(10px); }
.vp-ghost:hover { background:rgba(255,255,255,.25); }
.vp-nav.scrolled .vp-ghost { background:transparent; color:var(--accent); border-color:var(--accent-lt2); backdrop-filter:none; }
.vp-nav.scrolled .vp-ghost:hover { background:var(--accent-xlt); }
.vp-white { background:#fff; color:var(--accent-dk); font-weight:700; }
.vp-white:hover { background:var(--accent-xlt); transform:translateY(-2px); }
.vp-ghost-w { background:rgba(255,255,255,.1); color:#fff; border:1.5px solid rgba(255,255,255,.3); }
.vp-ghost-w:hover { background:rgba(255,255,255,.2); }

/* ══════════════════════════════════
   HERO
══════════════════════════════════ */
.vp-hero { min-height:100vh; position:relative; display:flex; align-items:center; justify-content:center; overflow:hidden; }
.vp-hero__slides { position:absolute; inset:0; }
.vp-hero__slide { position:absolute; inset:0; background-size:cover; background-position:center; opacity:0; transition:opacity 1.5s ease; animation:heroZoom 8s ease-out infinite; }
.vp-hero__slide.active { opacity:1; }
@keyframes heroZoom { 0%{transform:scale(1)} 100%{transform:scale(1.08)} }
.vp-hero__overlay { position:absolute; inset:0; background:linear-gradient(135deg,rgba(var(--accent-dk-rgb),.88) 0%,rgba(var(--accent-rgb),.65) 50%,rgba(var(--accent-dk-rgb),.88) 100%); }
.vp-hero__content { position:relative; z-index:1; text-align:center; max-width:800px; padding:0 24px; }
.vp-hero__pill { display:inline-flex; align-items:center; gap:8px; background:rgba(255,255,255,.15); border:1px solid rgba(255,255,255,.3); border-radius:100px; padding:8px 20px; font-size:13px; font-weight:500; color:#fff; margin-bottom:32px; backdrop-filter:blur(10px); }
.vp-dot-anim { width:8px; height:8px; border-radius:50%; background:#fff; animation:dpulse 2s infinite; flex-shrink:0; }
@keyframes dpulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.4;transform:scale(.7)} }
.vp-hero__h1 { font-family:'Playfair Display',serif; font-size:clamp(44px,6vw,80px); font-weight:800; line-height:1.05; color:#fff; margin-bottom:24px; letter-spacing:-1px; }
.vp-hero__h1 em { font-style:italic; color:rgba(255,255,255,.8); }
.vp-hero__p { font-size:18px; color:rgba(255,255,255,.85); max-width:580px; margin:0 auto 44px; line-height:1.7; }
.vp-searchbar { display:flex; align-items:center; gap:12px; background:var(--card-bg); border-radius:18px; box-shadow:0 12px 48px rgba(0,0,0,.25); padding:10px 10px 10px 22px; max-width:620px; margin:0 auto 48px; color:var(--accent-md); transition:background .3s; }
.vp-searchbar input { border:none; outline:none; font-size:16px; color:var(--text); width:100%; background:transparent; font-family:'Outfit',sans-serif; padding:8px 0; transition:color .3s; }
.vp-searchbar input::placeholder { color:var(--text-sec); }
.vp-search-btn { padding:12px 28px; background:linear-gradient(135deg,var(--accent),var(--accent-dk)); border:none; border-radius:12px; color:#fff; font-size:14px; font-family:'Outfit',sans-serif; font-weight:700; cursor:pointer; white-space:nowrap; transition:all .2s; }
.vp-search-btn:hover { transform:translateY(-1px); box-shadow:0 6px 20px rgba(var(--accent-rgb),.5); }
.vp-hero__stats { display:flex; align-items:center; justify-content:center; flex-wrap:wrap; }
.vp-hstat { text-align:center; padding:0 28px; }
.vp-hstat__num { display:block; font-family:'Playfair Display',serif; font-size:32px; font-weight:800; color:#fff; }
.vp-hstat__lbl { display:block; font-size:12px; color:rgba(255,255,255,.7); margin-top:5px; letter-spacing:.8px; text-transform:uppercase; }
.vp-hstat__sep { width:1px; height:48px; background:rgba(255,255,255,.2); }
.vp-hero__dots { display:flex; gap:8px; justify-content:center; margin-top:40px; }
.vp-hero__dots button { width:28px; height:4px; border-radius:2px; background:rgba(255,255,255,.3); border:none; cursor:pointer; transition:all .3s; padding:0; }
.vp-hero__dots button.active { background:#fff; width:40px; }
.vp-hero__scroll { position:absolute; bottom:32px; left:50%; transform:translateX(-50%); color:rgba(255,255,255,.6); animation:bounce 2s infinite; }
@keyframes bounce { 0%,100%{transform:translateX(-50%) translateY(0)} 50%{transform:translateX(-50%) translateY(8px)} }

/* ══════════════════════════════════
   SECTIONS
══════════════════════════════════ */
.vp-wrap { max-width:1280px; margin:0 auto; padding:0 40px; }
.vp-sec { padding:100px 0; background:var(--bg); transition:background .3s; }
.vp-sec--alt { background:var(--bg-alt); transition:background .3s; }
.vp-sec-top { display:flex; align-items:flex-end; justify-content:space-between; margin-bottom:56px; gap:30px; }
.vp-sec-top--center { justify-content:center; text-align:center; flex-direction:column; }
.vp-eyebrow { font-size:12px; font-weight:700; color:var(--accent); text-transform:uppercase; letter-spacing:3px; margin-bottom:12px; }
.vp-sec-title { font-family:'Playfair Display',serif; font-size:clamp(30px,3.5vw,44px); font-weight:800; color:var(--text); line-height:1.1; transition:color .3s; }
.vp-sec-sub { font-size:15px; color:var(--text-sec); max-width:320px; text-align:right; line-height:1.6; }

/* Featured */
.vp-feat-grid { display:grid; grid-template-columns:2fr 1fr 1fr; gap:20px; height:540px; }
.vp-feat-grid>.vp-feat--big { grid-row:span 2; }
.vp-feat-grid>:not(.vp-feat--big) { grid-column:span 2; }
.vp-feat { position:relative; border-radius:22px; overflow:hidden; cursor:pointer; transition:all .35s; box-shadow:0 4px 24px rgba(var(--accent-dk-rgb),.15); }
.vp-feat:hover { transform:translateY(-6px); box-shadow:0 24px 56px rgba(var(--accent-dk-rgb),.3); }
.vp-feat__img { position:relative; width:100%; height:100%; }
.vp-feat__img img { width:100%; height:100%; object-fit:cover; transition:transform .6s; }
.vp-feat:hover .vp-feat__img img { transform:scale(1.08); }
.vp-feat__ph { width:100%; height:100%; display:flex; align-items:center; justify-content:center; background:linear-gradient(135deg,var(--accent),var(--accent-dk)); font-size:60px; }
.vp-feat__overlay { position:absolute; inset:0; background:linear-gradient(to top,rgba(26,10,18,.92) 0%,rgba(26,10,18,.3) 50%,transparent 100%); }
.vp-feat__badge { position:absolute; top:16px; left:16px; background:linear-gradient(135deg,#FFB300,#F57C00); color:#fff; font-size:11px; font-weight:700; padding:5px 12px; border-radius:20px; }
.vp-feat__price { position:absolute; top:16px; right:16px; background:var(--accent); color:#fff; font-size:13px; font-weight:700; padding:6px 14px; border-radius:10px; }
.vp-feat__price.free { background:#059669; }
.vp-feat__info { position:absolute; left:24px; right:24px; bottom:24px; color:#fff; }
.vp-feat__title { font-family:'Playfair Display',serif; font-size:22px; font-weight:700; margin-bottom:10px; line-height:1.25; text-shadow:0 2px 8px rgba(0,0,0,.4); }
.vp-feat--big .vp-feat__title { font-size:32px; }
.vp-feat__metas { display:flex; flex-wrap:wrap; gap:14px; }
.vp-feat__meta { display:flex; align-items:center; gap:6px; font-size:12px; color:rgba(255,255,255,.85); }
.vp-feat-skel { border-radius:22px; background:linear-gradient(90deg,var(--skel-a) 25%,var(--skel-b) 50%,var(--skel-a) 75%); background-size:200% 100%; animation:vshim 1.4s infinite; }
.vp-feat-skel:first-child { grid-row:span 2; }
.vp-feat-skel:not(:first-child) { grid-column:span 2; }
@keyframes vshim { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

/* Catégories */
.vp-cats-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:24px; }
.vp-cat { position:relative; border-radius:22px; overflow:hidden; cursor:pointer; border:none; height:240px; transition:all .35s; box-shadow:0 4px 20px rgba(var(--accent-dk-rgb),.12); padding:0; }
.vp-cat:hover { transform:translateY(-8px); box-shadow:0 24px 56px rgba(var(--accent-rgb),.25); }
.vp-cat__img { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; transition:transform .6s; }
.vp-cat:hover .vp-cat__img { transform:scale(1.1); }
.vp-cat__overlay { position:absolute; inset:0; background:linear-gradient(135deg,rgba(var(--accent-dk-rgb),.65) 0%,rgba(var(--accent-rgb),.55) 50%,rgba(var(--accent-dk-rgb),.8) 100%); transition:all .3s; }
.vp-cat:hover .vp-cat__overlay { background:linear-gradient(135deg,rgba(var(--accent-dk-rgb),.85),rgba(var(--accent-rgb),.9)); }
.vp-cat__body { position:absolute; inset:0; display:flex; flex-direction:column; justify-content:flex-end; padding:26px; z-index:1; text-align:left; }
.vp-cat__emoji { font-size:40px; margin-bottom:10px; display:block; }
.vp-cat__name { font-family:'Playfair Display',serif; font-size:24px; font-weight:700; color:#fff; margin-bottom:10px; }
.vp-cat__cta { display:inline-flex; align-items:center; gap:6px; font-size:13px; font-weight:600; color:rgba(255,255,255,.95); transition:gap .2s; }
.vp-cat:hover .vp-cat__cta { gap:12px; }
.vp-cat-skel { border-radius:22px; height:240px; background:linear-gradient(90deg,var(--skel-a) 25%,var(--skel-b) 50%,var(--skel-a) 75%); background-size:200% 100%; animation:vshim 1.4s infinite; }

/* Cartes événement */
.vp-evgrid { display:grid; grid-template-columns:repeat(auto-fill,minmax(320px,1fr)); gap:28px; }
.vp-evc { background:var(--card-bg); border-radius:20px; overflow:hidden; cursor:pointer; transition:all .3s; border:1.5px solid var(--card-border); }
.vp-evc:hover { transform:translateY(-6px); box-shadow:0 20px 48px rgba(var(--accent-rgb),.15); border-color:var(--card-bh); }
.vp-evc__img { position:relative; height:220px; overflow:hidden; }
.vp-evc__img img { width:100%; height:100%; object-fit:cover; transition:transform .4s; }
.vp-evc:hover .vp-evc__img img { transform:scale(1.06); }
.vp-evc__ph { width:100%; height:100%; display:flex; align-items:center; justify-content:center; background:linear-gradient(135deg,var(--accent-lt),var(--accent-md)); font-size:48px; }
.vp-evc__price { position:absolute; top:14px; right:14px; background:var(--accent); color:#fff; border-radius:8px; padding:5px 13px; font-size:12px; font-weight:700; }
.vp-evc__price.free { background:#059669; }
.vp-evc__star { position:absolute; top:14px; left:14px; background:rgba(0,0,0,.45); backdrop-filter:blur(4px); border-radius:8px; padding:4px 10px; font-size:13px; }
.vp-evc__hov { position:absolute; inset:0; background:linear-gradient(135deg,rgba(var(--accent-dk-rgb),.88),rgba(var(--accent-rgb),.88)); display:flex; align-items:center; justify-content:center; color:#fff; font-size:16px; font-weight:700; opacity:0; transition:opacity .3s; }
.vp-evc:hover .vp-evc__hov { opacity:1; }
.vp-evc__body { padding:20px; }
.vp-evc__title { font-family:'Playfair Display',serif; font-size:17px; font-weight:700; color:var(--text); line-height:1.3; margin-bottom:12px; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; transition:color .3s; }
.vp-evc__metas { display:flex; flex-direction:column; gap:6px; margin-bottom:16px; }
.vp-evc__meta { display:flex; align-items:center; gap:7px; font-size:13px; color:var(--text-sec); transition:color .3s; }
.vp-evc__foot { display:flex; justify-content:space-between; align-items:center; padding-top:14px; border-top:1px solid var(--card-border); transition:border-color .3s; }
.vp-evc__org { display:flex; align-items:center; gap:8px; }
.vp-evc__av { width:30px; height:30px; border-radius:50%; background:linear-gradient(135deg,var(--accent-md),var(--accent)); color:#fff; font-size:12px; font-weight:700; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.vp-evc__org span { font-size:12px; color:var(--text-sec); font-weight:500; }
.vp-evc__book { padding:8px 18px; background:linear-gradient(135deg,var(--accent),var(--accent-dk)); color:#fff; border:none; border-radius:9px; font-size:13px; font-weight:600; cursor:pointer; font-family:'Outfit',sans-serif; transition:all .2s; box-shadow:0 3px 12px rgba(var(--accent-rgb),.25); }
.vp-evc__book:hover { transform:translateY(-1px); box-shadow:0 6px 18px rgba(var(--accent-rgb),.4); }
.vp-ev-skel { background:var(--card-bg); border-radius:20px; overflow:hidden; border:1.5px solid var(--card-border); }
.vp-ev-skel__img { height:220px; background:linear-gradient(90deg,var(--skel-a) 25%,var(--skel-b) 50%,var(--skel-a) 75%); background-size:200% 100%; animation:vshim 1.4s infinite; }
.vp-ev-skel__body { padding:20px; display:flex; flex-direction:column; gap:12px; }
.vp-ev-skel__l { height:13px; border-radius:7px; background:linear-gradient(90deg,var(--skel-a) 25%,var(--skel-b) 50%,var(--skel-a) 75%); background-size:200% 100%; animation:vshim 1.4s infinite; }
.w70{width:70%}.w100{width:100%}.w50{width:50%}

/* CTA organisateurs */
.vp-cta-box { display:grid; grid-template-columns:1fr 1fr; border-radius:32px; overflow:hidden; box-shadow:0 32px 80px rgba(var(--accent-rgb),.2); }
.vp-cta-box__img { position:relative; min-height:540px; }
.vp-cta-box__img img { width:100%; height:100%; object-fit:cover; }
.vp-cta-box__img-overlay { position:absolute; inset:0; background:linear-gradient(135deg,rgba(var(--accent-dk-rgb),.45),rgba(var(--accent-rgb),.3)); }
.vp-cta-box__content { background:linear-gradient(145deg,var(--accent-dkr),color-mix(in srgb,var(--accent-dk) 40%,#000)); padding:60px 56px; display:flex; flex-direction:column; justify-content:center; }
.vp-cta-tag { display:inline-block; background:rgba(255,255,255,.15); color:rgba(255,255,255,.9); border:1px solid rgba(255,255,255,.25); border-radius:100px; padding:6px 16px; font-size:12px; font-weight:600; margin-bottom:22px; width:fit-content; }
.vp-cta-title { font-family:'Playfair Display',serif; font-size:40px; font-weight:800; color:#fff; line-height:1.15; margin-bottom:18px; }
.vp-cta-sub { color:rgba(255,255,255,.7); font-size:15px; line-height:1.7; margin-bottom:28px; }
.vp-cta-features { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:32px; }
.vp-feat-item { display:flex; align-items:center; gap:10px; font-size:14px; color:rgba(255,255,255,.85); }
.vp-feat-item__icon { width:22px; height:22px; border-radius:50%; background:rgba(255,255,255,.2); color:#fff; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:700; flex-shrink:0; }
.vp-cta-btns { display:flex; gap:12px; flex-wrap:wrap; }

/* Témoignages */
.vp-testi-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:24px; }
.vp-testi { background:var(--card-bg); border:1.5px solid var(--card-border); border-radius:20px; padding:28px; transition:all .3s; }
.vp-testi:hover { transform:translateY(-4px); box-shadow:0 16px 40px rgba(var(--accent-rgb),.12); border-color:var(--card-bh); }
.vp-testi__stars { color:#FFB300; font-size:18px; margin-bottom:16px; letter-spacing:2px; }
.vp-testi__text { font-size:15px; line-height:1.7; color:var(--text-sec); margin-bottom:24px; font-style:italic; transition:color .3s; }
.vp-testi__author { display:flex; align-items:center; gap:12px; padding-top:18px; border-top:1px solid var(--card-border); transition:border-color .3s; }
.vp-testi__av { width:44px; height:44px; border-radius:50%; background:linear-gradient(135deg,var(--accent-md),var(--accent)); color:#fff; display:flex; align-items:center; justify-content:center; font-size:14px; font-weight:700; flex-shrink:0; }
.vp-testi__name { font-size:14px; font-weight:700; color:var(--text); transition:color .3s; }
.vp-testi__role { font-size:12px; color:var(--text-sec); margin-top:2px; }

/* Newsletter */
.vp-news { position:relative; border-radius:32px; overflow:hidden; background:linear-gradient(135deg,var(--accent) 0%,var(--accent-dk) 100%); padding:64px 40px; text-align:center; box-shadow:0 24px 60px rgba(var(--accent-rgb),.3); }
.vp-news__bg { position:absolute; inset:0; background-image:radial-gradient(circle at 20% 30%,rgba(255,255,255,.15) 0%,transparent 50%),radial-gradient(circle at 80% 70%,rgba(255,255,255,.1) 0%,transparent 50%); pointer-events:none; }
.vp-news__content { position:relative; z-index:1; max-width:540px; margin:0 auto; }
.vp-news__icon { font-size:44px; display:block; margin-bottom:16px; }
.vp-news__title { font-family:'Playfair Display',serif; font-size:36px; font-weight:800; color:#fff; margin-bottom:12px; }
.vp-news__sub { color:rgba(255,255,255,.85); font-size:15px; line-height:1.6; margin-bottom:28px; }
.vp-news__form { display:flex; gap:8px; background:#fff; border-radius:14px; padding:6px; max-width:460px; margin:0 auto; }
.vp-news__form input { flex:1; border:none; outline:none; padding:12px 18px; font-family:'Outfit',sans-serif; font-size:14px; color:#1a0a12; background:transparent; }
.vp-news__form button { padding:12px 24px; background:linear-gradient(135deg,var(--accent),var(--accent-dk)); color:#fff; border:none; border-radius:10px; font-family:'Outfit',sans-serif; font-size:14px; font-weight:700; cursor:pointer; transition:all .2s; white-space:nowrap; }
.vp-news__msg { color:#fff; font-size:14px; margin-top:16px; font-weight:600; }
.vp-news__hint { color:rgba(255,255,255,.6); font-size:12px; margin-top:16px; }

/* Footer */
.vp-footer { background:var(--footer-bg); padding:72px 0 0; transition:background .3s; }
.vp-footer__top { display:grid; grid-template-columns:1.5fr 2fr; gap:60px; margin-bottom:56px; }
.vp-footer__desc { color:var(--footer-text); font-size:14px; line-height:1.7; max-width:280px; margin-bottom:20px; }
.vp-footer__cols { display:grid; grid-template-columns:repeat(3,1fr); gap:32px; }
.vp-footer__h { color:var(--accent-md); font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:2px; margin-bottom:16px; }
.vp-footer__a { display:block; color:var(--footer-text); font-size:14px; cursor:pointer; text-decoration:none; margin-bottom:12px; transition:color .2s; background:none; border:none; font-family:'Outfit',sans-serif; text-align:left; padding:0; }
.vp-footer__a:hover { color:var(--accent-md); }
.vp-footer__socials { display:flex; gap:8px; }
.vp-social { width:36px; height:36px; border:1px solid var(--footer-sep); border-radius:10px; display:flex; align-items:center; justify-content:center; color:var(--footer-text); font-size:12px; font-weight:700; cursor:pointer; transition:all .2s; text-decoration:none; }
.vp-social:hover { border-color:var(--accent); color:var(--accent); }
.vp-footer__bot { display:flex; align-items:center; justify-content:space-between; border-top:1px solid var(--footer-sep); padding:24px 0; font-size:13px; color:var(--footer-text); }
.vp-footer__made { color:var(--accent-md); }

/* Page catégorie */
.vp-banner { padding:130px 40px 56px; text-align:center; position:relative; overflow:hidden; min-height:380px; display:flex; align-items:flex-end; justify-content:center; background-size:cover; background-position:center; }
.vp-banner__overlay { position:absolute; inset:0; background:linear-gradient(135deg,rgba(var(--accent-dk-rgb),.88) 0%,rgba(var(--accent-rgb),.7) 50%,rgba(var(--accent-dk-rgb),.88) 100%); }
.vp-banner__body { position:relative; z-index:1; }
.vp-back { display:inline-flex; align-items:center; gap:6px; background:rgba(255,255,255,.15); backdrop-filter:blur(8px); border:1px solid rgba(255,255,255,.25); color:#fff; border-radius:10px; padding:8px 18px; font-size:13px; font-weight:600; cursor:pointer; font-family:'Outfit',sans-serif; margin-bottom:26px; transition:all .2s; }
.vp-banner__emoji { font-size:60px; display:block; margin:0 auto 18px; }
.vp-banner__title { font-family:'Playfair Display',serif; font-size:56px; font-weight:800; color:#fff; margin-bottom:10px; }
.vp-banner__count { color:rgba(255,255,255,.75); font-size:16px; font-weight:500; }
.vp-filterbar { display:flex; align-items:center; gap:12px; flex-wrap:wrap; background:var(--filter-bg); border:1.5px solid var(--card-border); border-radius:16px; padding:14px 20px; margin-bottom:36px; transition:background .3s,border-color .3s; }
.vp-fsearch { display:flex; align-items:center; gap:10px; flex:1; min-width:200px; color:var(--accent-md); }
.vp-fsearch input { border:none; outline:none; font-size:14px; color:var(--text); width:100%; background:transparent; font-family:'Outfit',sans-serif; transition:color .3s; }
.vp-fsearch input::placeholder { color:var(--text-sec); }
.vp-fsel { background:var(--bg-alt); border:1.5px solid var(--card-border); border-radius:10px; padding:9px 16px; font-size:14px; color:var(--accent-dk); cursor:pointer; outline:none; font-family:'Outfit',sans-serif; font-weight:500; transition:background .3s; }
.vp-empty { text-align:center; padding:100px 20px; }
.vp-empty__emoji { font-size:60px; display:block; margin-bottom:20px; }
.vp-empty h3 { font-family:'Playfair Display',serif; font-size:26px; color:var(--accent-dkr); margin-bottom:10px; }
.vp-empty p { color:var(--text-sec); font-size:15px; margin-bottom:28px; }
.vp-pages { display:flex; align-items:center; justify-content:center; gap:8px; margin-top:56px; }
.vp-pgbtn { width:42px; height:42px; border-radius:11px; border:1.5px solid var(--card-border); background:var(--card-bg); cursor:pointer; display:flex; align-items:center; justify-content:center; color:var(--accent); transition:all .2s; }
.vp-pgbtn:hover:not(:disabled) { border-color:var(--accent); }
.vp-pgbtn:disabled { opacity:.3; cursor:not-allowed; }
.vp-pgnum { width:42px; height:42px; border-radius:11px; border:1.5px solid var(--card-border); background:var(--card-bg); font-size:14px; font-weight:600; color:var(--accent); cursor:pointer; transition:all .2s; font-family:'Outfit',sans-serif; }
.vp-pgnum.act,.vp-pgnum:hover { background:linear-gradient(135deg,var(--accent),var(--accent-dk)); color:#fff; border-color:var(--accent); }

/* ══ RESPONSIVE ══ */
@media (max-width:1024px) {
  .vp-nav__links{display:none}.vp-feat-grid{grid-template-columns:1fr;height:auto}.vp-feat-grid>.vp-feat--big,.vp-feat-grid>:not(.vp-feat--big){grid-row:auto;grid-column:auto}.vp-feat,.vp-feat-skel{height:280px}.vp-cta-box{grid-template-columns:1fr}.vp-cta-box__img{min-height:300px}.vp-cta-box__content{padding:48px 36px}.vp-footer__top{grid-template-columns:1fr;gap:40px}.vp-testi-grid{grid-template-columns:1fr}
}
@media (max-width:768px) {
  .vp-nav{padding:0 20px}.vp-wrap{padding:0 20px}.vp-nav__actions .vp-ghost{display:none}.vp-hero__h1{font-size:42px}.vp-hstat{padding:0 12px}.vp-hstat__sep{display:none}.vp-hstat__num{font-size:24px}.vp-searchbar{flex-direction:column;padding:16px;gap:12px;align-items:stretch}.vp-search-btn{width:100%}.vp-sec{padding:70px 0}.vp-sec-top{flex-direction:column;align-items:flex-start}.vp-sec-sub{text-align:left;max-width:100%}.vp-cats-grid{grid-template-columns:1fr 1fr;gap:14px}.vp-cat{height:180px}.vp-cat__name{font-size:18px}.vp-cat__emoji{font-size:32px}.vp-evgrid{grid-template-columns:1fr}.vp-cta-features{grid-template-columns:1fr}.vp-cta-title{font-size:28px}.vp-news{padding:48px 24px}.vp-news__title{font-size:26px}.vp-news__form{flex-direction:column;padding:12px}.vp-news__form button{width:100%}.vp-footer__cols{grid-template-columns:1fr 1fr;gap:24px}.vp-footer__bot{flex-direction:column;gap:8px;text-align:center}.vp-banner__title{font-size:38px}.vp-appearance-wrap{bottom:20px;right:16px}
}
</style>