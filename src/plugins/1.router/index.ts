import { setupLayouts } from 'virtual:meta-layouts'
import type { App } from 'vue'
// @ts-ignore
import { createRouter, createWebHistory } from 'vue-router/auto'
// @ts-ignore
import type { RouteRecordRaw } from 'vue-router'

function recursiveLayouts(route: RouteRecordRaw): RouteRecordRaw {
  if (route.children) {
    for (let i = 0; i < route.children.length; i++)
      route.children[i] = recursiveLayouts(route.children[i])
    return route
  }
  return setupLayouts([route])[0]
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior(to: any) {
    if (to.hash)
      return { el: to.hash, behavior: 'smooth', top: 60 }
    return { top: 0 }
  },
  extendRoutes: (pages: any) => [
    ...[...pages].map((route: any) => recursiveLayouts(route)),
  ],
})

// Pages accessibles sans token
const publicPages = [
  '/login',
  '/register',
  '/forgot-password',
  '/organizer/two-fa-verify',   // ← 2FA organizer pendant le login
]

function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.exp * 1000 < Date.now()
  } catch {
    return true
  }
}

router.beforeEach((to: any, _from: any, next: any) => {
  const path: string = to.path

  const accessToken    = localStorage.getItem('access_token')
  const organizerToken = localStorage.getItem('organizer_token')
  const isPublic       = publicPages.includes(path) || to.meta.public === true

  if (accessToken && isTokenExpired(accessToken)) {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    localStorage.removeItem('user_role')
  }
  if (organizerToken && isTokenExpired(organizerToken)) {
    localStorage.removeItem('organizer_token')
    localStorage.removeItem('organizer_refresh')
    localStorage.removeItem('organizer')
    localStorage.removeItem('user_role')
  }

  const validUserToken = localStorage.getItem('access_token')
  const validOrgToken  = localStorage.getItem('organizer_token')

  // ── Page publique → passe directement (avant tout autre check) ────────
  if (isPublic) {
    if (validOrgToken && !isTokenExpired(validOrgToken) && path === '/login') {
      next({ path: '/organizer/dashboard', replace: true })
      return
    }
    if (validUserToken && path === '/login') {
      try {
        const payload = JSON.parse(atob(validUserToken.split('.')[1]))
        if (payload.is_staff)
          next({ path: '/admin/dashboard', replace: true })
        else
          next({ path: '/user/dashboard', replace: true })
      } catch {
        localStorage.clear()
        next({ path: '/login', replace: true })
      }
      return
    }
    next()
    return
  }

  // ── Routes organizer (authentifiées) ──────────────────────────────────
  if (path.startsWith('/organizer')) {
    if (!validOrgToken) {
      next({ path: '/login', replace: true })
      return
    }
    if (isTokenExpired(validOrgToken)) {
      localStorage.removeItem('organizer_token')
      localStorage.removeItem('organizer')
      next({ path: '/login', replace: true })
      return
    }
    next()
    return
  }

  if (!validUserToken && !validOrgToken) {
    next({ path: '/login', replace: true })
    return
  }

  // ── Routes admin ──────────────────────────────────────────────────────
  if (path.startsWith('/admin')) {
    if (!validUserToken) {
      next({ path: '/login', replace: true })
      return
    }
    try {
      const payload = JSON.parse(atob(validUserToken.split('.')[1]))
      if (!payload.is_staff) {
        next({ path: '/user/dashboard', replace: true })
        return
      }
    } catch {
      localStorage.clear()
      next({ path: '/login', replace: true })
      return
    }
  }

  // ── Routes user ───────────────────────────────────────────────────────
  if (path.startsWith('/user')) {
    if (!validUserToken) {
      next({ path: '/login', replace: true })
      return
    }
  }

  next()
})

export { router }

export default function (app: App) {
  app.use(router as any)
}