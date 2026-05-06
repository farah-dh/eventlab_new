// src/stores/auth.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {

  const token     = ref(localStorage.getItem('access_token') || null)
  const orgToken  = ref(localStorage.getItem('organizer_token') || null)
  const user      = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const isLoading = ref(false)

  const isAuthenticated = computed(() => !!token.value || !!orgToken.value)
  const isAdmin         = computed(() => user.value?.is_staff === true)
  const isOrganizer     = computed(() =>
    !!orgToken.value || user.value?.is_organizer === true
  )

  // ── Login Utilisateur / Admin ──────────────────────────
  async function login(email: string, password: string) {
    isLoading.value = true
    try {
      const res = await fetch('/api/v1/auth/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      const json = await res.json()
      const payload = json.data || json

      // ✅ 2FA required
      if (payload['2fa_required']) {
        return { success: false, requires2FA: true, userId: payload.user_id }
      }

      if (!res.ok) {
        return {
          success: false,
          message: json.detail || json.message || 'Email ou mot de passe incorrect',
        }
      }

      const accessToken = payload.access || payload.token
      const userData    = payload.user || null

      token.value = accessToken
      user.value  = userData
      localStorage.setItem('access_token', accessToken)
      localStorage.setItem('refresh_token', payload.refresh || '')
      localStorage.setItem('user', JSON.stringify(userData))

      return { success: true }

    } catch (err) {
      return { success: false, message: 'Impossible de se connecter au serveur.' }
    } finally {
      isLoading.value = false
    }
  }

  // ── Login Organisateur ────────────────────────────────
  async function loginOrganizer(email: string, password: string) {
    isLoading.value = true
    try {
      const res = await fetch('/api/v1/auth/organizer-login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      const json = await res.json()

      if (!res.ok) {
        return {
          success: false,
          message: json.detail || json.message || 'Email ou mot de passe incorrect',
        }
      }

      const payload     = json.data || json
      const accessToken = payload.access || payload.token

      if (!accessToken) {
        return { success: false, message: 'Token manquant dans la réponse du serveur.' }
      }

      const organizerData = payload.organizer || payload.user || null
      const userData = organizerData
        ? { ...organizerData, is_organizer: true }
        : { is_organizer: true }

      orgToken.value = accessToken
      user.value     = userData
      localStorage.setItem('organizer_token', accessToken)
      localStorage.setItem('organizer_refresh', payload.refresh || '')
      localStorage.setItem('user', JSON.stringify(userData))

      return { success: true }

    } catch (err) {
      return { success: false, message: 'Impossible de se connecter au serveur.' }
    } finally {
      isLoading.value = false
    }
  }

  // ── Logout ────────────────────────────────────────────
  async function logout() {
    try {
      await fetch('/api/v1/auth/logout/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token.value || orgToken.value}`,
        },
      })
    } catch (_) {}

    token.value    = null
    orgToken.value = null
    user.value     = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('organizer_token')
    localStorage.removeItem('organizer_refresh')
    localStorage.removeItem('user')
  }

  // ── Forgot Password ───────────────────────────────────
  async function forgotPassword(email: string): Promise<void> {
    const res = await fetch('/api/v1/auth/password-reset/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    })
    if (res.ok) return
    let msg = 'Une erreur est survenue. Veuillez réessayer.'
    try {
      const json = await res.json()
      msg = json.detail || json.message || json.email?.[0] || msg
    } catch {}
    throw new Error(msg)
  }

  // ── Reset Password ────────────────────────────────────
  async function resetPassword(resetToken: string, password: string): Promise<void> {
    const res = await fetch('/api/v1/auth/password-reset/confirm/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: resetToken, password }),
    })
    if (res.ok) return
    let msg = 'Une erreur est survenue. Le lien est peut-être expiré.'
    try {
      const json = await res.json()
      msg = json.detail || json.message || json.token?.[0] || msg
    } catch {}
    throw new Error(msg)
  }

  // ── 2FA ───────────────────────────────────────────────

  async function verify2FA(userId: number, otp: string) {
    try {
      const res = await fetch('/api/v1/auth/2fa/verify/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, otp }),
      })
      const json = await res.json()
      if (!res.ok) return { success: false, message: json.message || 'Code incorrect.' }
      const payload = json.data || json
      token.value = payload.access
      user.value  = payload.user
      localStorage.setItem('access_token', payload.access)
      localStorage.setItem('refresh_token', payload.refresh || '')
      localStorage.setItem('user', JSON.stringify(payload.user))
      return { success: true }
    } catch {
      return { success: false, message: 'Erreur de connexion.' }
    }
  }

  async function resend2FA(userId: number) {
    try {
      const res = await fetch('/api/v1/auth/2fa/resend/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId }),
      })
      const json = await res.json()
      if (!res.ok) return { success: false, message: json.message || 'Erreur.' }
      return { success: true }
    } catch {
      return { success: false, message: 'Erreur de connexion.' }
    }
  }

  async function get2FAStatus() {
    try {
      const res = await fetch('/api/v1/auth/2fa/status/', {
        headers: { Authorization: `Bearer ${token.value}` },
      })
      const json = await res.json()
      return { enabled: json.data?.['2fa_enabled'] ?? false }
    } catch {
      return { enabled: false }
    }
  }

  async function enable2FA() {
    try {
      const res = await fetch('/api/v1/auth/2fa/enable/', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token.value}` },
      })
      const json = await res.json()
      if (!res.ok) return { success: false, message: json.message || 'Erreur.' }
      return { success: true }
    } catch {
      return { success: false, message: 'Erreur de connexion.' }
    }
  }

  async function confirmEnable2FA(otp: string) {
    try {
      const res = await fetch('/api/v1/auth/2fa/enable/confirm/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token.value}`,
        },
        body: JSON.stringify({ otp }),
      })
      const json = await res.json()
      if (!res.ok) return { success: false, message: json.message || 'Code incorrect.' }
      return { success: true }
    } catch {
      return { success: false, message: 'Erreur de connexion.' }
    }
  }

  async function disable2FA(otp?: string) {
    try {
      const res = await fetch('/api/v1/auth/2fa/disable/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token.value}`,
        },
        body: JSON.stringify(otp ? { otp } : {}),
      })
      const json = await res.json()
      if (!res.ok) return { success: false, message: json.message || 'Code incorrect.' }
      return { success: true }
    } catch {
      return { success: false, message: 'Erreur de connexion.' }
    }
  }

  return {
    token, orgToken, user, isLoading,
    isAuthenticated, isAdmin, isOrganizer,
    login, loginOrganizer, logout,
    forgotPassword, resetPassword,
    verify2FA, resend2FA, get2FAStatus,
    enable2FA, confirmEnable2FA, disable2FA,
  }
})