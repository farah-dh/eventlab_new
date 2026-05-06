<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

const router = useRouter()

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'
const getToken = () => localStorage.getItem('access_token') || localStorage.getItem('token')

const apiFetch = async (endpoint: string) => {
  const token = getToken()
  const res = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

const isLoading   = ref(true)
const events      = ref<any[]>([])
const search      = ref('')
const activeCategory = ref('Tous')
const sortBy      = ref('date')

const categories = computed(() => {
  const cats = new Set(events.value.map((e: any) => e.category?.name || e.category || 'Autre'))
  return ['Tous', ...Array.from(cats)]
})

const fetchEvents = async () => {
  isLoading.value = true
  try {
    const d = await apiFetch('/events/')
    const all = Array.isArray(d.results || d) ? (d.results || d) : []
    events.value = all.filter((e: any) => e.status === true || e.status === 'active' || e.is_published)
  }
  catch {
    events.value = []
  }
  finally {
    isLoading.value = false
  }
}

const filteredEvents = computed(() => {
  let list = [...events.value]

  if (search.value.trim()) {
    const q = search.value.toLowerCase()
    list = list.filter((e: any) =>
      (e.title || '').toLowerCase().includes(q)
      || (e.description || '').toLowerCase().includes(q)
      || (e.location_name || e.location || '').toLowerCase().includes(q),
    )
  }

  if (activeCategory.value !== 'Tous') {
    list = list.filter((e: any) => {
      const cat = e.category?.name || e.category || 'Autre'
      return cat === activeCategory.value
    })
  }

  if (sortBy.value === 'date')
    list.sort((a, b) => new Date(a.start_date || 0).getTime() - new Date(b.start_date || 0).getTime())
  else if (sortBy.value === 'price')
    list.sort((a, b) => Number(a.price || 0) - Number(b.price || 0))
  else if (sortBy.value === 'popular')
    list.sort((a, b) => (b.views_count || b.bookings_count || 0) - (a.views_count || a.bookings_count || 0))

  return list
})

function formatDate(d: string | null) {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatPrice(p: any) {
  if (p === null || p === undefined || p === 0 || p === '0')
    return 'Gratuit'
  return `${Number(p).toFixed(3)} DT`
}

function isFree(p: any) {
  return !p || Number(p) === 0
}

onMounted(fetchEvents)
</script>

<template>
  <div class="ev-root">

    <!-- HEADER -->
    <div class="ev-header">
      <div class="ev-header__glow g1" />
      <div class="ev-header__glow g2" />
      <div class="ev-header__content">
        <button class="ev-back-btn" @click="router.push('/user/dashboard')">
          <VIcon icon="tabler-arrow-left" size="16" /> Retour
        </button>
        <h1 class="ev-header__title">
          <VIcon icon="tabler-calendar-event" size="26" /> Découvrir les événements
        </h1>
        <p class="ev-header__sub">
          {{ filteredEvents.length }} événement{{ filteredEvents.length !== 1 ? 's' : '' }} disponible{{ filteredEvents.length !== 1 ? 's' : '' }}
        </p>
      </div>
    </div>

    <!-- TOOLBAR -->
    <div class="ev-toolbar">
      <div class="ev-search">
        <VIcon icon="tabler-search" size="16" class="ev-search__icon" />
        <input
          v-model="search"
          class="ev-search__input"
          placeholder="Rechercher un événement, lieu…"
        />
        <button v-if="search" class="ev-search__clear" @click="search = ''">
          <VIcon icon="tabler-x" size="14" />
        </button>
      </div>

      <div class="ev-sort">
        <VIcon icon="tabler-arrows-sort" size="15" style="color:var(--muted)" />
        <select v-model="sortBy" class="ev-sort__select">
          <option value="date">Par date</option>
          <option value="price">Par prix</option>
          <option value="popular">Popularité</option>
        </select>
      </div>
    </div>

    <!-- CATEGORIES -->
    <div class="ev-cats">
      <button
        v-for="cat in categories"
        :key="cat"
        class="ev-cat-btn"
        :class="{ 'ev-cat-btn--active': activeCategory === cat }"
        @click="activeCategory = cat"
      >
        {{ cat }}
      </button>
    </div>

    <!-- LOADING -->
    <div v-if="isLoading" class="ev-loading">
      <div class="ev-loading__spinner" />
      <p>Chargement des événements…</p>
    </div>

    <!-- EMPTY -->
    <div v-else-if="filteredEvents.length === 0" class="ev-empty">
      <div class="ev-empty__icon">🔍</div>
      <h3>Aucun événement trouvé</h3>
      <p>Essayez de modifier votre recherche ou vos filtres.</p>
      <button class="ev-btn-primary" @click="search = ''; activeCategory = 'Tous'">
        <VIcon icon="tabler-refresh" size="14" /> Réinitialiser les filtres
      </button>
    </div>

    <!-- GRID -->
    <div v-else class="ev-grid">
      <div
        v-for="event in filteredEvents"
        :key="event.id"
        class="ev-card"
        @click="router.push(`/user/events/${event.id}`)"
      >
        <!-- IMAGE / PLACEHOLDER -->
        <div class="ev-card__img">
          <img v-if="event.cover_image || event.banner || event.image || event.cover" :src="event.cover_image || event.banner || event.image || event.cover" :alt="event.title" />
          <div v-else class="ev-card__img-placeholder">
            <VIcon icon="tabler-calendar-event" size="40" style="color:var(--pink)" />
          </div>
          <span v-if="event.is_featured" class="ev-card__badge ev-card__badge--featured">
            <VIcon icon="tabler-star" size="11" /> Vedette
          </span>
          <span class="ev-card__price-badge" :class="isFree(event.price) ? 'ev-card__price-badge--free' : 'ev-card__price-badge--paid'">
            {{ formatPrice(event.price) }}
          </span>
        </div>

        <!-- BODY -->
        <div class="ev-card__body">
          <span v-if="event.category" class="ev-card__cat">
            {{ event.category?.name || event.category }}
          </span>
          <h3 class="ev-card__title">{{ event.title }}</h3>
          <p class="ev-card__desc">{{ event.description?.slice(0, 90) }}{{ event.description?.length > 90 ? '…' : '' }}</p>

          <div class="ev-card__meta">
            <span class="ev-card__meta-item">
              <VIcon icon="tabler-calendar" size="13" />
              {{ formatDate(event.start_date) }}
            </span>
            <span v-if="event.location_name || event.location" class="ev-card__meta-item">
              <VIcon icon="tabler-map-pin" size="13" />
              {{ event.location_name || event.location }}
            </span>
          </div>
        </div>

        <!-- FOOTER -->
        <div class="ev-card__footer">
          <div class="ev-card__stats">
            <span v-if="event.available_seats !== undefined" class="ev-card__stat">
              <VIcon icon="tabler-users" size="12" />
              {{ event.available_seats }} places
            </span>
          </div>
          <button class="ev-card__cta" @click.stop="router.push(`/user/events/${event.id}`)">
            Réserver <VIcon icon="tabler-arrow-right" size="13" />
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.ev-root {
  --pink: #E91E8C;
  --pink-dark: #AD1457;
  --pink-pale: #fdf0f6;
  --pink-light: #fce4ec;
  --text: #1a0a14;
  --muted: #7c6070;
  --border: #f0e0ea;
  --white: #ffffff;
  --radius: 18px;
  font-family: 'Segoe UI', system-ui, sans-serif;
  color: var(--text);
  padding-bottom: 48px;
}

/* HEADER */
.ev-header {
  position: relative;
  background: linear-gradient(135deg, #880E4F 0%, #AD1457 45%, #E91E8C 100%);
  border-radius: var(--radius);
  padding: 32px 36px 28px;
  margin-bottom: 20px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(233, 30, 140, .3);
}
.ev-header__glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(70px);
  pointer-events: none;
}
.ev-header__glow.g1 { width: 260px; height: 260px; background: rgba(255,180,220,.25); top: -100px; right: 60px; }
.ev-header__glow.g2 { width: 160px; height: 160px; background: rgba(255,100,180,.2); bottom: -60px; left: 160px; }
.ev-header__content { position: relative; z-index: 1; }
.ev-back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255,255,255,.15);
  border: 1px solid rgba(255,255,255,.3);
  color: #fff;
  border-radius: 10px;
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  margin-bottom: 14px;
  backdrop-filter: blur(6px);
  transition: background .2s;
}
.ev-back-btn:hover { background: rgba(255,255,255,.25); }
.ev-header__title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 26px;
  font-weight: 800;
  color: #fff;
  margin: 0 0 6px;
}
.ev-header__sub { font-size: 13px; color: rgba(255,255,255,.7); margin: 0; }

/* TOOLBAR */
.ev-toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 14px;
  align-items: center;
}
.ev-search {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
}
.ev-search__icon {
  position: absolute;
  left: 14px;
  color: var(--muted);
  pointer-events: none;
}
.ev-search__input {
  width: 100%;
  padding: 11px 40px 11px 40px;
  border: 1.5px solid var(--border);
  border-radius: 12px;
  font-size: 14px;
  outline: none;
  background: var(--white);
  color: var(--text);
  transition: border-color .2s;
}
.ev-search__input:focus { border-color: var(--pink); }
.ev-search__clear {
  position: absolute;
  right: 12px;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--muted);
  display: flex;
  align-items: center;
  padding: 4px;
  border-radius: 50%;
  transition: background .15s;
}
.ev-search__clear:hover { background: var(--pink-light); }
.ev-sort {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--white);
  border: 1.5px solid var(--border);
  border-radius: 12px;
  padding: 0 14px;
  height: 44px;
}
.ev-sort__select {
  border: none;
  background: none;
  font-size: 13px;
  color: var(--text);
  outline: none;
  cursor: pointer;
}

/* CATEGORIES */
.ev-cats {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}
.ev-cat-btn {
  padding: 7px 16px;
  border-radius: 20px;
  border: 1.5px solid var(--border);
  background: var(--white);
  font-size: 13px;
  font-weight: 600;
  color: var(--muted);
  cursor: pointer;
  transition: all .2s;
}
.ev-cat-btn:hover { border-color: var(--pink); color: var(--pink); }
.ev-cat-btn--active { background: var(--pink); color: #fff; border-color: var(--pink); }

/* LOADING */
.ev-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  gap: 16px;
  color: var(--muted);
}
.ev-loading__spinner {
  width: 44px;
  height: 44px;
  border: 3px solid var(--pink-light);
  border-top-color: var(--pink);
  border-radius: 50%;
  animation: spin .8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* EMPTY */
.ev-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  gap: 12px;
  text-align: center;
}
.ev-empty__icon { font-size: 52px; }
.ev-empty h3 { font-size: 18px; font-weight: 700; margin: 0; }
.ev-empty p { font-size: 14px; color: var(--muted); margin: 0; }

/* GRID */
.ev-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
}

/* CARD */
.ev-card {
  background: var(--white);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  cursor: pointer;
  transition: all .22s;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 12px rgba(233, 30, 140, .05);
}
.ev-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 32px rgba(233, 30, 140, .14);
  border-color: var(--pink);
}

.ev-card__img {
  position: relative;
  height: 160px;
  background: var(--pink-light);
  overflow: hidden;
}
.ev-card__img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform .3s;
}
.ev-card:hover .ev-card__img img { transform: scale(1.04); }
.ev-card__img-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #fce4ec, #fdf0f6);
}
.ev-card__badge {
  position: absolute;
  top: 10px;
  left: 10px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 800;
}
.ev-card__badge--featured { background: #fff8e1; color: #f57c00; }
.ev-card__price-badge {
  position: absolute;
  bottom: 10px;
  right: 10px;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 800;
}
.ev-card__price-badge--free { background: #e8f5e9; color: #2e7d32; }
.ev-card__price-badge--paid { background: #fff8e1; color: #f57c00; }

.ev-card__body { padding: 14px 16px 10px; flex: 1; display: flex; flex-direction: column; gap: 6px; }
.ev-card__cat {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .6px;
  color: var(--pink);
  background: var(--pink-light);
  padding: 2px 8px;
  border-radius: 20px;
  align-self: flex-start;
}
.ev-card__title { font-size: 15px; font-weight: 700; color: var(--text); margin: 0; line-height: 1.3; }
.ev-card__desc { font-size: 12px; color: var(--muted); margin: 0; line-height: 1.5; }
.ev-card__meta { display: flex; flex-wrap: wrap; gap: 8px; margin-top: auto; padding-top: 6px; }
.ev-card__meta-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--muted);
}

.ev-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px 14px;
  border-top: 1px solid var(--border);
  margin-top: 4px;
}
.ev-card__stats { display: flex; gap: 10px; }
.ev-card__stat { display: inline-flex; align-items: center; gap: 4px; font-size: 11px; color: var(--muted); }
.ev-card__cta {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: linear-gradient(135deg, var(--pink-dark), var(--pink));
  color: #fff;
  border: none;
  border-radius: 10px;
  padding: 8px 14px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all .2s;
  box-shadow: 0 3px 12px rgba(233, 30, 140, .3);
}
.ev-card__cta:hover { transform: translateY(-1px); box-shadow: 0 5px 18px rgba(233, 30, 140, .4); }

/* BTN PRIMARY */
.ev-btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 10px 20px;
  background: linear-gradient(135deg, var(--pink-dark), var(--pink));
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 3px 14px rgba(233, 30, 140, .3);
  transition: all .2s;
}
.ev-btn-primary:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(233, 30, 140, .4); }

/* RESPONSIVE */
@media (max-width: 1100px) { .ev-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 700px) {
  .ev-grid { grid-template-columns: 1fr; }
  .ev-header { padding: 24px 20px; }
  .ev-header__title { font-size: 20px; }
  .ev-toolbar { flex-direction: column; }
  .ev-sort { width: 100%; }
}
</style>