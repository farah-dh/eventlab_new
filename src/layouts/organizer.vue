<script setup lang="ts">
import { computed, ref, watch, onMounted, onBeforeUnmount } from 'vue'

const route  = useRoute()
const router = useRouter()

const organizer = computed(() => {
  try { return JSON.parse(localStorage.getItem('organizer') || '{}') }
  catch { return {} }
})

const userName = computed(() => {
  const org = organizer.value
  if (org.firstname && org.lastname) return `${org.firstname} ${org.lastname}`
  return org.organization_name || 'Organisateur'
})

const orgName = computed(() => organizer.value.organization_name || 'Mon Organisation')

const userInitials = computed(() => {
  const org = organizer.value
  if (org.firstname && org.lastname)
    return `${org.firstname[0]}${org.lastname[0]}`.toUpperCase()
  if (org.organization_name) return org.organization_name[0].toUpperCase()
  return 'O'
})

// ─── Navigation ───────────────────────────────────────────────────────────────
const navGroups = [
  {
    label: 'Principal',
    items: [
      { to: '/organizer/dashboard', icon: 'tabler-layout-dashboard', title: 'Tableau de bord' },
    ],
  },
  {
    label: 'Événements',
    items: [
      { to: '/organizer/events',        icon: 'tabler-calendar-event', title: 'Mes événements' },
      { to: '/organizer/events/create', icon: 'tabler-circle-plus',    title: 'Créer un événement' },
    ],
  },
  {
    label: 'Finances',
    items: [
      { to: '/organizer/finances',   icon: 'tabler-chart-bar',     title: 'Total des ventes' },
      { to: '/organizer/withdrawal', icon: 'tabler-cash-banknote', title: "Retrait d'argent" },
    ],
  },
  {
    label: 'Réservations',
    items: [
      { to: '/organizer/orders', icon: 'tabler-ticket', title: 'Réservations' },
    ],
  },
]

const pageTitle = computed(() => {
  const map: Record<string, string> = {
    'organizer-dashboard':     'Tableau de bord',
    'organizer-events':        'Mes événements',
    'organizer-events-create': 'Créer un événement',
    'organizer-orders':        'Réservations',
    'organizer-profile':       'Mon profil',
    'organizer-finances':      'Total des ventes',
    'organizer-withdrawal':    "Retrait d'argent",
  }
  return map[String(route.name)] || 'Dashboard'
})

const sidebarOpen         = ref(false)
const searchQuery         = ref('')
const notificationsDialog = ref(false)
const unreadCount         = ref(0)
const notifications       = ref<any[]>([])

// ─── Menu profil ──────────────────────────────────────────────────────────────
const profileMenuOpen = ref(false)
const profileMenuRef  = ref<HTMLElement | null>(null)

const toggleProfileMenu = () => { profileMenuOpen.value = !profileMenuOpen.value }
const closeProfileMenu  = (e: MouseEvent) => {
  if (profileMenuRef.value && !profileMenuRef.value.contains(e.target as Node))
    profileMenuOpen.value = false
}

onMounted(() => document.addEventListener('click', closeProfileMenu))
onBeforeUnmount(() => document.removeEventListener('click', closeProfileMenu))

let searchTimeout: ReturnType<typeof setTimeout>
watch(searchQuery, val => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => console.log('Recherche:', val), 300)
})

const handleLogout = () => {
  localStorage.removeItem('organizer_token')
  localStorage.removeItem('organizer_refresh')
  localStorage.removeItem('organizer')
  localStorage.removeItem('user_role')
  router.push('/login')
}

const goToProfile = () => {
  profileMenuOpen.value = false
  router.push('/organizer/profile')
}

const goToDashboard = () => {
  profileMenuOpen.value = false
  router.push('/organizer/dashboard')
}
</script>

<template>
  <div class="org-layout">

    <div v-if="sidebarOpen" class="overlay" @click="sidebarOpen = false" />

    <!-- ══════ SIDEBAR ══════ -->
    <aside :class="['sidebar', { 'sidebar--open': sidebarOpen }]">

      <!-- Brand -->
      <div class="sidebar-brand">
        <div class="brand-icon">
          <VIcon icon="tabler-calendar-event" color="white" size="18" />
        </div>
        <div>
          <span class="brand-name">EventLab</span>
          <span class="brand-sub">Espace organisateur</span>
        </div>
      </div>

      <!-- Nav -->
      <nav class="sidebar-nav">
        <template v-for="group in navGroups" :key="group.label">
          <span class="nav-section">{{ group.label }}</span>
          <RouterLink
            v-for="item in group.items"
            :key="item.to"
            :to="item.to"
            class="nav-item"
            active-class="nav-item--active"
            @click="sidebarOpen = false"
          >
            <span class="nav-item-icon">
              <VIcon :icon="item.icon" size="15" />
            </span>
            {{ item.title }}
          </RouterLink>
        </template>
      </nav>

      <!-- Footer -->
      <div class="sidebar-footer">
        <RouterLink to="/organizer/profile" class="user-card" @click="sidebarOpen = false">
          <div class="user-avatar">{{ userInitials }}</div>
          <div class="user-info">
            <span class="user-name">{{ userName }}</span>
            <span class="user-org">{{ orgName }}</span>
          </div>
          <VIcon icon="tabler-settings" size="14" class="user-settings-icon" />
        </RouterLink>
      </div>
    </aside>

    <!-- ══════ MAIN ══════ -->
    <div class="org-main">

      <header class="topbar">
        <div class="topbar-left">
          <button class="burger" @click="sidebarOpen = !sidebarOpen">
            <VIcon icon="tabler-menu-2" size="20" />
          </button>
          <span class="topbar-title">{{ pageTitle }}</span>
        </div>
        <div class="topbar-right">
          <div class="search-wrap">
            <VIcon icon="tabler-search" size="14" class="search-icon" />
            <input v-model="searchQuery" type="text" placeholder="Rechercher..." class="search-input">
          </div>
          <button class="icon-btn" @click="notificationsDialog = true">
            <VIcon icon="tabler-bell" size="17" />
            <span v-if="unreadCount > 0" class="notif-dot">{{ unreadCount }}</span>
          </button>

          <!-- Avatar + Menu profil -->
          <div ref="profileMenuRef" class="profile-wrap">
            <button class="topbar-avatar" @click.stop="toggleProfileMenu">
              {{ userInitials }}
            </button>
            <div v-if="profileMenuOpen" class="profile-menu">
              <div class="profile-menu-header">
                <div class="profile-menu-avatar">{{ userInitials }}</div>
                <div>
                  <p class="profile-menu-name">{{ userName }}</p>
                  <p class="profile-menu-org">{{ orgName }}</p>
                  <p class="profile-menu-email">{{ organizer.email || '' }}</p>
                </div>
              </div>
              <div class="profile-menu-divider" />
              <button class="profile-menu-item" @click="goToDashboard">
                <VIcon icon="tabler-layout-dashboard" size="16" /> Tableau de bord
              </button>
              <button class="profile-menu-item" @click="goToProfile">
                <VIcon icon="tabler-user-circle" size="16" /> Mon profil
              </button>
              <div class="profile-menu-divider" />
              <button class="profile-menu-item profile-menu-item--danger" @click="handleLogout">
                <VIcon icon="tabler-logout" size="16" /> Déconnexion
              </button>
            </div>
          </div>
        </div>
      </header>

      <main class="org-content">
        <RouterView />
      </main>
    </div>

    <!-- Dialog notifications -->
    <VDialog v-model="notificationsDialog" max-width="440">
      <VCard>
        <VCardText class="pa-6">
          <div class="d-flex align-center justify-space-between mb-4">
            <h3 class="text-h6 font-weight-bold">Notifications</h3>
            <VBtn icon variant="text" size="small" @click="notificationsDialog = false">
              <VIcon icon="tabler-x" size="16" />
            </VBtn>
          </div>
          <div v-if="notifications.length === 0" class="text-center py-8">
            <VIcon icon="tabler-bell-off" size="40" color="grey-lighten-2" class="mb-3" />
            <p class="text-medium-emphasis text-body-2">Aucune notification</p>
          </div>
        </VCardText>
      </VCard>
    </VDialog>

  </div>
</template>

<style scoped lang="scss">
// ── Variables rose ────────────────────────────────────────────────────────────
$pink-1:    #C8365F;
$pink-2:    #A82248;
$pink-soft: rgba(200, 54, 95, 0.15);

$sidebar-w:  250px;
$topbar-h:   56px;
$sidebar-bg: #16050C;

// ── Layout ────────────────────────────────────────────────────────────────────
.org-layout { display: flex; min-height: 100vh; background: #F3F4F6; }

.overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.55); z-index: 99;
  display: none;
  @media (max-width: 768px) { display: block; }
}

// ── Sidebar ───────────────────────────────────────────────────────────────────
.sidebar {
  width: $sidebar-w; background: $sidebar-bg;
  display: flex; flex-direction: column;
  position: fixed; height: 100vh; left: 0; top: 0; z-index: 100;
  transition: transform .25s ease;
  border-right: 1px solid rgba(200,54,95,0.12);

  &::before {
    content: '';
    position: absolute; inset: 0;
    background: radial-gradient(ellipse 120% 40% at 50% 0%, rgba(200,54,95,0.18) 0%, transparent 60%);
    pointer-events: none;
  }

  @media (max-width: 768px) {
    transform: translateX(-100%);
    &--open { transform: translateX(0); }
  }
}

.sidebar-brand {
  display: flex; align-items: center; gap: 11px;
  padding: 20px 16px 16px; position: relative; z-index: 1;
  border-bottom: 1px solid rgba(200,54,95,0.12);

  .brand-icon {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, $pink-1, $pink-2);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; box-shadow: 0 4px 12px rgba(200,54,95,0.4);
  }
  .brand-name { display: block; font-size: 15px; font-weight: 700; color: #FFF0F5; letter-spacing: -.2px; }
  .brand-sub  { display: block; font-size: 10.5px; color: rgba(200,54,95,0.6); margin-top: 1px; }
}

.sidebar-nav {
  flex: 1; padding: 14px 10px;
  display: flex; flex-direction: column; gap: 1px;
  overflow-y: auto; position: relative; z-index: 1;
  &::-webkit-scrollbar { width: 3px; }
  &::-webkit-scrollbar-track { background: transparent; }
  &::-webkit-scrollbar-thumb { background: rgba(200,54,95,0.2); border-radius: 2px; }
}

.nav-section {
  font-size: 9.5px; font-weight: 700;
  color: rgba(200,54,95,0.45);
  text-transform: uppercase; letter-spacing: 1px;
  padding: 12px 10px 4px; display: block;
  &:first-child { padding-top: 2px; }
}

.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 10px; border-radius: 8px;
  color: rgba(255,240,245,0.5); text-decoration: none;
  font-size: 13.5px; font-weight: 500;
  transition: all .15s; position: relative;

  .nav-item-icon {
    width: 28px; height: 28px; border-radius: 7px;
    display: flex; align-items: center; justify-content: center;
    background: rgba(255,255,255,0.04);
    transition: all .15s; flex-shrink: 0;
  }

  &:hover {
    background: rgba(200,54,95,0.08); color: #FFF0F5;
    .nav-item-icon { background: rgba(200,54,95,0.12); }
  }

  &--active {
    background: $pink-soft; color: #FFB3CF; font-weight: 600;
    .nav-item-icon {
      background: linear-gradient(135deg, $pink-1, $pink-2);
      box-shadow: 0 3px 10px rgba(200,54,95,0.4); color: white;
    }
    &::before {
      content: ''; position: absolute; left: 0; top: 50%;
      transform: translateY(-50%);
      width: 3px; height: 20px;
      background: $pink-1; border-radius: 0 3px 3px 0;
    }
  }
}

.sidebar-footer {
  padding: 10px; border-top: 1px solid rgba(200,54,95,0.12);
  position: relative; z-index: 1;
}

.user-card {
  display: flex; align-items: center; gap: 10px;
  padding: 10px; border-radius: 10px;
  background: rgba(200,54,95,0.08);
  border: 1px solid rgba(200,54,95,0.12);
  text-decoration: none; cursor: pointer; transition: all .15s;
  &:hover { background: rgba(200,54,95,0.14); border-color: rgba(200,54,95,0.25); }
}

.user-avatar {
  width: 32px; height: 32px; border-radius: 50%;
  background: linear-gradient(135deg, $pink-1, $pink-2);
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; color: white; flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(200,54,95,0.35);
}
.user-info           { flex: 1; min-width: 0; }
.user-name           { display: block; font-size: 12.5px; font-weight: 600; color: #FFF0F5; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.user-org            { display: block; font-size: 11px; color: rgba(200,54,95,0.5); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.user-settings-icon  { color: rgba(200,54,95,0.4); flex-shrink: 0; }

// ── Main ──────────────────────────────────────────────────────────────────────
.org-main {
  flex: 1; margin-left: $sidebar-w; min-height: 100vh;
  display: flex; flex-direction: column;
  @media (max-width: 768px) { margin-left: 0; }
}

// ── Topbar ────────────────────────────────────────────────────────────────────
.topbar {
  height: $topbar-h; background: white;
  border-bottom: 0.5px solid #F3E8ED;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px; position: sticky; top: 0; z-index: 50;
}
.topbar-left  { display: flex; align-items: center; gap: 14px; }
.topbar-title { font-size: 15px; font-weight: 600; color: #1A0510; }
.topbar-right { display: flex; align-items: center; gap: 10px; }

.search-wrap {
  display: flex; align-items: center; gap: 8px;
  background: #FFF8FA; border: 0.5px solid #F3D6E0;
  border-radius: 8px; padding: 6px 12px; transition: all .2s;
  &:focus-within {
    background: white; border-color: $pink-1;
    box-shadow: 0 0 0 3px rgba(200,54,95,0.08);
  }
  .search-icon  { color: rgba(200,54,95,0.4); flex-shrink: 0; }
  .search-input {
    border: none; background: none; outline: none;
    font-size: 13px; color: #1A0510; width: 150px;
    &::placeholder { color: rgba(200,54,95,0.35); }
  }
  @media (max-width: 768px) { display: none; }
}

.icon-btn {
  position: relative; width: 34px; height: 34px; border-radius: 8px;
  border: 0.5px solid #F3D6E0; background: white;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; color: $pink-1; transition: all .15s;
  &:hover { background: #FFF0F5; border-color: $pink-1; }
  .notif-dot {
    position: absolute; top: -3px; right: -3px;
    background: $pink-1; color: white; font-size: 9px; font-weight: 700;
    width: 16px; height: 16px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
  }
}

.profile-wrap { position: relative; }

.topbar-avatar {
  width: 34px; height: 34px; border-radius: 50%;
  background: linear-gradient(135deg, $pink-1, $pink-2);
  border: 2px solid #F9D0DE;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; color: white;
  cursor: pointer; transition: all .15s;
  box-shadow: 0 2px 8px rgba(200,54,95,0.3);
  &:hover { transform: scale(1.05); box-shadow: 0 4px 12px rgba(200,54,95,0.4); }
}

.profile-menu {
  position: absolute; top: calc(100% + 10px); right: 0;
  width: 240px; background: white;
  border: 0.5px solid #F3D6E0; border-radius: 12px;
  box-shadow: 0 8px 24px rgba(125,18,53,0.12);
  overflow: hidden; z-index: 200;
  animation: menuSlide .15s ease;
}

@keyframes menuSlide {
  from { opacity: 0; transform: translateY(-8px); }
  to   { opacity: 1; transform: translateY(0); }
}

.profile-menu-header {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px; background: #FFF8FA;
  border-bottom: 0.5px solid #F3D6E0;
}
.profile-menu-avatar {
  width: 38px; height: 38px; border-radius: 50%;
  background: linear-gradient(135deg, $pink-1, $pink-2);
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 700; color: white; flex-shrink: 0;
  box-shadow: 0 3px 10px rgba(200,54,95,0.35);
}
.profile-menu-name  { font-size: 13px; font-weight: 600; color: #1A0510; margin: 0 0 1px; }
.profile-menu-org   { font-size: 11px; color: $pink-1; margin: 0 0 1px; font-weight: 500; }
.profile-menu-email { font-size: 11px; color: #9CA3AF; margin: 0; }
.profile-menu-divider { height: 0.5px; background: #F3D6E0; margin: 4px 0; }

.profile-menu-item {
  display: flex; align-items: center; gap: 10px;
  width: 100%; padding: 10px 16px;
  border: none; background: none;
  font-size: 13px; color: #374151;
  cursor: pointer; transition: all .12s; text-align: left;
  &:hover { background: #FFF0F5; color: $pink-1; }
  &--danger { color: #EF4444; &:hover { background: #FEF2F2; color: #DC2626; } }
}

.burger {
  background: none; border: none; cursor: pointer; padding: 5px;
  border-radius: 7px; color: $pink-1;
  display: flex; align-items: center; justify-content: center;
  &:hover { background: #FFF0F5; }
}

.org-content { flex: 1; padding: 28px 24px; }
</style>