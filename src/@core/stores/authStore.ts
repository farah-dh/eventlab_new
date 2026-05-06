// stores/authStore.ts
import { defineStore } from 'pinia'
import { useApi } from '@/composables/useApi'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as any | null,
    token: null as string | null,
    isAuthenticated: false,
    loading: false,
  }),

  actions: {
    async login(email: string, password: string) {
      this.loading = true
      try {
        const response = await useApi('/auth/login/', {
          method: 'POST',
          body: JSON.stringify({ email, password }),
        }).json()
        
        // ✅ Correction : utiliser .value pour accéder aux données
        const data = response.data.value
        
        this.token = data.access
        this.user = data.user
        this.isAuthenticated = true
        
        // Stocker dans cookie/localStorage
        useCookie('accessToken').value = data.access
        localStorage.setItem('access_token', data.access)
        
        return true
      } catch (error) {
        console.error('Login failed', error)
        return false
      } finally {
        this.loading = false
      }
    },

    async logout() {
      this.token = null
      this.user = null
      this.isAuthenticated = false
      useCookie('accessToken').value = null
      localStorage.removeItem('access_token')
    },

    async fetchMe() {
      try {
        const response = await useApi('/auth/me/').json()
        const data = response.data.value
        this.user = data
        this.isAuthenticated = true
      } catch (error) {
        this.logout()
      }
    },
  },
})