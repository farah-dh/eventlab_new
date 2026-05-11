// composables/useApi.ts
import { createFetch } from '@vueuse/core'
import { destr } from 'destr'

export const useApi = createFetch({
  baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1',
  fetchOptions: {
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
  },
  options: {
    refetch: true,
    async beforeFetch({ options }) {
      // Récupérer le token depuis les cookies
      const accessToken = useCookie('accessToken').value

      if (accessToken) {
        options.headers = {
          ...options.headers,
          Authorization: `Bearer ${accessToken}`,
        }
      }

      return { options }
    },
    afterFetch(ctx) {
      const { data, response } = ctx

      // Gestion des erreurs 401
      if (response.status === 401) {
        useCookie('accessToken').value = null
        localStorage.removeItem('access_token')
        if (typeof window !== 'undefined') {
          window.location.href = '/login'
        }
      }

      // Parser les données JSON
      let parsedData = null
      try {
        parsedData = destr(data)
      } catch (error) {
        console.error('Erreur de parsing JSON:', error)
      }

      return { data: parsedData, response }
    },
    onFetchError(ctx) {
      console.error('Erreur API:', ctx.error)
      return ctx
    },
  },
})

// ========== API ADMIN ==========
export const adminApi = {
  // Users
  async getUsers() {
    return useApi('/users/').json()
  },
  async getUser(id: number) {
    return useApi(`/users/${id}/`).json()
  },
  async createUser(data: any) {
    return useApi('/users/', { method: 'POST', body: JSON.stringify(data) }).json()
  },
  async updateUser(id: number, data: any) {
    return useApi(`/users/${id}/`, { method: 'PUT', body: JSON.stringify(data) }).json()
  },
  async deleteUser(id: number) {
    return useApi(`/users/${id}/`, { method: 'DELETE' }).json()
  },

  // Events
  async getEvents() {
    return useApi('/events/').json()
  },
  async getEvent(id: number) {
    return useApi(`/events/${id}/`).json()
  },
  async approveEvent(id: number) {
    return useApi(`/events/${id}/approve/`, { method: 'POST' }).json()
  },
  async rejectEvent(id: number) {
    return useApi(`/events/${id}/reject/`, { method: 'POST' }).json()
  },
  async deleteEvent(id: number) {
    return useApi(`/events/${id}/`, { method: 'DELETE' }).json()
  },

  // Orders
  async getOrders() {
    return useApi('/orders/').json()
  },

  // Payments
  async getPayments() {
    return useApi('/payments/').json()
  },

  // Organizers
  async getOrganizers() {
    return useApi('/organizers/').json()
  },
}

// ========== API ORGANISATEUR ==========
export const organizerApi = {
  // Statistics
  async getStatistics() {
    return useApi('/organizer/statistics/').json()
  },
  
  // Events
  async getEvents() {
    return useApi('/organizer/events/').json()
  },
  async getEvent(id: number) {
    return useApi(`/organizer/events/${id}/`).json()
  },
  async createEvent(data: any) {
    return useApi('/organizer/events/', { method: 'POST', body: JSON.stringify(data) }).json()
  },
  async updateEvent(id: number, data: any) {
    return useApi(`/organizer/events/${id}/`, { method: 'PUT', body: JSON.stringify(data) }).json()
  },
  async deleteEvent(id: number) {
    return useApi(`/organizer/events/${id}/`, { method: 'DELETE' }).json()
  },
  
  // Reservations
  async getReservations(eventId?: number) {
    const url = eventId ? `/organizer/reservations/?event_id=${eventId}` : '/organizer/reservations/'
    return useApi(url).json()
  },
  async updateReservationStatus(id: number, status: string) {
    return useApi(`/organizer/reservations/${id}/`, { 
      method: 'PATCH', 
      body: JSON.stringify({ status }) 
    }).json()
  },
}

// ========== API UTILISATEUR (si nécessaire) ==========
export const userApi = {
  // Events publiques
  async getPublicEvents() {
    return useApi('/public/events/').json()
  },
  async getEventDetails(id: number) {
    return useApi(`/public/events/${id}/`).json()
  },
  
  // Réservations
  async createReservation(data: any) {
    return useApi('/reservations/', { method: 'POST', body: JSON.stringify(data) }).json()
  },
  async getMyReservations() {
    return useApi('/my/reservations/').json()
  },
  
  // Paiements
  async createPayment(data: any) {
    return useApi('/payments/', { method: 'POST', body: JSON.stringify(data) }).json()
  },
}