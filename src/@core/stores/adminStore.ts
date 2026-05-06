// stores/adminStore.ts
import { defineStore } from 'pinia'
import { adminApi } from '@/composables/useApi'

// Helper pour extraire les données d'une Ref
async function extractData<T>(promise: Promise<any>): Promise<T> {
  const response = await promise
  return response.data.value as T
}

export interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  role: 'user' | 'organizer' | 'admin'
  is_active: boolean
  date_joined: string
}

export interface Event {
  id: number
  title: string
  description: string
  date: string
  location: string
  price: number
  capacity: number
  tickets_sold: number
  status: 'pending' | 'published' | 'rejected' | 'completed'
  organizer_id: number
  created_at: string
}

export interface Payment {
  id: number
  order_id: number
  amount: number
  method: string
  status: string
  created_at: string
}

export const useAdminStore = defineStore('admin', {
  state: () => ({
    users: [] as User[],
    events: [] as Event[],
    payments: [] as Payment[],
    loading: false,
    error: null as string | null,
  }),

  getters: {
    totalUsers: (state) => state.users.length,
    organizers: (state) => state.users.filter((u) => u.role === 'organizer'),
    admins: (state) => state.users.filter((u) => u.role === 'admin'),
    regularUsers: (state) => state.users.filter((u) => u.role === 'user'),
    activeUsers: (state) => state.users.filter((u) => u.is_active),
    totalEvents: (state) => state.events.length,
    pendingEvents: (state) => state.events.filter((e) => e.status === 'pending'),
    publishedEvents: (state) => state.events.filter((e) => e.status === 'published'),
    totalRevenue: (state) => state.payments.reduce((sum, p) => sum + p.amount, 0),
  },

  actions: {
    // ========== UTILISATEURS ==========
    async fetchUsers() {
      this.loading = true
      try {
        const data = await extractData<User[]>(adminApi.getUsers())
        this.users = data
        this.error = null
      } catch (err: any) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },

    async createUser(userData: Partial<User>) {
      const data = await extractData<User>(adminApi.createUser(userData))
      this.users.push(data)
      return data
    },

    async updateUser(userId: number, userData: Partial<User>) {
      const data = await extractData<User>(adminApi.updateUser(userId, userData))
      const index = this.users.findIndex((u) => u.id === userId)
      if (index !== -1) this.users[index] = data
      return data
    },

    async deleteUser(userId: number) {
      await adminApi.deleteUser(userId)
      this.users = this.users.filter((u) => u.id !== userId)
    },

    // ========== ÉVÉNEMENTS ==========
    async fetchEvents() {
      this.loading = true
      try {
        const data = await extractData<Event[]>(adminApi.getEvents())
        this.events = data
        this.error = null
      } catch (err: any) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },

    async approveEvent(eventId: number) {
      const data = await extractData<Event>(adminApi.approveEvent(eventId))
      const index = this.events.findIndex((e) => e.id === eventId)
      if (index !== -1) this.events[index] = data
      return data
    },

    async rejectEvent(eventId: number) {
      const data = await extractData<Event>(adminApi.rejectEvent(eventId))
      const index = this.events.findIndex((e) => e.id === eventId)
      if (index !== -1) this.events[index] = data
      return data
    },

    async deleteEvent(eventId: number) {
      await adminApi.deleteEvent(eventId)
      this.events = this.events.filter((e) => e.id !== eventId)
    },

    // ========== PAIEMENTS ==========
    async fetchPayments() {
      const data = await extractData<Payment[]>(adminApi.getPayments())
      this.payments = data
    },

    // ========== TOUT EN UN ==========
    async fetchAllData() {
      await Promise.all([
        this.fetchUsers(),
        this.fetchEvents(),
        this.fetchPayments(),
      ])
    },

    // ========== RESET ==========
    reset() {
      this.users = []
      this.events = []
      this.payments = []
      this.loading = false
      this.error = null
    },
  },
})