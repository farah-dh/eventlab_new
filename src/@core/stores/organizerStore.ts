// src/@core/stores/organizerStore.ts
import { defineStore } from 'pinia'
import { organizerApi } from '@/composables/useApi'

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

export interface Reservation {
  id: number
  user_name: string
  user_email: string
  quantity: number
  total_price: number
  status: string
  created_at: string
}

export interface Statistics {
  total_revenue: number
  total_tickets_sold: number
  active_events: number
  total_events: number
}

export const useOrganizerStore = defineStore('organizer', {
  state: () => ({
    events: [] as Event[],
    reservations: [] as Reservation[],
    statistics: null as Statistics | null,
    loading: false,
    error: null as string | null,
  }),

  getters: {
    totalEvents: (state) => state.events.length,
    activeEvents: (state) => state.events.filter((e) => e.status === 'published').length,
    pendingEvents: (state) => state.events.filter((e) => e.status === 'pending').length,
    totalTicketsSold: (state) => state.events.reduce((sum, e) => sum + e.tickets_sold, 0),
    totalRevenue: (state) => state.events.reduce((sum, e) => sum + (e.tickets_sold * e.price), 0),
    publishedEvents: (state) => state.events.filter((e) => e.status === 'published'),
  },

  actions: {
    // ========== STATISTIQUES ==========
    async fetchStatistics() {
      this.loading = true
      try {
        const response = await organizerApi.getStatistics()
        this.statistics = response.data.value as Statistics
        this.error = null
      } catch (err: any) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },

    // ========== ÉVÉNEMENTS ==========
    async fetchEvents() {
      this.loading = true
      try {
        const response = await organizerApi.getEvents()
        this.events = response.data.value as Event[]
        this.error = null
      } catch (err: any) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },

    async createEvent(eventData: Partial<Event>) {
      const response = await organizerApi.createEvent(eventData)
      const newEvent = response.data.value as Event
      this.events.push(newEvent)
      return newEvent
    },

    async updateEvent(eventId: number, eventData: Partial<Event>) {
      const response = await organizerApi.updateEvent(eventId, eventData)
      const updated = response.data.value as Event
      const index = this.events.findIndex((e) => e.id === eventId)
      if (index !== -1) this.events[index] = updated
      return updated
    },

    async deleteEvent(eventId: number) {
      await organizerApi.deleteEvent(eventId)
      this.events = this.events.filter((e) => e.id !== eventId)
    },

    // ========== RÉSERVATIONS ==========
    async fetchReservations(eventId?: number) {
      this.loading = true
      try {
        const response = await organizerApi.getReservations(eventId)
        this.reservations = response.data.value as Reservation[]
        this.error = null
      } catch (err: any) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },

    async updateReservationStatus(reservationId: number, status: string) {
      const response = await organizerApi.updateReservationStatus(reservationId, status)
      const updated = response.data.value as Reservation
      const index = this.reservations.findIndex((r) => r.id === reservationId)
      if (index !== -1) this.reservations[index] = updated
      return updated
    },

    // ========== TOUT EN UN ==========
    async fetchAllData() {
      await Promise.all([
        this.fetchStatistics(),
        this.fetchEvents(),
      ])
    },

    reset() {
      this.events = []
      this.reservations = []
      this.statistics = null
      this.loading = false
      this.error = null
    },
  },
})