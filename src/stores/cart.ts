import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface CartItem {
  id: number              // ID unique panier
  eventId: number         // ID événement backend
  title: string           // Titre événement
  image: string | null    // Image
  price: number           // Prix unitaire
  quantity: number        // Quantité
  date: string            // Date événement
  location: string        // Lieu
  category: string        // Catégorie
}

const STORAGE_KEY = 'eventlab_cart'

const loadCart = (): CartItem[] => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

const saveCart = (items: CartItem[]) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
  } catch {}
}

export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>(loadCart())

  // Nombre total d'items
  const totalItems = computed(() =>
    items.value.reduce((sum, it) => sum + it.quantity, 0)
  )

  // Prix total
  const totalPrice = computed(() =>
    items.value.reduce((sum, it) => sum + (it.price * it.quantity), 0)
  )

  // Ajouter un item
  const addItem = (item: Omit<CartItem, 'id'>) => {
    // Si déjà dans panier (même événement), augmenter la quantité
    const existing = items.value.find(it => it.eventId === item.eventId)
    if (existing) {
      existing.quantity += item.quantity
    } else {
      items.value.push({
        ...item,
        id: Date.now() + Math.random(),
      })
    }
    saveCart(items.value)
  }

  // Retirer complètement un item
  const removeItem = (id: number) => {
    items.value = items.value.filter(it => it.id !== id)
    saveCart(items.value)
  }

  // Modifier quantité
  const updateQuantity = (id: number, qty: number) => {
    const item = items.value.find(it => it.id === id)
    if (!item) return
    if (qty <= 0) {
      removeItem(id)
      return
    }
    item.quantity = qty
    saveCart(items.value)
  }

  // Incrémenter
  const increment = (id: number) => {
    const item = items.value.find(it => it.id === id)
    if (item) updateQuantity(id, item.quantity + 1)
  }

  // Décrémenter
  const decrement = (id: number) => {
    const item = items.value.find(it => it.id === id)
    if (item) updateQuantity(id, item.quantity - 1)
  }

  // Vider tout
  const clearCart = () => {
    items.value = []
    saveCart(items.value)
  }

  return {
    items,
    totalItems,
    totalPrice,
    addItem,
    removeItem,
    updateQuantity,
    increment,
    decrement,
    clearCart,
  }
})